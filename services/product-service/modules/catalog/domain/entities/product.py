"""
Product Entity - Core domain entity
Logic nghiep vu thuan, khong phu thuoc framework
"""
from dataclasses import dataclass, field
from typing import Optional, List
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime
from enum import Enum

from ..value_objects.money import Money
from ..value_objects.sku import SKU


class ProductStatus(Enum):
    DRAFT = 'draft'
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    OUT_OF_STOCK = 'out_of_stock'


@dataclass
class Product:
    """Product Aggregate Root"""

    id: UUID
    name: str
    slug: str
    sku: SKU
    price: Money
    category_id: Optional[UUID] = None
    brand: str = ''
    description: str = ''
    short_description: str = ''
    compare_price: Optional[Money] = None
    cost_price: Optional[Money] = None
    status: ProductStatus = ProductStatus.DRAFT
    stock_quantity: int = 0
    low_stock_threshold: int = 10
    weight: Optional[Decimal] = None
    is_featured: bool = False
    view_count: int = 0
    sold_count: int = 0
    rating_avg: Decimal = Decimal('0')
    rating_count: int = 0
    seller_id: Optional[UUID] = None
    attributes: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(
        cls,
        name: str,
        slug: str,
        sku: str,
        price: Decimal,
        category_id: Optional[UUID] = None,
        brand: str = '',
        description: str = '',
        seller_id: Optional[UUID] = None,
        **kwargs
    ) -> 'Product':
        """Factory method de tao Product moi"""
        return cls(
            id=uuid4(),
            name=name,
            slug=slug,
            sku=SKU(sku),
            price=Money(price),
            category_id=category_id,
            brand=brand,
            description=description,
            seller_id=seller_id,
            **kwargs
        )

    @property
    def is_on_sale(self) -> bool:
        """Kiem tra san pham co dang giam gia"""
        if self.compare_price is None:
            return False
        return self.compare_price.amount > self.price.amount

    @property
    def discount_percent(self) -> int:
        """Tinh phan tram giam gia"""
        if not self.is_on_sale:
            return 0
        return int((1 - self.price.amount / self.compare_price.amount) * 100)

    @property
    def is_low_stock(self) -> bool:
        """Kiem tra ton kho thap"""
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def is_in_stock(self) -> bool:
        """Kiem tra con hang"""
        return self.stock_quantity > 0

    def activate(self) -> None:
        """Kich hoat san pham"""
        if self.stock_quantity <= 0:
            raise ValueError("Khong the kich hoat san pham het hang")
        self.status = ProductStatus.ACTIVE
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """Ngung ban san pham"""
        self.status = ProductStatus.INACTIVE
        self.updated_at = datetime.now()

    def update_stock(self, quantity: int) -> None:
        """Cap nhat so luong ton kho"""
        if quantity < 0:
            raise ValueError("So luong ton kho khong the am")
        self.stock_quantity = quantity
        if quantity == 0:
            self.status = ProductStatus.OUT_OF_STOCK
        self.updated_at = datetime.now()

    def decrease_stock(self, quantity: int) -> None:
        """Giam ton kho khi ban hang"""
        if quantity > self.stock_quantity:
            raise ValueError("Khong du hang trong kho")
        self.stock_quantity -= quantity
        if self.stock_quantity == 0:
            self.status = ProductStatus.OUT_OF_STOCK
        self.updated_at = datetime.now()

    def increase_stock(self, quantity: int) -> None:
        """Tang ton kho khi nhap hang"""
        if quantity < 0:
            raise ValueError("So luong nhap phai lon hon 0")
        self.stock_quantity += quantity
        if self.status == ProductStatus.OUT_OF_STOCK:
            self.status = ProductStatus.ACTIVE
        self.updated_at = datetime.now()

    def increment_view(self) -> None:
        """Tang luot xem"""
        self.view_count += 1

    def update_rating(self, new_rating: Decimal, new_count: int) -> None:
        """Cap nhat danh gia"""
        self.rating_avg = new_rating
        self.rating_count = new_count
        self.updated_at = datetime.now()

    def update_price(self, new_price: Decimal, compare_price: Optional[Decimal] = None) -> None:
        """Cap nhat gia san pham"""
        if new_price < 0:
            raise ValueError("Gia khong the am")
        self.price = Money(new_price)
        if compare_price is not None:
            self.compare_price = Money(compare_price)
        self.updated_at = datetime.now()

    def can_be_purchased(self, quantity: int = 1) -> bool:
        """Kiem tra co the mua duoc khong"""
        return (
            self.status == ProductStatus.ACTIVE and
            self.stock_quantity >= quantity
        )
