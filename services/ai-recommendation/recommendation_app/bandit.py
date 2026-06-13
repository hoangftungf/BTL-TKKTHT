"""
Multi-Armed Bandit for Recommendation Exploration (Phase 3.2)

Epsilon-Greedy strategy:
- epsilon % of requests → explore (random/popular items)
- (1 - epsilon) % of requests → exploit (best predicted items)

Usage:
    from recommendation_app.bandit import bandit

    if bandit.should_explore(user_id):
        items = get_popular_items()
    else:
        items = hybrid_engine.recommend(user_id)
"""

import logging
import random
from django.core.cache import cache

logger = logging.getLogger(__name__)


class EpsilonGreedyBandit:
    """
    Multi-Armed Bandit using Epsilon-Greedy strategy.

    - epsilon=0.10: 10% exploration, 90% exploitation
    - Adaptive epsilon for new users (more exploration)
    - Per-user exploration counts tracked in Redis
    """

    def __init__(self, epsilon: float = 0.10):
        self.epsilon = epsilon
        self._cache_ttl = 86400  # 24h

    def should_explore(self, user_id=None) -> bool:
        """
        Decide whether to explore or exploit.

        - Anonymous users (no user_id): always explore
        - New users (< 5 interactions): higher exploration (0.25)
        - Established users: default epsilon (0.10)
        """
        if user_id is None:
            return True

        # Check if user is "new" (few interactions)
        interaction_count = self._get_user_interaction_count(user_id)
        if interaction_count < 5:
            adjusted_epsilon = 0.25
        else:
            adjusted_epsilon = self.epsilon

        return random.random() < adjusted_epsilon

    def get_arm(self, arms: list, user_id=None) -> str:
        """
        Select an arm (recommendation source) using epsilon-greedy.

        Args:
            arms: list of arm names ['collab', 'kg', 'content', 'popular']
            user_id: optional user ID for personalization

        Returns:
            Selected arm name
        """
        if not arms:
            return 'popular'

        if self.should_explore(user_id):
            # Explore: pick a random arm
            arm = random.choice(arms)
            logger.info(f"[Bandit] EXPLORE: selected arm '{arm}' for user={user_id}")
            return arm

        # Exploit: pick the arm with highest historical CTR for this user
        arm = self._best_arm(arms, user_id)
        logger.info(f"[Bandit] EXPLOIT: selected arm '{arm}' for user={user_id}")
        return arm

    def record_feedback(self, user_id, arm: str, clicked: bool):
        """
        Record feedback for an arm to update CTR estimates.

        Args:
            user_id: user who received the recommendation
            arm: which source ('collab', 'kg', 'content', 'popular')
            clicked: whether the user clicked/interacted
        """
        if not user_id or not arm:
            return

        cache_key = f"bandit:ctr:{user_id}:{arm}"
        stats = cache.get(cache_key, {'impressions': 0, 'clicks': 0})
        stats['impressions'] += 1
        if clicked:
            stats['clicks'] += 1
        cache.set(cache_key, stats, timeout=self._cache_ttl)
        logger.info(f"[Bandit] Feedback: user={user_id}, arm={arm}, clicked={clicked}")

    def get_ctr(self, user_id, arm: str) -> float:
        """Get historical CTR for a user-arm pair."""
        cache_key = f"bandit:ctr:{user_id}:{arm}"
        stats = cache.get(cache_key, {'impressions': 0, 'clicks': 0})
        if stats['impressions'] == 0:
            return 0.0
        return stats['clicks'] / stats['impressions']

    def reset_user(self, user_id):
        """Reset bandit state for a user (for testing)."""
        from django.core.cache import cache
        for arm in ['collab', 'kg', 'content', 'popular']:
            cache.delete(f"bandit:ctr:{user_id}:{arm}")

    def _best_arm(self, arms: list, user_id) -> str:
        """Select the arm with the highest CTR for this user."""
        best_arm = arms[0]
        best_ctr = -1.0
        for arm in arms:
            ctr = self.get_ctr(user_id, arm)
            if ctr > best_ctr:
                best_ctr = ctr
                best_arm = arm
        return best_arm

    @staticmethod
    def _get_user_interaction_count(user_id) -> int:
        """Get the number of interactions for a user."""
        try:
            from recommendation_app.models import UserBehavior
            return UserBehavior.objects.filter(user_id=user_id).count()
        except Exception:
            return 0


# Singleton instance
bandit = EpsilonGreedyBandit()
