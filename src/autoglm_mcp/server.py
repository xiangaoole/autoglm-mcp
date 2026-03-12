#!/usr/bin/env python3
"""
AutoGLM MCP Server - Screen analysis API only, no action execution

Usage:
1. Install dependencies: pip install mcp openai pillow
2. Add this server to Claude Desktop config
3. Use the aiAsk tool via Claude to analyze phone screen

Note: Returned coordinates are pixel values converted from the model's
  relative scale (0-1000) using the actual screen resolution.
"""

import asyncio
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Please install mcp: pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("Please install openai: pip install openai", file=sys.stderr)
    sys.exit(1)

# ============ Configuration ============
BASE_URL = os.getenv("AUTOGLM_BASE_URL", "https://api.z.ai/api/paas/v4")
MODEL = os.getenv("AUTOGLM_MODEL", "autoglm-phone-multilingual")
APIKEY = os.getenv("AUTOGLM_APIKEY", "")

server = Server("autoglm-screen-analyzer")


# ============ System Prompt ============
def get_system_prompt() -> str:
    """Generate system prompt, consistent with phone_agent"""
    today = datetime.today()
    formatted_date = today.strftime("%Y-%m-%d, %A")

    return f"""The current date: {formatted_date}
# Setup
You are a professional Android operation agent assistant that can fulfill the user's high-level instructions. Given a screenshot of the Android interface at each step, you first analyze the situation, then plan the best course of action using Python-style pseudo-code.

# More details about the code
Your response format must be structured as follows:

Think first: Use <think>...</think> to analyze the current screen, identify key elements, and determine the most efficient action.
Provide the action: Use <answer>...</answer> to return a single line of pseudo-code representing the operation.

Your output should STRICTLY follow the format:
<think>
[Your thought]
</think>
<answer>
[Your operation code]
</answer>

- **Tap**
  Perform a tap action on a specified screen area. The element is a list of 2 integers, representing the coordinates of the tap point (0-1000 relative scale).
  **Example**:
  <answer>
  do(action="Tap", element=[x,y])
  </answer>
- **Type**
  Enter text into the currently focused input field.
  **Example**:
  <answer>
  do(action="Type", text="Hello World")
  </answer>
- **Swipe**
  Perform a swipe action with start point and end point.
  **Examples**:
  <answer>
  do(action="Swipe", start=[x1,y1], end=[x2,y2])
  </answer>
- **Long Press**
  Perform a long press action on a specified screen area.
  **Example**:
  <answer>
  do(action="Long Press", element=[x,y])
  </answer>
- **Launch**
  Launch an app.
  **Example**:
  <answer>
  do(action="Launch", app="Settings")
  </answer>
- **Back**
  Press the Back button to navigate to the previous screen.
  **Example**:
  <answer>
  do(action="Back")
  </answer>
- **Finish**
  Terminate the program and optionally print a message.
  **Example**:
  <answer>
  finish(message="Task completed.")
  </answer>

REMEMBER:
- You MUST respond in English only. However, keep UI text (buttons, labels, etc.) in their original language as shown on screen.
- Think before you act: Always analyze the current UI and the best course of action before executing any step.
- Only ONE LINE of action in <answer> part per response.
"""


# ============ ADB Utilities ============
def get_screenshot_with_info() -> str:
    """Get phone screenshot via ADB, returns base64 encoded image"""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        temp_path = f.name

    try:
        subprocess.run(
            ["adb", "shell", "screencap", "-p", "/sdcard/screenshot-autoglm.png"],
            check=True, capture_output=True
        )
        subprocess.run(
            ["adb", "pull", "/sdcard/screenshot-autoglm.png", temp_path],
            check=True, capture_output=True
        )

        with open(temp_path, "rb") as f:
            img_data = f.read()

        return base64.b64encode(img_data).decode("utf-8")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def get_current_app() -> str:
    """Get current foreground app package name"""
    try:
        result = subprocess.run(
            ["adb", "shell", "dumpsys", "activity", "activities"],
            capture_output=True, text=True, check=True
        )
        # Match mResumedActivity or topResumedActivity
        match = re.search(r'(?:mResumedActivity|topResumedActivity).*?(\S+)/\S+', result.stdout)
        if match:
            return match.group(1)
    except Exception:
        pass
    return "unknown"


def get_screen_size() -> tuple[int, int]:
    """Get phone screen resolution (width, height) via ADB"""
    try:
        result = subprocess.run(
            ["adb", "shell", "wm", "size"],
            capture_output=True, text=True, check=True
        )
        # Output format: "Physical size: 1080x2340"
        match = re.search(r'(\d+)x(\d+)', result.stdout)
        if match:
            return int(match.group(1)), int(match.group(2))
    except Exception:
        pass
    return 1080, 1920  # fallback default


def convert_coords_to_pixels(text: str, screen_width: int, screen_height: int) -> str:
    """Convert all 1000-based coordinates in text to pixel coordinates.

    Supported formats:
      - [x,y]       two integers  comma-separated  → point
      - [x1,y1,x2,y2] four integers comma-separated → rectangle
      - [x.y]       two integers  dot-separated     → point
      - [x1.y1.x2.y2] four integers dot-separated   → rectangle
    """

    def _to_pixel(val: int, is_x: bool) -> int:
        base = screen_width if is_x else screen_height
        return int(val / 1000 * base)

    def _replace_comma(m: re.Match) -> str:
        nums = [int(n) for n in m.group(1).split(",")]
        if len(nums) == 2:
            px = [_to_pixel(nums[0], True), _to_pixel(nums[1], False)]
        elif len(nums) == 4:
            px = [
                _to_pixel(nums[0], True), _to_pixel(nums[1], False),
                _to_pixel(nums[2], True), _to_pixel(nums[3], False),
            ]
        else:
            return m.group(0)  # leave unchanged
        return "[" + ",".join(str(v) for v in px) + "]"

    def _replace_dot(m: re.Match) -> str:
        nums = [int(n) for n in m.group(1).split(".")]
        if len(nums) == 2:
            px = [_to_pixel(nums[0], True), _to_pixel(nums[1], False)]
        elif len(nums) == 4:
            px = [
                _to_pixel(nums[0], True), _to_pixel(nums[1], False),
                _to_pixel(nums[2], True), _to_pixel(nums[3], False),
            ]
        else:
            return m.group(0)  # leave unchanged
        return "[" + ",".join(str(v) for v in px) + "]"

    # Match comma-separated: [123,456] or [1,2,3,4]
    text = re.sub(
        r'\[(\d+,\d+(?:,\d+,\d+)?)\]',
        _replace_comma,
        text,
    )

    # Match dot-separated: [123.456] or [1.2.3.4]
    text = re.sub(
        r'\[(\d+\.\d+(?:\.\d+\.\d+)?)\]',
        _replace_dot,
        text,
    )

    return text


# ============ Tool Definitions ============
@server.list_tools()
async def list_tools():
    """List available tools"""
    return [
        Tool(
            name="aiAsk",
            description="""Analyze current Android phone screen, identify UI elements and return coordinates.

Response format:
- <think>...</think> Analysis process
- <answer>do(action="Tap", element=[x,y])</answer> Action suggestion

Example questions:
- "What coordinates to click the search button?"
- "How to click the settings icon?"
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question about the screen, e.g., 'Where is the search button?'"
                    }
                },
                "required": ["question"]
            }
        ),
    ]


# ============ Tool Implementation ============
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute tool call"""
    if name == "aiAsk":
        return await ai_ask(arguments.get("question", ""))
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ============ AI Screen Analysis ============
async def ai_ask(question: str):
    """Call AutoGLM API to analyze screen"""

    if not APIKEY:
        return [TextContent(type="text", text="Error: AUTOGLM_APIKEY environment variable not set")]

    if not question:
        return [TextContent(type="text", text="Error: Question cannot be empty")]

    loop = asyncio.get_event_loop()

    def run_request():
        """Execute API request in thread"""
        # Get screenshot and screen info
        screenshot_b64 = get_screenshot_with_info()
        current_app = get_current_app()

        # Build screen info (consistent with phone_agent)
        screen_info = json.dumps({"current_app": current_app}, ensure_ascii=False)
        text_content = f"{question}\n\n{screen_info}"

        # Call API
        client = OpenAI(base_url=BASE_URL, api_key=APIKEY)

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": get_system_prompt()
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
                        },
                        {
                            "type": "text",
                            "text": text_content
                        }
                    ]
                }
            ],
        )

        result = response.choices[0].message.content

        # Convert 1000-based coordinates to pixel coordinates
        screen_width, screen_height = get_screen_size()
        result = convert_coords_to_pixels(result, screen_width, screen_height)

        # Add screen info for coordinate conversion
        return f"""{result}"""

    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, run_request),
            timeout=60
        )
        return [TextContent(type="text", text=result)]

    except asyncio.TimeoutError:
        return [TextContent(type="text", text="Error: Request timeout (60 seconds)")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ============ Start Server ============
async def _run_server():
    """Start MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Entry point"""
    asyncio.run(_run_server())


if __name__ == "__main__":
    main()
