"""Traia IATP - Inter Agent Transfer Protocol package."""

from .core.models import UtilityAgent, MCPServer, AgentCard
from .server.iatp_server_agent_generator import IATPServerAgentGenerator
from .registry.mongodb_registry import UtilityAgentRegistry, MCPServerRegistry
from .registry.iatp_search_api import find_utility_agent
from .client.a2a_client import UtilityAgencyTool, create_utility_agency_tools
from .utils.docker_utils import LocalDockerRunner, run_generated_agent_locally, use_run_local_docker_script

# X402 payment integration
from .x402 import (
    X402Config,
    X402PaymentInfo,
    X402ServicePrice,
    PaymentScheme,
    X402IATPMiddleware,
    require_iatp_payment,
    X402IATPClient,
    IATPSettlementFacilitator,
)
from .client.x402_a2a_client import X402A2AClient, create_x402_a2a_client

__version__ = "0.1.23"

__all__ = [
    # Core models
    "UtilityAgent",
    "MCPServer", 
    "AgentCard",
    # Server components
    "IATPServerAgentGenerator",
    # Registry
    "UtilityAgentRegistry",
    "MCPServerRegistry",
    "find_utility_agent",
    # Client
    "UtilityAgencyTool",
    "create_utility_agency_tools",
    # Docker utilities
    "LocalDockerRunner",
    "run_generated_agent_locally",
    "use_run_local_docker_script",
    # X402 payment integration
    "X402Config",
    "X402PaymentInfo",
    "X402ServicePrice",
    "PaymentScheme",
    "X402IATPMiddleware",
    "require_iatp_payment",
    "X402IATPClient",
    "IATPSettlementFacilitator",
    "X402A2AClient",
    "create_x402_a2a_client",
]
