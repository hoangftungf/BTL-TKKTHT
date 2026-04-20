"""
Product Variant Entity
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime

from ..value_objects.money import Money
from ..value_objects.sku import SKU


@dataclass
class ProductVariant:
    """Product Variant - Bien the san pham (size, color, etc.)"""

    id: UUID
    product_id: UUID
    name: str
    sku: SKU
    price: Money
    stock_quantity: int = 0
    attributes: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(
        cls,
        product_id: UUID,
        name: str,
        sku: str,
        price: Decimal,
        attributes: Optional[Dict[str, Any]] = None,
        stock_quantity: int = 0,
        **kwargs
    ) -> 'ProductVariant':
        """Factory method de tao Variant moi"""
        return cls(
            id=uuid4(),
            product_id=product_id,
            name=name,
            sku=SKU(sku),
            price=Money(price),
            attributes=attributes or {},
            stock_quantity=stock_quantity,
            **kwargs
        )

    @property
    def is_in_stock(self) -> bool:
        """Kiem tra con hang"""
        return self.stock_quantity > 0

    def update_stock(self, quantity: int) -> None:
        """Cap nhat ton kho"""
        if quantity < 0:
            raise ValueError("So luong khong the am")
        self.stock_quantity = quantity
        self.updated_at = datetime.now()

    def decrease_stock(self, quantity: int) -> None:
        """Giam ton kho"""
        if quantity > self.stock_quantity:
            raise ValueError("Khong du hang")
        self.stock_quantity -= quantity
        self.updated_at = datetime.now()

    def update_price(self, new_price: Decimal) -> None:
        """Cap nhat gia"""
        if new_price < 0:
            raise ValueError("Gia khong the am")
        self.price = Money(new_price)
        self.updated_at = datetime.now()

    def update_attributes(self, attributes: Dict[str, Any]) -> None:
        """Cap nhat thuoc tinh"""
        self.attributes = attributes
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Kich hoat bien the"""
        self.is_active = True
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """Vo hieu hoa bien the"""
        self.is_active = False
        self.updated_at = datetime.now()
