"""
Centralized User Behavior Tracking Service

This service provides a single, reusable function to track all 8 core user actions:
1. view_product
2. click_product
3. add_to_cart
4. remove_from_cart
5. purchase
6. add_to_wishlist
7. search
8. view_category

Usage:
    from recommendation_app.services.tracking_service import TrackingService

    # Track product view
    TrackingService.track(user_id, 'view_product', product_id=product_id)

    # Track search
    TrackingService.track(user_id, 'search', metadata={'query': 'iphone'})

    # Track category view
    TrackingService.track(user_id, 'view_category', category_id=category_id)
"""

import logging
from typing import Optional, Any
from uuid import UUID

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


# Valid actions for tracking
VALID_ACTIONS = [
    'view_product',
    'click_product',
    'add_to_cart',
    'remove_from_cart',
    'purchase',
    'add_to_wishlist',
    'search',
    'view_category',
]

# Action score weights for recommendation engine
ACTION_SCORES = {
    'view_product': 1.0,
    'click_product': 1.5,
    'add_to_cart': 3.0,
    'remove_from_cart': -1.0,
    'purchase': 5.0,
    'add_to_wishlist': 2.5,
    'search': 0.5,
    'view_category': 0.5,
}


class TrackingService:
    """
    Centralized service for tracking user behaviors.
    Thread-safe and handles null values gracefully.
    """

    @staticmethod
    def track(
        user_id: Optional[Any],
        action: str,
        product_id: Optional[Any] = None,
        category_id: Optional[Any] = None,
        metadata: Optional[dict] = None,
        search_query: Optional[str] = None,
    ) -> bool:
        """
        Track a user behavior action.

        Args:
            user_id: UUID of the user (can be None for anonymous)
            action: One of the 8 valid actions
            product_id: UUID of the product (optional)
            category_id: UUID of the category (optional)
            metadata: Additional JSON metadata (optional)
            search_query: Search query string for 'search' action (optional)

        Returns:
            True if tracking was successful, False otherwise
        """
        # Skip if no user ID (anonymous users)
        if not user_id:
            logger.debug(f"Skipping tracking for anonymous user: {action}")
            return False

        # Validate action
        if action not in VALID_ACTIONS:
            logger.warning(f"Invalid action '{action}'. Valid actions: {VALID_ACTIONS}")
            return False

        try:
            # Import here to avoid circular imports
            from recommendation_app.models import UserBehavior, UserInteraction

            # Normalize UUIDs
            user_uuid = TrackingService._to_uuid(user_id)
            product_uuid = TrackingService._to_uuid(product_id)
            category_uuid = TrackingService._to_uuid(category_id)

            if not user_uuid:
                return False

            # Build metadata
            final_metadata = metadata.copy() if metadata else {}
            if search_query and action == 'search':
                final_metadata['query'] = search_query

            with transaction.atomic():
                # Create UserBehavior record
                behavior = UserBehavior.objects.create(
                    user_id=user_uuid,
                    product_id=product_uuid,
                    category_id=category_uuid,
                    action=action,
                    search_query=search_query if action == 'search' else None,
                    metadata=final_metadata,
                )

                # Also create UserInteraction for product-related actions
                # This maintains compatibility with the recommendation engine
                if product_uuid and action in ['view_product', 'add_to_cart', 'purchase', 'add_to_wishlist']:
                    interaction_type_map = {
                        'view_product': 'view',
                        'add_to_cart': 'cart',
                        'purchase': 'purchase',
                        'add_to_wishlist': 'wishlist',
                    }
                    interaction_type = interaction_type_map.get(action)
                    if interaction_type:
                        UserInteraction.objects.create(
                            user_id=user_uuid,
                            product_id=product_uuid,
                            interaction_type=interaction_type,
                            score=ACTION_SCORES.get(action, 1.0),
                        )

            logger.info(
                f"Tracked: user={user_uuid}, action={action}, "
                f"product={product_uuid}, category={category_uuid}"
            )
            return True

        except Exception as e:
            logger.error(f"Error tracking behavior: {e}", exc_info=True)
            return False

    @staticmethod
    def track_bulk(
        user_id: Any,
        actions: list,
    ) -> int:
        """
        Track multiple actions at once (e.g., for purchase with multiple items).

        Args:
            user_id: UUID of the user
            actions: List of dicts with keys: action, product_id, category_id, metadata

        Returns:
            Number of successfully tracked actions
        """
        success_count = 0
        for action_data in actions:
            if TrackingService.track(
                user_id=user_id,
                action=action_data.get('action'),
                product_id=action_data.get('product_id'),
                category_id=action_data.get('category_id'),
                metadata=action_data.get('metadata'),
                search_query=action_data.get('search_query'),
            ):
                success_count += 1
        return success_count

    @staticmethod
    def _to_uuid(value: Any) -> Optional[UUID]:
        """Safely convert a value to UUID."""
        if value is None:
            return None
        if isinstance(value, UUID):
            return value
        try:
            return UUID(str(value))
        except (ValueError, AttributeError):
            logger.warning(f"Could not convert to UUID: {value}")
            return None

    @staticmethod
    def get_action_score(action: str) -> float:
        """Get the weight/score for an action type."""
        return ACTION_SCORES.get(action, 1.0)


# Convenience function for direct import
def track(
    user_id: Any,
    action: str,
    product_id: Any = None,
    category_id: Any = None,
    metadata: dict = None,
    search_query: str = None,
) -> bool:
    """
    Convenience function to track user behavior.

    Example:
        from recommendation_app.services.tracking_service import track
        track(request.user.id, 'view_product', product_id=product.id)
    """
    return TrackingService.track(
        user_id=user_id,
        action=action,
        product_id=product_id,
        category_id=category_id,
        metadata=metadata,
        search_query=search_query,
    )
