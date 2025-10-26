"""
Tool Registry
Manages all available tools in the system
"""
from typing import Dict, List
from pathlib import Path
from src.tools.base import BaseTool
from src.tools.web_search import WebSearchTool
from src.tools.file_tools import (
    FileSaverTool,
    FileSystemScannerTool,
    FindInFileTool
)
from src.tools.finance_data import FinanceDataDownloaderTool
from src.tools.python_sandbox import PythonExecutionTool
from src.tools.strategy_evaluation import RegressionBasedStrategyEvaluationTool
from src.mcp.protocol import ToolDefinition


class ToolRegistry:
    """Registry of all available tools"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.tools: Dict[str, BaseTool] = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all tools"""
        # Information gathering
        self.tools["web_search"] = WebSearchTool()
        
        # File system
        self.tools["file_saver"] = FileSaverTool(self.workspace_root)
        self.tools["file_system_scanner"] = FileSystemScannerTool(self.workspace_root)
        self.tools["find_in_file"] = FindInFileTool(self.workspace_root)
        
        # Financial data
        self.tools["finance_data_downloader"] = FinanceDataDownloaderTool(self.workspace_root)
        
        # Python execution
        self.tools["python_execution"] = PythonExecutionTool(self.workspace_root)
        
        # Strategy evaluation
        self.tools["regression_based_strategy_evaluation"] = RegressionBasedStrategyEvaluationTool(
            self.workspace_root
        )
    
    def get_tool(self, name: str) -> BaseTool:
        """Get tool by name"""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")
        return self.tools[name]
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all tools"""
        return self.tools
    
    def get_tool_definitions(
        self,
        tool_names: List[str] = None
    ) -> List[ToolDefinition]:
        """Get tool definitions for specified tools or all tools"""
        if tool_names is None:
            tool_names = list(self.tools.keys())
        
        return [
            self.tools[name].get_definition()
            for name in tool_names
            if name in self.tools
        ]
    
    def get_tools_for_agent(self, agent_type: str) -> List[str]:
        """Get list of tool names available to a specific agent type"""
        tool_mapping = {
            "orchestrator": ["file_system_scanner"],
            "planner": [],  # Pure reasoning, no tools
            "executor": [
                "web_search",
                "file_saver",
                "find_in_file",
                "finance_data_downloader",
                "python_execution",
                "regression_based_strategy_evaluation"
            ],
            "strategy_synthesizer": ["file_saver"],
            "strategy_evaluator": [
                "python_execution",
                "regression_based_strategy_evaluation",
                "file_saver"
            ],
            "judger": ["find_in_file"],
            "writer": ["find_in_file", "file_saver"]
        }
        
        return tool_mapping.get(agent_type, [])
