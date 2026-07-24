"""
Shared types for the MCPGRAM SDK. These mirror the JSON shapes returned
by GET /api/v1/tools and POST /api/v1/execute — see mcpgram-dashboard's
app/api/v1/tools/route.ts and app/api/v1/execute/route.ts for the
server-side source of truth. Kept in sync with @mcpgram/sdk's (JS) types.ts.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ToolDefinition:
    tool_id: str
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class ExecuteResult:
    status: Optional[str]  # "success" | "error" | None
    output: Any
    error: Optional[str]
