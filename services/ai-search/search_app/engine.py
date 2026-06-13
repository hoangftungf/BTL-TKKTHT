"""
AI Search Engine with NLP for Vietnamese
"""

import re
import unicodedata
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
DEFAULT_KEYWORD_WEIGHT = 0.5
DEFAULT_VECTOR_WEIGHT = 0.5
VECTOR_INDEX_DIR = 'data/vector_index'


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
        self._ensure_vector_index()

    def _ensure_vector_index(self):
        """Load FAISS index from disk or rebuild from ProductIndex embeddings."""
        try:
            if getattr(vector_store, '_initialized', False):
                return
            index_dir = self._get_vector_index_dir()
            loaded = vector_store.load(index_dir)
            if not loaded:
                logger.info("No existing vector index found, rebuilding from database")
                self.rebuild_vector_index()
            else:
                logger.info(f"Loaded vector index from {index_dir}")
        except Exception as e:
            logger.warning(f"Vector store initialization failed: {e}")

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
        """Rebuild FAISS vector index from ProductIndex.embedding (PostgreSQL authoritative source)."""
        from .models import ProductIndex

        # Reset vector store state (handle both FAISS and numpy fallback)
        try:
            vector_store.reset()
        except Exception:
            # FAISS not available — use numpy fallback
            vector_store.index = None
            vector_store.product_ids = []
            vector_store.product_data = {}
            vector_store._embeddings_fallback = []
            vector_store._initialized = True

        count = 0
        for idx in ProductIndex.objects.exclude(embedding__isnull=True).iterator(chunk_size=100):
            try:
                emb_bytes = bytes(idx.embedding)
                embedding = np.frombuffer(emb_bytes, dtype=np.float32)
                if embedding.size == 768:
                    vector_store.add(
                        product_id=str(idx.product_id),
                        embedding=embedding,
                        data={
                            'name': idx.name,
                            'category': idx.category,
                            'brand': idx.brand,
                            'price': float(idx.price),
                        },
                    )
                    count += 1
            except Exception as e:
                logger.warning(f"Failed to rebuild index for {idx.product_id}: {e}")

        # Persist to disk
        try:
            index_dir = self._get_vector_index_dir()
            vector_store.save(index_dir)
            logger.info(f"Saved vector index ({count} products) to {index_dir}")
        except Exception as e:
            logger.warning(f"Failed to save vector index: {e}")

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
