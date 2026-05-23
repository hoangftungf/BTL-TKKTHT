"""
Tiki Product Scraper using Playwright
======================================
Scrapes product data from Tiki.vn for AI evaluation pipeline.

Usage:
    python scripts/scrapers/tiki_scraper.py --output data/raw/tiki_products.json --limit 500
    python scripts/scrapers/tiki_scraper.py --categories laptop,smartphone --limit 200

Requirements:
    pip install playwright aiohttp
    playwright install chromium
"""

import argparse
import asyncio
import json
import logging
import os
import random
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, quote

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class ScrapedProduct:
    """Normalized product data structure"""
    source: str  # 'tiki' or 'shopee'
    source_id: str  # Original ID from source
    name: str
    price: int  # VND, no decimals
    original_price: Optional[int]
    discount_percent: Optional[int]
    brand: Optional[str]
    category_source: str  # Original category from source
    category_mapped: Optional[str]  # Mapped to our category system
    description: Optional[str]
    short_description: Optional[str]
    image_url: Optional[str]
    rating: Optional[float]
    review_count: Optional[int]
    sold_count: Optional[int]
    seller_name: Optional[str]
    url: str
    scraped_at: str


# Tiki category URLs for scraping
TIKI_CATEGORIES = {
    'laptop': {
        'url': 'https://tiki.vn/laptop/c8095',
        'name': 'Laptop',
        'mapped_id': 'cat_laptop'
    },
    'smartphone': {
        'url': 'https://tiki.vn/dien-thoai-smartphone/c1789',
        'name': 'Dien thoai Smartphone',
        'mapped_id': 'cat_smartphone'
    },
    'tablet': {
        'url': 'https://tiki.vn/may-tinh-bang/c1794',
        'name': 'May tinh bang',
        'mapped_id': 'cat_tablet'
    },
    'headphones': {
        'url': 'https://tiki.vn/tai-nghe/c8242',
        'name': 'Tai nghe',
        'mapped_id': 'cat_headphones'
    },
    'men_shirts': {
        'url': 'https://tiki.vn/ao-thun-nam/c921',
        'name': 'Ao nam',
        'mapped_id': 'cat_shirt_men'
    },
    'men_pants': {
        'url': 'https://tiki.vn/quan-nam/c915',
        'name': 'Quan nam',
        'mapped_id': 'cat_pants_men'
    },
    'men_shoes': {
        'url': 'https://tiki.vn/giay-the-thao-sneakers-nam/c1686',
        'name': 'Giay nam',
        'mapped_id': 'cat_shoes_men'
    },
    'women_dress': {
        'url': 'https://tiki.vn/dam-nu/c931',
        'name': 'Dam/Vay',
        'mapped_id': 'cat_dress'
    },
    'women_tops': {
        'url': 'https://tiki.vn/ao-nu/c927',
        'name': 'Ao nu',
        'mapped_id': 'cat_tops_women'
    },
    'skincare': {
        'url': 'https://tiki.vn/cham-soc-da-mat/c1521',
        'name': 'Cham soc da',
        'mapped_id': 'cat_skincare'
    },
    'makeup': {
        'url': 'https://tiki.vn/trang-diem-mat/c1525',
        'name': 'Trang diem',
        'mapped_id': 'cat_makeup'
    },
    'lipstick': {
        'url': 'https://tiki.vn/son-moi/c1520',
        'name': 'Son moi',
        'mapped_id': 'cat_lipstick'
    },
    'kitchen': {
        'url': 'https://tiki.vn/do-dung-nha-bep/c2044',
        'name': 'Do dung nha bep',
        'mapped_id': 'cat_kitchen'
    },
    'air_fryer': {
        'url': 'https://tiki.vn/noi-chien-khong-dau/c28930',
        'name': 'Noi chien khong dau',
        'mapped_id': 'cat_kitchen_appliances'
    }
}


class TikiScraper:
    """Scraper for Tiki.vn using Playwright"""

    BASE_URL = 'https://tiki.vn'

    # Tiki API endpoint for product listing
    API_URL = 'https://tiki.vn/api/personalish/v1/blocks/listings'

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.products: List[ScrapedProduct] = []
        self.browser = None
        self.context = None

    async def init_browser(self):
        """Initialize Playwright browser with stealth settings"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
            raise

        self.playwright = await async_playwright().start()

        # Launch with stealth settings
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )

        # Create context with realistic viewport and user agent
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='vi-VN',
            timezone_id='Asia/Ho_Chi_Minh'
        )

        # Add stealth scripts
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """)

        logger.info("Browser initialized with stealth mode")

    async def close(self):
        """Clean up browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    async def random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Add random delay to avoid detection"""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def scrape_category_api(self, category_key: str, limit: int = 100) -> List[ScrapedProduct]:
        """Scrape products using Tiki API (faster, more reliable)"""
        if category_key not in TIKI_CATEGORIES:
            logger.warning(f"Unknown category: {category_key}")
            return []

        cat_info = TIKI_CATEGORIES[category_key]
        products = []
        page = 1
        per_page = 40  # Tiki's default page size

        # Extract category ID from URL
        cat_id_match = re.search(r'/c(\d+)', cat_info['url'])
        if not cat_id_match:
            logger.error(f"Cannot extract category ID from {cat_info['url']}")
            return []
        cat_id = cat_id_match.group(1)

        logger.info(f"Scraping {cat_info['name']} (category ID: {cat_id})")

        page = await self.context.new_page()

        try:
            while len(products) < limit:
                # Build API URL
                api_params = {
                    'limit': per_page,
                    'include': 'advertisement',
                    'aggregations': 2,
                    'category': cat_id,
                    'page': page,
                    'urlKey': category_key
                }

                api_url = f"{self.API_URL}?{'&'.join(f'{k}={v}' for k, v in api_params.items())}"

                # Navigate to get cookies first (if first request)
                if page == 1:
                    await page.goto(cat_info['url'], wait_until='domcontentloaded')
                    await self.random_delay(2, 4)

                # Make API request
                response = await page.evaluate(f"""
                    async () => {{
                        const resp = await fetch('{api_url}', {{
                            headers: {{
                                'Accept': 'application/json',
                                'x-guest-token': localStorage.getItem('_guest_token') || ''
                            }}
                        }});
                        return await resp.json();
                    }}
                """)

                if not response or 'data' not in response:
                    logger.warning(f"No data in API response for page {page}")
                    break

                items = response.get('data', [])
                if not items:
                    logger.info(f"No more products at page {page}")
                    break

                for item in items:
                    if len(products) >= limit:
                        break

                    product = self._parse_api_product(item, cat_info)
                    if product:
                        products.append(product)

                logger.info(f"  Page {page}: scraped {len(items)} products (total: {len(products)})")
                page += 1
                await self.random_delay(1.5, 3.0)

        except Exception as e:
            logger.error(f"Error scraping {category_key}: {e}")
        finally:
            await page.close()

        return products

    async def scrape_category_html(self, category_key: str, limit: int = 100) -> List[ScrapedProduct]:
        """Fallback: Scrape products by parsing HTML (slower but more robust)"""
        if category_key not in TIKI_CATEGORIES:
            logger.warning(f"Unknown category: {category_key}")
            return []

        cat_info = TIKI_CATEGORIES[category_key]
        products = []
        page_num = 1

        logger.info(f"Scraping {cat_info['name']} via HTML")

        page = await self.context.new_page()

        try:
            while len(products) < limit:
                url = f"{cat_info['url']}?page={page_num}"

                await page.goto(url, wait_until='networkidle', timeout=30000)
                await self.random_delay(2, 4)

                # Wait for product grid to load
                try:
                    await page.wait_for_selector('[data-view-id="product_list_container"]', timeout=10000)
                except:
                    logger.warning(f"Product container not found on page {page_num}")
                    break

                # Extract product data from HTML
                items = await page.evaluate("""
                    () => {
                        const products = [];
                        const cards = document.querySelectorAll('[data-view-id="product_list_container"] a[href*="/p/"]');

                        cards.forEach(card => {
                            try {
                                const nameEl = card.querySelector('.name, [class*="name"], h3');
                                const priceEl = card.querySelector('[class*="price-discount"], [class*="final-price"]');
                                const originalPriceEl = card.querySelector('[class*="price-original"]');
                                const imgEl = card.querySelector('img');
                                const ratingEl = card.querySelector('[class*="rating"]');
                                const soldEl = card.querySelector('[class*="quantity-sold"]');

                                const href = card.getAttribute('href');
                                const idMatch = href ? href.match(/p(\\d+)/) : null;

                                products.push({
                                    id: idMatch ? idMatch[1] : null,
                                    name: nameEl ? nameEl.textContent.trim() : null,
                                    price: priceEl ? priceEl.textContent.replace(/[^0-9]/g, '') : null,
                                    originalPrice: originalPriceEl ? originalPriceEl.textContent.replace(/[^0-9]/g, '') : null,
                                    imageUrl: imgEl ? imgEl.src : null,
                                    url: href,
                                    rating: ratingEl ? ratingEl.textContent : null,
                                    sold: soldEl ? soldEl.textContent : null
                                });
                            } catch (e) {}
                        });

                        return products;
                    }
                """)

                if not items:
                    logger.info(f"No more products at page {page_num}")
                    break

                for item in items:
                    if len(products) >= limit:
                        break
                    if not item.get('name') or not item.get('price'):
                        continue

                    product = ScrapedProduct(
                        source='tiki',
                        source_id=item.get('id', ''),
                        name=item['name'],
                        price=int(item['price']) if item['price'] else 0,
                        original_price=int(item['originalPrice']) if item.get('originalPrice') else None,
                        discount_percent=None,
                        brand=None,
                        category_source=cat_info['name'],
                        category_mapped=cat_info['mapped_id'],
                        description=None,
                        short_description=None,
                        image_url=item.get('imageUrl'),
                        rating=None,
                        review_count=None,
                        sold_count=self._parse_sold_count(item.get('sold', '')),
                        seller_name=None,
                        url=urljoin(self.BASE_URL, item.get('url', '')),
                        scraped_at=datetime.now().isoformat()
                    )
                    products.append(product)

                logger.info(f"  Page {page_num}: scraped {len(items)} products (total: {len(products)})")
                page_num += 1
                await self.random_delay(2, 4)

        except Exception as e:
            logger.error(f"Error scraping {category_key}: {e}")
        finally:
            await page.close()

        return products

    def _parse_api_product(self, item: Dict[str, Any], cat_info: Dict) -> Optional[ScrapedProduct]:
        """Parse product from Tiki API response"""
        try:
            # Skip sponsored/ad items
            if item.get('type') == 'ad':
                return None

            price = item.get('price', 0)
            original_price = item.get('original_price') or item.get('list_price')

            discount = None
            if original_price and price and original_price > price:
                discount = int((1 - price / original_price) * 100)

            # Extract brand from brand_name or specifications
            brand = item.get('brand_name')
            if not brand:
                specs = item.get('specifications', [])
                for spec in specs:
                    if spec.get('name', '').lower() in ['thuong hieu', 'brand']:
                        brand = spec.get('value')
                        break

            return ScrapedProduct(
                source='tiki',
                source_id=str(item.get('id', '')),
                name=item.get('name', ''),
                price=int(price) if price else 0,
                original_price=int(original_price) if original_price else None,
                discount_percent=discount,
                brand=brand,
                category_source=cat_info['name'],
                category_mapped=cat_info['mapped_id'],
                description=item.get('description'),
                short_description=item.get('short_description'),
                image_url=item.get('thumbnail_url'),
                rating=item.get('rating_average'),
                review_count=item.get('review_count'),
                sold_count=item.get('quantity_sold', {}).get('value') if isinstance(item.get('quantity_sold'), dict) else item.get('quantity_sold'),
                seller_name=item.get('seller', {}).get('name') if isinstance(item.get('seller'), dict) else None,
                url=f"https://tiki.vn/{item.get('url_key', '')}-p{item.get('id', '')}",
                scraped_at=datetime.now().isoformat()
            )
        except Exception as e:
            logger.warning(f"Error parsing product: {e}")
            return None

    def _parse_sold_count(self, sold_text: str) -> Optional[int]:
        """Parse sold count from text like 'Da ban 1.2k'"""
        if not sold_text:
            return None
        match = re.search(r'([\d.,]+)\s*(k|K|tr|nghin)?', sold_text)
        if match:
            num = float(match.group(1).replace(',', '.'))
            unit = match.group(2)
            if unit and unit.lower() in ['k', 'nghin']:
                num *= 1000
            elif unit and unit.lower() == 'tr':
                num *= 1000000
            return int(num)
        return None

    async def scrape_all(
        self,
        categories: Optional[List[str]] = None,
        limit_per_category: int = 100,
        use_api: bool = True
    ) -> List[ScrapedProduct]:
        """Scrape products from multiple categories"""
        await self.init_browser()

        if categories is None:
            categories = list(TIKI_CATEGORIES.keys())

        all_products = []

        for cat_key in categories:
            try:
                if use_api:
                    products = await self.scrape_category_api(cat_key, limit_per_category)
                else:
                    products = await self.scrape_category_html(cat_key, limit_per_category)

                all_products.extend(products)
                logger.info(f"Completed {cat_key}: {len(products)} products")

            except Exception as e:
                logger.error(f"Failed to scrape {cat_key}: {e}")

            await self.random_delay(3, 6)

        await self.close()

        self.products = all_products
        return all_products

    def save_to_json(self, filepath: str):
        """Save scraped products to JSON file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        data = {
            'source': 'tiki',
            'scraped_at': datetime.now().isoformat(),
            'total_count': len(self.products),
            'products': [asdict(p) for p in self.products]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(self.products)} products to {filepath}")


async def main():
    parser = argparse.ArgumentParser(description='Scrape products from Tiki.vn')
    parser.add_argument('--output', '-o', default='data/raw/tiki_products.json',
                        help='Output JSON file path')
    parser.add_argument('--limit', '-l', type=int, default=500,
                        help='Maximum products to scrape (total)')
    parser.add_argument('--categories', '-c', type=str, default=None,
                        help='Comma-separated category keys (default: all)')
    parser.add_argument('--per-category', type=int, default=None,
                        help='Limit per category (default: limit / num_categories)')
    parser.add_argument('--no-headless', action='store_true',
                        help='Show browser window (for debugging)')
    parser.add_argument('--use-html', action='store_true',
                        help='Use HTML parsing instead of API')
    parser.add_argument('--list-categories', action='store_true',
                        help='List available categories and exit')

    args = parser.parse_args()

    if args.list_categories:
        print("\nAvailable categories:")
        for key, info in TIKI_CATEGORIES.items():
            print(f"  {key:15} -> {info['name']} ({info['mapped_id']})")
        return

    categories = args.categories.split(',') if args.categories else None
    num_cats = len(categories) if categories else len(TIKI_CATEGORIES)
    per_cat = args.per_category or (args.limit // num_cats)

    logger.info(f"Starting Tiki scraper")
    logger.info(f"  Categories: {categories or 'all'}")
    logger.info(f"  Limit per category: {per_cat}")
    logger.info(f"  Total limit: {args.limit}")

    scraper = TikiScraper(headless=not args.no_headless)

    try:
        products = await scraper.scrape_all(
            categories=categories,
            limit_per_category=per_cat,
            use_api=not args.use_html
        )

        # Trim to total limit
        if len(products) > args.limit:
            products = products[:args.limit]
            scraper.products = products

        scraper.save_to_json(args.output)

        # Print summary
        print(f"\n{'='*60}")
        print(f"SCRAPING COMPLETE")
        print(f"{'='*60}")
        print(f"Total products: {len(products)}")
        print(f"Output file: {args.output}")

        # Category breakdown
        cat_counts = {}
        for p in products:
            cat_counts[p.category_source] = cat_counts.get(p.category_source, 0) + 1
        print(f"\nBy category:")
        for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(main())
