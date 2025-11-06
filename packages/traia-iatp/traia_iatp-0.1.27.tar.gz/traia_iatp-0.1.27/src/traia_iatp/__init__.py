"""Traia IATP - Inter Agent Transfer Protocol package."""

from .core.models import UtilityAgent, MCPServer, AgentCard
from .server.iatp_server_agent_generator import IATPServerAgentGenerator
from .registry.mongodb_registry import UtilityAgentRegistry, MCPServerRegistry
from .registry.iatp_search_api import find_utility_agent
from .client.a2a_client import UtilityAgencyTool, create_utility_agency_tools
from .utils.docker_utils import LocalDockerRunner, run_generated_agent_locally, use_run_local_docker_script

# D402 payment integration
from .d402 import (
    D402Config,
    D402PaymentInfo,
    D402ServicePrice,
    PaymentScheme,
    D402IATPMiddleware,
    require_iatp_payment,
    D402IATPClient,
    IATPSettlementFacilitator,
)
from .client.d402_a2a_client import D402A2AClient, create_d402_a2a_client

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
    # D402 payment integration
    "D402Config",
    "D402PaymentInfo",
    "D402ServicePrice",
    "PaymentScheme",
    "D402IATPMiddleware",
    "require_iatp_payment",
    "D402IATPClient",
    "IATPSettlementFacilitator",
    "D402A2AClient",
    "create_d402_a2a_client",
]
