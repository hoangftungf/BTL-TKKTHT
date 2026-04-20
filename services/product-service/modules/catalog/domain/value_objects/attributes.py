"""
Product Attributes Value Object
Luu tru cac thuoc tinh dong cua san pham (JSON)
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass(frozen=True)
class ProductAttributes:
    """Product Attributes Value Object - Thuoc tinh san pham (JSONB)"""

    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Ensure data is dict
        if not isinstance(self.data, dict):
            raise ValueError("Attributes phai la dict")

    def get(self, key: str, default: Any = None) -> Any:
        """Lay gia tri thuoc tinh"""
        return self.data.get(key, default)

    def has(self, key: str) -> bool:
        """Kiem tra co thuoc tinh"""
        return key in self.data

    def keys(self) -> List[str]:
        """Lay danh sach key"""
        return list(self.data.keys())

    def to_dict(self) -> Dict[str, Any]:
        """Chuyen sang dict"""
        return dict(self.data)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> 'ProductAttributes':
        """Tao tu dict"""
        return cls(data or {})

    @classmethod
    def for_electronics(
        cls,
        brand: str,
        model: str,
        cpu: Optional[str] = None,
        ram: Optional[str] = None,
        storage: Optional[str] = None,
        screen_size: Optional[str] = None,
        **kwargs
    ) -> 'ProductAttributes':
        """Tao attributes cho san pham dien tu"""
        data = {
            'brand': brand,
            'model': model,
            **kwargs
        }
        if cpu:
            data['cpu'] = cpu
        if ram:
            data['ram'] = ram
        if storage:
            data['storage'] = storage
        if screen_size:
            data['screen_size'] = screen_size
        return cls(data)

    @classmethod
    def for_fashion(
        cls,
        size: str,
        color: str,
        material: Optional[str] = None,
        **kwargs
    ) -> 'ProductAttributes':
        """Tao attributes cho san pham thoi trang"""
        data = {
            'size': size,
            'color': color,
            **kwargs
        }
        if material:
            data['material'] = material
        return cls(data)
