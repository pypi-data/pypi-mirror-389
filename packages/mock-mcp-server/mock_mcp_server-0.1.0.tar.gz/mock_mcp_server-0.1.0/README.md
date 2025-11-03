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

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en-US/install-mcp?name=mock&config=eyJjb21tYW5kIjoidXZ4IG1vY2stbWNwLXNlcnZlciJ9)
[![Add to Kiro](https://kiro.dev/images/add-to-kiro.svg)](kiro://kiro.mcp/add?name=mock&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mock-mcp-server%22%5D%7D)

```json
{
  "mcpServers": {
    "mock": {
      "command": "uvx",
      "args": ["mock-mcp-server"]
    }
  }
}
```

### Streamable HTTP

Start server first:

```sh
uvx mock-mcp-server --transport http --host 127.0.0.1 --port 8000
```

Then configure your MCP client:

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en-US/install-mcp?name=mock&config=eyJ1cmwiOiJodHRwOi8vMTI3LjAuMC4xOjgwMDAifQ%3D%3D)
[![Add to Kiro](https://kiro.dev/images/add-to-kiro.svg)](kiro://kiro.mcp/add?name=mock&config=%7B%22url%22%3A%22http%3A%2F%2F127.0.0.1%3A8000%22%7D)

```json
{
  "mcpServers": {
    "mock": {
      "url": "http://127.0.0.1:8000"
    }
  }
}
```

### SSE

Start server first:

```sh
uvx mock-mcp-server --transport sse --host 127.0.0.1 --port 8000
```

Then configure your MCP client:

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en-US/install-mcp?name=mock&config=eyJ1cmwiOiJodHRwOi8vMTI3LjAuMC4xOjgwMDAifQ%3D%3D)
[![Add to Kiro](https://kiro.dev/images/add-to-kiro.svg)](kiro://kiro.mcp/add?name=mock&config=%7B%22url%22%3A%22http%3A%2F%2F127.0.0.1%3A8000%22%7D)

```json
{
  "mcpServers": {
    "mock": {
      "url": "http://127.0.0.1:8000"
    }
  }
}
```

## [CHANGELOG](./CHANGELOG.md)
