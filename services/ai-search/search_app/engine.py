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
        """Index một sản phẩm"""
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

        ProductIndex.objects.update_or_create(
            product_id=product_data['id'],
            defaults={
                'name': name,
                'name_normalized': self.nlp.normalize(name),
                'description': description,
                'category': category,
                'brand': product_data.get('brand', ''),
                'price': float(product_data.get('price', 0) or 0),
                'keywords': keywords,
                'popularity_score': float(product_data.get('sold_count', 0) or 0) * 0.5 + float(product_data.get('view_count', 0) or 0) * 0.1
            }
        )

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
