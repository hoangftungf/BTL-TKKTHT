"""
Management command to rebuild category hierarchy for AI/recommendation system
Step 2: Delete old categories (safe mode)
Step 3: Create new category tree
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from product_app.models import Category, Product


# Category tree definition
CATEGORY_TREE = {
    'Electronics': {
        'slug': 'electronics',
        'description': 'Electronic devices and appliances',
        'children': {
            'TV': {'slug': 'tv', 'description': 'Television and displays'},
            'Refrigerator': {'slug': 'refrigerator', 'description': 'Refrigerators and freezers'},
            'Washing Machine': {'slug': 'washing-machine', 'description': 'Washing machines and dryers'},
            'Air Conditioner': {'slug': 'air-conditioner', 'description': 'Air conditioners and coolers'},
        }
    },
    'Computers': {
        'slug': 'computers',
        'description': 'Computers and related equipment',
        'children': {
            'Laptop': {'slug': 'laptop', 'description': 'Laptops and notebooks'},
            'Desktop PC': {'slug': 'desktop-pc', 'description': 'Desktop computers'},
            'Components': {'slug': 'components', 'description': 'Computer components and parts'},
        }
    },
    'Phones & Tablets': {
        'slug': 'phones-tablets',
        'description': 'Mobile phones and tablets',
        'children': {
            'Smartphone': {'slug': 'smartphone', 'description': 'Smartphones and mobile phones'},
            'Tablet': {'slug': 'tablet', 'description': 'Tablets and e-readers'},
            'Phone Accessories': {'slug': 'phone-accessories', 'description': 'Phone cases, chargers, etc.'},
        }
    },
    'Fashion Men': {
        'slug': 'fashion-men',
        'description': "Men's fashion and clothing",
        'children': {
            'Shirt': {'slug': 'shirt-men', 'description': "Men's shirts and tops"},
            'Pants': {'slug': 'pants-men', 'description': "Men's pants and trousers"},
            'Shoes': {'slug': 'shoes-men', 'description': "Men's footwear"},
        }
    },
    'Fashion Women': {
        'slug': 'fashion-women',
        'description': "Women's fashion and clothing",
        'children': {
            'Dress': {'slug': 'dress', 'description': 'Dresses and skirts'},
            'Tops': {'slug': 'tops-women', 'description': "Women's tops and blouses"},
            'Heels': {'slug': 'heels', 'description': "Women's heels and footwear"},
        }
    },
    'Beauty & Cosmetics': {
        'slug': 'beauty-cosmetics',
        'description': 'Beauty and cosmetic products',
        'children': {
            'Lipstick': {'slug': 'lipstick', 'description': 'Lipsticks and lip care'},
            'Foundation': {'slug': 'foundation', 'description': 'Foundation and face makeup'},
            'Skincare': {'slug': 'skincare', 'description': 'Skincare products'},
        }
    },
    'Home & Kitchen': {
        'slug': 'home-kitchen',
        'description': 'Home and kitchen products',
        'children': {
            'Cookware': {'slug': 'cookware', 'description': 'Pots, pans, and cookware'},
            'Kitchen Appliances': {'slug': 'kitchen-appliances', 'description': 'Kitchen appliances'},
            'Furniture': {'slug': 'furniture', 'description': 'Home furniture'},
        }
    },
    'Sports & Outdoor': {
        'slug': 'sports-outdoor',
        'description': 'Sports and outdoor equipment',
        'children': {
            'Gym Equipment': {'slug': 'gym-equipment', 'description': 'Gym and fitness equipment'},
            'Outdoor Gear': {'slug': 'outdoor-gear', 'description': 'Outdoor and camping gear'},
        }
    },
    'Accessories': {
        'slug': 'accessories',
        'description': 'Accessories and wearables',
        'children': {
            'Watches': {'slug': 'watches', 'description': 'Watches and smartwatches'},
            'Bags': {'slug': 'bags', 'description': 'Bags and backpacks'},
        }
    },
    'Books & Office': {
        'slug': 'books-office',
        'description': 'Books and office supplies',
        'children': {
            'Books': {'slug': 'books', 'description': 'Books and publications'},
            'Stationery': {'slug': 'stationery', 'description': 'Stationery and office supplies'},
        }
    },
}


class Command(BaseCommand):
    help = 'Rebuild category hierarchy for AI/recommendation system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force rebuild even if products are assigned to categories',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write(self.style.NOTICE('Category Hierarchy Rebuild'))
        self.stdout.write(self.style.NOTICE('=' * 60))

        # Check existing state
        old_categories = Category.objects.count()
        products_with_category = Product.objects.filter(category__isnull=False).count()
        total_products = Product.objects.count()

        self.stdout.write(f'\nCurrent state:')
        self.stdout.write(f'  - Categories: {old_categories}')
        self.stdout.write(f'  - Products with category: {products_with_category}/{total_products}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No changes will be made'))
            self._show_new_structure()
            return

        if products_with_category > 0 and not force:
            self.stdout.write(self.style.WARNING(
                f'\nWarning: {products_with_category} products have categories assigned.'
            ))
            self.stdout.write('Use --force to proceed (products will be set to NULL category)')
            return

        # Execute rebuild
        with transaction.atomic():
            self._rebuild_categories(force)

        self.stdout.write(self.style.SUCCESS('\nCategory rebuild completed!'))
        self._print_summary()

    def _show_new_structure(self):
        """Display the new category structure"""
        self.stdout.write('\nNew category structure:')
        order = 0
        for parent_name, parent_data in CATEGORY_TREE.items():
            order += 1
            self.stdout.write(f'\n  {order}. {parent_name} [{parent_data["slug"]}]')
            child_order = 0
            for child_name, child_data in parent_data.get('children', {}).items():
                child_order += 1
                self.stdout.write(f'      {order}.{child_order} {child_name} [{child_data["slug"]}]')

    def _rebuild_categories(self, force):
        """Delete old categories and create new structure"""
        self.stdout.write('\nStep 1: Clearing product categories...')
        if force:
            Product.objects.all().update(category=None)
            self.stdout.write(self.style.SUCCESS('  Products cleared'))

        self.stdout.write('\nStep 2: Deleting old categories...')
        deleted_count = Category.objects.count()
        Category.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'  Deleted {deleted_count} categories'))

        self.stdout.write('\nStep 3: Creating new category tree...')
        self._create_categories()

    def _create_categories(self):
        """Create the new category hierarchy"""
        order = 0
        created_count = 0

        for parent_name, parent_data in CATEGORY_TREE.items():
            order += 1

            # Create parent category
            parent = Category.objects.create(
                name=parent_name,
                slug=parent_data['slug'],
                description=parent_data.get('description', ''),
                parent=None,
                level=0,
                is_active=True,
                display_order=order
            )
            created_count += 1
            self.stdout.write(f'  + {parent_name}')

            # Create child categories
            child_order = 0
            for child_name, child_data in parent_data.get('children', {}).items():
                child_order += 1
                Category.objects.create(
                    name=child_name,
                    slug=child_data['slug'],
                    description=child_data.get('description', ''),
                    parent=parent,
                    level=1,
                    is_active=True,
                    display_order=child_order
                )
                created_count += 1
                self.stdout.write(f'    - {child_name}')

        self.stdout.write(self.style.SUCCESS(f'\n  Created {created_count} categories'))

    def _print_summary(self):
        """Print final summary"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('Summary:')
        self.stdout.write('=' * 60)

        # Count by level
        level_0 = Category.objects.filter(level=0).count()
        level_1 = Category.objects.filter(level=1).count()
        total = Category.objects.count()

        self.stdout.write(f'  Main categories (level 0): {level_0}')
        self.stdout.write(f'  Subcategories (level 1): {level_1}')
        self.stdout.write(f'  Total categories: {total}')

        # List all categories
        self.stdout.write('\nCategory tree:')
        for cat in Category.objects.filter(level=0).order_by('display_order'):
            self.stdout.write(f'\n  [{cat.id}] {cat.name}')
            for child in cat.children.order_by('display_order'):
                self.stdout.write(f'      [{child.id}] {child.name}')
