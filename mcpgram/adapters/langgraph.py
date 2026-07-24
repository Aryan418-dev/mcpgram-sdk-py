"""
LangGraph adapter (Phase 3, step 5).

Converts MCPGRAM tool definitions into LangChain StructuredTool instances
— the same object LangGraph's create_react_agent() (and any other
LangChain-compatible agent) expects in its `tools=[...]` list. There's no
separate "LangGraph format" to target: LangGraph consumes LangChain tools
directly, so this adapter's whole job is producing a valid StructuredTool.

Requires langchain-core: pip install "mcpgram[langgraph]"
"""

from typing import Any, Callable, Dict, List

from .._schema import json_schema_to_pydantic_model
from ..types import ExecuteResult, ToolDefinition


def build_langgraph_tools(
    tools: List[ToolDefinition],
    call_fn: Callable[[str, Dict[str, Any]], ExecuteResult],
) -> List[Any]:
    try:
        from langchain_core.tools import StructuredTool
    except ImportError as e:
        raise ImportError(
            'LangGraph support requires langchain-core. Install it with: pip install "mcpgram[langgraph]"'
        ) from e

    structured_tools = []

    for tool in tools:
        args_schema = json_schema_to_pydantic_model(f"{tool.name}_Args", tool.input_schema)

        def make_fn(tool_id: str):
            def _fn(**kwargs) -> str:
                result = call_fn(tool_id, kwargs)
                if result.status == "error":
                    return f"Error: {result.error}"
                return str(result.output)

            return _fn

        structured_tools.append(
            StructuredTool.from_function(
                func=make_fn(tool.tool_id),
                name=tool.name,
                description=tool.description,
                args_schema=args_schema,
            )
        )

    return structured_tools
