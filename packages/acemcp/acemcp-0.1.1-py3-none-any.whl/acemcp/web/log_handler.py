"""Log handler for broadcasting logs to WebSocket clients."""

import asyncio
from typing import Any

from loguru import logger


class LogBroadcaster:
    """Broadcast logs to multiple WebSocket clients."""

    def __init__(self) -> None:
        """Initialize log broadcaster."""
        self.clients: list[asyncio.Queue] = []
        self._logger_setup = False

    def _setup_logger(self) -> None:
        """Setup loguru handler to broadcast logs."""
        if self._logger_setup:
            return

        def log_sink(message: Any) -> None:
            """Custom sink to broadcast log messages."""
            log_text = str(message)
            for client_queue in self.clients:
                try:
                    client_queue.put_nowait(log_text)
                except asyncio.QueueFull:
                    pass
                except Exception:
                    pass

        logger.add(log_sink, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")
        self._logger_setup = True

    def add_client(self, queue: asyncio.Queue) -> None:
        """Add a client queue.

        Args:
            queue: Client's asyncio queue
        """
        if not self._logger_setup:
            self._setup_logger()

        self.clients.append(queue)
        logger.info(f"WebSocket client connected. Total clients: {len(self.clients)}")

    def remove_client(self, queue: asyncio.Queue) -> None:
        """Remove a client queue.

        Args:
            queue: Client's asyncio queue
        """
        if queue in self.clients:
            self.clients.remove(queue)
            logger.info(f"WebSocket client removed. Total clients: {len(self.clients)}")


_broadcaster_instance: LogBroadcaster | None = None


def get_log_broadcaster() -> LogBroadcaster:
    """Get the global log broadcaster instance.

    Returns:
        LogBroadcaster instance
    """
    global _broadcaster_instance  # noqa: PLW0603
    if _broadcaster_instance is None:
        _broadcaster_instance = LogBroadcaster()
    return _broadcaster_instance

