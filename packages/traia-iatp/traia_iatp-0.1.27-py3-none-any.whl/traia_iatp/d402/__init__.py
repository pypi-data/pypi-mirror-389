"""D402 payment integration for IATP protocol.

This module provides d402 (HTTP 402 Payment Required) payment capabilities
for the Inter-Agent Transfer Protocol (IATP). It enables utility agents to
accept payments and client agents to send payments for API access.

Components:
- middleware: FastAPI middleware for accepting d402 payments
- client: d402 client integration for sending payments
- facilitator: Custom facilitator that interfaces with IATPSettlementLayer
- models: Payment configuration models
"""

from .models import (
    D402Config,
    D402PaymentInfo,
    D402ServicePrice,
    PaymentScheme,
)
from .middleware import D402IATPMiddleware, require_iatp_payment
from .client import D402IATPClient
from .facilitator import IATPSettlementFacilitator

__all__ = [
    "D402Config",
    "D402PaymentInfo",
    "D402ServicePrice",
    "PaymentScheme",
    "D402IATPMiddleware",
    "require_iatp_payment",
    "D402IATPClient",
    "IATPSettlementFacilitator",
]

