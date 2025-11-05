"""FastAPI web application for MCP server management."""

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from pydantic import BaseModel

from acemcp.config import get_config
from acemcp.web.log_handler import get_log_broadcaster


class ConfigUpdate(BaseModel):
    """Configuration update model."""

    base_url: str | None = None
    token: str | None = None
    index_storage_path: str | None = None
    max_index_files: int | None = None
    text_extensions: list[str] | None = None


def create_app() -> FastAPI:
    """Create FastAPI application.

    Returns:
        FastAPI application instance
    """
    app = FastAPI(title="Acemcp Management", description="MCP Server Management Interface", version="0.1.0")

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        """Serve the main management page."""
        html_file = Path(__file__).parent / "templates" / "index.html"
        if html_file.exists():
            return html_file.read_text(encoding="utf-8")
        return "<h1>Acemcp Management</h1><p>Template not found</p>"

    @app.get("/api/config")
    async def get_config_api() -> dict:
        """Get current configuration."""
        config = get_config()
        return {
            "index_storage_path": str(config.index_storage_path),
            "max_index_files": config.max_index_files,
            "base_url": config.base_url,
            "token": "***" if config.token else "",
            "token_full": config.token,
            "text_extensions": list(config.text_extensions),
        }

    @app.post("/api/config")
    async def update_config_api(config_update: ConfigUpdate) -> dict:
        """Update configuration.

        Args:
            config_update: Configuration updates

        Returns:
            Updated configuration
        """
        try:
            settings_file = Path(__file__).parent.parent / "settings.toml"

            if not settings_file.exists():
                msg = "settings.toml not found"
                raise HTTPException(status_code=404, detail=msg)

            with settings_file.open("r", encoding="utf-8") as f:
                content = f.read()

            import toml

            settings_data = toml.loads(content)

            if "default" not in settings_data:
                settings_data["default"] = {}

            if config_update.base_url is not None:
                settings_data["default"]["BASE_URL"] = config_update.base_url
            if config_update.token is not None:
                settings_data["default"]["TOKEN"] = config_update.token
            if config_update.index_storage_path is not None:
                settings_data["default"]["INDEX_STORAGE_PATH"] = config_update.index_storage_path
            if config_update.max_index_files is not None:
                settings_data["default"]["MAX_INDEX_FILES"] = config_update.max_index_files
            if config_update.text_extensions is not None:
                settings_data["default"]["TEXT_EXTENSIONS"] = config_update.text_extensions

            with settings_file.open("w", encoding="utf-8") as f:
                toml.dump(settings_data, f)

            config = get_config()
            config.reload()

            logger.info("Configuration updated and reloaded successfully")
            return {"status": "success", "message": "Configuration updated and applied successfully!"}

        except Exception as e:
            logger.exception("Failed to update configuration")
            msg = f"Failed to update configuration: {e!s}"
            raise HTTPException(status_code=500, detail=msg) from e

    @app.get("/api/status")
    async def get_status() -> dict:
        """Get server status."""
        config = get_config()
        projects_file = config.index_storage_path / "projects.json"
        project_count = 0
        if projects_file.exists():
            import json

            try:
                with projects_file.open("r", encoding="utf-8") as f:
                    projects = json.load(f)
                    project_count = len(projects)
            except Exception:
                logger.exception("Failed to load projects")

        return {"status": "running", "project_count": project_count, "storage_path": str(config.index_storage_path)}

    @app.websocket("/ws/logs")
    async def websocket_logs(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time logs."""
        await websocket.accept()
        logger.info("WebSocket client connected")
        queue: asyncio.Queue = asyncio.Queue()
        broadcaster = get_log_broadcaster()
        broadcaster.add_client(queue)

        try:
            while True:
                log_message = await queue.get()
                await websocket.send_text(log_message)
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        except Exception:
            logger.exception("WebSocket error")
        finally:
            broadcaster.remove_client(queue)

    return app

