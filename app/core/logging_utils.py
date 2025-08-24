"""
Structured JSON logging with memory tracking for debugging memory issues.
"""

import gc
import json
import logging
import tracemalloc
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

import psutil


class MemoryTracker:
    """Tracks memory usage and provides structured logging."""

    def __init__(self):
        self.process = psutil.Process()
        self.start_memory = self.get_memory_mb()
        tracemalloc.start()

    def get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        return float(self.process.memory_info().rss / 1024 / 1024)

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get detailed memory statistics."""
        memory_info = self.process.memory_info()
        return {
            "memory_mb": round(memory_info.rss / 1024 / 1024, 2),
            "memory_percent": round(self.process.memory_percent(), 2),
            "memory_peak_mb": round(memory_info.peak_wss / 1024 / 1024, 2)
            if hasattr(memory_info, "peak_wss")
            else None,
            "memory_growth_mb": round((memory_info.rss / 1024 / 1024) - self.start_memory, 2),
        }

    def get_tracemalloc_stats(self) -> Dict[str, Any]:
        """Get tracemalloc statistics."""
        if not tracemalloc.is_tracing():
            return {}

        snapshot = tracemalloc.take_snapshot()
        # Filter out internal Python modules
        top_stats = snapshot.statistics("lineno")

        # Only include stats from our application code, not Python internals
        filtered_stats = []
        for stat in top_stats:
            if stat.traceback:
                # Get the filename from the traceback
                filename = stat.traceback[0].filename if stat.traceback else ""
                # Skip internal Python files
                if not filename.startswith("<") and "site-packages" not in filename:
                    filtered_stats.append(stat)
                    if len(filtered_stats) >= 3:  # Get top 3
                        break

        if not filtered_stats:
            return {}  # Don't include tracemalloc data if only internal files

        return {
            "top_memory_consumers": [
                {
                    "file": stat.traceback[0].filename if stat.traceback else "unknown",
                    "line": stat.traceback[0].lineno if stat.traceback else 0,
                    "size_mb": round(stat.size / 1024 / 1024, 2),
                    "count": stat.count,
                }
                for stat in filtered_stats[:3]
            ]
        }


class StructuredLogger:
    """JSON structured logger with memory tracking."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.memory_tracker = MemoryTracker()
        self.session_id = str(uuid4())[:8]

    def log_step(self, step: str, **kwargs):
        """Log a processing step with memory tracking."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": self.session_id,
            "step": step,
            **self.memory_tracker.get_memory_stats(),
            **kwargs,
        }

        # Only add detailed debugging for specific important steps
        if any(keyword in step for keyword in ["error", "warning", "complete", "start"]):
            # Add tracemalloc data if available
            tracemalloc_stats = self.memory_tracker.get_tracemalloc_stats()
            if tracemalloc_stats:
                log_data.update(tracemalloc_stats)

            # Force garbage collection and log the effect
            gc_before = len(gc.get_objects())
            gc.collect()
            gc_after = len(gc.get_objects())

            log_data["gc_objects_before"] = gc_before
            log_data["gc_objects_after"] = gc_after
            log_data["gc_collected"] = gc_before - gc_after

        # Log as JSON
        self.logger.warning(json.dumps(log_data))

    def log_error(self, step: str, error: Exception, **kwargs):
        """Log an error with memory tracking."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": self.session_id,
            "step": step,
            "error": str(error),
            "error_type": type(error).__name__,
            **self.memory_tracker.get_memory_stats(),
            **kwargs,
        }

        self.logger.error(json.dumps(log_data))

    def log_memory_warning(self, step: str, threshold_mb: float = 1000, **kwargs):
        """Log if memory usage exceeds threshold."""
        current_memory = self.memory_tracker.get_memory_mb()
        if current_memory > threshold_mb:
            self.log_step(f"{step}_MEMORY_WARNING", memory_threshold_mb=threshold_mb, **kwargs)


# Global logger instance for document processing
processing_logger = StructuredLogger("document_processing")
