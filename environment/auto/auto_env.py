"""
AutoEnv — automatic environment discovery for fleet-midi agents.

Ports the OpenEnv AutoEnv pattern for the fleet-midi ecosystem.
Discovers running agents, creates environment clients, and provides
training loop helpers.

The central class is AutoEnv (factory, not instantiable directly).
FleetMidiEnvironment is the per-agent environment wrapper.

Examples:
    >>> from fleet_characters.environment.auto import AutoEnv, FleetMidiEnvironment
    >>>
    >>> # Discover running agents
    >>> alive = AutoEnv.discover()
    >>> for name, ep in alive.items():
    ...     print(f"{name} → {ep.base_url} (alive={ep.alive})")
    >>>
    >>> # Create environment for one agent
    >>> env = AutoEnv.from_agent("chord")
    >>> obs = env.reset(notes=[60, 64, 67])
    >>> step_result = env.step({"notes": [60, 64, 67, 72]})
    >>> print(step_result.observation)
    >>>
    >>> # Create environments for all running agents
    >>> envs = AutoEnv.all_agents()
    >>> for name, env in envs.items():
    ...     obs = env.observe()
    ...     print(f"{name}: {obs}")
    >>>
    >>> # Agents by character class
    >>> artificers = AutoEnv.agents_by_class("Artificer")
    >>> print(artificers)  # ['chord', 'scale', 'voicing']
    >>>
    >>> # Full training loop
    >>> result = AutoEnv.train_loop("chord", episodes=5)
    >>> print(result["total_reward"])
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import requests

from ._discovery import (
    ALL_AGENT_NAMES,
    FleetDiscovery,
    get_discovery,
    load_port_map,
)
from .auto_action import build_cue, build_think

# Import fleet_characters for AgentCharacter integration where available
try:
    from fleet_characters.agent_profile import AgentCharacter
    HAS_CHARACTERS = True
except ImportError:
    AgentCharacter = None  # type: ignore
    HAS_CHARACTERS = False

try:
    from fleet_characters.class_ import AGENT_DEFAULT_CLASSES, CharacterClass
    HAS_CLASSES = True
except ImportError:
    AGENT_DEFAULT_CLASSES = {}  # type: ignore
    CharacterClass = None  # type: ignore
    HAS_CLASSES = False

logger = logging.getLogger(__name__)


# ─── FleetMidiEnvironment — Per-Agent Client ───────────────────────────

@dataclass
class StepResult:
    """Result of one environment step.

    Mirrors OpenEnv's StepResult pattern.

    Attributes:
        observation: Agent response dict.
        reward: Optional scalar reward for this step.
        done: Whether the episode is finished.
        info: Additional metadata dict.
    """

    observation: dict
    reward: Optional[float] = None
    done: bool = False
    info: dict = field(default_factory=dict)


class FleetMidiEnvironment:
    """Environment client wrapping a single fleet-midi agent.

    Provides Gymnasium-style reset/step/observe interface for interacting
    with a running fleet-midi agent over HTTP.

    Each agent processes MIDI cues (notes, velocity, CC) or text think tasks
    and returns a ternary_vector analysis along with domain-specific output.

    When AgentCharacter is available, every interaction updates the character's
    stats (Perception, Dexterity, Intelligence, etc.) and class progression.

    Examples:
        >>> from fleet_characters.environment.auto import FleetMidiEnvironment
        >>>
        >>> # Connect to a running agent
        >>> env = FleetMidiEnvironment("chord", "http://localhost:2160")
        >>>
        >>> # Reset with initial notes
        >>> obs = env.reset(notes=[60, 64, 67])
        >>> print(obs["result"])
        'major'
        >>>
        >>> # Step with a new cue
        >>> result = env.step({"notes": [60, 63, 67]})
        >>> print(result.observation["type"])
        'minor'
        >>> print(result.observation["ternary_vector"])
        [-1, 0, 0]
        >>>
        >>> # Observe current state
        >>> status = env.observe()
        >>> print(status["agent"])
        'fleet-midi-chord'
        >>>
        >>> # Think mode — text reasoning
        >>> think_result = env.think("Analyze harmonic progression")
        >>> print(think_result["ternary_vector"])
    """

    def __init__(
        self,
        agent_name: str,
        base_url: str,
        character: Optional["AgentCharacter"] = None,
        timeout: float = 5.0,
    ):
        """Initialize environment for one agent.

        Args:
            agent_name: Agent name (e.g., "chord", "scale").
            base_url: Agent's base URL (e.g., "http://localhost:2160").
            character: Optional AgentCharacter instance for stats tracking.
            timeout: HTTP request timeout in seconds.
        """
        self.agent_name = agent_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._proxies: Dict[str, None] = {"http": None, "https": None}

        # AgentCharacter integration
        self.character: Optional["AgentCharacter"] = character
        self._last_observation: Optional[dict] = None
        self._step_count: int = 0
        self._episode_reward: float = 0.0

    def __repr__(self) -> str:
        return (
            f"FleetMidiEnvironment(agent='{self.agent_name}', "
            f"url='{self.base_url}')"
        )

    # ── HTTP helpers ────────────────────────────────────────────────

    def _get(self, path: str) -> dict:
        """Send GET request to agent."""
        resp = requests.get(
            f"{self.base_url}{path}",
            timeout=self.timeout,
            proxies=self._proxies,
        )
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, data: dict) -> dict:
        """Send POST request to agent."""
        resp = requests.post(
            f"{self.base_url}{path}",
            json=data,
            timeout=self.timeout,
            proxies=self._proxies,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()

    # ── Environment Interface ───────────────────────────────────────

    def reset(
        self,
        notes: Optional[List[int]] = None,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> dict:
        """Reset the environment to a starting state.

        Sends an initial observation cue to the agent and records the
        beginning of an episode.

        Args:
            notes: Optional starting MIDI notes.
            payload: Optional additional parameters.
            **kwargs: Extra fields for the cue dict.

        Returns:
            Observation dict from the agent (result, ternary_vector, etc.).
        """
        self._step_count = 0
        self._episode_reward = 0.0

        # Build and send reset cue
        cue = build_cue(self.agent_name, notes=notes, payload=payload, **kwargs)
        obs = self._post("/agent", cue)

        self._last_observation = obs
        self._update_character("cue", True)

        return obs

    def step(
        self,
        action: Dict[str, Any],
    ) -> "StepResult":
        """Take one step in the environment by sending a cue to the agent.

        Args:
            action: Cue dict with notes, payload, or voice fields.

        Returns:
            StepResult with observation, reward, done, info.
        """
        self._step_count += 1

        # If action is already a cue dict, forward directly.
        # If it's a StepResult, it's a Gymnasium wrapper integration.
        if isinstance(action, dict):
            cue = action
        else:
            # Gymnasium-style: action may be a raw value; wrap it
            cue = build_cue(self.agent_name, notes=action.get("notes"))

        try:
            start = time.time()
            obs = self._post("/agent", cue)
            elapsed = (time.time() - start) * 1000

            self._last_observation = obs

            # Compute reward from ternary vector if available
            reward = self._compute_reward(obs)
            self._episode_reward += reward

            # Update character stats
            success = obs.get("status") != "error"
            self._update_character("cue", success, response_time_ms=elapsed)

            return StepResult(
                observation=obs,
                reward=reward,
                done=False,
                info={"response_time_ms": round(elapsed, 1), "step": self._step_count},
            )

        except requests.RequestException as exc:
            logger.warning("Step failed for %s: %s", self.agent_name, exc)
            self._update_character("cue", False, response_time_ms=0)
            return StepResult(
                observation={"error": str(exc), "ternary_vector": [0, 0, 0]},
                reward=-1.0,
                done=True,
                info={"error": str(exc), "step": self._step_count},
            )

    def observe(self) -> dict:
        """Get the current agent state without stepping.

        Sends GET /agent and returns the health/probe response.
        Useful for monitoring without affecting state.

        Returns:
            Agent status dict.
        """
        obs = self._get("/agent")
        self._last_observation = obs
        return obs

    def think(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """Send a text reasoning task to the agent (think mode).

        The agent analyzes the task through its domain-specific lens and
        returns a ternary analysis.

        Args:
            task: Text description of the task.
            context: Optional context dict.

        Returns:
            Think response with analysis and ternary_vector.
        """
        payload = build_think(self.agent_name, task, context=context)
        obs = self._post("/agent", payload)
        self._last_observation = obs
        self._update_character("think", True)
        return obs

    def probe(self) -> dict:
        """Probe the agent — lightweight health check with no analysis.

        Returns:
            Probe response dict.
        """
        return self._post("/agent", {"type": "probe"})

    # ── Reward Computation ──────────────────────────────────────────

    @staticmethod
    def _compute_reward(observation: dict) -> float:
        """Compute scalar reward from agent observation.

        Uses the ternary_vector norms and success indicators.

        Args:
            observation: Agent response dict.

        Returns:
            Scalar reward value.
        """
        tv = observation.get("ternary_vector", [0, 0, 0])
        # Magnitude of ternary vector → how decisive/confident the response
        magnitude = sum(abs(v) for v in tv) / 3.0

        # Bonus for ternary diversity (non-zero in multiple dimensions)
        non_zero = sum(1 for v in tv if v != 0)
        diversity_bonus = non_zero * 0.2

        # Error penalty
        if observation.get("status") == "error" or observation.get("error"):
            return -1.0

        # Base reward from magnitude + diversity
        return magnitude + diversity_bonus

    # ── Character Integration ───────────────────────────────────────

    def _update_character(
        self,
        request_type: str = "cue",
        success: bool = True,
        response_time_ms: float = 100.0,
    ) -> None:
        """Update AgentCharacter stats if available."""
        if self.character is not None:
            try:
                self.character.process_request(
                    request_type=request_type,
                    success=success,
                    response_time_ms=response_time_ms,
                )
            except Exception as exc:
                logger.debug("Character update failed: %s", exc)

    # ── Properties ──────────────────────────────────────────────────

    @property
    def step_count(self) -> int:
        """Number of steps taken in current episode."""
        return self._step_count

    @property
    def episode_reward(self) -> float:
        """Cumulative reward for current episode."""
        return self._episode_reward

    @property
    def last_observation(self) -> Optional[dict]:
        """Most recent observation from the agent."""
        return self._last_observation

    @property
    def character_dict(self) -> Optional[dict]:
        """AgentCharacter serialized dict, if available."""
        if self.character is not None:
            return self.character.to_dict()
        return None


# ─── AutoEnv — Factory Class ───────────────────────────────────────────

@dataclass
class AgentInfo:
    """Summary info about a discovered agent."""

    agent_name: str
    port: int
    base_url: str
    alive: bool
    default_class: str
    response_time_ms: float
    health_data: Optional[dict]


class AutoEnv:
    """Factory for discovering and instantiating fleet-midi environments.

    Follows the HuggingFace OpenEnv AutoEnv pattern — not meant to be
    instantiated directly. Use class methods to create environments.

    Examples:
        >>> # From agent name
        >>> env = AutoEnv.from_agent("chord")
        >>> obs = env.reset(notes=[60, 64, 67])

        >>> # From multiple agents
        >>> envs = AutoEnv.from_agents(["chord", "scale", "tempo"])
        >>> for name, env in envs.items():
        ...     obs = env.observe()

        >>> # All 16 agents (only alive ones get envs)
        >>> all_envs = AutoEnv.all_agents()
        >>> print(f"{len(all_envs)} agents discovered")

        >>> # Filter by character class
        >>> bards = AutoEnv.agents_by_class("Bard")
        >>> print(bards)  # ['melody', 'bass']
    """

    def __init__(self) -> None:
        raise TypeError(
            "AutoEnv is a factory class and should not be instantiated directly. "
            "Use AutoEnv.from_agent() or AutoEnv.discover() instead."
        )

    # ── Discovery ───────────────────────────────────────────────────

    @classmethod
    def discover(cls) -> Dict[str, AgentInfo]:
        """Discover all running fleet-midi agents.

        Scans ports 2160-2175 (or custom mapping) and returns status
        for each agent.

        Returns:
            Dict of agent_name → AgentInfo with alive status, port, etc.
        """
        discovery = get_discovery()
        agents = discovery.discover()

        return {
            name: AgentInfo(
                agent_name=ep.agent_name,
                port=ep.port,
                base_url=ep.base_url,
                alive=ep.alive,
                default_class=_get_default_class(name),
                response_time_ms=ep.response_time_ms,
                health_data=ep.health_data,
            )
            for name, ep in agents.items()
        }

    @classmethod
    def list_environments(cls) -> None:
        """Print a formatted table of discovered agents to stdout."""
        agents = cls.discover()

        print("Available Fleet-MIDI Agents:")
        print("-" * 72)

        if not agents:
            print("  No agents discovered.")
            print("  Start agents with: python3 fleet-agent.py --port <port> --agent <name>")
        else:
            alive_count = sum(1 for a in agents.values() if a.alive)
            for name in sorted(agents.keys()):
                info = agents[name]
                status = "✅ ALIVE" if info.alive else "❌ DOWN"
                cls_name = info.default_class or "TBD"
                print(
                    f"  {name:<15} {status:<10} "
                    f"port={info.port:<4} "
                    f"class={cls_name:<16} "
                    f"{'✔' if info.alive else '✘'}"
                )

        print("-" * 72)
        total = len(agents)
        alive = sum(1 for a in agents.values() if a.alive)
        print(f"Total: {total} agents ({alive} alive, {total - alive} down)")

    # ── Factory Methods ─────────────────────────────────────────────

    @classmethod
    def from_agent(
        cls,
        agent_name: str,
        with_character: bool = True,
        port_overrides: Optional[Dict[str, int]] = None,
        timeout: float = 5.0,
    ) -> FleetMidiEnvironment:
        """Create a FleetMidiEnvironment for one agent.

        Args:
            agent_name: Agent name (e.g., "chord", "scale", "melody").
            with_character: If True, attach AgentCharacter for stats tracking.
            port_overrides: Optional port overrides for discovery.
            timeout: HTTP request timeout.

        Returns:
            FleetMidiEnvironment connected to the agent.

        Raises:
            ConnectionError: If agent is not alive.
            ValueError: If agent_name is unknown.
        """
        discovery = FleetDiscovery(port_overrides=port_overrides)
        ep = discovery.get_agent(agent_name)

        if not ep.alive:
            raise ConnectionError(
                f"Agent '{agent_name}' is not running on port {ep.port}. "
                f"Start it with: python3 fleet-agent.py --port {ep.port} --agent {agent_name}"
            )

        character = None
        if with_character and HAS_CHARACTERS:
            character = AgentCharacter(
                agent_name=f"fleet-midi-{agent_name}",
                domain=agent_name,
            )

        return FleetMidiEnvironment(
            agent_name=agent_name,
            base_url=ep.base_url,
            character=character,
            timeout=timeout,
        )

    @classmethod
    def from_agents(
        cls,
        agent_names: List[str],
        with_character: bool = True,
        port_overrides: Optional[Dict[str, int]] = None,
        timeout: float = 5.0,
    ) -> Dict[str, FleetMidiEnvironment]:
        """Create environments for multiple agents.

        Args:
            agent_names: List of agent names.
            with_character: If True, attach AgentCharacter to each.
            port_overrides: Optional port overrides.
            timeout: HTTP request timeout.

        Returns:
            Dict of agent_name → FleetMidiEnvironment.

        Raises:
            ConnectionError: If any requested agent is not alive.
        """
        envs: Dict[str, FleetMidiEnvironment] = {}
        errors: List[str] = []

        for name in agent_names:
            try:
                envs[name] = cls.from_agent(
                    agent_name=name,
                    with_character=with_character,
                    port_overrides=port_overrides,
                    timeout=timeout,
                )
            except (ConnectionError, ValueError) as exc:
                errors.append(f"{name}: {exc}")

        if errors and not envs:
            raise ConnectionError(
                f"All {len(agent_names)} requested agents failed:\n" + "\n".join(errors)
            )

        if errors:
            logger.warning(
                "%d/%d agents failed to connect:\n%s",
                len(errors),
                len(agent_names),
                "\n".join(errors),
            )

        return envs

    @classmethod
    def all_agents(
        cls,
        with_character: bool = True,
        port_overrides: Optional[Dict[str, int]] = None,
        timeout: float = 5.0,
    ) -> Dict[str, FleetMidiEnvironment]:
        """Create environments for all 16 fleet-midi agents.

        Only creates environments for agents that are alive (connected).

        Args:
            with_character: If True, attach AgentCharacter to each.
            port_overrides: Optional port overrides.
            timeout: HTTP request timeout.

        Returns:
            Dict of agent_name → FleetMidiEnvironment for alive agents.
        """
        discovery = FleetDiscovery(port_overrides=port_overrides)
        agents = discovery.discover()

        alive = [name for name, ep in agents.items() if ep.alive]

        if not alive:
            logger.warning(
                "No fleet-midi agents are running. "
                "Start them with: python3 fleet-agent.py --port <port> --agent <name>"
            )
            return {}

        return cls.from_agents(
            agent_names=alive,
            with_character=with_character,
            port_overrides=port_overrides,
            timeout=timeout,
        )

    # ── Class-Based Filtering ───────────────────────────────────────

    @classmethod
    def agents_by_class(
        cls,
        class_name: str,
        only_alive: bool = True,
    ) -> List[str]:
        """Get agent names that have a specific default character class.

        Class mapping (from class_.py AGENT_DEFAULT_CLASSES):
          Artificer  → chord, scale, voicing
          Bard       → melody, bass
          Sage       → tempo, groove
          Scout      → expression, dynamics, velocity
          Diplomat   → pan, modulation, fx
          Speedster  → arp, register
          Warden     → cc

        Args:
            class_name: Character class name (case-insensitive).
            only_alive: If True, only return agents that are alive.

        Returns:
            List of agent names matching the class.

        Examples:
            >>> AutoEnv.agents_by_class("Artificer")
            ['chord', 'scale', 'voicing']
            >>> AutoEnv.agents_by_class("Bard")
            ['melody', 'bass']
        """
        class_name_lower = class_name.lower()
        matching = []

        for name, default_class in AGENT_DEFAULT_CLASSES.items():
            cls_label = default_class.name if HAS_CLASSES else default_class
            if cls_label.lower() == class_name_lower:
                matching.append(name)

        if only_alive:
            discovery = get_discovery()
            agents = discovery.discover()
            matching = [name for name in matching if agents.get(name, type("", (), {"alive": False})()).alive]  # type: ignore

        return matching

    # ── Training Loop ───────────────────────────────────────────────

    @classmethod
    def train_loop(
        cls,
        agent_name: str,
        episodes: int = 1,
        cue_factory: Optional[Callable[[int], Dict[str, Any]]] = None,
        reward_threshold: float = 0.5,
        with_character: bool = True,
        port_overrides: Optional[Dict[str, int]] = None,
        timeout: float = 5.0,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """Run a complete training loop for one agent.

        A training loop consists of `episodes` iterations where each episode:
        1. Resets the agent environment
        2. Optionally runs a cue_factory for each step
        3. Collects observations and rewards
        4. Tracks cumulative stats

        Args:
            agent_name: Agent to train.
            episodes: Number of training episodes.
            cue_factory: Callable(episode_num) → cue dict for each episode.
                If None, sends a probe action each episode.
            reward_threshold: Reward threshold for success classification.
            with_character: Track character stats.
            port_overrides: Optional port overrides.
            timeout: HTTP request timeout.
            verbose: If True, print per-episode progress.

        Returns:
            Dict with training results:
                - agent: agent name
                - episodes_completed: int
                - total_reward: float
                - avg_reward: float
                - max_reward: float
                - min_reward: float
                - all_rewards: List[float]
                - total_time_ms: float
                - success_rate: float
                - character: dict or None
        """
        env = cls.from_agent(
            agent_name=agent_name,
            with_character=with_character,
            port_overrides=port_overrides,
            timeout=timeout,
        )

        all_rewards: List[float] = []
        start_time = time.time()

        if verbose:
            print(f"🏋️  Training '{agent_name}' — {episodes} episodes")

        for episode in range(1, episodes + 1):
            ep_start = time.time()

            # Reset
            obs = env.reset()

            # Build action (use cue_factory or probe)
            if cue_factory is not None:
                action = cue_factory(episode)
            else:
                action = {"type": "probe"}

            # Step
            result = env.step(action)

            reward = result.reward if result.reward is not None else 0.0
            all_rewards.append(reward)

            ep_time = (time.time() - ep_start) * 1000

            if verbose:
                tv = result.observation.get("ternary_vector", [0, 0, 0])
                status = "✅" if reward >= reward_threshold else "⚠️"
                print(
                    f"  Episode {episode}/{episodes} {status} "
                    f"reward={reward:.3f} tv={tv} "
                    f"time={ep_time:.0f}ms"
                )

        total_time = (time.time() - start_time) * 1000

        result = {
            "agent": agent_name,
            "episodes_completed": episodes,
            "total_reward": round(sum(all_rewards), 3),
            "avg_reward": round(sum(all_rewards) / max(episodes, 1), 3),
            "max_reward": round(max(all_rewards), 3) if all_rewards else 0.0,
            "min_reward": round(min(all_rewards), 3) if all_rewards else 0.0,
            "all_rewards": all_rewards,
            "total_time_ms": round(total_time, 1),
            "success_rate": round(
                sum(1 for r in all_rewards if r >= reward_threshold) / max(episodes, 1),
                3,
            ),
            "character": env.character_dict,
        }

        if verbose:
            print(
                f"  {'='*40}\n"
                f"  ✅ Done: {episodes} episodes, "
                f"avg_reward={result['avg_reward']:.3f}, "
                f"success_rate={result['success_rate']:.1%}, "
                f"total_time={total_time:.0f}ms"
            )

        return result

    @classmethod
    def train_all(
        cls,
        episodes: int = 1,
        cue_factory: Optional[Callable[[str, int], Dict[str, Any]]] = None,
        reward_threshold: float = 0.5,
        with_character: bool = True,
        port_overrides: Optional[Dict[str, int]] = None,
        timeout: float = 5.0,
        verbose: bool = True,
    ) -> Dict[str, Dict[str, Any]]:
        """Run training loop for all alive agents.

        Args:
            episodes: Episodes per agent.
            cue_factory: Callable(agent_name, episode_num) → cue dict.
                If None, uses probe for each.
            reward_threshold: Success threshold.
            with_character: Track character stats.
            port_overrides: Optional port overrides.
            timeout: HTTP request timeout.
            verbose: If True, print progress.

        Returns:
            Dict of agent_name → training result dict.
        """
        envs = cls.all_agents(
            with_character=with_character,
            port_overrides=port_overrides,
            timeout=timeout,
        )

        if not envs:
            logger.warning("No alive agents to train.")
            return {}

        results: Dict[str, Dict[str, Any]] = {}

        for name, env in envs.items():
            factory = None
            if cue_factory is not None:
                # Wrap to provide agent_name
                def _make_factory(agent: str = name) -> Callable[[int], Dict[str, Any]]:
                    return lambda ep: cue_factory(agent, ep)
                factory = _make_factory()

            result = cls.train_loop(
                agent_name=name,
                episodes=episodes,
                cue_factory=factory,
                reward_threshold=reward_threshold,
                with_character=False,  # character already attached
                port_overrides=port_overrides,
                timeout=timeout,
                verbose=verbose,
            )
            results[name] = result

        return results

    # ── Info ────────────────────────────────────────────────────────

    @classmethod
    def get_agent_info(cls, agent_name: str) -> Dict[str, Any]:
        """Get detailed information about a single agent.

        Args:
            agent_name: Agent name.

        Returns:
            Dict with agent metadata.
        """
        discovery = get_discovery()
        ep = discovery.get_agent(agent_name)

        return {
            "agent_name": ep.agent_name,
            "port": ep.port,
            "base_url": ep.base_url,
            "alive": ep.alive,
            "default_class": _get_default_class(agent_name),
            "response_time_ms": ep.response_time_ms,
            "health_data": ep.health_data,
        }

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the discovery cache so next discover() re-checks all agents."""
        discovery = get_discovery()
        discovery.clear_cache()


# ─── Helpers ───────────────────────────────────────────────────────────

def _get_default_class(agent_name: str) -> str:
    """Get default character class name for an agent."""
    if HAS_CLASSES:
        cls = AGENT_DEFAULT_CLASSES.get(agent_name)
        if cls is not None:
            return cls.name if hasattr(cls, "name") else str(cls)
    # Fallback class names
    _FALLBACK_CLASSES = {
        "chord": "Artificer",
        "scale": "Artificer",
        "voicing": "Artificer",
        "tempo": "Sage",
        "groove": "Sage",
        "cc": "Warden",
        "expression": "Scout",
        "dynamics": "Scout",
        "velocity": "Scout",
        "pan": "Diplomat",
        "modulation": "Diplomat",
        "fx": "Diplomat",
        "arp": "Speedster",
        "register": "Speedster",
        "melody": "Bard",
        "bass": "Bard",
    }
    return _FALLBACK_CLASSES.get(agent_name, "Undefined")
