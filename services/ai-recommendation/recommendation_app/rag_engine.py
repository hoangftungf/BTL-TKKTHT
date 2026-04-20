"""
RAG (Retrieval-Augmented Generation) Engine
Sử dụng FAISS cho Vector Search và LLM cho response generation
"""

import os
import logging
import json
import numpy as np
import httpx
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """
    Text Embedding Model

    Hỗ trợ nhiều backends:
    - sentence-transformers (local)
    - Ollama embeddings
    - Simple TF-IDF fallback
    """

    def __init__(self):
        self.model = None
        self.model_type = None
        self._initialize()

    def _initialize(self):
        """Initialize embedding model"""
        # Try sentence-transformers first
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self.model_type = 'sentence-transformers'
            logger.info("Using sentence-transformers for embeddings")
            return
        except ImportError:
            logger.info("sentence-transformers not available")

        # Try Ollama embeddings
        ollama_host = getattr(settings, 'OLLAMA_HOST', os.environ.get('OLLAMA_HOST', 'http://localhost:11434'))
        try:
            response = httpx.get(f"{ollama_host}/api/tags", timeout=5.0)
            if response.status_code == 200:
                self.model = ollama_host
                self.model_type = 'ollama'
                logger.info("Using Ollama for embeddings")
                return
        except Exception:
            pass

        # Fallback to TF-IDF
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.model = TfidfVectorizer(max_features=384)
        self.model_type = 'tfidf'
        logger.info("Using TF-IDF fallback for embeddings")

    def embed(self, texts):
        """
        Generate embeddings for texts

        Args:
            texts: list of strings

        Returns:
            numpy array of shape (n_texts, embedding_dim)
        """
        if not texts:
            return np.array([])

        if isinstance(texts, str):
            texts = [texts]

        if self.model_type == 'sentence-transformers':
            return self.model.encode(texts, convert_to_numpy=True)

        elif self.model_type == 'ollama':
            embeddings = []
            for text in texts:
                try:
                    response = httpx.post(
                        f"{self.model}/api/embeddings",
                        json={"model": "nomic-embed-text", "prompt": text},
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        embedding = response.json().get('embedding', [])
                        embeddings.append(embedding)
                    else:
                        # Fallback to zero vector
                        embeddings.append([0.0] * 384)
                except Exception as e:
                    logger.error(f"Ollama embedding error: {e}")
                    embeddings.append([0.0] * 384)
            return np.array(embeddings)

        else:  # TF-IDF
            try:
                if hasattr(self.model, 'vocabulary_') and self.model.vocabulary_:
                    return self.model.transform(texts).toarray()
                else:
                    return self.model.fit_transform(texts).toarray()
            except Exception as e:
                logger.error(f"TF-IDF error: {e}")
                return np.zeros((len(texts), 384))

    @property
    def embedding_dim(self):
        """Get embedding dimension"""
        if self.model_type == 'sentence-transformers':
            return self.model.get_sentence_embedding_dimension()
        elif self.model_type == 'ollama':
            return 768  # nomic-embed-text dimension
        else:
            return 384  # TF-IDF max_features


class FAISSIndex:
    """
    FAISS Vector Index cho product embeddings
    """

    def __init__(self, embedding_dim=384):
        self.embedding_dim = embedding_dim
        self.index = None
        self.product_ids = []
        self.product_data = {}
        self._initialize()

    def _initialize(self):
        """Initialize FAISS index"""
        try:
            import faiss
            # Use IndexFlatIP for inner product (cosine similarity after normalization)
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            logger.info(f"FAISS index initialized with dim={self.embedding_dim}")
        except ImportError:
            logger.warning("FAISS not available, using numpy fallback")
            self.index = None

    def add(self, product_id, embedding, product_data=None):
        """Add product to index"""
        if embedding is None or len(embedding) == 0:
            return False

        embedding = np.array(embedding).astype('float32')

        # Normalize for cosine similarity
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        if len(embedding.shape) == 1:
            embedding = embedding.reshape(1, -1)

        if self.index is not None:
            import faiss
            self.index.add(embedding)
        else:
            # Numpy fallback
            if not hasattr(self, '_embeddings'):
                self._embeddings = []
            self._embeddings.append(embedding[0])

        self.product_ids.append(str(product_id))
        if product_data:
            self.product_data[str(product_id)] = product_data

        return True

    def search(self, query_embedding, k=10):
        """
        Search for similar products

        Args:
            query_embedding: query vector
            k: number of results

        Returns:
            list of (product_id, score, product_data)
        """
        if len(self.product_ids) == 0:
            return []

        query_embedding = np.array(query_embedding).astype('float32')

        # Normalize
        norm = np.linalg.norm(query_embedding)
        if norm > 0:
            query_embedding = query_embedding / norm

        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)

        if self.index is not None:
            # FAISS search
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
            # Numpy fallback
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

    def save(self, path):
        """Save index to file"""
        if self.index is not None:
            import faiss
            faiss.write_index(self.index, f"{path}.index")

        # Save metadata
        with open(f"{path}.meta", 'w') as f:
            json.dump({
                'product_ids': self.product_ids,
                'product_data': self.product_data,
                'embedding_dim': self.embedding_dim
            }, f)

        logger.info(f"FAISS index saved to {path}")

    def load(self, path):
        """Load index from file"""
        try:
            if os.path.exists(f"{path}.index"):
                import faiss
                self.index = faiss.read_index(f"{path}.index")

            if os.path.exists(f"{path}.meta"):
                with open(f"{path}.meta", 'r') as f:
                    meta = json.load(f)
                    self.product_ids = meta['product_ids']
                    self.product_data = meta['product_data']
                    self.embedding_dim = meta['embedding_dim']

            logger.info(f"FAISS index loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            return False


class RAGEngine:
    """
    RAG Engine kết hợp:
    1. Retrieval: FAISS vector search
    2. Augmentation: Context building
    3. Generation: LLM response
    """

    def __init__(self):
        self.embedding_model = EmbeddingModel()
        self.index = FAISSIndex(embedding_dim=self.embedding_model.embedding_dim)
        self.ollama_host = getattr(settings, 'OLLAMA_HOST', os.environ.get('OLLAMA_HOST', 'http://localhost:11434'))
        self.ollama_model = getattr(settings, 'OLLAMA_MODEL', os.environ.get('OLLAMA_MODEL', 'llama3.2'))

        # Try to load existing index
        index_path = getattr(settings, 'MODEL_DIR', '.') / 'faiss_products' if hasattr(settings, 'MODEL_DIR') else 'faiss_products'
        if os.path.exists(f"{index_path}.meta"):
            self.index.load(str(index_path))

    def index_products(self):
        """Index tất cả products vào FAISS"""
        logger.info("Indexing products to FAISS...")

        # Fetch products from product service
        product_service_url = getattr(settings, 'PRODUCT_SERVICE_URL', 'http://localhost:8003')

        try:
            response = httpx.get(
                f"{product_service_url}/api/products/?page_size=1000",
                timeout=30.0
            )

            if response.status_code != 200:
                logger.error(f"Failed to fetch products: {response.status_code}")
                return {'status': 'error', 'message': 'Failed to fetch products'}

            products = response.json().get('results', [])

        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return {'status': 'error', 'message': str(e)}

        if not products:
            return {'status': 'no_products'}

        # Reset index
        self.index = FAISSIndex(embedding_dim=self.embedding_model.embedding_dim)

        # Build text representations
        texts = []
        for p in products:
            text = self._build_product_text(p)
            texts.append(text)

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} products...")
        embeddings = self.embedding_model.embed(texts)

        # Add to index
        for i, (p, embedding) in enumerate(zip(products, embeddings)):
            self.index.add(
                product_id=p['id'],
                embedding=embedding,
                product_data={
                    'name': p.get('name', ''),
                    'description': p.get('description', ''),
                    'price': p.get('price'),
                    'category': p.get('category', {}).get('name') if p.get('category') else None,
                    'brand': p.get('brand', '')
                }
            )

        # Save index
        index_path = getattr(settings, 'MODEL_DIR', '.') / 'faiss_products' if hasattr(settings, 'MODEL_DIR') else 'faiss_products'
        self.index.save(str(index_path))

        logger.info(f"Indexed {len(products)} products")
        return {
            'status': 'success',
            'indexed_count': len(products)
        }

    def _build_product_text(self, product):
        """Build text representation for product"""
        parts = [
            product.get('name', ''),
            product.get('description', ''),
            product.get('brand', ''),
        ]

        if product.get('category'):
            if isinstance(product['category'], dict):
                parts.append(product['category'].get('name', ''))
            else:
                parts.append(str(product['category']))

        # Add attributes if available
        if product.get('attributes'):
            for attr in product['attributes']:
                parts.append(f"{attr.get('name', '')}: {attr.get('value', '')}")

        return ' '.join(filter(None, parts))

    def retrieve(self, query, k=10):
        """
        Retrieve relevant products for query

        Args:
            query: search query string
            k: number of results

        Returns:
            list of product results with scores
        """
        cache_key = f"rag_retrieve:{hash(query)}:{k}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Generate query embedding
        query_embedding = self.embedding_model.embed([query])[0]

        # Search FAISS
        results = self.index.search(query_embedding, k=k)

        # Add reason
        for r in results:
            r['reason'] = 'Phù hợp ngữ nghĩa (RAG)'

        cache.set(cache_key, results, timeout=300)
        return results

    def generate_response(self, query, context_products, max_products=5):
        """
        Generate natural language response using LLM

        Args:
            query: user query
            context_products: list of relevant products
            max_products: max products to include in context

        Returns:
            Generated response string
        """
        # Build context
        context = self._build_context(context_products[:max_products])

        # Build prompt
        prompt = f"""Bạn là trợ lý AI tư vấn sản phẩm. Dựa trên thông tin sản phẩm dưới đây, hãy trả lời câu hỏi của khách hàng một cách hữu ích và thân thiện.

Thông tin sản phẩm:
{context}

Câu hỏi của khách hàng: {query}

Hãy trả lời ngắn gọn, đề xuất 1-3 sản phẩm phù hợp nhất với lý do cụ thể."""

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
                return self._fallback_response(context_products)

        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return self._fallback_response(context_products)

    def _build_context(self, products):
        """Build context string from products"""
        lines = []
        for i, p in enumerate(products, 1):
            data = p.get('data', {})
            line = f"{i}. {data.get('name', 'Unknown')}"
            if data.get('price'):
                line += f" - Giá: {data['price']:,.0f}đ"
            if data.get('category'):
                line += f" - Danh mục: {data['category']}"
            if data.get('brand'):
                line += f" - Thương hiệu: {data['brand']}"
            lines.append(line)

        return '\n'.join(lines)

    def _fallback_response(self, products):
        """Fallback response when LLM is not available"""
        if not products:
            return "Xin lỗi, tôi không tìm thấy sản phẩm phù hợp với yêu cầu của bạn."

        response = "Dựa trên yêu cầu của bạn, tôi gợi ý các sản phẩm sau:\n\n"
        for i, p in enumerate(products[:3], 1):
            data = p.get('data', {})
            response += f"{i}. **{data.get('name', 'Unknown')}**"
            if data.get('price'):
                response += f" - {data['price']:,.0f}đ"
            response += "\n"

        return response

    def recommend(self, query, n=10):
        """
        RAG-based recommendation

        Args:
            query: natural language query
            n: number of results

        Returns:
            dict with products and optional generated response
        """
        # Retrieve relevant products
        products = self.retrieve(query, k=n)

        # Generate response
        response = self.generate_response(query, products)

        return {
            'query': query,
            'products': products,
            'response': response,
            'source': 'rag'
        }

    def get_similar_by_embedding(self, product_id, n=10):
        """Get similar products by embedding similarity"""
        # Get product data from index
        if product_id not in self.index.product_data:
            return []

        product_data = self.index.product_data[product_id]

        # Build query from product
        query = f"{product_data.get('name', '')} {product_data.get('category', '')} {product_data.get('brand', '')}"

        # Retrieve similar (excluding self)
        results = self.retrieve(query, k=n + 1)

        # Filter out the query product
        return [r for r in results if r['product_id'] != product_id][:n]


# Singleton instance
rag_engine = RAGEngine()
