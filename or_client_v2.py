"""
Enhanced OpenRouter Client with Multi-Model Load Balancing
Distributes requests across multiple models to eliminate rate limits
"""

import json
import sys
import time
import base64
import logging
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum

import requests

from cache_manager import get_cache_manager
from rate_limiter import get_rate_limiter
from request_queue import get_request_queue, RequestPriority
from model_router import get_model_router, LoadBalancingStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("openrouter_client_v2")

# ============================================================================
# Configuration
# ============================================================================

API_URL = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT = 120
DEFAULT_MAX_TOKENS = 2000
DEFAULT_TEMPERATURE = 0.7
RETRY_DELAY = 1
MAX_RETRIES_PER_MODEL = 2
MAX_RETRIES_TOTAL = 5  # Total retries across all models
CACHE_API_RESPONSES = True
CACHE_TTL = 3600  # 1 hour


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = _get_base_dir()
API_KEY_PATH = BASE_DIR / "config" / "api_keys.json"


def _load_api_key() -> str:
    try:
        with open(API_KEY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        key = data.get("openrouter_api_key", "").strip()
        if not key:
            raise ValueError("openrouter_api_key is empty in api_keys.json")
        return key
    except FileNotFoundError:
        raise RuntimeError(f"api_keys.json not found at: {API_KEY_PATH}")
    except Exception as e:
        raise RuntimeError(f"Failed to load OpenRouter API key: {e}")


# ============================================================================
# Available Models (Free Tier for Maximum Rate Limit Distribution)
# ============================================================================

TEXT_MODELS: List[str] = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "minimax/minimax-m2.5:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "qwen/qwen3-coder:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "google/gemma-3-27b-it:free",
    "arcee-ai/trinity-large-preview:free",
]

VISION_MODELS: List[str] = [
    "google/gemini-2.0-flash-lite-preview-02-05:free",
    "meta-llama/llama-3.2-90b-vision-instruct:free",
]


class OpenRouterClientV2:
    """
    Enhanced OpenRouter client with multi-model load balancing
    
    Features:
    - Intelligent model selection across 10+ models
    - Automatic failover when models rate limit
    - Load balancing strategies (round-robin, least-loaded, fastest, etc)
    - Per-model health tracking and metrics
    - Seamless integration with existing caching and rate limiting
    """

    def __init__(
        self,
        enable_caching: bool = True,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOADED,
        _cache_manager=None,
        _rate_limiter=None,
        _request_queue=None,
        _model_router=None,
    ):
        """
        Initialize enhanced OpenRouter client
        
        Args:
            enable_caching: Enable response caching
            strategy: Load balancing strategy
            _cache_manager: Cache manager instance (uses global if None)
            _rate_limiter: Rate limiter instance (uses global if None)
            _request_queue: Request queue instance (uses global if None)
            _model_router: Model router instance (uses global if None)
        """
        self.api_key = _load_api_key()
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/mark-xxv",
            "X-Title": "MARK XXV",
        }

        self.enable_caching = enable_caching
        self._cache_manager = _cache_manager or get_cache_manager()
        self._rate_limiter = _rate_limiter or get_rate_limiter()
        self._request_queue = _request_queue or get_request_queue()
        self._model_router = _model_router or get_model_router(TEXT_MODELS, strategy)

        logger.info(
            f"OpenRouterClientV2 initialized with {len(TEXT_MODELS)} models "
            f"using {strategy.value} strategy"
        )

    def _call_single_model(
        self,
        model: str,
        messages: List[dict],
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        response_format: Optional[dict] = None,
    ) -> Optional[str]:
        """
        Call a single model (internal helper)
        
        Returns:
            Response text or None if failed
        """
        payload: dict = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = response_format

        # Check cache for identical requests
        if CACHE_API_RESPONSES and self.enable_caching:
            cached = self._cache_manager.get_api_response("POST", API_URL, payload)
            if cached:
                logger.debug(f"[OpenRouter] Cache hit: {model}")
                self._model_router.record_success(model, 0.0)  # Cache hits are free
                return cached

        # Wait for rate limit clearance
        self._rate_limiter.wait_for_request(model)

        start_time = time.time()

        try:
            resp = requests.post(
                API_URL,
                headers=self._headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            latency = time.time() - start_time

            if resp.status_code == 429:
                logger.warning(f"[OpenRouter] {model} → Rate limited (429)")
                self._model_router.mark_rate_limited(model)
                self._rate_limiter.record_rate_limit(model)
                return None

            if resp.status_code == 200:
                data = resp.json()
                content = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                result = content.strip() if content else None

                # Cache successful response
                if result and CACHE_API_RESPONSES and self.enable_caching:
                    self._cache_manager.cache_api_response(
                        "POST", API_URL, payload, result, ttl=CACHE_TTL
                    )

                # Record success with token usage
                tokens_used = data.get("usage", {}).get("total_tokens", 0)
                self._model_router.record_success(model, latency, tokens_used)
                self._rate_limiter.record_success(model)

                logger.info(
                    f"[OpenRouter] {model} → Success ({latency:.2f}s, {tokens_used} tokens)"
                )
                return result

            logger.warning(
                f"[OpenRouter] {model} → HTTP {resp.status_code}"
            )
            self._model_router.record_failure(model, latency)
            self._rate_limiter.record_error(model)

        except requests.exceptions.Timeout:
            latency = time.time() - start_time
            logger.warning(f"[OpenRouter] {model} → Timeout after {latency:.2f}s")
            self._model_router.record_failure(model, latency)
            self._rate_limiter.record_error(model)
        except Exception as e:
            latency = time.time() - start_time
            logger.error(f"[OpenRouter] {model} → Unexpected error: {e}")
            self._model_router.record_failure(model, latency)
            self._rate_limiter.record_error(model)

        return None

    def _call_with_smart_fallback(
        self,
        messages: List[dict],
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        response_format: Optional[dict] = None,
    ) -> Optional[str]:
        """
        Call with automatic fallback across multiple models
        
        Strategy:
        1. Select best model based on health/load metrics
        2. If it fails, try alternatives
        3. Skip already-failed models
        4. Return first successful response
        
        Returns:
            Response text or None if all models fail
        """
        failed_models = set()
        attempts = 0

        for attempt in range(MAX_RETRIES_TOTAL):
            attempts += 1

            # Select best available model
            try:
                model = self._model_router.select_model(exclude_models=list(failed_models))
            except RuntimeError:
                logger.error("No available models remaining")
                return None

            logger.info(
                f"[OpenRouter] Attempt {attempt + 1}/{MAX_RETRIES_TOTAL}: {model}"
            )

            # Try to call this model
            result = self._call_single_model(
                model, messages, max_tokens, temperature, response_format
            )

            if result:
                return result  # Success!

            # Mark as failed and try next
            failed_models.add(model)

            # Brief delay before retry
            if attempt < MAX_RETRIES_TOTAL - 1:
                time.sleep(RETRY_DELAY)

        logger.error(f"[OpenRouter] All {attempts} attempts failed")
        return None

    def call(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        response_format: Optional[dict] = None,
        priority: RequestPriority = RequestPriority.NORMAL,
    ) -> Optional[str]:
        """
        Call OpenRouter API with automatic load balancing
        
        Args:
            messages: Chat messages
            model: Specific model (if None, auto-select best)
            max_tokens: Max response tokens
            temperature: Response temperature
            response_format: Response format (e.g., JSON)
            priority: Request priority for queue
            
        Returns:
            Response text or None
        """
        # Queue the request
        self._request_queue.enqueue(
            priority=priority,
            func=self._call_with_smart_fallback,
            args=(
                messages,
                max_tokens,
                temperature,
                response_format,
            ),
        )

        # Process request (async/sync depending on queue implementation)
        result = self._request_queue.get_result()
        return result

    def get_model_status(self) -> Dict:
        """Get status of all models"""
        return self._model_router.get_model_status()

    def get_recommended_model(self) -> str:
        """Get best model for current conditions"""
        return self._model_router.get_recommended_model()

    def get_best_models(self, count: int = 3) -> List[tuple]:
        """Get top N healthiest models"""
        return self._model_router.get_best_models(count)

    def get_metrics(self) -> Dict:
        """Get comprehensive metrics"""
        return {
            "model_status": self.get_model_status(),
            "best_models": self.get_best_models(5),
            "recommended_model": self.get_recommended_model(),
            "cache_stats": self._cache_manager.get_stats(),
            "rate_limiter_stats": self._rate_limiter.get_stats(),
        }


# Global instance
_client_v2: Optional[OpenRouterClientV2] = None


def get_openrouter_client(strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOADED) -> OpenRouterClientV2:
    """Get or create global OpenRouter client (singleton)"""
    global _client_v2
    if _client_v2 is None:
        _client_v2 = OpenRouterClientV2(strategy=strategy)
    return _client_v2


# ============================================================================
# Demo / Testing
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    client = get_openrouter_client(LoadBalancingStrategy.LEAST_LOADED)

    # Test request
    messages = [
        {"role": "user", "content": "Say 'Hello from JARVIS Multi-Model Load Balancer!'"}
    ]

    print("Calling OpenRouter with multi-model load balancing...")
    response = client.call(messages, priority=RequestPriority.HIGH)

    if response:
        print(f"\n✅ Response: {response}")
    else:
        print("\n❌ No response from any model")

    # Print metrics
    print("\n=== Model Status ===")
    for model_id, status in client.get_model_status().items():
        print(f"\n{model_id}:")
        print(f"  Health Score: {status['health_score']}/100")
        print(f"  Requests: {status['total_requests']} (Success: {status['successful_requests']})")
        print(f"  Error Rate: {status['error_rate']:.1f}%")
        print(f"  Avg Latency: {status['avg_latency']:.2f}s")
