"""
Unified Neo4j Knowledge Graph Client — singleton, dùng chung cho mọi AI services.

Consolidates:
- chatbot_app/engine.py → KnowledgeGraphClient
- recommendation_app/knowledge_graph.py → KnowledgeGraphEngine
- recommendation/services/neo4j_client.py → get_driver(), run_query()

Usage:
    from lib.ai_core.neo4j_client import kg_client

    # Search
    products = await kg_client.search_products(...)
    recs = await kg_client.get_user_recommendations(user_id)
"""
import logging
import os
from typing import Any, Dict, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


# Minimal entity-like container for ask_for_clarification
class _QueryEntities:
    """Minimal entity container used by ask_for_clarification."""
    def __init__(self, entities):
        self.category = getattr(entities, 'category', None)
        self.brand = getattr(entities, 'brand', None)
        self.price_min = getattr(entities, 'price_min', None)
        self.price_max = getattr(entities, 'price_max', None)
        self.confidence = getattr(entities, 'confidence', 0.0)


class UnifiedKGClient:
    """
    Singleton Neo4j client cho tất cả AI services.

    Cung cấp đầy đủ operations:
    - Product search (text, category, brand, price)
    - User recommendations (collaborative + content-based)
    - Similar products
    - Frequently bought together
    - Trending products
    - Interaction tracking
    - Stats
    """

    _instance = None
    _driver = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._driver is not None:
            return
        self._connect()

    def _connect(self):
        """Lazy-connect to Neo4j (singleton driver)."""
        if self._driver is not None:
            return
        try:
            from neo4j import GraphDatabase

            uri = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
            user = os.environ.get("NEO4J_USER", "neo4j")
            password = os.environ.get("NEO4J_PASSWORD", "password123")

            self._driver = GraphDatabase.driver(uri, auth=(user, password))
            logger.info(f"KG Client connected to Neo4j at {uri}")
        except Exception as e:
            logger.error(f"KG Client cannot connect to Neo4j: {e}")
            self._driver = None

    def _get_session(self):
        if self._driver is None:
            self._connect()
        if self._driver:
            return self._driver.session()
        return None

    # ------------------------------------------------------------------
    # Product Operations
    # ------------------------------------------------------------------

    def add_product(
        self,
        product_id: str,
        name: str,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        price: Optional[float] = None,
        status: str = "active",
        stock: int = 0,
    ):
        """Add or update a product node in the graph."""
        session = self._get_session()
        if not session:
            return False
        try:
            with session:
                session.run(
                    """
                    MERGE (p:Product {id: $id})
                    SET p.name = $name,
                        p.price = $price,
                        p.status = $status,
                        p.stock = $stock
                    """,
                    id=str(product_id), name=name, price=price or 0,
                    status=status, stock=stock,
                )
                if category:
                    session.run(
                        """
                        MERGE (c:Category {name: $category})
                        WITH c
                        MATCH (p:Product {id: $id})
                        MERGE (p)-[:BELONGS_TO]->(c)
                        """,
                        category=category, id=str(product_id),
                    )
                if brand:
                    session.run(
                        """
                        MERGE (b:Brand {name: $brand})
                        WITH b
                        MATCH (p:Product {id: $id})
                        MERGE (p)-[:MADE_BY]->(b)
                        """,
                        brand=brand, id=str(product_id),
                    )
            return True
        except Exception as e:
            logger.error(f"add_product error: {e}")
            return False

    def remove_product(self, product_id: str) -> bool:
        """Remove a product node and its relationships."""
        session = self._get_session()
        if not session:
            return False
        try:
            with session:
                session.run(
                    "MATCH (p:Product {id: $id}) DETACH DELETE p",
                    id=str(product_id),
                )
            return True
        except Exception as e:
            logger.error(f"remove_product error: {e}")
            return False

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_products(
        self,
        query: str = "",
        category: Optional[str] = None,
        brand: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        n: int = 10,
    ) -> List[Dict]:
        """Search products in Neo4j with filters."""
        session = self._get_session()
        if not session:
            return []

        where_clauses = ["p.status = 'active'"]
        params = {}

        if query:
            where_clauses.append(
                "(toLower(p.name) CONTAINS toLower($query) OR toLower(p.description) CONTAINS toLower($query))"
            )
            params["query"] = query

        if category:
            where_clauses.append("toLower(c.name) CONTAINS toLower($category)")
            params["category"] = category

        if brand:
            where_clauses.append("toLower(b.name) CONTAINS toLower($brand)")
            params["brand"] = brand

        if price_min is not None:
            where_clauses.append("toFloat(p.price) >= $price_min")
            params["price_min"] = price_min

        if price_max is not None:
            where_clauses.append("toFloat(p.price) <= $price_max")
            params["price_max"] = price_max

        where_str = " AND ".join(where_clauses)

        try:
            with session:
                result = session.run(
                    f"""
                    MATCH (p:Product)
                    OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)
                    OPTIONAL MATCH (p)-[:MADE_BY]->(b:Brand)
                    WHERE {where_str}
                    RETURN p.id AS product_id, p.name AS name,
                           toFloat(p.price) AS price,
                           c.name AS category, b.name AS brand
                    LIMIT $limit
                    """,
                    **params, limit=n,
                )
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"search_products error: {e}")
            return []

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    def get_similar_products(
        self, product_id: str, n: int = 10
    ) -> List[Dict]:
        """Get similar products via [:SIMILAR] relationships."""
        session = self._get_session()
        if not session:
            return []
        try:
            with session:
                result = session.run(
                    """
                    MATCH (p:Product {id: $id})-[r:SIMILAR]->(rec:Product)
                    RETURN rec.id AS product_id, rec.name AS name,
                           r.score AS score
                    ORDER BY r.score DESC
                    LIMIT $limit
                    """,
                    id=str(product_id), limit=n,
                )
                return [
                    {
                        "product_id": r["product_id"],
                        "name": r["name"],
                        "score": r["score"],
                        "reason": "Sản phẩm tương tự (Graph)",
                    }
                    for r in result
                ]
        except Exception as e:
            logger.error(f"get_similar_products error: {e}")
            return []

    def get_user_recommendations(
        self, user_id: str, n: int = 10
    ) -> List[Dict]:
        """Hybrid recommendations: collaborative + content-based."""
        session = self._get_session()
        if not session:
            return []

        try:
            with session:
                # Collaborative: users who bought this also bought
                collab = session.run(
                    """
                    MATCH (u:User {id: $uid})-[:PURCHASED]->(p:Product)
                    <-[:PURCHASED]-(other:User)
                    MATCH (other)-[:PURCHASED]->(rec:Product)
                    WHERE NOT (u)-[:PURCHASED]->(rec)
                    WITH rec, COUNT(DISTINCT other) AS score
                    RETURN rec.id AS product_id, rec.name AS name, score
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    uid=str(user_id), limit=n // 2,
                )
                collab_recs = [
                    {
                        "product_id": r["product_id"],
                        "name": r["name"],
                        "score": float(r["score"]),
                        "reason": "Người mua tương tự cũng thích",
                    }
                    for r in collab
                ]

                # Content-based: same category
                content = session.run(
                    """
                    MATCH (u:User {id: $uid})-[:PURCHASED|VIEWED]->(p:Product)
                    -[:BELONGS_TO]->(c:Category)
                    MATCH (rec:Product)-[:BELONGS_TO]->(c)
                    WHERE NOT (u)-[:PURCHASED]->(rec) AND rec <> p
                    WITH rec, COUNT(DISTINCT c) AS score
                    RETURN rec.id AS product_id, rec.name AS name, score
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    uid=str(user_id), limit=n // 2,
                )
                content_recs = [
                    {
                        "product_id": r["product_id"],
                        "name": r["name"],
                        "score": float(r["score"]),
                        "reason": "Cùng danh mục quan tâm",
                    }
                    for r in content
                ]

                # Deduplicate
                seen = set()
                results = []
                for rec in collab_recs + content_recs:
                    if rec["product_id"] not in seen:
                        seen.add(rec["product_id"])
                        results.append(rec)
                return results[:n]

        except Exception as e:
            logger.error(f"get_user_recommendations error: {e}")
            return []

    def get_frequently_bought_together(
        self, product_id: str, n: int = 5
    ) -> List[Dict]:
        """Products frequently bought together with this product."""
        session = self._get_session()
        if not session:
            return []
        try:
            with session:
                result = session.run(
                    """
                    MATCH (p:Product {id: $id})<-[:PURCHASED]-(u:User)
                    -[:PURCHASED]->(other:Product)
                    WHERE other.id <> $id
                    WITH other, COUNT(DISTINCT u) AS co_purchases
                    RETURN other.id AS product_id, other.name AS name,
                           co_purchases
                    ORDER BY co_purchases DESC
                    LIMIT $limit
                    """,
                    id=str(product_id), limit=n,
                )
                return [
                    {
                        "product_id": r["product_id"],
                        "name": r["name"],
                        "co_purchase_count": r["co_purchases"],
                        "reason": "Thường được mua cùng (Graph)",
                    }
                    for r in result
                ]
        except Exception as e:
            logger.error(f"get_frequently_bought_together error: {e}")
            return []

    def get_trending(self, n: int = 10) -> List[Dict]:
        """Trending products based on recent interactions."""
        session = self._get_session()
        if not session:
            return []
        try:
            with session:
                result = session.run(
                    """
                    MATCH (p:Product)<-[r:VIEWED|PURCHASED]-(:User)
                    WHERE p.status = 'active'
                    WITH p, COUNT(r) AS interactions
                    RETURN p.id AS product_id, p.name AS name,
                           interactions AS score
                    ORDER BY interactions DESC
                    LIMIT $limit
                    """,
                    limit=n,
                )
                return [
                    {
                        "product_id": r["product_id"],
                        "name": r["name"],
                        "score": float(r["score"]),
                        "reason": "Đang thịnh hành (Graph)",
                    }
                    for r in result
                ]
        except Exception as e:
            logger.error(f"get_trending error: {e}")
            return []

    # ------------------------------------------------------------------
    # User Interaction Tracking
    # ------------------------------------------------------------------

    def record_interaction(
        self,
        user_id: str,
        product_id: str,
        action: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Record a user-product interaction in the graph."""
        session = self._get_session()
        if not session:
            return False

        rel_map = {
            "view": "VIEWED",
            "purchase": "PURCHASED",
            "cart": "ADDED_TO_CART",
            "wishlist": "WISHLISTED",
            "review": "REVIEWED",
        }
        rel_type = rel_map.get(action, "INTERACTED")
        metadata = metadata or {}

        try:
            with session:
                # Ensure nodes exist
                session.run("MERGE (u:User {id: $uid})", uid=str(user_id))
                session.run(
                    "MERGE (p:Product {id: $pid})",
                    pid=str(product_id),
                )

                if rel_type == "VIEWED":
                    session.run(
                        f"""
                        MATCH (u:User {{id: $uid}}), (p:Product {{id: $pid}})
                        MERGE (u)-[r:{rel_type}]->(p)
                        SET r.count = COALESCE(r.count, 0) + 1,
                            r.last_viewed = datetime()
                        """,
                        uid=str(user_id), pid=str(product_id),
                    )
                elif rel_type == "PURCHASED":
                    session.run(
                        f"""
                        MATCH (u:User {{id: $uid}}), (p:Product {{id: $pid}})
                        MERGE (u)-[r:{rel_type}]->(p)
                        SET r.count = COALESCE(r.count, 0) + 1,
                            r.total_amount = COALESCE(r.total_amount, 0) + $amount,
                            r.last_purchase = datetime()
                        """,
                        uid=str(user_id), pid=str(product_id),
                        amount=metadata.get("amount", 0),
                    )
                else:
                    session.run(
                        f"""
                        MATCH (u:User {{id: $uid}}), (p:Product {{id: $pid}})
                        MERGE (u)-[r:{rel_type}]->(p)
                        SET r.timestamp = datetime()
                        """,
                        uid=str(user_id), pid=str(product_id),
                    )
            return True
        except Exception as e:
            logger.error(f"record_interaction error: {e}")
            return False

    # ------------------------------------------------------------------
    # Admin
    # ------------------------------------------------------------------

    def create_indexes(self):
        """Create recommended indexes."""
        session = self._get_session()
        if not session:
            return
        indexes = [
            "CREATE INDEX user_id IF NOT EXISTS FOR (u:User) ON (u.id)",
            "CREATE INDEX product_id IF NOT EXISTS FOR (p:Product) ON (p.id)",
            "CREATE INDEX product_status IF NOT EXISTS FOR (p:Product) ON (p.status)",
            "CREATE INDEX category_name IF NOT EXISTS FOR (c:Category) ON (c.name)",
            "CREATE INDEX brand_name IF NOT EXISTS FOR (b:Brand) ON (b.name)",
        ]
        with session:
            for q in indexes:
                try:
                    session.run(q)
                except Exception as e:
                    logger.warning(f"Index creation warning: {e}")
        logger.info("Neo4j indexes created/verified")

    def clear_graph(self):
        """Clear all nodes and relationships (use with caution!)."""
        session = self._get_session()
        if not session:
            return
        with session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.warning("Neo4j graph cleared")

    def ask_for_clarification(self, entities) -> Optional[str]:
        """Generate a clarification prompt when product search is ambiguous."""
        ent = _QueryEntities(entities)
        hints = []
        if not ent.category:
            hints.append("danh mục sản phẩm bạn muốn tìm")
        if not ent.brand and ent.category:
            hints.append(f"thương hiệu {ent.category} bạn quan tâm")
        if ent.price_min and not ent.price_max:
            hints.append("mức giá tối đa bạn muốn")
        if not hints:
            hints.append("thông tin chi tiết hơn về sản phẩm bạn cần")
        msg = f"Bạn có thể cho tôi biết thêm {' và '.join(hints)} không?"
        logger.info(f"[KG] ask_for_clarification: confidence={ent.confidence}, msg='{msg}'")
        return msg

    def get_stats(self) -> Dict[str, int]:
        """Get graph statistics."""
        session = self._get_session()
        if not session:
            return {"error": "Neo4j not available"}
        try:
            with session:
                users = session.run(
                    "MATCH (u:User) RETURN COUNT(u) AS c"
                ).single()["c"]
                products = session.run(
                    "MATCH (p:Product) RETURN COUNT(p) AS c"
                ).single()["c"]
                categories = session.run(
                    "MATCH (c:Category) RETURN COUNT(c) AS c"
                ).single()["c"]
                rels = session.run(
                    "MATCH ()-[r]->() RETURN COUNT(r) AS c"
                ).single()["c"]
                return {
                    "users": users,
                    "products": products,
                    "categories": categories,
                    "relationships": rels,
                }
        except Exception as e:
            logger.error(f"get_stats error: {e}")
            return {"error": str(e)}


# Singleton instance
kg_client = UnifiedKGClient()
