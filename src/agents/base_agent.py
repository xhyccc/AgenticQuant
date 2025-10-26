"""
Base Agent with ReAct Loop Implementation
"""
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from src.mcp.protocol import (
    AgentState, MCPMessage, MessageRole, ToolCall, ToolResult,
    create_mcp_message, create_tool_call
)
from src.llm_client import LLMClient
from src.tools import ToolRegistry
import json
from datetime import datetime


class BaseAgent(ABC):
    """Base class for all agents implementing ReAct pattern"""
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        workspace_path: str,
        tool_registry: ToolRegistry,
        llm_client: LLMClient
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.workspace_path = workspace_path
        self.tool_registry = tool_registry
        self.llm_client = llm_client
        
        self.state = AgentState(
            agent_id=agent_id,
            agent_type=agent_type,
            status="idle",
            workspace_path=workspace_path
        )
        
        self.max_iterations = 10  # Max ReAct iterations (reduced to minimize API calls)
        self._task_finished = False  # Flag to signal early completion
    
    def finish(self) -> Dict[str, Any]:
        """
        Signal that the task is complete and should finish immediately.
        This can be called by agents to exit the ReAct loop early.
        
        Returns:
            A dictionary indicating the finish signal
        """
        self._task_finished = True
        return {
            "status": "finished",
            "message": "Task completed by agent's finish() call"
        }
    
    # Example: Update executor system prompt
    def get_system_prompt(self) -> str:
        return """You are a tactical executor...
        
    IMPORTANT: When you complete your task successfully, call the finish() 
    tool with a summary. This helps the system move efficiently."""
    
    @abstractmethod
    def get_available_tools(self) -> List[str]:
        """Get list of tools this agent can use"""
        pass
    
    async def execute_task(
        self,
        task: str,
        context: Optional[List[MCPMessage]] = None
    ) -> Dict[str, Any]:
        """
        Execute a task using ReAct loop
        
        Returns:
            {
                "success": bool,
                "result": Any,
                "thoughts": List[str],
                "actions": List[ToolCall],
                "observations": List[str]
            }
        """
        # Reset finish flag at the start of each task
        self._task_finished = False
        
        self.state.status = "thinking"
        self.state.current_task = task
        
        # Initialize context
        if context is None:
            context = []
        
        # Get current time for context
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Build system prompt with timestamp
        system_prompt = self.get_system_prompt()
        system_prompt_with_time = f"""{system_prompt}

===== CURRENT CONTEXT =====
Current Date: {current_date}
Current Time: {current_time}
Workspace: {self.workspace_path}
===========================

Remember to use the current date/time information when relevant to your task."""
        
        # Add system prompt and task
        messages = [
            {"role": "system", "content": system_prompt_with_time},
            {"role": "user", "content": task}
        ]
        
        # Add context messages
        for msg in context:
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        thoughts = []
        actions = []
        observations = []
        
        # ReAct loop
        for iteration in range(self.max_iterations):
            # Check if task was marked as finished
            if self._task_finished:
                self.state.status = "completed"
                return {
                    "success": True,
                    "result": thoughts[-1] if thoughts else "Task completed via finish()",
                    "thoughts": thoughts,
                    "actions": actions,
                    "observations": observations,
                    "iterations": iteration,
                    "finished_early": True
                }
            
            try:
                # Get available tools
                tool_names = self.get_available_tools()
                tool_definitions = self.tool_registry.get_tool_definitions(tool_names)
                
                # Add the special "finish" tool that agents can call to complete early
                from src.mcp.protocol import ToolDefinition, ToolParameter
                finish_tool = ToolDefinition(
                    name="finish",
                    description="Call this tool when you have completed the task successfully. This will immediately end the current task and move to the next step.",
                    parameters=[
                        ToolParameter(
                            name="message",
                            type="string",
                            description="Final summary message describing what was accomplished",
                            required=False
                        )
                    ],
                    returns={
                        "type": "object",
                        "description": "Confirmation of task completion"
                    }
                )
                
                # Combine agent tools with finish tool
                if tool_definitions is None:
                    tool_definitions = []
                tool_definitions.append(finish_tool)
                
                # LLM call
                response = await self.llm_client.chat_completion(
                    messages=messages,
                    tools=tool_definitions if tool_definitions else None,
                    temperature=0.7
                )
                
                # Extract thought (content)
                thought = response["content"]
                if thought:
                    thoughts.append(thought)
                    self.state.thought = thought
                
                # Check for tool calls
                if response["tool_calls"]:
                    for tool_call_data in response["tool_calls"]:
                        # Display the tool call
                        print(f"\n🔧 Tool Call: {tool_call_data['name']}")
                        print(f"   Arguments: {json.dumps(tool_call_data.get('arguments', {}), indent=2)}")
                        
                        # Check if this is a special "finish" call
                        if tool_call_data["name"] == "finish":
                            # Agent is signaling completion
                            self._task_finished = True
                            self.state.status = "completed"
                            
                            # Create finish tool call and add to actions for logging
                            finish_call = create_tool_call(
                                tool_name="finish",
                                arguments=tool_call_data.get("arguments", {}),
                                agent_id=self.agent_id
                            )
                            actions.append(finish_call)
                            
                            # Extract final message from arguments if provided
                            final_message = tool_call_data.get("arguments", {}).get("message", thought)
                            
                            return {
                                "success": True,
                                "result": final_message or thought or "Task completed",
                                "thoughts": thoughts,
                                "actions": actions,
                                "observations": observations,
                                "iterations": iteration + 1,
                                "finished_early": True
                            }
                        
                        # Create tool call
                        tool_call = create_tool_call(
                            tool_name=tool_call_data["name"],
                            arguments=tool_call_data["arguments"],
                            agent_id=self.agent_id
                        )
                        actions.append(tool_call)
                        self.state.action = tool_call
                        self.state.status = "acting"
                        
                        # Execute tool
                        tool = self.tool_registry.get_tool(tool_call.tool_name)
                        tool_result = await tool.execute_with_result(
                            call_id=tool_call.call_id,
                            **tool_call.arguments
                        )
                        
                        # Format observation
                        if tool_result.status.value == "success":
                            observation = f"Tool '{tool_call.tool_name}' succeeded: {json.dumps(tool_result.output, indent=2)}"
                        else:
                            observation = f"Tool '{tool_call.tool_name}' failed: {tool_result.error}"
                        
                        observations.append(observation)
                        self.state.observation = observation
                        
                        # Add to messages for next iteration
                        messages.append({
                            "role": "assistant",
                            "content": thought if thought else f"Using tool: {tool_call.tool_name}"
                        })
                        messages.append({
                            "role": "tool",
                            "content": observation
                        })
                    
                    self.state.status = "thinking"
                    
                else:
                    # No more tool calls - task complete
                    self.state.status = "completed"
                    return {
                        "success": True,
                        "result": thought,
                        "thoughts": thoughts,
                        "actions": actions,
                        "observations": observations,
                        "iterations": iteration + 1
                    }
            
            except Exception as e:
                self.state.status = "error"
                return {
                    "success": False,
                    "error": str(e),
                    "thoughts": thoughts,
                    "actions": actions,
                    "observations": observations,
                    "iterations": iteration + 1
                }
        
        # Max iterations reached
        self.state.status = "completed"
        return {
            "success": True,
            "result": "Max iterations reached",
            "thoughts": thoughts,
            "actions": actions,
            "observations": observations,
            "iterations": self.max_iterations
        }
