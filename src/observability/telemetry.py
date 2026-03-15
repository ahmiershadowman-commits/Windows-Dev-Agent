"""
OpenTelemetry integration for Windows Dev Agent Plugin.

Provides comprehensive observability with spans, metrics, and logs.
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Telemetry log file
TELEMETRY_FILE = Path(__file__).parent.parent.parent / ".logs" / "telemetry.jsonl"


class Span:
    """Represents an execution span for tracing."""

    def __init__(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        self.name = name
        self.attributes = attributes or {}
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status = "unknown"
        self.error: Optional[str] = None

    def end(self, status: str = "ok", error: Optional[str] = None):
        """End the span."""
        self.end_time = time.time()
        self.status = status
        self.error = error

    @property
    def duration(self) -> float:
        """Get span duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "status": self.status,
            "error": self.error,
            "attributes": self.attributes,
        }


class Meter:
    """Collects metrics."""

    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.histograms: Dict[str, list] = {}

    def counter(self, name: str, value: int = 1):
        """Increment a counter."""
        if name not in self.counters:
            self.counters[name] = 0
        self.counters[name] += value

    def histogram(self, name: str, value: float):
        """Record a histogram value."""
        if name not in self.histograms:
            self.histograms[name] = []
        self.histograms[name].append(value)

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return {
            "counters": self.counters,
            "histograms": {
                name: {
                    "count": len(values),
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                    "avg": sum(values) / len(values) if values else 0,
                }
                for name, values in self.histograms.items()
            },
        }


class Telemetry:
    """Central telemetry collector."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.spans: list = []
        self.meter = Meter()
        self.logs: list = []

    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Span:
        """Start a span."""
        span = Span(name, attributes)
        self.spans.append(span)
        logger.debug(f"Span started: {name}")
        return span

    def log(self, level: str, message: str, attributes: Optional[Dict[str, Any]] = None):
        """Log a message."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "attributes": attributes or {},
        }
        self.logs.append(log_entry)
        logger.info(f"{level}: {message}")

    def record_execution(self, capability_id: str, tool_id: str, duration: float, success: bool):
        """Record a capability execution."""
        self.meter.counter("executions_total")
        if success:
            self.meter.counter("executions_successful")
        else:
            self.meter.counter("executions_failed")
        self.meter.histogram("execution_duration_seconds", duration)

    def get_summary(self) -> Dict[str, Any]:
        """Get telemetry summary."""
        return {
            "spans": len(self.spans),
            "logs": len(self.logs),
            "metrics": self.meter.get_summary(),
        }

    def export_to_file(self, path: Optional[Path] = None):
        """Export telemetry to file."""
        filepath = path or TELEMETRY_FILE
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(filepath, "a") as f:
                for log in self.logs:
                    f.write(f"{log}\n")
                for span in self.spans:
                    f.write(f"{span.to_dict()}\n")
            logger.info(f"Exported telemetry to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export telemetry: {e}")


# Global telemetry instance
_telemetry: Optional[Telemetry] = None


def get_telemetry() -> Telemetry:
    """Get or create global telemetry instance."""
    global _telemetry
    if _telemetry is None:
        _telemetry = Telemetry()
    return _telemetry
