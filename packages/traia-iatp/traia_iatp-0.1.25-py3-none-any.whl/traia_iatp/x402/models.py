"""X402 payment models for IATP protocol."""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PaymentScheme(str, Enum):
    """Payment schemes supported by x402."""
    EXACT = "exact"  # EIP-3009 exact payment


class X402ServicePrice(BaseModel):
    """Pricing configuration for an IATP service."""
    
    # Price per request in USD (e.g., "0.01" for 1 cent)
    usd_amount: str = Field(..., description="Price in USD per request")
    
    # Alternative: Price in TRAIA tokens (atomic units)
    traia_amount: Optional[str] = Field(None, description="Price in TRAIA tokens (atomic units)")
    
    # Network to accept payments on
    network: str = Field(default="base-mainnet", description="Blockchain network")
    
    # Asset to accept (USDC address or TRAIA token address)
    asset_address: str = Field(..., description="Token contract address")
    
    # Maximum timeout for payment completion
    max_timeout_seconds: int = Field(default=300, description="Max time to complete payment")


class X402Config(BaseModel):
    """Configuration for x402 payment integration in IATP."""
    
    # Enable/disable x402 payments
    enabled: bool = Field(default=False, description="Enable x402 payments")
    
    # Payment address (utility agent contract address)
    pay_to_address: str = Field(..., description="Ethereum address to receive payments")
    
    # Pricing per service/skill
    default_price: X402ServicePrice = Field(..., description="Default price for all services")
    skill_prices: Dict[str, X402ServicePrice] = Field(
        default_factory=dict, 
        description="Custom prices per skill ID"
    )
    
    # Facilitator configuration
    facilitator_url: str = Field(
        default="https://api.traia.io/x402/facilitator",
        description="URL of the x402 facilitator service"
    )
    
    # Custom facilitator authentication (if needed)
    facilitator_api_key: Optional[str] = Field(None, description="API key for facilitator")
    
    # Paths to gate with payments (* for all)
    protected_paths: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Paths that require payment"
    )
    
    # Service description for payment prompt
    service_description: str = Field(..., description="Description shown in payment UI")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class X402PaymentInfo(BaseModel):
    """Payment information for agent card discovery."""
    
    enabled: bool = Field(..., description="Whether x402 is enabled")
    payment_schemes: list[PaymentScheme] = Field(
        default_factory=lambda: [PaymentScheme.EXACT],
        description="Supported payment schemes"
    )
    networks: list[str] = Field(..., description="Supported blockchain networks")
    default_price: X402ServicePrice = Field(..., description="Default pricing")
    facilitator_url: str = Field(..., description="Facilitator service URL")
    
    class Config:
        use_enum_values = True


class IATPSettlementRequest(BaseModel):
    """Request to settle a payment through IATP settlement layer."""
    
    consumer: str = Field(..., description="Consumer address (client agent)")
    provider: str = Field(..., description="Provider address (utility agent)")
    amount: str = Field(..., description="Amount in atomic units")
    timestamp: int = Field(..., description="Request timestamp")
    service_description: str = Field(..., description="Description of service")
    consumer_signature: str = Field(..., description="Consumer's EIP-712 signature")
    provider_signature: str = Field(..., description="Provider's attestation signature")

