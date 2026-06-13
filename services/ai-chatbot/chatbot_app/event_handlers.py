"""
Event Handlers cho ai-chatbot — consume domain events từ RabbitMQ.

Khi nhận được event từ product-service hoặc order-service,
cập nhật FAISS index và Neo4j knowledge graph tương ứng.

Các handler này được gọi bởi management command `consume_events`.
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

    # 1. Normalize data + generate embedding
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

    # 3. Update Neo4j KG
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

    # 4. Clear semantic cache so stale results aren't served
    try:
        cache.delete_pattern("rag_retrieve:*")
        cache.delete_pattern("chatbot_response:*")
        logger.debug("  Semantic cache cleared")
    except Exception as e:
        logger.warning(f"  Cache clear error: {e}")


def handle_product_deleted(event_data: dict):
    """Remove product từ vector store + KG khi product bị xóa."""
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
        cache.delete_pattern("rag_retrieve:*")
        cache.delete_pattern("chatbot_response:*")
    except Exception:
        pass


def handle_order_placed(event_data: dict):
    """Xử lý order.placed — update chat context (lightweight)."""
    order_id = event_data.get('order_id')
    user_id = event_data.get('user_id')
    logger.info(f"Order placed: {order_id} by user {user_id}")

    # Chatbot không cần xử lý nặng cho order events,
    # nhưng có thể dùng để warming cache cho user này
    try:
        cache_key = f"user_recent_order:{user_id}"
        cache.set(cache_key, {
            'order_id': order_id,
            'total': event_data.get('total', 0),
            'items_count': len(event_data.get('items', [])),
        }, timeout=3600)
    except Exception as e:
        logger.warning(f"Order cache error: {e}")
