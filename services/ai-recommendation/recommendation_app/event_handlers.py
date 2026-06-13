"""
Event Handlers cho ai-recommendation — consume domain events từ RabbitMQ.

Khi nhận được product.updated → update FAISS + Neo4j
Khi nhận được order.placed → track purchase behavior
Khi nhận được review.created → update product rating
"""
import json
import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def handle_product_updated(event_data: dict):
    """Update vector store + KG khi product thay đổi."""
    from lib.ai_core.vector_store import vector_store
    from lib.ai_core.neo4j_client import kg_client
    from lib.ai_core.embedder import embedder
    from lib.ai_core.acl import ProductACL

    pid = event_data.get('id')
    if not pid:
        logger.warning("handle_product_updated: no id in event_data")
        return

    pid_str = str(pid)
    logger.info(f"Handling product.updated: {pid_str} - {event_data.get('name', '')}")

    # 1. Normalize + embed
    normalized = ProductACL.from_api_response(event_data)
    text = ProductACL.to_embedding_text(normalized)
    embeddings = embedder.embed_sync([text])

    if not embeddings or len(embeddings) == 0:
        logger.warning(f"No embedding generated for product {pid_str}")
        return

    # 2. Update FAISS vector store
    index_dir = getattr(settings, 'AI_INDEX_DIR', '/app/ai_index')
    vector_store.load(index_dir)

    if pid_str in vector_store.product_ids:
        vector_store.remove(pid_str)
        logger.info(f"  Removed old embedding for {pid_str}")

    vector_store.add(pid_str, embeddings[0], normalized)
    vector_store.save(index_dir)
    logger.info(f"  FAISS vector store updated for {pid_str}")

    # 3. Update Neo4j KG (via knowledge_graph singleton để dùng đúng format)
    from recommendation_app.knowledge_graph import knowledge_graph
    knowledge_graph.add_product(
        product_id=pid_str,
        name=event_data.get('name', ''),
        category=event_data.get('category'),
        brand=event_data.get('brand'),
        price=event_data.get('price', 0),
    )

    # Also update KG client directly for full fields
    kg_client.add_product(
        product_id=pid_str,
        name=event_data.get('name', ''),
        category=event_data.get('category'),
        brand=event_data.get('brand'),
        price=event_data.get('price', 0),
        status=event_data.get('status', 'active'),
        stock=event_data.get('stock_quantity', 0),
    )
    logger.info(f"  Neo4j KG updated for {pid_str}")

    # 4. Clear cache
    try:
        cache.delete_pattern("rec_*")
        cache.delete_pattern("similar_*")
        cache.delete_pattern("trending_*")
    except Exception:
        pass


def handle_product_deleted(event_data: dict):
    """Remove product từ vector store + KG."""
    from lib.ai_core.vector_store import vector_store
    from lib.ai_core.neo4j_client import kg_client

    product_id = event_data.get('product_id')
    if not product_id:
        logger.warning("handle_product_deleted: no product_id in event_data")
        return

    pid_str = str(product_id)
    logger.info(f"Handling product.deleted: {pid_str}")

    # 1. Remove from FAISS
    index_dir = getattr(settings, 'AI_INDEX_DIR', '/app/ai_index')
    vector_store.load(index_dir)
    vector_store.remove(pid_str)
    vector_store.save(index_dir)
    logger.info(f"  Removed from FAISS: {pid_str}")

    # 2. Remove from Neo4j
    kg_client.remove_product(pid_str)
    logger.info(f"  Removed from KG: {pid_str}")

    # 3. Clear cache
    try:
        cache.delete_pattern("rec_*")
        cache.delete_pattern("similar_*")
    except Exception:
        pass


def handle_order_placed(event_data: dict):
    """Track purchase behavior khi có đơn hàng mới."""
    try:
        from recommendation_app.models import UserBehavior
        items = event_data.get('items', [])
        user_id = event_data.get('user_id')
        if not user_id or not items:
            logger.warning("handle_order_placed: missing user_id or items")
            return

        for item in items:
            UserBehavior.objects.create(
                user_id=user_id,
                product_id=item['product_id'],
                action='purchase',
                metadata={
                    'order_id': event_data.get('order_id'),
                    'quantity': item.get('quantity'),
                    'price': item.get('price'),
                }
            )

        # Also record in Neo4j
        from lib.ai_core.neo4j_client import kg_client
        for item in items:
            kg_client.record_interaction(
                user_id=str(user_id),
                product_id=str(item['product_id']),
                action='purchase',
                metadata={'amount': item.get('price', 0)},
            )

        logger.info(f"Tracked {len(items)} purchases for user {user_id}")

        # Clear rec cache for this user
        try:
            cache.delete(f"rec_user:{user_id}")
        except Exception:
            pass

    except Exception as e:
        logger.error(f"handle_order_placed failed: {e}")


def handle_review_created(event_data: dict):
    """Update product rating stats khi có review mới."""
    from lib.ai_core.neo4j_client import kg_client

    product_id = event_data.get('product_id')
    rating = event_data.get('rating')
    if not product_id or rating is None:
        logger.warning("handle_review_created: missing product_id or rating")
        return

    pid_str = str(product_id)
    logger.info(f"Review created for product {pid_str}, rating={rating}")

    # 1. Record review interaction in KG
    kg_client.record_interaction(
        user_id=str(event_data.get('user_id', 'anonymous')),
        product_id=pid_str,
        action='review',
    )

    # 2. Update average rating on Product node in Neo4j
    session = kg_client._get_session()
    if session:
        try:
            with session:
                # Aggregate updated rating from all REVIEWED relationships
                result = session.run(
                    """
                    MATCH (p:Product {id: $pid})<-[r:REVIEWED]-(:User)
                    WITH p, COUNT(r) AS review_count, AVG(r.rating) AS avg_rating
                    SET p.review_count = review_count,
                        p.avg_rating = avg_rating
                    RETURN review_count, avg_rating
                    """,
                    pid=pid_str,
                )
                row = result.single()
                if row:
                    logger.info(
                        f"  Updated product {pid_str}: "
                        f"avg_rating={row['avg_rating']:.2f}, "
                        f"reviews={row['review_count']}"
                    )
        except Exception as e:
            logger.error(f"  Failed to update rating in KG: {e}")

    # 3. Clear cache
    try:
        cache.delete_pattern("rec_*")
        cache.delete(f"product_rating:{pid_str}")
    except Exception:
        pass
