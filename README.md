# mcpgram (Python)

Official Python SDK for **MCPGRAM** — one client for native connectors and external MCP servers, with adapters for **LangGraph** and **CrewAI**.

This is Phase 3, step 5. It mirrors `@mcpgram/sdk` (the JS package) against the same two REST endpoints, so both SDKs stay in sync by construction rather than by convention.

## Install

```bash
pip install mcpgram              # core client only
pip install "mcpgram[langgraph]" # + LangChain/LangGraph adapter
pip install "mcpgram[crewai]"    # + CrewAI adapter
```

(Not yet published to PyPI — this repo currently ships source only.)

## Usage

```python
from mcpgram import Platform

client = Platform(
    api_key="mcpg_live_...",   # from your workspace's API Keys page
    base_url="https://your-mcpgram-deployment.example.com",
)

github = client.use("github")
result = github.call("github_list_repos", {"per_page": 10})

if result.status == "success":
    print(result.output)
else:
    print("error:", result.error)
```

### LangGraph

```python
from langgraph.prebuilt import create_react_agent
from mcpgram import Platform

client = Platform(api_key="mcpg_live_...", base_url="https://...")
tools = client.use("github").for_langgraph()   # -> list[StructuredTool]

agent = create_react_agent(model, tools)
```

### CrewAI

```python
from crewai import Agent
from mcpgram import Platform

client = Platform(api_key="mcpg_live_...", base_url="https://...")
tools = client.use("github").for_crewai()      # -> list[BaseTool]

agent = Agent(role="Engineer", goal="...", backstory="...", tools=tools)
```

## How argument schemas work

Each tool's JSON Schema (from MCPGRAM's `/api/v1/tools`) is converted into a minimal pydantic model — enough to drive LangChain/CrewAI's own argument validation for common types (string/integer/number/boolean/array/object). More exotic schemas (nested `$ref`s, `oneOf`/`anyOf`) fall back to `Any` per-field rather than failing the whole tool; the real validation still happens server-side in `/api/v1/execute` either way.

## Error handling

- Network/auth/discovery errors raise `PlatformApiError` (`.status`, `.body`, `.retry_after_ms` on 429s).
- A tool that *ran* but failed resolves normally as `ExecuteResult(status="error", ...)` — in the LangGraph/CrewAI adapters this is surfaced to the agent as the string `"Error: ..."` rather than raising, so the agent can see and react to it instead of the whole chain crashing.

## Status

Mirrors `mcpgram-dashboard`'s `/api/v1/tools` and `/api/v1/execute` endpoints, and `mcpgram-sdk` (JS) for API shape. See those repos for the server-side/JS source of truth.
