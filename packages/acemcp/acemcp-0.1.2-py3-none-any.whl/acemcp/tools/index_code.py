"""Index code tool for MCP server."""

import json
from typing import Any

from loguru import logger

from acemcp.config import get_config
from acemcp.index import IndexManager


async def index_code_tool(arguments: dict[str, Any]) -> list[dict[str, Any]]:
    """Index a code project.

    Args:
        arguments: Tool arguments containing:
            - project_id: Unique identifier for the project
            - project_root_path: Root path of the project to index

    Returns:
        List containing result dictionary
    """
    try:
        project_id = arguments.get("project_id")
        project_root_path = arguments.get("project_root_path")

        if not project_id:
            return [{"type": "text", "text": "Error: project_id is required"}]

        if not project_root_path:
            return [{"type": "text", "text": "Error: project_root_path is required"}]

        logger.info(f"Tool invoked: index_code for project {project_id}")

        config = get_config()
        index_manager = IndexManager(config.index_storage_path, config.base_url, config.token, config.text_extensions, config.max_index_files)
        result = await index_manager.index_project(project_id, project_root_path)

        return [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]

    except Exception as e:
        logger.exception("Error in index_code_tool")
        return [{"type": "text", "text": f"Error: {e!s}"}]

