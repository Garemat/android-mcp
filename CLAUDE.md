# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

A minimal MCP server (stdio transport) that wraps ADB to let AI agents control Android devices. Keep it simple — the value is in reliable, low-level primitives, not high-level automation logic.

## Commands

```bash
# Install in editable mode (do this once after cloning)
pip install -e .

# Run the server directly (useful for smoke-testing the binary)
android-mcp

# Run against a specific device
ANDROID_SERIAL=emulator-5554 android-mcp
```

There are no unit tests yet. Manual testing against a running emulator is the current approach.

## Architecture

Three files, each with a single responsibility:

- **`adb.py`** — thin wrappers around `adb` subprocess calls. Each function maps 1:1 to an ADB command. No business logic here.
- **`ui.py`** — parses UIAutomator XML dumps into a `UIElement` dataclass tree. `to_text()` renders a compact readable hierarchy for the model. `find_all()` / `find_first()` search by text, content description, or resource ID.
- **`server.py`** — MCP server. Defines tool schemas in `list_tools()`, routes calls in `call_tool()`. Thin glue between MCP and `adb`/`ui`.

## Adding a new tool

1. Add a `Tool(...)` entry in `list_tools()` in `server.py` with name, description, and `inputSchema`.
2. Add an `elif name == "your_tool":` branch in `call_tool()`.
3. If you need a new ADB command, add a function to `adb.py` first, then call it from `server.py`.
4. Test manually: launch the server, connect an MCP client, call the tool.

## Guidelines

- **Keep `adb.py` pure.** Functions take args, call ADB, return output. No MCP types, no JSON, no tool logic.
- **Tool descriptions are read by the model.** Write them from the model's perspective — what it needs to know to decide when to use the tool and what the output means.
- **Errors surface as `isError=True` responses**, not exceptions. The `call_tool()` handler already wraps everything in a try/except — let it catch unexpected errors, but raise `RuntimeError` from `adb.py` for known failure modes (non-zero exit, device not found, etc.).
- **No new dependencies** without a strong reason. The only runtime dep is `mcp`. ADB gives us everything we need for device interaction.
- **Python 3.11+ only.** Use `str | None` union syntax, `match`, walrus operator freely — no need to support older versions.
