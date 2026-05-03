"""
Management command to auto-classify and migrate products to new categories
Step 4: Auto classify products
Step 5: Migrate products
Step 6: Validate
"""

import re
from django.core.management.base import BaseCommand
from django.db import transaction
from product_app.models import Category, Product


# Classification rules with priority (higher priority = checked first)
CLASSIFICATION_RULES = [
    # Smartphones - check specific brands
    {
        'patterns': [
            r'\biphone\b', r'\bsamsung\s*galaxy\s*(s|a|z|note)\d', r'\bxiaomi\b',
            r'\boppo\b', r'\bvivo\b', r'\brealme\b', r'\bpixel\b', r'\boneplus\b',
            r'\bredmi\b', r'\bhuawei\s*(p|mate|nova)\b'
        ],
        'category_slug': 'smartphone',
        'priority': 100
    },
    # Laptops - check specific brands/models
    {
        'patterns': [
            r'\bmacbook\b', r'\blaptop\b', r'\bnotebook\b',
            r'\b(dell|asus|hp|lenovo|acer|msi)\s*(inspiron|vivobook|pavilion|thinkpad|aspire|ideapad|rog|gaming|xps|spectre|envy|zenbook)\b',
            r'\b(dell|asus|hp|lenovo|acer|msi)\b.*\blaptop\b',
            r'\bdell\s*xps\b', r'\bhp\s*(spectre|envy|omen)\b', r'\basus\s*(zenbook|vivobook)\b',
            r'\bcore\s*i[3579]\b.*\b(dell|hp|asus|lenovo)\b',
        ],
        'category_slug': 'laptop',
        'priority': 95
    },
    # Tablets
    {
        'patterns': [
            r'\bipad\b', r'\btablet\b', r'\bgalaxy\s*tab\b', r'\bsurface\s*pro\b',
            r'\bmatrix\s*pad\b', r'\bmi\s*pad\b'
        ],
        'category_slug': 'tablet',
        'priority': 90
    },
    # Desktop PC
    {
        'patterns': [
            r'\bpc\b', r'\bdesktop\b', r'\bmay\s*tinh\s*ban\b', r'\bimac\b',
            r'\bmac\s*(mini|studio|pro)\b'
        ],
        'category_slug': 'desktop-pc',
        'priority': 88
    },
    # Watches
    {
        'patterns': [
            r'\bwatch\b', r'\bdong\s*ho\b', r'\bđồng\s*hồ\b',
            r'\bapple\s*watch\b', r'\bgalaxy\s*watch\b', r'\bgarmin\b', r'\bfitbit\b'
        ],
        'category_slug': 'watches',
        'priority': 85
    },
    # Phone Accessories (AirPods, cases, chargers)
    {
        'patterns': [
            r'\bairpods\b', r'\bearbuds\b', r'\btai\s*nghe\b', r'\bheadphone\b',
            r'\bsac\b', r'\bcharger\b', r'\bop\s*lung\b', r'\bcase\b',
            r'\bphu\s*kien\b', r'\baccessor'
        ],
        'category_slug': 'phone-accessories',
        'priority': 80
    },
    # TV (only match explicit TV mentions)
    {
        'patterns': [
            r'\btivi\b', r'\btelevision\b', r'\bsmart\s*tv\b',
            r'\b(oled|qled|neo\s*qled)\s*tv\b',
            r'\b(samsung|lg|sony|tcl)\b.*\b\d{2,3}\s*inch\s*(tv|tivi)\b'
        ],
        'category_slug': 'tv',
        'priority': 75
    },
    # Kitchen Appliances
    {
        'patterns': [
            r'\bnoi\b', r'\bnồi\b', r'\bbep\b', r'\bbếp\b', r'\bmay\s*(xay|ep|pha)\b',
            r'\bmáy\b.*\b(xay|ép|pha)\b', r'\bair\s*fryer\b', r'\blò\s*(vi\s*sóng|nuong)\b',
            r'\bblender\b', r'\bcoffee\s*maker\b', r'\bphilips\b', r'\bdelonghi\b',
            r'\bvitamix\b', r'\bfissler\b', r'\bbosch\b.*\b(bep|tu)\b'
        ],
        'category_slug': 'kitchen-appliances',
        'priority': 70
    },
    # Refrigerator
    {
        'patterns': [
            r'\btu\s*lanh\b', r'\btủ\s*lạnh\b', r'\brefrigerator\b', r'\bfreezer\b'
        ],
        'category_slug': 'refrigerator',
        'priority': 68
    },
    # Washing Machine
    {
        'patterns': [
            r'\bmay\s*giat\b', r'\bmáy\s*giặt\b', r'\bwashing\s*machine\b',
            r'\bdryer\b', r'\bmay\s*say\b'
        ],
        'category_slug': 'washing-machine',
        'priority': 66
    },
    # Air Conditioner
    {
        'patterns': [
            r'\bdieu\s*hoa\b', r'\bđiều\s*hòa\b', r'\bair\s*conditioner\b',
            r'\bmay\s*lanh\b', r'\bac\b'
        ],
        'category_slug': 'air-conditioner',
        'priority': 64
    },
    # Men's Shirts
    {
        'patterns': [
            r'\bao\s*(so\s*mi|hoodie|khoac|polo|thun)\s*(nam)?\b',
            r'\báo\s*(sơ\s*mi|hoodie|khoác|polo|thun)\b.*\bnam\b',
            r'\bshirt\b.*\b(men|nam)\b', r'\bhoodie\s*(nam|men)\b',
            r'\b(men|nam)\b.*\b(shirt|ao)\b'
        ],
        'category_slug': 'shirt-men',
        'priority': 60
    },
    # Men's Pants
    {
        'patterns': [
            r'\bquan\s*(jean|kaki|short|dai)\s*(nam)?\b',
            r'\bquần\b.*\bnam\b', r'\b(jean|jeans|pants|trouser)\b.*\b(men|nam)\b',
            r'\b(men|nam)\b.*\b(quan|pants)\b'
        ],
        'category_slug': 'pants-men',
        'priority': 58
    },
    # Men's Shoes
    {
        'patterns': [
            r'\bgiay\s*(nam|sneaker|the\s*thao|tay|oxford)\b',
            r'\bgiày\b.*\bnam\b', r'\b(nike|adidas|puma|converse)\b.*\b(nam|men|giay)\b',
            r'\bsneaker\s*(nam|men)\b', r'\boxford\b'
        ],
        'category_slug': 'shoes-men',
        'priority': 56
    },
    # Women's Dress
    {
        'patterns': [
            r'\bdam\b', r'\bđầm\b', r'\bvay\b', r'\bváy\b', r'\bdress\b',
            r'\bskirt\b', r'\bmaxi\b', r'\bmidi\b', r'\ba-line\b'
        ],
        'category_slug': 'dress',
        'priority': 55
    },
    # Women's Tops
    {
        'patterns': [
            r'\bao\s*(nu|blouse|croptop)\b', r'\báo\b.*\bnữ\b',
            r'\b(blouse|croptop|top)\b.*\b(women|nu)\b',
            r'\b(women|nu)\b.*\b(shirt|ao|top)\b'
        ],
        'category_slug': 'tops-women',
        'priority': 53
    },
    # Women's Heels
    {
        'patterns': [
            r'\bgiay\s*(cao\s*got|nu)\b', r'\bgiày\s*cao\s*gót\b',
            r'\bheel\b', r'\bsandal\s*(nu|women)\b', r'\bjuno\b'
        ],
        'category_slug': 'heels',
        'priority': 51
    },
    # Lipstick
    {
        'patterns': [
            r'\bson\b', r'\blipstick\b', r'\blip\s*(tint|gloss|balm)\b',
            r'\bson\s*moi\b'
        ],
        'category_slug': 'lipstick',
        'priority': 50
    },
    # Foundation
    {
        'patterns': [
            r'\bkem\s*(nen|lot|chong\s*nang)\b', r'\bfoundation\b',
            r'\bconcealer\b', r'\bprimer\b', r'\bbb\s*cream\b', r'\bcc\s*cream\b'
        ],
        'category_slug': 'foundation',
        'priority': 48
    },
    # Skincare
    {
        'patterns': [
            r'\bskincare\b', r'\bserum\b', r'\btoner\b', r'\bmoisturiz\b',
            r'\bcleans\b', r'\bsua\s*rua\b', r'\bduong\s*(da|am)\b'
        ],
        'category_slug': 'skincare',
        'priority': 46
    },
    # Bags
    {
        'patterns': [
            r'\btui\s*(xach|deo)\b', r'\btúi\b', r'\bbalo\b', r'\bbackpack\b',
            r'\bbag\b', r'\bvi\b.*\b(nam|nu)\b'
        ],
        'category_slug': 'bags',
        'priority': 45
    },
    # Cookware
    {
        'patterns': [
            r'\bbo\s*noi\b', r'\bchao\b', r'\bpot\b', r'\bpan\b',
            r'\bcookware\b', r'\btefal\b', r'\bdung\s*cu\s*nha\s*bep\b'
        ],
        'category_slug': 'cookware',
        'priority': 40
    },
    # Gym Equipment
    {
        'patterns': [
            r'\bgym\b', r'\bfitness\b', r'\bta\s*(tay|chan)\b', r'\btạ\b',
            r'\bdumbbell\b', r'\btreadmill\b', r'\byoga\b'
        ],
        'category_slug': 'gym-equipment',
        'priority': 35
    },
    # Books
    {
        'patterns': [
            r'\bsach\b', r'\bsách\b', r'\bbook\b', r'\btruyện\b'
        ],
        'category_slug': 'books',
        'priority': 30
    },
    # Stationery
    {
        'patterns': [
            r'\bvan\s*phong\s*pham\b', r'\bstationery\b', r'\bbut\b', r'\bso\s*tay\b',
            r'\bpen\b', r'\bnotebook\b(?!.*laptop)'
        ],
        'category_slug': 'stationery',
        'priority': 28
    },
]


def classify_product(product_name: str, product_description: str = '') -> dict:
    """
    Classify a product based on its name and description.

    Args:
        product_name: Product name
        product_description: Product description (optional)

    Returns:
        dict with 'category_slug', 'confidence', 'matched_pattern'
    """
    # Combine name and description for matching
    text = f"{product_name} {product_description}".lower()

    # Remove Vietnamese diacritics for broader matching
    text_normalized = normalize_vietnamese(text)

    best_match = None
    best_priority = -1
    matched_pattern = None

    for rule in CLASSIFICATION_RULES:
        if rule['priority'] <= best_priority:
            continue

        for pattern in rule['patterns']:
            # Try matching with original text
            if re.search(pattern, text, re.IGNORECASE):
                best_match = rule['category_slug']
                best_priority = rule['priority']
                matched_pattern = pattern
                break
            # Try matching with normalized text
            if re.search(pattern, text_normalized, re.IGNORECASE):
                best_match = rule['category_slug']
                best_priority = rule['priority']
                matched_pattern = pattern
                break

    if best_match:
        return {
            'category_slug': best_match,
            'confidence': best_priority / 100.0,
            'matched_pattern': matched_pattern
        }

    # Fallback: try to match by brand for generic assignment
    return fallback_classify(text)


def normalize_vietnamese(text: str) -> str:
    """Remove Vietnamese diacritics for broader matching"""
    replacements = {
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
    }
    for viet, latin in replacements.items():
        text = text.replace(viet, latin)
    return text


def fallback_classify(text: str) -> dict:
    """Fallback classification based on common keywords"""
    # Brand-based fallback
    brand_mapping = {
        # Tech brands -> default categories
        'apple': 'smartphone',
        'samsung': 'smartphone',
        'sony': 'electronics',
        'lg': 'electronics',
        'panasonic': 'electronics',
        # Fashion brands
        'nike': 'shoes-men',
        'adidas': 'shoes-men',
        'uniqlo': 'shirt-men',
        'zara': 'dress',
        'h&m': 'dress',
        'gucci': 'bags',
        # Kitchen brands
        'tefal': 'kitchen-appliances',
        'philips': 'kitchen-appliances',
        'lock&lock': 'cookware',
    }

    for brand, category in brand_mapping.items():
        if brand in text:
            return {
                'category_slug': category,
                'confidence': 0.3,
                'matched_pattern': f'brand:{brand}'
            }

    # No match - return None
    return {
        'category_slug': None,
        'confidence': 0,
        'matched_pattern': None
    }


class Command(BaseCommand):
    help = 'Auto-classify and migrate products to new categories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show classification results without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed classification for each product',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']

        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write(self.style.NOTICE('Product Classification & Migration'))
        self.stdout.write(self.style.NOTICE('=' * 60))

        # Load categories
        categories = {cat.slug: cat for cat in Category.objects.all()}
        if not categories:
            self.stdout.write(self.style.ERROR(
                'No categories found! Run rebuild_categories first.'
            ))
            return

        self.stdout.write(f'\nLoaded {len(categories)} categories')

        # Get all products
        products = Product.objects.all()
        total = products.count()
        self.stdout.write(f'Found {total} products to classify\n')

        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY RUN] No changes will be made\n'))

        # Classification stats
        stats = {
            'classified': 0,
            'unclassified': 0,
            'by_category': {},
            'by_confidence': {'high': 0, 'medium': 0, 'low': 0, 'none': 0}
        }

        # Process products
        products_to_update = []

        for product in products:
            result = classify_product(product.name, product.description or '')

            category_slug = result['category_slug']
            confidence = result['confidence']
            matched = result['matched_pattern']

            if category_slug and category_slug in categories:
                category = categories[category_slug]
                stats['classified'] += 1
                stats['by_category'][category_slug] = stats['by_category'].get(category_slug, 0) + 1

                if confidence >= 0.7:
                    stats['by_confidence']['high'] += 1
                elif confidence >= 0.4:
                    stats['by_confidence']['medium'] += 1
                else:
                    stats['by_confidence']['low'] += 1

                if verbose:
                    self.stdout.write(
                        f'  [{confidence:.0%}] {product.name[:50]} -> {category.name} (pattern: {matched})'
                    )

                if not dry_run:
                    product.category = category
                    products_to_update.append(product)
            else:
                stats['unclassified'] += 1
                stats['by_confidence']['none'] += 1

                if verbose:
                    self.stdout.write(
                        self.style.WARNING(f'  [???] {product.name[:50]} -> UNCLASSIFIED')
                    )

        # Bulk update
        if not dry_run and products_to_update:
            with transaction.atomic():
                Product.objects.bulk_update(products_to_update, ['category'], batch_size=100)
            self.stdout.write(self.style.SUCCESS(f'\nUpdated {len(products_to_update)} products'))

        # Print summary
        self._print_summary(stats, total, categories)

        # Validation
        self._validate(total)

    def _print_summary(self, stats, total, categories):
        """Print classification summary"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('Classification Summary')
        self.stdout.write('=' * 60)

        self.stdout.write(f'\nTotal products: {total}')
        self.stdout.write(f'Classified: {stats["classified"]} ({stats["classified"]*100//total if total else 0}%)')
        self.stdout.write(f'Unclassified: {stats["unclassified"]}')

        self.stdout.write('\nConfidence levels:')
        self.stdout.write(f'  High (>=70%): {stats["by_confidence"]["high"]}')
        self.stdout.write(f'  Medium (40-69%): {stats["by_confidence"]["medium"]}')
        self.stdout.write(f'  Low (<40%): {stats["by_confidence"]["low"]}')
        self.stdout.write(f'  None: {stats["by_confidence"]["none"]}')

        self.stdout.write('\nProducts per category:')
        for slug, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
            cat_name = categories.get(slug, Category(name=slug)).name
            self.stdout.write(f'  {cat_name}: {count}')

        # Categories with no products
        empty_cats = [slug for slug in categories if slug not in stats['by_category']]
        if empty_cats:
            self.stdout.write('\nCategories with no products:')
            for slug in empty_cats:
                self.stdout.write(f'  - {categories[slug].name}')

    def _validate(self, total):
        """Validate migration results"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('Validation')
        self.stdout.write('=' * 60)

        # Check products without category
        no_category = Product.objects.filter(category__isnull=True).count()
        with_category = Product.objects.filter(category__isnull=False).count()

        self.stdout.write(f'\nProducts with category: {with_category}')
        self.stdout.write(f'Products without category: {no_category}')

        if no_category == 0:
            self.stdout.write(self.style.SUCCESS('\n[PASS] All products have categories'))
        else:
            self.stdout.write(self.style.WARNING(
                f'\n[WARN] {no_category} products still need manual categorization'
            ))
            # List uncategorized products
            uncategorized = Product.objects.filter(category__isnull=True)[:10]
            self.stdout.write('\nUncategorized products (first 10):')
            for p in uncategorized:
                self.stdout.write(f'  - {p.name}')

        # Check hierarchy
        self.stdout.write('\nCategory hierarchy:')
        for cat in Category.objects.filter(level=0).order_by('display_order'):
            child_count = cat.children.count()
            product_count = Product.objects.filter(category=cat).count()
            self.stdout.write(f'  {cat.name}: {child_count} subcategories, {product_count} direct products')

            for child in cat.children.order_by('display_order'):
                child_products = Product.objects.filter(category=child).count()
                self.stdout.write(f'    - {child.name}: {child_products} products')
