# ⚠️ ARCHIVED — use the canonical Python SDK

**This repository is a duplicate and should not receive new work.**

The official Python SDK lives at:

**https://github.com/Aryan418-dev/mcpgram-python-sdk**

```bash
# Install from the canonical repo (until published to PyPI)
pip install git+https://github.com/Aryan418-dev/mcpgram-python-sdk.git
```

## Why two repos existed

`mcpgram-sdk-py` and `mcpgram-python-sdk` were both created within ~2 hours
on 2026-07-24, both claiming LangGraph + CrewAI adapters. They diverged:

| | **mcpgram-sdk-py** (this repo) | **mcpgram-python-sdk** (canonical) |
|---|---|---|
| Layout | root `mcpgram/` package | `src/mcpgram/` |
| HTTP client | `requests` | `httpx` |
| Adapters | LangGraph, CrewAI only | LangGraph, CrewAI, Claude, OpenAI |
| Size | smaller | fuller client + formats layer |

**Canonical choice: `mcpgram-python-sdk`.**

This repo is retained only so existing clones/links do not 404. It will be
archived on GitHub when the settings API is applied.

See also the JS/TS SDK: https://github.com/Aryan418-dev/mcpgram-sdk
