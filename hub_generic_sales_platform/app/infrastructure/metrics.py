"""
Prometheus metrics for IRIS Hub.
Exposes: request count, latency, tier distribution (decision counts).
"""
import time
from typing import Optional, Tuple

try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Metrics (lazy init to avoid import-time side effects)
_http_requests_total: Optional["Counter"] = None
_http_request_duration_seconds: Optional["Histogram"] = None
_iris_decisions_total: Optional["Counter"] = None


def _ensure_metrics():
    """Initialize metrics on first use."""
    global _http_requests_total, _http_request_duration_seconds, _iris_decisions_total
    if not PROMETHEUS_AVAILABLE:
        return
    if _http_requests_total is not None:
        return
    _http_requests_total = Counter(
        "iris_http_requests_total",
        "Total HTTP requests",
        ["method", "path_template", "status"]
    )
    _http_request_duration_seconds = Histogram(
        "iris_http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["method", "path_template"],
        buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
    )
    _iris_decisions_total = Counter(
        "iris_decisions_total",
        "Total routing decisions by tier",
        ["tier"]
    )


def record_request(method: str, path_template: str, status: int, duration_seconds: float) -> None:
    """Record HTTP request metric."""
    if not PROMETHEUS_AVAILABLE:
        return
    _ensure_metrics()
    status_str = str(status)
    if status >= 500:
        status_str = "5xx"
    elif status >= 400:
        status_str = "4xx"
    elif status >= 300:
        status_str = "3xx"
    elif status >= 200:
        status_str = "2xx"
    _http_requests_total.labels(method=method, path_template=path_template, status=status_str).inc()
    _http_request_duration_seconds.labels(method=method, path_template=path_template).observe(duration_seconds)


def record_decision_tier(tier: str) -> None:
    """Record a routing decision by tier (fast_path, knowledge_path, agentic_path)."""
    if not PROMETHEUS_AVAILABLE:
        return
    _ensure_metrics()
    t = (tier or "unknown").lower()
    _iris_decisions_total.labels(tier=t).inc()


def get_prometheus_output() -> Tuple[bytes, str]:
    """Return (body, content_type) for /metrics endpoint."""
    if not PROMETHEUS_AVAILABLE:
        return b"# prometheus_client not installed\n", "text/plain; charset=utf-8"
    return generate_latest(), CONTENT_TYPE_LATEST


def normalize_path(path: str) -> str:
    """Normalize path for metrics (e.g. /api/v1/sessions/abc123 -> /api/v1/sessions/{id})."""
    if not path or path == "/":
        return path or "/"
    parts = path.strip("/").split("/")
    normalized = []
    for i, p in enumerate(parts):
        if p.isdigit() or (len(p) >= 32 and p.replace("-", "").isalnum()):
            normalized.append("{id}")
        elif len(p) == 36 and "-" in p:  # UUID
            normalized.append("{id}")
        else:
            normalized.append(p)
    return "/" + "/".join(normalized)
