"""
Multi-Model Router & Load Balancer for JARVIS
Distributes requests across multiple AI models to effectively eliminate rate limits
"""

import json
import time
import threading
import logging
from enum import Enum
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import random

logger = logging.getLogger("model_router")


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"              # Rotate through models
    LEAST_LOADED = "least_loaded"            # Use model with fewest active requests
    WEIGHTED_RANDOM = "weighted_random"      # Random based on model health/speed
    FASTEST = "fastest"                      # Use fastest responding model
    LOWEST_RATE_LIMIT = "lowest_rate_limit"  # Use model with most remaining quota


@dataclass
class ModelMetrics:
    """Track per-model metrics for intelligent routing"""
    model_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency: float = 0.0
    rate_limit_hits: int = 0
    last_error: str = ""
    last_error_time: Optional[datetime] = None
    is_healthy: bool = True
    health_check_time: datetime = field(default_factory=datetime.now)
    tokens_used: int = 0
    tokens_limit: int = 100000  # Per-model quota (free tier)
    active_requests: int = 0
    request_history: List[float] = field(default_factory=list)  # Last 60s window
    _lock: threading.Lock = field(default_factory=threading.Lock)

    @property
    def avg_latency(self) -> float:
        """Average response time for this model"""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency / self.successful_requests if self.successful_requests > 0 else 0.0

    @property
    def error_rate(self) -> float:
        """Error rate for this model (0.0 to 1.0)"""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests

    @property
    def remaining_quota(self) -> int:
        """Remaining tokens for this model"""
        return max(0, self.tokens_limit - self.tokens_used)

    @property
    def health_score(self) -> float:
        """Health score 0-100 (higher is better)"""
        # Base score
        score = 100.0
        
        # Penalize errors
        score -= (self.error_rate * 30)
        
        # Penalize rate limits
        score -= min(self.rate_limit_hits * 5, 30)
        
        # Bonus for availability
        if self.is_healthy:
            score += 10
        
        return max(0, min(100, score))

    def record_request(self, success: bool, latency: float, tokens_used: int = 0):
        """Record a request"""
        with self._lock:
            self.total_requests += 1
            self.total_latency += latency
            self.active_requests = max(0, self.active_requests - 1)
            
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
            
            self.tokens_used += tokens_used
            self.request_history.append(time.time())
            
            # Keep only last 60 seconds
            cutoff = time.time() - 60
            self.request_history = [t for t in self.request_history if t > cutoff]

    def record_rate_limit(self):
        """Record a rate limit hit"""
        with self._lock:
            self.rate_limit_hits += 1
            self.failed_requests += 1
            self.last_error = "Rate limit exceeded"
            self.last_error_time = datetime.now()
            self.is_healthy = False

    def record_error(self, error: str):
        """Record an error"""
        with self._lock:
            self.failed_requests += 1
            self.last_error = error
            self.last_error_time = datetime.now()
            if "rate" in error.lower():
                self.is_healthy = False

    def requests_per_minute(self) -> int:
        """Requests in last minute"""
        return len(self.request_history)


class ModelRouter:
    """
    Intelligent model router that distributes requests across multiple models
    to effectively eliminate rate limits by load balancing
    """

    def __init__(self, models: List[str], strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOADED):
        """
        Initialize model router
        
        Args:
            models: List of available model IDs
            strategy: Load balancing strategy to use
        """
        self.models = models
        self.strategy = strategy
        self.metrics: Dict[str, ModelMetrics] = {
            model: ModelMetrics(model_id=model) for model in models
        }
        self.current_round_robin_index = 0
        self._lock = threading.Lock()
        self.fallback_models = models.copy()
        random.shuffle(self.fallback_models)
        
        logger.info(f"ModelRouter initialized with {len(models)} models using {strategy.value} strategy")

    def select_model(self, exclude_models: Optional[List[str]] = None) -> str:
        """
        Select best model for next request based on strategy
        
        Args:
            exclude_models: Models to exclude from selection (e.g., failed models)
            
        Returns:
            Selected model ID
        """
        exclude = set(exclude_models or [])
        available = [m for m in self.models if m not in exclude and self.metrics[m].is_healthy]
        
        if not available:
            # Fallback: use any model if all are marked unhealthy
            available = [m for m in self.models if m not in exclude]
        
        if not available:
            raise RuntimeError("No available models")

        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._select_round_robin(available)
        
        elif self.strategy == LoadBalancingStrategy.LEAST_LOADED:
            return self._select_least_loaded(available)
        
        elif self.strategy == LoadBalancingStrategy.FASTEST:
            return self._select_fastest(available)
        
        elif self.strategy == LoadBalancingStrategy.LOWEST_RATE_LIMIT:
            return self._select_lowest_rate_limit(available)
        
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_RANDOM:
            return self._select_weighted_random(available)
        
        else:
            return available[0]

    def _select_round_robin(self, available: List[str]) -> str:
        """Round-robin selection"""
        with self._lock:
            self.current_round_robin_index = (self.current_round_robin_index + 1) % len(available)
            return available[self.current_round_robin_index]

    def _select_least_loaded(self, available: List[str]) -> str:
        """Select model with fewest active requests"""
        return min(available, key=lambda m: self.metrics[m].active_requests)

    def _select_fastest(self, available: List[str]) -> str:
        """Select fastest responding model"""
        return min(available, key=lambda m: self.metrics[m].avg_latency or float('inf'))

    def _select_lowest_rate_limit(self, available: List[str]) -> str:
        """Select model with most remaining quota"""
        return max(available, key=lambda m: self.metrics[m].remaining_quota)

    def _select_weighted_random(self, available: List[str]) -> str:
        """Random selection weighted by health score"""
        scores = {m: self.metrics[m].health_score for m in available}
        total_score = sum(scores.values())
        
        if total_score == 0:
            return random.choice(available)
        
        # Weighted random selection
        rand = random.uniform(0, total_score)
        cumulative = 0
        for model, score in scores.items():
            cumulative += score
            if rand <= cumulative:
                return model
        
        return available[-1]

    def get_model_status(self) -> Dict:
        """Get status of all models"""
        status = {}
        for model_id, metrics in self.metrics.items():
            status[model_id] = {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "avg_latency": round(metrics.avg_latency, 3),
                "error_rate": round(metrics.error_rate * 100, 1),
                "rate_limit_hits": metrics.rate_limit_hits,
                "health_score": round(metrics.health_score, 1),
                "is_healthy": metrics.is_healthy,
                "active_requests": metrics.active_requests,
                "tokens_used": metrics.tokens_used,
                "remaining_quota": metrics.remaining_quota,
                "requests_per_minute": metrics.requests_per_minute(),
                "last_error": metrics.last_error,
            }
        return status

    def get_best_models(self, count: int = 3) -> List[Tuple[str, float]]:
        """Get top N healthiest models with their health scores"""
        models_health = [(m, self.metrics[m].health_score) for m in self.models]
        models_health.sort(key=lambda x: x[1], reverse=True)
        return models_health[:count]

    def get_recommended_model(self) -> str:
        """Get the single best model for current conditions"""
        best_models = self.get_best_models(1)
        if best_models:
            return best_models[0][0]
        return self.models[0]

    def mark_rate_limited(self, model: str):
        """Mark model as rate limited"""
        self.metrics[model].record_rate_limit()
        logger.warning(f"Model {model} hit rate limit. Health score: {self.metrics[model].health_score}")

    def mark_error(self, model: str, error: str):
        """Mark model with error"""
        self.metrics[model].record_error(error)
        logger.error(f"Model {model} error: {error}")

    def mark_recovered(self, model: str):
        """Mark model as recovered"""
        self.metrics[model].is_healthy = True
        self.metrics[model].rate_limit_hits = max(0, self.metrics[model].rate_limit_hits - 1)
        logger.info(f"Model {model} recovered")

    def record_success(self, model: str, latency: float, tokens_used: int = 0):
        """Record successful request"""
        self.metrics[model].record_request(True, latency, tokens_used)

    def record_failure(self, model: str, latency: float):
        """Record failed request"""
        self.metrics[model].record_request(False, latency)


# Global router instance
_model_router: Optional[ModelRouter] = None
_router_lock = threading.Lock()


def get_model_router(models: Optional[List[str]] = None, 
                     strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOADED) -> ModelRouter:
    """Get or create global model router instance (singleton)"""
    global _model_router
    
    if _model_router is None:
        with _router_lock:
            if _model_router is None:
                if not models:
                    from or_client import TEXT_MODELS
                    models = TEXT_MODELS
                
                _model_router = ModelRouter(models, strategy)
                logger.info("Created global ModelRouter instance")
    
    return _model_router


def reset_model_router():
    """Reset router (for testing)"""
    global _model_router
    _model_router = None


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.DEBUG)
    
    test_models = [
        "model-1",
        "model-2",
        "model-3",
        "model-4",
    ]
    
    router = ModelRouter(test_models, LoadBalancingStrategy.LEAST_LOADED)
    
    # Simulate some requests
    for i in range(20):
        model = router.select_model()
        latency = (i % 3) * 0.1  # Vary latency
        tokens = (i % 5) * 100
        
        # Sometimes mark as rate limited
        if i == 5:
            router.mark_rate_limited("model-1")
        elif i == 15:
            router.mark_recovered("model-1")
        
        router.record_success(model, latency, tokens)
        print(f"Request {i}: {model} (latency: {latency}s, tokens: {tokens})")
    
    # Print status
    print("\n=== Model Status ===")
    for model_id, status in router.get_model_status().items():
        print(f"\n{model_id}:")
        for key, value in status.items():
            print(f"  {key}: {value}")
    
    print("\n=== Best Models ===")
    for model, score in router.get_best_models(2):
        print(f"  {model}: {score}")
    
    print(f"\n=== Recommended Model ===")
    print(f"  {router.get_recommended_model()}")
