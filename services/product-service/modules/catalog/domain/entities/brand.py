"""
Brand Entity
"""
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime


@dataclass
class Brand:
    """Brand Entity - Thuong hieu san pham"""

    id: UUID
    name: str
    slug: str
    description: str = ''
    logo_url: Optional[str] = None
    website: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(
        cls,
        name: str,
        slug: str,
        description: str = '',
        logo_url: Optional[str] = None,
        website: Optional[str] = None,
    ) -> 'Brand':
        """Factory method de tao Brand moi"""
        return cls(
            id=uuid4(),
            name=name,
            slug=slug,
            description=description,
            logo_url=logo_url,
            website=website,
        )

    def activate(self) -> None:
        """Kich hoat thuong hieu"""
        self.is_active = True
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """Vo hieu hoa thuong hieu"""
        self.is_active = False
        self.updated_at = datetime.now()
