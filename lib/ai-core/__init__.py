"""
AI Core Library — Shared AI Infrastructure
============================================
Unified components cho tất cả AI services.

Usage:
    from lib.ai_core import (
        embedder,
        vector_store,
        kg_client,
        tracker,
        semantic_cache,
        ProductACL,
    )

    # Embedding
    embeddings = embedder.embed_sync(["text"])

    # Vector search
    results = vector_store.search(query_emb, k=10)

    # Knowledge Graph
    recs = kg_client.get_user_recommendations(user_id)

    # Tracking
    tracker.track(user_id, 'view', product_id=123)

    # Cache
    cached = semantic_cache.get("query")
    semantic_cache.set("query", "response", "intent", [])
"""
from lib.ai_core.embedder import UnifiedEmbedder, embedder
from lib.ai_core.vector_store import UnifiedVectorStore, vector_store
from lib.ai_core.neo4j_client import UnifiedKGClient, kg_client
from lib.ai_core.tracking import UnifiedTracker, tracker
from lib.ai_core.cache import SemanticCache, semantic_cache
from lib.ai_core.acl import ProductACL, OrderACL, ReviewACL

__all__ = [
    "UnifiedEmbedder", "embedder",
    "UnifiedVectorStore", "vector_store",
    "UnifiedKGClient", "kg_client",
    "UnifiedTracker", "tracker",
    "SemanticCache", "semantic_cache",
    "ProductACL", "OrderACL", "ReviewACL",
]
