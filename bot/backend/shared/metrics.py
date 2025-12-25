"""
Metrics Collection for Observability
Task 9: Track requests, errors, and latency per tenant
"""
from typing import Dict, Optional
from time import time
from collections import defaultdict
from threading import Lock
import json

from .logger import logger


class MetricsCollector:
    """
    Metrics collector for Prometheus export.
    
    Tracks:
    - HTTP requests per tenant (counter)
    - Errors per tenant (counter)
    - Request latency per tenant (histogram)
    - Active requests per tenant (gauge)
    """
    
    def __init__(self):
        """Initialize metrics collector"""
        self._lock = Lock()
        
        # Counters: tenant_id -> count
        self._request_count: Dict[str, int] = defaultdict(int)
        self._error_count: Dict[str, int] = defaultdict(int)
        
        # Histogram: tenant_id -> list of latencies (seconds)
        self._latencies: Dict[str, list[float]] = defaultdict(list)
        
        # Gauge: tenant_id -> current active requests
        self._active_requests: Dict[str, int] = defaultdict(int)
        
        # Error types: tenant_id -> error_code -> count
        self._error_types: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        logger.info("MetricsCollector initialized")
    
    def record_request(
        self,
        tenant_id: str,
        endpoint: str,
        method: str = "POST",
        status_code: int = 200,
        latency_seconds: float = 0.0,
    ):
        """
        Record HTTP request.
        
        Args:
            tenant_id: Tenant ID
            endpoint: Endpoint path
            method: HTTP method
            status_code: HTTP status code
            latency_seconds: Request latency in seconds
        """
        with self._lock:
            # Increment request count
            self._request_count[tenant_id] += 1
            
            # Record latency
            self._latencies[tenant_id].append(latency_seconds)
            # Keep only last 1000 latencies per tenant
            if len(self._latencies[tenant_id]) > 1000:
                self._latencies[tenant_id] = self._latencies[tenant_id][-1000:]
            
            # Record error if status >= 400
            if status_code >= 400:
                self._error_count[tenant_id] += 1
    
    def record_error(
        self,
        tenant_id: str,
        error_code: str,
    ):
        """
        Record error.
        
        Args:
            tenant_id: Tenant ID
            error_code: Error code
        """
        with self._lock:
            self._error_count[tenant_id] += 1
            self._error_types[tenant_id][error_code] += 1
    
    def start_request(self, tenant_id: str):
        """Increment active requests counter"""
        with self._lock:
            self._active_requests[tenant_id] += 1
    
    def end_request(self, tenant_id: str):
        """Decrement active requests counter"""
        with self._lock:
            if self._active_requests[tenant_id] > 0:
                self._active_requests[tenant_id] -= 1
    
    def get_metrics(self) -> Dict[str, any]:
        """
        Get current metrics snapshot.
        
        Returns:
            Dict with metrics data
        """
        with self._lock:
            metrics = {
                "requests": dict(self._request_count),
                "errors": dict(self._error_count),
                "active_requests": dict(self._active_requests),
                "error_types": {
                    tenant: dict(errors) 
                    for tenant, errors in self._error_types.items()
                },
            }
            
            # Calculate latency statistics
            latency_stats = {}
            for tenant_id, latencies in self._latencies.items():
                if latencies:
                    latency_stats[tenant_id] = {
                        "count": len(latencies),
                        "min": min(latencies),
                        "max": max(latencies),
                        "avg": sum(latencies) / len(latencies),
                        "p50": self._percentile(latencies, 50),
                        "p95": self._percentile(latencies, 95),
                        "p99": self._percentile(latencies, 99),
                    }
            
            metrics["latency"] = latency_stats
            
            return metrics
    
    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus format.
        
        Returns:
            Prometheus metrics text format
        """
        metrics = self.get_metrics()
        lines = []
        
        # Request counter
        lines.append("# TYPE bot_requests_total counter")
        for tenant_id, count in metrics["requests"].items():
            lines.append(f'bot_requests_total{{tenant_id="{tenant_id}"}} {count}')
        
        # Error counter
        lines.append("# TYPE bot_errors_total counter")
        for tenant_id, count in metrics["errors"].items():
            lines.append(f'bot_errors_total{{tenant_id="{tenant_id}"}} {count}')
        
        # Active requests gauge
        lines.append("# TYPE bot_active_requests gauge")
        for tenant_id, count in metrics["active_requests"].items():
            lines.append(f'bot_active_requests{{tenant_id="{tenant_id}"}} {count}')
        
        # Latency histogram (using summary for simplicity)
        lines.append("# TYPE bot_request_latency_seconds summary")
        for tenant_id, stats in metrics["latency"].items():
            lines.append(f'bot_request_latency_seconds{{tenant_id="{tenant_id}",quantile="0.5"}} {stats["p50"]}')
            lines.append(f'bot_request_latency_seconds{{tenant_id="{tenant_id}",quantile="0.95"}} {stats["p95"]}')
            lines.append(f'bot_request_latency_seconds{{tenant_id="{tenant_id}",quantile="0.99"}} {stats["p99"]}')
            lines.append(f'bot_request_latency_seconds_sum{{tenant_id="{tenant_id}"}} {stats["avg"] * stats["count"]}')
            lines.append(f'bot_request_latency_seconds_count{{tenant_id="{tenant_id}"}} {stats["count"]}')
        
        # Error types
        lines.append("# TYPE bot_error_types_total counter")
        for tenant_id, error_types in metrics["error_types"].items():
            for error_code, count in error_types.items():
                lines.append(f'bot_error_types_total{{tenant_id="{tenant_id}",error_code="{error_code}"}} {count}')
        
        return "\n".join(lines) + "\n"
    
    @staticmethod
    def _percentile(data: list[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        
        return sorted_data[index]
    
    def reset(self):
        """Reset all metrics (for testing)"""
        with self._lock:
            self._request_count.clear()
            self._error_count.clear()
            self._latencies.clear()
            self._active_requests.clear()
            self._error_types.clear()


# Global metrics collector instance
metrics_collector = MetricsCollector()


class RequestMetrics:
    """
    Context manager for tracking request metrics.
    
    Usage:
        with RequestMetrics(tenant_id, endpoint):
            # process request
    """
    
    def __init__(
        self,
        tenant_id: str,
        endpoint: str,
        method: str = "POST",
    ):
        """
        Initialize request metrics tracker.
        
        Args:
            tenant_id: Tenant ID
            endpoint: Endpoint path
            method: HTTP method
        """
        self.tenant_id = tenant_id
        self.endpoint = endpoint
        self.method = method
        self.start_time: Optional[float] = None
        self.status_code: int = 200
    
    def __enter__(self):
        """Start tracking request"""
        self.start_time = time()
        metrics_collector.start_request(self.tenant_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End tracking request"""
        if self.start_time:
            latency = time() - self.start_time
            metrics_collector.record_request(
                tenant_id=self.tenant_id,
                endpoint=self.endpoint,
                method=self.method,
                status_code=self.status_code,
                latency_seconds=latency,
            )
            metrics_collector.end_request(self.tenant_id)
        
        return False  # Don't suppress exceptions

