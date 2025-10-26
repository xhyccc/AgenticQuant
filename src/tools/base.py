"""
Base Tool Interface
All tools implement this interface for MCP compliance
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from src.mcp.protocol import ToolDefinition, ToolResult, ToolCallStatus
import time


class BaseTool(ABC):
    """Base class for all tools"""
    
    def __init__(self):
        self.name = self.__class__.__name__.lower()
    
    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """Return MCP-compliant tool definition"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given arguments"""
        pass
    
    async def execute_with_result(
        self,
        call_id: str,
        **kwargs
    ) -> ToolResult:
        """
        Execute tool and wrap result in ToolResult
        """
        start_time = time.time()
        
        try:
            output = await self.execute(**kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            # Extract artifacts if present
            artifacts = []
            if isinstance(output, dict) and "artifacts" in output:
                artifacts = output["artifacts"]
                output = output.get("result", output)
            
            return ToolResult(
                call_id=call_id,
                status=ToolCallStatus.SUCCESS,
                output=output,
                artifacts=artifacts,
                execution_time_ms=execution_time
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolResult(
                call_id=call_id,
                status=ToolCallStatus.ERROR,
                error=str(e),
                execution_time_ms=execution_time
            )
