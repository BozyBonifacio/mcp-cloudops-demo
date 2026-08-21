from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_cloudops.prompts.cloudops import register_prompts
from mcp_cloudops.resources.cloudops import register_resources
from mcp_cloudops.tools.cloudops import register_tools

mcp = FastMCP(
    "MCP CloudOps Demo",
    instructions=(
        "A safe educational MCP server backed entirely by deterministic fake Azure-style data. "
        "No cloud credentials are required and no real infrastructure is modified."
    ),
)

register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
