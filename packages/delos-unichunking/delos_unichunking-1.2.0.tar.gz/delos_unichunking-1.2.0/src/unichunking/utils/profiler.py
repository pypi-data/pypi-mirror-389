"""Simple profiler to track time spent in different functions."""

import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Any


class TimingProfiler:
    """Track cumulative time spent in different code sections."""

    def __init__(self) -> None:
        """Initialize profiler."""
        self.timings: dict[str, list[float]] = defaultdict(list)
        self.enabled = True

    @contextmanager
    def measure(self, name: str):
        """Context manager to measure time spent in a code block.

        Usage:
            with profiler.measure("function_name"):
                # code to measure
        """
        if not self.enabled:
            yield
            return

        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.timings[name].append(elapsed)

    def get_stats(self, name: str) -> dict[str, Any]:
        """Get statistics for a specific timing."""
        if name not in self.timings:
            return {"count": 0, "total_ms": 0, "avg_ms": 0, "min_ms": 0, "max_ms": 0}

        times = self.timings[name]
        total_s = sum(times)
        return {
            "count": len(times),
            "total_ms": total_s * 1000,
            "avg_ms": (total_s / len(times)) * 1000,
            "min_ms": min(times) * 1000,
            "max_ms": max(times) * 1000,
        }

    def print_summary(self) -> None:
        """Print summary of all timings."""
        if not self.timings:
            return


        # Sort by total time (descending)
        sorted_names = sorted(
            self.timings.keys(),
            key=lambda n: sum(self.timings[n]),
            reverse=True,
        )

        for name in sorted_names:
            self.get_stats(name)


    def reset(self) -> None:
        """Clear all timing data."""
        self.timings.clear()


# Global profiler instance
_profiler = TimingProfiler()


def get_profiler() -> TimingProfiler:
    """Get the global profiler instance."""
    return _profiler
