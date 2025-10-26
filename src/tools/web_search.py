"""Web search tool using DuckDuckGo."""
from typing import List, Dict, Optional

from ddgs import DDGS

from src.tools.base import BaseTool
from src.mcp.protocol import ToolDefinition, ToolParameter

class WebSearchTool(BaseTool):
    """Search the web using DuckDuckGo."""
    
    def __init__(self):
        super().__init__()
        self.name = "web_search"
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=(
                "Searches the web using DuckDuckGo to collect up-to-date information on a topic. "
                "Returns titles, URLs, and snippets."
            ),
            parameters=[
                ToolParameter(
                    name="keywords",
                    type="string",
                    description="The search query keywords",
                    required=True
                ),
                ToolParameter(
                    name="max_results",
                    type="integer",
                    description="Maximum number of results to return (default: 10)",
                    required=False,
                    default=10
                ),
                ToolParameter(
                    name="timelimit",
                    type="string",
                    description="Time limit for results: 'd' (day), 'w' (week), 'm' (month), 'y' (year)",
                    required=False,
                    enum=["d", "w", "m", "y"]
                ),
                ToolParameter(
                    name="region",
                    type="string",
                    description="Region for search results (e.g., 'us-en', 'uk-en')",
                    required=False,
                    default="us-en"
                )
            ],
            returns={
                "type": "array",
                "description": "List of search results with title, url, and body"
            }
        )
    
    async def execute(
        self,
        keywords: str,
        max_results: int = 10,
        timelimit: Optional[str] = None,
        region: str = "us-en"
    ) -> List[Dict[str, str]]:
        """Execute web search"""
        try:
            return self._duckduckgo_search(
                keywords=keywords,
                max_results=max_results,
                timelimit=timelimit,
                region=region
            )
        except Exception as e:
            raise Exception(f"Web search failed: {str(e)}")

    def _duckduckgo_search(
        self,
        keywords: str,
        max_results: int,
        timelimit: Optional[str],
        region: str
    ) -> List[Dict[str, str]]:
        with DDGS() as ddgs:
            results = []
            search_kwargs = {
                "keywords": keywords,
                "region": region,
                "max_results": max_results
            }

            if timelimit:
                search_kwargs["timelimit"] = timelimit

            for result in ddgs.text(**search_kwargs):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", "")
                })

            return results
