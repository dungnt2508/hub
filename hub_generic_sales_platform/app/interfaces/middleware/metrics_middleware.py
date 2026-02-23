"""
Prometheus metrics middleware - records request count and latency.
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.infrastructure.metrics import record_request, normalize_path


class MetricsMiddleware(BaseHTTPMiddleware):
    """Records HTTP request count and latency for Prometheus."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        path_template = normalize_path(request.url.path)
        record_request(
            method=request.method,
            path_template=path_template,
            status=response.status_code,
            duration_seconds=duration
        )
        return response
