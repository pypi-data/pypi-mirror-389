import typer
from fastmcp import FastMCP
from fastmcp.server.server import Transport
from typing_extensions import Annotated
from typing import Optional

from . import __version__

mcp = FastMCP("Mock MCP Server")


def version_callback(value: bool):
    if value:
        print(f"Mock MCP Server Version: {__version__}")
        raise typer.Exit()


def app(
    transport: Annotated[Transport, typer.Option(help="Transport type")] = "stdio",
    host: Annotated[str, typer.Option(help="Host to bind to")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Port to bind to")] = 8000,
    _version: Annotated[
        Optional[bool],
        typer.Option(
            "--version", callback=version_callback, help="Show version and exit"
        ),
    ] = None,
):
    """Mock MCP Server for testing."""
    if transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=transport, host=host, port=port)


@mcp.tool
def mock_echo(message: str) -> str:
    """Echo back the provided message."""
    return f"Mock server echoes: {message}"


@mcp.resource("resource://mock-data")
def get_mock_data() -> str:
    """Provides mock data for testing."""
    return "This is mock data from the test server."


@mcp.prompt
def mock_prompt(topic: str) -> str:
    """Generates a mock prompt for testing purposes."""
    return f"This is a mock prompt about '{topic}' for testing the MCP server."


def main():
    typer.run(app)


if __name__ == "__main__":
    main()
