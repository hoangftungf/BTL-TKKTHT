"""
AI Chatbot Engine with Ollama LLM Integration and RAG + Knowledge Graph Support
Bước 2c: Tích hợp RAG với Knowledge Graph cho chatbot
"""

import os
import re
import json
import logging
import httpx
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


# ===================== INTENT & ENTITY EXTRACTION =====================

@dataclass
class ExtractedEntities:
    """Structured entities extracted from user query"""
    category: Optional[str] = None
    price_max: Optional[int] = None
    price_min: Optional[int] = None
    price_exact: Optional[int] = None
    brand: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    raw_query: str = ""
    confidence: float = 0.0


class QueryParser:
    """
    Parse natural language queries into structured data.
    Handles Vietnamese language patterns for e-commerce.
    """

    # Category mappings (Vietnamese keywords -> normalized category for Neo4j search)
    # Keys are the normalized category names that will be used in Neo4j CONTAINS query
    # Includes both diacritics and non-diacritics versions
    CATEGORY_PATTERNS = {
        'laptop': ['laptop', 'máy tính xách tay', 'may tinh xach tay', 'notebook', 'macbook'],
        'điện thoại': ['điện thoại', 'dien thoai', 'phone', 'smartphone', 'di động', 'di dong', 'dt', 'dienthoai'],
        'tablet': ['tablet', 'máy tính bảng', 'may tinh bang', 'ipad'],
        'giày': ['giày', 'giay', 'giầy', 'sneaker', 'boot', 'dép', 'dep', 'sandal', 'giay dep'],
        'áo': ['áo', 'ao', 'áo sơ mi', 'ao so mi', 'áo thun', 'ao thun', 'áo khoác', 'ao khoac', 't-shirt', 'tshirt', 'shirt'],
        'quần': ['quần', 'quan', 'quần jean', 'quan jean', 'quần tây', 'quan tay', 'quần short', 'quan short'],
        'mỹ phẩm': ['mỹ phẩm', 'my pham', 'son', 'kem', 'serum', 'toner', 'makeup', 'skincare', 'dưỡng da', 'duong da'],
        'đồng hồ': ['đồng hồ', 'dong ho', 'watch', 'smartwatch', 'apple watch'],
        'tai nghe': ['tai nghe', 'headphone', 'earphone', 'airpod', 'earbud'],
        'túi xách': ['túi', 'tui', 'túi xách', 'tui xach', 'balo', 'ba lô', 'ba lo', 'cặp', 'cap', 'handbag'],
        'gia dụng': ['gia dụng', 'gia dung', 'nồi', 'noi', 'chảo', 'chao', 'máy xay', 'may xay', 'máy ép', 'may ep', 'quạt', 'quat', 'điều hòa', 'dieu hoa', 'máy giặt', 'may giat'],
        'sách': ['sách', 'sach', 'book', 'truyện', 'truyen', 'tiểu thuyết', 'tieu thuyet'],
    }

    # Map specific product types to broader Neo4j categories (for flexible matching)
    # This helps when Neo4j has different category names
    CATEGORY_NEO4J_ALIASES = {
        'điện thoại': ['phone', 'điện thoại', 'smartphone', 'mobile'],
        'laptop': ['laptop', 'máy tính', 'computer', 'notebook'],
        'giày': ['giày', 'shoe', 'footwear', 'giày dép'],
        'gia dụng': ['gia dụng', 'home', 'appliance', 'đồ gia dụng'],
    }

    # Brand patterns
    BRAND_PATTERNS = {
        'apple': ['apple', 'iphone', 'ipad', 'macbook', 'airpod'],
        'samsung': ['samsung', 'galaxy'],
        'xiaomi': ['xiaomi', 'redmi', 'poco'],
        'asus': ['asus', 'rog', 'zenbook', 'vivobook'],
        'dell': ['dell', 'xps', 'inspiron', 'latitude'],
        'hp': ['hp', 'pavilion', 'envy', 'spectre'],
        'lenovo': ['lenovo', 'thinkpad', 'ideapad', 'legion'],
        'nike': ['nike', 'air jordan', 'air force'],
        'adidas': ['adidas', 'yeezy'],
        'sony': ['sony', 'playstation', 'ps5'],
    }

    # Price patterns (Vietnamese - both diacritics and non-diacritics)
    PRICE_PATTERNS = [
        # "20 triệu", "20triệu", "20 tr", "20trieu"
        (r'(\d+(?:[.,]\d+)?)\s*(triệu|trieu|tr)', 1_000_000),
        # "500k", "500 nghìn", "500nghin"
        (r'(\d+(?:[.,]\d+)?)\s*(k|nghìn|nghin|nghìn đồng|nghin dong)', 1_000),
        # "2 tỷ", "2ty"
        (r'(\d+(?:[.,]\d+)?)\s*(tỷ|ty)', 1_000_000_000),
        # Plain number with many digits (assume VND)
        (r'(\d{6,})\s*(?:đ|d|đồng|dong|vnd)?', 1),
    ]

    # Price constraint patterns
    PRICE_CONSTRAINT_PATTERNS = {
        'max': [
            r'(?:dưới|duoi|under|<=?|tối đa|max|không quá|ko quá)\s*',
            r'(?:giá|gia)?\s*(?:dưới|duoi|under)\s*',
            r'(?:khoảng|tầm|around)?\s*(\d)',  # "khoảng 20tr" implies max
        ],
        'min': [
            r'(?:trên|tren|trở lên|above|>=?|tối thiểu|min|từ)\s*',
            r'(?:giá|gia)?\s*(?:trên|tren|over)\s*',
        ],
        'range': [
            r'(?:từ|tu)\s*(\d+(?:[.,]\d+)?)\s*(?:triệu|tr|k)?\s*(?:đến|den|tới|toi|-)\s*(\d+(?:[.,]\d+)?)\s*(?:triệu|tr|k)?',
        ],
    }

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for efficiency"""
        self._category_regex = {}
        for cat, keywords in self.CATEGORY_PATTERNS.items():
            pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            self._category_regex[cat] = re.compile(pattern, re.IGNORECASE)

        self._brand_regex = {}
        for brand, keywords in self.BRAND_PATTERNS.items():
            pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            self._brand_regex[brand] = re.compile(pattern, re.IGNORECASE)

    def parse(self, query: str) -> ExtractedEntities:
        """
        Parse user query and extract structured entities.

        Example:
            "tư vấn laptop giá 20 triệu" ->
            ExtractedEntities(category="laptop", price_max=20000000)
        """
        entities = ExtractedEntities(raw_query=query)
        query_lower = query.lower()

        # 1. Extract category
        entities.category = self._extract_category(query_lower)

        # 2. Extract brand
        entities.brand = self._extract_brand(query_lower)

        # 3. Extract price constraints
        self._extract_price(query_lower, entities)

        # 4. Calculate confidence
        entities.confidence = self._calculate_confidence(entities)

        logger.info(f"Parsed query '{query}' -> category={entities.category}, "
                    f"price_max={entities.price_max}, price_min={entities.price_min}, "
                    f"brand={entities.brand}, confidence={entities.confidence:.2f}")

        return entities

    def _extract_category(self, query: str) -> Optional[str]:
        """Extract product category from query"""
        for category, regex in self._category_regex.items():
            if regex.search(query):
                return category
        return None

    def _extract_brand(self, query: str) -> Optional[str]:
        """Extract brand from query"""
        for brand, regex in self._brand_regex.items():
            if regex.search(query):
                return brand
        return None

    def _extract_price(self, query: str, entities: ExtractedEntities) -> None:
        """Extract price constraints from query"""
        # Check for price range first (supports both diacritics and non-diacritics)
        range_match = re.search(
            r'(?:từ|tu)\s*(\d+(?:[.,]\d+)?)\s*(triệu|trieu|tr|k)?\s*(?:đến|den|tới|toi|-)\s*(\d+(?:[.,]\d+)?)\s*(triệu|trieu|tr|k)?',
            query, re.IGNORECASE
        )
        if range_match:
            min_val = self._parse_number(range_match.group(1))
            min_unit = range_match.group(2) or range_match.group(4) or 'trieu'
            max_val = self._parse_number(range_match.group(3))
            max_unit = range_match.group(4) or min_unit

            entities.price_min = int(min_val * self._get_unit_multiplier(min_unit))
            entities.price_max = int(max_val * self._get_unit_multiplier(max_unit))
            return

        # Check for max price constraint (supports both diacritics and non-diacritics)
        max_patterns = [
            r'(?:dưới|duoi|under|tối đa|toi da|max|không quá|khong qua|ko quá|ko qua)\s*(\d+(?:[.,]\d+)?)\s*(triệu|trieu|tr|k|nghìn|nghin)?',
            r'(?:giá|gia)\s*(?:dưới|duoi)\s*(\d+(?:[.,]\d+)?)\s*(triệu|trieu|tr|k)?',
        ]
        for pattern in max_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                value = self._parse_number(match.group(1))
                unit = match.group(2) if match.lastindex >= 2 else 'trieu'
                entities.price_max = int(value * self._get_unit_multiplier(unit))
                return

        # Check for min price constraint
        min_patterns = [
            r'(?:trên|tren|từ|tu|trở lên|tro len|above|tối thiểu|toi thieu|min)\s*(\d+(?:[.,]\d+)?)\s*(triệu|trieu|tr|k)?',
        ]
        for pattern in min_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                value = self._parse_number(match.group(1))
                unit = match.group(2) if match.lastindex >= 2 else 'trieu'
                entities.price_min = int(value * self._get_unit_multiplier(unit))
                return

        # Extract any price mention as approximate max (user usually means "around" or "under")
        for pattern, base_multiplier in self.PRICE_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                value = self._parse_number(match.group(1))
                unit = match.group(2) if match.lastindex >= 2 else None
                multiplier = self._get_unit_multiplier(unit) if unit else base_multiplier
                price = int(value * multiplier)

                # Check context for constraint type (supports both diacritics and non-diacritics)
                if re.search(r'(khoảng|khoang|tầm|tam|around|approximately|~)', query):
                    # "khoảng 20tr" -> range +/-20%
                    entities.price_min = int(price * 0.8)
                    entities.price_max = int(price * 1.2)
                else:
                    # Default: treat as max price
                    entities.price_max = price
                return

    def _parse_number(self, num_str: str) -> float:
        """Parse number string, handling Vietnamese/European formats"""
        num_str = num_str.replace(',', '.').replace(' ', '')
        return float(num_str)

    def _get_unit_multiplier(self, unit: Optional[str]) -> int:
        """Get multiplier for price unit"""
        if not unit:
            return 1_000_000  # Default to triệu
        unit = unit.lower()
        if unit in ('triệu', 'tr', 'trieu'):
            return 1_000_000
        elif unit in ('k', 'nghìn', 'nghin', 'nghìn đồng', 'nghin dong'):
            return 1_000
        elif unit in ('tỷ', 'ty'):
            return 1_000_000_000
        return 1

    def _calculate_confidence(self, entities: ExtractedEntities) -> float:
        """Calculate confidence score for extracted entities"""
        score = 0.0
        if entities.category:
            score += 0.4
        if entities.price_max or entities.price_min:
            score += 0.3
        if entities.brand:
            score += 0.2
        if entities.attributes:
            score += 0.1
        return min(score, 1.0)


# Global parser instance
query_parser = QueryParser()

# Neo4j configuration
NEO4J_URI = getattr(settings, 'NEO4J_URI', os.environ.get('NEO4J_URI', 'bolt://localhost:7687'))
NEO4J_USER = getattr(settings, 'NEO4J_USER', os.environ.get('NEO4J_USER', 'neo4j'))
NEO4J_PASSWORD = getattr(settings, 'NEO4J_PASSWORD', os.environ.get('NEO4J_PASSWORD', 'password123'))


# ===================== RAG COMPONENTS =====================

class ProductVectorStore:
    """
    Vector Store for product embeddings using FAISS
    """

    def __init__(self):
        self.index = None
        self.product_ids = []
        self.product_data = {}
        self.embedding_dim = 768  # nomic-embed-text embedding dimension
        self._initialized = False

    def _initialize(self):
        """Initialize FAISS index"""
        if self._initialized:
            return

        try:
            import faiss
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self._initialized = True
            logger.info("FAISS index initialized for chatbot")
        except ImportError:
            logger.warning("FAISS not available, using simple similarity")
            self._embeddings = []
            self._initialized = True

    def add(self, product_id, embedding, product_data=None):
        """Add product to vector store"""
        self._initialize()

        embedding = np.array(embedding).astype('float32')
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        if len(embedding.shape) == 1:
            embedding = embedding.reshape(1, -1)

        if self.index is not None:
            self.index.add(embedding)
        else:
            self._embeddings.append(embedding[0])

        self.product_ids.append(str(product_id))
        if product_data:
            self.product_data[str(product_id)] = product_data

    def search(self, query_embedding, k=5):
        """Search for similar products"""
        self._initialize()

        if len(self.product_ids) == 0:
            return []

        query_embedding = np.array(query_embedding).astype('float32')
        norm = np.linalg.norm(query_embedding)
        if norm > 0:
            query_embedding = query_embedding / norm

        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)

        if self.index is not None:
            import faiss
            distances, indices = self.index.search(query_embedding, min(k, len(self.product_ids)))
            results = []
            for i, idx in enumerate(indices[0]):
                if idx >= 0 and idx < len(self.product_ids):
                    product_id = self.product_ids[idx]
                    results.append({
                        'product_id': product_id,
                        'score': float(distances[0][i]),
                        'data': self.product_data.get(product_id, {})
                    })
            return results
        else:
            if not hasattr(self, '_embeddings') or len(self._embeddings) == 0:
                return []
            embeddings = np.array(self._embeddings)
            scores = np.dot(embeddings, query_embedding.T).flatten()
            top_indices = np.argsort(scores)[::-1][:k]
            results = []
            for idx in top_indices:
                product_id = self.product_ids[idx]
                results.append({
                    'product_id': product_id,
                    'score': float(scores[idx]),
                    'data': self.product_data.get(product_id, {})
                })
            return results


class TextEmbedder:
    """Generate text embeddings"""

    def __init__(self, ollama_host):
        self.ollama_host = ollama_host
        self._tfidf = None

    def embed(self, texts):
        """Generate embeddings for texts using Ollama's nomic-embed-text model"""
        if isinstance(texts, str):
            texts = [texts]

        # Use nomic-embed-text for semantic embeddings (768 dimensions)
        # Batch process for efficiency
        try:
            # Process in batches of 10 for better performance
            batch_size = 10
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                response = httpx.post(
                    f"{self.ollama_host}/api/embed",
                    json={"model": "nomic-embed-text", "input": batch},
                    timeout=120.0  # Longer timeout for batches
                )
                if response.status_code == 200:
                    result = response.json()
                    emb_list = result.get('embeddings', [])
                    for emb in emb_list:
                        all_embeddings.append(emb if emb else [0.0] * 768)
                else:
                    logger.warning(f"Ollama embed returned {response.status_code}")
                    all_embeddings.extend([[0.0] * 768] * len(batch))

            return np.array(all_embeddings)
        except Exception as e:
            logger.warning(f"Ollama embedding failed: {e}, using TF-IDF")

        # Fallback to TF-IDF
        from sklearn.feature_extraction.text import TfidfVectorizer
        if self._tfidf is None:
            self._tfidf = TfidfVectorizer(max_features=768)
        try:
            if hasattr(self._tfidf, 'vocabulary_') and self._tfidf.vocabulary_:
                return self._tfidf.transform(texts).toarray()
            else:
                return self._tfidf.fit_transform(texts).toarray()
        except:
            return np.zeros((len(texts), 768))


class KnowledgeGraphClient:
    """
    Client để query Neo4j Knowledge Graph
    Cung cấp context bổ sung cho RAG
    """

    def __init__(self):
        self.driver = None
        self._connect()

    def _connect(self):
        """Connect to Neo4j"""
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            logger.info(f"Connected to Neo4j at {NEO4J_URI}")
        except Exception as e:
            logger.warning(f"Cannot connect to Neo4j: {e}")
            self.driver = None

    def _get_session(self):
        if self.driver is None:
            self._connect()
        if self.driver:
            return self.driver.session()
        return None

    def get_product_recommendations(self, user_id, n=5):
        """Lấy recommendations cho user từ graph"""
        session = self._get_session()
        if not session:
            return []

        try:
            with session:
                result = session.run("""
                    MATCH (u:User {id: $user_id})-[:PURCHASED|VIEWED]->(p:Product)
                          <-[:PURCHASED|VIEWED]-(other:User)-[:PURCHASED]->(rec:Product)
                    WHERE NOT (u)-[:PURCHASED]->(rec)
                    WITH rec, COUNT(DISTINCT other) AS score
                    RETURN rec.id AS product_id, rec.name AS name, rec.price AS price, score
                    ORDER BY score DESC
                    LIMIT $limit
                """, user_id=str(user_id), limit=n)

                return [{
                    'product_id': r['product_id'],
                    'name': r['name'],
                    'price': r['price'],
                    'score': r['score'],
                    'reason': 'Nguoi dung tuong tu cung thich'
                } for r in result]
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []

    def get_frequently_bought_together(self, product_id, n=3):
        """Sản phẩm thường mua cùng"""
        session = self._get_session()
        if not session:
            return []

        try:
            with session:
                result = session.run("""
                    MATCH (p:Product {id: $product_id})<-[:PURCHASED]-(u:User)
                          -[:PURCHASED]->(other:Product)
                    WHERE other.id <> $product_id
                    WITH other, COUNT(DISTINCT u) AS co_purchases
                    RETURN other.id AS product_id, other.name AS name, co_purchases
                    ORDER BY co_purchases DESC
                    LIMIT $limit
                """, product_id=str(product_id), limit=n)

                return [{
                    'product_id': r['product_id'],
                    'name': r['name'],
                    'co_purchases': r['co_purchases']
                } for r in result]
        except Exception as e:
            logger.error(f"Error getting bought together: {e}")
            return []

    def search_by_category(self, category_keyword, n=5):
        """Tìm sản phẩm theo category"""
        session = self._get_session()
        if not session:
            return []

        try:
            with session:
                result = session.run("""
                    MATCH (c:Category)
                    WHERE toLower(c.name) CONTAINS toLower($keyword)
                    MATCH (p:Product)-[:BELONGS_TO]->(c)
                    OPTIONAL MATCH (:User)-[r:PURCHASED]->(p)
                    WITH p, c, COUNT(r) AS purchases
                    RETURN p.id AS product_id, p.name AS name, p.price AS price,
                           c.name AS category, purchases
                    ORDER BY purchases DESC
                    LIMIT $limit
                """, keyword=category_keyword, limit=n)

                return [{
                    'product_id': r['product_id'],
                    'name': r['name'],
                    'price': r['price'],
                    'category': r['category'],
                    'score': r['purchases']
                } for r in result]
        except Exception as e:
            logger.error(f"Error searching by category: {e}")
            return []

    def search_products_structured(self, entities: 'ExtractedEntities', n=5) -> List[Dict]:
        """
        Search products using structured entities from QueryParser.
        Builds dynamic Cypher query based on extracted entities.

        STRICT MATCHING: Only returns products that match category AND price constraints.
        NO FALLBACK to random/trending products.

        Args:
            entities: ExtractedEntities from QueryParser.parse()
            n: Number of results to return

        Returns:
            List of products matching the structured query
        """
        session = self._get_session()
        if not session:
            logger.warning("No Neo4j session available for structured search")
            return []

        try:
            with session:
                # Build dynamic Cypher query with STRICT category matching
                where_clauses = []
                params = {"limit": n}

                # STRICT Category filter - must match category
                if entities.category:
                    # Use MATCH to require category relationship
                    query_start = """
                        MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
                        WHERE toLower(c.name) CONTAINS toLower($category)
                    """
                    params["category"] = entities.category
                    logger.info(f"[DEBUG] Neo4j category filter: {entities.category}")
                else:
                    # No category specified - match all products
                    query_start = """
                        MATCH (p:Product)
                        OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)
                        WHERE 1=1
                    """

                # Brand filter
                if entities.brand:
                    where_clauses.append(
                        "(toLower(p.name) CONTAINS toLower($brand) OR "
                        "toLower(coalesce(p.brand, '')) CONTAINS toLower($brand))"
                    )
                    params["brand"] = entities.brand
                    logger.info(f"[DEBUG] Neo4j brand filter: {entities.brand}")

                # STRICT Price filters
                if entities.price_max:
                    where_clauses.append("p.price <= $price_max")
                    params["price_max"] = entities.price_max
                    logger.info(f"[DEBUG] Neo4j price_max filter: {entities.price_max}")

                if entities.price_min:
                    where_clauses.append("p.price >= $price_min")
                    params["price_min"] = entities.price_min
                    logger.info(f"[DEBUG] Neo4j price_min filter: {entities.price_min}")

                # Build WHERE clause for additional filters
                additional_where = ""
                if where_clauses:
                    additional_where = " AND " + " AND ".join(where_clauses)

                # Complete query with scoring
                cypher_query = f"""
                    {query_start}
                    {additional_where}
                    OPTIONAL MATCH (:User)-[r:PURCHASED|VIEWED|CLICKED]->(p)
                    WITH p, c, COUNT(r) AS popularity
                    RETURN p.id AS product_id,
                           p.name AS name,
                           p.price AS price,
                           coalesce(p.brand, '') AS brand,
                           coalesce(p.description, '') AS description,
                           coalesce(p.image_url, '') AS image_url,
                           coalesce(c.name, '') AS category,
                           popularity
                    ORDER BY popularity DESC, p.price ASC
                    LIMIT $limit
                """

                logger.info(f"[DEBUG] Neo4j Query:\n{cypher_query}")
                logger.info(f"[DEBUG] Query params: {params}")

                result = session.run(cypher_query, **params)

                products = []
                for r in result:
                    products.append({
                        'product_id': r['product_id'],
                        'name': r['name'],
                        'price': r['price'],
                        'brand': r['brand'],
                        'description': r['description'],
                        'image_url': r['image_url'],
                        'category': r['category'],
                        'popularity': r['popularity'],
                        'source': 'kg_structured'
                    })

                logger.info(f"[DEBUG] Structured search found {len(products)} products: "
                           f"{[p['name'] for p in products[:3]]}")
                return products

        except Exception as e:
            logger.error(f"Error in structured search: {e}")
            return []

    def ask_for_clarification(self, entities: 'ExtractedEntities') -> Optional[str]:
        """
        Generate clarification question if entities are insufficient.

        Returns:
            Clarification question string, or None if entities are sufficient
        """
        if entities.confidence >= 0.4:
            return None

        if not entities.category and not entities.brand:
            return "Bạn muốn tìm sản phẩm loại gì? (laptop, điện thoại, giày, áo, mỹ phẩm...)"

        return None

    def get_trending_products(self, n=5):
        """Lấy sản phẩm trending"""
        session = self._get_session()
        if not session:
            return []

        try:
            with session:
                result = session.run("""
                    MATCH (u:User)-[r:PURCHASED|VIEWED|CLICKED]->(p:Product)
                    WITH p, COUNT(r) AS interactions
                    RETURN p.id AS product_id, p.name AS name, p.price AS price, interactions
                    ORDER BY interactions DESC
                    LIMIT $limit
                """, limit=n)

                return [{
                    'product_id': r['product_id'],
                    'name': r['name'],
                    'price': r['price'],
                    'interactions': r['interactions'],
                    'reason': 'San pham pho bien'
                } for r in result]
        except Exception as e:
            logger.error(f"Error getting trending: {e}")
            return []


# Global KG client
kg_client = KnowledgeGraphClient()


class RAGPipeline:
    """
    RAG Pipeline for product-aware responses
    """

    def __init__(self, ollama_host, ollama_model):
        self.ollama_host = ollama_host
        self.ollama_model = ollama_model
        self.embedder = TextEmbedder(ollama_host)
        self.vector_store = ProductVectorStore()
        self._indexed = False

    def index_products(self):
        """Index products from product service"""
        if self._indexed:
            return

        product_service_url = getattr(settings, 'PRODUCT_SERVICE_URL', 'http://product-service:8000/api/products')

        try:
            response = httpx.get(f"{product_service_url}?page_size=500", timeout=30.0)
            if response.status_code == 200:
                products = response.json().get('results', [])

                texts = []
                for p in products:
                    text = f"{p.get('name', '')} {p.get('description', '')} {p.get('brand', '')}"
                    if p.get('category'):
                        if isinstance(p['category'], dict):
                            text += f" {p['category'].get('name', '')}"
                    texts.append(text)

                if texts:
                    embeddings = self.embedder.embed(texts)
                    for i, (p, emb) in enumerate(zip(products, embeddings)):
                        self.vector_store.add(
                            product_id=p['id'],
                            embedding=emb,
                            product_data={
                                'name': p.get('name', ''),
                                'price': p.get('price'),
                                'category': p.get('category', {}).get('name') if isinstance(p.get('category'), dict) else '',
                                'brand': p.get('brand', '')
                            }
                        )

                self._indexed = True
                logger.info(f"Indexed {len(products)} products for RAG")
        except Exception as e:
            logger.error(f"Failed to index products: {e}")

    def retrieve(self, query, k=5, user_id=None):
        """Retrieve relevant products - STRICT filtering by category and price"""
        self.index_products()

        cache_key = f"rag_kg_chatbot:{hash(query)}:{k}:{user_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # 1. Parse query to extract structured entities
        entities = query_parser.parse(query)

        # DEBUG: Log extracted entities
        logger.info(f"[DEBUG] Query: '{query}'")
        logger.info(f"[DEBUG] Extracted entities - category: {entities.category}, "
                    f"price_min: {entities.price_min}, price_max: {entities.price_max}, "
                    f"brand: {entities.brand}, confidence: {entities.confidence}")

        # 2. Use ONLY structured search based on extracted entities
        kg_results = []
        if entities.category or entities.price_max or entities.price_min or entities.brand:
            kg_results = self._query_knowledge_graph_structured(entities, user_id, k)
            logger.info(f"[DEBUG] KG structured search returned {len(kg_results)} products")

        # 3. NO FALLBACK - Do not add unrelated products
        # If no results from structured search, return empty (will trigger no_results_response)

        # 4. Apply strict filtering to ensure all products match criteria
        filtered_results = self._strict_filter_products(kg_results, entities)
        logger.info(f"[DEBUG] After strict filter: {len(filtered_results)} products")

        # 5. Format results
        merged = []
        for r in filtered_results[:k]:
            merged.append({
                'product_id': r.get('product_id'),
                'score': r.get('popularity', 0) + 1,
                'data': {
                    'name': r.get('name', ''),
                    'price': r.get('price'),
                    'category': r.get('category', ''),
                    'brand': r.get('brand', ''),
                    'description': r.get('description', ''),
                    'image_url': r.get('image_url', '')
                },
                'sources': [r.get('source', 'kg_structured')]
            })

        logger.info(f"[DEBUG] Final products: {[p['data']['name'] for p in merged]}")

        cache.set(cache_key, merged, timeout=300)
        return merged, entities

    def _strict_filter_products(self, products: List[Dict], entities: ExtractedEntities) -> List[Dict]:
        """
        STRICT filtering - only keep products that match ALL specified criteria.
        DO NOT return products outside the query constraints.
        """
        if not products:
            return []

        filtered = []
        for p in products:
            # Check price constraints
            price = p.get('price')
            if price is not None:
                try:
                    price = float(price)
                    if entities.price_max and price > entities.price_max:
                        logger.debug(f"[FILTER] Excluded {p.get('name')} - price {price} > max {entities.price_max}")
                        continue
                    if entities.price_min and price < entities.price_min:
                        logger.debug(f"[FILTER] Excluded {p.get('name')} - price {price} < min {entities.price_min}")
                        continue
                except (ValueError, TypeError):
                    pass

            # Product passes all filters
            filtered.append(p)

        return filtered

    def _query_knowledge_graph_structured(self, entities: ExtractedEntities, user_id=None, k=5):
        """
        Query Knowledge Graph using structured entities.
        STRICT: Only returns products matching the extracted criteria.
        NO user recommendations that might be from different categories.
        """
        results = []

        # Use structured search if we have category, price, or brand
        if entities.category or entities.price_max or entities.price_min or entities.brand:
            structured_results = kg_client.search_products_structured(entities, n=k)
            results.extend(structured_results)
            logger.info(f"[DEBUG] Structured KG search returned {len(structured_results)} results")

        # DO NOT add user recommendations - they may include irrelevant categories
        # User recommendations should only be shown on homepage, not in search results

        return results

    def _query_knowledge_graph_fallback(self, query, user_id=None, k=5):
        """Fallback KG query for when structured search doesn't work"""
        results = []

        # Get trending if no specific user
        trending = kg_client.get_trending_products(n=k // 2)
        for p in trending:
            p['source'] = 'kg_trending'
        results.extend(trending)

        # Search by category keywords in query (legacy approach)
        keywords = ['laptop', 'dien thoai', 'phone', 'tablet', 'dong ho',
                    'thoi trang', 'gia dung', 'sach', 'the thao', 'my pham']
        for kw in keywords:
            if kw in query.lower():
                cat_results = kg_client.search_by_category(kw, n=k // 2)
                for p in cat_results:
                    p['source'] = 'kg_category'
                results.extend(cat_results)
                break

        return results

    def _query_knowledge_graph(self, query, user_id=None, k=5):
        """Query Knowledge Graph for additional context (legacy compatibility)"""
        entities = query_parser.parse(query)
        results = self._query_knowledge_graph_structured(entities, user_id, k)
        if not results:
            results = self._query_knowledge_graph_fallback(query, user_id, k)
        return results

    def _merge_results_with_entities(self, vector_results, kg_results, entities: ExtractedEntities, k):
        """Merge results with priority based on entity match"""
        product_scores = {}

        # KG structured results get higher weight when entities are clear
        kg_weight = 0.7 if entities.confidence >= 0.5 else 0.4
        vector_weight = 1.0 - kg_weight

        # KG results (prioritize structured matches)
        for r in kg_results:
            pid = r.get('product_id')
            if pid:
                score = kg_weight
                # Boost products that match price constraints
                if entities.price_max and r.get('price'):
                    try:
                        price = float(r['price'])
                        if price <= entities.price_max:
                            score += 0.2
                    except (ValueError, TypeError):
                        pass

                if pid in product_scores:
                    product_scores[pid]['score'] += score
                    product_scores[pid]['sources'].append(r.get('source', 'kg'))
                else:
                    product_scores[pid] = {
                        'product_id': pid,
                        'score': score,
                        'data': {
                            'name': r.get('name', ''),
                            'price': r.get('price'),
                            'category': r.get('category', ''),
                            'brand': r.get('brand', ''),
                            'description': r.get('description', ''),
                            'image_url': r.get('image_url', '')
                        },
                        'sources': [r.get('source', 'kg')]
                    }

        # Vector results
        for r in vector_results:
            pid = r.get('product_id')
            if pid:
                if pid in product_scores:
                    product_scores[pid]['score'] += r.get('score', 0) * vector_weight
                    product_scores[pid]['sources'].append('vector')
                else:
                    product_scores[pid] = {
                        'product_id': pid,
                        'score': r.get('score', 0) * vector_weight,
                        'data': r.get('data', {}),
                        'sources': ['vector']
                    }

        # Sort and return
        results = sorted(product_scores.values(), key=lambda x: x['score'], reverse=True)
        return results[:k]

    def _merge_results(self, vector_results, kg_results, k):
        """Merge và rank kết quả từ vector search và KG"""
        product_scores = {}

        # Vector results (weight 0.6)
        for r in vector_results:
            pid = r.get('product_id')
            if pid:
                product_scores[pid] = {
                    'product_id': pid,
                    'score': r.get('score', 0) * 0.6,
                    'data': r.get('data', {}),
                    'sources': ['vector']
                }

        # KG results (weight 0.4)
        for r in kg_results:
            pid = r.get('product_id')
            if pid:
                if pid in product_scores:
                    product_scores[pid]['score'] += 0.4
                    product_scores[pid]['sources'].append(r.get('source', 'kg'))
                else:
                    product_scores[pid] = {
                        'product_id': pid,
                        'score': 0.4,
                        'data': {
                            'name': r.get('name', ''),
                            'price': r.get('price'),
                            'category': r.get('category', '')
                        },
                        'sources': [r.get('source', 'kg')]
                    }

        # Sort and return
        results = sorted(product_scores.values(), key=lambda x: x['score'], reverse=True)
        return results[:k]

    def generate_augmented_response(self, query, context_products, kg_context=None):
        """Generate response with product context + Knowledge Graph context"""
        # Check cache first
        cache_key = f"rag_response:{hash(query)}:{hash(str(context_products))}"
        cached_response = cache.get(cache_key)
        if cached_response:
            logger.info("RAG response from cache")
            return cached_response

        context = self._build_context(context_products)

        # Add KG context if available
        kg_info = ""
        if kg_context:
            if kg_context.get('bought_together'):
                items = [b.get('name') for b in kg_context['bought_together'][:2] if b.get('name')]
                if items:
                    kg_info += f"\nSan pham thuong mua kem: {', '.join(items)}"
            if kg_context.get('trending'):
                kg_info += "\n(Dang la san pham pho bien)"

        # Shorter, more focused prompt for faster generation
        prompt = f"""Tro ly AI shop. Goi y san pham cho khach.

San pham:
{context}
{kg_info}

Hoi: {query}

Tra loi ngan (1-2 cau):"""

        try:
            response = httpx.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 150,  # Limit output tokens for faster response
                        "temperature": 0.7
                    }
                },
                timeout=90.0  # Increased timeout
            )
            if response.status_code == 200:
                result = response.json().get('response', '')
                if result:
                    # Cache successful response
                    cache.set(cache_key, result, timeout=600)
                    return result
        except httpx.TimeoutException:
            logger.warning("RAG generation timeout - using fallback")
        except Exception as e:
            logger.error(f"RAG generation error: {e}")

        return self._fallback_response(context_products)

    def _build_context(self, products):
        lines = []
        for i, p in enumerate(products[:5], 1):
            data = p.get('data', {})
            line = f"{i}. {data.get('name', 'Unknown')}"
            if data.get('price'):
                try:
                    price = float(data['price'])
                    line += f" - {price:,.0f}đ"
                except (ValueError, TypeError):
                    line += f" - {data['price']}đ"
            if data.get('category'):
                line += f" ({data['category']})"
            lines.append(line)
        return '\n'.join(lines)

    def _fallback_response(self, products):
        if not products:
            return "Xin lỗi, tôi không tìm thấy sản phẩm phù hợp. Bạn có thể mô tả chi tiết hơn không?"
        response = "Dưới đây là một số sản phẩm phù hợp với yêu cầu của bạn:\n\n"
        for i, p in enumerate(products[:3], 1):
            data = p.get('data', {})
            name = data.get('name', 'Sản phẩm')
            response += f"**{i}. {name}**"
            if data.get('price'):
                try:
                    price = float(data['price'])
                    response += f" - {price:,.0f}đ"
                except (ValueError, TypeError):
                    response += f" - {data['price']}đ"
            if data.get('category'):
                response += f" ({data['category']})"
            response += "\n"
        response += "\nBạn muốn tìm hiểu thêm về sản phẩm nào?"
        return response


class IntentClassifier:
    """Phân loại ý định người dùng với hỗ trợ tư vấn sản phẩm"""

    # Product-related keywords for detection
    PRODUCT_KEYWORDS = [
        'laptop', 'điện thoại', 'phone', 'máy tính', 'tablet', 'ipad',
        'giày', 'dép', 'áo', 'quần', 'váy', 'đầm', 'túi', 'balo',
        'đồng hồ', 'watch', 'tai nghe', 'headphone', 'airpod',
        'mỹ phẩm', 'son', 'kem', 'serum', 'skincare',
        'sách', 'truyện', 'nồi', 'chảo', 'quạt', 'điều hòa',
        'iphone', 'samsung', 'xiaomi', 'macbook', 'dell', 'asus',
        'nike', 'adidas', 'sony', 'apple'
    ]

    INTENT_PATTERNS = {
        'greeting': [
            r'\b(xin chào|chào|hi|hello|hey)\b',
            r'^(chào|hi|hello)',
        ],
        'product_search': [
            # Tư vấn patterns
            r'\b(tư vấn|tu van|gợi ý|goi y|recommend|đề xuất|de xuat)\b',
            # Tìm kiếm patterns
            r'\b(tìm|tìm kiếm|search|kiếm|muốn mua|cần mua)\b',
            # Giá patterns
            r'\b(giá|gia)\s*\d+',
            r'\d+\s*(triệu|tr|k|nghìn)',
            # Mua/Bán patterns
            r'\b(có|bán|có bán)\b.*\b(không|gì|nào)\b',
            r'\b(mua|cần|muốn|want)\b',
            # Hỏi về sản phẩm
            r'\b(nào tốt|nào hay|nào đẹp|chọn gì)\b',
            r'\b(dưới|duoi|under|khoảng|tầm|around)\s*\d+',
        ],
        'order_status': [
            r'\b(đơn hàng|order|đơn)\b.*\b(đâu|sao|thế nào|status)\b',
            r'\b(theo dõi|tracking|giao hàng)\b',
            r'\b(khi nào|bao giờ)\b.*\b(nhận|giao)\b',
        ],
        'return_policy': [
            r'\b(đổi|trả|hoàn)\b.*\b(hàng|tiền|sản phẩm)\b',
            r'\b(chính sách|policy)\b.*\b(đổi|trả)\b',
        ],
        'payment': [
            r'\b(thanh toán|payment|trả tiền)\b',
            r'\b(COD|momo|vnpay|thẻ)\b',
        ],
        'shipping': [
            r'\b(ship|giao hàng|vận chuyển|delivery)\b',
            r'\b(phí ship|phí giao|shipping fee)\b',
        ],
        'support': [
            r'\b(hỗ trợ|support|giúp|help)\b',
            r'\b(liên hệ|contact|hotline)\b',
        ],
        'goodbye': [
            r'\b(tạm biệt|bye|goodbye|cảm ơn|thank)\b',
        ],
    }

    @classmethod
    def classify(cls, text):
        """Phân loại intent từ text với ưu tiên product_search"""
        text_lower = text.lower()

        # Check for product keywords first - high priority for product search
        for keyword in cls.PRODUCT_KEYWORDS:
            if keyword in text_lower:
                # If contains product keyword + price or action word, it's product search
                if re.search(r'\d+\s*(triệu|tr|k|nghìn)?', text_lower) or \
                   re.search(r'(tư vấn|gợi ý|tìm|mua|có|bán|cần|muốn)', text_lower):
                    return 'product_search'

        # Standard pattern matching
        for intent, patterns in cls.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent

        # If contains any product keyword but no other intent matched
        for keyword in cls.PRODUCT_KEYWORDS:
            if keyword in text_lower:
                return 'product_search'

        return 'general'


class ChatbotEngine:
    """
    AI Chatbot Engine với:
    1. Intent Classification
    2. FAQ Matching
    3. RAG (Retrieval-Augmented Generation)
    4. LLM Response Generation (Ollama)
    5. Context Management
    """

    SYSTEM_PROMPT = """Bạn là trợ lý AI của cửa hàng thương mại điện tử.
Nhiệm vụ của bạn là hỗ trợ khách hàng với:
- Tìm kiếm và tư vấn sản phẩm
- Theo dõi đơn hàng
- Giải đáp thắc mắc về chính sách
- Hỗ trợ thanh toán và giao hàng

Hãy trả lời ngắn gọn, thân thiện và hữu ích bằng tiếng Việt.
Khi tư vấn sản phẩm, hãy đưa ra gợi ý cụ thể với giá và lý do phù hợp.
Nếu không biết câu trả lời, hãy hướng dẫn khách hàng liên hệ hotline: 1900-xxxx"""

    INTENT_RESPONSES = {
        'greeting': [
            "Xin chào! Tôi là trợ lý AI của shop. Tôi có thể giúp gì cho bạn?",
            "Chào bạn! Bạn cần tư vấn về sản phẩm hay đơn hàng?",
        ],
        'goodbye': [
            "Cảm ơn bạn đã liên hệ! Chúc bạn một ngày tốt lành!",
            "Tạm biệt! Hẹn gặp lại bạn!",
        ],
        'return_policy': [
            "Chính sách đổi trả của shop:\n- Đổi trả miễn phí trong 7 ngày\n- Sản phẩm còn nguyên tem mác\n- Hoàn tiền trong 3-5 ngày làm việc",
        ],
        'payment': [
            "Shop hỗ trợ các hình thức thanh toán:\n- COD (thanh toán khi nhận hàng)\n- MoMo\n- VNPay\n- Chuyển khoản ngân hàng",
        ],
        'shipping': [
            "Thông tin giao hàng:\n- Nội thành: 1-2 ngày\n- Ngoại thành: 3-5 ngày\n- Miễn phí ship đơn từ 500k",
        ],
        'support': [
            "Bạn có thể liên hệ với chúng tôi qua:\n- Hotline: 1900-xxxx (8h-22h)\n- Email: support@shop.vn\n- Chat trực tiếp tại đây",
        ],
    }

    # Intents that should use RAG for product recommendations
    RAG_INTENTS = ['product_search', 'general']

    def __init__(self):
        self.ollama_host = settings.OLLAMA_HOST
        self.ollama_model = settings.OLLAMA_MODEL
        self.classifier = IntentClassifier()
        self.rag = RAGPipeline(self.ollama_host, self.ollama_model)

    async def chat(self, message, conversation_id=None, session_id=None, user_id=None):
        """
        Xử lý tin nhắn từ người dùng
        """
        from .models import Conversation, Message

        # Get or create conversation
        conversation = self._get_or_create_conversation(
            conversation_id, session_id, user_id
        )

        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=message
        )

        # Classify intent
        intent = self.classifier.classify(message)

        # Check FAQ first
        faq_answer = self._check_faq(message)
        if faq_answer:
            response = faq_answer
        elif intent in self.INTENT_RESPONSES:
            # Use predefined response
            import random
            response = random.choice(self.INTENT_RESPONSES[intent])
        else:
            # Use LLM for complex queries
            response = await self._generate_llm_response(message, conversation)

        # Save assistant message
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response,
            metadata={'intent': intent}
        )

        return {
            'conversation_id': str(conversation.id),
            'response': response,
            'intent': intent,
            'message_id': str(assistant_message.id)
        }

    def chat_sync(self, message, conversation_id=None, session_id=None, user_id=None):
        """Synchronous version of chat with RAG + Knowledge Graph + Intent/Entity extraction"""
        from .models import Conversation, Message

        # Get or create conversation
        conversation = self._get_or_create_conversation(
            conversation_id, session_id, user_id
        )

        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=message
        )

        # Classify intent
        intent = self.classifier.classify(message)

        # Extract entities using QueryParser
        entities = query_parser.parse(message)

        # Check FAQ first
        faq_answer = self._check_faq(message)
        products = []
        kg_context = {}
        used_kg = False
        extracted_entities = None

        if faq_answer:
            response = faq_answer
        elif intent in self.INTENT_RESPONSES:
            import random
            response = random.choice(self.INTENT_RESPONSES[intent])
        elif intent in self.RAG_INTENTS:
            # Check if we need clarification
            clarification = kg_client.ask_for_clarification(entities)
            if clarification and entities.confidence < 0.3:
                response = clarification
                extracted_entities = {
                    'category': entities.category,
                    'price_max': entities.price_max,
                    'price_min': entities.price_min,
                    'brand': entities.brand,
                    'confidence': entities.confidence,
                    'needs_clarification': True
                }
            else:
                # Use RAG + Knowledge Graph with structured entities
                result = self.rag.retrieve(message, k=5, user_id=user_id)

                # Handle tuple return (products, entities) from new retrieve method
                if isinstance(result, tuple):
                    products, retrieved_entities = result
                else:
                    products = result
                    retrieved_entities = entities

                extracted_entities = {
                    'category': retrieved_entities.category,
                    'price_max': retrieved_entities.price_max,
                    'price_min': retrieved_entities.price_min,
                    'brand': retrieved_entities.brand,
                    'confidence': retrieved_entities.confidence,
                    'needs_clarification': False
                }

                if products:
                    # Get additional KG context
                    top_product_id = products[0].get('product_id')
                    if top_product_id:
                        kg_context['bought_together'] = kg_client.get_frequently_bought_together(
                            top_product_id, n=3
                        )
                        used_kg = True

                    # Generate response with entity context
                    response = self._generate_structured_response(
                        message, products, entities, kg_context
                    )
                else:
                    # No products found
                    response = self._no_results_response(entities)
        else:
            # Use LLM for other queries
            response = self._generate_llm_response_sync(message, conversation)

        # Save assistant message
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response,
            metadata={
                'intent': intent,
                'products': [p['product_id'] for p in products] if products else [],
                'used_rag': intent in self.RAG_INTENTS and bool(products),
                'used_knowledge_graph': used_kg,
                'kg_context': kg_context if kg_context else None,
                'extracted_entities': extracted_entities
            }
        )

        # Update conversation
        conversation.save()

        return {
            'conversation_id': str(conversation.id),
            'response': response,
            'intent': intent,
            'message_id': str(assistant_message.id),
            'products': products if products else None,
            'used_rag': intent in self.RAG_INTENTS and bool(products),
            'used_knowledge_graph': used_kg,
            'bought_together': kg_context.get('bought_together') if kg_context else None,
            'extracted_entities': extracted_entities
        }

    def _generate_structured_response(self, query, products, entities: ExtractedEntities, kg_context=None):
        """Generate response using extracted entities for better context"""
        # Build entity context
        entity_context = []
        if entities.category:
            entity_context.append(f"Loại: {entities.category}")
        if entities.price_max:
            entity_context.append(f"Giá tối đa: {entities.price_max:,}đ")
        if entities.price_min:
            entity_context.append(f"Giá tối thiểu: {entities.price_min:,}đ")
        if entities.brand:
            entity_context.append(f"Thương hiệu: {entities.brand}")

        # Use RAG pipeline with enhanced context
        return self.rag.generate_augmented_response(query, products, kg_context)

    def _no_results_response(self, entities: ExtractedEntities):
        """Generate response when no products found"""
        response = "Xin lỗi, tôi không tìm thấy sản phẩm phù hợp"

        details = []
        if entities.category:
            details.append(f"loại **{entities.category}**")
        if entities.price_max:
            details.append(f"giá dưới **{entities.price_max:,}đ**")
        if entities.price_min:
            details.append(f"giá từ **{entities.price_min:,}đ**")
        if entities.brand:
            details.append(f"thương hiệu **{entities.brand}**")

        if details:
            response += f" với {', '.join(details)}"

        response += ".\n\nBạn có thể:\n"
        response += "- Thử tìm với mức giá khác\n"
        response += "- Chọn loại sản phẩm khác\n"
        response += "- Mô tả chi tiết hơn về sản phẩm bạn cần"

        return response

    def _get_or_create_conversation(self, conversation_id, session_id, user_id):
        """Get existing or create new conversation"""
        from .models import Conversation
        import uuid as uuid_module

        if conversation_id:
            try:
                return Conversation.objects.get(id=conversation_id)
            except Conversation.DoesNotExist:
                pass

        if not session_id:
            session_id = str(uuid_module.uuid4())

        conversation, created = Conversation.objects.get_or_create(
            session_id=session_id,
            defaults={'user_id': user_id}
        )
        return conversation

    def _check_faq(self, message):
        """Tìm câu trả lời từ FAQ"""
        from .models import FAQ

        cache_key = f"faq:{hash(message.lower())}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Simple keyword matching
        keywords = message.lower().split()

        faqs = FAQ.objects.filter(is_active=True)
        for faq in faqs:
            faq_keywords = faq.keywords.lower().split()
            matches = sum(1 for k in keywords if k in faq_keywords or k in faq.question.lower())
            if matches >= 2:
                # Update view count
                faq.view_count += 1
                faq.save(update_fields=['view_count'])
                cache.set(cache_key, faq.answer, timeout=300)
                return faq.answer

        return None

    def _generate_llm_response_sync(self, message, conversation):
        """Generate response using Ollama LLM (sync)"""
        # Check cache
        cache_key = f"llm_response:{hash(message)}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            # Build messages context - limit to last 5 messages for speed
            messages = self._build_context(conversation, message)
            if len(messages) > 6:  # system + 5 messages
                messages = [messages[0]] + messages[-5:]

            response = httpx.post(
                f"{self.ollama_host}/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "num_predict": 200,
                        "temperature": 0.7
                    }
                },
                timeout=90.0
            )

            if response.status_code == 200:
                data = response.json()
                result = data.get('message', {}).get('content', self._fallback_response())
                cache.set(cache_key, result, timeout=300)
                return result
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return self._fallback_response()

        except httpx.TimeoutException:
            logger.warning("LLM response timeout")
            return self._fallback_response()
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return self._fallback_response()

    async def _generate_llm_response(self, message, conversation):
        """Generate response using Ollama LLM (async)"""
        # Check cache
        cache_key = f"llm_response:{hash(message)}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            messages = self._build_context(conversation, message)
            if len(messages) > 6:
                messages = [messages[0]] + messages[-5:]

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_host}/api/chat",
                    json={
                        "model": self.ollama_model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "num_predict": 200,
                            "temperature": 0.7
                        }
                    },
                    timeout=90.0
                )

                if response.status_code == 200:
                    data = response.json()
                    result = data.get('message', {}).get('content', self._fallback_response())
                    cache.set(cache_key, result, timeout=300)
                    return result
                else:
                    return self._fallback_response()

        except httpx.TimeoutException:
            logger.warning("LLM response timeout")
            return self._fallback_response()
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return self._fallback_response()

    def _build_context(self, conversation, current_message):
        """Build conversation context for LLM"""
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        # Get recent messages
        recent_messages = conversation.messages.order_by('-created_at')[:10]
        for msg in reversed(list(recent_messages)):
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Add current message
        messages.append({"role": "user", "content": current_message})

        return messages

    def _fallback_response(self):
        """Response khi LLM không available"""
        return "Xin lỗi, tôi không thể xử lý yêu cầu lúc này. Vui lòng thử lại sau hoặc liên hệ hotline: 1900-xxxx để được hỗ trợ."

    def search_products(self, query):
        """Search products via AI Search service"""
        try:
            response = httpx.post(
                f"{settings.PRODUCT_SERVICE_URL}/../search/",
                json={"query": query},
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json().get('results', [])
        except Exception as e:
            logger.error(f"Product search error: {e}")
        return []


# Singleton instance
chatbot_engine = ChatbotEngine()
