from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from tools_countries import register


def run() -> None:
    mcp = FastMCP("countries-sqlite-api", host="127.0.0.1", port=8001, streamable_http_path="/mcp")
    register(mcp)
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    run()
