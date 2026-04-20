"""
Category Entity
"""
from dataclasses import dataclass, field
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime


@dataclass
class Category:
    """Category Entity - Danh muc san pham"""

    id: UUID
    name: str
    slug: str
    description: str = ''
    image_url: Optional[str] = None
    parent_id: Optional[UUID] = None
    is_active: bool = True
    display_order: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Transient field - khong luu vao DB
    children: List['Category'] = field(default_factory=list)
    product_count: int = 0

    @classmethod
    def create(
        cls,
        name: str,
        slug: str,
        description: str = '',
        parent_id: Optional[UUID] = None,
        **kwargs
    ) -> 'Category':
        """Factory method de tao Category moi"""
        return cls(
            id=uuid4(),
            name=name,
            slug=slug,
            description=description,
            parent_id=parent_id,
            **kwargs
        )

    @property
    def is_root(self) -> bool:
        """Kiem tra co phai danh muc goc"""
        return self.parent_id is None

    @property
    def has_children(self) -> bool:
        """Kiem tra co danh muc con"""
        return len(self.children) > 0

    def activate(self) -> None:
        """Kich hoat danh muc"""
        self.is_active = True
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """Vo hieu hoa danh muc"""
        self.is_active = False
        self.updated_at = datetime.now()

    def update_display_order(self, order: int) -> None:
        """Cap nhat thu tu hien thi"""
        self.display_order = order
        self.updated_at = datetime.now()

    def move_to_parent(self, parent_id: Optional[UUID]) -> None:
        """Di chuyen danh muc sang parent khac"""
        if parent_id == self.id:
            raise ValueError("Danh muc khong the la con cua chinh no")
        self.parent_id = parent_id
        self.updated_at = datetime.now()
