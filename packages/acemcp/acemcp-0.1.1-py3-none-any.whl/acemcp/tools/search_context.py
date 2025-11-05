"""Search context tool for MCP server."""

from typing import Any

from loguru import logger

from acemcp.config import get_config
from acemcp.index import IndexManager


async def search_context_tool(arguments: dict[str, Any]) -> list[dict[str, Any]]:
    """Search for code context based on query.

    Args:
        arguments: Tool arguments containing:
            - project_id: Project identifier to search within
            - query: Search query string

    Returns:
        List containing search results
    """
    try:
        project_id = arguments.get("project_id")
        query = arguments.get("query")

        if not project_id:
            return [{"type": "text", "text": "Error: project_id is required"}]

        if not query:
            return [{"type": "text", "text": "Error: query is required"}]

        logger.info(f"Tool invoked: search_context for project {project_id} with query: {query}")

        config = get_config()
        index_manager = IndexManager(config.index_storage_path, config.base_url, config.token, config.text_extensions, config.max_index_files)
        result = await index_manager.search_context(project_id, query)

        return [{"type": "text", "text": result}]

    except Exception as e:
        logger.exception("Error in search_context_tool")
        return [{"type": "text", "text": f"Error: {e!s}"}]

