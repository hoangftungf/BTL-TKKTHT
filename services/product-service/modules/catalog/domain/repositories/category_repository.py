"""
Category Repository Interface
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities.category import Category


class CategoryRepository(ABC):
    """Category Repository Interface"""

    @abstractmethod
    def get_by_id(self, category_id: UUID) -> Optional[Category]:
        """Lay danh muc theo ID"""
        pass

    @abstractmethod
    def get_by_slug(self, slug: str) -> Optional[Category]:
        """Lay danh muc theo slug"""
        pass

    @abstractmethod
    def list_root_categories(self) -> List[Category]:
        """Lay danh sach danh muc goc (khong co parent)"""
        pass

    @abstractmethod
    def list_children(self, parent_id: UUID) -> List[Category]:
        """Lay danh sach danh muc con"""
        pass

    @abstractmethod
    def list_all_active(self) -> List[Category]:
        """Lay tat ca danh muc active"""
        pass

    @abstractmethod
    def save(self, category: Category) -> Category:
        """Luu danh muc"""
        pass

    @abstractmethod
    def delete(self, category_id: UUID) -> bool:
        """Xoa danh muc"""
        pass

    @abstractmethod
    def exists_by_slug(self, slug: str) -> bool:
        """Kiem tra slug da ton tai"""
        pass

    @abstractmethod
    def get_product_count(self, category_id: UUID) -> int:
        """Dem so san pham trong danh muc"""
        pass
