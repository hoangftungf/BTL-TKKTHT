"""
Product Repository Interface (Port)
Dinh nghia interface cho repository, khong phu thuoc implementation
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities.product import Product


class ProductRepository(ABC):
    """Product Repository Interface - Port trong Hexagonal Architecture"""

    @abstractmethod
    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """Lay san pham theo ID"""
        pass

    @abstractmethod
    def get_by_sku(self, sku: str) -> Optional[Product]:
        """Lay san pham theo SKU"""
        pass

    @abstractmethod
    def get_by_slug(self, slug: str) -> Optional[Product]:
        """Lay san pham theo slug"""
        pass

    @abstractmethod
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
        """Lay danh sach san pham active voi filter"""
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 50) -> List[Product]:
        """Tim kiem san pham"""
        pass

    @abstractmethod
    def get_featured(self, limit: int = 10) -> List[Product]:
        """Lay san pham noi bat"""
        pass

    @abstractmethod
    def get_by_category(
        self,
        category_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Product], int]:
        """Lay san pham theo danh muc"""
        pass

    @abstractmethod
    def save(self, product: Product) -> Product:
        """Luu san pham (create hoac update)"""
        pass

    @abstractmethod
    def delete(self, product_id: UUID) -> bool:
        """Xoa san pham"""
        pass

    @abstractmethod
    def exists_by_sku(self, sku: str) -> bool:
        """Kiem tra SKU da ton tai"""
        pass

    @abstractmethod
    def exists_by_slug(self, slug: str) -> bool:
        """Kiem tra slug da ton tai"""
        pass

    @abstractmethod
    def update_stock(self, product_id: UUID, quantity: int) -> bool:
        """Cap nhat ton kho"""
        pass

    @abstractmethod
    def increment_view_count(self, product_id: UUID) -> bool:
        """Tang luot xem"""
        pass
