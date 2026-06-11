"""
Fleet agent port discovery — finds running fleet-midi agents on localhost.

Port convention (16 agents, starting at 2160):
  chord=2160, scale=2161, voicing=2162, tempo=2163, cc=2164,
  expression=2165, dynamics=2166, pan=2167, modulation=2168,
  arp=2169, groove=2170, velocity=2171, fx=2172, register=2173,
  melody=2174, bass=2175

Each agent exposes:
  GET /health  → {"status":"ok","agent":"fleet-midi-<name>"}
  GET /agent   → same
  POST /agent  → probe/cue/think handlers

Port map can be overridden via constructor or environment variable
  FLEET_MIDI_PORT_MAP='{"chord":2200,"scale":2201,...}'
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

# ─── Default Port Map ──────────────────────────────────────────────────

_DEFAULT_PORT_MAP: Dict[str, int] = {
    "chord": 2160,
    "scale": 2161,
    "voicing": 2162,
    "tempo": 2163,
    "cc": 2164,
    "expression": 2165,
    "dynamics": 2166,
    "pan": 2167,
    "modulation": 2168,
    "arp": 2169,
    "groove": 2170,
    "velocity": 2171,
    "fx": 2172,
    "register": 2173,
    "melody": 2174,
    "bass": 2175,
}

# Reversed lookup: port → agent name
_REVERSE_PORT_MAP: Dict[int, str] = {
    v: k for k, v in _DEFAULT_PORT_MAP.items()
}

ALL_AGENT_NAMES: List[str] = list(_DEFAULT_PORT_MAP.keys())


# ─── Data Classes ──────────────────────────────────────────────────────

@dataclass
class AgentEndpoint:
    """Describes one discovered fleet-midi agent endpoint."""

    agent_name: str
    port: int
    base_url: str
    alive: bool
    health_data: Optional[dict] = None
    response_time_ms: float = 0.0
    last_checked: float = 0.0


@dataclass
class DiscoveryCache:
    """Cached discovery results with expiry."""

    agents: Dict[str, AgentEndpoint]
    discovered_at: float
    ttl: float = 10.0  # seconds

    @property
    def expired(self) -> bool:
        return (time.time() - self.discovered_at) > self.ttl


# ─── Port Map Loading ──────────────────────────────────────────────────

def load_port_map(overrides: Optional[Dict[str, int]] = None) -> Dict[str, int]:
    """Load the port map, merging defaults with overrides.

    Environment variable FLEET_MIDI_PORT_MAP is also consulted (JSON dict).
    Explicit overrides take highest priority.

    Args:
        overrides: Optional dict of agent_name → port to override defaults.

    Returns:
        Final port mapping dict.
    """
    port_map = dict(_DEFAULT_PORT_MAP)

    # Check env var
    env_json = os.environ.get("FLEET_MIDI_PORT_MAP")
    if env_json:
        try:
            parsed = json.loads(env_json)
            if isinstance(parsed, dict):
                for k, v in parsed.items():
                    if isinstance(v, int):
                        port_map[k] = v
                        logger.debug("Port override from env: %s → %d", k, v)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Invalid FLEET_MIDI_PORT_MAP env var: %s", exc)

    # Apply explicit overrides
    if overrides:
        port_map.update(overrides)

    return port_map


# ─── Health Check ──────────────────────────────────────────────────────

def check_agent_health(
    agent_name: str,
    port: int,
    timeout: float = 2.0,
) -> AgentEndpoint:
    """Ping a fleet-midi agent at the given port and return its status.

    Args:
        agent_name: Agent name (e.g., "chord").
        port: Port number.
        timeout: HTTP timeout in seconds.

    Returns:
        AgentEndpoint with alive status and health data.
    """
    base_url = f"http://localhost:{port}"
    start = time.time()

    try:
        proxies = {"http": None, "https": None}
        resp = requests.get(
            f"{base_url}/health",
            timeout=timeout,
            proxies=proxies,
        )
        elapsed = (time.time() - start) * 1000

        if resp.status_code == 200:
            data = resp.json()
            return AgentEndpoint(
                agent_name=agent_name,
                port=port,
                base_url=base_url,
                alive=True,
                health_data=data,
                response_time_ms=round(elapsed, 1),
                last_checked=time.time(),
            )

        # Non-200 response — agent is running but unhealthy
        return AgentEndpoint(
            agent_name=agent_name,
            port=port,
            base_url=base_url,
            alive=False,
            health_data={"status_code": resp.status_code},
            response_time_ms=round(elapsed, 1),
            last_checked=time.time(),
        )

    except requests.ConnectionError:
        return AgentEndpoint(
            agent_name=agent_name,
            port=port,
            base_url=base_url,
            alive=False,
            response_time_ms=0.0,
            last_checked=time.time(),
        )
    except requests.Timeout:
        return AgentEndpoint(
            agent_name=agent_name,
            port=port,
            base_url=base_url,
            alive=False,
            health_data={"error": "timeout"},
            response_time_ms=timeout * 1000,
            last_checked=time.time(),
        )
    except requests.RequestException as exc:
        return AgentEndpoint(
            agent_name=agent_name,
            port=port,
            base_url=base_url,
            alive=False,
            health_data={"error": str(exc)},
            last_checked=time.time(),
        )


# ─── Discovery Class ───────────────────────────────────────────────────

class FleetDiscovery:
    """Discovers running fleet-midi agents via port health checks.

    Port convention: 16 agents on ports 2160-2175.
    Supports custom port mapping and result caching.

    Examples:
        >>> discovery = FleetDiscovery()
        >>> results = discovery.discover()
        >>> print(results["chord"].alive)
        True

        >>> # Custom ports
        >>> discovery = FleetDiscovery(port_overrides={"chord": 2200})
        >>> all_agents = discovery.discover()

        >>> # Per-agent lookup
        >>> ep = discovery.get_agent("scale")
        >>> if ep.alive:
        ...     print(ep.base_url)
        http://localhost:2161
    """

    def __init__(
        self,
        port_overrides: Optional[Dict[str, int]] = None,
        cache_ttl: float = 10.0,
        health_timeout: float = 2.0,
    ):
        """Initialize discovery.

        Args:
            port_overrides: Optional agent_name → port overrides.
            cache_ttl: Cache time-to-live in seconds.
            health_timeout: Per-agent health-check timeout in seconds.
        """
        self._port_map = load_port_map(port_overrides)
        self._cache_ttl = cache_ttl
        self._health_timeout = health_timeout
        self._cache: Optional[DiscoveryCache] = None

    @property
    def port_map(self) -> Dict[str, int]:
        """Current port map (read-only)."""
        return dict(self._port_map)

    def _build_new_cache(self) -> DiscoveryCache:
        """Discover all agents and return a fresh cache."""
        agents: Dict[str, AgentEndpoint] = {}
        for agent_name, port in self._port_map.items():
            ep = check_agent_health(agent_name, port, timeout=self._health_timeout)
            agents[agent_name] = ep

        return DiscoveryCache(
            agents=agents,
            discovered_at=time.time(),
            ttl=self._cache_ttl,
        )

    def discover(self, use_cache: bool = True) -> Dict[str, AgentEndpoint]:
        """Discover all running fleet-midi agents.

        Args:
            use_cache: If True, return cached results if not expired.

        Returns:
            Dict of agent_name → AgentEndpoint.
        """
        if use_cache and self._cache and not self._cache.expired:
            return dict(self._cache.agents)

        cache = self._build_new_cache()
        self._cache = cache
        return dict(cache.agents)

    def get_agent(self, agent_name: str, use_cache: bool = True) -> AgentEndpoint:
        """Get endpoint info for a single agent.

        Args:
            agent_name: Agent name (e.g., "chord").
            use_cache: If True, use cached results if fresh.

        Returns:
            AgentEndpoint for the requested agent.

        Raises:
            ValueError: If agent_name is unknown.
        """
        if agent_name not in self._port_map:
            known = sorted(self._port_map.keys())
            raise ValueError(
                f"Unknown agent '{agent_name}'. "
                f"Choose from: {', '.join(known)}"
            )

        results = self.discover(use_cache=use_cache)
        return results[agent_name]

    def get_agent_url(self, agent_name: str, use_cache: bool = True) -> str:
        """Get the base URL for an agent.

        Convenience wrapper — raises if the agent isn't alive.

        Args:
            agent_name: Agent name.
            use_cache: If True, use cached results.

        Returns:
            Base URL string (e.g., "http://localhost:2160").

        Raises:
            ConnectionError: If the agent is not alive.
            ValueError: If agent_name is unknown.
        """
        ep = self.get_agent(agent_name, use_cache=use_cache)
        if not ep.alive:
            raise ConnectionError(
                f"Agent '{agent_name}' not alive at {ep.base_url}. "
                f"Make sure the fleet-midi server is running on port {ep.port}."
            )
        return ep.base_url

    def list_alive(self, use_cache: bool = True) -> List[AgentEndpoint]:
        """Return only alive agents.

        Args:
            use_cache: If True, use cached results.

        Returns:
            List of alive AgentEndpoint objects.
        """
        results = self.discover(use_cache=use_cache)
        return [ep for ep in results.values() if ep.alive]

    def list_dead(self, use_cache: bool = True) -> List[AgentEndpoint]:
        """Return only dead/unreachable agents.

        Args:
            use_cache: If True, use cached results.

        Returns:
            List of dead AgentEndpoint objects.
        """
        results = self.discover(use_cache=use_cache)
        return [ep for ep in results.values() if not ep.alive]

    def alive_count(self, use_cache: bool = True) -> int:
        """Number of currently alive agents."""
        return len(self.list_alive(use_cache=use_cache))

    def clear_cache(self) -> None:
        """Force next discover() to re-check all agents."""
        self._cache = None

    def agent_name_for_port(self, port: int) -> Optional[str]:
        """Reverse lookup: port → agent name."""
        return _REVERSE_PORT_MAP.get(port)


# ─── Global Instance ───────────────────────────────────────────────────

_global_discovery: Optional[FleetDiscovery] = None


def get_discovery() -> FleetDiscovery:
    """Get or create the global FleetDiscovery instance.

    Returns:
        Global FleetDiscovery instance.
    """
    global _global_discovery
    if _global_discovery is None:
        _global_discovery = FleetDiscovery()
    return _global_discovery


def reset_discovery() -> None:
    """Reset the global discovery instance (useful for testing)."""
    global _global_discovery
    if _global_discovery is not None:
        _global_discovery.clear_cache()
    _global_discovery = None
