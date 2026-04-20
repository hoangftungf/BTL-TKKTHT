"""
Money Value Object
Value Objects la immutable, khong co identity
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Union


@dataclass(frozen=True)
class Money:
    """Money Value Object - Dai dien cho gia tri tien te"""

    amount: Decimal
    currency: str = 'VND'

    def __post_init__(self):
        # Validate
        if self.amount < 0:
            raise ValueError("So tien khong the am")
        # Round to 0 decimal places for VND
        object.__setattr__(
            self, 'amount',
            Decimal(self.amount).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        )

    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Khong the cong tien khac loai tien te")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Khong the tru tien khac loai tien te")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, multiplier: Union[int, float, Decimal]) -> 'Money':
        return Money(self.amount * Decimal(str(multiplier)), self.currency)

    def __truediv__(self, divisor: Union[int, float, Decimal]) -> 'Money':
        if divisor == 0:
            raise ValueError("Khong the chia cho 0")
        return Money(self.amount / Decimal(str(divisor)), self.currency)

    def __lt__(self, other: 'Money') -> bool:
        return self.amount < other.amount

    def __le__(self, other: 'Money') -> bool:
        return self.amount <= other.amount

    def __gt__(self, other: 'Money') -> bool:
        return self.amount > other.amount

    def __ge__(self, other: 'Money') -> bool:
        return self.amount >= other.amount

    def format(self) -> str:
        """Format gia tri tien te"""
        if self.currency == 'VND':
            return f"{self.amount:,.0f} VND"
        return f"{self.amount:,.2f} {self.currency}"

    @classmethod
    def zero(cls, currency: str = 'VND') -> 'Money':
        """Tao gia tri tien = 0"""
        return cls(Decimal('0'), currency)

    def is_zero(self) -> bool:
        """Kiem tra gia tri = 0"""
        return self.amount == 0
