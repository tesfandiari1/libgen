from __future__ import annotations

import logging
import os
import sys
from collections import deque
from typing import List


class RingBufferHandler(logging.Handler):
    """In-memory ring buffer for recent logs, suitable for UI display."""

    def __init__(self, capacity: int = 1000) -> None:
        super().__init__()
        self._buffer: deque[str] = deque(maxlen=capacity)
        self.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s", "%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._buffer.append(self.format(record))
        except Exception:
            # Never raise from logging
            pass

    def get_lines(self, limit: int = 200) -> List[str]:
        if limit <= 0:
            return []
        return list(self._buffer)[-limit:]


_RING_HANDLER: RingBufferHandler | None = None


def configure_logging() -> None:
    """Configure root logging for console output using LOG_LEVEL env and ring buffer."""
    global _RING_HANDLER
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s", "%H:%M:%S")
    )

    _RING_HANDLER = RingBufferHandler(capacity=int(os.getenv("LOG_RING_CAPACITY", "2000")))

    logging.basicConfig(level=level, handlers=[stream_handler, _RING_HANDLER], force=True)


def get_recent_logs(limit: int = 200) -> List[str]:
    """Return recent log lines from the in-memory ring buffer."""
    if _RING_HANDLER is None:
        return []
    return _RING_HANDLER.get_lines(limit)


