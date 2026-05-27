"""
Performance metrics and monitoring for JARVIS upgrades.
Tracks API usage, cache hit rates, memory operations, and system health.
"""

import time
import json
from pathlib import Path
from typing import Dict, Any, Optional
from collections import defaultdict
from threading import Lock
import sys


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
METRICS_PATH = BASE_DIR / "metrics" / "performance.json"
METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)


class MetricsCollector:
    """Collect and aggregate performance metrics."""

    def __init__(self):
        self._metrics: Dict[str, Any] = {
            "api_calls": defaultdict(lambda: {"count": 0, "tokens": 0, "latency_total": 0.0}),
            "cache_hits": defaultdict(int),
            "cache_misses": defaultdict(int),
            "memory_ops": {"reads": 0, "writes": 0, "searches": 0},
            "errors": defaultdict(int),
            "rate_limits": defaultdict(int),
            "startup_time": 0.0,
        }
        self._lock = Lock()
        self._start_time = time.time()

    def record_api_call(
        self,
        model: str,
        tokens_used: int = 0,
        latency: float = 0.0,
        cached: bool = False,
    ) -> None:
        """Record API call metrics."""
        with self._lock:
            if cached:
                self._metrics["cache_hits"][model] += 1
            else:
                self._metrics["cache_misses"][model] += 1
                stats = self._metrics["api_calls"][model]
                stats["count"] += 1
                stats["tokens"] += tokens_used
                stats["latency_total"] += latency

    def record_memory_operation(
        self,
        operation: str,  # "read", "write", "search"
        duration: float = 0.0,
        success: bool = True,
    ) -> None:
        """Record memory operation metrics."""
        with self._lock:
            if operation in ["read", "write", "search"]:
                self._metrics["memory_ops"][operation] += 1

    def record_error(self, error_type: str) -> None:
        """Record error occurrence."""
        with self._lock:
            self._metrics["errors"][error_type] += 1

    def record_rate_limit(self, model: str) -> None:
        """Record rate limit hit."""
        with self._lock:
            self._metrics["rate_limits"][model] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        with self._lock:
            api_stats = {}
            for model, stats in self._metrics["api_calls"].items():
                if stats["count"] > 0:
                    avg_latency = stats["latency_total"] / stats["count"]
                else:
                    avg_latency = 0
                
                cache_hits = self._metrics["cache_hits"].get(model, 0)
                cache_misses = self._metrics["cache_misses"].get(model, 0)
                total = cache_hits + cache_misses
                hit_rate = (cache_hits / total * 100) if total > 0 else 0
                
                api_stats[model] = {
                    "calls": stats["count"],
                    "tokens": stats["tokens"],
                    "avg_latency_ms": round(avg_latency * 1000, 2),
                    "cache_hits": cache_hits,
                    "cache_misses": cache_misses,
                    "cache_hit_rate": round(hit_rate, 1),
                }
            
            total_cache_hits = sum(self._metrics["cache_hits"].values())
            total_cache_misses = sum(self._metrics["cache_misses"].values())
            total_cache = total_cache_hits + total_cache_misses
            overall_hit_rate = (total_cache_hits / total_cache * 100) if total_cache > 0 else 0
            
            return {
                "api": api_stats,
                "cache": {
                    "total_hits": total_cache_hits,
                    "total_misses": total_cache_misses,
                    "overall_hit_rate": round(overall_hit_rate, 1),
                },
                "memory": dict(self._metrics["memory_ops"]),
                "errors": dict(self._metrics["errors"]),
                "rate_limits": dict(self._metrics["rate_limits"]),
                "uptime_seconds": round(time.time() - self._start_time, 1),
            }

    def save_metrics(self) -> None:
        """Save metrics to file."""
        stats = self.get_stats()
        try:
            METRICS_PATH.write_text(
                json.dumps(stats, indent=2, default=str),
                encoding="utf-8"
            )
            print(f"[Metrics] 💾 Saved to {METRICS_PATH}")
        except Exception as e:
            print(f"[Metrics] ⚠️  Save failed: {e}")

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._metrics = {
                "api_calls": defaultdict(lambda: {"count": 0, "tokens": 0, "latency_total": 0.0}),
                "cache_hits": defaultdict(int),
                "cache_misses": defaultdict(int),
                "memory_ops": {"reads": 0, "writes": 0, "searches": 0},
                "errors": defaultdict(int),
                "rate_limits": defaultdict(int),
            }
            self._start_time = time.time()


class HealthMonitor:
    """Monitor system health and generate alerts."""

    def __init__(self):
        self._thresholds = {
            "error_rate": 0.1,  # 10% errors
            "rate_limit_rate": 0.05,  # 5% rate limited
            "cache_hit_rate": 0.3,  # Alert if below 30%
        }
        self._alerts: list[str] = []
        self._lock = Lock()

    def check_health(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze metrics and generate health report."""
        with self._lock:
            self._alerts.clear()
            
            health_status = "healthy"
            
            # Check error rate
            if stats.get("errors"):
                total_errors = sum(stats["errors"].values())
                api_calls = sum(
                    s.get("calls", 0) for s in stats.get("api", {}).values()
                )
                if api_calls > 0:
                    error_rate = total_errors / api_calls
                    if error_rate > self._thresholds["error_rate"]:
                        self._alerts.append(
                            f"⚠️  High error rate: {error_rate * 100:.1f}%"
                        )
                        health_status = "degraded"
            
            # Check rate limiting
            if stats.get("rate_limits"):
                total_limits = sum(stats["rate_limits"].values())
                api_calls = sum(
                    s.get("calls", 0) for s in stats.get("api", {}).values()
                )
                if api_calls > 0:
                    limit_rate = total_limits / api_calls
                    if limit_rate > self._thresholds["rate_limit_rate"]:
                        self._alerts.append(
                            f"⚠️  Frequent rate limiting: {limit_rate * 100:.1f}%"
                        )
                        health_status = "degraded"
            
            # Check cache hit rate
            cache_hit_rate = stats.get("cache", {}).get("overall_hit_rate", 0)
            if cache_hit_rate < self._thresholds["cache_hit_rate"]:
                self._alerts.append(
                    f"⚠️  Low cache hit rate: {cache_hit_rate:.1f}%"
                )
            
            return {
                "status": health_status,
                "alerts": self._alerts,
                "checks": {
                    "error_rate": len([a for a in self._alerts if "error" in a]) == 0,
                    "rate_limiting": len([a for a in self._alerts if "rate" in a]) == 0,
                    "cache_efficiency": cache_hit_rate >= self._thresholds["cache_hit_rate"],
                }
            }

    def print_report(self, stats: Dict[str, Any]) -> None:
        """Print health report to console."""
        health = self.check_health(stats)
        
        print("\n" + "=" * 60)
        print("🔍 JARVIS Health Report")
        print("=" * 60)
        
        status_icon = "✅" if health["status"] == "healthy" else "⚠️ "
        print(f"\nStatus: {status_icon} {health['status'].upper()}")
        
        if health["alerts"]:
            print("\nAlerts:")
            for alert in health["alerts"]:
                print(f"  {alert}")
        
        print("\nCache Performance:")
        cache = stats.get("cache", {})
        print(f"  Hit Rate: {cache.get('overall_hit_rate', 0):.1f}%")
        print(f"  Hits: {cache.get('total_hits', 0)}")
        print(f"  Misses: {cache.get('total_misses', 0)}")
        
        print("\nMemory Operations:")
        mem = stats.get("memory", {})
        print(f"  Reads: {mem.get('reads', 0)}")
        print(f"  Writes: {mem.get('writes', 0)}")
        print(f"  Searches: {mem.get('searches', 0)}")
        
        print("\nUptime:")
        print(f"  {stats.get('uptime_seconds', 0):.0f} seconds")
        
        print("=" * 60 + "\n")


# Global instances
_metrics_collector: Optional[MetricsCollector] = None
_health_monitor: Optional[HealthMonitor] = None
_monitor_lock = Lock()


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        with _monitor_lock:
            if _metrics_collector is None:
                _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_health_monitor() -> HealthMonitor:
    """Get or create global health monitor."""
    global _health_monitor
    if _health_monitor is None:
        with _monitor_lock:
            if _health_monitor is None:
                _health_monitor = HealthMonitor()
    return _health_monitor
