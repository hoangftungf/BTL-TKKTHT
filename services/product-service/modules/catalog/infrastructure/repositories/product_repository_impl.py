"""
Product Repository Implementation
Implement domain repository interface using Django ORM
"""
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from django.db.models import Q

from ...domain.entities.product import Product, ProductStatus
from ...domain.repositories.product_repository import ProductRepository
from ...domain.value_objects.money import Money
from ...domain.value_objects.sku import SKU
from ..models.product_model import ProductModel


class DjangoProductRepository(ProductRepository):
    """Django ORM implementation of ProductRepository"""

    def _to_entity(self, model: ProductModel) -> Product:
        """Convert ORM model to domain entity"""
        return Product(
            id=model.id,
            name=model.name,
            slug=model.slug,
            sku=SKU(model.sku),
            price=Money(model.price),
            category_id=model.category_id,
            brand=model.brand,
            description=model.description,
            short_description=model.short_description,
            compare_price=Money(model.compare_price) if model.compare_price else None,
            cost_price=Money(model.cost_price) if model.cost_price else None,
            status=ProductStatus(model.status),
            stock_quantity=model.stock_quantity,
            low_stock_threshold=model.low_stock_threshold,
            weight=model.weight,
            is_featured=model.is_featured,
            view_count=model.view_count,
            sold_count=model.sold_count,
            rating_avg=model.rating_avg,
            rating_count=model.rating_count,
            seller_id=model.seller_id,
            attributes=model.attributes or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model_data(self, entity: Product) -> dict:
        """Convert domain entity to model data dict"""
        return {
            'id': entity.id,
            'name': entity.name,
            'slug': entity.slug,
            'sku': str(entity.sku),
            'price': entity.price.amount,
            'category_id': entity.category_id,
            'brand': entity.brand,
            'description': entity.description,
            'short_description': entity.short_description,
            'compare_price': entity.compare_price.amount if entity.compare_price else None,
            'cost_price': entity.cost_price.amount if entity.cost_price else None,
            'status': entity.status.value,
            'stock_quantity': entity.stock_quantity,
            'low_stock_threshold': entity.low_stock_threshold,
            'weight': entity.weight,
            'is_featured': entity.is_featured,
            'view_count': entity.view_count,
            'sold_count': entity.sold_count,
            'rating_avg': entity.rating_avg,
            'rating_count': entity.rating_count,
            'seller_id': entity.seller_id,
            'attributes': entity.attributes,
        }

    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        try:
            model = ProductModel.objects.select_related('category').get(pk=product_id)
            return self._to_entity(model)
        except ProductModel.DoesNotExist:
            return None

    def get_by_sku(self, sku: str) -> Optional[Product]:
        try:
            model = ProductModel.objects.select_related('category').get(sku=sku.upper())
            return self._to_entity(model)
        except ProductModel.DoesNotExist:
            return None

    def get_by_slug(self, slug: str) -> Optional[Product]:
        try:
            model = ProductModel.objects.select_related('category').get(slug=slug)
            return self._to_entity(model)
        except ProductModel.DoesNotExist:
            return None

    def list_active(
        self,
        category_id: Optional[UUID] = None,
        brand: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        ordering: str = '-created_at',
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Product], int]:
        queryset = ProductModel.objects.filter(status='active').select_related('category')

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if brand:
            queryset = queryset.filter(brand__iexact=brand)
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        valid_orderings = ['price', '-price', 'name', '-name', '-sold_count', '-rating_avg', '-created_at']
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)

        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        models = queryset[start:end]

        return [self._to_entity(m) for m in models], total

    def search(self, query: str, limit: int = 50) -> List[Product]:
        models = ProductModel.objects.filter(
            status='active'
        ).filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(sku__icontains=query)
        ).select_related('category')[:limit]

        return [self._to_entity(m) for m in models]

    def get_featured(self, limit: int = 10) -> List[Product]:
        models = ProductModel.objects.filter(
            status='active', is_featured=True
        ).select_related('category').order_by('-created_at')[:limit]

        return [self._to_entity(m) for m in models]

    def get_by_category(
        self,
        category_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Product], int]:
        queryset = ProductModel.objects.filter(
            category_id=category_id, status='active'
        ).select_related('category')

        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        models = queryset[start:end]

        return [self._to_entity(m) for m in models], total

    def save(self, product: Product) -> Product:
        data = self._to_model_data(product)
        model, created = ProductModel.objects.update_or_create(
            id=product.id,
            defaults=data
        )
        return self._to_entity(model)

    def delete(self, product_id: UUID) -> bool:
        deleted, _ = ProductModel.objects.filter(pk=product_id).delete()
        return deleted > 0

    def exists_by_sku(self, sku: str) -> bool:
        return ProductModel.objects.filter(sku=sku.upper()).exists()

    def exists_by_slug(self, slug: str) -> bool:
        return ProductModel.objects.filter(slug=slug).exists()

    def update_stock(self, product_id: UUID, quantity: int) -> bool:
        updated = ProductModel.objects.filter(pk=product_id).update(
            stock_quantity=quantity,
            status='out_of_stock' if quantity == 0 else 'active'
        )
        return updated > 0

    def increment_view_count(self, product_id: UUID) -> bool:
        from django.db.models import F
        updated = ProductModel.objects.filter(pk=product_id).update(
            view_count=F('view_count') + 1
        )
        return updated > 0
