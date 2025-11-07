## Setup with Claude Desktop

### Option 1: Using uvx (Recommended)
Add this MCP server config to your `claude_desktop_config.json`:

```json
"kipu-quantum-hub-mcp": {
   "command": "uvx",
   "args": ["kipu-quantum-hub-mcp"],
   "env": {
     "KIPU_ACCESS_TOKEN": "<YOUR_PERSONAL_ACCESS_TOKEN>"
   }
}
```

### Option 2: Local Development Setup
1. Clone the repository 
2. Install uv if you don't have it already
3. Run `uv sync` 
4. Add an MCP server config to the `claude_desktop_config.json`:
   ```json
   "kipu-quantum-hub-mcp": {
      "command": "<UV_PATH>",
      "args": [
         "--directory",
          "<PROJECT_PATH>", 
          "run",
          "src/kipu_quantum_hub_mcp/server.py"
      ],
      "env": {
        "KIPU_ACCESS_TOKEN": "<YOUR_PERSONAL_ACCESS_TOKEN>"
      }
    }
   ```
   