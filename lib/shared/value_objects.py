"""
Value Objects dùng chung toàn hệ thống.
Tất cả đều immutable (frozen dataclass) — tự validate khi khởi tạo.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Money:
    """Value Object: Tiền tệ — immutable, self-validating.

    Usage:
        price = Money(Decimal('100000'))
        price.to_float()  # → 100000.0
        price.to_neo4j()  # → 100000.0 (Neo4j不支持Decimal)
    """
    amount: Decimal
    currency: str = "VND"

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))
        if self.amount < 0:
            raise ValueError(f"Money amount cannot be negative: {self.amount}")
        if self.currency not in ("VND", "USD"):
            raise ValueError(f"Unsupported currency: {self.currency}")

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, multiplier: int | float | Decimal) -> "Money":
        return Money(self.amount * Decimal(str(multiplier)), self.currency)

    def __repr__(self) -> str:
        if self.currency == "VND":
            return f"{self.amount:,.0f}₫"
        return f"{self.currency} {self.amount:,.2f}"

    def to_float(self) -> float:
        """Serialize to float (cho JSON response)."""
        return float(self.amount)

    def to_decimal(self) -> Decimal:
        return self.amount

    def to_neo4j(self) -> float:
        """Neo4j không support Decimal → cast to float."""
        return float(self.amount)


@dataclass(frozen=True)
class Address:
    """Value Object: Địa chỉ thống nhất toàn hệ thống.

    Dùng chung cho order-service, user-service, shipping-service.
    """
    province: str
    district: str
    ward: str
    street: str
    address_type: str = "home"  # home | office | other

    def __post_init__(self):
        if not self.province or not self.district:
            raise ValueError("Province and district are required")
        if self.address_type not in ("home", "office", "other"):
            raise ValueError(f"Invalid address_type: {self.address_type}")

    def full_address(self) -> str:
        parts = [self.street, self.ward, self.district, self.province]
        return ", ".join(p for p in parts if p)

    def to_dict(self) -> dict:
        return {
            "province": self.province,
            "district": self.district,
            "ward": self.ward,
            "street": self.street,
        }

    def to_order_format(self) -> dict:
        """Transform sang format của order-service."""
        return {
            "shipping_province": self.province,
            "shipping_district": self.district,
            "shipping_ward": self.ward,
            "shipping_address": self.street,
        }
