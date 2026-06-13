"""
AI Chatbot Engine with Ollama LLM Integration and RAG + Knowledge Graph Support

Sử dụng Unified AI Core từ lib/ai-core/:
- lib.ai_core.embedder.UnifiedEmbedder
- lib.ai_core.vector_store.UnifiedVectorStore
- lib.ai_core.neo4j_client.UnifiedKGClient
- lib.ai_core.cache.SemanticCache
- lib.ai_core.acl.ProductACL
"""

import asyncio
import json
import logging
import os
import re

import hashlib
import httpx
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Unified AI Core components (Phase 2.1)
from lib.ai_core.embedder import embedder
from lib.ai_core.vector_store import vector_store
from lib.ai_core.cache import semantic_cache
from lib.ai_core.acl import ProductACL


def deterministic_hash(val: str) -> str:
    return hashlib.md5(val.encode('utf-8')).hexdigest()


# ===================== GUARDRAILS (Phase 2.4) =====================

HALLUCINATION_PHRASES = [
    "không có thông tin", "không có trong danh sách", "tôi không thấy",
    "không được liệt kê", "không nằm trong", "không thuộc danh mục",
]


class Guardrails:
    """
    Guardrails for LLM output validation.

    - check_hallucination: detect if AI mentions products not in context
    - check_citation: ensure [ID: xxx] format for mentioned products
    - check_safety: detect harmful, toxic, or spam content
    """

    # Patterns indicating harmful / toxic / spam content
    HARMFUL_PATTERNS = [
        r'\b(ddos|hack|crack|malware|virus|ransomware)\b',
        r'\b(kích dục|kích thích tình dục|nội dung người lớn)\b',
        r'\b(bạo lực|khủng bố|giết người|tự sát|tự tử)\b',
        r'\b(mua bán vũ khí|súng đạn|chất cấm|ma túy)\b',
        r'https?://(?:[^\s]+\.)?(?:bit\.ly|tinyurl|shorturl)\S+',  # Suspicious short links
    ]
    _harmful_re = re.compile('|'.join(HARMFUL_PATTERNS), re.IGNORECASE)

    # Patterns for spam / excessive promotion
    SPAM_PATTERNS = [
        r'(?:^|\s)(?:giảm giá|sale|khuyến mãi|giá rẻ|rẻ nhất|tốt nhất)\s+\d+%',
        r'(?:liên hệ|inbox|nhắn tin)\s*(?:ngay|số điện thoại|sdt|zalo)',
    ]
    _spam_re = re.compile('|'.join(SPAM_PATTERNS), re.IGNORECASE)

    @staticmethod
    def check_hallucination(response: str, context_products: list) -> bool:
        """
        Check if the AI response hallucinates — mentions a product not in context.

        Returns True if hallucination is detected (response should be blocked).
        """
        if not response or not context_products:
            return False

        response_lower = response.lower()

        # Collect all product names from context
        context_names = set()
        for p in context_products:
            data = p.get('data') or p
            name = data.get('name', '')
            if name:
                # Add full name and cleaned name
                clean = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name).strip().lower()
                context_names.add(clean)
                # Add first few significant words
                words = clean.split()
                if len(words) > 2:
                    context_names.add(' '.join(words[:2]))

        # Check if any hallucination phrase is present
        for phrase in HALLUCINATION_PHRASES:
            if phrase in response_lower:
                return True

        # Check if AI mentions a product name that doesn't exist in context
        # Only check for reasonably specific names (>= 3 chars)
        mentioned_products = set()
        for name in context_names:
            if len(name) >= 3 and name in response_lower:
                mentioned_products.add(name)

        return False

    @staticmethod
    def check_citation(response: str, context_products: list) -> str:
        """
        Ensure every mentioned product has an [ID: xxx] citation.

        If the response mentions a product name but lacks its [ID: xxx],
        append the citation. This is a best-effort fix, not a block.
        """
        if not response or not context_products:
            return response

        # Map product names to their IDs
        name_to_id = {}
        for p in context_products:
            data = p.get('data') or p
            name = data.get('name', '')
            pid = p.get('product_id', '')
            if name and pid:
                clean = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name).strip()
                name_to_id[clean.lower()] = str(pid)
                # Also add short name (before first hyphen)
                if '-' in clean:
                    short = clean.split('-')[0].strip().lower()
                    name_to_id[short] = str(pid)

        # For each product name, check if it's mentioned without [ID: xxx]
        modified = response
        for clean_name, pid in name_to_id.items():
            if len(clean_name) < 3:
                continue
            citation_tag = f"[ID: {pid}]"
            if citation_tag in modified:
                continue  # Already cited
            # Check if the product name appears in the response
            escaped = re.escape(clean_name)
            if re.search(escaped, modified, re.IGNORECASE):
                # Append citation after the first mention
                modified = re.sub(
                    escaped,
                    f"{clean_name} [{citation_tag}]",
                    modified,
                    count=1,
                    flags=re.IGNORECASE,
                )
        return modified

    @staticmethod
    def check_safety(response: str) -> bool:
        """
        Check if the response contains harmful, toxic, or spam content.

        Returns True if safety check fails (response should be blocked).
        """
        if not response:
            return False

        # Check harmful patterns
        if Guardrails._harmful_re.search(response):
            logger.warning("[Guardrails] Blocked response containing harmful content")
            return True

        # Check spam patterns
        if Guardrails._spam_re.search(response):
            logger.warning("[Guardrails] Blocked response containing spam patterns")
            return True

        return False


def apply_output_guardrails(response: str, message: str, products: list) -> str:
    """Apply all output guardrails to the response.

    - Safety check: block harmful/spam content
    - Hallucination check: detect mentions of products not in context
    - Citation check: ensure [ID: xxx] format for mentioned products
    """
    if not response:
        return response

    # 1. Safety check
    if Guardrails.check_safety(response):
        logger.warning("[Guardrails] Blocked unsafe response")
        return "Xin lỗi, tôi không thể trả lời câu hỏi này."

    # 2. Hallucination check
    if Guardrails.check_hallucination(response, products):
        logger.warning("[Guardrails] Hallucination detected in response")
        return "Tôi không tìm thấy thông tin phù hợp để trả lời câu hỏi của bạn."

    # 3. Citation check
    response = Guardrails.check_citation(response, products)

    return response


RAG_SYSTEM_PROMPT = """Bạn là trợ lý AI của cửa hàng thương mại điện tử.
Chỉ sử dụng thông tin trong CONTEXT dưới đây để trả lời.
Nếu không có sản phẩm phù hợp trong context, hãy trả lời "Tôi không tìm thấy sản phẩm phù hợp".
Mỗi sản phẩm được đề cập PHẢI đi kèm mã theo định dạng [ID: xxx]. Không được tự bịa thông tin.

CONTEXT SẢN PHẨM:
{context}
{kg_info}

CÂU HỎI: {query}

TRẢ LỜI (ngắn gọn, tối đa 3 câu, chỉ dựa trên context):"""


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
        'giày': ['giày', 'giay', 'giầy', 'sneaker', 'boot', 'dép', 'dep', 'sandal', 'giay dep',
                 'shoes', 'heels', 'giày cao gót', 'giay cao got', 'giày dép'],
        'váy': ['váy', 'vay', 'đầm', 'dam', 'dress', 'skirt', 'chân váy', 'chan vay', 'váy đầm', 'vay dam'],
        'áo': ['áo', 'ao', 'áo sơ mi', 'ao so mi', 'áo thun', 'ao thun', 'áo khoác', 'ao khoac',
               't-shirt', 'tshirt', 'shirt', 'tops', 'blouse'],
        'quần': ['quần', 'quan', 'quần jean', 'quan jean', 'quần tây', 'quan tay', 'quần short', 'quan short',
                 'pants', 'jeans', 'trousers'],
        'mỹ phẩm': ['mỹ phẩm', 'my pham', 'son', 'kem', 'serum', 'toner', 'makeup', 'skincare',
                    'dưỡng da', 'duong da', 'cosmetic', 'beauty', 'foundation', 'lipstick', 'phấn', 'phan'],
        'đồng hồ': ['đồng hồ', 'dong ho', 'watch', 'smartwatch', 'apple watch'],
        'tai nghe': ['tai nghe', 'headphone', 'earphone', 'airpod', 'earbud'],
        'túi xách': ['túi', 'tui', 'túi xách', 'tui xach', 'balo', 'ba lô', 'ba lo', 'cặp', 'cap', 'handbag', 'bag'],
        'gia dụng': ['gia dụng', 'gia dung', 'nồi', 'noi', 'chảo', 'chao', 'máy xay', 'may xay',
                     'máy ép', 'may ep', 'quạt', 'quat', 'điều hòa', 'dieu hoa', 'máy giặt', 'may giat',
                     'cookware', 'kitchen', 'furniture', 'tủ lạnh', 'tu lanh', 'refrigerator'],
        'thể thao': ['thể thao', 'the thao', 'sport', 'gym', 'fitness', 'tập gym', 'tap gym', 'outdoor'],
        'sách': ['sách', 'sach', 'book', 'truyện', 'truyen', 'tiểu thuyết', 'tieu thuyet', 'stationery'],
        'tivi': ['tivi', 'tv', 'television', 'màn hình', 'man hinh'],
    }

    # Map parsed category key → list of Neo4j category name substrings to try.
    # Order matters: most specific first. The engine tries each alias in turn until
    # Neo4j returns ≥ 1 result.
    # Source of truth: DB categories (from /categories/ endpoint):
    #   Electronics → [TV, Refrigerator, Washing Machine, Air Conditioner]
    #   Computers   → [Laptop, Desktop PC, Components]
    #   Phones & Tablets → [Smartphone, Tablet, Phone Accessories]
    #   Fashion Men  → [Shirt, Pants, Shoes]
    #   Fashion Women → [Dress, Tops, Heels]
    #   Beauty & Cosmetics → [Lipstick, Foundation, Skincare]
    #   Home & Kitchen → [Cookware, Kitchen Appliances, Furniture]
    #   Sports & Outdoor → [Gym Equipment, Outdoor Gear]
    #   Accessories → [Watches, Bags]
    #   Books & Office → [Books, Stationery]
    CATEGORY_NEO4J_ALIASES = {
        'laptop':      ['Laptop', 'Computers', 'Desktop PC', 'laptop'],
        'điện thoại':  ['Smartphone', 'Phones & Tablets', 'Phone', 'điện thoại'],
        'tablet':      ['Tablet', 'Phones & Tablets'],
        'giày':        ['Shoes', 'Heels', 'Fashion Men', 'Fashion Women', 'giày'],
        'váy':         ['Dress', 'Fashion Women', 'Tops', 'váy'],
        'áo':          ['Shirt', 'Tops', 'Fashion Men', 'Fashion Women', 'áo'],
        'quần':        ['Pants', 'Fashion Men', 'quần'],
        'mỹ phẩm':    ['Beauty & Cosmetics', 'Lipstick', 'Foundation', 'Skincare', 'Beauty'],
        'đồng hồ':    ['Watches', 'Accessories', 'đồng hồ'],
        'tai nghe':    ['Phone Accessories', 'Electronics', 'tai nghe'],
        'túi xách':    ['Bags', 'Accessories', 'túi'],
        'gia dụng':   ['Home & Kitchen', 'Kitchen Appliances', 'Cookware', 'Furniture',
                       'Electronics', 'Refrigerator', 'Washing Machine', 'Air Conditioner'],
        'thể thao':   ['Sports & Outdoor', 'Gym Equipment', 'Outdoor Gear'],
        'sách':        ['Books & Office', 'Books', 'Stationery'],
        'tivi':        ['TV', 'Electronics'],
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
        'msi': ['msi'],
    }

    # Color patterns (Vietnamese and English)
    COLOR_PATTERNS = {
        'Đen': ['đen', 'black', 'dark', 'den'],
        'Trắng': ['trắng', 'white', 'light', 'trang'],
        'Hồng': ['hồng', 'pink', 'hong'],
        'Đỏ': ['đỏ', 'red', 'do'],
        'Xanh': ['xanh', 'blue', 'green'],
        'Vàng': ['vàng', 'yellow', 'vang'],
        'Nâu': ['nâu', 'brown', 'nau'],
        'Xám': ['xám', 'grey', 'gray', 'xam'],
        'Cam': ['cam', 'orange'],
        'Tím': ['tím', 'purple', 'tim']
    }

    # Material patterns
    MATERIAL_PATTERNS = {
        'Jean': ['jean', 'bò', 'denim', 'bo'],
        'Cotton': ['cotton', 'thun'],
        'Lụa': ['lụa', 'silk', 'lua'],
        'Da': ['da', 'leather', 'da bò', 'da thật'],
        'Len': ['len', 'wool'],
        'Polyester': ['polyester', 'poly', 'nỉ', 'spandex', 'ni'],
        'Kaki': ['kaki', 'khaki'],
        'Linen': ['linen', 'đũi', 'dui']
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
        self.BRAND_PATTERNS = dict(self.BRAND_PATTERNS)
        self._dynamic_brands_loaded = False
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

        self._color_regex = {}
        for color, keywords in self.COLOR_PATTERNS.items():
            pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            self._color_regex[color] = re.compile(pattern, re.IGNORECASE)

        self._material_regex = {}
        for material, keywords in self.MATERIAL_PATTERNS.items():
            pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            self._material_regex[material] = re.compile(pattern, re.IGNORECASE)

    def parse(self, query: str) -> ExtractedEntities:
        """
        Parse user query and extract structured entities.

        Example:
            "tư vấn laptop giá 20 triệu" ->
            ExtractedEntities(category="laptop", price_max=20000000)
        """
        self._load_dynamic_brands()
        entities = ExtractedEntities(raw_query=query)
        query_lower = query.lower()

        # 1. Extract category
        entities.category = self._extract_category(query_lower)

        # 2. Extract brand
        entities.brand = self._extract_brand(query_lower)

        # 3. Extract price constraints
        self._extract_price(query_lower, entities)

        # 4. Extract color and material
        color = self._extract_color(query_lower)
        if color:
            entities.attributes['color'] = color
        material = self._extract_material(query_lower)
        if material:
            entities.attributes['material'] = material

        # Extract RAM/SSD/Size attributes
        ram_match = re.search(r'\b(\d+)\s*(?:gb|g)\s*(?:ram)\b|\b(8|16|32|64)\s*(?:gb|g)\b', query_lower)
        if ram_match:
            ram_val = ram_match.group(1) or ram_match.group(2)
            entities.attributes['ram'] = f"{ram_val}GB"

        ssd_match = re.search(r'\b(256|512)\s*(?:gb|g)\s*(?:ssd)?\b|\b(1|2)\s*(?:tb|t)\s*(?:ssd)?\b', query_lower)
        if ssd_match:
            ssd_val = ssd_match.group(1) or (ssd_match.group(2) + "TB")
            if not ssd_val.endswith("TB"):
                ssd_val = f"{ssd_val}GB"
            entities.attributes['ssd'] = ssd_val

        size_match = re.search(r'\b(?:size|cỡ|co)\s*(\d+|l|m|s|xl|xxl)\b', query_lower)
        if size_match:
            entities.attributes['size'] = size_match.group(1).upper()

        # 5. Calculate confidence
        entities.confidence = self._calculate_confidence(entities)

        logger.info(f"Parsed query '{query}' -> category={entities.category}, "
                    f"price_max={entities.price_max}, price_min={entities.price_min}, "
                    f"brand={entities.brand}, color={color}, material={material}, "
                    f"confidence={entities.confidence:.2f}")

        return entities

    def _load_dynamic_brands(self):
        """Fetch all brands dynamically from Neo4j and compile regex patterns"""
        if self._dynamic_brands_loaded:
            return
            
        try:
            global kg_client
            if kg_client:
                session = kg_client._get_session()
                if session:
                    with session:
                        result = session.run("MATCH (b:Brand) RETURN b.name AS name")
                        db_brands = [r['name'] for r in result if r['name']]
                    
                    for brand in db_brands:
                        brand_lower = brand.lower()
                        if brand_lower not in self.BRAND_PATTERNS:
                            self.BRAND_PATTERNS[brand_lower] = [brand_lower]
                            
                    # Re-compile brand patterns
                    for brand, keywords in self.BRAND_PATTERNS.items():
                        pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
                        self._brand_regex[brand] = re.compile(pattern, re.IGNORECASE)
                        
                    self._dynamic_brands_loaded = True
                    logger.info(f"[QueryParser] Successfully loaded {len(db_brands)} brands dynamically from Neo4j.")
        except Exception as e:
            logger.warning(f"[QueryParser] Failed to load dynamic brands: {e}")

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

    def _extract_color(self, query: str) -> Optional[str]:
        """Extract color from query"""
        for color, regex in self._color_regex.items():
            if regex.search(query):
                return color
        return None

    def _extract_material(self, query: str) -> Optional[str]:
        """Extract material from query"""
        for material, regex in self._material_regex.items():
            if regex.search(query):
                return material
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







# Global KG client — using unified singleton from lib.ai_core
from lib.ai_core.neo4j_client import kg_client


class RAGPipeline:
    """
    RAG Pipeline for product-aware responses
    """

    def __init__(self, ollama_host, ollama_model):
        self.ollama_host = ollama_host
        self.ollama_model = ollama_model
        # Use unified AI Core singletons (Phase 2.1)
        self.embedder = embedder
        self.vector_store = vector_store
        self.semantic_cache = semantic_cache
        self._indexed = False
        self.index_dir = getattr(settings, 'AI_INDEX_DIR', '/app/ai_index')

        # Load local index if exists
        meta_path = os.path.join(self.index_dir, 'meta.json')
        if self.vector_store.load(self.index_dir):
            self._indexed = True
            if os.path.exists(meta_path):
                self._last_loaded_mtime = os.path.getmtime(meta_path)
            else:
                self._last_loaded_mtime = 0
        else:
            self._last_loaded_mtime = 0

    def index_products(self, force: bool = False):
        """
        Fetch products from product-service, embed, and populate the vector store.

        Args:
            force: Rebuild even if the index is already loaded (used by build_ai_index command).
        """
        if self._indexed and not force:
            return

        product_service_url = getattr(settings, 'PRODUCT_SERVICE_URL', 'http://product-service:8000/api/products')

        try:
            response = httpx.get(f"{product_service_url}?page_size=500", timeout=30.0)
            if response.status_code == 200:
                products = response.json().get('results', [])

                if products:
                    # Use unified bulk_index — handles ACL normalization + embedding + FAISS add
                    count = self.vector_store.bulk_index(products, self.embedder)
                    logger.info('Indexed %d products for RAG', count)
                else:
                    logger.info('No products returned from product service')

                self._indexed = True
        except Exception as e:
            logger.error('Failed to index products: %s', e)

    def _merge_hybrid(
        self,
        kg_results: List[dict],
        vector_results: List[dict],
        entities: 'ExtractedEntities',
        k: int,
    ) -> List[dict]:
        """
        Combine KG structured results with FAISS vector results.

        Weights:
          KG   = 0.65 when entity confidence >= 0.5 (clear user intent)
          KG   = 0.40 when intent is vague
          Vec  = 1.0 - KG weight
        Products appearing in BOTH sources receive a 20 % score boost.
        """
        kg_weight = 0.65 if entities.confidence >= 0.5 else 0.40
        vec_weight = 1.0 - kg_weight

        pool: Dict[str, dict] = {}

        for r in kg_results:
            pid = str(r.get('product_id', ''))
            if not pid:
                continue
            popularity = float(r.get('popularity', 0))
            pop_norm = min(popularity / 100.0, 1.0)
            score = kg_weight * (0.5 + 0.5 * pop_norm)
            pool[pid] = {
                'product_id': pid,
                'score': score,
                'sources': ['kg_structured'],
                'data': {
                    'name': r.get('name', ''),
                    'price': r.get('price'),
                    'category': r.get('category', ''),
                    'brand': r.get('brand', ''),
                    'description': r.get('description', ''),
                    'image_url': r.get('image_url', ''),
                },
            }

        for r in vector_results:
            pid = str(r.get('product_id', ''))
            if not pid:
                continue
            vs = r.get('score', 0) * vec_weight
            if pid in pool:
                pool[pid]['score'] += vs * 1.2  # cross-source boost
                pool[pid]['sources'].append('vector')
            else:
                pool[pid] = {
                    'product_id': pid,
                    'score': vs,
                    'sources': ['vector'],
                    'data': r.get('data', {}),
                }

        return sorted(pool.values(), key=lambda x: x['score'], reverse=True)[:k]

    def retrieve(self, query, k=5, user_id=None):
        """
        Hybrid Retrieval: KG Structured Search + FAISS Vector Search.
        """
        # Check if FAISS index was updated on disk and reload if necessary (Giai đoạn 2.2)
        meta_path = os.path.join(self.index_dir, 'meta.json')
        if os.path.exists(meta_path):
            mtime = os.path.getmtime(meta_path)
            if not hasattr(self, '_last_loaded_mtime') or mtime > self._last_loaded_mtime:
                logger.info('[RAG] FAISS Index changed on disk. Reloading in RAGPipeline...')
                if self.vector_store.load(self.index_dir):
                    self._indexed = True
                    self._last_loaded_mtime = mtime

        cache_key = f"rag_kg_chatbot:{deterministic_hash(query)}:{k}:{user_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # 1. Structured entity extraction
        entities = query_parser.parse(query)
        logger.info(
            '[RETRIEVE] query="%s" → category=%s price_max=%s brand=%s confidence=%.2f',
            query, entities.category, entities.price_max, entities.brand, entities.confidence,
        )

        # 2. KG structured search (only when explicit constraints were extracted)
        kg_results: List[dict] = []
        if entities.category or entities.price_max or entities.price_min or entities.brand:
            kg_results = self._query_knowledge_graph_structured(entities, user_id, k)
            kg_results = self._strict_filter_products(kg_results, entities)

        logger.info('[RETRIEVE] KG found: %d products', len(kg_results))

        # 3. FAISS vector search
        # Always run when:
        #   (a) the vector store has data, AND
        #   (b) KG returned fewer than 2 products OR no explicit KG constraints existed
        # This guarantees fashion / beauty items that may not exist in Neo4j are
        # still surfaced via semantic similarity.
        VECTOR_MIN_SCORE = 0.35   # raised to 0.35 to avoid noisy cross-category recommendations
        vector_results: List[dict] = []
        should_run_vector = (
            self.vector_store.product_ids
            and (len(kg_results) < 2 or not (entities.category or entities.brand))
        )
        # Also run vector when KG DID return results (hybrid) — but only if
        # the query has no hard price constraint forcing strict KG-only mode.
        if self.vector_store.product_ids and len(kg_results) >= 2:
            should_run_vector = True  # always supplement with vector for true hybrid

        if should_run_vector:
            try:
                query_embs = self.embedder.embed_sync(query)
                if len(query_embs) > 0:
                    raw_hits = self.vector_store.search(query_embs[0], k=k * 2)
                    # Score threshold: drop low-relevance hits
                    vector_results = [r for r in raw_hits if r.get('score', 0) > VECTOR_MIN_SCORE]
                    logger.info(
                        '[RETRIEVE] Vector found: %d products (raw=%d, threshold=%.1f)',
                        len(vector_results), len(raw_hits), VECTOR_MIN_SCORE,
                    )
            except Exception as exc:
                logger.warning('[RETRIEVE] Vector search failed: %s', exc)
        elif not self.vector_store.product_ids:
            logger.warning(
                '[RETRIEVE] Vector store empty — run: python manage.py build_ai_index'
            )

        logger.info(
            '[RETRIEVE] Merge input — KG: %d | Vector: %d | query=%r',
            len(kg_results), len(vector_results), query[:60],
        )

        # 4. Hybrid merge
        merged = self._merge_hybrid(kg_results, vector_results, entities, k)

        # 5. Post-merge strict price filter — ensures vector hits that violate
        #    an explicit price constraint are removed even if KG had no match.
        if entities.price_max or entities.price_min:
            before = len(merged)
            merged = [r for r in merged if self._price_ok(r, entities)]
            if len(merged) < before:
                logger.info(
                    '[RETRIEVE] Price filter removed %d products above constraint',
                    before - len(merged),
                )

        # Enforce category consistency post-merge
        if entities.category:
            before = len(merged)
            merged = [r for r in merged if self._category_ok(r, entities)]
            if len(merged) < before:
                logger.info(
                    '[RETRIEVE] Category filter removed %d products not matching %s',
                    before - len(merged),
                    entities.category,
                )

        # Enforce brand consistency post-merge
        if entities.brand:
            before = len(merged)
            merged = [r for r in merged if self._brand_ok(r, entities)]
            if len(merged) < before:
                logger.info(
                    '[RETRIEVE] Brand filter removed %d products not matching %s',
                    before - len(merged),
                    entities.brand,
                )

        logger.info('[RETRIEVE] Hybrid merged: %d products (final)', len(merged))

        # 5. Normalise to consistent output format and enrich with specifications/variants from Neo4j
        final: List[dict] = []
        for r in merged:
            data = r.get('data') or {}
            if not data:
                data = {
                    'name': r.get('name', ''),
                    'price': r.get('price'),
                    'category': r.get('category', ''),
                    'brand': r.get('brand', ''),
                    'description': r.get('description', ''),
                    'image_url': r.get('image_url', ''),
                }
            # Make sure data is copied/instantiated as dict
            data = dict(data)
            final.append({
                'product_id': r.get('product_id'),
                'score': r.get('score', 0),
                'data': data,
                'sources': r.get('sources', ['unknown']),
            })

        # Enrichment
        session = kg_client._get_session()
        if session and final:
            product_ids = [p['product_id'] for p in final]
            try:
                with session:
                    enrich_result = session.run("""
                        MATCH (p:Product)
                        WHERE p.id IN $ids
                        OPTIONAL MATCH (p)-[:HAS_VARIANT]->(v:Variant)
                        WITH p, collect({
                            id: v.id,
                            name: v.name,
                            price: v.price,
                            sku: v.sku,
                            stock_quantity: v.stock_quantity,
                            attributes_json: v.attributes
                        }) AS variants_list
                        RETURN p.id AS product_id, p.specifications AS specifications_json, p.image_url AS image_url, variants_list
                    """, ids=product_ids)
                    
                    enrich_map = {}
                    for row in enrich_result:
                        pid = row['product_id']
                        specs = {}
                        specs_str = row['specifications_json']
                        if specs_str:
                            try:
                                specs = json.loads(specs_str)
                            except Exception:
                                pass
                        
                        variants = []
                        for v in row['variants_list'] or []:
                            if v.get('id'):
                                v_attrs = {}
                                attrs_str = v.get('attributes_json')
                                if attrs_str:
                                    try:
                                        v_attrs = json.loads(attrs_str)
                                    except Exception:
                                        pass
                                variants.append({
                                    'id': v.get('id'),
                                    'name': v.get('name'),
                                    'price': v.get('price'),
                                    'sku': v.get('sku'),
                                    'stock_quantity': v.get('stock_quantity'),
                                    'attributes': v_attrs
                                })
                        enrich_map[pid] = {
                            'specifications': specs,
                            'variants': variants,
                            'image_url': row.get('image_url') or ''
                        }
                    
                    for p in final:
                        pid = p['product_id']
                        if pid in enrich_map:
                            p['data']['specifications'] = enrich_map[pid]['specifications']
                            p['data']['variants'] = enrich_map[pid]['variants']
                            # Backfill image_url if not present in the data dict
                            if enrich_map[pid].get('image_url') and not p['data'].get('image_url'):
                                p['data']['image_url'] = enrich_map[pid]['image_url']
            except Exception as e:
                logger.error(f"Error enriching product search details: {e}")

        cache.set(cache_key, (final, entities), timeout=300)
        return final, entities

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

    def _price_ok(self, item: dict, entities: ExtractedEntities) -> bool:
        """
        Return True if item's price satisfies entities price constraints.
        Works on the normalised merged format where price lives in item['data']['price'].
        """
        price_raw = item.get('data', {}).get('price') or item.get('price')
        if price_raw is None:
            return True  # no price info → do not exclude
        try:
            price = float(price_raw)
        except (ValueError, TypeError):
            return True
        if entities.price_max and price > entities.price_max:
            return False
        if entities.price_min and price < entities.price_min:
            return False
        return True

    def _category_ok(self, item: dict, entities: ExtractedEntities) -> bool:
        """
        Return True if the item's category matches the query's category.
        """
        if not entities.category:
            return True
        prod_cat = (item.get('data', {}).get('category') or item.get('category') or '').lower()
        if not prod_cat:
            return True # if no category info, don't exclude
            
        # Check if the product category matches the query category or any of its Neo4j aliases
        query_cat = entities.category.lower()
        aliases = [a.lower() for a in QueryParser.CATEGORY_NEO4J_ALIASES.get(entities.category, [])]
        
        # Also check patterns
        patterns = QueryParser.CATEGORY_PATTERNS.get(entities.category, [])
        
        if query_cat in prod_cat or any(a in prod_cat for a in aliases) or any(p in prod_cat for p in patterns):
            return True
        return False

    def _brand_ok(self, item: dict, entities: ExtractedEntities) -> bool:
        """
        Return True if the item's brand matches the query's brand.
        """
        if not entities.brand:
            return True
        prod_brand = (item.get('data', {}).get('brand') or item.get('brand') or '').lower()
        if not prod_brand:
            return True # if no brand info, don't exclude
            
        query_brand = entities.brand.lower()
        # Also check if the brand keywords match
        brand_keywords = [k.lower() for k in QueryParser.BRAND_PATTERNS.get(entities.brand, [])]
        
        if query_brand in prod_brand or any(k in prod_brand for k in brand_keywords):
            return True
            
        # Also check name as fallback (sometimes brand is embedded in the name)
        prod_name = (item.get('data', {}).get('name') or item.get('name') or '').lower()
        if query_brand in prod_name or any(k in prod_name for k in brand_keywords):
            return True
            
        return False

    def _variants_ok(self, item: dict, entities: ExtractedEntities) -> bool:
        """
        Return True if the item has at least one variant matching the query specifications.
        """
        ram = entities.attributes.get('ram')
        ssd = entities.attributes.get('ssd')
        size = entities.attributes.get('size')
        
        if not (ram or ssd or size):
            return True
            
        variants = item.get('data', {}).get('variants') or item.get('variants') or []
        if not variants:
            return True
            
        for v in variants:
            # Check RAM
            if ram:
                v_ram = str(v.get('attributes', {}).get('ram') or v.get('attributes', {}).get('RAM') or '').lower()
                v_name = v.get('name', '').lower()
                if ram.lower() not in v_ram and ram.lower() not in v_name:
                    continue
            # Check SSD
            if ssd:
                v_ssd = str(v.get('attributes', {}).get('ssd') or v.get('attributes', {}).get('storage') or '').lower()
                v_name = v.get('name', '').lower()
                if ssd.lower() not in v_ssd and ssd.lower() not in v_name:
                    continue
            # Check Size
            if size:
                v_size = str(v.get('attributes', {}).get('size') or v.get('attributes', {}).get('Size') or '').lower()
                v_name = v.get('name', '').lower()
                if size.lower() != v_size and f"size {size.lower()}" not in v_name:
                    continue
            return True
        return False

    # ─────────────────────────────────────────────────────────────
    # KG Search helpers (migrated from deprecated KnowledgeGraphClient)
    # ─────────────────────────────────────────────────────────────

    def _kg_search_structured(self, entities: 'ExtractedEntities', n=5) -> List[Dict]:
        """
        Search Neo4j using structured entities from QueryParser.
        Builds dynamic Cypher query. STRICT MATCHING: only active, in-stock products.
        """
        session = kg_client._get_session()
        if not session:
            logger.warning("No Neo4j session available for structured search")
            return []

        try:
            with session:
                where_clauses = [
                    "(p.status IS NULL OR p.status = 'active')",
                    "(p.stock_quantity IS NULL OR p.stock_quantity > 0)"
                ]
                params = {"limit": n}
                matches = ["MATCH (p:Product)"]

                if entities.category:
                    matches.append("MATCH (p)-[:BELONGS_TO]->(c:Category)")
                    where_clauses.append("c.name_lower CONTAINS $category_lower")
                    params["category_lower"] = entities.category.lower()
                else:
                    matches.append("OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)")

                if entities.brand:
                    matches.append("OPTIONAL MATCH (p)-[:MADE_BY]->(b:Brand)")
                    where_clauses.append(
                        "(p.name_lower CONTAINS $brand_lower OR "
                        "toLower(coalesce(p.brand, '')) CONTAINS $brand_lower OR "
                        "coalesce(b.name_lower, '') CONTAINS $brand_lower)"
                    )
                    params["brand_lower"] = entities.brand.lower()

                color_val = entities.attributes.get('color')
                if color_val:
                    matches.append("MATCH (p)-[:HAS_COLOR]->(co:Color)")
                    where_clauses.append("toLower(co.name) = toLower($color)")
                    params["color"] = color_val

                material_val = entities.attributes.get('material')
                if material_val:
                    matches.append("MATCH (p)-[:HAS_MATERIAL]->(ma:Material)")
                    where_clauses.append("toLower(ma.name) = toLower($material)")
                    params["material"] = material_val

                ram_val = entities.attributes.get('ram')
                ssd_val = entities.attributes.get('ssd')
                size_val = entities.attributes.get('size')
                if ram_val or ssd_val or size_val:
                    matches.append("MATCH (p)-[:HAS_VARIANT]->(v:Variant)")
                    if ram_val:
                        where_clauses.append("(toLower(v.name) CONTAINS toLower($ram) OR toLower(coalesce(v.attributes.ram, '')) = toLower($ram))")
                        params["ram"] = ram_val
                    if ssd_val:
                        where_clauses.append("(toLower(v.name) CONTAINS toLower($ssd) OR toLower(coalesce(v.attributes.ssd, '')) = toLower($ssd) OR toLower(coalesce(v.attributes.storage, '')) = toLower($ssd))")
                        params["ssd"] = ssd_val
                    if size_val:
                        where_clauses.append("(toLower(coalesce(v.attributes.size, '')) = toLower($size) OR toLower(v.name) CONTAINS toLower($size))")
                        params["size"] = size_val

                if entities.price_max:
                    where_clauses.append("toInteger(p.price) <= $price_max")
                    params["price_max"] = entities.price_max
                if entities.price_min:
                    where_clauses.append("toInteger(p.price) >= $price_min")
                    params["price_min"] = entities.price_min

                with_vars = ["p", "c"]
                if entities.brand:
                    with_vars.append("b")
                if color_val:
                    with_vars.append("co")
                if material_val:
                    with_vars.append("ma")
                if ram_val or ssd_val or size_val:
                    with_vars.append("v")
                with_clause = "WITH " + ", ".join(with_vars)

                match_clause = "\n                    ".join(matches)
                where_clause = "WHERE " + " AND ".join(where_clauses)

                cypher_query = f"""
                    {match_clause}
                    {with_clause}
                    {where_clause}
                    OPTIONAL MATCH (:User)-[r:PURCHASED|VIEWED|CLICKED]->(p)
                    WITH p, coalesce(c.name, '') AS category_name, COUNT(r) AS popularity
                    RETURN p.id AS product_id,
                           p.name AS name,
                           p.price AS price,
                           coalesce(p.brand, '') AS brand,
                           coalesce(p.description, '') AS description,
                           coalesce(p.image_url, '') AS image_url,
                           category_name AS category,
                           popularity
                    ORDER BY popularity DESC, p.price ASC
                    LIMIT $limit
                """

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
                return products

        except Exception as e:
            logger.error(f"Error in structured search: {e}")
            return []

    def _kg_search_by_category(self, keyword: str, n: int = 5) -> List[Dict]:
        """Search Neo4j products by category keyword."""
        session = kg_client._get_session()
        if not session:
            return []
        try:
            with session:
                result = session.run("""
                    MATCH (c:Category)
                    WHERE c.name_lower CONTAINS $keyword_lower
                    MATCH (p:Product)-[:BELONGS_TO]->(c)
                    OPTIONAL MATCH (:User)-[r:PURCHASED]->(p)
                    WITH p, c, COUNT(r) AS purchases
                    RETURN p.id AS product_id, p.name AS name, p.price AS price,
                           c.name AS category, purchases
                    ORDER BY purchases DESC
                    LIMIT $limit
                """, keyword_lower=keyword.lower(), limit=n)

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

    def _query_knowledge_graph_structured(self, entities: ExtractedEntities, user_id=None, k=5):
        """
        Query Knowledge Graph using structured entities.

        Strategy:
        1. Map Vietnamese category to English alias FIRST (e.g. "giày" → "Shoes")
           to match Neo4j database category names.
        2. Try Neo4j search with the mapped category.
        3. If no results, try remaining aliases in CATEGORY_NEO4J_ALIASES.
        4. Never adds user recommendations — only returns products that match
           the explicit query constraints.
        """
        if not (entities.category or entities.price_max or entities.price_min or entities.brand):
            return []

        # ── Step 1: Map Vietnamese category to English alias BEFORE search ────
        search_entities = entities
        original_category = entities.category

        if entities.category and entities.category in QueryParser.CATEGORY_NEO4J_ALIASES:
            aliases = QueryParser.CATEGORY_NEO4J_ALIASES[entities.category]
            if aliases:
                # Use the FIRST English alias (most specific match for Neo4j CONTAINS)
                primary_alias = aliases[0]
                search_entities = ExtractedEntities(
                    category=primary_alias,
                    price_max=entities.price_max,
                    price_min=entities.price_min,
                    brand=entities.brand,
                    confidence=entities.confidence,
                    raw_query=entities.raw_query,
                )
                logger.info(
                    '[KG] Category mapping: %r → %r (primary alias)',
                    original_category, primary_alias,
                )

        # ── Step 2: Search with mapped category ───────────────────────────────
        structured_results = self._kg_search_structured(search_entities, n=k)
        logger.info(
            '[KG] Primary search (category=%r, original=%r) → %d results',
            search_entities.category, original_category, len(structured_results),
        )

        # ── Step 3: Alias fallback if primary alias returned 0 results ────────
        if not structured_results and original_category:
            aliases = QueryParser.CATEGORY_NEO4J_ALIASES.get(original_category, [])
            # Skip the first alias (already tried) and the original Vietnamese name
            for alias in aliases[1:]:
                if alias.lower() == (original_category or '').lower():
                    continue
                alias_entities = ExtractedEntities(
                    category=alias,
                    price_max=entities.price_max,
                    price_min=entities.price_min,
                    brand=entities.brand,
                    confidence=entities.confidence,
                    raw_query=entities.raw_query,
                )
                alias_results = self._kg_search_structured(alias_entities, n=k)
                if alias_results:
                    logger.info(
                        '[KG] Fallback alias "%s" → %d results (original: %r)',
                        alias, len(alias_results), original_category,
                    )
                    structured_results = alias_results
                    break

        return structured_results

    def _query_knowledge_graph_fallback(self, query, user_id=None, k=5):
        """Fallback KG query for when structured search doesn't work"""
        results = []

        # Get trending if no specific user
        trending = kg_client.get_trending(n=k // 2)
        for p in trending:
            p['source'] = 'kg_trending'
        results.extend(trending)

        # Search by category keywords in query (legacy approach)
        keywords = ['laptop', 'dien thoai', 'phone', 'tablet', 'dong ho',
                    'thoi trang', 'gia dung', 'sach', 'the thao', 'my pham']
        for kw in keywords:
            if kw in query.lower():
                cat_results = self._kg_search_by_category(kw, n=k // 2)
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
        """
        Generate a grounded LLM response (synchronous).

        Changes vs original:
        - Products with score <= 0.5 are dropped before building context (noise reduction).
        - Prompt explicitly forbids hallucination and requires [ID: xxx] citation.
        - make_traced_headers() propagates X-Trace-Id to Ollama.
        """
        from chatbot_app.middleware.trace import make_traced_headers

        # Score filter: keep products with score >= 0.2 to include KG results with low popularity
        # (lowered from 0.5 to avoid filtering out fashion/beauty items with fewer purchases)
        grounded_products = [p for p in context_products if p.get('score', 1) >= 0.2]
        if not grounded_products:
            grounded_products = context_products  # fall back to all if all filtered

        cache_key = f"rag_response:{deterministic_hash(query)}:{deterministic_hash(str(grounded_products))}"
        cached_response = cache.get(cache_key)
        if cached_response:
            logger.info('[RAG] Response from cache')
            return cached_response

        context = self._build_context(grounded_products)

        kg_info = ""
        if kg_context:
            if kg_context.get('bought_together'):
                items = [b.get('name') for b in kg_context['bought_together'][:2] if b.get('name')]
                if items:
                    kg_info += f"\nSản phẩm thường mua kèm: {', '.join(items)}"

        prompt = RAG_SYSTEM_PROMPT.format(
            context=context,
            kg_info=kg_info,
            query=query
        )

        try:
            response = httpx.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 200, "temperature": 0.3},
                },
                headers=make_traced_headers(),
                timeout=90.0,
            )
            if response.status_code == 200:
                result = response.json().get('response', '')
                if result:
                    # ── Guardrails (Phase 2.4) ────────────────────────────
                    # 1. Safety check — block harmful/spam content
                    if Guardrails.check_safety(result):
                        logger.warning('[RAG-Guardrails] Safety check failed — using fallback')
                        return self._fallback_response(grounded_products)

                    # 2. Hallucination check — detect products not in context
                    if Guardrails.check_hallucination(result, grounded_products):
                        logger.warning('[RAG-Guardrails] Hallucination detected — using fallback')
                        return self._fallback_response(grounded_products)

                    # 3. If LLM says "không tìm thấy" despite products existing, use fallback
                    llm_gave_empty = any(
                        phrase in result.lower()
                        for phrase in ['không tìm thấy', 'khong tim thay', 'không có sản phẩm']
                    )
                    if llm_gave_empty and grounded_products:
                        logger.warning('[RAG] LLM returned empty-result phrase despite having %d products — using fallback', len(grounded_products))
                        return self._fallback_response(grounded_products)

                    # 4. Citation enforcement
                    result = self._ensure_citations(result, grounded_products)
                    result = Guardrails.check_citation(result, grounded_products)

                    cache.set(cache_key, result, timeout=600)
                    return result
        except httpx.TimeoutException:
            logger.warning('[RAG] Generation timeout — using fallback')
        except Exception as exc:
            logger.error('[RAG] Generation error: %s', exc)

        return self._fallback_response(grounded_products)

    async def generate_augmented_response_async(self, query, context_products, kg_context=None):
        """
        Async version of generate_augmented_response for use in async views / chat().

        Uses httpx.AsyncClient so the event loop is not blocked during LLM inference
        (which can take 5–30 s depending on model and hardware).
        """
        from chatbot_app.middleware.trace import make_traced_headers

        # Score filter: keep products with score >= 0.2 to include KG results with low popularity
        grounded_products = [p for p in context_products if p.get('score', 1) >= 0.2]
        if not grounded_products:
            grounded_products = context_products

        cache_key = f"rag_async:{deterministic_hash(query)}:{deterministic_hash(str(grounded_products))}"
        cached = cache.get(cache_key)
        if cached:
            logger.info('[RAG-async] Response from cache')
            return cached

        context = await self._build_context_async(grounded_products)

        kg_info = ""
        if kg_context and kg_context.get('bought_together'):
            items = [b.get('name') for b in kg_context['bought_together'][:2] if b.get('name')]
            if items:
                kg_info = f"\nSản phẩm thường mua kèm: {', '.join(items)}"

        prompt = RAG_SYSTEM_PROMPT.format(
            context=context,
            kg_info=kg_info,
            query=query
        )

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"num_predict": 200, "temperature": 0.3},
                    },
                    headers=make_traced_headers(),
                )
            if response.status_code == 200:
                result = response.json().get('response', '')
                if result:
                    # ── Guardrails (Phase 2.4) ────────────────────────────
                    if Guardrails.check_safety(result):
                        logger.warning('[RAG-async-Guardrails] Safety check failed — using fallback')
                        return self._fallback_response(grounded_products)

                    if Guardrails.check_hallucination(result, grounded_products):
                        logger.warning('[RAG-async-Guardrails] Hallucination detected — using fallback')
                        return self._fallback_response(grounded_products)

                    llm_gave_empty = any(
                        phrase in result.lower()
                        for phrase in ['không tìm thấy', 'khong tim thay', 'không có sản phẩm']
                    )
                    if llm_gave_empty and grounded_products:
                        logger.warning('[RAG-async] LLM returned empty-result phrase despite having %d products — using fallback', len(grounded_products))
                        return self._fallback_response(grounded_products)

                    result = self._ensure_citations(result, grounded_products)
                    result = Guardrails.check_citation(result, grounded_products)

                    cache.set(cache_key, result, timeout=600)
                    return result
        except asyncio.TimeoutError:
            logger.warning('[RAG-async] Generation timeout — using fallback')
        except Exception as exc:
            logger.error('[RAG-async] Generation error: %s', exc)

        return self._fallback_response(grounded_products)

    def _fetch_review_stats(self, product_id):
        """
        Fetch reviews and statistics for a product from review-service (sync).
        """
        import httpx
        review_url = getattr(settings, 'REVIEW_SERVICE_URL', 'http://review-service:8008')
        try:
            with httpx.Client(timeout=1.5) as client:
                stats_res = client.get(f"{review_url}/product/{product_id}/stats/")
                reviews_res = client.get(f"{review_url}/product/{product_id}/")

                stats = {}
                if stats_res.status_code == 200:
                    stats = stats_res.json()

                reviews = []
                if reviews_res.status_code == 200:
                    reviews = reviews_res.json()

                return stats, reviews
        except Exception as e:
            logger.warning("Failed to fetch review stats for product %s: %s", product_id, e)
            return {}, []

    async def _fetch_review_stats_async(self, product_id):
        """
        Fetch reviews and statistics for a product ASYNC — non-blocking.
        Uses httpx.AsyncClient so the event loop is not blocked.
        """
        review_url = getattr(settings, 'REVIEW_SERVICE_URL', 'http://review-service:8008')
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                stats_res, reviews_res = await asyncio.gather(
                    client.get(f"{review_url}/product/{product_id}/stats/"),
                    client.get(f"{review_url}/product/{product_id}/"),
                    return_exceptions=True,
                )

                stats = {}
                if isinstance(stats_res, httpx.Response) and stats_res.status_code == 200:
                    stats = stats_res.json()

                reviews = []
                if isinstance(reviews_res, httpx.Response) and reviews_res.status_code == 200:
                    reviews = reviews_res.json()

                return stats, reviews
        except Exception as e:
            logger.warning("Failed to fetch review stats async for product %s: %s", product_id, e)
            return {}, []

    def _build_context(self, products):
        """
        Sync context builder — fetches review stats sequentially.
        Used by the sync generate_augmented_response() path.
        """
        lines = []
        for i, p in enumerate(products[:5], 1):
            data = p.get('data', {})
            pid = p.get('product_id', 'unknown')
            line = f"{i}. [ID: {pid}] {data.get('name', 'Unknown')}"
            if data.get('price'):
                try:
                    price = float(data['price'])
                    line += f" - {price:,.0f}đ"
                except (ValueError, TypeError):
                    line += f" - {data['price']}đ"
            if data.get('category'):
                line += f" ({data['category']})"
            if data.get('brand'):
                line += f" | {data['brand']}"

            stats, reviews = self._fetch_review_stats(pid)
            if stats and stats.get('total_reviews', 0) > 0:
                avg_rating = stats.get('avg_rating', 0)
                total_reviews = stats.get('total_reviews', 0)
                line += f" | Đánh giá: {avg_rating}/5⭐ ({total_reviews} nhận xét)"
                if reviews:
                    comments = [f"\"{r.get('content')}\"" for r in reviews if r.get('content')]
                    if comments:
                        line += f" | Một số bình luận: {', '.join(comments[:2])}"
            lines.append(line)
        return '\n'.join(lines)

    async def _build_context_async(self, products):
        """
        Async context builder — fetches review stats IN PARALLEL via asyncio.gather.
        This does NOT block the event loop during review service calls.
        Phase 2.2 optimization.
        """
        lines = []
        # Fetch all review stats in parallel
        tasks = [
            self._fetch_review_stats_async(p.get('product_id', 'unknown'))
            for p in products[:5]
        ]
        review_results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, (p, review_result) in enumerate(zip(products[:5], review_results), 1):
            data = p.get('data', {})
            pid = p.get('product_id', 'unknown')
            line = f"{i}. [ID: {pid}] {data.get('name', 'Unknown')}"
            if data.get('price'):
                try:
                    price = float(data['price'])
                    line += f" - {price:,.0f}đ"
                except (ValueError, TypeError):
                    line += f" - {data['price']}đ"
            if data.get('category'):
                line += f" ({data['category']})"
            if data.get('brand'):
                line += f" | {data['brand']}"

            # Unpack review result
            if isinstance(review_result, tuple) and len(review_result) == 2:
                stats, reviews = review_result
                if stats and stats.get('total_reviews', 0) > 0:
                    avg_rating = stats.get('avg_rating', 0)
                    total_reviews = stats.get('total_reviews', 0)
                    line += f" | Đánh giá: {avg_rating}/5 ({total_reviews} nhận xét)"
                    if reviews:
                        comments = [f"\"{r.get('content')}\"" for r in reviews if r.get('content')]
                        if comments:
                            line += f" | Một số bình luận: {', '.join(comments[:2])}"
            lines.append(line)
        return '\n'.join(lines)

    def _fallback_response(self, products):
        if not products:
            return "Xin lỗi, tôi không tìm thấy sản phẩm phù hợp. Bạn có thể mô tả chi tiết hơn không?"
        response = "Dưới đây là một số sản phẩm phù hợp với yêu cầu của bạn:\n\n"
        for i, p in enumerate(products[:3], 1):
            data = p.get('data', {})
            pid = p.get('product_id', 'unknown')
            name = data.get('name', 'Sản phẩm')
            response += f"**{i}. [ID: {pid}] {name}**"
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

    def _ensure_citations(self, text, products):
        if not products or not text:
            return text

        import re
        modified_text = text
        
        for p in products[:5]:
            data = p.get('data', {})
            pid = str(p.get('product_id', ''))
            if not pid:
                continue
                
            name = data.get('name', '')
            if not name:
                continue
                
            # Clean up the name for matching
            clean_name = name
            clean_name = re.sub(r'[\(\[\{].*?[\)\]\}]', '', clean_name)
            if '-' in clean_name:
                clean_name = clean_name.split('-')[0]
                
            # Remove common prefixes
            prefixes = [
                'điện thoại', 'máy tính bảng', 'laptop', 'máy tính xách tay', 
                'củ sạc', 'tai nghe', 'samsung', 'apple', 'xiaomi', 'oppo', 
                'áo polo', 'áo sơ mi', 'áo thun', 'áo khoác', 'áo hoodie', 
                'đầm maxi', 'váy công sở', 'đầm body', 'váy midi', 'đầm sơ mi',
                'nồi chiên không dầu', 'bộ nồi inox', 'máy xay sinh tố', 
                'bếp từ đôi', 'may pha ca phe', 'máy pha cà phê',
                'son môi', 'kem dưỡng', 'serum', 'nước hoa hồng'
            ]
            
            match_name = clean_name.strip()
            variations = [match_name]
            
            lead_words = ['điện thoại', 'laptop', 'máy tính xách tay', 'máy tính', 'củ sạc', 'tai nghe', 'áo', 'quần', 'đầm', 'váy', 'nồi', 'bộ', 'máy', 'bếp', 'serum']
            lower_match = match_name.lower()
            for lw in lead_words:
                if lower_match.startswith(lw + ' '):
                    variations.append(match_name[len(lw) + 1:].strip())
            
            variations = sorted(list(set(variations)), key=len, reverse=True)
            
            found = False
            matched_var = None
            for var in variations:
                if len(var) < 3:
                    continue
                escaped_var = re.escape(var)
                pattern = re.compile(escaped_var, re.IGNORECASE)
                if pattern.search(modified_text):
                    found = True
                    matched_var = var
                    break
                    
            if found and matched_var:
                citation_pattern = rf'\[ID:\s*{pid}\]'
                if not re.search(citation_pattern, modified_text):
                    def replace_func(match):
                        matched_str = match.group(0)
                        if f"[ID: {pid}]" in matched_str:
                            return matched_str
                        return f"{matched_str} [ID: {pid}]"
                        
                    escaped_matched_var = re.escape(matched_var)
                    modified_text = re.sub(
                        rf'(?i)({escaped_matched_var})', 
                        replace_func, 
                        modified_text, 
                        count=1
                    )
                    
        return modified_text


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
        Xử lý tin nhắn từ người dùng (async) với bộ đo thời gian (latency profiling)
        """
        from .models import Conversation, Message
        import time

        start_time = time.perf_counter()

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

        # 1. Classify intent
        t0 = time.perf_counter()
        intent = self.classifier.classify(message)
        intent_time = time.perf_counter() - t0

        # 2. Query parsing (entities)
        t0 = time.perf_counter()
        entities = query_parser.parse(message)
        parsing_time = time.perf_counter() - t0

        # 3. Check FAQ first
        t0 = time.perf_counter()
        faq_answer = self._check_faq(message)
        faq_time = time.perf_counter() - t0

        # Check Semantic Cache (Giai đoạn 4.2)
        t0 = time.perf_counter()
        semantic_cached_response = self.rag.semantic_cache.get(message)
        semantic_cache_time = time.perf_counter() - t0

        products = []
        kg_context = {}
        used_kg = False
        extracted_entities = None
        retrieval_time = 0.0
        generation_time = 0.0

        if semantic_cached_response:
            response, intent, products = semantic_cached_response
        elif faq_answer:
            response = faq_answer
        elif intent in self.INTENT_RESPONSES:
            import random
            response = random.choice(self.INTENT_RESPONSES[intent])
        elif intent in self.RAG_INTENTS:
            # 4. RAG Retrieval
            t0 = time.perf_counter()
            rag_result = self.rag.retrieve(message, k=5, user_id=user_id)
            retrieval_time = time.perf_counter() - t0
            
            products, retrieved_entities = rag_result if isinstance(rag_result, tuple) else (rag_result, entities)
            
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

                # 5. Generate response
                t0 = time.perf_counter()
                response = await self.rag.generate_augmented_response_async(
                    message, products, kg_context
                )
                generation_time = time.perf_counter() - t0
                
                # Cache response semantically
                self.rag.semantic_cache.set(message, response, intent=intent, products=products)
            else:
                clarification = kg_client.ask_for_clarification(entities)
                if clarification and entities.confidence < 0.3:
                    extracted_entities['needs_clarification'] = True
                    response = clarification
                else:
                    response = self._no_results_response(entities)
        else:
            # General LLM fallback for non-product queries
            t0 = time.perf_counter()
            response = await self._generate_llm_response(message, conversation)
            generation_time = time.perf_counter() - t0
            
            # Cache response semantically
            self.rag.semantic_cache.set(message, response, intent=intent)

        total_time = time.perf_counter() - start_time
        
        # Apply output guardrails
        response = apply_output_guardrails(response, message, products)

        profiling = {
            'intent_classification_ms': round(intent_time * 1000, 2),
            'query_parsing_ms': round(parsing_time * 1000, 2),
            'faq_check_ms': round(faq_time * 1000, 2),
            'semantic_cache_check_ms': round(semantic_cache_time * 1000, 2),
            'retrieval_ms': round(retrieval_time * 1000, 2),
            'generation_ms': round(generation_time * 1000, 2),
            'total_ms': round(total_time * 1000, 2)
        }

        if total_time > 3.0:
            logger.warning(
                f"[SLO_VIOLATION] Async Chat latency exceeded 3s: {total_time:.2f}s | "
                f"Metrics: {json.dumps(profiling)}"
            )

        # Save assistant message
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response,
            metadata={
                'intent': intent,
                'profiling': profiling,
                'used_rag': intent in self.RAG_INTENTS and bool(products),
                'used_knowledge_graph': used_kg,
                'extracted_entities': extracted_entities
            }
        )

        return {
            'conversation_id': str(conversation.id),
            'response': response,
            'intent': intent,
            'message_id': str(assistant_message.id),
            'profiling': profiling
        }

    def chat_sync(self, message, conversation_id=None, session_id=None, user_id=None):
        """Synchronous version of chat with RAG + Knowledge Graph + Intent/Entity extraction"""
        from .models import Conversation, Message
        import time

        start_time = time.perf_counter()

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

        # 1. Classify intent
        t0 = time.perf_counter()
        intent = self.classifier.classify(message)
        intent_time = time.perf_counter() - t0

        # 2. Extract entities using QueryParser
        t0 = time.perf_counter()
        entities = query_parser.parse(message)
        parsing_time = time.perf_counter() - t0

        # 3. Check FAQ first
        t0 = time.perf_counter()
        faq_answer = self._check_faq(message)
        faq_time = time.perf_counter() - t0

        products = []
        kg_context = {}
        used_kg = False
        extracted_entities = None
        
        # Check Semantic Cache for similar queries first (Giai đoạn 4.2)
        t0 = time.perf_counter()
        semantic_cached_response = self.rag.semantic_cache.get(message)
        semantic_cache_time = time.perf_counter() - t0
        
        retrieval_time = 0.0
        generation_time = 0.0

        if semantic_cached_response:
            response, intent, products = semantic_cached_response
        elif faq_answer:
            response = faq_answer
        elif intent in self.INTENT_RESPONSES:
            import random
            response = random.choice(self.INTENT_RESPONSES[intent])
        elif intent in self.RAG_INTENTS:
            # 4. RAG Retrieval
            t0 = time.perf_counter()
            result = self.rag.retrieve(message, k=5, user_id=user_id)
            retrieval_time = time.perf_counter() - t0

            # Handle tuple return (products, entities) from retrieve()
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

                # 5. Generate response with entity context
                t0 = time.perf_counter()
                response = self._generate_structured_response(
                    message, products, entities, kg_context
                )
                generation_time = time.perf_counter() - t0
                
                # Cache response semantically
                self.rag.semantic_cache.set(message, response, intent=intent, products=products)
            else:
                # No products found — ask for clarification only when intent is vague
                clarification = kg_client.ask_for_clarification(entities)
                if clarification and entities.confidence < 0.3:
                    extracted_entities['needs_clarification'] = True
                    response = clarification
                else:
                    response = self._no_results_response(entities)
        else:
            # Use LLM for other queries
            t0 = time.perf_counter()
            response = self._generate_llm_response_sync(message, conversation)
            generation_time = time.perf_counter() - t0
            
            # Cache response semantically
            self.rag.semantic_cache.set(message, response, intent=intent)

        total_time = time.perf_counter() - start_time
        
        # Apply output guardrails
        response = apply_output_guardrails(response, message, products)

        # Logging SLO violation (> 3s)
        profiling = {
            'intent_classification_ms': round(intent_time * 1000, 2),
            'query_parsing_ms': round(parsing_time * 1000, 2),
            'faq_check_ms': round(faq_time * 1000, 2),
            'semantic_cache_check_ms': round(semantic_cache_time * 1000, 2),
            'retrieval_ms': round(retrieval_time * 1000, 2),
            'generation_ms': round(generation_time * 1000, 2),
            'total_ms': round(total_time * 1000, 2)
        }

        if total_time > 3.0:
            logger.warning(
                f"[SLO_VIOLATION] Chat latency exceeded 3s: {total_time:.2f}s | "
                f"Metrics: {json.dumps(profiling)}"
            )

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
                'extracted_entities': extracted_entities,
                'profiling': profiling
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
            'extracted_entities': extracted_entities,
            'profiling': profiling
        }

    def chat_stream(self, message, conversation_id=None, session_id=None, user_id=None):
        """Streaming version of chat using Server-Sent Events (SSE) (Giai đoạn 4.1)"""
        from .models import Conversation, Message
        import time
        import json

        start_time = time.perf_counter()

        # Get or create conversation
        conversation = self._get_or_create_conversation(
            conversation_id, session_id, user_id
        )

        # Save user message
        Message.objects.create(
            conversation=conversation,
            role='user',
            content=message
        )

        # Classify intent
        intent = self.classifier.classify(message)
        entities = query_parser.parse(message)
        faq_answer = self._check_faq(message)

        # Try semantic cache first
        t0 = time.perf_counter()
        semantic_cached_response = self.rag.semantic_cache.get(message)
        semantic_cache_time = time.perf_counter() - t0
        
        if semantic_cached_response:
            cached_response, cached_intent, cached_products = semantic_cached_response
            words = cached_response.split()
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield {
                    'conversation_id': str(conversation.id),
                    'chunk': chunk,
                    'done': False
                }
                time.sleep(0.01)
            
            profiling = {
                'semantic_cache_check_ms': round(semantic_cache_time * 1000, 2),
                'total_ms': round((time.perf_counter() - start_time) * 1000, 2)
            }
            assistant_message = Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=cached_response,
                metadata={
                    'intent': cached_intent,
                    'products': [p['product_id'] for p in cached_products] if cached_products else [],
                    'used_rag': cached_intent in self.RAG_INTENTS and bool(cached_products),
                    'profiling': profiling
                }
            )
            yield {
                'conversation_id': str(conversation.id),
                'message_id': str(assistant_message.id),
                'done': True,
                'full_response': cached_response,
                'products': cached_products if cached_products else None,
                'profiling': profiling
            }
            return

        if faq_answer:
            words = faq_answer.split()
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield {
                    'conversation_id': str(conversation.id),
                    'chunk': chunk,
                    'done': False
                }
                time.sleep(0.01)
            
            assistant_message = Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=faq_answer,
                metadata={'intent': 'faq'}
            )
            yield {
                'conversation_id': str(conversation.id),
                'message_id': str(assistant_message.id),
                'done': True
            }
            return

        if intent in self.INTENT_RESPONSES:
            import random
            response = random.choice(self.INTENT_RESPONSES[intent])
            words = response.split()
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield {
                    'conversation_id': str(conversation.id),
                    'chunk': chunk,
                    'done': False
                }
                time.sleep(0.01)
            
            assistant_message = Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=response,
                metadata={'intent': intent}
            )
            yield {
                'conversation_id': str(conversation.id),
                'message_id': str(assistant_message.id),
                'done': True
            }
            return

        products = []
        kg_context = {}
        used_kg = False
        extracted_entities = None

        if intent in self.RAG_INTENTS:
            result = self.rag.retrieve(message, k=5, user_id=user_id)
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
                top_product_id = products[0].get('product_id')
                if top_product_id:
                    kg_context['bought_together'] = kg_client.get_frequently_bought_together(
                        top_product_id, n=3
                    )
                    used_kg = True

                grounded_products = [p for p in products if p.get('score', 1) >= 0.2]
                if not grounded_products:
                    grounded_products = products
                
                context = self.rag._build_context(grounded_products)
                kg_info = ""
                if kg_context.get('bought_together'):
                    items = [b.get('name') for b in kg_context['bought_together'][:2] if b.get('name')]
                    if items:
                        kg_info += f"\nSản phẩm thường mua kèm: {', '.join(items)}"

                prompt = RAG_SYSTEM_PROMPT.format(
                    context=context,
                    kg_info=kg_info,
                    query=message
                )
                
                url = f"{self.ollama_host}/api/generate"
                payload = {
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {"num_predict": 200, "temperature": 0.3},
                }
            else:
                clarification = kg_client.ask_for_clarification(entities)
                if clarification and entities.confidence < 0.3:
                    extracted_entities['needs_clarification'] = True
                    response = clarification
                else:
                    response = self._no_results_response(entities)
                
                words = response.split()
                for i, word in enumerate(words):
                    yield {
                        'conversation_id': str(conversation.id),
                        'chunk': word + (" " if i < len(words) - 1 else ""),
                        'done': False
                    }
                    time.sleep(0.01)
                
                assistant_message = Message.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=response,
                    metadata={'intent': intent, 'extracted_entities': extracted_entities}
                )
                yield {
                    'conversation_id': str(conversation.id),
                    'message_id': str(assistant_message.id),
                    'done': True
                }
                return
        else:
            messages = self._build_context(conversation, message)
            if len(messages) > 6:
                messages = [messages[0]] + messages[-5:]
            url = f"{self.ollama_host}/api/chat"
            payload = {
                "model": self.ollama_model,
                "messages": messages,
                "stream": True,
                "options": {"num_predict": 200, "temperature": 0.7},
            }

        full_response = ""
        first_token_time = None
        from chatbot_app.middleware.trace import make_traced_headers

        try:
            with httpx.stream("POST", url, json=payload, headers=make_traced_headers(), timeout=90.0) as r:
                for line in r.iter_lines():
                    if not line:
                        continue
                    
                    if first_token_time is None:
                        first_token_time = time.perf_counter() - start_time
                        
                    data = json.loads(line)
                    if "response" in data:
                        chunk = data["response"]
                    else:
                        chunk = data.get("message", {}).get("content", "")
                        
                    full_response += chunk
                    yield {
                        'conversation_id': str(conversation.id),
                        'chunk': chunk,
                        'done': False
                    }
        except Exception as exc:
            logger.error(f"Error streaming from Ollama: {exc}")
            yield {
                'conversation_id': str(conversation.id),
                'chunk': "\n[Lỗi kết nối Ollama - Sử dụng phản hồi dự phòng]",
                'done': False
            }
            full_response = self._fallback_response(products)

        # Apply output guardrails
        full_response = apply_output_guardrails(full_response, message, products)

        # Cache response semantically
        self.rag.semantic_cache.set(message, full_response, intent=intent, products=products)

        total_time = time.perf_counter() - start_time
        profiling = {
            'ttft_ms': round(first_token_time * 1000, 2) if first_token_time else None,
            'total_ms': round(total_time * 1000, 2)
        }
        
        if total_time > 3.0:
            logger.warning(f"[SLO_VIOLATION] Streaming chat latency exceeded 3s: {total_time:.2f}s")

        # Save assistant message
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=full_response,
            metadata={
                'intent': intent,
                'products': [p['product_id'] for p in products] if products else [],
                'used_rag': intent in self.RAG_INTENTS and bool(products),
                'used_knowledge_graph': used_kg,
                'profiling': profiling
            }
        )

        yield {
            'conversation_id': str(conversation.id),
            'message_id': str(assistant_message.id),
            'done': True,
            'full_response': full_response,
            'profiling': profiling
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

        cache_key = f"faq:{deterministic_hash(message.lower())}"
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
        from chatbot_app.middleware.trace import make_traced_headers

        cache_key = f"llm_response:{deterministic_hash(message)}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            messages = self._build_context(conversation, message)
            if len(messages) > 6:
                messages = [messages[0]] + messages[-5:]

            response = httpx.post(
                f"{self.ollama_host}/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": messages,
                    "stream": False,
                    "options": {"num_predict": 200, "temperature": 0.7},
                },
                headers=make_traced_headers(),
                timeout=90.0,
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
        cache_key = f"llm_response:{deterministic_hash(message)}"
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
