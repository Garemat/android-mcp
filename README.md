# android-mcp

An [MCP](https://modelcontextprotocol.io) server that lets Claude (and other MCP clients) control Android devices and emulators via ADB.

## What it does

Exposes 14 tools over stdio so an AI agent can interact with a connected Android device as a user would — taking screenshots, reading the UI hierarchy, tapping elements, swiping, typing text, launching apps, and reading logs.

## Requirements

- Python 3.11+
- `adb` on your PATH (part of [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools))
- A connected Android device or running emulator

## Installation

```bash
pip install adb-mcp
```

Or directly from GitHub (useful before the first PyPI release lands):

```bash
pip install git+https://github.com/Garemat/android-mcp.git
```

Or from a local clone:

```bash
git clone https://github.com/Garemat/android-mcp
cd android-mcp
pip install -e .
```

## Usage with Claude Code

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "android": {
      "command": "android-mcp",
      "args": []
    }
  }
}
```

Claude Code will pick this up automatically on next launch. All 14 tools will be available in the conversation.

## Usage with other MCP clients

The server speaks the MCP stdio transport. Point your client at:

```
android-mcp
```

## Tools

| Tool | Description |
|------|-------------|
| `list_devices` | List connected devices and emulators |
| `screenshot` | Take a screenshot — returns a PNG image |
| `get_ui_hierarchy` | Dump the current screen as a readable element tree with labels, IDs, tap targets, and coordinates |
| `tap` | Tap at specific screen coordinates |
| `tap_element` | Find a UI element by text, content description, or resource ID and tap its centre |
| `swipe` | Swipe from one point to another |
| `type_text` | Type text into the focused input field |
| `press_key` | Press a hardware key (`back`, `home`, `enter`, `volume_up`, etc.) |
| `launch_app` | Launch an app by package name |
| `stop_app` | Force-stop an app by package name |
| `install_apk` | Install an APK from a local path |
| `get_logcat` | Get recent device logs, optionally filtered by tag |
| `wait` | Wait for a number of seconds |
| `get_device_info` | Get screen size, Android version, and optionally an app's version |

## Multi-device

All tools accept an optional `device` parameter (ADB serial). Omit it to use the default device when only one is connected.

```
list_devices          → emulator-5554, emulator-5556
screenshot device=emulator-5556
```

## Project structure

```
src/android_mcp/
  server.py   — MCP server, tool definitions, request routing
  adb.py      — ADB wrappers (subprocess calls, output parsing)
  ui.py       — UIAutomator XML parser → UIElement tree + text renderer
```

## Licence

MIT
