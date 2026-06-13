"""
Semantic Cache — Redis-based LRU cache với similarity matching.

Tìm cache hit bằng cosine similarity giữa query embeddings.
Configurable threshold, max entries LRU eviction.

Usage:
    from lib.ai_core.cache import semantic_cache

    # Check cache
    cached = semantic_cache.get("tôi cần mua laptop")
    if cached:
        response, intent, products = cached

    # Set cache
    semantic_cache.set("tôi cần mua laptop", response, intent, products)
"""
import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from django.core.cache import cache

logger = logging.getLogger(__name__)


class SemanticCache:
    """
    Redis-based semantic cache.

    - Stores (query, embedding, response, intent, products) tuples
    - LRU eviction when exceeds max_entries
    - Configurable similarity threshold (default 0.88)
    - TTL: 24 hours
    """

    def __init__(
        self,
        threshold: float = 0.88,
        max_entries: int = 500,
        cache_key: str = "semantic_cache_data",
    ):
        self.threshold = threshold
        self.max_entries = max_entries
        self.cache_key = cache_key
        self.ttl = 86400  # 24 hours

    def get(
        self, query: str
    ) -> Optional[Tuple[str, str, List[Dict]]]:
        """
        Look up cache by semantic similarity.

        Returns (response, intent, products) if hit, None if miss.
        """
        cache_data = cache.get(self.cache_key, [])
        if not cache_data:
            return None

        try:
            from lib.ai_core.embedder import embedder

            query_embs = embedder.embed_sync(query)
            if len(query_embs) == 0:
                return None
            q_emb = np.array(query_embs[0])
            q_norm = q_emb / (np.linalg.norm(q_emb) + 1e-10)

            best_sim = -1.0
            best_entry = None

            for entry in cache_data:
                cached_query, cached_emb_list = entry[0], entry[1]
                emb = np.array(cached_emb_list)
                emb_norm = emb / (np.linalg.norm(emb) + 1e-10)
                sim = float(np.dot(emb_norm, q_norm))

                if sim > best_sim:
                    best_sim = sim
                    best_entry = entry

            if best_sim >= self.threshold:
                logger.info(f"SemanticCache HIT (sim={best_sim:.3f})")
                # entry format: (query, emb, response, intent, products)
                response = best_entry[2]
                intent = best_entry[3] if len(best_entry) > 3 else "product_search"
                products = best_entry[4] if len(best_entry) > 4 else []
                return response, intent, products

            logger.debug(f"SemanticCache MISS (best_sim={best_sim:.3f})")
            return None

        except Exception as e:
            logger.error(f"SemanticCache get error: {e}")
            return None

    def set(
        self,
        query: str,
        response: str,
        intent: str = "product_search",
        products: Optional[List[Dict]] = None,
    ):
        """Store query + response in cache."""
        try:
            from lib.ai_core.embedder import embedder

            query_embs = embedder.embed_sync(query)
            if len(query_embs) == 0:
                return

            cache_data = cache.get(self.cache_key, [])

            # LRU eviction
            if len(cache_data) >= self.max_entries:
                cache_data = cache_data[-(self.max_entries - 1):]

            cache_data.append((
                query,
                list(query_embs[0]),
                response,
                intent,
                products or [],
            ))
            cache.set(self.cache_key, cache_data, timeout=self.ttl)
            logger.debug(f"SemanticCache SET ({len(cache_data)} entries)")

        except Exception as e:
            logger.error(f"SemanticCache set error: {e}")

    def clear(self):
        """Clear the entire cache."""
        cache.delete(self.cache_key)
        logger.info("SemanticCache cleared")

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cache_data = cache.get(self.cache_key, [])
        return {
            "entries": len(cache_data),
            "max_entries": self.max_entries,
            "threshold": self.threshold,
            "ttl_hours": self.ttl // 3600,
        }


# Singleton instance
semantic_cache = SemanticCache()
