"""Package for the logger."""

from .logger import logger
from .profiler import get_profiler

__all__ = [
    "get_profiler",
    "logger",
]
