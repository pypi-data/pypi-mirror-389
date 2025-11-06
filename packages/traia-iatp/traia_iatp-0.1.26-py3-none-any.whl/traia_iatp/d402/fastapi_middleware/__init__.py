"""FastAPI middleware for d402 payments."""

from .middleware import require_payment

__all__ = ["require_payment"]

