"""
Knowledge Graph với Neo4j — sử dụng UnifiedKGClient từ lib/ai-core.

Các method graph cơ bản (add_product, record_interaction, get_recommendations, etc.)
được delegate xuống lib.ai_core.neo4j_client.kg_client (singleton).

Chỉ giữ lại các method đặc thù cho recommendation:
- add_product_similarity
- sync_from_database
"""

import logging
from django.conf import settings
import httpx

logger = logging.getLogger(__name__)

# Unified KG client singleton from lib/ai-core
from lib.ai_core.neo4j_client import kg_client as _kg


class KnowledgeGraphEngine:
    """
    Knowledge Graph Engine — wraps UnifiedKGClient từ ai-core.

    Graph Schema:
    - Nodes: User, Product, Category, Brand, Color, Material, Variant
    - Relationships: VIEWED, PURCHASED, ADDED_TO_CART, WISHLISTED,
                     BELONGS_TO, MADE_BY, HAS_COLOR, HAS_MATERIAL,
                     HAS_VARIANT, SIMILAR
    """

    def __init__(self):
        # Delegate to unified client
        self._client = _kg

    # =====================================================================
    # Delegated methods (ủy quyền xuống UnifiedKGClient)
    # =====================================================================

    def add_user(self, user_id, name=None):
        """Ensure User node exists in graph."""
        session = self._client._get_session()
        if not session:
            return False
        try:
            with session:
                session.run(
                    "MERGE (u:User {id: $user_id}) SET u.name = COALESCE($name, u.name)",
                    user_id=str(user_id), name=name,
                )
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False

    def add_product(self, product_id, name, category=None, brand=None, price=None):
        """Add product node — delegates to UnifiedKGClient."""
        return self._client.add_product(
            product_id=str(product_id), name=name,
            category=category, brand=brand, price=price,
        )

    def record_interaction(self, user_id, product_id, interaction_type, metadata=None):
        """Record user-product interaction — delegates to UnifiedKGClient."""
        return self._client.record_interaction(
            user_id=str(user_id), product_id=str(product_id),
            interaction_type=interaction_type, metadata=metadata or {},
        )

    def get_similar_products(self, product_id, n=10):
        """Get similar products from graph — delegates to UnifiedKGClient."""
        results = self._client.get_similar_products(product_id=str(product_id), n=n)
        # Format to match expected output
        return [
            {
                'product_id': r['product_id'],
                'name': r.get('name', ''),
                'score': r.get('score', 0),
                'reason': 'Sản phẩm tương tự (Graph)',
            }
            for r in results
        ]

    def get_user_recommendations(self, user_id, n=10):
        """Get personalized recommendations — delegates to UnifiedKGClient."""
        results = self._client.get_user_recommendations(user_id=str(user_id), n=n)
        return [
            {
                'product_id': r['product_id'],
                'name': r.get('name', ''),
                'score': r.get('score', 0),
                'reason': r.get('reason', 'Gợi ý từ Knowledge Graph'),
            }
            for r in results
        ]

    def get_frequently_bought_together(self, product_id, n=5):
        """Get frequently bought together — delegates to UnifiedKGClient."""
        results = self._client.get_frequently_bought_together(
            product_id=str(product_id), n=n,
        )
        return [
            {
                'product_id': r['product_id'],
                'name': r.get('name', ''),
                'co_purchase_count': r.get('score', 0),
                'reason': 'Thường được mua cùng (Graph)',
            }
            for r in results
        ]

    def get_trending(self, n=10):
        """Get trending products — delegates to UnifiedKGClient."""
        results = self._client.get_trending(n=n)
        return [
            {
                'product_id': r['product_id'],
                'name': r.get('name', ''),
                'price': r.get('price', 0),
                'interactions': r.get('score', 0),
                'reason': 'Sản phẩm phổ biến',
            }
            for r in results
        ]

    def get_stats(self):
        """Get graph statistics — delegates to UnifiedKGClient."""
        return self._client.get_stats()

    def create_indexes(self):
        """Create Neo4j indexes — delegates to UnifiedKGClient."""
        return self._client.create_indexes()

    # =====================================================================
    # Recommendation-specific methods
    # =====================================================================

    def add_product_similarity(self, product_id, similar_product_id, score):
        """Add SIMILAR relationship between two products."""
        session = self._client._get_session()
        if not session:
            return False
        try:
            with session:
                session.run(
                    """
                    MATCH (p1:Product {id: $product_id}), (p2:Product {id: $similar_id})
                    MERGE (p1)-[r:SIMILAR]->(p2)
                    SET r.score = $score
                    """,
                    product_id=str(product_id),
                    similar_id=str(similar_product_id),
                    score=score,
                )
            return True
        except Exception as e:
            logger.error(f"Error adding similarity: {e}")
            return False

    def sync_from_database(self):
        """Sync data from PostgreSQL to Neo4j."""
        from .models import UserInteraction, ProductSimilarity

        logger.info("Starting graph sync from database...")

        session = self._client._get_session()
        if not session:
            return {'status': 'error', 'message': 'Neo4j not available'}

        try:
            # Sync products from product service
            product_service_url = getattr(
                settings, 'PRODUCT_SERVICE_URL', 'http://localhost:8003'
            )
            try:
                response = httpx.get(
                    f"{product_service_url}/?page_size=1000", timeout=30.0
                )
                if response.status_code == 200:
                    products = response.json().get('results', [])
                    for p in products:
                        self._client.add_product(
                            product_id=p['id'],
                            name=p.get('name', ''),
                            category=p.get('category', {}).get('name')
                            if isinstance(p.get('category'), dict) else p.get('category'),
                            brand=p.get('brand', ''),
                            price=p.get('price'),
                        )
                    logger.info(f"Synced {len(products)} products to graph")
            except Exception as e:
                logger.warning(f"Could not sync products: {e}")

            # Sync interactions
            interactions = UserInteraction.objects.all()
            interaction_count = 0
            for interaction in interactions:
                self._client.record_interaction(
                    user_id=str(interaction.user_id),
                    product_id=str(interaction.product_id),
                    interaction_type=interaction.interaction_type,
                )
                interaction_count += 1
            logger.info(f"Synced {interaction_count} interactions to graph")

            # Sync similarities
            similarities = ProductSimilarity.objects.all()
            sim_count = 0
            for sim in similarities:
                self.add_product_similarity(
                    product_id=str(sim.product_id),
                    similar_product_id=str(sim.similar_product_id),
                    score=sim.similarity_score,
                )
                sim_count += 1
            logger.info(f"Synced {sim_count} similarities to graph")

            return {
                'status': 'success',
                'interactions': interaction_count,
                'similarities': sim_count,
            }
        except Exception as e:
            logger.error(f"Error syncing graph: {e}")
            return {'status': 'error', 'message': str(e)}


# Singleton instance
knowledge_graph = KnowledgeGraphEngine()
