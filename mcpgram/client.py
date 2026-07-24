"""
MCPGRAM Python client (Platform) and Toolset.

Mirrors the JS SDK (@mcpgram/sdk) against the same two public endpoints:

    GET  /api/v1/tools?server=<name>   -- discover tools (use, for_langgraph, for_crewai)
    POST /api/v1/execute                -- run a tool (call)

Usage:
    client = Platform(api_key="mcpg_live_...", base_url="https://...")
    github = client.use("github")
    result = github.call("github_list_repos", {"per_page": 10})
"""

from typing import Any, Callable, Dict, List, Optional

import requests

from .errors import PlatformApiError
from .types import ExecuteResult, ToolDefinition

CallFn = Callable[[str, Dict[str, Any]], ExecuteResult]


class Toolset:
    """
    Result of Platform.use(name): a bundle of tools belonging to one or
    more matching connectors/MCP servers, plus a convenience call() that
    resolves a tool by name or ID within this bundle.
    """

    def __init__(self, query: str, tools: List[ToolDefinition], call_fn: CallFn):
        self.query = query
        self.tools = tools
        self._call_fn = call_fn
        self._by_id = {t.tool_id: t for t in tools}
        self._by_name = {t.name: t for t in tools}

    def call(self, tool_name_or_id: str, input: Optional[Dict[str, Any]] = None) -> ExecuteResult:
        input = input or {}
        tool = self._by_id.get(tool_name_or_id) or self._by_name.get(tool_name_or_id)
        if not tool:
            available = ", ".join(t.name for t in self.tools) or "(none)"
            raise ValueError(
                f'Tool "{tool_name_or_id}" not found in "{self.query}". Available tools: {available}'
            )
        return self._call_fn(tool.tool_id, input)

    def for_langgraph(self) -> List[Any]:
        """Returns this toolset's tools as LangChain StructuredTool instances, ready for LangGraph."""
        from .adapters.langgraph import build_langgraph_tools

        return build_langgraph_tools(self.tools, self._call_fn)

    def for_crewai(self) -> List[Any]:
        """Returns this toolset's tools as CrewAI BaseTool instances."""
        from .adapters.crewai import build_crewai_tools

        return build_crewai_tools(self.tools, self._call_fn)


class Platform:
    def __init__(self, api_key: str, base_url: str, timeout: float = 30.0):
        if not api_key:
            raise ValueError(
                "Platform requires an api_key. Create one from your workspace's API Keys page in the MCPGRAM dashboard."
            )
        if not base_url:
            raise ValueError(
                "Platform requires a base_url (e.g. the URL of your MCPGRAM deployment). There's no default yet."
            )
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()

    def _request(self, method: str, path: str, **kwargs) -> Any:
        res = self._session.request(
            method,
            f"{self._base_url}{path}",
            headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
            timeout=self._timeout,
            **kwargs,
        )
        try:
            body = res.json()
        except ValueError:
            body = None

        # 502 is a deliberate "tool ran but failed" response shape from
        # /api/v1/execute, not a transport-level failure -- let it through
        # so call() can return it as a normal ExecuteResult instead of raising.
        if not res.ok and res.status_code != 502:
            retry_after = res.headers.get("retry-after")
            raise PlatformApiError(
                (body or {}).get("error", f"Request to {path} failed with status {res.status_code}"),
                res.status_code,
                body,
                float(retry_after) * 1000 if retry_after else None,
            )
        return body

    def _list_tools(self, server_filter: Optional[str] = None) -> List[ToolDefinition]:
        query = f"?server={server_filter}" if server_filter else ""
        json = self._request("GET", f"/api/v1/tools{query}") or {}
        servers = json.get("servers", [])

        tools: List[ToolDefinition] = []
        for server in servers:
            for t in server.get("tools", []):
                tools.append(
                    ToolDefinition(
                        tool_id=t["tool_id"],
                        name=t["name"],
                        description=t.get("description", ""),
                        input_schema=t.get("input_schema") or {},
                    )
                )
        return tools

    def use(self, name: str) -> Toolset:
        """
        Resolve tools for a connector or MCP server by name
        (case-insensitive substring match against the server's display
        name, handled server-side). Raises if nothing matches.
        """
        tools = self._list_tools(name)
        if not tools:
            raise ValueError(
                f'No connected server or connector matches "{name}". Check the name against your workspace\'s dashboard.'
            )
        return Toolset(name, tools, self.call)

    def for_langgraph(self, server_filter: Optional[str] = None) -> List[Any]:
        """All (or scoped) workspace tools as LangChain StructuredTool instances, ready for LangGraph."""
        from .adapters.langgraph import build_langgraph_tools

        return build_langgraph_tools(self._list_tools(server_filter), self.call)

    def for_crewai(self, server_filter: Optional[str] = None) -> List[Any]:
        """All (or scoped) workspace tools as CrewAI BaseTool instances."""
        from .adapters.crewai import build_crewai_tools

        return build_crewai_tools(self._list_tools(server_filter), self.call)

    def call(self, tool_id: str, input: Optional[Dict[str, Any]] = None) -> ExecuteResult:
        """Directly execute a known tool_id (bypasses use() when you already have the ID)."""
        json = self._request("POST", "/api/v1/execute", json={"tool_id": tool_id, "input": input or {}}) or {}
        return ExecuteResult(status=json.get("status"), output=json.get("output"), error=json.get("error"))
