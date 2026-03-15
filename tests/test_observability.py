"""Tests for observability and telemetry."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.observability.telemetry import Telemetry, Span, Meter, get_telemetry


class TestSpan:
    """Test span creation and tracking."""

    def test_span_creation(self):
        """Test creating a span."""
        span = Span("test-span")
        assert span.name == "test-span"
        assert span.start_time > 0

    def test_span_end(self):
        """Test ending a span."""
        span = Span("test")
        span.end(status="ok")
        assert span.status == "ok"
        assert span.end_time is not None

    def test_span_duration(self):
        """Test span duration calculation."""
        span = Span("test")
        span.end()
        assert span.duration >= 0


class TestMeter:
    """Test meter for metrics."""

    def test_counter(self):
        """Test counter."""
        meter = Meter()
        meter.counter("test")
        assert meter.counters["test"] == 1
        meter.counter("test", 5)
        assert meter.counters["test"] == 6

    def test_histogram(self):
        """Test histogram."""
        meter = Meter()
        meter.histogram("latency", 100)
        meter.histogram("latency", 200)
        assert len(meter.histograms["latency"]) == 2

    def test_get_summary(self):
        """Test getting metrics summary."""
        meter = Meter()
        meter.counter("executions")
        meter.histogram("duration", 1.5)
        summary = meter.get_summary()
        assert "counters" in summary
        assert "histograms" in summary


class TestTelemetry:
    """Test telemetry collection."""

    def test_telemetry_creation(self):
        """Test creating telemetry instance."""
        telemetry = Telemetry()
        assert telemetry is not None
        assert telemetry.enabled is True

    def test_start_span(self):
        """Test starting a span."""
        telemetry = Telemetry()
        span = telemetry.start_span("test", {"key": "value"})
        assert span is not None
        assert len(telemetry.spans) == 1

    def test_log(self):
        """Test logging."""
        telemetry = Telemetry()
        telemetry.log("info", "Test message")
        assert len(telemetry.logs) == 1

    def test_record_execution(self):
        """Test recording execution."""
        telemetry = Telemetry()
        telemetry.record_execution("test-cap", "test-tool", 1.5, True)
        summary = telemetry.get_summary()
        assert summary["metrics"]["counters"]["executions_total"] == 1
        assert summary["metrics"]["counters"]["executions_successful"] == 1

    def test_get_summary(self):
        """Test getting telemetry summary."""
        telemetry = Telemetry()
        telemetry.start_span("test")
        telemetry.log("info", "message")
        summary = telemetry.get_summary()
        assert summary["spans"] == 1
        assert summary["logs"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
