"""D402 middleware for IATP FastAPI servers (utility agents)."""

import logging
from typing import Callable, Optional
from fastapi import Request
from fastapi.responses import JSONResponse, HTMLResponse

from .fastapi_middleware.middleware import require_payment as d402_require_payment
from .types import Price, PaywallConfig, HTTPInputSchema
from typing import Callable, Dict
from typing_extensions import TypedDict

from .models import D402Config, PaymentScheme

# FacilitatorConfig (copied from d402)
class FacilitatorConfig(TypedDict, total=False):
    url: str
    create_headers: Callable[[], dict[str, dict[str, str]]]

logger = logging.getLogger(__name__)


class D402IATPMiddleware:
    """Middleware that integrates d402 payments into IATP servers.
    
    This middleware wraps the Coinbase d402 middleware and adapts it for
    IATP utility agents, connecting to the custom IATP Settlement Layer.
    """
    
    def __init__(self, config: D402Config):
        """Initialize the d402 IATP middleware.
        
        Args:
            config: D402 configuration including pricing and facilitator settings
        """
        self.config = config
        self.facilitator_config: FacilitatorConfig = {
            "url": config.facilitator_url,
        }
        
        # Add authentication headers if API key is provided
        if config.facilitator_api_key:
            async def create_headers():
                return {
                    "verify": {"Authorization": f"Bearer {config.facilitator_api_key}"},
                    "settle": {"Authorization": f"Bearer {config.facilitator_api_key}"}
                }
            self.facilitator_config["create_headers"] = create_headers
    
    def create_middleware(
        self,
        skill_id: Optional[str] = None,
        custom_price: Optional[Price] = None,
        custom_description: Optional[str] = None,
    ) -> Callable:
        """Create a FastAPI middleware function for a specific skill or endpoint.
        
        Args:
            skill_id: Optional skill ID to use custom pricing
            custom_price: Optional override price
            custom_description: Optional override description
            
        Returns:
            FastAPI middleware function
        """
        if not self.config.enabled:
            # Return passthrough middleware if payments not enabled
            async def passthrough(request: Request, call_next: Callable):
                return await call_next(request)
            return passthrough
        
        # Determine the price to use
        if custom_price:
            price = custom_price
        elif skill_id and skill_id in self.config.skill_prices:
            price_config = self.config.skill_prices[skill_id]
            price = price_config.usd_amount
        else:
            price = self.config.default_price.usd_amount
        
        # Determine the description
        description = custom_description or self.config.service_description
        
        # Get the pricing configuration
        price_config = (
            self.config.skill_prices.get(skill_id) 
            if skill_id and skill_id in self.config.skill_prices
            else self.config.default_price
        )
        
        # Create the d402 middleware using Coinbase's implementation
        return d402_require_payment(
            price=price,
            pay_to_address=self.config.pay_to_address,
            path=self.config.protected_paths,
            description=description,
            mime_type="application/json",
            max_deadline_seconds=price_config.max_timeout_seconds,
            input_schema=HTTPInputSchema(
                query_params=None,
                body_type="json",
                body_fields=None,
                header_fields=None
            ),
            output_schema=None,
            discoverable=True,
            facilitator_config=self.facilitator_config,
            network=price_config.network,
            resource=None,  # Will be determined from request URL
            paywall_config=None,  # Could add custom paywall UI here
            custom_paywall_html=None
        )


def require_iatp_payment(
    config: D402Config,
    skill_id: Optional[str] = None,
    custom_price: Optional[Price] = None,
    custom_description: Optional[str] = None,
) -> Callable:
    """Convenience function to create d402 middleware for IATP.
    
    Usage:
        @app.middleware("http")
        async def payment_middleware(request: Request, call_next):
            middleware = require_iatp_payment(d402_config)
            return await middleware(request, call_next)
    
    Or for specific routes:
        @app.post("/process")
        async def process_request(request: Request):
            # Will require payment
            pass
        
        app.middleware("http")(
            require_iatp_payment(d402_config, skill_id="process_request")
        )
    
    Args:
        config: D402 configuration
        skill_id: Optional skill ID for custom pricing
        custom_price: Optional price override
        custom_description: Optional description override
        
    Returns:
        FastAPI middleware function
    """
    middleware = D402IATPMiddleware(config)
    return middleware.create_middleware(skill_id, custom_price, custom_description)


async def add_d402_info_to_agent_card(agent_card: dict, config: D402Config) -> dict:
    """Add d402 payment information to an agent card.
    
    This adds payment capabilities to the agent card for client discovery.
    
    Args:
        agent_card: The agent card dictionary
        config: D402 configuration
        
    Returns:
        Updated agent card with payment information
    """
    if not config.enabled:
        return agent_card
    
    # Add d402 payment information to metadata
    agent_card.setdefault("metadata", {})
    agent_card["metadata"]["d402"] = {
        "enabled": True,
        "paymentSchemes": [PaymentScheme.EXACT.value],
        "networks": [config.default_price.network],
        "defaultPrice": {
            "usdAmount": config.default_price.usd_amount,
            "network": config.default_price.network,
            "asset": config.default_price.asset_address,
            "maxTimeoutSeconds": config.default_price.max_timeout_seconds
        },
        "payToAddress": config.pay_to_address,
        "facilitatorUrl": config.facilitator_url,
        "skillPrices": {
            skill_id: {
                "usdAmount": price.usd_amount,
                "network": price.network,
                "asset": price.asset_address,
                "maxTimeoutSeconds": price.max_timeout_seconds
            }
            for skill_id, price in config.skill_prices.items()
        }
    }
    
    return agent_card

