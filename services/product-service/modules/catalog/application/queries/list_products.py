"""
List Products Query
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class ListProductsQuery:
    """Query de lay danh sach san pham"""

    category_id: Optional[UUID] = None
    brand: Optional[str] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    is_featured: Optional[bool] = None
    ordering: str = '-created_at'
    page: int = 1
    page_size: int = 20

    VALID_ORDERINGS = [
        'price', '-price', 'name', '-name',
        '-sold_count', '-rating_avg', '-created_at', 'created_at'
    ]

    def __post_init__(self):
        if self.ordering not in self.VALID_ORDERINGS:
            self.ordering = '-created_at'
        if self.page < 1:
            self.page = 1
        if self.page_size < 1 or self.page_size > 100:
            self.page_size = 20
