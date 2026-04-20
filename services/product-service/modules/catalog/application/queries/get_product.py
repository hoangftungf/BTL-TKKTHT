"""
Get Product Query
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class GetProductQuery:
    """Query de lay san pham theo ID hoac slug"""

    product_id: Optional[UUID] = None
    slug: Optional[str] = None
    increment_view: bool = True

    def __post_init__(self):
        if not self.product_id and not self.slug:
            raise ValueError("Phai cung cap product_id hoac slug")
