#!/usr/bin/env python3
"""
EnvClient — abstract base class and helpers for Gymnasium-style environments.

Ported from OpenEnv's env_client.py for the fleet-midi ecosystem.

Provides:
  - EnvClient: Abstract async/sync environment client base class
  - GenericEnvClient: Generic parameterized client
  - SyncWrapper: Synchronous wrapper for async clients
  - WebSocketTransport: WebSocket-based transport for persistent sessions
  - AgentResponse, CueObservation, CueRequest: Domain types
  - compute_reward, compute_reward_simple, make_env: Utility functions
"""

from __future__ import annotations

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar

from .client_types import StepResult, ObsT, StateT


# ======================================================================
# Domain Types
# ======================================================================


@dataclass
class AgentResponse:
    """Response from a fleet-midi agent after processing a cue or think request.

    Attributes:
        agent: Agent identifier (e.g., "fleet-midi-chord").
        result: Output result from the agent's domain analysis.
        ternary_vector: The [-1,0,1] ternary classification vector.
        response_time_ms: Time taken to process the request.
        status: "ok" or "error".
        error: Error message if status is "error".
        extra: Any additional fields from the agent response.
    """
    agent: str = ""
    result: Optional[str] = None
    ternary_vector: Tuple[int, int, int] = (0, 0, 0)
    response_time_ms: float = 0.0
    status: str = "ok"
    error: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentResponse':
        """Parse agent response dict into an AgentResponse."""
        tv_raw = data.get('ternary_vector', [0, 0, 0])
        if isinstance(tv_raw, list):
            tv = tuple(tv_raw[:3]) if len(tv_raw) >= 3 else (0, 0, 0)
        else:
            tv = (0, 0, 0)
        extras = {k: v for k, v in data.items()
                  if k not in ('agent', 'result', 'ternary_vector',
                               'response_time_ms', 'status', 'error')}
        return cls(
            agent=data.get('agent', ''),
            result=data.get('result'),
            ternary_vector=tv,
            response_time_ms=data.get('response_time_ms', 0.0),
            status=data.get('status', 'ok'),
            error=data.get('error'),
            extra=extras,
        )


@dataclass
class CueObservation:
    """Observation from a MIDI cue step.

    Contains the agent's analysis of the cue along with readiness metadata.
    """
    agent_response: AgentResponse
    agent_name: str
    step_count: int
    agent_alive: bool
    latency_ms: float

    @property
    def ternary_vector(self) -> Tuple[int, int, int]:
        return self.agent_response.ternary_vector

    @property
    def reward_baseline(self) -> float:
        """Normalized magnitude of ternary vector as a baseline reward hint."""
        return sum(abs(v) for v in self.ternary_vector) / 3.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_name': self.agent_name,
            'agent_alive': self.agent_alive,
            'step_count': self.step_count,
            'latency_ms': self.latency_ms,
            'ternary_vector': list(self.ternary_vector),
            'agent_result': self.agent_response.result,
            'reward_baseline': self.reward_baseline,
            **self.agent_response.extra,
        }


@dataclass
class CueRequest:
    """A MIDI cue request to be sent to a fleet-midi agent.

    Attributes:
        notes: MIDI note numbers (0–127).
        velocity: MIDI velocity (0–127).
        bpm: Beats per minute for tempo agents.
        cc: Control change value (0–127).
        payload: Additional domain-specific parameters.
    """
    notes: List[int] = field(default_factory=list)
    velocity: int = 64
    bpm: Optional[int] = None
    cc: Optional[int] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        body = {'notes': self.notes}
        if self.velocity is not None:
            body['velocity'] = self.velocity
        if self.bpm is not None:
            body['bpm'] = self.bpm
        if self.cc is not None:
            body['cc'] = self.cc
        body.update(self.payload)
        return body


# ======================================================================
# Utility Functions
# ======================================================================


def compute_reward(ternary_vector: Tuple[int, int, int],
                   success: bool = True,
                   response_time_ms: float = 100.0) -> float:
    """Compute a reward from a ternary vector and metadata.

    Args:
        ternary_vector: (-1, 0, 1) classification vector from agent.
        success: Whether the agent request succeeded.
        response_time_ms: Time taken for the request.

    Returns:
        Scalar reward value.
    """
    reward = 0.0
    # Ternary magnitude
    reward += sum(abs(v) for v in ternary_vector) * 0.5
    # Success bonus
    reward += 2.0 if success else -1.0
    # Speed bonus
    if response_time_ms < 50:
        reward += 0.5
    elif response_time_ms > 500:
        reward -= 0.5
    return reward


def compute_reward_simple(ternary_vector: Tuple[int, int, int]) -> float:
    """Simplified reward from ternary vector only.

    Returns sum of absolute values, normalized to [0, 3].
    """
    return float(sum(abs(v) for v in ternary_vector))


def make_env(agent_name: str, host: str = "127.0.0.1",
             port: Optional[int] = None) -> 'FleetMidiEnvironment':
    """Quick factory for creating a FleetMidiEnvironment.

    Convenience function for REPL and scripts. Requires FleetMidiEnvironment
    to be importable (fleet_env.py module).

    Args:
        agent_name: Name of fleet-midi agent.
        host: Agent host.
        port: Agent port (auto-resolved from AGENT_PORTS if None).

    Returns:
        Configured FleetMidiEnvironment.
    """
    from .fleet_env import FleetMidiEnvironment
    return FleetMidiEnvironment(agent_name=agent_name, host=host, port=port)


# ======================================================================
# WebSocket Transport
# ======================================================================


class WebSocketTransport:
    """Minimal WebSocket transport for agent communication.

    This provides the low-level send/receive pattern used by EnvClient
    for persistent connections. For the fleet-midi ecosystem, agents
    primarily use HTTP, but this transport enables future WebSocket
    agent servers.
    """

    def __init__(self, base_url: str, timeout: float = 5.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._ws = None

    @property
    def is_connected(self) -> bool:
        return self._ws is not None

    async def connect(self):
        """Establish WebSocket connection (stub)."""
        # In production, this would use websockets library
        # For now, mark as connected for HTTP fallback clients
        self._ws = True  # placeholder

    async def disconnect(self):
        self._ws = None

    async def send(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send and receive via WebSocket (stub — falls through to HTTP)."""
        # Placeholder for when agents support WebSocket
        raise NotImplementedError(
            "WebSocket transport not yet available for fleet-midi agents. "
            "Use HTTP transport (default)."
        )

    async def close(self):
        await self.disconnect()


# ======================================================================
# SyncWrapper
# ======================================================================


class SyncWrapper:
    """Synchronous wrapper around an async environment client.

    Wraps an EnvClient-compatible async instance, exposing
    synchronous reset/step methods for use in non-async code.
    """

    def __init__(self, async_env):
        self._async_env = async_env
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def reset(self, **kwargs) -> StepResult:
        """Synchronous reset."""
        return self._run_async(self._async_env.reset(**kwargs))

    def step(self, action: Any, **kwargs) -> StepResult:
        """Synchronous step."""
        return self._run_async(self._async_env.step(action, **kwargs))

    def observe(self) -> Any:
        """Synchronous observe."""
        if hasattr(self._async_env, 'observe'):
            result = self._async_env.observe()
            if asyncio.iscoroutine(result):
                return self._run_async(result)
            return result
        return self._run_async(self._async_env.reset())

    def close(self):
        """Synchronous close."""
        if hasattr(self._async_env, 'close'):
            result = self._async_env.close()
            if asyncio.iscoroutine(result):
                self._run_async(result)

    def _run_async(self, coro) -> Any:
        """Run a coroutine synchronously in an event loop."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop — create one
            return asyncio.run(coro)

        # We're inside a running loop — use it
        if not self._loop:
            self._loop = loop
        # Run the coroutine by creating a future
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ======================================================================
# EnvClient
# ======================================================================


class EnvClient(ABC):
    """Abstract base class for Gymnasium-style environment clients.

    Provides the core reset/step interface. Designed to work with both
    sync and async patterns. Subclasses implement domain-specific
    observation/action spaces.

    For fleet-midi agents, see FleetMidiEnvironment in fleet_env.py.
    """

    @abstractmethod
    def reset(self) -> Any:
        """Reset the environment and return initial observation."""
        ...

    @abstractmethod
    def step(self, action: Any) -> StepResult:
        """Take a step in the environment.

        Args:
            action: Domain-specific action.

        Returns:
            StepResult containing observation, reward, done.
        """
        ...

    def observe(self) -> Any:
        """Peek at current observation without stepping.

        Default re-resets; subclasses should implement true passive observation.
        """
        return self.reset()

    def close(self):
        """Clean up resources."""
        pass

    def seed(self, seed: Optional[int] = None):
        """Set random seed for reproducibility."""
        pass

    @property
    def action_space(self) -> Optional[Any]:
        return None

    @property
    def observation_space(self) -> Optional[Any]:
        return None


class GenericEnvClient(Generic[ObsT, StateT], EnvClient):
    """Generic environment client parameterized on observation and state types.

    Stores internal state; override reset/step for domain logic.
    """

    def __init__(self, initial_observation: ObsT, initial_state: StateT):
        self._initial_obs = initial_observation
        self._initial_state = initial_state
        self._observation: ObsT = initial_observation
        self._state: StateT = initial_state
        self._metadata: Dict[Any, Any] = {}

    def reset(self) -> ObsT:
        self._observation = self._initial_obs
        self._state = self._initial_state
        self._metadata = {}
        return self._observation

    def step(self, action: Any) -> StepResult:
        return StepResult(observation=self._observation, reward=0.0, done=False)

    def observe(self) -> ObsT:
        return self._observation

    @property
    def state(self) -> StateT:
        return self._state

    @property
    def metadata(self) -> Dict[Any, Any]:
        return self._metadata
