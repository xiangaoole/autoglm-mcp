# AutoGLM MCP Server

Android screen analysis capabilities via MCP protocol.

## Installation

### Option 1: Using uvx (Recommended)

No manual installation required. Just add to AI agent mcp config:

```json
{
  "mcpServers": {
    "autoglm": {
      "command": "uvx",
      "args": ["autoglm-mcp"],
      "env": {
        "AUTOGLM_APIKEY": "your-api-key"
      }
    }
  }
}
```

### Option 2: pip install

```bash
pip install autoglm-mcp
```

Then configure AI agent mcp:

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

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTOGLM_APIKEY` | API key (required) | - |
| `AUTOGLM_BASE_URL` | API endpoint | `https://api.z.ai/api/paas/v4` |
| `AUTOGLM_MODEL` | Model name | `autoglm-phone-multilingual` |

## Usage

Ensure your phone is connected via ADB, then use the `aiAsk` tool in Claude:

- "What are the coordinates to click the search button?"
- "How do I open Settings?"

Returned coordinates are relative values (0-1000), convert to pixels:
```
x_pixel = int(x / 1000 * screen_width)
y_pixel = int(y / 1000 * screen_height)
```
