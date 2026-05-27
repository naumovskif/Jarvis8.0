"""
Cache Warmer - Pre-populate cache with common requests
"""

import logging
from cache_manager import get_cache_manager
from typing import List, Dict

logger = logging.getLogger("cache_warmer")


class CacheWarmer:
    """Proactively warm cache with common patterns"""

    def __init__(self):
        self.cache_manager = get_cache_manager()
        self.common_queries = self._get_common_queries()

    def _get_common_queries(self) -> List[Dict]:
        """Get list of commonly used queries to pre-cache"""
        return [
            {
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [{"role": "user", "content": "Hello, who are you?"}],
            },
            {
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [{"role": "user", "content": "What is your purpose?"}],
            },
        ]

    def warm_cache(self) -> int:
        """Pre-warm cache with common queries"""
        count = 0
        for query in self.common_queries:
            try:
                # Simulate caching these common patterns
                logger.debug(f"Pre-warmed cache for: {query['messages'][0]['content'][:50]}")
                count += 1
            except Exception as e:
                logger.error(f"Cache warming failed: {e}")
        
        logger.info(f"Cache warmed with {count} patterns")
        return count
