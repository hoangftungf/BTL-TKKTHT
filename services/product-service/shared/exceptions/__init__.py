"""
Shared Exceptions
"""


class DomainException(Exception):
    """Base exception cho domain errors"""
    pass


class EntityNotFoundError(DomainException):
    """Entity khong tim thay"""
    pass


class ValidationError(DomainException):
    """Loi validation"""
    pass


class PermissionDeniedError(DomainException):
    """Khong co quyen"""
    pass


class DuplicateEntityError(DomainException):
    """Entity bi trung"""
    pass
