"""
Minimal JSON Schema -> pydantic model conversion, shared by the
LangGraph and CrewAI adapters (both need a pydantic args_schema to hand
to their respective tool classes).

Supports the common primitive types our own connectors and most MCP
servers actually produce (string/integer/number/boolean/array/object).
Anything more exotic (nested $refs, oneOf/anyOf, etc.) falls back to Any
rather than failing the whole tool — a permissive fallback is safer here
than a strict one, since this only drives client-side validation, not the
actual execution (the real validation happens server-side in /api/v1/execute).
"""

from typing import Any, Dict, Optional, Type

from pydantic import Field, create_model

_TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def json_schema_to_pydantic_model(name: str, schema: Dict[str, Any]) -> Type:
    properties = (schema or {}).get("properties", {}) or {}
    required = set((schema or {}).get("required", []) or [])

    fields: Dict[str, Any] = {}
    for prop_name, prop_schema in properties.items():
        prop_schema = prop_schema or {}
        py_type = _TYPE_MAP.get(prop_schema.get("type"), Any)
        description = prop_schema.get("description", "")
        default = prop_schema.get("default")

        if prop_name in required:
            fields[prop_name] = (py_type, Field(..., description=description))
        else:
            fields[prop_name] = (Optional[py_type], Field(default, description=description))

    if not fields:
        # Zero-argument tool -- still needs a valid (empty) model.
        return create_model(name)

    return create_model(name, **fields)
