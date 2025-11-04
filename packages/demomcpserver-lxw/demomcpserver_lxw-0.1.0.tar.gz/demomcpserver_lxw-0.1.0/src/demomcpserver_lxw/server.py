from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError#, ResourceError

mcp = FastMCP(name="Liyu Demo MCP Server", version="1.0.0")

def main() -> None:
    mcp.run()


@mcp.tool
async def greet(name: str, ctx: Context) -> str:
    """A simple greeting tool that returns a greeting message."""
    await ctx.info("called greeting tool.")
    if not name:
        raise ToolError("Name cannot be empty.")
    return f"Hello, {name}!"


@mcp.resource("data://config")
async def get_config(ctx: Context) -> dict:
    """Provides application configuration as JSON."""

    await ctx.info("Processing config resource request.")

    return {
        "theme": "dark",
        "version": "1.2.0",
        "features": ["tools", "resources"],
    }
