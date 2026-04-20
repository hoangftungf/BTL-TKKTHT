"""
Category Repository Implementation
"""
from typing import Optional, List
from uuid import UUID

from ...domain.entities.category import Category
from ...domain.repositories.category_repository import CategoryRepository
from ..models.category_model import CategoryModel


class DjangoCategoryRepository(CategoryRepository):
    """Django ORM implementation of CategoryRepository"""

    def _to_entity(self, model: CategoryModel) -> Category:
        """Convert ORM model to domain entity"""
        return Category(
            id=model.id,
            name=model.name,
            slug=model.slug,
            description=model.description,
            image_url=model.image.url if model.image else None,
            parent_id=model.parent_id,
            is_active=model.is_active,
            display_order=model.display_order,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model_data(self, entity: Category) -> dict:
        """Convert domain entity to model data dict"""
        return {
            'id': entity.id,
            'name': entity.name,
            'slug': entity.slug,
            'description': entity.description,
            'parent_id': entity.parent_id,
            'is_active': entity.is_active,
            'display_order': entity.display_order,
        }

    def get_by_id(self, category_id: UUID) -> Optional[Category]:
        try:
            model = CategoryModel.objects.get(pk=category_id)
            return self._to_entity(model)
        except CategoryModel.DoesNotExist:
            return None

    def get_by_slug(self, slug: str) -> Optional[Category]:
        try:
            model = CategoryModel.objects.get(slug=slug)
            return self._to_entity(model)
        except CategoryModel.DoesNotExist:
            return None

    def list_root_categories(self) -> List[Category]:
        models = CategoryModel.objects.filter(
            parent__isnull=True, is_active=True
        ).order_by('display_order', 'name')
        return [self._to_entity(m) for m in models]

    def list_children(self, parent_id: UUID) -> List[Category]:
        models = CategoryModel.objects.filter(
            parent_id=parent_id, is_active=True
        ).order_by('display_order', 'name')
        return [self._to_entity(m) for m in models]

    def list_all_active(self) -> List[Category]:
        models = CategoryModel.objects.filter(
            is_active=True
        ).order_by('display_order', 'name')
        return [self._to_entity(m) for m in models]

    def save(self, category: Category) -> Category:
        data = self._to_model_data(category)
        model, created = CategoryModel.objects.update_or_create(
            id=category.id,
            defaults=data
        )
        return self._to_entity(model)

    def delete(self, category_id: UUID) -> bool:
        deleted, _ = CategoryModel.objects.filter(pk=category_id).delete()
        return deleted > 0

    def exists_by_slug(self, slug: str) -> bool:
        return CategoryModel.objects.filter(slug=slug).exists()

    def get_product_count(self, category_id: UUID) -> int:
        from ..models.product_model import ProductModel
        return ProductModel.objects.filter(
            category_id=category_id, status='active'
        ).count()
