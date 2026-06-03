from mcp.server.fastmcp import FastMCP

HOST = "127.0.0.1"
PORT = 8000
MCP_PATH = "/mcp"

mcp = FastMCP(
    name="learn-mcp-inspector",
    host=HOST,
    port=PORT,
    streamable_http_path=MCP_PATH,
)


@mcp.tool(name="hello_from_mcp")
def hello_from_mcp() -> str:
    """Return a short greeting from the local MCP server."""
    return "Hello from the local MCP server."


def run() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    run()
