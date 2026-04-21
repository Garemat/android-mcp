import asyncio
import time
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, TextContent, ImageContent,
    CallToolResult, ListToolsResult,
)
from . import adb, ui

server = Server("android-mcp")

KEYCODES = {
    "back": 4, "home": 3, "menu": 82, "enter": 66,
    "delete": 67, "tab": 61, "up": 19, "down": 20,
    "left": 21, "right": 22, "volume_up": 24, "volume_down": 25,
    "power": 26, "camera": 27, "search": 84,
}


@server.list_tools()
async def list_tools() -> ListToolsResult:
    return ListToolsResult(tools=[
        Tool(
            name="list_devices",
            description="List connected Android devices and emulators.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="screenshot",
            description="Take a screenshot of the device screen. Returns an image.",
            inputSchema={
                "type": "object",
                "properties": {
                    "device": {"type": "string", "description": "Device serial (omit for default)"},
                },
            },
        ),
        Tool(
            name="get_ui_hierarchy",
            description=(
                "Dump the current UI as a readable hierarchy showing all visible elements, "
                "their labels, resource IDs, whether they're tappable, and their screen coordinates. "
                "Use this to understand what's on screen before deciding where to tap."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "device": {"type": "string"},
                },
            },
        ),
        Tool(
            name="tap",
            description="Tap at specific screen coordinates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "device": {"type": "string"},
                },
                "required": ["x", "y"],
            },
        ),
        Tool(
            name="tap_element",
            description=(
                "Find a UI element by text or resource ID and tap its centre. "
                "Prefer this over tap() when you know the label or ID of what you want to tap."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Visible text on the element"},
                    "content_desc": {"type": "string", "description": "Accessibility content description"},
                    "resource_id": {"type": "string", "description": "Resource ID (partial match)"},
                    "device": {"type": "string"},
                },
            },
        ),
        Tool(
            name="swipe",
            description="Swipe from one point to another.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x1": {"type": "integer"},
                    "y1": {"type": "integer"},
                    "x2": {"type": "integer"},
                    "y2": {"type": "integer"},
                    "duration_ms": {"type": "integer", "default": 300},
                    "device": {"type": "string"},
                },
                "required": ["x1", "y1", "x2", "y2"],
            },
        ),
        Tool(
            name="type_text",
            description="Type text into the currently focused input field.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "device": {"type": "string"},
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="press_key",
            description=(
                f"Press a hardware key. Available keys: {', '.join(KEYCODES.keys())}."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "enum": list(KEYCODES.keys())},
                    "device": {"type": "string"},
                },
                "required": ["key"],
            },
        ),
        Tool(
            name="launch_app",
            description="Launch an app by package name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "package": {"type": "string", "description": "e.g. io.github.garemat.lunachron"},
                    "device": {"type": "string"},
                },
                "required": ["package"],
            },
        ),
        Tool(
            name="stop_app",
            description="Force-stop an app by package name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "package": {"type": "string"},
                    "device": {"type": "string"},
                },
                "required": ["package"],
            },
        ),
        Tool(
            name="install_apk",
            description="Install an APK onto the device.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Local path to the APK file"},
                    "device": {"type": "string"},
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="get_logcat",
            description="Get recent device logs. Useful for spotting crashes or errors after an action.",
            inputSchema={
                "type": "object",
                "properties": {
                    "lines": {"type": "integer", "default": 100},
                    "tag": {"type": "string", "description": "Filter to a specific log tag"},
                    "device": {"type": "string"},
                },
            },
        ),
        Tool(
            name="wait",
            description="Wait for a specified number of seconds (e.g. for animations or loading).",
            inputSchema={
                "type": "object",
                "properties": {
                    "seconds": {"type": "number"},
                },
                "required": ["seconds"],
            },
        ),
        Tool(
            name="get_device_info",
            description="Get screen size, Android version, and installed app version.",
            inputSchema={
                "type": "object",
                "properties": {
                    "package": {"type": "string", "description": "Optional: get version of this app"},
                    "device": {"type": "string"},
                },
            },
        ),
    ])


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    device = arguments.get("device")
    try:
        if name == "list_devices":
            devices = adb.get_devices()
            if not devices:
                return CallToolResult(content=[TextContent(type="text", text="No devices connected.")])
            lines = [f"- {d['serial']}" + (f" ({d.get('model', '')})" if d.get("model") else "") for d in devices]
            return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])

        elif name == "screenshot":
            b64 = adb.screenshot(device)
            return CallToolResult(content=[ImageContent(type="image", data=b64, mimeType="image/png")])

        elif name == "get_ui_hierarchy":
            xml = adb.ui_dump(device)
            root = ui.parse(xml)
            text = ui.to_text(root)
            return CallToolResult(content=[TextContent(type="text", text=text)])

        elif name == "tap":
            adb.tap(arguments["x"], arguments["y"], device)
            return CallToolResult(content=[TextContent(type="text", text=f"Tapped ({arguments['x']}, {arguments['y']}).")])

        elif name == "tap_element":
            xml = adb.ui_dump(device)
            root = ui.parse(xml)
            element = ui.find_first(
                root,
                text=arguments.get("text"),
                content_desc=arguments.get("content_desc"),
                resource_id=arguments.get("resource_id"),
            )
            if not element:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"No element found matching {arguments}.")],
                    isError=True,
                )
            cx, cy = element.center
            adb.tap(cx, cy, device)
            return CallToolResult(content=[TextContent(type="text", text=f"Tapped '{element}' at ({cx}, {cy}).")])

        elif name == "swipe":
            adb.swipe(arguments["x1"], arguments["y1"], arguments["x2"], arguments["y2"],
                      arguments.get("duration_ms", 300), device)
            return CallToolResult(content=[TextContent(type="text", text="Swiped.")])

        elif name == "type_text":
            adb.input_text(arguments["text"], device)
            return CallToolResult(content=[TextContent(type="text", text=f"Typed: {arguments['text']!r}")])

        elif name == "press_key":
            key = arguments["key"]
            adb.press_keyevent(KEYCODES[key], device)
            return CallToolResult(content=[TextContent(type="text", text=f"Pressed {key}.")])

        elif name == "launch_app":
            adb.launch_app(arguments["package"], device)
            return CallToolResult(content=[TextContent(type="text", text=f"Launched {arguments['package']}.")])

        elif name == "stop_app":
            adb.stop_app(arguments["package"], device)
            return CallToolResult(content=[TextContent(type="text", text=f"Stopped {arguments['package']}.")])

        elif name == "install_apk":
            result = adb.install_apk(arguments["path"], device)
            return CallToolResult(content=[TextContent(type="text", text=result)])

        elif name == "get_logcat":
            logs = adb.get_logcat(arguments.get("lines", 100), arguments.get("tag"), device)
            return CallToolResult(content=[TextContent(type="text", text=logs)])

        elif name == "wait":
            await asyncio.sleep(arguments["seconds"])
            return CallToolResult(content=[TextContent(type="text", text=f"Waited {arguments['seconds']}s.")])

        elif name == "get_device_info":
            w, h = adb.get_screen_size(device)
            version = adb.get_android_version(device)
            info = [f"Screen: {w}x{h}", f"Android: {version}"]
            if pkg := arguments.get("package"):
                info.append(f"App version: {adb.get_package_version(pkg, device)}")
            return CallToolResult(content=[TextContent(type="text", text="\n".join(info))])

        else:
            return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {name}")], isError=True)

    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=str(e))], isError=True)


def main():
    asyncio.run(_main())


async def _main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    main()
