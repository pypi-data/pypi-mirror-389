"""
AIS Protocol - Observability

Structured logging and metrics collection for production monitoring.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, field
from collections import defaultdict
from threading import Lock


# ============================================================================
# Structured Logging
# ============================================================================

class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs log records as JSON for easy parsing by log aggregators
    (Elasticsearch, Datadog, CloudWatch, etc.).

    Example:
        ```python
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        ```
    """

    def __init__(
        self,
        include_timestamp: bool = True,
        include_level: bool = True,
        include_logger_name: bool = True,
        additional_fields: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize structured formatter.

        Args:
            include_timestamp: Include timestamp in output
            include_level: Include log level
            include_logger_name: Include logger name
            additional_fields: Static fields to include in every log
        """
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.include_logger_name = include_logger_name
        self.additional_fields = additional_fields or {}

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON string
        """
        log_data: Dict[str, Any] = {
            "message": record.getMessage(),
        }

        # Add timestamp
        if self.include_timestamp:
            log_data["timestamp"] = datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat()

        # Add level
        if self.include_level:
            log_data["level"] = record.levelname
            log_data["level_number"] = record.levelno

        # Add logger name
        if self.include_logger_name:
            log_data["logger"] = record.name

        # Add location info
        log_data["location"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }

        # Add extra fields from record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'message', 'pathname', 'process', 'processName',
                'relativeCreated', 'thread', 'threadName', 'exc_info',
                'exc_text', 'stack_info', 'taskName'
            ]:
                extra_fields[key] = value

        if extra_fields:
            log_data["extra"] = extra_fields

        # Add static additional fields
        if self.additional_fields:
            log_data.update(self.additional_fields)

        return json.dumps(log_data)


def setup_structured_logging(
    logger_name: str,
    level: int = logging.INFO,
    service_name: Optional[str] = None,
    environment: Optional[str] = None
) -> logging.Logger:
    """
    Set up structured logging for a logger.

    Args:
        logger_name: Name of the logger
        level: Logging level
        service_name: Service name for context
        environment: Environment (dev, staging, prod)

    Returns:
        Configured logger
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers = []

    # Create structured handler
    handler = logging.StreamHandler()

    additional_fields = {}
    if service_name:
        additional_fields["service"] = service_name
    if environment:
        additional_fields["environment"] = environment

    formatter = StructuredFormatter(additional_fields=additional_fields)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# ============================================================================
# Metrics Collection
# ============================================================================

@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: str = "gauge"  # gauge, counter, histogram


class Metrics:
    """
    Metrics collection for monitoring AIS protocol performance.

    Collects counters, gauges, and histograms for:
    - Message processing times
    - Request counts
    - Error rates
    - Session counts
    - Transport metrics

    Example:
        ```python
        metrics = Metrics()
        metrics.increment("requests.received", tags={"endpoint": "/ais/v0.1/message"})
        metrics.gauge("sessions.active", 5)
        metrics.histogram("request.duration_ms", 123.45)
        ```
    """

    def __init__(self, prefix: str = "ais"):
        """
        Initialize metrics collector.

        Args:
            prefix: Metric name prefix (default: "ais")
        """
        self.prefix = prefix
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()
        self._metric_points: List[MetricPoint] = []

    def _build_name(self, name: str) -> str:
        """Build full metric name with prefix."""
        return f"{self.prefix}.{name}" if self.prefix else name

    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter metric.

        Args:
            name: Metric name
            value: Amount to increment (default: 1.0)
            tags: Additional tags for the metric
        """
        full_name = self._build_name(name)
        with self._lock:
            self._counters[full_name] += value
            self._metric_points.append(MetricPoint(
                name=full_name,
                value=value,
                timestamp=time.time(),
                tags=tags or {},
                metric_type="counter"
            ))

    def decrement(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Decrement a counter metric.

        Args:
            name: Metric name
            value: Amount to decrement (default: 1.0)
            tags: Additional tags for the metric
        """
        self.increment(name, -value, tags)

    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Set a gauge metric (point-in-time value).

        Args:
            name: Metric name
            value: Current value
            tags: Additional tags for the metric
        """
        full_name = self._build_name(name)
        with self._lock:
            self._gauges[full_name] = value
            self._metric_points.append(MetricPoint(
                name=full_name,
                value=value,
                timestamp=time.time(),
                tags=tags or {},
                metric_type="gauge"
            ))

    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a histogram value (for distributions).

        Args:
            name: Metric name
            value: Value to record
            tags: Additional tags for the metric
        """
        full_name = self._build_name(name)
        with self._lock:
            self._histograms[full_name].append(value)
            self._metric_points.append(MetricPoint(
                name=full_name,
                value=value,
                timestamp=time.time(),
                tags=tags or {},
                metric_type="histogram"
            ))

    def timing(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a timing metric (convenience method for histograms).

        Args:
            name: Metric name
            duration_ms: Duration in milliseconds
            tags: Additional tags for the metric
        """
        self.histogram(name, duration_ms, tags)

    def get_counter(self, name: str) -> float:
        """
        Get current counter value.

        Args:
            name: Metric name

        Returns:
            Current counter value
        """
        full_name = self._build_name(name)
        with self._lock:
            return self._counters.get(full_name, 0.0)

    def get_gauge(self, name: str) -> Optional[float]:
        """
        Get current gauge value.

        Args:
            name: Metric name

        Returns:
            Current gauge value or None
        """
        full_name = self._build_name(name)
        with self._lock:
            return self._gauges.get(full_name)

    def get_histogram_stats(self, name: str) -> Optional[Dict[str, float]]:
        """
        Get histogram statistics.

        Args:
            name: Metric name

        Returns:
            Dict with min, max, mean, p50, p95, p99 or None
        """
        full_name = self._build_name(name)
        with self._lock:
            values = self._histograms.get(full_name, [])
            if not values:
                return None

            sorted_values = sorted(values)
            count = len(sorted_values)

            return {
                "count": count,
                "min": sorted_values[0],
                "max": sorted_values[-1],
                "mean": sum(sorted_values) / count,
                "p50": sorted_values[int(count * 0.50)],
                "p95": sorted_values[int(count * 0.95)] if count > 1 else sorted_values[0],
                "p99": sorted_values[int(count * 0.99)] if count > 1 else sorted_values[0],
            }

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all current metrics.

        Returns:
            Dict with counters, gauges, and histogram stats
        """
        with self._lock:
            result = {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {}
            }

            for name in self._histograms.keys():
                # Remove prefix for output
                display_name = name[len(self.prefix) + 1:] if self.prefix else name
                stats = self.get_histogram_stats(display_name)
                if stats:
                    result["histograms"][display_name] = stats

            return result

    def get_recent_points(self, limit: int = 100) -> List[MetricPoint]:
        """
        Get recent metric points.

        Args:
            limit: Maximum number of points to return

        Returns:
            List of recent metric points
        """
        with self._lock:
            return self._metric_points[-limit:]

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._metric_points.clear()

    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string
        """
        lines = []

        with self._lock:
            # Export counters
            for name, value in self._counters.items():
                safe_name = name.replace(".", "_").replace("-", "_")
                lines.append(f"# TYPE {safe_name} counter")
                lines.append(f"{safe_name} {value}")

            # Export gauges
            for name, value in self._gauges.items():
                safe_name = name.replace(".", "_").replace("-", "_")
                lines.append(f"# TYPE {safe_name} gauge")
                lines.append(f"{safe_name} {value}")

            # Export histogram summaries
            for name, values in self._histograms.items():
                if not values:
                    continue

                safe_name = name.replace(".", "_").replace("-", "_")
                stats = self.get_histogram_stats(name[len(self.prefix) + 1:] if self.prefix else name)

                lines.append(f"# TYPE {safe_name} summary")
                lines.append(f"{safe_name}_count {stats['count']}")
                lines.append(f"{safe_name}_sum {sum(values)}")
                lines.append(f"{safe_name}{{quantile=\"0.5\"}} {stats['p50']}")
                lines.append(f"{safe_name}{{quantile=\"0.95\"}} {stats['p95']}")
                lines.append(f"{safe_name}{{quantile=\"0.99\"}} {stats['p99']}")

        return "\n".join(lines) + "\n"


# ============================================================================
# Context Manager for Timing
# ============================================================================

class Timer:
    """
    Context manager for timing operations.

    Example:
        ```python
        metrics = Metrics()
        with Timer(metrics, "operation.duration"):
            # Do work
            pass
        ```
    """

    def __init__(self, metrics: Metrics, metric_name: str, tags: Optional[Dict[str, str]] = None):
        """
        Initialize timer.

        Args:
            metrics: Metrics instance
            metric_name: Name of timing metric
            tags: Additional tags
        """
        self.metrics = metrics
        self.metric_name = metric_name
        self.tags = tags
        self.start_time: Optional[float] = None

    def __enter__(self):
        """Start timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and record metric."""
        if self.start_time is not None:
            duration_ms = (time.time() - self.start_time) * 1000
            self.metrics.timing(self.metric_name, duration_ms, self.tags)
