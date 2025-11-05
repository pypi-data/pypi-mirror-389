"""Configuration management for acemcp MCP server."""

from pathlib import Path

from dynaconf import Dynaconf
import os
import pathlib
# 按照绝对路径找到配置文件的路径（兼容打包单文件执行和调试运行，可查看spec文件）
base_path = pathlib.Path(os.path.abspath(os.path.dirname(__file__)))
# 配置文件
config_path = base_path / "settings.toml"

settings = Dynaconf(
    envvar_prefix="ACEMCP",
    settings_files=[config_path],
    environments=True,
    load_dotenv=True,
    merge_enabled=True,
)


class Config:
    """MCP server configuration."""

    def __init__(self, base_url: str | None = None, token: str | None = None, index_storage_path: str | None = None) -> None:
        """Initialize configuration.

        Args:
            base_url: Override BASE_URL from command line
            token: Override TOKEN from command line
            index_storage_path: Override INDEX_STORAGE_PATH from command line
        """
        self._cli_base_url = base_url
        self._cli_token = token
        self._cli_index_storage_path = index_storage_path

        self.index_storage_path: Path = Path(index_storage_path or settings.get("INDEX_STORAGE_PATH", ".acemcp_index"))
        self.max_index_files: int = settings.get("MAX_INDEX_FILES", 10000)
        self.base_url: str = base_url or settings.get("BASE_URL", "")
        self.token: str = token or settings.get("TOKEN", "")
        self.text_extensions: set[str] = set(
            settings.get(
                "TEXT_EXTENSIONS",
                [
                    ".py",
                    ".js",
                    ".ts",
                    ".jsx",
                    ".tsx",
                    ".java",
                    ".go",
                    ".rs",
                    ".cpp",
                    ".c",
                    ".h",
                    ".hpp",
                    ".cs",
                    ".rb",
                    ".php",
                    ".md",
                    ".txt",
                    ".json",
                    ".yaml",
                    ".yml",
                    ".toml",
                    ".xml",
                    ".html",
                    ".css",
                    ".scss",
                    ".sql",
                    ".sh",
                    ".bash",
                ],
            )
        )

    def reload(self) -> None:
        """Reload configuration from settings, respecting CLI overrides."""
        settings.reload()
        self.index_storage_path = Path(self._cli_index_storage_path or settings.get("INDEX_STORAGE_PATH", ".acemcp_index"))
        self.max_index_files = settings.get("MAX_INDEX_FILES", 10000)
        self.base_url = self._cli_base_url or settings.get("BASE_URL", "")
        self.token = self._cli_token or settings.get("TOKEN", "")
        self.text_extensions = set(
            settings.get(
                "TEXT_EXTENSIONS",
                [
                    ".py",
                    ".js",
                    ".ts",
                    ".jsx",
                    ".tsx",
                    ".java",
                    ".go",
                    ".rs",
                    ".cpp",
                    ".c",
                    ".h",
                    ".hpp",
                    ".cs",
                    ".rb",
                    ".php",
                    ".md",
                    ".txt",
                    ".json",
                    ".yaml",
                    ".yml",
                    ".toml",
                    ".xml",
                    ".html",
                    ".css",
                    ".scss",
                    ".sql",
                    ".sh",
                    ".bash",
                ],
            )
        )

    def validate(self) -> None:
        """Validate configuration."""
        if self.max_index_files <= 0:
            msg = "MAX_INDEX_FILES must be positive"
            raise ValueError(msg)
        if not self.base_url:
            msg = "BASE_URL must be configured"
            raise ValueError(msg)
        if not self.token:
            msg = "TOKEN must be configured"
            raise ValueError(msg)


_config_instance: Config | None = None


def get_config() -> Config:
    """Get the global config instance.

    Returns:
        Config instance
    """
    global _config_instance  # noqa: PLW0603
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def init_config(base_url: str | None = None, token: str | None = None, index_storage_path: str | None = None) -> Config:
    """Initialize config with command line arguments.

    Args:
        base_url: Override BASE_URL from command line
        token: Override TOKEN from command line
        index_storage_path: Override INDEX_STORAGE_PATH from command line

    Returns:
        Config instance
    """
    global _config_instance  # noqa: PLW0603
    _config_instance = Config(base_url=base_url, token=token, index_storage_path=index_storage_path)
    return _config_instance


config = get_config()

