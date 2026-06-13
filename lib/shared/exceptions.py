"""Shared domain exceptions."""


class DomainError(Exception):
    """Base exception for all domain errors."""
    pass


class InvalidMoneyError(DomainError):
    """Raised when Money value object validation fails."""
    pass


class InvalidAddressError(DomainError):
    """Raised when Address value object validation fails."""
    pass


class ProductNotFoundError(DomainError):
    """Raised when a product is not found."""
    pass


class UserNotFoundError(DomainError):
    """Raised when a user is not found."""
    pass


class EventPublishError(DomainError):
    """Raised when publishing a domain event fails."""
    pass
