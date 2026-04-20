"""
Hybrid Recommendation Engine
Kết hợp LSTM + Knowledge Graph + RAG theo công thức:
final_score = w1 * lstm + w2 * graph + w3 * rag
"""

import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


class HybridRecommendationEngine:
    """
    Hybrid Recommendation Engine kết hợp 3 mô hình:
    1. LSTM: Dự đoán hành vi dựa trên sequence
    2. Knowledge Graph: Quan hệ sản phẩm và user
    3. RAG: Hiểu ngữ nghĩa từ mô tả

    Final Score = w1 * lstm_score + w2 * graph_score + w3 * rag_score
    """

    # Default weights
    DEFAULT_WEIGHTS = {
        'lstm': 0.35,
        'graph': 0.35,
        'rag': 0.30
    }

    def __init__(self, weights=None):
        self.weights = weights or self.DEFAULT_WEIGHTS

        # Lazy loading engines
        self._lstm_engine = None
        self._graph_engine = None
        self._rag_engine = None
        self._collab_engine = None

    @property
    def lstm_engine(self):
        if self._lstm_engine is None:
            from .lstm_model import lstm_engine
            self._lstm_engine = lstm_engine
        return self._lstm_engine

    @property
    def graph_engine(self):
        if self._graph_engine is None:
            from .knowledge_graph import knowledge_graph
            self._graph_engine = knowledge_graph
        return self._graph_engine

    @property
    def rag_engine(self):
        if self._rag_engine is None:
            from .rag_engine import rag_engine
            self._rag_engine = rag_engine
        return self._rag_engine

    @property
    def collab_engine(self):
        if self._collab_engine is None:
            from .engine import recommendation_engine
            self._collab_engine = recommendation_engine
        return self._collab_engine

    def get_recommendations(self, user_id=None, query=None, product_id=None, n=10):
        """
        Get hybrid recommendations

        Args:
            user_id: User ID for personalized recommendations
            query: Natural language query for RAG
            product_id: Product ID for similar product recommendations
            n: Number of results

        Returns:
            dict with combined recommendations and scores
        """
        cache_key = f"hybrid_rec:{user_id}:{query}:{product_id}:{n}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        all_scores = {}  # product_id -> {scores, reasons}

        # 1. LSTM predictions (if user_id provided)
        if user_id:
            lstm_recs = self._get_lstm_recommendations(user_id, n * 2)
            for rec in lstm_recs:
                pid = rec['product_id']
                if pid not in all_scores:
                    all_scores[pid] = {'lstm': 0, 'graph': 0, 'rag': 0, 'collab': 0, 'reasons': []}
                all_scores[pid]['lstm'] = rec.get('score', 0)
                all_scores[pid]['reasons'].append(rec.get('reason', 'LSTM prediction'))

        # 2. Knowledge Graph recommendations
        if user_id:
            graph_recs = self._get_graph_recommendations(user_id, n * 2)
            for rec in graph_recs:
                pid = rec['product_id']
                if pid not in all_scores:
                    all_scores[pid] = {'lstm': 0, 'graph': 0, 'rag': 0, 'collab': 0, 'reasons': []}
                all_scores[pid]['graph'] = rec.get('score', 0)
                all_scores[pid]['reasons'].append(rec.get('reason', 'Graph relation'))

        # 3. RAG recommendations (if query provided)
        if query:
            rag_recs = self._get_rag_recommendations(query, n * 2)
            for rec in rag_recs:
                pid = rec['product_id']
                if pid not in all_scores:
                    all_scores[pid] = {'lstm': 0, 'graph': 0, 'rag': 0, 'collab': 0, 'reasons': []}
                all_scores[pid]['rag'] = rec.get('score', 0)
                all_scores[pid]['reasons'].append(rec.get('reason', 'Semantic match'))

        # 4. Similar products (if product_id provided)
        if product_id:
            similar_recs = self._get_similar_products(product_id, n * 2)
            for rec in similar_recs:
                pid = rec['product_id']
                if pid not in all_scores:
                    all_scores[pid] = {'lstm': 0, 'graph': 0, 'rag': 0, 'collab': 0, 'reasons': []}
                # Distribute similar scores across models
                all_scores[pid]['graph'] = max(all_scores[pid]['graph'], rec.get('score', 0) * 0.5)
                all_scores[pid]['rag'] = max(all_scores[pid]['rag'], rec.get('score', 0) * 0.5)
                all_scores[pid]['reasons'].append(rec.get('reason', 'Similar product'))

        # 5. Collaborative filtering (fallback for user)
        if user_id:
            collab_recs = self._get_collab_recommendations(user_id, n * 2)
            for rec in collab_recs:
                pid = rec['product_id']
                if pid not in all_scores:
                    all_scores[pid] = {'lstm': 0, 'graph': 0, 'rag': 0, 'collab': 0, 'reasons': []}
                all_scores[pid]['collab'] = rec.get('score', 0)
                if not all_scores[pid]['reasons']:
                    all_scores[pid]['reasons'].append(rec.get('reason', 'Collaborative filtering'))

        # Calculate hybrid scores
        results = []
        for pid, scores in all_scores.items():
            # Normalize scores
            lstm_score = self._normalize_score(scores['lstm'])
            graph_score = self._normalize_score(scores['graph'])
            rag_score = self._normalize_score(scores['rag'])
            collab_score = self._normalize_score(scores['collab'])

            # Apply weights
            hybrid_score = (
                self.weights['lstm'] * lstm_score +
                self.weights['graph'] * graph_score +
                self.weights['rag'] * rag_score +
                0.2 * collab_score  # Bonus for collaborative
            )

            # Deduplicate and combine reasons
            unique_reasons = list(dict.fromkeys(scores['reasons']))

            results.append({
                'product_id': pid,
                'score': round(hybrid_score, 4),
                'scores_detail': {
                    'lstm': round(lstm_score, 4),
                    'graph': round(graph_score, 4),
                    'rag': round(rag_score, 4),
                    'collab': round(collab_score, 4)
                },
                'reasons': unique_reasons[:3],  # Top 3 reasons
                'primary_reason': unique_reasons[0] if unique_reasons else 'Hybrid recommendation'
            })

        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:n]

        response = {
            'user_id': str(user_id) if user_id else None,
            'query': query,
            'product_id': str(product_id) if product_id else None,
            'recommendations': results,
            'weights': self.weights,
            'total_candidates': len(all_scores)
        }

        cache.set(cache_key, response, timeout=600)
        return response

    def _normalize_score(self, score, min_val=0, max_val=1):
        """Normalize score to 0-1 range"""
        if score is None:
            return 0
        score = float(score)
        if score <= 0:
            return 0
        if score >= max_val:
            return 1
        return min(1, max(0, score))

    def _get_lstm_recommendations(self, user_id, n):
        """Get LSTM predictions"""
        try:
            return self.lstm_engine.predict(user_id, n=n)
        except Exception as e:
            logger.warning(f"LSTM engine error: {e}")
            return []

    def _get_graph_recommendations(self, user_id, n):
        """Get Knowledge Graph recommendations"""
        try:
            return self.graph_engine.get_user_recommendations(user_id, n=n)
        except Exception as e:
            logger.warning(f"Graph engine error: {e}")
            return []

    def _get_rag_recommendations(self, query, n):
        """Get RAG recommendations"""
        try:
            return self.rag_engine.retrieve(query, k=n)
        except Exception as e:
            logger.warning(f"RAG engine error: {e}")
            return []

    def _get_similar_products(self, product_id, n):
        """Get similar products from multiple sources"""
        results = []

        # From Graph
        try:
            graph_similar = self.graph_engine.get_similar_products(product_id, n=n // 2)
            results.extend(graph_similar)
        except Exception as e:
            logger.warning(f"Graph similar error: {e}")

        # From RAG embeddings
        try:
            rag_similar = self.rag_engine.get_similar_by_embedding(product_id, n=n // 2)
            results.extend(rag_similar)
        except Exception as e:
            logger.warning(f"RAG similar error: {e}")

        # From Collaborative
        try:
            collab_similar = self.collab_engine.get_similar_products(product_id, n=n // 2)
            results.extend(collab_similar)
        except Exception as e:
            logger.warning(f"Collab similar error: {e}")

        return results

    def _get_collab_recommendations(self, user_id, n):
        """Get collaborative filtering recommendations"""
        try:
            return self.collab_engine.get_user_recommendations(user_id, n=n)
        except Exception as e:
            logger.warning(f"Collab engine error: {e}")
            return []

    def train_all_models(self):
        """Train tất cả các models"""
        results = {}

        # Train LSTM
        logger.info("Training LSTM model...")
        try:
            lstm_result = self.lstm_engine.train()
            results['lstm'] = lstm_result
        except Exception as e:
            logger.error(f"LSTM training error: {e}")
            results['lstm'] = {'status': 'error', 'message': str(e)}

        # Train Collaborative Filtering
        logger.info("Training Collaborative Filtering model...")
        try:
            collab_result = self.collab_engine.train_model()
            results['collaborative'] = collab_result
        except Exception as e:
            logger.error(f"Collab training error: {e}")
            results['collaborative'] = {'status': 'error', 'message': str(e)}

        # Index products for RAG
        logger.info("Indexing products for RAG...")
        try:
            rag_result = self.rag_engine.index_products()
            results['rag'] = rag_result
        except Exception as e:
            logger.error(f"RAG indexing error: {e}")
            results['rag'] = {'status': 'error', 'message': str(e)}

        # Sync Knowledge Graph
        logger.info("Syncing Knowledge Graph...")
        try:
            graph_result = self.graph_engine.sync_from_database()
            results['graph'] = graph_result
        except Exception as e:
            logger.error(f"Graph sync error: {e}")
            results['graph'] = {'status': 'error', 'message': str(e)}

        return results

    def get_chatbot_response(self, query, user_id=None):
        """
        Generate chatbot response using RAG

        Args:
            query: User question
            user_id: Optional user ID for personalization

        Returns:
            dict with response and product recommendations
        """
        # Get RAG recommendations
        rag_result = self.rag_engine.recommend(query, n=5)

        # If user provided, also get personalized recommendations
        personalized = []
        if user_id:
            hybrid_result = self.get_recommendations(user_id=user_id, query=query, n=3)
            personalized = hybrid_result.get('recommendations', [])

        return {
            'query': query,
            'response': rag_result.get('response', ''),
            'products': rag_result.get('products', []),
            'personalized': personalized,
            'source': 'hybrid_rag'
        }

    def set_weights(self, lstm=None, graph=None, rag=None):
        """Update model weights"""
        if lstm is not None:
            self.weights['lstm'] = lstm
        if graph is not None:
            self.weights['graph'] = graph
        if rag is not None:
            self.weights['rag'] = rag

        # Normalize weights
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}

        return self.weights


# Singleton instance
hybrid_engine = HybridRecommendationEngine()
