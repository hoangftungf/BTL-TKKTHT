"""
RAG + Knowledge Graph Engine
Kết hợp Vector Search (FAISS) với Knowledge Graph (Neo4j) cho chatbot
"""

import os
import logging
import httpx
from django.conf import settings
from django.core.cache import cache

from .rag_engine import RAGEngine
from .knowledge_graph import knowledge_graph

logger = logging.getLogger(__name__)


class RAGKnowledgeGraphEngine:
    """
    RAG Engine tích hợp Knowledge Graph

    Flow:
    1. User query → Intent classification
    2. Vector search (FAISS) → Semantic similar products
    3. Graph query (Neo4j) → Relationship-based recommendations
    4. Merge & rank results
    5. Build context với graph relationships
    6. LLM generate response

    Ưu điểm so với RAG thuần:
    - Có thêm thông tin quan hệ (users who bought also bought...)
    - Recommendations dựa trên collaborative filtering từ graph
    - Context phong phú hơn với category, brand relationships
    """

    def __init__(self):
        self.rag = RAGEngine()
        self.kg = knowledge_graph
        self.ollama_host = getattr(settings, 'OLLAMA_HOST',
                                   os.environ.get('OLLAMA_HOST', 'http://localhost:11434'))
        self.ollama_model = getattr(settings, 'OLLAMA_MODEL',
                                    os.environ.get('OLLAMA_MODEL', 'llama3.2'))

    def query(self, user_query, user_id=None, n=10):
        """
        Main query method - kết hợp RAG + Knowledge Graph

        Args:
            user_query: Câu hỏi của user
            user_id: ID user (nếu có) để personalize
            n: Số kết quả trả về

        Returns:
            dict với products, response, và metadata
        """
        cache_key = f"rag_kg:{hash(user_query)}:{user_id}:{n}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # 1. Vector search (semantic similarity)
        vector_results = self.rag.retrieve(user_query, k=n)
        logger.info(f"Vector search returned {len(vector_results)} results")

        # 2. Knowledge Graph search
        graph_results = self._query_knowledge_graph(user_query, user_id, n)
        logger.info(f"Graph search returned {len(graph_results)} results")

        # 3. Merge and rank results
        merged_results = self._merge_results(vector_results, graph_results, n)

        # 4. Get additional context from graph
        graph_context = self._get_graph_context(merged_results, user_id)

        # 5. Generate response with LLM
        response = self._generate_response(user_query, merged_results, graph_context)

        result = {
            'query': user_query,
            'products': merged_results,
            'response': response,
            'graph_context': graph_context,
            'sources': {
                'vector_count': len(vector_results),
                'graph_count': len(graph_results),
                'merged_count': len(merged_results)
            }
        }

        cache.set(cache_key, result, timeout=300)
        return result

    def _query_knowledge_graph(self, query, user_id=None, n=10):
        """Query Knowledge Graph dựa trên câu hỏi"""
        results = []

        # Extract potential product/category/brand names from query
        query_lower = query.lower()

        # 1. Nếu có user_id, lấy personalized recommendations
        if user_id:
            user_recs = self.kg.get_user_recommendations(str(user_id), n=n//2)
            for rec in user_recs:
                rec['source'] = 'graph_collaborative'
            results.extend(user_recs)

        # 2. Query products by category nếu query mention category
        category_products = self._search_by_category(query_lower, n//2)
        results.extend(category_products)

        # 3. Query frequently bought together nếu có product context
        # (sẽ được xử lý trong get_graph_context)

        return results

    def _search_by_category(self, query, n=5):
        """Tìm products theo category từ query"""
        session = self.kg._get_session()
        if session is None:
            return []

        results = []
        try:
            with session:
                # Tìm categories match với query
                result = session.run("""
                    MATCH (c:Category)
                    WHERE toLower(c.name) CONTAINS $query
                    MATCH (p:Product)-[:BELONGS_TO]->(c)
                    OPTIONAL MATCH (u:User)-[r:PURCHASED]->(p)
                    WITH p, c, COUNT(r) AS purchases
                    RETURN p.id AS product_id, p.name AS name, p.price AS price,
                           c.name AS category, purchases
                    ORDER BY purchases DESC
                    LIMIT $limit
                """, query=query, limit=n)

                for record in result:
                    results.append({
                        'product_id': record['product_id'],
                        'name': record['name'],
                        'score': float(record['purchases']) / 10,  # Normalize
                        'data': {
                            'name': record['name'],
                            'price': record['price'],
                            'category': record['category']
                        },
                        'reason': f"Thuộc danh mục {record['category']}",
                        'source': 'graph_category'
                    })
        except Exception as e:
            logger.error(f"Error searching by category: {e}")

        return results

    def _merge_results(self, vector_results, graph_results, n):
        """
        Merge kết quả từ vector search và graph search

        Strategy:
        - Weighted scoring: vector (0.6) + graph (0.4)
        - Boost nếu xuất hiện ở cả 2 nguồn
        """
        product_scores = {}

        # Process vector results
        for r in vector_results:
            pid = r.get('product_id')
            if pid:
                product_scores[pid] = {
                    'product_id': pid,
                    'vector_score': r.get('score', 0) * 0.6,
                    'graph_score': 0,
                    'data': r.get('data', {}),
                    'reasons': [r.get('reason', 'Semantic match')]
                }

        # Process graph results
        for r in graph_results:
            pid = r.get('product_id')
            if pid:
                if pid in product_scores:
                    # Boost for appearing in both
                    product_scores[pid]['graph_score'] = r.get('score', 0) * 0.4
                    product_scores[pid]['reasons'].append(r.get('reason', 'Graph match'))
                else:
                    product_scores[pid] = {
                        'product_id': pid,
                        'vector_score': 0,
                        'graph_score': r.get('score', 0) * 0.4,
                        'data': r.get('data', {}),
                        'reasons': [r.get('reason', 'Graph match')]
                    }

        # Calculate final scores and sort
        results = []
        for pid, data in product_scores.items():
            total_score = data['vector_score'] + data['graph_score']
            # Boost if in both sources
            if data['vector_score'] > 0 and data['graph_score'] > 0:
                total_score *= 1.2

            results.append({
                'product_id': pid,
                'score': total_score,
                'data': data['data'],
                'reason': ' | '.join(data['reasons'][:2])
            })

        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:n]

    def _get_graph_context(self, products, user_id=None):
        """
        Lấy context bổ sung từ Knowledge Graph

        Returns thông tin về:
        - Frequently bought together
        - Category insights
        - User behavior patterns
        """
        context = {
            'bought_together': [],
            'category_info': [],
            'user_preferences': []
        }

        if not products:
            return context

        session = self.kg._get_session()
        if session is None:
            return context

        try:
            with session:
                # 1. Frequently bought together cho top product
                if products:
                    top_product = products[0]['product_id']
                    bought_together = self.kg.get_frequently_bought_together(top_product, n=3)
                    context['bought_together'] = bought_together

                # 2. Category popularity
                result = session.run("""
                    MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
                    WHERE p.id IN $product_ids
                    MATCH (c)<-[:BELONGS_TO]-(other:Product)<-[r:PURCHASED]-(:User)
                    WITH c.name AS category, COUNT(DISTINCT r) AS total_purchases
                    RETURN category, total_purchases
                    ORDER BY total_purchases DESC
                    LIMIT 3
                """, product_ids=[p['product_id'] for p in products[:5]])

                for record in result:
                    context['category_info'].append({
                        'category': record['category'],
                        'popularity': record['total_purchases']
                    })

                # 3. User preferences nếu có user_id
                if user_id:
                    result = session.run("""
                        MATCH (u:User {id: $user_id})-[r]->(p:Product)-[:BELONGS_TO]->(c:Category)
                        WITH c.name AS category, COUNT(r) AS interactions
                        RETURN category, interactions
                        ORDER BY interactions DESC
                        LIMIT 3
                    """, user_id=str(user_id))

                    for record in result:
                        context['user_preferences'].append({
                            'category': record['category'],
                            'interest_score': record['interactions']
                        })

        except Exception as e:
            logger.error(f"Error getting graph context: {e}")

        return context

    def _generate_response(self, query, products, graph_context):
        """Generate response với LLM, sử dụng cả product info và graph context"""

        # Build product context
        product_lines = []
        for i, p in enumerate(products[:5], 1):
            data = p.get('data', {})
            line = f"{i}. {data.get('name', p.get('product_id', 'Unknown'))}"
            if data.get('price'):
                line += f" - {data['price']:,.0f}d"
            if data.get('category'):
                line += f" ({data['category']})"
            line += f" | {p.get('reason', '')}"
            product_lines.append(line)

        product_context = '\n'.join(product_lines)

        # Build graph context
        graph_info = []
        if graph_context.get('bought_together'):
            items = [b.get('name', b.get('product_id')) for b in graph_context['bought_together'][:2]]
            if items:
                graph_info.append(f"San pham thuong mua kem: {', '.join(items)}")

        if graph_context.get('category_info'):
            top_cat = graph_context['category_info'][0]
            graph_info.append(f"Danh muc pho bien: {top_cat['category']}")

        if graph_context.get('user_preferences'):
            prefs = [p['category'] for p in graph_context['user_preferences'][:2]]
            if prefs:
                graph_info.append(f"So thich cua ban: {', '.join(prefs)}")

        graph_context_str = '\n'.join(graph_info) if graph_info else "Khong co thong tin bo sung"

        # Build prompt
        prompt = f"""Ban la tro ly AI cua cua hang thuong mai dien tu.
Dua tren thong tin san pham va du lieu tu Knowledge Graph, hay tra loi cau hoi cua khach hang.

SAN PHAM PHU HOP:
{product_context}

THONG TIN BO SUNG TU KNOWLEDGE GRAPH:
{graph_context_str}

CAU HOI: {query}

Tra loi ngan gon, than thien. Goi y 2-3 san pham phu hop nhat voi ly do cu the.
Neu co san pham thuong mua kem, hay de xuat them."""

        try:
            response = httpx.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30.0
            )

            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                logger.error(f"LLM error: {response.status_code}")
                return self._fallback_response(products, graph_context)

        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return self._fallback_response(products, graph_context)

    def _fallback_response(self, products, graph_context):
        """Fallback response khi LLM không available"""
        if not products:
            return "Xin loi, toi khong tim thay san pham phu hop voi yeu cau cua ban."

        response = "Dua tren yeu cau cua ban, toi goi y:\n\n"
        for i, p in enumerate(products[:3], 1):
            data = p.get('data', {})
            response += f"{i}. **{data.get('name', 'San pham')}**"
            if data.get('price'):
                response += f" - {data['price']:,.0f}d"
            response += f"\n   Ly do: {p.get('reason', 'Phu hop voi yeu cau')}\n"

        if graph_context.get('bought_together'):
            response += "\nSan pham thuong mua kem:\n"
            for item in graph_context['bought_together'][:2]:
                response += f"- {item.get('name', item.get('product_id'))}\n"

        return response

    def get_product_insights(self, product_id):
        """Lấy insights về 1 product từ Knowledge Graph"""
        session = self.kg._get_session()
        if session is None:
            return {}

        insights = {}
        try:
            with session:
                # Basic info
                result = session.run("""
                    MATCH (p:Product {id: $product_id})
                    OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)
                    OPTIONAL MATCH (p)-[:MADE_BY]->(b:Brand)
                    OPTIONAL MATCH (u:User)-[r:PURCHASED]->(p)
                    RETURN p.name AS name, p.price AS price,
                           c.name AS category, b.name AS brand,
                           COUNT(r) AS purchase_count
                """, product_id=str(product_id))

                record = result.single()
                if record:
                    insights['product'] = {
                        'name': record['name'],
                        'price': record['price'],
                        'category': record['category'],
                        'brand': record['brand'],
                        'purchase_count': record['purchase_count']
                    }

                # Bought together
                insights['bought_together'] = self.kg.get_frequently_bought_together(product_id, n=5)

                # Similar products
                insights['similar'] = self.kg.get_similar_products(product_id, n=5)

        except Exception as e:
            logger.error(f"Error getting product insights: {e}")

        return insights

    def chat(self, message, user_id=None, conversation_history=None):
        """
        Chat method cho chatbot integration

        Args:
            message: Tin nhắn từ user
            user_id: ID user
            conversation_history: Lịch sử hội thoại

        Returns:
            dict với response và metadata
        """
        # Query RAG + KG
        result = self.query(message, user_id=user_id, n=5)

        return {
            'response': result['response'],
            'products': result['products'],
            'sources': result['sources'],
            'used_knowledge_graph': True
        }


# Singleton instance
rag_kg_engine = RAGKnowledgeGraphEngine()
