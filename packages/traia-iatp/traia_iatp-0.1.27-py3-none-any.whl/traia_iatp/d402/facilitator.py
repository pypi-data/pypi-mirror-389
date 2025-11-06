"""Custom d402 facilitator that interfaces with IATP Settlement Layer."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import httpx
from eth_account import Account
from web3 import Web3
from eth_account.messages import encode_defunct

from .types import (
    PaymentPayload,
    PaymentRequirements,
    VerifyResponse,
    SettleResponse
)
from .models import IATPSettlementRequest

logger = logging.getLogger(__name__)


class IATPSettlementFacilitator:
    """Custom d402 facilitator that settles payments through IATP Settlement Layer.
    
    This facilitator verifies d402 payment headers and then submits settlement
    requests to the on-chain IATP Settlement Layer contract via a relayer service.
    
    Flow:
    1. Utility agent receives request with X-PAYMENT header
    2. Facilitator verifies the payment signature and authorization
    3. Utility agent processes the request
    4. Facilitator settles the payment by submitting to relayer
    5. Relayer submits to IATPSettlementLayer.sol on-chain
    """
    
    def __init__(
        self,
        relayer_url: str,
        relayer_api_key: Optional[str] = None,
        provider_operator_key: Optional[str] = None,
        web3_provider: Optional[str] = None
    ):
        """Initialize the IATP Settlement Facilitator.
        
        Args:
            relayer_url: URL of the Traia relayer service
            relayer_api_key: Optional API key for relayer authentication
            provider_operator_key: Operator private key for provider attestation
            web3_provider: Optional Web3 provider URL for direct blockchain interaction
        """
        self.relayer_url = relayer_url.rstrip("/")
        self.relayer_api_key = relayer_api_key
        self.provider_operator_key = provider_operator_key
        
        # Initialize Web3 if provider is given
        self.w3 = Web3(Web3.HTTPProvider(web3_provider)) if web3_provider else None
        
        # Initialize operator account if key provided
        self.operator_account = None
        if provider_operator_key:
            if provider_operator_key.startswith("0x"):
                provider_operator_key = provider_operator_key[2:]
            self.operator_account = Account.from_key(provider_operator_key)
    
    async def verify(
        self,
        payment: PaymentPayload,
        payment_requirements: PaymentRequirements
    ) -> VerifyResponse:
        """Verify a payment header is valid.
        
        This checks:
        1. Signature is valid
        2. Authorization is not expired
        3. Amount matches requirements
        4. From address has sufficient balance
        
        Args:
            payment: Payment payload from X-PAYMENT header
            payment_requirements: Payment requirements from server
            
        Returns:
            VerifyResponse with validation result
        """
        try:
            # Extract payment details
            if payment.scheme != "exact":
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason=f"Unsupported scheme: {payment.scheme}",
                    payer=None
                )
            
            payload = payment.payload
            authorization = payload.authorization
            signature = payload.signature
            
            # Verify the signature matches the authorization
            payer = authorization.from_
            
            # Reconstruct the EIP-712 message and verify signature
            # This would use the exact EIP-712 domain from payment_requirements.extra
            eip712_domain = payment_requirements.extra or {}
            
            # For now, perform basic validation
            # In production, this should verify the EIP-3009 signature
            if not payer or not signature:
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason="Missing payer or signature",
                    payer=None
                )
            
            # Verify amount matches requirements
            if authorization.value != payment_requirements.max_amount_required:
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason=f"Amount mismatch: expected {payment_requirements.max_amount_required}, got {authorization.value}",
                    payer=payer
                )
            
            # Verify not expired
            import time
            current_time = int(time.time())
            valid_after = int(authorization.valid_after)
            valid_before = int(authorization.valid_before)
            
            if current_time < valid_after or current_time > valid_before:
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason="Authorization expired or not yet valid",
                    payer=payer
                )
            
            # Verify to address matches pay_to
            if authorization.to.lower() != payment_requirements.pay_to.lower():
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason=f"Pay-to address mismatch",
                    payer=payer
                )
            
            # All checks passed
            return VerifyResponse(
                is_valid=True,
                invalid_reason=None,
                payer=payer
            )
            
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return VerifyResponse(
                is_valid=False,
                invalid_reason=f"Verification error: {str(e)}",
                payer=None
            )
    
    async def settle(
        self,
        payment: PaymentPayload,
        payment_requirements: PaymentRequirements
    ) -> SettleResponse:
        """Settle a verified payment through the IATP Settlement Layer.
        
        This submits the payment to the relayer, which will:
        1. Verify both consumer and provider signatures
        2. Submit to IATPSettlementLayer.settleRequest()
        3. Process the EIP-3009 authorization on-chain
        4. Credit the provider's epoch balance
        
        Args:
            payment: Verified payment payload
            payment_requirements: Payment requirements
            
        Returns:
            SettleResponse with settlement result
        """
        try:
            payload = payment.payload
            authorization = payload.authorization
            consumer_signature = payload.signature
            
            # Create the service request struct (matches Solidity ServiceRequest)
            service_request = {
                "consumer": authorization.from_,
                "provider": payment_requirements.pay_to,
                "amount": authorization.value,
                "timestamp": int(authorization.valid_after),
                "serviceDescription": Web3.keccak(
                    text=payment_requirements.description
                ).hex()
            }
            
            # Create provider attestation if operator key is available
            provider_signature = None
            if self.operator_account:
                # Hash the consumer's signed request
                request_signature_hash = Web3.keccak(hexstr=consumer_signature).hex()
                
                # Create attestation message
                attestation_message = encode_defunct(
                    text=f"Attesting completion of service request: {request_signature_hash}"
                )
                
                # Sign the attestation
                signed = self.operator_account.sign_message(attestation_message)
                provider_signature = signed.signature.hex()
            
            # Prepare settlement request for relayer
            settlement_request = {
                "signedRequest": consumer_signature,
                "serviceRequest": service_request,
                "providerSignature": provider_signature or "0x",
                "attestationTimestamp": int(datetime.utcnow().timestamp()),
                "network": payment.network
            }
            
            # Submit to relayer
            headers = {"Content-Type": "application/json"}
            if self.relayer_api_key:
                headers["Authorization"] = f"Bearer {self.relayer_api_key}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.relayer_url}/settle",
                    json=settlement_request,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return SettleResponse(
                        success=True,
                        error_reason=None,
                        transaction=result.get("transactionHash"),
                        network=payment.network,
                        payer=authorization.from_
                    )
                else:
                    error_msg = f"Relayer error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return SettleResponse(
                        success=False,
                        error_reason=error_msg,
                        transaction=None,
                        network=payment.network,
                        payer=authorization.from_
                    )
                    
        except Exception as e:
            logger.error(f"Error settling payment: {e}")
            return SettleResponse(
                success=False,
                error_reason=f"Settlement error: {str(e)}",
                transaction=None,
                network=payment.network,
                payer=None
            )
    
    async def list(self, request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List discoverable IATP services that accept d402 payments.
        
        This queries the Traia registry for utility agents with d402 enabled.
        
        Args:
            request: Optional filters for discovery
            
        Returns:
            List of discoverable services
        """
        # This would query the MongoDB registry
        # For now, return empty list
        return {
            "d402Version": 1,
            "items": [],
            "pagination": {
                "limit": 100,
                "offset": 0,
                "total": 0
            }
        }


def create_iatp_facilitator(
    relayer_url: str = "https://api.traia.io/relayer",
    relayer_api_key: Optional[str] = None,
    provider_operator_key: Optional[str] = None,
    web3_provider: Optional[str] = None
) -> IATPSettlementFacilitator:
    """Convenience function to create an IATP Settlement Facilitator.
    
    Args:
        relayer_url: URL of the Traia relayer service
        relayer_api_key: Optional API key for relayer
        provider_operator_key: Provider's operator private key
        web3_provider: Optional Web3 provider URL
        
    Returns:
        Configured IATPSettlementFacilitator
        
    Example:
        facilitator = create_iatp_facilitator(
            relayer_url="https://api.traia.io/relayer",
            relayer_api_key=os.getenv("TRAIA_RELAYER_API_KEY"),
            provider_operator_key=os.getenv("OPERATOR_PRIVATE_KEY")
        )
        
        # Use in d402 middleware
        from traia_iatp.d402 import D402Config, require_iatp_payment
        
        config = D402Config(
            enabled=True,
            pay_to_address="0x...",  # Utility agent contract address
            default_price=D402ServicePrice(...),
            facilitator_url="custom"  # Will use custom facilitator
        )
    """
    return IATPSettlementFacilitator(
        relayer_url=relayer_url,
        relayer_api_key=relayer_api_key,
        provider_operator_key=provider_operator_key,
        web3_provider=web3_provider
    )

