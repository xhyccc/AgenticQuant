"""
File System Tools
"""
from typing import Any, List, Dict, Optional
from src.tools.base import BaseTool
from src.mcp.protocol import ToolDefinition, ToolParameter
from pathlib import Path
import json
import os
import aiofiles


class FileSaverTool(BaseTool):
    """Save content to a file"""
    
    def __init__(self, workspace_root: Path):
        super().__init__()
        self.name = "file_saver"
        self.workspace_root = workspace_root
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=(
                "Writes content to a workspace file. Creates parent directories if needed. "
                "Optionally appends when the target file already exists. When saving iterative "
                "artifacts within the same session, prefer versioned filenames (e.g., v1, v2) "
                "so previous outputs remain accessible."
            ),
            parameters=[
                ToolParameter(
                    name="filename",
                    type="string",
                    description="The name of the file (can include subdirectories)",
                    required=True
                ),
                ToolParameter(
                    name="content",
                    type="string",
                    description="The content to write to the file",
                    required=True
                ),
                ToolParameter(
                    name="append",
                    type="boolean",
                    description="Set to true to append to the file when it already exists",
                    required=False,
                    default=False
                )
            ],
            returns={
                "type": "object",
                "description": "File path and success status"
            }
        )
    
    async def execute(
        self,
        filename: str,
        content: str,
        append: bool = False
    ) -> Dict[str, Any]:
        """Save content to file"""
        try:
            # Clean the filename to prevent nested workspaces
            # Remove any absolute path prefixes or workspace directory references
            clean_filename = filename
            if filename.startswith('/'):
                clean_filename = filename.lstrip('/')
            
            # Remove any "workspaces/..." prefix that might cause nesting
            parts = Path(clean_filename).parts
            if parts and parts[0] == 'workspaces':
                clean_filename = str(Path(*parts[1:]))  # Skip the first "workspaces" part
            
            file_path = self.workspace_root / clean_filename
            
            # Ensure we're not creating paths outside workspace
            try:
                file_path.relative_to(self.workspace_root)
            except ValueError:
                raise Exception(f"Invalid file path: attempting to write outside workspace")
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            mode = 'a' if append else 'w'

            async with aiofiles.open(file_path, mode, encoding='utf-8') as f:
                await f.write(content)
                if append:
                    await f.flush()
            
            return {
                "result": {
                    "file_path": str(file_path),
                    "size_bytes": len(content.encode('utf-8')),
                    "success": True,
                    "append": append
                },
                "artifacts": [str(file_path)]
            }
        except Exception as e:
            raise Exception(f"Failed to save file: {str(e)}")


class FileSystemScannerTool(BaseTool):
    """Scan directory and list all files"""
    
    def __init__(self, workspace_root: Path):
        super().__init__()
        self.name = "file_system_scanner"
        self.workspace_root = workspace_root
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description="Scans the current working directory and returns a list of all files with their metadata (name, size, modification time).",
            parameters=[],
            returns={
                "type": "array",
                "description": "List of files with metadata"
            }
        )
    
    async def execute(self) -> List[Dict[str, Any]]:
        """Scan directory"""
        try:
            files = []
            
            for root, _, filenames in os.walk(self.workspace_root):
                for filename in filenames:
                    file_path = Path(root) / filename
                    stat = file_path.stat()
                    
                    # Get relative path from workspace root
                    rel_path = file_path.relative_to(self.workspace_root)
                    
                    files.append({
                        "name": str(rel_path),
                        "size_bytes": stat.st_size,
                        "modified_time": stat.st_mtime,
                        "is_directory": False
                    })
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x["modified_time"], reverse=True)
            
            return files
        except Exception as e:
            raise Exception(f"Failed to scan directory: {str(e)}")


class FindInFileTool(BaseTool):
    """Search for content within a file"""
    
    def __init__(self, workspace_root: Path):
        super().__init__()
        self.name = "find_in_file"
        self.workspace_root = workspace_root
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description="Search for specific content within a local file using keywords or patterns. Returns matching lines with context.",
            parameters=[
                ToolParameter(
                    name="filename",
                    type="string",
                    description="The name of the file to search in",
                    required=True
                ),
                ToolParameter(
                    name="query",
                    type="string",
                    description="The search query (keywords or regex pattern)",
                    required=True
                ),
                ToolParameter(
                    name="context_lines",
                    type="integer",
                    description="Number of context lines to include before/after match (default: 2)",
                    required=False,
                    default=2
                )
            ],
            returns={
                "type": "object",
                "description": "Matching content with line numbers and context"
            }
        )
    
    async def execute(
        self,
        filename: str,
        query: str,
        context_lines: int = 2
    ) -> Dict[str, Any]:
        """Search in file"""
        try:
            file_path = self.workspace_root / filename
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {filename}")
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            lines = content.split('\n')
            matches = []
            
            for i, line in enumerate(lines):
                if query.lower() in line.lower():
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    
                    matches.append({
                        "line_number": i + 1,
                        "matched_line": line,
                        "context": lines[start:end]
                    })
            
            return {
                "filename": filename,
                "query": query,
                "total_matches": len(matches),
                "matches": matches
            }
        except Exception as e:
            raise Exception(f"Failed to search file: {str(e)}")
