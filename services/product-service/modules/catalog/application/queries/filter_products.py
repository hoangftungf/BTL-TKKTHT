"""
Filter Products Query
"""
from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID


@dataclass
class FilterProductsQuery:
    """Query de loc san pham nang cao"""

    query: Optional[str] = None
    category_ids: Optional[List[UUID]] = None
    brands: Optional[List[str]] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_rating: Optional[float] = None
    in_stock_only: bool = False
    on_sale_only: bool = False
    ordering: str = '-created_at'
    page: int = 1
    page_size: int = 20
