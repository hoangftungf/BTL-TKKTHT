"""
Tests for QueryParser - Intent Detection and Entity Extraction
"""
import sys
import os

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest


class TestQueryParser(unittest.TestCase):
    """Test cases for QueryParser entity extraction"""

    @classmethod
    def setUpClass(cls):
        # Import here to avoid Django setup issues in simple test
        from chatbot_app.engine import QueryParser, ExtractedEntities
        cls.parser = QueryParser()

    def test_laptop_20_trieu(self):
        """Test: 'tư vấn laptop giá 20 triệu'"""
        entities = self.parser.parse("tư vấn laptop giá 20 triệu")

        self.assertEqual(entities.category, "laptop")
        self.assertEqual(entities.price_max, 20_000_000)
        self.assertGreaterEqual(entities.confidence, 0.7)

    def test_phone_15tr(self):
        """Test: 'tìm điện thoại 15tr'"""
        entities = self.parser.parse("tìm điện thoại 15tr")

        self.assertEqual(entities.category, "điện thoại")
        self.assertEqual(entities.price_max, 15_000_000)

    def test_price_range(self):
        """Test: 'laptop từ 15 đến 25 triệu'"""
        entities = self.parser.parse("laptop từ 15 đến 25 triệu")

        self.assertEqual(entities.category, "laptop")
        self.assertEqual(entities.price_min, 15_000_000)
        self.assertEqual(entities.price_max, 25_000_000)

    def test_under_price(self):
        """Test: 'giày dưới 500k'"""
        entities = self.parser.parse("giày dưới 500k")

        self.assertEqual(entities.category, "giày")
        self.assertEqual(entities.price_max, 500_000)

    def test_brand_detection(self):
        """Test: 'iPhone 15 giá bao nhiêu'"""
        entities = self.parser.parse("iPhone 15 giá bao nhiêu")

        self.assertEqual(entities.category, "điện thoại")
        self.assertEqual(entities.brand, "apple")

    def test_around_price(self):
        """Test: 'laptop khoảng 20 triệu'"""
        entities = self.parser.parse("laptop khoảng 20 triệu")

        self.assertEqual(entities.category, "laptop")
        # "khoảng" implies ±20% range
        self.assertEqual(entities.price_min, 16_000_000)
        self.assertEqual(entities.price_max, 24_000_000)

    def test_no_category_asks_clarification(self):
        """Test: query without category should have low confidence"""
        entities = self.parser.parse("giá 20 triệu")

        self.assertIsNone(entities.category)
        self.assertLess(entities.confidence, 0.4)

    def test_cosmetics(self):
        """Test: 'son môi dưới 300k'"""
        entities = self.parser.parse("son môi dưới 300k")

        self.assertEqual(entities.category, "mỹ phẩm")
        self.assertEqual(entities.price_max, 300_000)

    def test_samsung_galaxy(self):
        """Test: 'Samsung Galaxy giá 10 triệu'"""
        entities = self.parser.parse("Samsung Galaxy giá 10 triệu")

        self.assertEqual(entities.category, "điện thoại")
        self.assertEqual(entities.brand, "samsung")
        self.assertEqual(entities.price_max, 10_000_000)

    def test_macbook(self):
        """Test: 'macbook pro 30 triệu'"""
        entities = self.parser.parse("macbook pro 30 triệu")

        self.assertEqual(entities.category, "laptop")
        self.assertEqual(entities.brand, "apple")
        self.assertEqual(entities.price_max, 30_000_000)


class TestIntentClassifier(unittest.TestCase):
    """Test cases for IntentClassifier"""

    @classmethod
    def setUpClass(cls):
        from chatbot_app.engine import IntentClassifier
        cls.classifier = IntentClassifier

    def test_product_search_with_price(self):
        """Test product search intent detection"""
        intent = self.classifier.classify("tư vấn laptop giá 20 triệu")
        self.assertEqual(intent, "product_search")

    def test_greeting(self):
        """Test greeting intent"""
        intent = self.classifier.classify("xin chào")
        self.assertEqual(intent, "greeting")

    def test_product_keyword_triggers_search(self):
        """Test that product keywords trigger product_search"""
        intent = self.classifier.classify("điện thoại nào tốt")
        self.assertEqual(intent, "product_search")

    def test_goodbye(self):
        """Test goodbye intent"""
        intent = self.classifier.classify("cảm ơn, tạm biệt")
        self.assertEqual(intent, "goodbye")


if __name__ == '__main__':
    # Setup minimal Django settings for import
    import django
    from django.conf import settings as django_settings

    if not django_settings.configured:
        django_settings.configure(
            DEBUG=True,
            DATABASES={},
            INSTALLED_APPS=[],
            CACHES={
                'default': {
                    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                }
            },
            OLLAMA_HOST='http://localhost:11434',
            OLLAMA_MODEL='llama3.2',
        )

    unittest.main(verbosity=2)
