"""
Anti-Corruption Layer (ACL) cho AI Services
=============================================
Transform dữ liệu từ domain services (product-service, order-service)
thành internal format của AI services.

Nếu product-service thay đổi API response, CHỈ cần sửa file này.
Tất cả AI services đều dùng ProductACL thay vì consume raw JSON.
"""
from typing import Any, Dict, List, Optional


class ProductACL:
    """
    Anti-Corruption Layer: Transform product-service response
    thành internal model chuẩn cho AI services.

    Usage:
        from lib.ai_core.acl import ProductACL

        # Transform API response → AI internal format
        product = ProductACL.from_api_response(raw_json)

        # Build embedding text
        text = ProductACL.to_embedding_text(product)
    """

    @staticmethod
    def from_api_response(raw: dict) -> dict:
        """Transform product-service API response → AI internal format.

        Đây là hàm duy nhất cần sửa nếu product-service thay đổi API.
        """
        return {
            'id': str(raw['id']),
            'name': raw.get('name', ''),
            'price': float(raw.get('price', 0)),
            'brand': raw.get('brand', ''),
            'category': ProductACL._extract_category_name(raw),
            'category_id': ProductACL._extract_category_id(raw),
            'description': raw.get('description', '') or raw.get('short_description', '') or '',
            'short_description': raw.get('short_description', ''),
            'image_url': ProductACL._extract_image(raw),
            'images': ProductACL._extract_images(raw),
            'specifications': ProductACL._extract_specifications(raw),
            'variants': ProductACL._extract_variants(raw),
            'color': raw.get('color', ''),
            'material': raw.get('material', ''),
            'status': raw.get('status', 'active'),
            'stock_quantity': raw.get('stock_quantity', 0),
            'rating_avg': float(raw.get('rating_avg', 0) or 0),
            'rating_count': raw.get('rating_count', 0),
            'sku': raw.get('sku', ''),
        }

    @staticmethod
    def to_embedding_text(product: dict) -> str:
        """Build structured text for embedding model.

        Thay thế `_build_product_text()` ở chatbot và recommendation.
        Fields separated by ' | ' cho embedding model thấy rõ boundaries.
        """
        parts = []

        if product.get('name'):
            parts.append(product['name'])
        if product.get('brand'):
            parts.append(product['brand'])
        if product.get('category'):
            parts.append(product['category'])
        if product.get('color'):
            parts.append(f"Màu: {product['color']}")
        if product.get('material'):
            parts.append(f"Chất liệu: {product['material']}")

        description = product.get('description', '')
        if description:
            desc_words = description.split()
            if len(desc_words) > 300:
                description = ' '.join(desc_words[:300])
            parts.append(description)

        # Specifications
        specs = product.get('specifications', {})
        if specs and isinstance(specs, dict):
            spec_parts = [f"{k}: {v}" for k, v in specs.items()]
            if spec_parts:
                parts.append(f"Thông số kỹ thuật: {', '.join(spec_parts)}")
        elif specs and isinstance(specs, str) and specs.strip():
            parts.append(f"Thông số kỹ thuật: {specs}")

        # Variants
        variants = product.get('variants', [])
        if variants and isinstance(variants, list):
            var_parts = []
            for v in variants:
                v_name = v.get('name', '')
                v_price = v.get('price')
                v_stock = v.get('stock_quantity')
                try:
                    price_str = f"{float(v_price):,.0f}đ" if v_price is not None else "Liên hệ"
                except (ValueError, TypeError):
                    price_str = "Liên hệ"
                stock_str = f"Còn {v_stock}" if v_stock is not None else "Còn hàng"
                var_parts.append(f"[{v_name} - Giá: {price_str} - {stock_str}]")
            if var_parts:
                parts.append(f"Các biến thể: {', '.join(var_parts)}")

        return ' | '.join(parts)

    @staticmethod
    def to_neo4j_properties(product: dict) -> dict:
        """Transform AI internal format → Neo4j node properties."""
        return {
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'brand': product['brand'],
            'category': product['category'],
            'status': product['status'],
            'stock': product['stock_quantity'],
            'rating_avg': product['rating_avg'],
            'rating_count': product['rating_count'],
        }

    # ------------------------------------------------------------------
    # Internal extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_category_name(raw: dict) -> str:
        """Category có thể là dict {id, name}, string, hoặc None."""
        cat = raw.get('category')
        if isinstance(cat, dict):
            return cat.get('name', '')
        return str(cat) if cat else ''

    @staticmethod
    def _extract_category_id(raw: dict) -> Optional[str]:
        """Extract category ID nếu category là dict."""
        cat = raw.get('category')
        if isinstance(cat, dict):
            return str(cat.get('id', '')) if cat.get('id') else None
        return None

    @staticmethod
    def _extract_image(raw: dict) -> str:
        """Image URL normalization — handle http:/ vs https:// và relative URLs."""
        # Try explicit image_url field first
        image_url = raw.get('image_url', '')
        if image_url:
            return ProductACL._normalize_url(image_url)

        # Try primary_image
        img = raw.get('primary_image', '')
        if img:
            return ProductACL._normalize_url(str(img))

        # Try images list
        images = raw.get('images', [])
        if images and isinstance(images, list):
            first = images[0]
            if isinstance(first, dict):
                url = first.get('image', '') or first.get('url', '') or first.get('image_url', '')
                return ProductACL._normalize_url(url) if url else ''
            return ProductACL._normalize_url(str(first)) if first else ''

        return ''

    @staticmethod
    def _extract_images(raw: dict) -> List[str]:
        """Extract all image URLs."""
        images = raw.get('images', [])
        if not images or not isinstance(images, list):
            return []

        urls = []
        for img in images:
            if isinstance(img, dict):
                url = img.get('image', '') or img.get('url', '') or img.get('image_url', '')
            else:
                url = str(img)
            if url:
                urls.append(ProductACL._normalize_url(url))
        return urls

    @staticmethod
    def _extract_specifications(raw: dict) -> dict:
        """Extract specifications — handle cả dict và string formats."""
        specs = raw.get('specifications', {})
        if isinstance(specs, str):
            import json
            try:
                return json.loads(specs)
            except (json.JSONDecodeError, TypeError):
                return {'raw': specs}
        return specs if isinstance(specs, dict) else {}

    @staticmethod
    def _extract_variants(raw: dict) -> List[Dict[str, Any]]:
        """Extract variants — handle cả list và nested formats."""
        variants = raw.get('variants', [])
        if not variants or not isinstance(variants, list):
            return []

        result = []
        for v in variants:
            if isinstance(v, dict):
                result.append({
                    'id': str(v.get('id', '')),
                    'name': v.get('name', ''),
                    'sku': v.get('sku', ''),
                    'price': float(v['price']) if v.get('price') else None,
                    'stock_quantity': v.get('stock_quantity', 0),
                    'attributes': v.get('attributes', {}),
                    'is_active': v.get('is_active', True),
                })
        return result

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Fix common URL issues: http:/ → http://, etc."""
        if not url:
            return ''
        url = str(url)
        if url.startswith('http:/') and not url.startswith('http://'):
            url = url.replace(':/', '://', 1)
        return url


class OrderACL:
    """ACL cho order-service responses."""

    @staticmethod
    def from_api_response(raw: dict) -> dict:
        """Transform order-service response → AI internal format."""
        return {
            'order_id': str(raw.get('id', '')),
            'order_number': raw.get('order_number', ''),
            'user_id': str(raw.get('user_id', '')),
            'status': raw.get('status', ''),
            'total_amount': float(raw.get('total_amount', 0)),
            'items': [
                {
                    'product_id': item.get('product_id', ''),
                    'product_name': item.get('product_name', ''),
                    'quantity': item.get('quantity', 1),
                    'price': float(item.get('price', 0)),
                }
                for item in raw.get('items', [])
            ],
            'created_at': raw.get('created_at', ''),
        }


class ReviewACL:
    """ACL cho review-service responses."""

    @staticmethod
    def from_api_response(raw: dict) -> dict:
        return {
            'review_id': str(raw.get('id', '')),
            'product_id': str(raw.get('product_id', '')),
            'user_id': str(raw.get('user_id', '')),
            'rating': raw.get('rating', 0),
            'comment': raw.get('comment', ''),
            'created_at': raw.get('created_at', ''),
        }
