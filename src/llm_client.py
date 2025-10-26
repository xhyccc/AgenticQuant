"""
LLM Client with support for multiple providers
"""
from typing import List, Dict, Any, Optional, Callable
import openai
from anthropic import Anthropic
from src.config import config
from src.mcp.protocol import ToolDefinition
import json
import requests
import asyncio
import logging
import re

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client supporting multiple providers"""
    
    def __init__(
        self,
        provider: str = None,
        model: str = None,
        api_key: str = None
    ):
        self.provider = provider or config.DEFAULT_LLM_PROVIDER
        self.model = model or config.DEFAULT_MODEL
        
        if self.provider == "openai":
            self.api_key = api_key or config.OPENAI_API_KEY
            openai.api_key = self.api_key
            self.client = openai
        elif self.provider == "anthropic":
            self.api_key = api_key or config.ANTHROPIC_API_KEY
            self.client = Anthropic(api_key=self.api_key)
        elif self.provider == "siliconflow":
            self.api_key = api_key or config.SILICONFLOW_API_KEY
            self.api_endpoint = config.SILICONFLOW_API_ENDPOINT
            self.client = None  # We'll use requests directly
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _convert_tools_to_openai_format(
        self,
        tools: List[ToolDefinition]
    ) -> List[Dict[str, Any]]:
        """Convert MCP tool definitions to OpenAI function format"""
        openai_tools = []
        for tool in tools:
            properties = {}
            required = []
            
            for param in tool.parameters:
                prop = {
                    "type": param.type,
                    "description": param.description
                }
                if param.enum:
                    prop["enum"] = param.enum
                if param.default is not None:
                    prop["default"] = param.default
                
                properties[param.name] = prop
                if param.required:
                    required.append(param.name)
            
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties
                    }
                }
            }
            
            # Only add required if not empty (some APIs require this field to be present or absent, not empty)
            if required:
                tool_def["function"]["parameters"]["required"] = required
            
            openai_tools.append(tool_def)
        
        return openai_tools
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate chat completion with optional tool calling
        
        Returns:
            {
                "content": str,
                "tool_calls": [{"name": str, "arguments": dict}],
                "finish_reason": str
            }
        """
        if max_tokens is None:
            max_tokens = config.LLM_MAX_TOKENS

        if self.provider == "openai":
            return await self._openai_completion(
                messages, tools, temperature, max_tokens
            )
        elif self.provider == "anthropic":
            return await self._anthropic_completion(
                messages, tools, temperature, max_tokens
            )
        elif self.provider == "siliconflow":
            return await self._siliconflow_completion(
                messages, tools, temperature, max_tokens
            )
    
    async def _openai_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolDefinition]],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """OpenAI completion"""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if tools:
            kwargs["tools"] = self._convert_tools_to_openai_format(tools)
            kwargs["tool_choice"] = "auto"
        
        response = self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        
        logger.info(f"LLM response (OpenAI): {message.content[:50]}")
        result = {
            "content": message.content or "",
            "tool_calls": [],
            "finish_reason": response.choices[0].finish_reason
        }
        
        if message.tool_calls:
            for tool_call in message.tool_calls:
                result["tool_calls"].append({
                    "name": tool_call.function.name,
                    "arguments": json.loads(tool_call.function.arguments)
                })
        
        return result
    
    async def _anthropic_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolDefinition]],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Anthropic completion"""
        # Extract system message if present
        system_message = None
        if messages and messages[0]["role"] == "system":
            system_message = messages[0]["content"]
            messages = messages[1:]
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if system_message:
            kwargs["system"] = system_message
        
        # Note: Anthropic has different tool calling format
        # For simplicity, we'll implement basic version
        # Production would need full Anthropic tools API
        
        response = self.client.messages.create(**kwargs)
        
        logger.info(f"LLM response (Anthropic): {(response.content[0].text if response.content else '')[:50]}")
        result = {
            "content": response.content[0].text if response.content else "",
            "tool_calls": [],
            "finish_reason": response.stop_reason
        }
        
        return result
    
    async def _siliconflow_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolDefinition]],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """SiliconFlow completion (OpenAI-compatible API with text-based tool calling fallback)"""
        import asyncio
        import re
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # For DeepSeek models that don't support tool calling API,
        # we'll use text-based tool calling instead
        use_text_based_tools = "deepseek" in self.model.lower() and tools
        
        # Convert any "tool" role messages to "user" role for compatibility
        # Many models don't support the "tool" role
        modified_messages = []
        for msg in messages:
            if msg.get("role") == "tool":
                modified_messages.append({
                    "role": "user",
                    "content": f"[Tool Result]\n{msg['content']}"
                })
            else:
                modified_messages.append(msg)
        
        payload = {
            "model": self.model,
            "messages": modified_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        if use_text_based_tools:
            # Add tool descriptions to the system message
            tool_descriptions = self._format_tools_as_text(tools)
            
            # Add tool calling instructions
            tool_instruction = f"""

You have access to the following tools. To use a tool, respond with JSON in this EXACT format:
```json
{{
  "action": "tool_call",
  "tool": "tool_name",
  "arguments": {{
    "arg1": "value1",
    "arg2": "value2"
  }}
}}
```

Available tools:
{tool_descriptions}

IMPORTANT: 
- Always use the exact JSON format shown above
- Put the JSON in a code block with ```json
- After using a tool, you'll receive the result and can continue reasoning
"""
            
            # Add to last user message or create system message
            if modified_messages and modified_messages[-1]["role"] == "user":
                modified_messages[-1]["content"] = modified_messages[-1]["content"] + tool_instruction
            
            payload["messages"] = modified_messages
            logger.debug(f"Using text-based tool calling for {len(tools)} tools")
            ##for tool in tools:
            ##   logger.debug(f" - {tool.name}: {tool.description}")
        else:
            # Try standard tool calling API (for models that support it)
            if tools:
                try:
                    openai_tools = self._convert_tools_to_openai_format(tools)
                    payload["tools"] = openai_tools
                    payload["tool_choice"] = "auto"
                    logger.debug(f"Using API-based tool calling for {len(tools)} tools")
                except Exception as e:
                    logger.warning(f"Could not format tools: {e}")
        
        # Make request
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    self.api_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=120
                )
            )
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
        
        if response.status_code != 200:
            error_detail = response.text
            logger.error(f"SiliconFlow API error {response.status_code}: {error_detail}")
            
            # If tool calling API failed and we haven't tried text-based yet
            if response.status_code == 400 and tools and not use_text_based_tools:
                logger.warning("API tool calling failed, retrying with text-based approach")
                return await self._siliconflow_completion(
                    messages, tools, temperature, max_tokens
                )
            
            raise Exception(f"SiliconFlow API error: {response.status_code} - {error_detail}")
        
        data = response.json()
        message = data["choices"][0]["message"]
        content = message.get("content") or ""
        
        logger.info(f"LLM response (SiliconFlow): {content[:50]}")
        result = {
            "content": content,
            "tool_calls": [],
            "finish_reason": data["choices"][0].get("finish_reason", "stop")
        }
        
        # Parse tool calls from API response (standard format)
        if message.get("tool_calls"):
            for tool_call in message["tool_calls"]:
                result["tool_calls"].append({
                    "name": tool_call["function"]["name"],
                    "arguments": json.loads(tool_call["function"]["arguments"])
                })
        
        # Parse text-based tool calls (for DeepSeek and others)
        elif use_text_based_tools and content:
            parsed_tools = self._parse_text_tool_calls(content)
            if parsed_tools:
                result["tool_calls"] = parsed_tools
                logger.debug(f"Parsed {len(parsed_tools)} tool calls from text response")
        
        return result
    
    def _format_tools_as_text(self, tools: List[ToolDefinition]) -> str:
        """Format tool definitions as human-readable text"""
        lines = []
        for tool in tools:
            lines.append(f"\n{tool.name}:")
            lines.append(f"  Description: {tool.description}")
            lines.append(f"  Parameters:")
            for param in tool.parameters:
                required = " (required)" if param.required else " (optional)"
                lines.append(f"    - {param.name} ({param.type}){required}: {param.description}")
        return "\n".join(lines)
    
    def _parse_text_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """Parse tool calls from text response in JSON format"""
        tool_calls = []
        
        # Look for JSON code blocks
        json_pattern = r'```json\s*(\{[\s\S]*?\})\s*```'
        matches = re.findall(json_pattern, content)
        
        for match in matches:
            try:
                data = json.loads(match)
                if data.get("action") == "tool_call" and "tool" in data and "arguments" in data:
                    tool_calls.append({
                        "name": data["tool"],
                        "arguments": data["arguments"]
                    })
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse tool call JSON: {e}")
                continue
        
        # Also look for plain JSON (without code blocks)
        if not tool_calls:
            try:
                # Try to find JSON object in the content
                json_obj_pattern = r'\{[^{}]*"action"\s*:\s*"tool_call"[^{}]*\}'
                matches = re.findall(json_obj_pattern, content)
                for match in matches:
                    data = json.loads(match)
                    if "tool" in data and "arguments" in data:
                        tool_calls.append({
                            "name": data["tool"],
                            "arguments": data["arguments"]
                        })
            except:
                pass
        
        return tool_calls


def get_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> LLMClient:
    """Factory function to get LLM client"""
    return LLMClient(provider=provider, model=model)
