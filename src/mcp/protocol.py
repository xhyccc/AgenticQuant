"""
Model Context Protocol (MCP) Implementation
Standardized communication protocol for agent-tool interaction
"""
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message roles in MCP"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCallStatus(str, Enum):
    """Status of tool execution"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


class MCPMessage(BaseModel):
    """Base MCP message structure"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolParameter(BaseModel):
    """Tool parameter definition"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[str]] = None


class ToolDefinition(BaseModel):
    """MCP-compliant tool definition"""
    name: str
    description: str
    parameters: List[ToolParameter]
    returns: Dict[str, str]  # {"type": "string", "description": "..."}


class ToolCall(BaseModel):
    """Tool call request"""
    tool_name: str
    arguments: Dict[str, Any]
    call_id: str = Field(default_factory=lambda: f"call_{datetime.utcnow().timestamp()}")
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ToolResult(BaseModel):
    """Tool execution result"""
    call_id: str
    status: ToolCallStatus
    output: Optional[Any] = None
    error: Optional[str] = None
    artifacts: List[str] = Field(default_factory=list)  # File paths created
    execution_time_ms: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentState(BaseModel):
    """Agent execution state"""
    agent_id: str
    agent_type: str  # orchestrator, planner, executor, etc.
    status: Literal["idle", "thinking", "acting", "waiting", "error", "completed"]
    current_task: Optional[str] = None
    thought: Optional[str] = None  # ReAct thought
    action: Optional[ToolCall] = None  # ReAct action
    observation: Optional[str] = None  # ReAct observation
    workspace_path: str
    context: List[MCPMessage] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowPlan(BaseModel):
    """Structured plan from Planner agent"""
    plan_id: str
    user_request: str
    steps: List[Dict[str, Any]]  # [{"step_number": 1, "objective": "...", "required_tools": [...]}]
    estimated_duration_minutes: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MCPContext(BaseModel):
    """Complete context for an MCP session"""
    session_id: str
    workspace_path: str
    user_request: str
    plan: Optional[WorkflowPlan] = None
    agents_state: Dict[str, AgentState] = Field(default_factory=dict)
    message_history: List[MCPMessage] = Field(default_factory=list)
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tool_results: List[ToolResult] = Field(default_factory=list)
    artifacts: List[str] = Field(default_factory=list)
    status: Literal["initializing", "planning", "executing", "refining", "reporting", "completed", "failed"]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


def create_mcp_message(
    role: MessageRole,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> MCPMessage:
    """Helper to create MCP message"""
    return MCPMessage(
        role=role,
        content=content,
        metadata=metadata or {}
    )


def create_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    agent_id: str
) -> ToolCall:
    """Helper to create tool call"""
    return ToolCall(
        tool_name=tool_name,
        arguments=arguments,
        agent_id=agent_id
    )


def create_tool_result(
    call_id: str,
    status: ToolCallStatus,
    output: Optional[Any] = None,
    error: Optional[str] = None,
    artifacts: Optional[List[str]] = None
) -> ToolResult:
    """Helper to create tool result"""
    return ToolResult(
        call_id=call_id,
        status=status,
        output=output,
        error=error,
        artifacts=artifacts or []
    )
