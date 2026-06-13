"""
Unified Tracking Service — ghi nhận tương tác người dùng.

Consolidates dual-write (UserBehavior + UserInteraction) thành single write path:
1. Save to PostgreSQL (UserBehavior)
2. Update Neo4j graph (async)
3. Invalidate relevant caches

Usage:
    from lib.ai_core.tracking import tracker

    tracker.track(user_id, 'view', product_id=123)
    tracker.track(user_id, 'purchase', product_id=123, metadata={'amount': 100000})
"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class UnifiedTracker:
    """
    Single tracking interface cho mọi services.

    Thay thế dual-write pattern:
    - UserBehavior (8 actions) ← chỉ dùng bảng này
    - UserInteraction (5 types) ← xóa sau migration
    """

    ACTION_MAP = {
        "view": "view",
        "purchase": "purchase",
        "cart": "cart",
        "wishlist": "wishlist",
        "review": "review",
        "search": "search",
        "click": "click",
        "share": "share",
    }

    @staticmethod
    def track(
        user_id: str,
        action: str,
        product_id: Optional[str] = None,
        category_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Ghi nhận tương tác của user.

        1. Save to PostgreSQL (UserBehavior)
        2. Update Neo4j (async)
        3. Invalidate caches
        """
        action = UnifiedTracker.ACTION_MAP.get(action, action)
        metadata = metadata or {}

        # 1. Save to PostgreSQL
        try:
            from recommendation_app.models import UserBehavior

            UserBehavior.objects.create(
                user_id=user_id,
                product_id=product_id,
                category_id=category_id,
                action=action,
                metadata=metadata,
            )
        except Exception as e:
            logger.warning(f"PostgreSQL tracking failed: {e}")

        # 2. Update Neo4j (fire-and-forget)
        try:
            from lib.ai_core.neo4j_client import kg_client

            kg_client.record_interaction(
                user_id=user_id,
                product_id=product_id or "",
                action=action,
                metadata=metadata,
            )
        except Exception as e:
            logger.warning(f"Neo4j tracking failed: {e}")

        # 3. Invalidate caches
        try:
            from django.core.cache import cache

            cache.delete(f"user_recommendations:{user_id}:*")
            cache.delete(f"trending_products:*")
        except Exception:
            pass

        return True

    @staticmethod
    def track_purchase_bulk(
        user_id: str,
        items: list,
        order_id: str,
    ):
        """Track purchase for all items in an order."""
        for item in items:
            UnifiedTracker.track(
                user_id=user_id,
                action="purchase",
                product_id=item.get("product_id"),
                metadata={
                    "order_id": order_id,
                    "quantity": item.get("quantity", 1),
                    "price": item.get("price", 0),
                    "product_name": item.get("product_name", ""),
                },
            )


# Singleton instance
tracker = UnifiedTracker()
