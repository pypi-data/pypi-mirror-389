"""X402 payment integration for IATP protocol.

This module provides x402 (HTTP 402 Payment Required) payment capabilities
for the Inter-Agent Transfer Protocol (IATP). It enables utility agents to
accept payments and client agents to send payments for API access.

Components:
- middleware: FastAPI middleware for accepting x402 payments
- client: x402 client integration for sending payments
- facilitator: Custom facilitator that interfaces with IATPSettlementLayer
- models: Payment configuration models
"""

from .models import (
    X402Config,
    X402PaymentInfo,
    X402ServicePrice,
    PaymentScheme,
)
from .middleware import X402IATPMiddleware, require_iatp_payment
from .client import X402IATPClient
from .facilitator import IATPSettlementFacilitator

__all__ = [
    "X402Config",
    "X402PaymentInfo",
    "X402ServicePrice",
    "PaymentScheme",
    "X402IATPMiddleware",
    "require_iatp_payment",
    "X402IATPClient",
    "IATPSettlementFacilitator",
]

