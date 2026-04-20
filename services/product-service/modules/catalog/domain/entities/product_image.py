"""
Product Image Entity
"""
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime


@dataclass
class ProductImage:
    """Product Image Entity"""

    id: UUID
    product_id: UUID
    image_url: str
    alt_text: str = ''
    is_primary: bool = False
    display_order: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(
        cls,
        product_id: UUID,
        image_url: str,
        alt_text: str = '',
        is_primary: bool = False,
        display_order: int = 0,
    ) -> 'ProductImage':
        """Factory method de tao ProductImage moi"""
        return cls(
            id=uuid4(),
            product_id=product_id,
            image_url=image_url,
            alt_text=alt_text,
            is_primary=is_primary,
            display_order=display_order,
        )

    def set_as_primary(self) -> None:
        """Dat lam anh chinh"""
        self.is_primary = True

    def unset_primary(self) -> None:
        """Bo anh chinh"""
        self.is_primary = False

    def update_order(self, order: int) -> None:
        """Cap nhat thu tu hien thi"""
        self.display_order = order
