"""
Knowledge Graph với Neo4j
Quản lý quan hệ giữa Users và Products
"""

import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Neo4j driver - lazy import
neo4j_driver = None


def get_neo4j_driver():
    """Get or create Neo4j driver"""
    global neo4j_driver

    if neo4j_driver is not None:
        return neo4j_driver

    try:
        from neo4j import GraphDatabase

        neo4j_uri = getattr(settings, 'NEO4J_URI', os.environ.get('NEO4J_URI', 'bolt://localhost:7687'))
        neo4j_user = getattr(settings, 'NEO4J_USER', os.environ.get('NEO4J_USER', 'neo4j'))
        neo4j_password = getattr(settings, 'NEO4J_PASSWORD', os.environ.get('NEO4J_PASSWORD', 'password'))

        neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        logger.info(f"Connected to Neo4j at {neo4j_uri}")
        return neo4j_driver
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        return None


class KnowledgeGraphEngine:
    """
    Knowledge Graph Engine với Neo4j

    Graph Schema:
    - Nodes:
        - (:User {id, name})
        - (:Product {id, name, category, brand, price})
        - (:Category {name})
        - (:Brand {name})

    - Relationships:
        - (User)-[:VIEWED {timestamp, count}]->(Product)
        - (User)-[:PURCHASED {timestamp, amount}]->(Product)
        - (User)-[:ADDED_TO_CART {timestamp}]->(Product)
        - (User)-[:WISHLISTED {timestamp}]->(Product)
        - (Product)-[:BELONGS_TO]->(Category)
        - (Product)-[:MADE_BY]->(Brand)
        - (Product)-[:SIMILAR {score}]->(Product)
    """

    def __init__(self):
        self.driver = None

    def _get_session(self):
        """Get Neo4j session"""
        if self.driver is None:
            self.driver = get_neo4j_driver()
        if self.driver is None:
            return None
        return self.driver.session()

    def create_indexes(self):
        """Tạo indexes cho graph"""
        session = self._get_session()
        if session is None:
            return {'status': 'error', 'message': 'Neo4j not available'}

        try:
            with session:
                # Create indexes
                session.run("CREATE INDEX user_id IF NOT EXISTS FOR (u:User) ON (u.id)")
                session.run("CREATE INDEX product_id IF NOT EXISTS FOR (p:Product) ON (p.id)")
                session.run("CREATE INDEX category_name IF NOT EXISTS FOR (c:Category) ON (c.name)")
                session.run("CREATE INDEX brand_name IF NOT EXISTS FOR (b:Brand) ON (b.name)")

            logger.info("Neo4j indexes created")
            return {'status': 'success'}
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            return {'status': 'error', 'message': str(e)}

    def add_user(self, user_id, name=None):
        """Thêm User node"""
        session = self._get_session()
        if session is None:
            return False

        try:
            with session:
                session.run(
                    """
                    MERGE (u:User {id: $user_id})
                    SET u.name = COALESCE($name, u.name)
                    """,
                    user_id=str(user_id),
                    name=name
                )
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False

    def add_product(self, product_id, name, category=None, brand=None, price=None):
        """Thêm Product node với relationships"""
        session = self._get_session()
        if session is None:
            return False

        try:
            with session:
                # Create product
                session.run(
                    """
                    MERGE (p:Product {id: $product_id})
                    SET p.name = $name, p.price = $price
                    """,
                    product_id=str(product_id),
                    name=name,
                    price=price
                )

                # Create category relationship
                if category:
                    session.run(
                        """
                        MERGE (c:Category {name: $category})
                        WITH c
                        MATCH (p:Product {id: $product_id})
                        MERGE (p)-[:BELONGS_TO]->(c)
                        """,
                        category=category,
                        product_id=str(product_id)
                    )

                # Create brand relationship
                if brand:
                    session.run(
                        """
                        MERGE (b:Brand {name: $brand})
                        WITH b
                        MATCH (p:Product {id: $product_id})
                        MERGE (p)-[:MADE_BY]->(b)
                        """,
                        brand=brand,
                        product_id=str(product_id)
                    )

            return True
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            return False

    def record_interaction(self, user_id, product_id, interaction_type, metadata=None):
        """
        Ghi nhận tương tác giữa User và Product

        Args:
            user_id: ID của user
            product_id: ID của product
            interaction_type: view, purchase, cart, wishlist
            metadata: dict với thông tin bổ sung (amount, timestamp, etc.)
        """
        session = self._get_session()
        if session is None:
            return False

        relationship_map = {
            'view': 'VIEWED',
            'purchase': 'PURCHASED',
            'cart': 'ADDED_TO_CART',
            'wishlist': 'WISHLISTED',
            'review': 'REVIEWED'
        }

        rel_type = relationship_map.get(interaction_type, 'INTERACTED')
        metadata = metadata or {}

        try:
            with session:
                # Ensure nodes exist
                session.run(
                    "MERGE (u:User {id: $user_id})",
                    user_id=str(user_id)
                )
                session.run(
                    "MERGE (p:Product {id: $product_id})",
                    product_id=str(product_id)
                )

                # Create/update relationship
                if rel_type == 'VIEWED':
                    session.run(
                        f"""
                        MATCH (u:User {{id: $user_id}}), (p:Product {{id: $product_id}})
                        MERGE (u)-[r:{rel_type}]->(p)
                        SET r.count = COALESCE(r.count, 0) + 1,
                            r.last_viewed = datetime()
                        """,
                        user_id=str(user_id),
                        product_id=str(product_id)
                    )
                elif rel_type == 'PURCHASED':
                    session.run(
                        f"""
                        MATCH (u:User {{id: $user_id}}), (p:Product {{id: $product_id}})
                        MERGE (u)-[r:{rel_type}]->(p)
                        SET r.count = COALESCE(r.count, 0) + 1,
                            r.total_amount = COALESCE(r.total_amount, 0) + $amount,
                            r.last_purchase = datetime()
                        """,
                        user_id=str(user_id),
                        product_id=str(product_id),
                        amount=metadata.get('amount', 0)
                    )
                else:
                    session.run(
                        f"""
                        MATCH (u:User {{id: $user_id}}), (p:Product {{id: $product_id}})
                        MERGE (u)-[r:{rel_type}]->(p)
                        SET r.timestamp = datetime()
                        """,
                        user_id=str(user_id),
                        product_id=str(product_id)
                    )

            return True
        except Exception as e:
            logger.error(f"Error recording interaction: {e}")
            return False

    def add_product_similarity(self, product_id, similar_product_id, score):
        """Thêm quan hệ SIMILAR giữa 2 products"""
        session = self._get_session()
        if session is None:
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
                    score=score
                )
            return True
        except Exception as e:
            logger.error(f"Error adding similarity: {e}")
            return False

    def get_similar_products(self, product_id, n=10):
        """
        Lấy sản phẩm tương tự từ graph

        Cypher: MATCH (p:Product {id:$id})-[:SIMILAR]->(rec) RETURN rec
        """
        session = self._get_session()
        if session is None:
            return []

        try:
            with session:
                result = session.run(
                    """
                    MATCH (p:Product {id: $product_id})-[r:SIMILAR]->(rec:Product)
                    RETURN rec.id AS product_id, rec.name AS name, r.score AS score
                    ORDER BY r.score DESC
                    LIMIT $limit
                    """,
                    product_id=str(product_id),
                    limit=n
                )
                return [
                    {
                        'product_id': record['product_id'],
                        'name': record['name'],
                        'score': record['score'],
                        'reason': 'Sản phẩm tương tự (Graph)'
                    }
                    for record in result
                ]
        except Exception as e:
            logger.error(f"Error getting similar products: {e}")
            return []

    def get_user_recommendations(self, user_id, n=10):
        """
        Gợi ý sản phẩm cho user dựa trên graph

        Query 1: Sản phẩm mà users tương tự đã mua
        Query 2: Sản phẩm cùng category với sản phẩm user đã mua
        """
        session = self._get_session()
        if session is None:
            return []

        try:
            with session:
                # Collaborative: Users who bought this also bought
                collab_result = session.run(
                    """
                    MATCH (u:User {id: $user_id})-[:PURCHASED]->(p:Product)<-[:PURCHASED]-(other:User)
                    MATCH (other)-[:PURCHASED]->(rec:Product)
                    WHERE NOT (u)-[:PURCHASED]->(rec)
                    WITH rec, COUNT(DISTINCT other) AS purchasers
                    RETURN rec.id AS product_id, rec.name AS name, purchasers AS score
                    ORDER BY purchasers DESC
                    LIMIT $limit
                    """,
                    user_id=str(user_id),
                    limit=n // 2
                )
                collab_recs = [
                    {
                        'product_id': r['product_id'],
                        'name': r['name'],
                        'score': float(r['score']),
                        'reason': 'Người mua tương tự cũng thích'
                    }
                    for r in collab_result
                ]

                # Content-based: Same category products
                content_result = session.run(
                    """
                    MATCH (u:User {id: $user_id})-[:PURCHASED|VIEWED]->(p:Product)-[:BELONGS_TO]->(c:Category)
                    MATCH (rec:Product)-[:BELONGS_TO]->(c)
                    WHERE NOT (u)-[:PURCHASED]->(rec) AND rec <> p
                    WITH rec, COUNT(DISTINCT c) AS category_matches
                    RETURN rec.id AS product_id, rec.name AS name, category_matches AS score
                    ORDER BY category_matches DESC
                    LIMIT $limit
                    """,
                    user_id=str(user_id),
                    limit=n // 2
                )
                content_recs = [
                    {
                        'product_id': r['product_id'],
                        'name': r['name'],
                        'score': float(r['score']),
                        'reason': 'Cùng danh mục quan tâm'
                    }
                    for r in content_result
                ]

                # Combine and deduplicate
                seen = set()
                results = []
                for rec in collab_recs + content_recs:
                    if rec['product_id'] not in seen:
                        seen.add(rec['product_id'])
                        results.append(rec)

                return results[:n]

        except Exception as e:
            logger.error(f"Error getting graph recommendations: {e}")
            return []

    def get_frequently_bought_together(self, product_id, n=5):
        """
        Sản phẩm thường được mua cùng

        Cypher: Users who bought this product, what else did they buy?
        """
        session = self._get_session()
        if session is None:
            return []

        try:
            with session:
                result = session.run(
                    """
                    MATCH (p:Product {id: $product_id})<-[:PURCHASED]-(u:User)-[:PURCHASED]->(other:Product)
                    WHERE other.id <> $product_id
                    WITH other, COUNT(DISTINCT u) AS co_purchases
                    RETURN other.id AS product_id, other.name AS name, co_purchases
                    ORDER BY co_purchases DESC
                    LIMIT $limit
                    """,
                    product_id=str(product_id),
                    limit=n
                )
                return [
                    {
                        'product_id': r['product_id'],
                        'name': r['name'],
                        'co_purchase_count': r['co_purchases'],
                        'reason': 'Thường được mua cùng (Graph)'
                    }
                    for r in result
                ]
        except Exception as e:
            logger.error(f"Error getting bought together: {e}")
            return []

    def sync_from_database(self):
        """
        Đồng bộ data từ PostgreSQL sang Neo4j
        """
        from .models import UserInteraction, ProductSimilarity
        import httpx

        logger.info("Starting graph sync from database...")

        session = self._get_session()
        if session is None:
            return {'status': 'error', 'message': 'Neo4j not available'}

        try:
            # Sync products from product service
            product_service_url = getattr(settings, 'PRODUCT_SERVICE_URL', 'http://localhost:8003')
            try:
                response = httpx.get(f"{product_service_url}/api/products/?page_size=1000", timeout=30.0)
                if response.status_code == 200:
                    products = response.json().get('results', [])
                    for p in products:
                        self.add_product(
                            product_id=p['id'],
                            name=p.get('name', ''),
                            category=p.get('category', {}).get('name') if p.get('category') else None,
                            brand=p.get('brand', ''),
                            price=p.get('price')
                        )
                    logger.info(f"Synced {len(products)} products to graph")
            except Exception as e:
                logger.warning(f"Could not sync products: {e}")

            # Sync interactions
            interactions = UserInteraction.objects.all()
            interaction_count = 0
            for interaction in interactions:
                self.record_interaction(
                    user_id=interaction.user_id,
                    product_id=interaction.product_id,
                    interaction_type=interaction.interaction_type
                )
                interaction_count += 1

            logger.info(f"Synced {interaction_count} interactions to graph")

            # Sync similarities
            similarities = ProductSimilarity.objects.all()
            sim_count = 0
            for sim in similarities:
                self.add_product_similarity(
                    product_id=sim.product_id,
                    similar_product_id=sim.similar_product_id,
                    score=sim.similarity_score
                )
                sim_count += 1

            logger.info(f"Synced {sim_count} similarities to graph")

            return {
                'status': 'success',
                'interactions': interaction_count,
                'similarities': sim_count
            }

        except Exception as e:
            logger.error(f"Error syncing graph: {e}")
            return {'status': 'error', 'message': str(e)}

    def get_stats(self):
        """Lấy thống kê graph"""
        session = self._get_session()
        if session is None:
            return {'status': 'error', 'message': 'Neo4j not available'}

        try:
            with session:
                result = session.run(
                    """
                    MATCH (u:User) WITH COUNT(u) AS users
                    MATCH (p:Product) WITH users, COUNT(p) AS products
                    MATCH ()-[r]->() WITH users, products, COUNT(r) AS relationships
                    RETURN users, products, relationships
                    """
                )
                record = result.single()
                return {
                    'users': record['users'],
                    'products': record['products'],
                    'relationships': record['relationships']
                }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'status': 'error', 'message': str(e)}


# Singleton instance
knowledge_graph = KnowledgeGraphEngine()
