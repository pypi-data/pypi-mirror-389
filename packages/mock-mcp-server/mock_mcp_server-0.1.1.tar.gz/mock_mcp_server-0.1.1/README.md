# Mock MCP Server

[![PyPI - Version](https://img.shields.io/pypi/v/mock-mcp-server)](https://pypi.org/project/mock-mcp-server/)

A mock MCP server for testing MCP client implementations and development workflows.

Support tools, prompts and resources.

## Usage

### Full Usage

<details>

<summary><code>uvx mock-mcp-server --help</code></summary>

```sh
 Usage: mock-mcp-server [OPTIONS]

 Mock MCP Server for testing.

╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --transport        [stdio|http|sse|streamable-http]  Transport type [default: stdio]        │
│ --host             TEXT                              Host to bind to [default: 127.0.0.1]   │
│ --port             INTEGER                           Port to bind to [default: 8000]        │
│ --version                                            Show version and exit                  │
│ --help                                               Show this message and exit.            │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
```

</details>

### Stdio

Add to your MCP client configuration:

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en-US/install-mcp?name=mock-stdio&config=eyJjb21tYW5kIjoidXZ4IG1vY2stbWNwLXNlcnZlciJ9)
[![Add to Kiro](https://kiro.dev/images/add-to-kiro.svg)](kiro://kiro.mcp/add?name=mock-stdio&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mock-mcp-server%22%5D%7D)

```json
{
  "mcpServers": {
    "mock-stdio": {
      "command": "uvx",
      "args": ["mock-mcp-server"]
    }
  }
}
```

### Streamable HTTP

Start server first:

```sh
uvx mock-mcp-server --transport http --host 127.0.0.1 --port 7788
```

Then configure your MCP client:

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en-US/install-mcp?name=mock-streamable-http&config=eyJ1cmwiOiJodHRwOi8vMTI3LjAuMC4xOjc3ODgvbWNwIn0%3D)
[![Add to Kiro](https://kiro.dev/images/add-to-kiro.svg)](kiro://kiro.mcp/add?name=mock-streamable-http&config=%7B%22url%22%3A%22http%3A%2F%2F127.0.0.1%3A7788%2Fmcp%22%7D)

```json
{
  "mcpServers": {
    "mock-streamable-http": {
      "url": "http://127.0.0.1:7788/mcp"
    }
  }
}
```

### SSE

Start server first:

```sh
uvx mock-mcp-server --transport sse --host 127.0.0.1 --port 7789
```

Then configure your MCP client:

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en-US/install-mcp?name=mock-sse&config=eyJ1cmwiOiJodHRwOi8vMTI3LjAuMC4xOjc3ODkvc3NlIn0%3D)
[![Add to Kiro](https://kiro.dev/images/add-to-kiro.svg)](kiro://kiro.mcp/add?name=mock-sse&config=%7B%22url%22%3A%22http%3A%2F%2F127.0.0.1%3A7789%2Fsse%22%7D)

```json
{
  "mcpServers": {
    "mock-sse": {
      "url": "http://127.0.0.1:7789/sse"
    }
  }
}
```

## [CHANGELOG](./CHANGELOG.md)
