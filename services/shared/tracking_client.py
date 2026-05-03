"""
Shared Tracking Client for Microservices

This client sends tracking requests to the ai-recommendation service.
Use this in any microservice to track user behaviors.

Usage:
    from shared.tracking_client import track_behavior

    track_behavior(
        user_id=request.user.id,
        action='view_product',
        product_id=product_id
    )
"""

import logging
import httpx
import os
from typing import Optional, Any
from threading import Thread

logger = logging.getLogger(__name__)

# Configuration
RECOMMENDATION_SERVICE_URL = os.environ.get(
    'RECOMMENDATION_SERVICE_URL',
    'http://ai-recommendation:8008'
)
TRACKING_TIMEOUT = 5.0  # seconds


def track_behavior(
    user_id: Any,
    action: str,
    product_id: Optional[Any] = None,
    category_id: Optional[Any] = None,
    metadata: Optional[dict] = None,
    search_query: Optional[str] = None,
    async_mode: bool = True,
) -> bool:
    """
    Track user behavior by sending to recommendation service.

    Args:
        user_id: UUID of the user
        action: One of 8 valid actions:
            - view_product
            - click_product
            - add_to_cart
            - remove_from_cart
            - purchase
            - add_to_wishlist
            - search
            - view_category
        product_id: UUID of the product (optional)
        category_id: UUID of the category (optional)
        metadata: Additional JSON data (optional)
        search_query: Query string for search action (optional)
        async_mode: If True, send request in background thread (default: True)

    Returns:
        True if request was sent (not necessarily successful in async mode)
    """
    if not user_id:
        logger.debug("Skipping tracking for anonymous user")
        return False

    payload = {
        'user_id': str(user_id),
        'action': action,
        'product_id': str(product_id) if product_id else None,
        'category_id': str(category_id) if category_id else None,
        'metadata': metadata or {},
        'search_query': search_query,
    }

    if async_mode:
        # Send in background thread to not block request
        thread = Thread(target=_send_tracking_request, args=(payload,))
        thread.daemon = True
        thread.start()
        return True
    else:
        return _send_tracking_request(payload)


def _send_tracking_request(payload: dict) -> bool:
    """Send tracking request to recommendation service."""
    try:
        url = f"{RECOMMENDATION_SERVICE_URL}/track/"
        response = httpx.post(url, json=payload, timeout=TRACKING_TIMEOUT)

        if response.status_code == 200:
            logger.debug(f"Tracked: {payload['action']} for user {payload['user_id']}")
            return True
        else:
            logger.warning(
                f"Tracking failed: {response.status_code} - {response.text}"
            )
            return False

    except httpx.TimeoutException:
        logger.warning(f"Tracking timeout for action: {payload['action']}")
        return False
    except Exception as e:
        logger.error(f"Tracking error: {e}")
        return False


def track_bulk(user_id: Any, actions: list, async_mode: bool = True) -> bool:
    """
    Track multiple actions at once.

    Args:
        user_id: UUID of the user
        actions: List of dicts with keys: action, product_id, category_id, metadata
        async_mode: If True, send in background

    Returns:
        True if request was sent
    """
    for action_data in actions:
        track_behavior(
            user_id=user_id,
            action=action_data.get('action'),
            product_id=action_data.get('product_id'),
            category_id=action_data.get('category_id'),
            metadata=action_data.get('metadata'),
            search_query=action_data.get('search_query'),
            async_mode=async_mode,
        )
    return True
