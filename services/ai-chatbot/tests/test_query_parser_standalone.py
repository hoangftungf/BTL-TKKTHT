"""
Standalone Tests for QueryParser - Intent Detection and Entity Extraction
No Django or external dependencies required.
"""
import re
from typing import Dict, Optional, Any
from dataclasses import dataclass, field


# ===================== COPY OF CORE LOGIC FOR TESTING =====================

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
    """Parse natural language queries into structured data."""

    CATEGORY_PATTERNS = {
        'laptop': ['laptop', 'may tinh xach tay', 'notebook', 'macbook'],
        'dien thoai': ['dien thoai', 'phone', 'smartphone', 'iphone', 'samsung', 'di dong', 'dt'],
        'tablet': ['tablet', 'may tinh bang', 'ipad'],
        'giay': ['giay', 'sneaker', 'boot', 'dep', 'sandal'],
        'ao': ['ao', 'ao so mi', 'ao thun', 'ao khoac', 't-shirt', 'tshirt', 'shirt'],
        'quan': ['quan', 'quan jean', 'quan tay', 'quan short'],
        'my pham': ['my pham', 'son', 'kem', 'serum', 'toner', 'makeup', 'skincare', 'duong da'],
        'dong ho': ['dong ho', 'watch', 'smartwatch', 'apple watch'],
        'tai nghe': ['tai nghe', 'headphone', 'earphone', 'airpod', 'earbud'],
        'tui xach': ['tui', 'tui xach', 'balo', 'ba lo', 'cap', 'handbag'],
        'do gia dung': ['gia dung', 'noi', 'chao', 'may xay', 'may ep', 'quat', 'dieu hoa'],
        'sach': ['sach', 'book', 'truyen', 'tieu thuyet'],
    }

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

    PRICE_PATTERNS = [
        (r'(\d+(?:[.,]\d+)?)\s*(trieu|tr)', 1_000_000),
        (r'(\d+(?:[.,]\d+)?)\s*(k|nghin)', 1_000),
        (r'(\d+(?:[.,]\d+)?)\s*(ty)', 1_000_000_000),
        (r'(\d{6,})\s*(?:d|dong|vnd)?', 1),
    ]

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        self._category_regex = {}
        for cat, keywords in self.CATEGORY_PATTERNS.items():
            pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            self._category_regex[cat] = re.compile(pattern, re.IGNORECASE)

        self._brand_regex = {}
        for brand, keywords in self.BRAND_PATTERNS.items():
            pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            self._brand_regex[brand] = re.compile(pattern, re.IGNORECASE)

    def parse(self, query: str) -> ExtractedEntities:
        entities = ExtractedEntities(raw_query=query)
        query_lower = query.lower()

        entities.category = self._extract_category(query_lower)
        entities.brand = self._extract_brand(query_lower)
        self._extract_price(query_lower, entities)
        entities.confidence = self._calculate_confidence(entities)

        return entities

    def _extract_category(self, query: str) -> Optional[str]:
        for category, regex in self._category_regex.items():
            if regex.search(query):
                return category
        return None

    def _extract_brand(self, query: str) -> Optional[str]:
        for brand, regex in self._brand_regex.items():
            if regex.search(query):
                return brand
        return None

    def _extract_price(self, query: str, entities: ExtractedEntities) -> None:
        # Check for price range first
        range_match = re.search(
            r'(?:tu)\s*(\d+(?:[.,]\d+)?)\s*(trieu|tr|k)?\s*(?:den|toi|-)\s*(\d+(?:[.,]\d+)?)\s*(trieu|tr|k)?',
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

        # Check for max price constraint
        max_patterns = [
            r'(?:duoi|under|toi da|max|khong qua|ko qua)\s*(\d+(?:[.,]\d+)?)\s*(trieu|tr|k|nghin)?',
            r'(?:gia)\s*(?:duoi)\s*(\d+(?:[.,]\d+)?)\s*(trieu|tr|k)?',
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
            r'(?:tren|tu|tro len|above|toi thieu|min)\s*(\d+(?:[.,]\d+)?)\s*(trieu|tr|k)?',
        ]
        for pattern in min_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                value = self._parse_number(match.group(1))
                unit = match.group(2) if match.lastindex >= 2 else 'trieu'
                entities.price_min = int(value * self._get_unit_multiplier(unit))
                return

        # Extract any price mention as approximate max
        for pattern, base_multiplier in self.PRICE_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                value = self._parse_number(match.group(1))
                unit = match.group(2) if match.lastindex >= 2 else None
                multiplier = self._get_unit_multiplier(unit) if unit else base_multiplier
                price = int(value * multiplier)

                if re.search(r'(khoang|tam|around|approximately|~)', query):
                    entities.price_min = int(price * 0.8)
                    entities.price_max = int(price * 1.2)
                else:
                    entities.price_max = price
                return

    def _parse_number(self, num_str: str) -> float:
        num_str = num_str.replace(',', '.').replace(' ', '')
        return float(num_str)

    def _get_unit_multiplier(self, unit: Optional[str]) -> int:
        if not unit:
            return 1_000_000
        unit = unit.lower()
        if unit in ('trieu', 'tr'):
            return 1_000_000
        elif unit in ('k', 'nghin'):
            return 1_000
        elif unit in ('ty',):
            return 1_000_000_000
        return 1

    def _calculate_confidence(self, entities: ExtractedEntities) -> float:
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


class IntentClassifier:
    """Intent classifier for user queries"""

    PRODUCT_KEYWORDS = [
        'laptop', 'dien thoai', 'phone', 'may tinh', 'tablet', 'ipad',
        'giay', 'dep', 'ao', 'quan', 'vay', 'dam', 'tui', 'balo',
        'dong ho', 'watch', 'tai nghe', 'headphone', 'airpod',
        'my pham', 'son', 'kem', 'serum', 'skincare',
        'sach', 'truyen', 'noi', 'chao', 'quat', 'dieu hoa',
        'iphone', 'samsung', 'xiaomi', 'macbook', 'dell', 'asus',
        'nike', 'adidas', 'sony', 'apple'
    ]

    INTENT_PATTERNS = {
        'greeting': [r'\b(chao|hi|hello|hey)\b', r'^(chao|hi|hello)'],
        'product_search': [
            r'\b(tu van|goi y|recommend|de xuat)\b',
            r'\b(tim|search|kiem|muon mua|can mua)\b',
            r'\b(gia)\s*\d+',
            r'\d+\s*(trieu|tr|k|nghin)',
            r'\b(co|ban|co ban)\b.*\b(khong|gi|nao)\b',
            r'\b(mua|can|muon|want)\b',
            r'\b(nao tot|nao hay|nao dep|chon gi)\b',
            r'\b(duoi|under|khoang|tam|around)\s*\d+',
        ],
        'goodbye': [r'\b(tam biet|bye|goodbye|cam on|thank)\b'],
    }

    @classmethod
    def classify(cls, text):
        text_lower = text.lower()

        for keyword in cls.PRODUCT_KEYWORDS:
            if keyword in text_lower:
                if re.search(r'\d+\s*(trieu|tr|k|nghin)?', text_lower) or \
                   re.search(r'(tu van|goi y|tim|mua|co|ban|can|muon)', text_lower):
                    return 'product_search'

        for intent, patterns in cls.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent

        for keyword in cls.PRODUCT_KEYWORDS:
            if keyword in text_lower:
                return 'product_search'

        return 'general'


# ===================== TESTS =====================

def test_laptop_20_trieu():
    """Test: 'tu van laptop gia 20 trieu'"""
    parser = QueryParser()
    entities = parser.parse("tu van laptop gia 20 trieu")

    assert entities.category == "laptop", f"Expected 'laptop', got {entities.category}"
    assert entities.price_max == 20_000_000, f"Expected 20000000, got {entities.price_max}"
    assert entities.confidence >= 0.7, f"Expected confidence >= 0.7, got {entities.confidence}"
    print("[PASS] test_laptop_20_trieu")


def test_phone_15tr():
    """Test: 'tim dien thoai 15tr'"""
    parser = QueryParser()
    entities = parser.parse("tim dien thoai 15tr")

    assert entities.category == "dien thoai", f"Expected 'dien thoai', got {entities.category}"
    assert entities.price_max == 15_000_000, f"Expected 15000000, got {entities.price_max}"
    print("[PASS] test_phone_15tr")


def test_price_range():
    """Test: 'laptop tu 15 den 25 trieu'"""
    parser = QueryParser()
    entities = parser.parse("laptop tu 15 den 25 trieu")

    assert entities.category == "laptop", f"Expected 'laptop', got {entities.category}"
    assert entities.price_min == 15_000_000, f"Expected price_min 15000000, got {entities.price_min}"
    assert entities.price_max == 25_000_000, f"Expected price_max 25000000, got {entities.price_max}"
    print("[PASS] test_price_range")


def test_under_price():
    """Test: 'giay duoi 500k'"""
    parser = QueryParser()
    entities = parser.parse("giay duoi 500k")

    assert entities.category == "giay", f"Expected 'giay', got {entities.category}"
    assert entities.price_max == 500_000, f"Expected 500000, got {entities.price_max}"
    print("[PASS] test_under_price")


def test_brand_detection():
    """Test: 'iPhone 15 gia bao nhieu'"""
    parser = QueryParser()
    entities = parser.parse("iPhone 15 gia bao nhieu")

    assert entities.category == "dien thoai", f"Expected 'dien thoai', got {entities.category}"
    assert entities.brand == "apple", f"Expected 'apple', got {entities.brand}"
    print("[PASS] test_brand_detection")


def test_around_price():
    """Test: 'laptop khoang 20 trieu'"""
    parser = QueryParser()
    entities = parser.parse("laptop khoang 20 trieu")

    assert entities.category == "laptop", f"Expected 'laptop', got {entities.category}"
    assert entities.price_min == 16_000_000, f"Expected price_min 16000000, got {entities.price_min}"
    assert entities.price_max == 24_000_000, f"Expected price_max 24000000, got {entities.price_max}"
    print("[PASS] test_around_price")


def test_no_category_low_confidence():
    """Test: query without category should have low confidence"""
    parser = QueryParser()
    entities = parser.parse("gia 20 trieu")

    assert entities.category is None, f"Expected None, got {entities.category}"
    assert entities.confidence < 0.4, f"Expected confidence < 0.4, got {entities.confidence}"
    print("[PASS] test_no_category_low_confidence")


def test_cosmetics():
    """Test: 'son moi duoi 300k'"""
    parser = QueryParser()
    entities = parser.parse("son moi duoi 300k")

    assert entities.category == "my pham", f"Expected 'my pham', got {entities.category}"
    assert entities.price_max == 300_000, f"Expected 300000, got {entities.price_max}"
    print("[PASS] test_cosmetics")


def test_samsung_galaxy():
    """Test: 'Samsung Galaxy gia 10 trieu'"""
    parser = QueryParser()
    entities = parser.parse("Samsung Galaxy gia 10 trieu")

    assert entities.category == "dien thoai", f"Expected 'dien thoai', got {entities.category}"
    assert entities.brand == "samsung", f"Expected 'samsung', got {entities.brand}"
    assert entities.price_max == 10_000_000, f"Expected 10000000, got {entities.price_max}"
    print("[PASS] test_samsung_galaxy")


def test_macbook():
    """Test: 'macbook pro 30 trieu'"""
    parser = QueryParser()
    entities = parser.parse("macbook pro 30 trieu")

    assert entities.category == "laptop", f"Expected 'laptop', got {entities.category}"
    assert entities.brand == "apple", f"Expected 'apple', got {entities.brand}"
    assert entities.price_max == 30_000_000, f"Expected 30000000, got {entities.price_max}"
    print("[PASS] test_macbook")


def test_intent_product_search():
    """Test product search intent detection"""
    intent = IntentClassifier.classify("tu van laptop gia 20 trieu")
    assert intent == "product_search", f"Expected 'product_search', got {intent}"
    print("[PASS] test_intent_product_search")


def test_intent_greeting():
    """Test greeting intent"""
    intent = IntentClassifier.classify("hello")
    assert intent == "greeting", f"Expected 'greeting', got {intent}"
    print("[PASS] test_intent_greeting")


def test_intent_product_keyword():
    """Test that product keywords trigger product_search"""
    intent = IntentClassifier.classify("dien thoai nao tot")
    assert intent == "product_search", f"Expected 'product_search', got {intent}"
    print("[PASS] test_intent_product_keyword")


def test_intent_goodbye():
    """Test goodbye intent"""
    intent = IntentClassifier.classify("thank you, bye")
    assert intent == "goodbye", f"Expected 'goodbye', got {intent}"
    print("[PASS] test_intent_goodbye")


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("RUNNING QUERY PARSER TESTS")
    print("=" * 60 + "\n")

    tests = [
        test_laptop_20_trieu,
        test_phone_15tr,
        test_price_range,
        test_under_price,
        test_brand_detection,
        test_around_price,
        test_no_category_low_confidence,
        test_cosmetics,
        test_samsung_galaxy,
        test_macbook,
        test_intent_product_search,
        test_intent_greeting,
        test_intent_product_keyword,
        test_intent_goodbye,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__} ERROR: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
