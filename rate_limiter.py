"""
Advanced rate limiting with exponential backoff, token budgeting, and circuit breaker.
Prevents 429 errors and optimizes API usage patterns.
"""

import time
import json
from pathlib import Path
from threading import Lock
from typing import Optional
from collections import defaultdict, deque
import sys


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
RATE_LIMIT_CONFIG = BASE_DIR / "config" / "rate_limits.json"


class TokenBucket:
    """Token bucket for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Max tokens in bucket
            refill_rate: Tokens per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = Lock()

    def _refill(self) -> None:
        """Add tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def wait_until_available(self, tokens: int = 1) -> float:
        """Wait until tokens are available. Returns wait time."""
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0

            deficit = tokens - self.tokens
            wait_time = deficit / self.refill_rate
            self.tokens = 0
            self.last_refill = time.time() + wait_time
            return wait_time


class CircuitBreaker:
    """Circuit breaker pattern for API resilience."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
        self._lock = Lock()

    def record_success(self) -> None:
        """Record successful call."""
        with self._lock:
            self.failure_count = 0
            self.state = "closed"

    def record_failure(self) -> None:
        """Record failed call."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"

    def is_open(self) -> bool:
        """Check if circuit is open."""
        with self._lock:
            if self.state == "open":
                elapsed = time.time() - (self.last_failure_time or 0)
                if elapsed >= self.recovery_timeout:
                    self.state = "half_open"
                    self.failure_count = 0
                    return False
                return True
            return False

    def can_attempt(self) -> bool:
        """Check if attempt is allowed."""
        with self._lock:
            return self.state != "open"


class RateLimiter:
    """
    Comprehensive rate limiter with:
    - Per-model token budgets
    - Exponential backoff for failures
    - Sliding window rate limiting
    - Circuit breaker for failing services
    """

    def __init__(self):
        self._token_buckets: dict[str, TokenBucket] = {}
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._backoff_state: dict[str, tuple[int, float]] = {}  # (attempt, next_time)
        self._request_history: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()
        self._load_config()

    def _load_config(self) -> None:
        """Load rate limit configuration."""
        if RATE_LIMIT_CONFIG.exists():
            try:
                config = json.loads(RATE_LIMIT_CONFIG.read_text(encoding="utf-8"))
                for model, limits in config.items():
                    capacity = limits.get("capacity", 100)
                    refill_rate = limits.get("refill_rate", 10.0)
                    self._token_buckets[model] = TokenBucket(capacity, refill_rate)
            except Exception as e:
                print(f"[RateLimiter] ⚠️ Config load failed: {e}")

    def _get_bucket(self, model: str) -> TokenBucket:
        """Get or create token bucket for model."""
        if model not in self._token_buckets:
            # Default: 100 capacity, 10 tokens/sec
            self._token_buckets[model] = TokenBucket(capacity=100, refill_rate=10.0)
        return self._token_buckets[model]

    def _get_circuit(self, model: str) -> CircuitBreaker:
        """Get or create circuit breaker for model."""
        if model not in self._circuit_breakers:
            self._circuit_breakers[model] = CircuitBreaker()
        return self._circuit_breakers[model]

    def can_request(self, model: str, tokens: int = 1) -> bool:
        """Check if request is allowed."""
        circuit = self._get_circuit(model)
        if not circuit.can_attempt():
            return False

        # Check backoff
        if model in self._backoff_state:
            attempt, next_time = self._backoff_state[model]
            if time.time() < next_time:
                return False

        # Check token availability
        bucket = self._get_bucket(model)
        return bucket.consume(tokens)

    def wait_for_request(self, model: str, tokens: int = 1) -> float:
        """
        Wait until request is allowed.
        Returns: wait time in seconds
        """
        circuit = self._get_circuit(model)

        # Wait for circuit to close
        while not circuit.can_attempt():
            time.sleep(0.1)

        # Wait for backoff
        if model in self._backoff_state:
            attempt, next_time = self._backoff_state[model]
            wait = max(0, next_time - time.time())
            if wait > 0:
                time.sleep(wait)

        # Wait for tokens
        bucket = self._get_bucket(model)
        wait = bucket.wait_until_available(tokens)
        if wait > 0:
            time.sleep(wait)
        return wait

    def record_request(self, model: str) -> None:
        """Record successful request."""
        with self._lock:
            now = time.time()
            self._request_history[model].append(now)
            # Keep last 100 requests for sliding window
            while len(self._request_history[model]) > 100:
                self._request_history[model].popleft()
        self._get_circuit(model).record_success()
        # Clear backoff
        self._backoff_state.pop(model, None)

    def record_rate_limit(self, model: str, attempt: int = 0) -> None:
        """Record rate limit error (429). Triggers exponential backoff."""
        circuit = self._get_circuit(model)
        circuit.record_failure()

        # Exponential backoff: 2^attempt, max 300s
        wait = min(2 ** attempt, 300)
        self._backoff_state[model] = (attempt + 1, time.time() + wait)
        print(f"[RateLimiter] ⏸️  {model} rate limited. Backoff: {wait}s")

    def record_error(self, model: str) -> None:
        """Record other API errors."""
        self._get_circuit(model).record_failure()

    def record_success(self, model: str) -> None:
        """Record successful API call."""
        self.record_request(model)

    def get_requests_per_minute(self, model: str) -> float:
        """Get recent request rate."""
        with self._lock:
            history = self._request_history[model]
            if not history:
                return 0.0
            now = time.time()
            cutoff = now - 60
            recent = sum(1 for t in history if t > cutoff)
            return float(recent)

    def get_stats(self, model: str) -> dict:
        """Get detailed stats for model."""
        bucket = self._get_bucket(model)
        circuit = self._get_circuit(model)
        with self._lock:
            history = self._request_history[model]
            rpm = self.get_requests_per_minute(model)

        backoff = self._backoff_state.get(model)
        backoff_info = None
        if backoff:
            attempt, next_time = backoff
            backoff_info = {
                "attempt": attempt,
                "next_available": max(0, next_time - time.time()),
            }

        return {
            "model": model,
            "tokens_available": int(bucket.tokens),
            "circuit_state": circuit.state,
            "failures": circuit.failure_count,
            "requests_per_minute": rpm,
            "backoff": backoff_info,
            "history_count": len(history),
        }

    def reset_model(self, model: str) -> None:
        """Reset rate limiting for a model."""
        with self._lock:
            self._token_buckets.pop(model, None)
            self._circuit_breakers.pop(model, None)
            self._backoff_state.pop(model, None)
            self._request_history[model].clear()

    def update_budget(self, model: str, capacity: int, refill_rate: float) -> None:
        """Update token budget for model."""
        self._token_buckets[model] = TokenBucket(capacity, refill_rate)

    def save_config(self) -> None:
        """Save current configuration."""
        config = {}
        for model, bucket in self._token_buckets.items():
            config[model] = {
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate,
            }
        try:
            RATE_LIMIT_CONFIG.parent.mkdir(parents=True, exist_ok=True)
            RATE_LIMIT_CONFIG.write_text(
                json.dumps(config, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            print(f"[RateLimiter] ⚠️ Config save failed: {e}")


# Global instance
_limiter: Optional[RateLimiter] = None
_limiter_lock = Lock()


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter."""
    global _limiter
    if _limiter is None:
        with _limiter_lock:
            if _limiter is None:
                _limiter = RateLimiter()
    return _limiter
