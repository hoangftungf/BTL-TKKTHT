"""
SKU Value Object
"""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SKU:
    """SKU Value Object - Ma san pham duy nhat"""

    value: str

    def __post_init__(self):
        # Validate SKU format
        if not self.value:
            raise ValueError("SKU khong duoc de trong")
        if len(self.value) > 100:
            raise ValueError("SKU khong duoc vuot qua 100 ky tu")
        # Normalize to uppercase
        object.__setattr__(self, 'value', self.value.upper().strip())

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other) -> bool:
        if isinstance(other, SKU):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.upper().strip()
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    @classmethod
    def generate(cls, category_code: str, product_id: str) -> 'SKU':
        """Tao SKU tu ma danh muc va id san pham"""
        sku_value = f"{category_code}-{product_id}".upper()
        return cls(sku_value)

    def matches_pattern(self, pattern: str) -> bool:
        """Kiem tra SKU co khop voi pattern (regex)"""
        return bool(re.match(pattern, self.value))
