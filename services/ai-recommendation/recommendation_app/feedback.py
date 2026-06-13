"""
Feedback Collector — CTR & engagement tracking per recommendation source (Phase 3.3)

Tracks:
- Impressions (which products were shown, from which source)
- Clicks (user clicked/interacted)
- Add-to-cart rate per source
- Purchase rate per source

Used by HybridEngineV2 to adjust weights adaptively.
"""

import logging
from datetime import datetime, timedelta
from django.core.cache import cache
from django.db.models import Count, Q

logger = logging.getLogger(__name__)

# Recommendation source identifiers
SOURCES = ['collab', 'kg', 'content', 'popular', 'bandit']


class FeedbackCollector:
    """
    Collect and analyze feedback per recommendation source.

    Data stored in Redis with 7-day TTL for recent-window analysis,
    and in PostgreSQL (UserBehavior with source metadata) for long-term.
    """

    def __init__(self):
        self._cache_ttl = 604800  # 7 days

    # ──────────────────────────────────────────────
    # Record
    # ──────────────────────────────────────────────

    def record_impression(self, user_id, product_id, source: str, position: int = 0):
        """
        Record that a product was shown to a user from a specific source.

        Args:
            user_id: user who saw the recommendation
            product_id: recommended product
            source: source identifier ('collab', 'kg', 'content', 'popular', 'bandit')
            position: position in the recommendation list (0-based)
        """
        if not user_id or not source:
            return
        self._incr(f"fb:imp:{source}", 1)
        self._incr(f"fb:imp:total", 1)
        logger.debug(f"[Feedback] Impression: user={user_id}, source={source}, pos={position}")

    def record_click(self, user_id, product_id, source: str):
        """Record a user click on a recommended product."""
        if not user_id or not source:
            return
        self._incr(f"fb:click:{source}", 1)
        self._incr(f"fb:click:total", 1)
        logger.info(f"[Feedback] Click: user={user_id}, source={source}")

    def record_add_to_cart(self, user_id, product_id, source: str):
        """Record add-to-cart from a recommendation."""
        if not user_id or not source:
            return
        self._incr(f"fb:cart:{source}", 1)
        self._incr(f"fb:cart:total", 1)

    def record_purchase(self, user_id, product_id, source: str):
        """Record purchase from a recommendation."""
        if not user_id or not source:
            return
        self._incr(f"fb:purchase:{source}", 1)
        self._incr(f"fb:purchase:total", 1)

    # ──────────────────────────────────────────────
    # Stats
    # ──────────────────────────────────────────────

    def get_ctr(self, source: str) -> float:
        """Get click-through rate for a source (clicks / impressions)."""
        impressions = cache.get(f"fb:imp:{source}", 0)
        clicks = cache.get(f"fb:click:{source}", 0)
        if impressions == 0:
            return 0.0
        return clicks / impressions

    def get_cart_rate(self, source: str) -> float:
        """Get add-to-cart rate for a source."""
        impressions = cache.get(f"fb:imp:{source}", 0)
        carts = cache.get(f"fb:cart:{source}", 0)
        if impressions == 0:
            return 0.0
        return carts / impressions

    def get_purchase_rate(self, source: str) -> float:
        """Get purchase conversion rate for a source."""
        impressions = cache.get(f"fb:imp:{source}", 0)
        purchases = cache.get(f"fb:purchase:{source}", 0)
        if impressions == 0:
            return 0.0
        return purchases / impressions

    def get_source_scores(self) -> dict:
        """
        Get combined engagement scores for all sources.

        Returns:
            dict: {source: combined_score}, higher = better performance
        """
        scores = {}
        for source in SOURCES:
            ctr = self.get_ctr(source)
            cart_rate = self.get_cart_rate(source)
            purchase_rate = self.get_purchase_rate(source)
            # Weighted score: CTR (0.3) + cart (0.3) + purchase (0.4)
            scores[source] = ctr * 0.3 + cart_rate * 0.3 + purchase_rate * 0.4
        return scores

    def get_engagement_summary(self) -> dict:
        """Get a summary of all engagement metrics."""
        summary = {}
        for source in SOURCES:
            summary[source] = {
                'impressions': cache.get(f"fb:imp:{source}", 0),
                'clicks': cache.get(f"fb:click:{source}", 0),
                'add_to_carts': cache.get(f"fb:cart:{source}", 0),
                'purchases': cache.get(f"fb:purchase:{source}", 0),
                'ctr': round(self.get_ctr(source), 4),
                'cart_rate': round(self.get_cart_rate(source), 4),
                'purchase_rate': round(self.get_purchase_rate(source), 4),
            }
        summary['total'] = {
            'impressions': cache.get("fb:imp:total", 0),
            'clicks': cache.get("fb:click:total", 0),
            'add_to_carts': cache.get("fb:cart:total", 0),
            'purchases': cache.get("fb:purchase:total", 0),
        }
        return summary

    def reset_stats(self):
        """Reset all feedback stats (for testing)."""
        for key in ['imp', 'click', 'cart', 'purchase']:
            cache.delete(f"fb:{key}:total")
            for source in SOURCES:
                cache.delete(f"fb:{key}:{source}")

    # ──────────────────────────────────────────────
    # Adaptive weight computation
    # ──────────────────────────────────────────────

    def compute_optimal_weights(self, density: float = 0.5, query_specificity: float = 0.0) -> dict:
        """
        Compute optimal hybrid weights based on feedback data and context.

        Args:
            density: user history density (0=new user, 1=power user)
            query_specificity: how specific the query is (0=vague, 1=very specific)

        Returns:
            dict with weights for each source
        """
        base_weights = {'collab': 0.25, 'kg': 0.25, 'content': 0.25, 'popular': 0.25}

        # Adjust for user history density
        if density < 0.2:  # New user — favor content-based + popular
            base_weights['collab'] = 0.10
            base_weights['kg'] = 0.15
            base_weights['content'] = 0.35
            base_weights['popular'] = 0.40
        elif density > 0.8:  # Power user — favor collaborative + KG
            base_weights['collab'] = 0.35
            base_weights['kg'] = 0.35
            base_weights['content'] = 0.20
            base_weights['popular'] = 0.10

        # Adjust for query specificity
        if query_specificity > 0.7:  # Very specific query — favor content/KG
            base_weights['collab'] *= 0.5
            base_weights['kg'] *= 1.5
            base_weights['content'] *= 1.5
            base_weights['popular'] *= 0.5

        # Blend with feedback-driven CTR if enough data
        source_scores = self.get_source_scores()
        total_fb_impressions = cache.get("fb:imp:total", 0)
        if total_fb_impressions > 100:  # Only use feedback when enough data
            fb_weights = {}
            total_score = sum(source_scores.values()) or 1.0
            for source in SOURCES:
                fb_weights[source] = max(source_scores[source] / total_score, 0.05)

            # 50/50 blend: base heuristic + feedback-driven
            for source in SOURCES:
                base_weights[source] = base_weights.get(source, 0.25) * 0.5 + fb_weights.get(source, 0.25) * 0.5

        # Normalize to sum = 1
        total = sum(base_weights.values())
        if total > 0:
            base_weights = {k: v / total for k, v in base_weights.items()}

        return base_weights

    # ──────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────

    @staticmethod
    def _incr(key: str, delta: int = 1):
        """Increment a Redis counter."""
        try:
            cache.set(key, (cache.get(key, 0) or 0) + delta, timeout=604800)
        except Exception as e:
            logger.warning(f"Feedback counter error: {e}")


# Singleton instance
feedback_collector = FeedbackCollector()
