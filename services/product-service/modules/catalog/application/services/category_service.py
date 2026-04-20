"""
Category Application Service
"""
from typing import Optional, List
from uuid import UUID

from ...domain.entities.category import Category
from ...domain.repositories.category_repository import CategoryRepository


class CategoryService:
    """Category Application Service"""

    def __init__(self, category_repository: CategoryRepository):
        self._repository = category_repository

    def get_category(self, category_id: UUID) -> Optional[Category]:
        """Lay danh muc theo ID"""
        return self._repository.get_by_id(category_id)

    def get_category_by_slug(self, slug: str) -> Optional[Category]:
        """Lay danh muc theo slug"""
        return self._repository.get_by_slug(slug)

    def list_root_categories(self) -> List[Category]:
        """Lay danh sach danh muc goc"""
        return self._repository.list_root_categories()

    def list_children(self, parent_id: UUID) -> List[Category]:
        """Lay danh muc con"""
        return self._repository.list_children(parent_id)

    def get_category_tree(self) -> List[Category]:
        """Lay cay danh muc (root categories voi children)"""
        root_categories = self._repository.list_root_categories()

        for category in root_categories:
            category.children = self._repository.list_children(category.id)
            category.product_count = self._repository.get_product_count(category.id)

            # Load sub-children (2 levels)
            for child in category.children:
                child.children = self._repository.list_children(child.id)
                child.product_count = self._repository.get_product_count(child.id)

        return root_categories

    def create_category(
        self,
        name: str,
        slug: str,
        description: str = '',
        parent_id: Optional[UUID] = None,
        **kwargs
    ) -> Category:
        """Tao danh muc moi"""
        # Validate slug unique
        if self._repository.exists_by_slug(slug):
            raise ValueError(f"Slug '{slug}' da ton tai")

        # Validate parent exists
        if parent_id:
            parent = self._repository.get_by_id(parent_id)
            if not parent:
                raise ValueError("Danh muc cha khong ton tai")

        category = Category.create(
            name=name,
            slug=slug,
            description=description,
            parent_id=parent_id,
            **kwargs
        )

        return self._repository.save(category)

    def update_category(self, category_id: UUID, **update_data) -> Category:
        """Cap nhat danh muc"""
        category = self._repository.get_by_id(category_id)
        if not category:
            raise ValueError("Danh muc khong ton tai")

        for key, value in update_data.items():
            if hasattr(category, key) and value is not None:
                setattr(category, key, value)

        return self._repository.save(category)

    def delete_category(self, category_id: UUID) -> bool:
        """Xoa danh muc"""
        category = self._repository.get_by_id(category_id)
        if not category:
            raise ValueError("Danh muc khong ton tai")

        # Check if has products
        product_count = self._repository.get_product_count(category_id)
        if product_count > 0:
            raise ValueError(f"Khong the xoa danh muc co {product_count} san pham")

        # Check if has children
        children = self._repository.list_children(category_id)
        if children:
            raise ValueError("Khong the xoa danh muc co danh muc con")

        return self._repository.delete(category_id)

    def activate_category(self, category_id: UUID) -> Category:
        """Kich hoat danh muc"""
        category = self._repository.get_by_id(category_id)
        if not category:
            raise ValueError("Danh muc khong ton tai")

        category.activate()
        return self._repository.save(category)

    def deactivate_category(self, category_id: UUID) -> Category:
        """Vo hieu hoa danh muc"""
        category = self._repository.get_by_id(category_id)
        if not category:
            raise ValueError("Danh muc khong ton tai")

        category.deactivate()
        return self._repository.save(category)
