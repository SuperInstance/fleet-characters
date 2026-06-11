"""
AutoEnv — automatic environment discovery for fleet-midi agents.

Ports the OpenEnv auto/ subpackage pattern for the fleet-midi ecosystem.

Provides:
  - AutoEnv: Factory class for discovering and instantiating environments
  - FleetMidiEnvironment: Gymnasium-style per-agent environment client
  - FleetDiscovery: Port scanning and health check discovery
  - CueBuilder / AutoAction: Fluent cue payload construction
  - build_cue, build_think: Quick action helpers

Module hierarchy:
  auto/__init__.py     ← this file (public exports)
  auto/auto_env.py     ← AutoEnv + FleetMidiEnvironment
  auto/_discovery.py   ← FleetDiscovery + port mapping
  auto/auto_action.py  ← CueBuilder + build_cue + build_think
"""

# AutoEnv — main factory (used as AutoEnv.from_agent(...), etc.)
from .auto_env import AutoEnv, FleetMidiEnvironment, StepResult, AgentInfo

# Discovery
from ._discovery import (
    FleetDiscovery,
    AgentEndpoint,
    get_discovery,
    reset_discovery,
    check_agent_health,
    load_port_map,
    ALL_AGENT_NAMES,
)

# Action builders
from .auto_action import (
    build_cue,
    build_think,
    CueBuilder,
    AutoAction,  # legacy alias
    AGENT_PAYLOAD_KEYS,
)

__all__ = [
    # Factory
    "AutoEnv",
    # Environment client
    "FleetMidiEnvironment",
    "StepResult",
    "AgentInfo",
    # Discovery
    "FleetDiscovery",
    "AgentEndpoint",
    "get_discovery",
    "reset_discovery",
    "check_agent_health",
    "load_port_map",
    "ALL_AGENT_NAMES",
    # Action builders
    "build_cue",
    "build_think",
    "CueBuilder",
    "AutoAction",
    "AGENT_PAYLOAD_KEYS",
]
