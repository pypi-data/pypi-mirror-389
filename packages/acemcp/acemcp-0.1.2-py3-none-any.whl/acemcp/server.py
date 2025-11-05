"""MCP server for codebase indexing."""

import argparse
import asyncio

import uvicorn
from loguru import logger
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from acemcp.config import get_config, init_config
from acemcp.tools import index_code_tool, search_context_tool
from acemcp.web import create_app

app = Server("acemcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools.

    Returns:
        List of available tools
    """
    return [
        Tool(
            name="index_code",
            description="Index a code project for semantic search. Provide project_id and project_root_path.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Unique identifier for the project"},
                    "project_root_path": {"type": "string", "description": "Root path of the project to index"},
                },
                "required": ["project_id", "project_root_path"],
            },
        ),
        Tool(
            name="search_context",
            description="Search for relevant code context based on a query within a specific project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project identifier to search within"},
                    "query": {"type": "string", "description": "Search query string"},
                },
                "required": ["project_id", "query"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[dict]:
    """Handle tool calls.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        Tool execution results
    """
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    if name == "index_code":
        return await index_code_tool(arguments)
    if name == "search_context":
        return await search_context_tool(arguments)

    return [{"type": "text", "text": f"Unknown tool: {name}"}]


async def run_web_server(port: int) -> None:
    """Run the web management server.

    Args:
        port: Port to run the web server on
    """
    web_app = create_app()
    config_uvicorn = uvicorn.Config(web_app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config_uvicorn)
    await server.serve()


async def main(base_url: str | None = None, token: str | None = None, index_storage_path: str | None = None, web_port: int | None = None) -> None:
    """Run the MCP server.

    Args:
        base_url: Override BASE_URL from command line
        token: Override TOKEN from command line
        index_storage_path: Override INDEX_STORAGE_PATH from command line
        web_port: Port for web management interface (None to disable)
    """
    try:
        config = init_config(base_url=base_url, token=token, index_storage_path=index_storage_path)
        config.validate()
        logger.info("Starting acemcp MCP server...")
        logger.info(f"Configuration: index_storage_path={config.index_storage_path}, max_index_files={config.max_index_files}")
        logger.info(f"API: base_url={config.base_url}")

        if web_port:
            logger.info(f"Starting web management interface on port {web_port}")
            web_task = asyncio.create_task(run_web_server(web_port))

        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

        if web_port:
            web_task.cancel()

    except Exception:
        logger.exception("Server error")
        raise


def run() -> None:
    """Entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="Acemcp MCP Server for codebase indexing")
    parser.add_argument("--base-url", type=str, help="Override BASE_URL configuration")
    parser.add_argument("--token", type=str, help="Override TOKEN configuration")
    parser.add_argument("--index-storage-path", type=str, help="Override INDEX_STORAGE_PATH configuration")
    parser.add_argument("--web-port", type=int, help="Enable web management interface on specified port (e.g., 8080)")

    args = parser.parse_args()

    asyncio.run(main(base_url=args.base_url, token=args.token, index_storage_path=args.index_storage_path, web_port=args.web_port))


if __name__ == "__main__":
    run()

