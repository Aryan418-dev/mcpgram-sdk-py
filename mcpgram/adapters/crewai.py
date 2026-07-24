"""
CrewAI adapter (Phase 3, step 5).

Converts MCPGRAM tool definitions into CrewAI BaseTool instances, ready
to hand to an Agent's `tools=[...]`. CrewAI tools are pydantic-backed
classes (name/description/args_schema class attrs + a _run method), so
each tool gets its own dynamically-built BaseTool subclass, closing over
its own tool_id for execution.

Requires crewai: pip install "mcpgram[crewai]"
"""

from typing import Any, Callable, Dict, List

from .._schema import json_schema_to_pydantic_model
from ..types import ExecuteResult, ToolDefinition


def build_crewai_tools(
    tools: List[ToolDefinition],
    call_fn: Callable[[str, Dict[str, Any]], ExecuteResult],
) -> List[Any]:
    try:
        from crewai.tools import BaseTool
    except ImportError as e:
        raise ImportError(
            'CrewAI support requires the crewai package. Install it with: pip install "mcpgram[crewai]"'
        ) from e

    crew_tools = []

    for tool in tools:
        args_schema = json_schema_to_pydantic_model(f"{tool.name}_Args", tool.input_schema)

        def make_run(bound_tool_id: str):
            def _run(self, **kwargs) -> str:
                result = call_fn(bound_tool_id, kwargs)
                if result.status == "error":
                    return f"Error: {result.error}"
                return str(result.output)

            return _run

        DynamicTool = type(
            f"MCPGRAM_{tool.name}",
            (BaseTool,),
            {
                "name": tool.name,
                "description": tool.description,
                "args_schema": args_schema,
                "_run": make_run(tool.tool_id),
            },
        )

        crew_tools.append(DynamicTool())

    return crew_tools
