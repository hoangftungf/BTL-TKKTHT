"""
Update Product Command
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from decimal import Decimal


@dataclass
class UpdateProductCommand:
    """Command de cap nhat san pham"""

    product_id: UUID
    seller_id: Optional[UUID] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    price: Optional[Decimal] = None
    compare_price: Optional[Decimal] = None
    category_id: Optional[UUID] = None
    brand: Optional[str] = None
    status: Optional[str] = None
    stock_quantity: Optional[int] = None
    is_featured: Optional[bool] = None
    attributes: Optional[dict] = None
