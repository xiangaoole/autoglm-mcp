# AutoGLM MCP Server

Android screen analysis capabilities via MCP protocol.

## Installation

### Option 1: Using uvx (Recommended)

No manual installation required. Just add to AI agent MCP config:

```json
{
  "mcpServers": {
    "autoglm-mcp": {
      "command": "uvx",
      "args": ["autoglm-mcp"],
      "env": {
        "AUTOGLM_BASE_URL": "https://api.z.ai/api/paas/v4",
        "AUTOGLM_MODEL": "autoglm-phone-multilingual",
        "AUTOGLM_APIKEY": "your-api-key-here"
      }
    }
  }
}
```

### Option 2: pip install

```bash
pip install autoglm-mcp
```

Then configure AI agent MCP:

```json
{
  "mcpServers": {
    "autoglm-mcp": {
      "command": "autoglm-mcp",
      "env": {
        "AUTOGLM_BASE_URL": "https://api.z.ai/api/paas/v4",
        "AUTOGLM_MODEL": "autoglm-phone-multilingual",
        "AUTOGLM_APIKEY": "your-api-key-here"
      }
    }
  }
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTOGLM_APIKEY` | API key (required) | - |
| `AUTOGLM_BASE_URL` | API endpoint | `https://api.z.ai/api/paas/v4` |
| `AUTOGLM_MODEL` | Model name | `autoglm-phone-multilingual` |

## Usage

Ensure your phone is connected via ADB, then use the `aiAsk` tool in AI agent:

- "What are the coordinates to click the search button?"
- "How do I open Settings?"

## Local Development & Debugging

### Prerequisites

- Python >= 3.10
- Node.js >= 18 (for MCP Inspector)
- ADB installed and phone connected (`adb devices` shows your device)

### Install from Source

```bash
cd mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### MCP Inspector (Recommended)

[MCP Inspector](https://github.com/modelcontextprotocol/inspector) is the official visual debugging tool for MCP servers — like Postman for MCP.

```bash
npx @modelcontextprotocol/inspector \
  -e AUTOGLM_APIKEY="your-api-key-here" \
  -e AUTOGLM_BASE_URL="https://api.z.ai/api/paas/v4" \
  -e AUTOGLM_MODEL="autoglm-phone-multilingual" \
  -- \
  /path/to/file/mcp/.venv/bin/python -m autoglm_mcp.server
```

Then open `http://localhost:6274` in your browser:

1. Click **Connect** to connect to the server
2. Switch to the **Tools** tab — you should see the `aiAsk` tool
3. Enter a question (e.g. `"What is on the screen?"`) and click **Run Tool**
4. Inspect the JSON-RPC request/response in the left panel

### Use local mcp server

```json
"autoglm-mcp": {
  "command": "/path/to/file/mcp/.venv/bin/python",
  "args": [
    "-m",
    "autoglm_mcp.server"
  ],
  "env": {
    "AUTOGLM_BASE_URL": "https://api.z.ai/api/paas/v4",
    "AUTOGLM_MODEL": "autoglm-phone-multilingual",
    "AUTOGLM_APIKEY": "xxx"
  }
}
```