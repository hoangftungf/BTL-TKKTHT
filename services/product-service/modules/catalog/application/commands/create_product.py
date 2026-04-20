"""
Create Product Command
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from decimal import Decimal


@dataclass
class CreateProductCommand:
    """Command de tao san pham moi"""

    name: str
    slug: str
    sku: str
    price: Decimal
    seller_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    brand: str = ''
    description: str = ''
    short_description: str = ''
    compare_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    stock_quantity: int = 0
    low_stock_threshold: int = 10
    weight: Optional[Decimal] = None
    is_featured: bool = False
    attributes: dict = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}
