"""Index manager for codebase indexing."""

import json
import os
from pathlib import Path

import httpx
from loguru import logger


class IndexManager:
    """Manages codebase indexing and retrieval."""

    def __init__(self, storage_path: Path, base_url: str, token: str, text_extensions: set[str], max_index_files: int) -> None:
        """Initialize index manager.

        Args:
            storage_path: Path to store index data
            base_url: Base URL for API requests
            token: Authorization token
            text_extensions: Set of text file extensions to index
            max_index_files: Maximum number of files to index
        """
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.text_extensions = text_extensions
        self.max_index_files = max_index_files
        self.projects_file = storage_path / "projects.json"
        logger.info(f"IndexManager initialized with storage path: {storage_path}, max_index_files: {max_index_files}")

    def _load_projects(self) -> dict[str, list[str]]:
        """Load projects data from storage.

        Returns:
            Dictionary mapping project_id to blob_names
        """
        if not self.projects_file.exists():
            return {}
        try:
            with self.projects_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.exception("Failed to load projects data")
            return {}

    def _save_projects(self, projects: dict[str, list[str]]) -> None:
        """Save projects data to storage.

        Args:
            projects: Dictionary mapping project_id to blob_names
        """
        try:
            with self.projects_file.open("w", encoding="utf-8") as f:
                json.dump(projects, f, indent=2, ensure_ascii=False)
        except Exception:
            logger.exception("Failed to save projects data")
            raise

    def _collect_files(self, project_root_path: str) -> list[dict[str, str]]:
        """Collect all text files from project directory.

        Args:
            project_root_path: Root path of the project

        Returns:
            List of blobs with path and content
        """
        blobs = []
        root_path = Path(project_root_path)

        if not root_path.exists():
            msg = f"Project root path does not exist: {project_root_path}"
            raise FileNotFoundError(msg)

        for dirpath, _dirnames, filenames in os.walk(root_path):
            for filename in filenames:
                if len(blobs) >= self.max_index_files:
                    logger.warning(f"Reached max_index_files limit ({self.max_index_files}), stopping file collection")
                    break

                file_path = Path(dirpath) / filename

                if file_path.suffix.lower() not in self.text_extensions:
                    continue

                try:
                    relative_path = file_path.relative_to(root_path)
                    with file_path.open("r", encoding="utf-8") as f:
                        content = f.read()
                    blobs.append({"path": str(relative_path), "content": content})
                    logger.debug(f"Collected file: {relative_path}")
                except Exception:
                    logger.warning(f"Failed to read file: {file_path}")
                    continue

            if len(blobs) >= self.max_index_files:
                break

        logger.info(f"Collected {len(blobs)} files from {project_root_path}")
        return blobs

    async def index_project(self, project_id: str, project_root_path: str) -> dict[str, str]:
        """Index a code project.

        Args:
            project_id: Unique identifier for the project
            project_root_path: Root path of the project to index

        Returns:
            Result dictionary with status and message
        """
        logger.info(f"Indexing project: {project_id} from {project_root_path}")

        try:
            blobs = self._collect_files(project_root_path)

            if not blobs:
                return {"status": "error", "message": "No text files found in project"}

            payload = {"blobs": blobs}

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/batch-upload",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()

            blob_names = result.get("blob_names", [])

            if not blob_names:
                return {"status": "error", "message": "No blob names returned from API"}

            projects = self._load_projects()
            projects[project_id] = blob_names
            self._save_projects(projects)

            logger.info(f"Project {project_id} indexed successfully with {len(blob_names)} blobs")
            return {"status": "success", "message": f"Project {project_id} indexed with {len(blob_names)} blobs"}

        except Exception as e:
            logger.exception(f"Failed to index project {project_id}")
            return {"status": "error", "message": str(e)}

    async def search_context(self, project_id: str, query: str) -> str:
        """Search for code context based on query.

        Args:
            project_id: Project identifier to search within
            query: Search query string

        Returns:
            Formatted retrieval result
        """
        logger.info(f"Searching context in project {project_id} with query: {query}")

        try:
            projects = self._load_projects()

            if project_id not in projects:
                return f"Error: Project {project_id} not found. Please index the project first."

            blob_names = projects[project_id]

            payload = {"information_request": query, "blobs": {"checkpoint_id": None, "added_blobs": blob_names, "deleted_blobs": []}, "dialog": [], "max_output_length": 0, "disable_codebase_retrieval": False, "enable_commit_retrieval": False}

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/agents/codebase-retrieval",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()

            formatted_retrieval = result.get("formatted_retrieval", "")

            logger.info(f"Search completed for project {project_id}")
            return formatted_retrieval

        except Exception as e:
            logger.exception(f"Failed to search context in project {project_id}")
            return f"Error: {e!s}"

