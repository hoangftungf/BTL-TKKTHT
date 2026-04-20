"""
Product Application Service
Xu ly cac use case lien quan den Product
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal

from ...domain.entities.product import Product, ProductStatus
from ...domain.repositories.product_repository import ProductRepository
from ...domain.value_objects.money import Money
from ...domain.value_objects.sku import SKU


class ProductService:
    """Product Application Service - Orchestrate use cases"""

    def __init__(self, product_repository: ProductRepository):
        self._repository = product_repository

    def get_product(self, product_id: UUID) -> Optional[Product]:
        """Lay thong tin san pham va tang view count"""
        product = self._repository.get_by_id(product_id)
        if product:
            self._repository.increment_view_count(product_id)
        return product

    def get_product_by_slug(self, slug: str) -> Optional[Product]:
        """Lay san pham theo slug"""
        return self._repository.get_by_slug(slug)

    def list_products(
        self,
        category_id: Optional[UUID] = None,
        brand: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        ordering: str = '-created_at',
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Lay danh sach san pham voi filter"""
        products, total = self._repository.list_active(
            category_id=category_id,
            brand=brand,
            min_price=min_price,
            max_price=max_price,
            ordering=ordering,
            page=page,
            page_size=page_size
        )
        return {
            'products': products,
            'total': total,
            'page': page,
            'page_size': page_size
        }

    def search_products(self, query: str, limit: int = 50) -> List[Product]:
        """Tim kiem san pham"""
        if not query or len(query) < 2:
            return []
        return self._repository.search(query, limit)

    def get_featured_products(self, limit: int = 10) -> List[Product]:
        """Lay san pham noi bat"""
        return self._repository.get_featured(limit)

    def get_products_by_category(
        self,
        category_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Lay san pham theo danh muc"""
        products, total = self._repository.get_by_category(
            category_id=category_id,
            page=page,
            page_size=page_size
        )
        return {
            'products': products,
            'total': total,
            'page': page,
            'page_size': page_size
        }

    def create_product(
        self,
        name: str,
        slug: str,
        sku: str,
        price: Decimal,
        seller_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        brand: str = '',
        description: str = '',
        short_description: str = '',
        compare_price: Optional[Decimal] = None,
        stock_quantity: int = 0,
        **kwargs
    ) -> Product:
        """Tao san pham moi"""
        # Validate SKU unique
        if self._repository.exists_by_sku(sku):
            raise ValueError(f"SKU '{sku}' da ton tai")

        # Validate slug unique
        if self._repository.exists_by_slug(slug):
            raise ValueError(f"Slug '{slug}' da ton tai")

        # Create product entity
        product = Product.create(
            name=name,
            slug=slug,
            sku=sku,
            price=price,
            seller_id=seller_id,
            category_id=category_id,
            brand=brand,
            description=description,
            short_description=short_description,
            stock_quantity=stock_quantity,
            **kwargs
        )

        if compare_price:
            product.compare_price = Money(compare_price)

        return self._repository.save(product)

    def update_product(
        self,
        product_id: UUID,
        seller_id: Optional[UUID] = None,
        **update_data
    ) -> Product:
        """Cap nhat san pham"""
        product = self._repository.get_by_id(product_id)
        if not product:
            raise ValueError("San pham khong ton tai")

        # Check permission
        if product.seller_id and seller_id and product.seller_id != seller_id:
            raise PermissionError("Ban khong co quyen sua san pham nay")

        # Update fields
        for key, value in update_data.items():
            if hasattr(product, key) and value is not None:
                if key == 'price':
                    product.price = Money(value)
                elif key == 'compare_price':
                    product.compare_price = Money(value) if value else None
                elif key == 'sku':
                    product.sku = SKU(value)
                elif key == 'status':
                    product.status = ProductStatus(value)
                else:
                    setattr(product, key, value)

        return self._repository.save(product)

    def delete_product(self, product_id: UUID, seller_id: Optional[UUID] = None) -> bool:
        """Xoa san pham"""
        product = self._repository.get_by_id(product_id)
        if not product:
            raise ValueError("San pham khong ton tai")

        # Check permission
        if product.seller_id and seller_id and product.seller_id != seller_id:
            raise PermissionError("Ban khong co quyen xoa san pham nay")

        return self._repository.delete(product_id)

    def activate_product(self, product_id: UUID) -> Product:
        """Kich hoat san pham"""
        product = self._repository.get_by_id(product_id)
        if not product:
            raise ValueError("San pham khong ton tai")

        product.activate()
        return self._repository.save(product)

    def deactivate_product(self, product_id: UUID) -> Product:
        """Ngung ban san pham"""
        product = self._repository.get_by_id(product_id)
        if not product:
            raise ValueError("San pham khong ton tai")

        product.deactivate()
        return self._repository.save(product)

    def update_stock(self, product_id: UUID, quantity: int) -> bool:
        """Cap nhat ton kho"""
        product = self._repository.get_by_id(product_id)
        if not product:
            raise ValueError("San pham khong ton tai")

        product.update_stock(quantity)
        return self._repository.update_stock(product_id, quantity)

    def decrease_stock(self, product_id: UUID, quantity: int) -> bool:
        """Giam ton kho khi ban hang"""
        product = self._repository.get_by_id(product_id)
        if not product:
            raise ValueError("San pham khong ton tai")

        product.decrease_stock(quantity)
        return self._repository.update_stock(product_id, product.stock_quantity)
