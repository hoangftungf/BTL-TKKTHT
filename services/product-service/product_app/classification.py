"""
Product Classification Module for AI/Recommendation System

Provides intelligent product classification based on product name and description.
Uses pattern matching with priority-based rules.

Usage:
    from product_app.classification import ProductClassifier

    classifier = ProductClassifier()
    result = classifier.classify("MacBook Pro M3 14 inch")
    print(result)  # {'category_slug': 'laptop', 'confidence': 0.95, ...}
"""

import re
from typing import Optional
from dataclasses import dataclass


@dataclass
class ClassificationResult:
    """Result of product classification"""
    category_slug: Optional[str]
    confidence: float
    matched_pattern: Optional[str]
    parent_category: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'category_slug': self.category_slug,
            'confidence': self.confidence,
            'matched_pattern': self.matched_pattern,
            'parent_category': self.parent_category
        }


class ProductClassifier:
    """
    Intelligent product classifier using pattern matching rules.

    Classifies products into hierarchical categories for e-commerce AI systems.
    """

    # Category hierarchy mapping (child -> parent)
    CATEGORY_HIERARCHY = {
        'tv': 'electronics',
        'refrigerator': 'electronics',
        'washing-machine': 'electronics',
        'air-conditioner': 'electronics',
        'laptop': 'computers',
        'desktop-pc': 'computers',
        'components': 'computers',
        'smartphone': 'phones-tablets',
        'tablet': 'phones-tablets',
        'phone-accessories': 'phones-tablets',
        'shirt-men': 'fashion-men',
        'pants-men': 'fashion-men',
        'shoes-men': 'fashion-men',
        'dress': 'fashion-women',
        'tops-women': 'fashion-women',
        'heels': 'fashion-women',
        'lipstick': 'beauty-cosmetics',
        'foundation': 'beauty-cosmetics',
        'skincare': 'beauty-cosmetics',
        'cookware': 'home-kitchen',
        'kitchen-appliances': 'home-kitchen',
        'furniture': 'home-kitchen',
        'gym-equipment': 'sports-outdoor',
        'outdoor-gear': 'sports-outdoor',
        'watches': 'accessories',
        'bags': 'accessories',
        'books': 'books-office',
        'stationery': 'books-office',
    }

    # Classification rules with priority
    RULES = [
        # Smartphones
        {
            'patterns': [
                r'\biphone\s*\d', r'\biphone\b', r'\bsamsung\s*galaxy\s*(s|a|z|note|fold)\d',
                r'\bxiaomi\b', r'\boppo\b', r'\bvivo\b', r'\brealme\b', r'\bpixel\b',
                r'\boneplus\b', r'\bredmi\b', r'\bhuawei\s*(p|mate|nova)\b', r'\bnote\s*\d+\s*pro'
            ],
            'category': 'smartphone',
            'priority': 100
        },
        # Laptops
        {
            'patterns': [
                r'\bmacbook\b', r'\blaptop\b', r'\bnotebook\b',
                r'\b(dell|asus|hp|lenovo|acer|msi)\s*(inspiron|vivobook|pavilion|thinkpad|aspire|ideapad|rog|zenbook|gaming|xps|spectre|envy)\b',
                r'\bcore\s*i[357]\b.*\b(laptop|notebook)\b',
                r'\bdell\s*xps\b', r'\bhp\s*(spectre|envy|omen)\b', r'\basus\s*(zenbook|vivobook)\b',
                r'\bcore\s*i[3579]\b.*\b(dell|hp|asus|lenovo)\b',
            ],
            'category': 'laptop',
            'priority': 95
        },
        # Tablets
        {
            'patterns': [
                r'\bipad\s*(pro|air|mini)?\b', r'\btablet\b', r'\bgalaxy\s*tab\b',
                r'\bsurface\s*(pro|go)\b', r'\bmi\s*pad\b', r'\bmatrix\s*pad\b'
            ],
            'category': 'tablet',
            'priority': 90
        },
        # Desktop PC
        {
            'patterns': [
                r'\bdesktop\b', r'\bpc\s*(gaming|workstation)?\b', r'\bmay\s*tinh\s*ban\b',
                r'\bimac\b', r'\bmac\s*(mini|studio|pro)\b', r'\bcase\s*pc\b'
            ],
            'category': 'desktop-pc',
            'priority': 88
        },
        # Watches & Smartwatches
        {
            'patterns': [
                r'\b(smart)?watch\b', r'\bdong\s*ho\b', r'\bđồng\s*hồ\b',
                r'\bapple\s*watch\b', r'\bgalaxy\s*watch\b', r'\bgarmin\b',
                r'\bfitbit\b', r'\bamazfit\b', r'\bhuawei\s*watch\b'
            ],
            'category': 'watches',
            'priority': 85
        },
        # Phone Accessories
        {
            'patterns': [
                r'\bairpods\b', r'\bearbuds\b', r'\btai\s*nghe\b', r'\bheadphone\b',
                r'\bsac\s*(du\s*phong|nhanh|khong\s*day)?\b', r'\bcharger\b',
                r'\bop\s*lung\b', r'\bcase\b', r'\bphu\s*kien\b', r'\bscreen\s*protector\b'
            ],
            'category': 'phone-accessories',
            'priority': 80
        },
        # TV (only match explicit TV mentions)
        {
            'patterns': [
                r'\btivi\b', r'\btelevision\b', r'\bsmart\s*tv\b',
                r'\b(oled|qled|neo\s*qled|mini\s*led)\s*tv\b',
                r'\b(samsung|lg|sony|tcl)\b.*\b\d{2,3}\s*inch\s*(tv|tivi)\b'
            ],
            'category': 'tv',
            'priority': 75
        },
        # Kitchen Appliances
        {
            'patterns': [
                r'\bnoi\s*(chien|com|ap\s*suat)\b', r'\bnồi\b', r'\bbep\s*(tu|gas|hong\s*ngoai)\b',
                r'\bmay\s*(xay|ep|pha|rua\s*bat)\b', r'\bair\s*fryer\b', r'\blo\s*(vi\s*song|nuong)\b',
                r'\bblender\b', r'\bcoffee\s*maker\b', r'\bmay\s*pha\s*ca\s*phe\b',
                r'\b(philips|delonghi|vitamix|fissler|bosch)\b.*\b(may|noi|bep)\b'
            ],
            'category': 'kitchen-appliances',
            'priority': 70
        },
        # Refrigerator
        {
            'patterns': [
                r'\btu\s*lanh\b', r'\btủ\s*lạnh\b', r'\brefrigerator\b', r'\bfreezer\b',
                r'\b(samsung|lg|panasonic|hitachi)\b.*\b(inverter|side\s*by\s*side)\b'
            ],
            'category': 'refrigerator',
            'priority': 68
        },
        # Washing Machine
        {
            'patterns': [
                r'\bmay\s*giat\b', r'\bmáy\s*giặt\b', r'\bwashing\s*machine\b',
                r'\bdryer\b', r'\bmay\s*say\b', r'\bcua\s*(truoc|ngang)\b'
            ],
            'category': 'washing-machine',
            'priority': 66
        },
        # Air Conditioner
        {
            'patterns': [
                r'\bdieu\s*hoa\b', r'\bđiều\s*hòa\b', r'\bair\s*conditioner\b',
                r'\bmay\s*lanh\b', r'\binverter\b.*\btu\b'
            ],
            'category': 'air-conditioner',
            'priority': 64
        },
        # Men's Shirts
        {
            'patterns': [
                r'\bao\s*(so\s*mi|hoodie|khoac|polo|thun)\b.*\bnam\b',
                r'\báo\b.*\bnam\b', r'\b(shirt|hoodie|jacket|polo)\b.*\b(men|nam)\b',
                r'\bnam\b.*\b(ao|shirt)\b'
            ],
            'category': 'shirt-men',
            'priority': 60
        },
        # Men's Pants
        {
            'patterns': [
                r'\bquan\s*(jean|kaki|short|dai|tay)\b.*\bnam\b',
                r'\bquần\b.*\bnam\b', r'\b(jean|jeans|pants|trouser)\b.*\b(men|nam)\b',
                r'\bnam\b.*\b(quan|pants|jean)\b'
            ],
            'category': 'pants-men',
            'priority': 58
        },
        # Men's Shoes
        {
            'patterns': [
                r'\bgiay\b.*\bnam\b', r'\bgiày\b.*\bnam\b',
                r'\b(sneaker|oxford|loafer|boot)\b.*\b(men|nam)\b',
                r'\b(nike|adidas|puma|converse|vans)\b.*\b(nam|men|giay)\b'
            ],
            'category': 'shoes-men',
            'priority': 56
        },
        # Women's Dress
        {
            'patterns': [
                r'\bdam\b', r'\bđầm\b', r'\bvay\b', r'\bváy\b', r'\bdress\b',
                r'\bskirt\b', r'\bmaxi\b', r'\bmidi\b', r'\ba-line\b', r'\bbodycon\b'
            ],
            'category': 'dress',
            'priority': 55
        },
        # Women's Tops
        {
            'patterns': [
                r'\bao\b.*\bnu\b', r'\báo\b.*\bnữ\b',
                r'\b(blouse|croptop|tank\s*top)\b', r'\b(women|nu)\b.*\b(shirt|ao|top)\b'
            ],
            'category': 'tops-women',
            'priority': 53
        },
        # Women's Heels
        {
            'patterns': [
                r'\bgiay\s*cao\s*got\b', r'\bgiày\s*cao\s*gót\b', r'\bheel\b',
                r'\bsandal\b.*\b(nu|women)\b', r'\bpump\b', r'\bwedge\b'
            ],
            'category': 'heels',
            'priority': 51
        },
        # Lipstick
        {
            'patterns': [
                r'\bson\s*(moi|li)?\b', r'\blipstick\b', r'\blip\s*(tint|gloss|balm|liner)\b'
            ],
            'category': 'lipstick',
            'priority': 50
        },
        # Foundation
        {
            'patterns': [
                r'\bkem\s*(nen|lot|bb|cc)\b', r'\bfoundation\b', r'\bconcealer\b',
                r'\bprimer\b', r'\bcushion\b', r'\bphan\s*nen\b'
            ],
            'category': 'foundation',
            'priority': 48
        },
        # Skincare
        {
            'patterns': [
                r'\bskincare\b', r'\bserum\b', r'\btoner\b', r'\bmoisturiz\b',
                r'\bcleans\b', r'\bsua\s*rua\s*mat\b', r'\bduong\s*(da|am)\b',
                r'\bmask\b', r'\bessence\b', r'\bsunscreen\b', r'\bspf\b'
            ],
            'category': 'skincare',
            'priority': 46
        },
        # Bags
        {
            'patterns': [
                r'\btui\s*(xach|deo|cheo)\b', r'\btúi\b', r'\bbalo\b', r'\bbackpack\b',
                r'\bbag\b', r'\bclutch\b', r'\btote\b', r'\bcrossbody\b'
            ],
            'category': 'bags',
            'priority': 45
        },
        # Cookware
        {
            'patterns': [
                r'\bbo\s*noi\b', r'\bchao\b', r'\bcháo\b', r'\bpot\b', r'\bpan\b',
                r'\bcookware\b', r'\btefal\b', r'\block\s*&\s*lock\b', r'\bdung\s*cu\b'
            ],
            'category': 'cookware',
            'priority': 40
        },
        # Gym Equipment
        {
            'patterns': [
                r'\bgym\b', r'\bfitness\b', r'\bta\s*(tay|chan)\b', r'\btạ\b',
                r'\bdumbbell\b', r'\btreadmill\b', r'\byoga\b', r'\bworkout\b'
            ],
            'category': 'gym-equipment',
            'priority': 35
        },
        # Outdoor Gear
        {
            'patterns': [
                r'\boutdoor\b', r'\bcamping\b', r'\bhiking\b', r'\btent\b',
                r'\bleo\s*nui\b', r'\bdu\s*lich\b'
            ],
            'category': 'outdoor-gear',
            'priority': 33
        },
        # Books
        {
            'patterns': [
                r'\bsach\b', r'\bsách\b', r'\bbook\b', r'\btruyện\b', r'\btiểu\s*thuyết\b'
            ],
            'category': 'books',
            'priority': 30
        },
        # Stationery
        {
            'patterns': [
                r'\bvan\s*phong\s*pham\b', r'\bstationery\b', r'\bbut\b', r'\bso\s*tay\b',
                r'\bpen\b', r'\bpencil\b', r'\beraser\b'
            ],
            'category': 'stationery',
            'priority': 28
        },
        # Furniture
        {
            'patterns': [
                r'\bban\s*(lam\s*viec|an|trang\s*diem)\b', r'\bghe\b', r'\bgiuong\b',
                r'\bsofa\b', r'\btable\b', r'\bchair\b', r'\bdesk\b', r'\bcabinet\b'
            ],
            'category': 'furniture',
            'priority': 25
        },
        # Components
        {
            'patterns': [
                r'\bcpu\b', r'\bgpu\b', r'\bram\b', r'\bssd\b', r'\bhdd\b',
                r'\bmainboard\b', r'\bvga\b', r'\bcard\s*man\s*hinh\b', r'\bnguon\b'
            ],
            'category': 'components',
            'priority': 22
        },
    ]

    # Brand -> Category fallback mapping
    BRAND_FALLBACK = {
        'apple': 'smartphone',
        'samsung': 'smartphone',
        'xiaomi': 'smartphone',
        'oppo': 'smartphone',
        'vivo': 'smartphone',
        'realme': 'smartphone',
        'sony': 'electronics',
        'lg': 'electronics',
        'panasonic': 'electronics',
        'sharp': 'electronics',
        'nike': 'shoes-men',
        'adidas': 'shoes-men',
        'puma': 'shoes-men',
        'uniqlo': 'shirt-men',
        'zara': 'dress',
        'h&m': 'dress',
        'mango': 'dress',
        'gucci': 'bags',
        'louis vuitton': 'bags',
        'tefal': 'cookware',
        'philips': 'kitchen-appliances',
        'lock&lock': 'cookware',
        'loreal': 'skincare',
        'maybelline': 'lipstick',
        'mac': 'lipstick',
    }

    # Vietnamese diacritics mapping
    VIET_TO_LATIN = str.maketrans({
        'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        'đ': 'd',
    })

    def __init__(self):
        # Pre-compile regex patterns for performance
        self._compiled_rules = []
        for rule in self.RULES:
            compiled = {
                'patterns': [re.compile(p, re.IGNORECASE) for p in rule['patterns']],
                'category': rule['category'],
                'priority': rule['priority']
            }
            self._compiled_rules.append(compiled)

        # Sort by priority descending
        self._compiled_rules.sort(key=lambda x: -x['priority'])

    def normalize(self, text: str) -> str:
        """Normalize text by removing Vietnamese diacritics"""
        return text.lower().translate(self.VIET_TO_LATIN)

    def classify(self, product_name: str, description: str = '') -> ClassificationResult:
        """
        Classify a product based on name and description.

        Args:
            product_name: Product name
            description: Product description (optional)

        Returns:
            ClassificationResult with category, confidence, and matched pattern
        """
        # Combine and normalize text
        text = f"{product_name} {description}".lower()
        text_normalized = self.normalize(text)

        # Try pattern matching
        for rule in self._compiled_rules:
            for pattern in rule['patterns']:
                if pattern.search(text) or pattern.search(text_normalized):
                    category = rule['category']
                    return ClassificationResult(
                        category_slug=category,
                        confidence=rule['priority'] / 100.0,
                        matched_pattern=pattern.pattern,
                        parent_category=self.CATEGORY_HIERARCHY.get(category)
                    )

        # Fallback: brand-based classification
        for brand, category in self.BRAND_FALLBACK.items():
            if brand in text:
                return ClassificationResult(
                    category_slug=category,
                    confidence=0.3,
                    matched_pattern=f'brand:{brand}',
                    parent_category=self.CATEGORY_HIERARCHY.get(category)
                )

        # No match
        return ClassificationResult(
            category_slug=None,
            confidence=0.0,
            matched_pattern=None,
            parent_category=None
        )

    def classify_batch(self, products: list) -> list:
        """
        Classify multiple products.

        Args:
            products: List of dicts with 'name' and optional 'description'

        Returns:
            List of ClassificationResult
        """
        results = []
        for product in products:
            name = product.get('name', '')
            desc = product.get('description', '')
            results.append(self.classify(name, desc))
        return results

    def get_parent_category(self, category_slug: str) -> Optional[str]:
        """Get parent category for a given category slug"""
        return self.CATEGORY_HIERARCHY.get(category_slug)

    def get_all_categories(self) -> dict:
        """Get all category slugs organized by parent"""
        result = {}
        for child, parent in self.CATEGORY_HIERARCHY.items():
            if parent not in result:
                result[parent] = []
            result[parent].append(child)
        return result


# Singleton instance for easy import
classifier = ProductClassifier()


def classify_product(name: str, description: str = '') -> dict:
    """
    Convenience function for product classification.

    Args:
        name: Product name
        description: Product description

    Returns:
        dict with classification result
    """
    return classifier.classify(name, description).to_dict()
