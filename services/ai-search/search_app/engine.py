"""
AI Search Engine with NLP for Vietnamese
"""

import re
import unicodedata
from typing import Optional
from django.db.models import Q, F
from django.core.cache import cache
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging
from pathlib import Path
from lib.ai_core.embedder import embedder
from lib.ai_core.vector_store import vector_store
from lib.ai_core.acl import ProductACL

logger = logging.getLogger(__name__)


class VietnameseNLP:
    """Vietnamese text processing"""

    # Vietnamese stopwords
    STOPWORDS = {
        'và', 'của', 'có', 'là', 'được', 'cho', 'với', 'các', 'này',
        'trong', 'để', 'những', 'một', 'người', 'như', 'khi', 'từ',
        'không', 'cũng', 'theo', 'về', 'đã', 'sẽ', 'tại', 'hay',
        'hoặc', 'nhưng', 'vì', 'nếu', 'thì', 'mà', 'do', 'bởi'
    }

    # Common Vietnamese character mappings for normalization
    CHAR_MAP = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'đ': 'd',
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
    }

    @classmethod
    def normalize(cls, text):
        """Chuẩn hóa text tiếng Việt (bỏ dấu)"""
        if not text:
            return ''
        text = text.lower()
        result = []
        for char in text:
            result.append(cls.CHAR_MAP.get(char, char))
        return ''.join(result)

    @classmethod
    def tokenize(cls, text):
        """Tokenize text"""
        if not text:
            return []
        # Simple word tokenization
        words = re.findall(r'\w+', text.lower())
        return [w for w in words if w not in cls.STOPWORDS and len(w) > 1]

    @classmethod
    def extract_keywords(cls, text, max_keywords=10):
        """Extract keywords từ text"""
        words = cls.tokenize(text)
        # Simple frequency-based extraction
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:max_keywords]]


import difflib
import json

HARDCODED_SYNONYMS = {
    'giay the thao': ['sneaker', 'giay the thao', 'giay thê thao', 'giay chay bo'],
    'sneaker': ['giay the thao', 'giay chay bo'],
    'but bi': ['viet bi', 'viêt bi', 'but bi'],
    'viet bi': ['but bi', 'bút bi'],
    'tai nghe khong day': ['true wireless', 'tws', 'tai nghe bluetooth', 'tai nghe khong day', 'airpods'],
    'true wireless': ['tai nghe khong day', 'tws', 'tai nghe bluetooth'],
    'tws': ['tai nghe khong day', 'true wireless', 'tai nghe bluetooth'],
    'dien thoai': ['smartphone', 'dien thoai', 'dt', 'iphone', 'samsung'],
    'smartphone': ['dien thoai', 'dt', 'iphone', 'samsung'],
    'may tinh bang': ['ipad', 'tablet', 'may tinh bang'],
    'tablet': ['may tinh bang', 'ipad'],
    'ipad': ['may tinh bang', 'tablet'],
    'may tinh xach tay': ['laptop', 'macbook', 'may tinh xach tay'],
    'laptop': ['may tinh xach tay', 'macbook'],
    'macbook': ['laptop', 'may tinh xach tay'],
    'ao thun': ['t-shirt', 'ao thun', 'ao phong', 'ao pull'],
    't-shirt': ['ao thun', 'ao phong'],
    'ao phong': ['ao thun', 't-shirt'],
    'binh giu nhiet': ['binh nuoc', 'ly giu nhiet', 'binh giu nhiet', 'ly nuoc'],
    'binh nuoc': ['binh giu nhiet', 'ly giu nhiet', 'binh nuoc'],
    'ly giu nhiet': ['binh giu nhiet', 'binh nuoc']
}

# Reciprocal Rank Fusion (RRF) constants
RRF_K = 60
DEFAULT_KEYWORD_WEIGHT = 0.3
DEFAULT_VECTOR_WEIGHT = 0.7
VECTOR_INDEX_DIR = 'data/vector_index'


class Reranker:
    """
    Cross-Encoder Reranker — tăng precision cho search results.

    Kết hợp nhiều tín hiệu để rerank:
    1. Vector similarity score (từ FAISS)
    2. Keyword match strength (exact match > fuzzy)
    3. Exact phrase bonus
    4. Popularity score (fallback)

    Optionally dùng Ollama LLM để đánh giá relevance top-K candidates.
    """

    # Trọng số cho các tín hiệu
    W_VECTOR = 0.35
    W_KEYWORD = 0.35
    W_EXACT = 0.20
    W_POPULARITY = 0.10

    def __init__(self, use_llm_rerank: bool = False):
        self.nlp = VietnameseNLP()
        self.use_llm_rerank = use_llm_rerank

    def rerank(
        self,
        query: str,
        results: list,
        keyword_ranks: Optional[dict] = None,
        vector_ranks: Optional[dict] = None,
    ) -> list:
        """
        Rerank results using combined signals.

        Args:
            query: Original search query
            results: List of result dicts with at least 'product_id', 'name'
            keyword_ranks: {product_id: rank} from keyword search
            vector_ranks: {product_id: rank} from vector search

        Returns:
            Reranked list of results (sorted by combined score descending)
        """
        if not results:
            return results

        query_normalized = self.nlp.normalize(query)
        query_tokens = set(self.nlp.tokenize(query))

        for r in results:
            pid = r['product_id']
            name = r.get('name', '')
            name_norm = r.get('name_normalized', '') or self.nlp.normalize(name)
            desc = r.get('description', '') or ''
            category = r.get('category', '') or ''
            brand = r.get('brand', '') or ''

            # 1. Vector similarity score (from existing _score field)
            vector_score = r.get('_score', 0.0)
            vector_score = max(0.0, min(1.0, vector_score * 10.0))  # normalize

            # 2. Keyword match strength
            keyword_score = self._keyword_match_score(
                query_normalized, query_tokens, name_norm, desc, category, brand
            )

            # 3. Exact phrase bonus
            exact_score = self._exact_match_score(query_normalized, name_norm)

            # 4. Popularity
            popularity = float(r.get('popularity_score', 0) or 0)
            pop_score = min(1.0, popularity / 100.0)

            # Combined score
            combined = (
                self.W_VECTOR * vector_score
                + self.W_KEYWORD * keyword_score
                + self.W_EXACT * exact_score
                + self.W_POPULARITY * pop_score
            )

            r['_rerank_score'] = round(combined, 4)
            r['_scores'] = {
                'vector': round(vector_score, 3),
                'keyword': round(keyword_score, 3),
                'exact': round(exact_score, 3),
                'popularity': round(pop_score, 3),
            }

        # Sort by rerank score descending
        results.sort(key=lambda x: x.get('_rerank_score', 0), reverse=True)

        # Optional: LLM rerank for top-5
        if self.use_llm_rerank and len(results) > 1:
            results = self._llm_rerank(query, results[:5]) + results[5:]

        return results

    def _keyword_match_score(
        self,
        query_norm: str,
        query_tokens: set,
        name_norm: str,
        desc: str,
        category: str,
        brand: str,
    ) -> float:
        """Calculate keyword match strength."""
        if not query_tokens:
            return 0.0

        desc_norm = self.nlp.normalize(desc)
        cat_norm = self.nlp.normalize(category)
        brand_norm = self.nlp.normalize(brand)

        # Count token matches in each field (weighted by field importance)
        name_matches = sum(1 for t in query_tokens if t in name_norm) if name_norm else 0
        desc_matches = sum(1 for t in query_tokens if t in desc_norm) if desc_norm else 0
        cat_matches = sum(1 for t in query_tokens if t in cat_norm) if cat_norm else 0
        brand_matches = sum(1 for t in query_tokens if t in brand_norm) if brand_norm else 0

        total_tokens = len(query_tokens)
        score = (
            (name_matches / total_tokens) * 0.5
            + (desc_matches / total_tokens) * 0.2
            + (cat_matches / total_tokens) * 0.15
            + (brand_matches / total_tokens) * 0.15
        )

        return min(1.0, score)

    def _exact_match_score(self, query_norm: str, name_norm: str) -> float:
        """Bonus for exact phrase match in product name."""
        if not query_norm or not name_norm:
            return 0.0
        if query_norm in name_norm:
            return 1.0 if query_norm == name_norm else 0.7
        # Partial phrase match
        query_words = query_norm.split()
        name_words = name_norm.split()
        if len(query_words) > 1:
            matching = sum(1 for qw in query_words if qw in name_norm)
            return matching / len(query_words) * 0.5
        return 0.0

    def _llm_rerank(self, query: str, candidates: list) -> list:
        """Use Ollama LLM to rerank top candidates for relevance."""
        if len(candidates) < 2:
            return candidates

        try:
            import httpx
            from django.conf import settings

            # Build prompt
            items_text = "\n".join(
                f"[{i+1}] {r.get('name', '')} — {r.get('description', '')[:100]}"
                for i, r in enumerate(candidates)
            )
            prompt = (
                f"Query: {query}\n\n"
                f"Candidate products:\n{items_text}\n\n"
                "Rank these products by relevance to the query. "
                "Return ONLY a comma-separated list of numbers in order of relevance (most relevant first). "
                "Example: 3,1,2"
            )

            ollama_host = getattr(settings, 'OLLAMA_HOST', 'http://ollama:11434')
            response = httpx.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": "llama3.2:3b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 50},
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                text = response.json().get('response', '')
                # Parse "3,1,2" format
                import re
                indices = [int(x.strip()) for x in re.findall(r'\d+', text) if 1 <= int(x.strip()) <= len(candidates)]
                if indices:
                    indices = list(dict.fromkeys(indices))  # dedupe preserve order
                    reranked = [candidates[i-1] for i in indices if i <= len(candidates)]
                    # Add any missing candidates at the end
                    seen = {id(r) for r in reranked}
                    reranked.extend(r for r in candidates if id(r) not in seen)
                    return reranked
        except Exception as e:
            logger.warning(f"LLM rerank failed (falling back to signal-based): {e}")

        return candidates


class SmartSearchV2:
    """
    Hybrid Search V2 (Phase 4):
    1. Lexical (keyword + fuzzy + synonym) — exact match
    2. Semantic (FAISS vector search) — meaning match
    3. Reranker — combined signal reranking

    Chạy lexical + semantic song song (asyncio), RRF fusion, rerank top-K.
    """

    def __init__(self):
        self.nlp = VietnameseNLP()
        self.reranker = Reranker(use_llm_rerank=False)

    async def search(
        self,
        query: str,
        filters: Optional[dict] = None,
        page: int = 1,
        page_size: int = 20,
        mode: str = 'hybrid',
        rerank: bool = True,
        rerank_top_k: int = 30,
    ) -> dict:
        """
        Async hybrid search with reranking.

        Args:
            query: Search query
            filters: Optional filters (category, brand, min_price, max_price)
            page: Page number (1-based)
            page_size: Results per page
            mode: 'keyword' | 'vector' | 'hybrid'
            rerank: Apply cross-encoder reranking
            rerank_top_k: Number of top results to rerank

        Returns:
            Dict with results, total, page, page_size, mode
        """
        from .models import ProductIndex

        if not query:
            return {'results': [], 'total': 0, 'mode': mode}

        query_normalized = self.nlp.normalize(query)

        # Cache key
        cache_key = f"smartv2:{query_normalized}:{page}:{page_size}:{mode}:{rerank}"
        if filters:
            cache_key += f":{hash(str(filters))}"

        cached = cache.get(cache_key)
        if cached:
            return cached

        # Run lexical + semantic in parallel
        keyword_ranks = {}
        vector_ranks = {}

        if mode in ('keyword', 'hybrid'):
            keyword_ranks = search_engine._keyword_search_ranks(query, filters)

        if mode in ('vector', 'hybrid'):
            vector_ranks = await self._async_vector_search(query, filters)

        # Fuse via RRF
        all_ids = set(keyword_ranks.keys()) | set(vector_ranks.keys())
        if not all_ids:
            response = {
                'query': query, 'results': [], 'total': 0,
                'page': page, 'page_size': page_size, 'mode': mode,
            }
            cache.set(cache_key, response, timeout=300)
            return response

        if mode == 'hybrid':
            scores = {}
            for pid in all_ids:
                score = 0.0
                if pid in keyword_ranks:
                    score += DEFAULT_KEYWORD_WEIGHT / (RRF_K + keyword_ranks[pid])
                if pid in vector_ranks:
                    score += DEFAULT_VECTOR_WEIGHT / (RRF_K + vector_ranks[pid])
                scores[pid] = score
        elif mode == 'keyword':
            scores = {pid: 1.0 / (RRF_K + rank) for pid, rank in keyword_ranks.items()}
        elif mode == 'vector':
            scores = {pid: 1.0 / (RRF_K + rank) for pid, rank in vector_ranks.items()}
        else:
            scores = keyword_ranks

        ranked_ids = sorted(scores.keys(), key=lambda pid: scores[pid], reverse=True)

        total = len(ranked_ids)

        # Fetch candidates for reranking (top rerank_top_k)
        fetch_end = rerank_top_k if rerank else page * page_size
        candidate_ids = ranked_ids[:fetch_end]

        results = []
        if candidate_ids:
            product_map = {
                str(p.product_id): p
                for p in ProductIndex.objects.filter(product_id__in=candidate_ids)
            }
            for pid in candidate_ids:
                p = product_map.get(pid)
                if p:
                    results.append({
                        'product_id': str(p.product_id),
                        'name': p.name,
                        'name_normalized': p.name_normalized,
                        'description': p.description,
                        'category': p.category,
                        'brand': p.brand,
                        'price': float(p.price),
                        'keywords': p.keywords,
                        'popularity_score': p.popularity_score,
                        '_score': float(scores[pid]),
                    })

        # Rerank
        if rerank and len(results) > 1:
            results = self.reranker.rerank(query, results, keyword_ranks, vector_ranks)

        # Paginate after reranking
        start = (page - 1) * page_size
        end = start + page_size
        page_results = results[start:end]

        # Record search history (sync)
        search_engine._record_search(query, query_normalized, total)

        response = {
            'query': query,
            'results': page_results,
            'total': total,
            'page': page,
            'page_size': page_size,
            'mode': mode,
            'reranked': rerank,
        }

        cache.set(cache_key, response, timeout=300)
        return response

    async def _async_vector_search(
        self,
        query: str,
        filters: Optional[dict] = None,
    ) -> dict:
        """Async vector search — chạy song song với keyword search."""
        search_engine._ensure_vector_index()

        try:
            embedding = embedder.embed_sync(query)
            vec_filters = None
            if filters:
                vf = {}
                if filters.get('category'):
                    vf['category'] = filters['category']
                if filters.get('brand'):
                    vf['brand'] = filters['brand']
                if filters.get('min_price'):
                    vf['price_min'] = float(filters['min_price'])
                if filters.get('max_price'):
                    vf['price_max'] = float(filters['max_price'])
                vec_filters = vf if vf else None

            vec_results = vector_store.search(embedding, k=50, filters=vec_filters)
            return {
                r['product_id']: rank
                for rank, r in enumerate(vec_results, start=1)
            }
        except Exception as e:
            logger.warning(f"Async vector search failed: {e}")
            return {}


# Singleton
smart_search = SmartSearchV2()


class SearchEngine:
    """
    Smart Search Engine với:
    1. Full-text search
    2. Fuzzy matching & Typo tolerance
    3. Synonym expansion
    4. Query understanding
    """

    def __init__(self):
        self.nlp = VietnameseNLP()
        self.tfidf = None
        self._vector_verified = False
        self._load_vector_index()

    def _load_vector_index(self):
        """Load FAISS index from disk during startup (no verification, no rebuild)."""
        try:
            vs_ok = (
                getattr(vector_store, '_initialized', False)
                and vector_store.product_ids
                and getattr(vector_store, 'index', None) is not None
                and vector_store.index.ntotal > 0
            )
            if vs_ok:
                return

            index_dir = self._get_vector_index_dir()
            loaded = vector_store.load(index_dir)
            if loaded:
                logger.info(f"Loaded vector index from {index_dir}")
            else:
                logger.info("No existing vector index found")
        except Exception as e:
            logger.warning(f"Vector store load failed: {e}")

    def _ensure_vector_index(self):
        """Lazy verification + rebuild of vector index (called on first search).

        Handles gunicorn post-fork and embedding model reload:
        - After fork, FAISS index may be lost — reload from disk
        - After model reload, embeddings may be incompatible — regenerate
        """
        if self._vector_verified:
            return

        try:
            # Post-fork: reload if FAISS index lost or empty
            need_load = not (
                getattr(vector_store, '_initialized', False)
                and vector_store.product_ids
                and getattr(vector_store, 'index', None) is not None
                and vector_store.index.ntotal > 0
            )
            if need_load:
                logger.info("Reloading vector store (post-fork)")
                index_dir = self._get_vector_index_dir()
                vector_store.load(index_dir)

            # Verify model session compatibility
            if not self._verify_embeddings():
                logger.warning(
                    "Stored embeddings incompatible with current model session, "
                    "regenerating all embeddings"
                )
                self.rebuild_vector_index()

            self._vector_verified = True
        except Exception as e:
            logger.warning(f"Vector store initialization failed: {e}")
            self._vector_verified = True  # Don't retry on every request

    def _verify_embeddings(self) -> bool:
        """Check if stored FAISS embeddings match the current embedder session."""
        from .models import ProductIndex
        if not vector_store.product_ids:
            return False

        ref_pid = vector_store.product_ids[0]
        try:
            p = ProductIndex.objects.get(product_id=ref_pid)
        except ProductIndex.DoesNotExist:
            if vector_store.product_data:
                ref_data = next(iter(vector_store.product_data.values()))
            else:
                return False

        fresh_emb = self._embed_product(p)
        if fresh_emb is None:
            return False

        try:
            results = vector_store.search(fresh_emb, k=5)
            if not results:
                return False
            top_score = results[0]['score']
            top_pid = results[0]['product_id']
            return top_pid == ref_pid and top_score > 0.5
        except Exception as e:
            logger.warning(f"Embedding verification failed (model session changed?): {e}")
            return False

    def _embed_product(self, product) -> Optional[np.ndarray]:
        """Generate embedding for a ProductIndex record."""
        from lib.ai_core.acl import ProductACL
        raw = {
            'id': str(product.product_id),
            'name': product.name,
            'description': product.description,
            'brand': product.brand,
            'category': product.category,
        }
        try:
            normal = ProductACL.from_api_response(raw)
            embed_text = ProductACL.to_embedding_text(normal)
            embedding = embedder.embed_sync(embed_text)
            if embedding is None or embedding.size == 0:
                return None
            emb_1d = embedding[0] if embedding.ndim > 1 else embedding
            return emb_1d.astype(np.float32)
        except Exception as e:
            logger.warning(f"Failed to embed product {product.product_id}: {e}")
            return None

    def _get_vector_index_dir(self):
        """Get persistent directory for FAISS index files."""
        from django.conf import settings
        d = Path(settings.BASE_DIR) / VECTOR_INDEX_DIR
        d.mkdir(parents=True, exist_ok=True)
        return str(d)

    def _keyword_search_ranks(self, query, filters=None):
        """Run keyword search and return {product_id_str: rank} dict (1-based rank)."""
        from .models import ProductIndex, Synonym

        query_normalized = self.nlp.normalize(query)
        query_tokens = self.nlp.tokenize(query)

        # Synonym expansion
        expanded_keywords = {query_normalized}
        for token in query_tokens:
            expanded_keywords.add(token)

        # DB synonyms
        try:
            db_synonyms = Synonym.objects.filter(
                Q(word__iexact=query_normalized) | Q(word__in=query_tokens)
            )
            for syn_obj in db_synonyms:
                try:
                    words_list = json.loads(syn_obj.synonyms)
                    for w in words_list:
                        expanded_keywords.add(self.nlp.normalize(w))
                except Exception:
                    for w in syn_obj.synonyms.split(','):
                        expanded_keywords.add(self.nlp.normalize(w.strip()))
        except Exception as e:
            logger.error(f"Error loading DB synonyms: {e}")

        # Hardcoded synonyms
        for kw in list(expanded_keywords):
            if kw in HARDCODED_SYNONYMS:
                for syn in HARDCODED_SYNONYMS[kw]:
                    expanded_keywords.add(self.nlp.normalize(syn))

        # Build keyword query
        q_objects = Q()
        q_objects |= Q(name__icontains=query)
        q_objects |= Q(name_normalized__icontains=query_normalized)
        for kw in expanded_keywords:
            q_objects |= Q(name_normalized__icontains=kw)
            q_objects |= Q(keywords__icontains=kw)
            q_objects |= Q(brand__icontains=kw)
            q_objects |= Q(category__icontains=kw)

        queryset = ProductIndex.objects.filter(q_objects)

        # Apply filters
        if filters:
            if filters.get('category'):
                queryset = queryset.filter(category__icontains=filters['category'])
            if filters.get('brand'):
                queryset = queryset.filter(brand__icontains=filters['brand'])
            if filters.get('min_price'):
                queryset = queryset.filter(price__gte=filters['min_price'])
            if filters.get('max_price'):
                queryset = queryset.filter(price__lte=filters['max_price'])

        # Score and rank by popularity
        queryset = queryset.order_by('-popularity_score')

        ranks = {}
        for rank, item in enumerate(queryset.values('product_id'), start=1):
            ranks[str(item['product_id'])] = rank

        return ranks

    def hybrid_search(self, query, filters=None, page=1, page_size=20, mode='hybrid'):
        """
        Hybrid search with Reciprocal Rank Fusion (RRF).

        Modes:
          'keyword' – keyword-only (same as search())
          'vector'  – semantic-only (FAISS)
          'hybrid'  – RRF merge of keyword + vector (default)
        """
        self._ensure_vector_index()
        from .models import ProductIndex

        if not query:
            return {'results': [], 'total': 0, 'mode': mode}

        query_normalized = self.nlp.normalize(query)

        # Cache key
        cache_key = f"hybrid:{query_normalized}:{page}:{page_size}:{mode}"
        if filters:
            cache_key += f":{hash(str(filters))}"

        cached = cache.get(cache_key)
        if cached:
            return cached

        keyword_ranks = {}
        vector_ranks = {}

        # 1. Keyword search
        if mode in ('keyword', 'hybrid'):
            keyword_ranks = self._keyword_search_ranks(query, filters)

        # 2. Vector search
        if mode in ('vector', 'hybrid'):
            try:
                embedding = embedder.embed_sync(query)
                # Map service-level filter names to vector_store filter names
                vec_filters = None
                if filters:
                    vf = {}
                    if filters.get('category'):
                        vf['category'] = filters['category']
                    if filters.get('brand'):
                        vf['brand'] = filters['brand']
                    if filters.get('min_price'):
                        vf['price_min'] = float(filters['min_price'])
                    if filters.get('max_price'):
                        vf['price_max'] = float(filters['max_price'])
                    vec_filters = vf if vf else None

                vec_results = vector_store.search(embedding, k=50, filters=vec_filters)
                for rank, r in enumerate(vec_results, start=1):
                    vector_ranks[r['product_id']] = rank
            except Exception as e:
                logger.warning(f"Vector search failed, falling back to keyword: {e}")

        # 3. Fuse via RRF
        all_ids = set(keyword_ranks.keys()) | set(vector_ranks.keys())
        if not all_ids:
            response = {'query': query, 'results': [], 'total': 0, 'page': page, 'page_size': page_size, 'mode': mode}
            cache.set(cache_key, response, timeout=300)
            return response

        if mode == 'hybrid':
            scores = {}
            for pid in all_ids:
                score = 0.0
                if pid in keyword_ranks:
                    score += DEFAULT_KEYWORD_WEIGHT / (RRF_K + keyword_ranks[pid])
                if pid in vector_ranks:
                    score += DEFAULT_VECTOR_WEIGHT / (RRF_K + vector_ranks[pid])
                scores[pid] = score
        elif mode == 'keyword':
            scores = {pid: 1.0 / (RRF_K + rank) for pid, rank in keyword_ranks.items()}
        elif mode == 'vector':
            scores = {pid: 1.0 / (RRF_K + rank) for pid, rank in vector_ranks.items()}
        else:
            scores = keyword_ranks  # fallback

        ranked_ids = sorted(scores.keys(), key=lambda pid: scores[pid], reverse=True)

        total = len(ranked_ids)
        start = (page - 1) * page_size
        end = start + page_size
        page_ids = ranked_ids[start:end]

        # Fetch results preserving RRF rank order
        results = []
        if page_ids:
            product_map = {str(p.product_id): p for p in ProductIndex.objects.filter(product_id__in=page_ids)}
            for pid in page_ids:
                p = product_map.get(pid)
                if p:
                    results.append({
                        'product_id': str(p.product_id),
                        'name': p.name,
                        'name_normalized': p.name_normalized,
                        'description': p.description,
                        'category': p.category,
                        'brand': p.brand,
                        'price': float(p.price),
                        'keywords': p.keywords,
                        'popularity_score': p.popularity_score,
                        '_score': float(scores[pid]),
                    })

        # Record search history
        self._record_search(query, query_normalized, total)

        response = {
            'query': query,
            'results': results,
            'total': total,
            'page': page,
            'page_size': page_size,
            'mode': mode,
        }

        cache.set(cache_key, response, timeout=300)
        return response

    def rebuild_vector_index(self):
        """Rebuild FAISS vector index from product text.

        Regenerates ALL embeddings using the current embedder model session,
        ensuring compatibility between stored embeddings and query embeddings.
        """
        from .models import ProductIndex

        # Force correct dimension from embedder config (handles corrupt meta.json)
        vector_store.embedding_dim = embedder.EMBEDDING_DIM

        # Reset vector store state (handle both FAISS and numpy fallback)
        try:
            vector_store.reset()
        except Exception:
            vector_store.index = None
            vector_store.product_ids = []
            vector_store.product_data = {}
            vector_store._embeddings_fallback = []
            vector_store._initialized = True

        products = list(ProductIndex.objects.all())
        if not products:
            logger.info("No products to index")
            return 0

        texts = []
        for p in products:
            raw = {
                'id': str(p.product_id),
                'name': p.name,
                'description': p.description,
                'brand': p.brand,
                'category': p.category,
            }
            normal = ProductACL.from_api_response(raw)
            texts.append(ProductACL.to_embedding_text(normal))

        # Batch-generate all embeddings (single model session)
        logger.info(f"Generating {len(texts)} embeddings with {embedder.MODEL_NAME}...")
        try:
            embeddings = embedder.embed_sync(texts)
            logger.info(f"Embeddings generated: shape={embeddings.shape}")
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            return 0

        if embeddings.ndim < 2 or embeddings.shape[1] != embedder.EMBEDDING_DIM:
            logger.error(f"Unexpected embedding shape: {embeddings.shape}")
            return 0

        count = 0
        errors = 0
        for i, p in enumerate(products):
            try:
                emb_1d = np.asarray(embeddings[i], dtype=np.float32)
                pid = str(p.product_id)
                vector_store.add(
                    product_id=pid,
                    embedding=emb_1d,
                    data={
                        'name': p.name,
                        'category': p.category,
                        'brand': p.brand,
                        'price': float(p.price),
                    },
                )
                count += 1
            except Exception as e:
                errors += 1
                if errors <= 3:
                    import traceback
                    logger.warning(f"Failed to add {p.product_id}: {e}\n{traceback.format_exc()}")

        # Persist to disk
        try:
            index_dir = self._get_vector_index_dir()
            import shutil
            if Path(index_dir).exists():
                shutil.rmtree(index_dir)
            vector_store.save(index_dir)
            logger.info(f"Saved vector index ({count} products) to {index_dir}")
        except Exception as e:
            logger.warning(f"Failed to save vector index: {e}")

        if errors:
            logger.warning(f"Indexed {count}/{len(products)} products ({errors} errors)")
        else:
            logger.info(f"Rebuilt vector index with {count} products")
        return count

    def search(self, query, filters=None, page=1, page_size=20):
        """
        Tìm kiếm thông minh
        """
        from .models import ProductIndex, SearchHistory, Synonym

        if not query:
            return {'results': [], 'total': 0}

        # Normalize query
        query_normalized = self.nlp.normalize(query)
        query_tokens = self.nlp.tokenize(query)

        # Cache key
        cache_key = f"search:{query_normalized}:{page}:{page_size}"
        if filters:
            cache_key += f":{hash(str(filters))}"

        cached = cache.get(cache_key)
        if cached:
            return cached

        # Synonym Expansion
        expanded_keywords = {query_normalized}
        for token in query_tokens:
            expanded_keywords.add(token)

        # Load from DB synonyms
        try:
            db_synonyms = Synonym.objects.filter(
                Q(word__iexact=query_normalized) | Q(word__in=query_tokens)
            )
            for syn_obj in db_synonyms:
                try:
                    words_list = json.loads(syn_obj.synonyms)
                    for w in words_list:
                        expanded_keywords.add(self.nlp.normalize(w))
                except Exception:
                    for w in syn_obj.synonyms.split(','):
                        expanded_keywords.add(self.nlp.normalize(w.strip()))
        except Exception as e:
            logger.error(f"Error loading DB synonyms: {e}")

        # Fallback to hardcoded synonyms
        for kw in list(expanded_keywords):
            if kw in HARDCODED_SYNONYMS:
                for syn in HARDCODED_SYNONYMS[kw]:
                    expanded_keywords.add(self.nlp.normalize(syn))

        # Build search query
        q_objects = Q()

        # Exact match (highest priority)
        q_objects |= Q(name__icontains=query)
        q_objects |= Q(name_normalized__icontains=query_normalized)

        # Token & Synonym matching
        for kw in expanded_keywords:
            q_objects |= Q(name_normalized__icontains=kw)
            q_objects |= Q(keywords__icontains=kw)
            q_objects |= Q(brand__icontains=kw)
            q_objects |= Q(category__icontains=kw)

        # Apply filters & query
        queryset = ProductIndex.objects.filter(q_objects)

        if filters:
            if filters.get('category'):
                queryset = queryset.filter(category__icontains=filters['category'])
            if filters.get('brand'):
                queryset = queryset.filter(brand__icontains=filters['brand'])
            if filters.get('min_price'):
                queryset = queryset.filter(price__gte=filters['min_price'])
            if filters.get('max_price'):
                queryset = queryset.filter(price__lte=filters['max_price'])

        # Fuzzy Matching fallback (Typo Tolerance) if no results found
        if queryset.count() == 0:
            all_indices = ProductIndex.objects.all().values(
                'id', 'product_id', 'name', 'name_normalized', 'brand', 'category', 'price', 'popularity_score'
            )
            matched_items = []
            for item in all_indices:
                name_norm = item['name_normalized'] or ''
                brand_norm = self.nlp.normalize(item['brand']) if item['brand'] else ''
                cat_norm = self.nlp.normalize(item['category']) if item['category'] else ''

                ratio_name = difflib.SequenceMatcher(None, query_normalized, name_norm).ratio()
                ratio_brand = difflib.SequenceMatcher(None, query_normalized, brand_norm).ratio() if brand_norm else 0
                ratio_cat = difflib.SequenceMatcher(None, query_normalized, cat_norm).ratio() if cat_norm else 0

                best_ratio = max(ratio_name, ratio_brand, ratio_cat)

                query_words = query_normalized.split()
                name_words = name_norm.split()

                word_matches = 0
                for qw in query_words:
                    close = difflib.get_close_matches(qw, name_words, n=1, cutoff=0.7)
                    if close:
                        word_matches += 1

                word_ratio = word_matches / len(query_words) if query_words else 0

                if best_ratio >= 0.6 or word_ratio >= 0.65:
                    score = max(best_ratio, word_ratio) * 0.8 + (float(item['popularity_score'] or 0) / 100.0) * 0.2
                    matched_items.append((item['id'], score))

            if matched_items:
                matched_items.sort(key=lambda x: x[1], reverse=True)
                best_ids = [x[0] for x in matched_items[:limit]]
                queryset = ProductIndex.objects.filter(id__in=best_ids)

        # Score and sort
        queryset = queryset.order_by('-popularity_score')

        # Pagination
        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        results = list(queryset[start:end].values())

        # Record search history
        self._record_search(query, query_normalized, total)

        response = {
            'query': query,
            'results': results,
            'total': total,
            'page': page,
            'page_size': page_size,
        }

        cache.set(cache_key, response, timeout=300)
        return response

    def autocomplete(self, query, limit=10):
        """Gợi ý tìm kiếm"""
        from .models import ProductIndex, SearchHistory

        if not query or len(query) < 2:
            return []

        cache_key = f"autocomplete:{query}:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        query_normalized = self.nlp.normalize(query)
        suggestions = []

        # From search history
        history = SearchHistory.objects.filter(
            query_normalized__startswith=query_normalized
        ).order_by('-search_count')[:limit // 2]

        for h in history:
            suggestions.append({
                'text': h.query,
                'type': 'history',
                'count': h.search_count
            })

        # From product names
        products = ProductIndex.objects.filter(
            name_normalized__icontains=query_normalized
        ).order_by('-popularity_score')[:limit // 2]

        for p in products:
            suggestions.append({
                'text': p.name,
                'type': 'product',
                'product_id': str(p.product_id)
            })

        # Remove duplicates
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            key = s['text'].lower()
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(s)

        cache.set(cache_key, unique_suggestions[:limit], timeout=60)
        return unique_suggestions[:limit]

    def _record_search(self, query, query_normalized, result_count):
        """Ghi nhận lịch sử tìm kiếm"""
        from .models import SearchHistory

        try:
            history, created = SearchHistory.objects.get_or_create(
                query_normalized=query_normalized,
                defaults={
                    'query': query,
                    'result_count': result_count
                }
            )
            if not created:
                history.search_count = F('search_count') + 1
                history.result_count = result_count
                history.save()
        except Exception as e:
            logger.error(f"Error recording search: {e}")

    def index_product(self, product_data):
        """Index một sản phẩm (keyword + embedding + FAISS)"""
        from .models import ProductIndex

        name = product_data.get('name', '')
        description = product_data.get('description', '') or product_data.get('short_description', '')

        # Extract keywords
        text = f"{name} {description}"
        keywords = ' '.join(self.nlp.extract_keywords(text))

        # Handle category - can be dict with 'name' or string or have separate 'category_name'
        category = product_data.get('category', '')
        if isinstance(category, dict):
            category = category.get('name', '')
        else:
            category = product_data.get('category_name', str(category))

        index_obj, created = ProductIndex.objects.update_or_create(
            product_id=product_data['id'],
            defaults={
                'name': name,
                'name_normalized': self.nlp.normalize(name),
                'description': description,
                'category': category,
                'brand': product_data.get('brand', ''),
                'price': float(product_data.get('price', 0) or 0),
                'keywords': keywords,
                'popularity_score': float(product_data.get('sold_count', 0) or 0) * 0.5 + float(product_data.get('view_count', 0) or 0) * 0.1,
            }
        )

        # Generate and store embedding (silent fail)
        try:
            normalized = ProductACL.from_api_response(product_data)
            embed_text = ProductACL.to_embedding_text(normalized)
            embedding = embedder.embed_sync(embed_text)

            if embedding is not None and embedding.size > 0:
                emb_1d = embedding[0] if embedding.ndim > 1 else embedding
                ProductIndex.objects.filter(product_id=product_data['id']).update(
                    embedding=emb_1d.astype(np.float32).tobytes()
                )
                vector_store.add(
                    product_id=str(product_data['id']),
                    embedding=emb_1d,
                    data=normalized,
                )
                logger.debug(f"Generated embedding for product {product_data['id']}")
        except Exception as e:
            logger.warning(f"Embedding generation failed for product {product_data.get('id')}: {e}")

    def reindex_all(self):
        """Reindex tất cả sản phẩm từ Product Service"""
        import httpx
        from django.conf import settings

        try:
            response = httpx.get(
                f"{settings.PRODUCT_SERVICE_URL}/?page_size=1000",
                timeout=30.0
            )
            if response.status_code == 200:
                data = response.json()
                products = data.get('results', [])

                for product in products:
                    self.index_product(product)

                return {'indexed': len(products)}
        except Exception as e:
            logger.error(f"Reindex error: {e}")
            return {'error': str(e)}


# Singleton
search_engine = SearchEngine()
