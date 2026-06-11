#!/usr/bin/env python3
"""
FleetMidiEnvironment — Gymnasium-style RL environment wrapping a single
fleet-midi agent.

Each environment wraps ONE fleet-midi agent (chord, scale, melody, etc.)
and provides reset/step semantics for RL training loops.

Key features:
    - reset(): Returns agent character state + readiness
    - step(action): Sends MIDI cue, gets analysis, computes reward, grows stats
    - Multiple reward modes: character-based, rubric-based, hybrid
    - HTTP client (httpx) for calling the agent's endpoint
    - Auto-discovery via FleetMidiEnvironment.from_agent_name(name)
    - Full integration with fleet-characters (agent_profile.py, stats.py)
"""

import json
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from .env_client import EnvClient
from .client_types import StepResult, ObsT, StateT
from .rubrics import Rubric, SuccessBonusRubric, CompositeRubric


# ─── Reward Modes ──────────────────────────────────────────────────


class RewardMode(Enum):
    """How reward is computed for each step."""
    CHARACTER = "character"        # Reward = stat growth (intrinsic)
    RUBRIC = "rubric"              # Reward = rubric score (extrinsic)
    HYBRID = "hybrid"              # Reward = rubric * stat_modifier


# ─── Agent port registry (shared with auto.py) ────────────────────


AGENT_PORTS: Dict[str, int] = {
    'chord': 9010,
    'scale': 9011,
    'voicing': 9012,
    'tempo': 9013,
    'groove': 9014,
    'cc': 9015,
    'expression': 9016,
    'dynamics': 9017,
    'pan': 9018,
    'modulation': 9019,
    'arp': 9020,
    'velocity': 9021,
    'fx': 9022,
    'register': 9023,
    'melody': 9024,
    'bass': 9025,
}


# ─── Default agents for each domain ───────────────────────────────


AGENT_NAMES = list(AGENT_PORTS.keys())
DEFAULT_HOST = "127.0.0.1"


# ─── Environment State Definition ─────────────────────────────────


@dataclass
class FleetObservation:
    """Observation returned by reset() and step().

    Contains the full agent character state (stats, class, level, arc)
    plus readiness information and the last processed result.
    """
    agent_name: str
    agent_host: str
    agent_port: int
    agent_alive: bool
    domain: str

    # Character state (from AgentCharacter.to_dict())
    character: Dict[str, Any]

    # Readiness
    ready: bool
    latency_ms: float

    # Last result (None on reset)
    last_result: Optional[Dict[str, Any]] = None

    # Step metadata
    step_count: int = 0
    reward_baseline: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Flat dict for Gymnasium observation compatibility."""
        return {
            'agent_name': self.agent_name,
            'agent_host': self.agent_host,
            'agent_port': self.agent_port,
            'agent_alive': self.agent_alive,
            'domain': self.domain,
            # Flatten top-level character fields for easy access
            'level': self.character.get('level', 1),
            'title': self.character.get('title', 'Rising'),
            'class_': self.character.get('class', 'Undefined'),
            'xp': self.character.get('xp', 0),
            'xp_to_next': self.character.get('xp_to_next', 10),
            'total_requests': self.character.get('total_requests', 0),
            'success_streak': self.character.get('success_streak', 0),
            'best_streak': self.character.get('best_streak', 0),
            'integration_score': self.character.get('integration_score', 0.7),
            'stats_average': self.character.get('stats', {}).get('average', 10.0),
            # Readiness
            'ready': self.ready,
            'latency_ms': self.latency_ms,
            # Step
            'step_count': self.step_count,
            # Embed full character for downstream consumers
            'character': self.character,
        }

    def __repr__(self) -> str:
        return (f"<FleetObservation agent={self.agent_name} "
                f"alive={self.agent_alive} ready={self.ready} "
                f"level={self.character.get('level', 1)} "
                f"class_={self.character.get('class', 'Undefined')}>")


# ─── The Environment ──────────────────────────────────────────────


class FleetMidiEnvironment(EnvClient):
    """Gymnasium-style environment wrapping a single fleet-midi agent.

    Usage:
        env = FleetMidiEnvironment(agent_name='chord')
        obs = env.reset()
        result = env.step({'notes': [60, 64, 67]})
        # Or with async:
        result = await env.step_async({'notes': [60, 64, 67]})
    """

    def __init__(
        self,
        agent_name: str,
        host: str = DEFAULT_HOST,
        port: Optional[int] = None,
        reward_mode: Union[str, RewardMode] = RewardMode.CHARACTER,
        rubric: Optional[Rubric] = None,
        response_timeout: float = 5.0,
        auto_start_character: bool = True,
        character_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        Args:
            agent_name: Name of the fleet-midi agent (chord, scale, melody, etc.)
            host: Host running the agent.
            port: Agent port. If None, looked up from AGENT_PORTS.
            reward_mode: How reward is computed (character, rubric, or hybrid).
            rubric: Rubric for extrinsic reward computation.
                     Defaults to SuccessBonusRubric if mode is rubric/hybrid.
            response_timeout: HTTP request timeout in seconds.
            auto_start_character: If True, create an AgentCharacter on init.
            character_kwargs: Extra kwargs for AgentCharacter constructor.
        """
        if agent_name not in AGENT_PORTS:
            raise ValueError(
                f"Unknown agent '{agent_name}'. "
                f"Known agents: {', '.join(AGENT_NAMES)}"
            )

        if port is None:
            port = AGENT_PORTS[agent_name]

        # Resolve reward mode
        if isinstance(reward_mode, str):
            reward_mode = RewardMode(reward_mode)

        self._agent_name = agent_name
        self._host = host
        self._port = port
        self._reward_mode = reward_mode
        self._response_timeout = response_timeout

        # Base URL for HTTP calls
        self._base_url = f"http://{host}:{port}"

        # Rubric
        if rubric is not None:
            self._rubric = rubric
        elif reward_mode in (RewardMode.RUBRIC, RewardMode.HYBRID):
            self._rubric = SuccessBonusRubric()
        else:
            self._rubric = None

        # Character — imported lazily for integration
        self._character = None
        if auto_start_character:
            self._start_character(**(character_kwargs or {}))

        # Internal state
        self._step_count: int = 0
        self._last_result: Optional[Dict[str, Any]] = None
        self._last_observation: Optional[FleetObservation] = None
        self._episode_reward: float = 0.0
        self._done: bool = False

        # httpx client (created lazily on first request)
        self._http = None

    # ─── Character Management ─────────────────────────────────

    def _start_character(self, **kwargs):
        """Create the AgentCharacter for this environment's agent."""
        from fleet_characters.agent_profile import AgentCharacter

        name = kwargs.pop('agent_name', f"fleet-midi-{self._agent_name}")
        domain = kwargs.pop('domain', self._agent_name)
        self._character = AgentCharacter(agent_name=name, domain=domain, **kwargs)

    @property
    def character(self):
        """The underlying AgentCharacter instance (lazy-created if needed)."""
        if self._character is None:
            self._start_character()
        return self._character

    @property
    def agent_alive(self) -> bool:
        """Check if the agent endpoint is reachable via TCP probe."""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            sock.connect((self._host, self._port))
            sock.close()
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    # ─── HTTP Client ──────────────────────────────────────────

    def _get_http(self):
        """Lazy httpx client."""
        if self._http is None:
            try:
                import httpx
                self._http = httpx.Client(timeout=self._response_timeout)
            except ImportError:
                raise ImportError(
                    "httpx is required for FleetMidiEnvironment. "
                    "Install with: pip install httpx"
                )
        return self._http

    def _call_agent(self, payload: Dict[str, Any], mode: str = "cue") -> Dict[str, Any]:
        """Call the agent's POST /agent endpoint.

        Args:
            payload: JSON-serializable dict sent as request body.
            mode: "cue" sends MIDI cue; "think" sends text task.

        Returns:
            Parsed JSON response dict, or an error dict on failure.
        """
        import httpx

        http = self._get_http()
        start = time.monotonic()

        # Wrap payload with mode
        body = dict(payload)
        if mode == "think":
            body['type'] = 'think'

        try:
            resp = http.post(
                f"{self._base_url}/agent",
                json=body,
            )
            elapsed = time.monotonic() - start
            resp.raise_for_status()
            data = resp.json()
            data['response_time_ms'] = round(elapsed * 1000, 1)
            return data
        except httpx.RequestError as e:
            elapsed = time.monotonic() - start
            return {
                'error': f"request_failed: {e}",
                'status': 'error',
                'response_time_ms': round(elapsed * 1000, 1),
                'ternary_vector': [0, 0, 0],
            }
        except httpx.HTTPStatusError as e:
            elapsed = time.monotonic() - start
            return {
                'error': f"http_{e.response.status_code}: {e.response.text[:200]}",
                'status': 'error',
                'response_time_ms': round(elapsed * 1000, 1),
                'ternary_vector': [0, 0, 0],
            }

    # ─── EnvClient Interface ──────────────────────────────────

    def reset(self) -> FleetObservation:
        """Reset the environment.

        Returns a FleetObservation containing the agent's character state
        and readiness. The observation serves as the initial state for RL.

        Returns:
            FleetObservation with agent_alive check, character state,
            and ready=True if the character is initialized.
        """
        self._step_count = 0
        self._last_result = None
        self._episode_reward = 0.0
        self._done = False

        # Probe agent liveness
        alive = self.agent_alive
        latency_ms = 0.0

        # Build observation
        obs = FleetObservation(
            agent_name=self._agent_name,
            agent_host=self._host,
            agent_port=self._port,
            agent_alive=alive,
            domain=self._agent_name,
            character=self.character.to_dict() if self._character else {},
            ready=self._character is not None,
            latency_ms=latency_ms,
            last_result=None,
            step_count=0,
            reward_baseline=self.character.stats.average() if self._character else 10.0,
        )

        self._last_observation = obs
        return obs

    def step(self, action: Union[Dict[str, Any], str]) -> StepResult:
        """Execute one environment step.

        Args:
            action: Either:
                - dict with MIDI cue data (e.g. {'notes': [60, 64, 67]})
                - str with a text task for think mode
                The action is sent to the agent's POST /agent endpoint.

        Returns:
            StepResult containing:
                observation: FleetObservation with updated character state
                reward: Scalar reward based on reward_mode
                done: False (episode continues indefinitely)

        The agent's stats grow naturally from every step.
        """
        self._step_count += 1

        # Determine mode
        if isinstance(action, str):
            mode = "think"
            payload = {'task': action}
        elif isinstance(action, dict) and 'task' in action:
            mode = "think"
            payload = action
        else:
            mode = "cue"
            payload = action

        # Call agent
        result = self._call_agent(payload, mode=mode)
        self._last_result = result

        response_time_ms = result.get('response_time_ms', 100.0)
        has_error = 'error' in result
        success = not has_error

        # Grow character stats
        if self._character is not None:
            request_type = mode  # 'cue' or 'think'
            growth_result = self._character.process_request(
                request_type=request_type,
                success=success,
                response_time_ms=response_time_ms,
            )

        # Compute reward
        reward = self._compute_reward(action, result)

        # Accumulate
        self._episode_reward += reward

        # Build observation
        obs = self._build_observation(result, response_time_ms)

        return StepResult(
            observation=obs,
            reward=reward,
            done=self._done,
        )

    async def step_async(self, action: Union[Dict[str, Any], str]) -> StepResult:
        """Asynchronous step using httpx.AsyncClient.

        Same semantics as step() but returns a coroutine.
        Useful for async training pipelines.
        """
        self._step_count += 1

        if isinstance(action, str):
            mode = "think"
            payload = {'task': action}
        elif isinstance(action, dict) and 'task' in action:
            mode = "think"
            payload = action
        else:
            mode = "cue"
            payload = action

        result = await self._call_agent_async(payload, mode=mode)
        self._last_result = result

        response_time_ms = result.get('response_time_ms', 100.0)
        has_error = 'error' in result
        success = not has_error

        if self._character is not None:
            self._character.process_request(
                request_type=mode,
                success=success,
                response_time_ms=response_time_ms,
            )

        reward = self._compute_reward(action, result)
        self._episode_reward += reward
        obs = self._build_observation(result, response_time_ms)

        return StepResult(
            observation=obs,
            reward=reward,
            done=self._done,
        )

    # ─── Reward Computation ──────────────────────────────────

    def _compute_reward(self, action: Any, result: Dict[str, Any]) -> float:
        """Compute reward based on the configured reward_mode.

        Returns:
            Float reward value.
        """
        if self._reward_mode == RewardMode.CHARACTER:
            # Character-based: reward = stat growth from last step
            return self._character_reward(result)

        elif self._reward_mode == RewardMode.RUBRIC:
            # Rubric-based: reward = rubric score
            return self._rubric_reward(action, result)

        elif self._reward_mode == RewardMode.HYBRID:
            # Hybrid: rubric score * character modifier
            char_reward = self._character_reward(result)
            rubric_reward = self._rubric_reward(action, result)
            # Scale rubric by stat modifier: agents with higher stats
            # amplify their extrinsic reward
            stat_modifier = max(0.5, self.character.stats.average() / 10.0)
            return rubric_reward * stat_modifier + char_reward * 0.1

        return 0.0

    def _character_reward(self, result: Dict[str, Any]) -> float:
        """Intrinsic reward based on character stat growth.

        Computed from:
            - Success/failure: +2.0 for success, -1.0 for error
            - Ternary vector positivity: -1 to +1
            - Response time bonus: +0.5 if fast (<50ms)
            - Streak bonus: +1.0 for milestone streaks
        """
        has_error = 'error' in result
        reward = 0.0

        # Base success/failure
        if has_error:
            reward -= 1.0
        else:
            reward += 2.0

        # Ternary vector bonus
        vec = result.get('ternary_vector', [0, 0, 0])
        if vec:
            # Reward alignment: positive first component = good
            reward += vec[0] * 0.5

        # Speed bonus
        rt = result.get('response_time_ms', 100.0)
        if rt < 50:
            reward += 0.5
        elif rt > 500:
            reward -= 0.5

        # Streak bonus
        if self._character is not None:
            if self._character.success_streak > 0 and self._character.success_streak % 10 == 0:
                reward += 1.0

        return reward

    def _rubric_reward(self, action: Any, result: Dict[str, Any]) -> float:
        """Extrinsic reward from the configured rubric.

        Falls back to SuccessBonusRubric if no rubric is set.
        """
        rubric = self._rubric or SuccessBonusRubric()
        prev_obs = self._last_observation
        prev_result = prev_obs.last_result if prev_obs else None
        return rubric.score(action, result, previous_observation=prev_result)

    # ─── Observation Building ────────────────────────────────

    def _build_observation(self, result: Dict[str, Any],
                           response_time_ms: float) -> FleetObservation:
        """Build a FleetObservation from a step result."""
        alive = 'error' not in result or self.agent_alive
        obs = FleetObservation(
            agent_name=self._agent_name,
            agent_host=self._host,
            agent_port=self._port,
            agent_alive=alive,
            domain=self._agent_name,
            character=self.character.to_dict() if self._character else {},
            ready=self._character is not None,
            latency_ms=response_time_ms,
            last_result=result,
            step_count=self._step_count,
            reward_baseline=self.character.stats.average() if self._character else 10.0,
        )
        self._last_observation = obs
        return obs

    # ─── Async HTTP ─────────────────────────────────────────

    async def _call_agent_async(self, payload: Dict[str, Any],
                                 mode: str = "cue") -> Dict[str, Any]:
        """Async HTTP call to the agent endpoint."""
        import httpx

        start = time.monotonic()
        body = dict(payload)
        if mode == "think":
            body['type'] = 'think'

        try:
            async with httpx.AsyncClient(timeout=self._response_timeout) as client:
                resp = await client.post(f"{self._base_url}/agent", json=body)
                elapsed = time.monotonic() - start
                resp.raise_for_status()
                data = resp.json()
                data['response_time_ms'] = round(elapsed * 1000, 1)
                return data
        except Exception as e:
            elapsed = time.monotonic() - start
            return {
                'error': f"request_failed: {e}",
                'status': 'error',
                'response_time_ms': round(elapsed * 1000, 1),
                'ternary_vector': [0, 0, 0],
            }

    # ─── Auto-Discovery ──────────────────────────────────────

    @classmethod
    def from_agent_name(
        cls,
        agent_name: str,
        host: str = DEFAULT_HOST,
        port: Optional[int] = None,
        probe: bool = True,
        probe_timeout: float = 0.5,
        **kwargs,
    ) -> Optional['FleetMidiEnvironment']:
        """Create an environment for a named agent, with optional health probe.

        This is the primary auto-discovery entry point.

        Args:
            agent_name: Name of the fleet-midi agent.
            host: Host to connect to.
            port: Port (auto-resolved from AGENT_PORTS if None).
            probe: If True, check agent is alive before returning.
            probe_timeout: TCP probe timeout in seconds.
            **kwargs: Passed through to FleetMidiEnvironment constructor.

        Returns:
            FleetMidiEnvironment if agent is alive (or probe=False), else None.

        Examples:
            env = FleetMidiEnvironment.from_agent_name('chord')
            env = FleetMidiEnvironment.from_agent_name('scale', probe=False)
        """
        if port is None:
            if agent_name not in AGENT_PORTS:
                raise ValueError(
                    f"Unknown agent '{agent_name}'. "
                    f"Known: {', '.join(AGENT_NAMES)}"
                )
            port = AGENT_PORTS[agent_name]

        if probe:
            alive, _ = cls._tcp_probe(host, port, probe_timeout)
            if not alive:
                return None

        return cls(agent_name=agent_name, host=host, port=port, **kwargs)

    @classmethod
    def discover_all(
        cls,
        host: str = DEFAULT_HOST,
        port_range: Optional[range] = None,
        probe_timeout: float = 0.5,
        **kwargs,
    ) -> List['FleetMidiEnvironment']:
        """Discover ALL running fleet-midi agents and create environments.

        Scans the default port range (9010–9025) and wraps every
        reachable agent.

        Args:
            host: Host to scan.
            port_range: Range of ports to check (default 9010–9025).
            probe_timeout: TCP probe timeout per port.
            **kwargs: Extra kwargs for each FleetMidiEnvironment.

        Returns:
            List of FleetMidiEnvironment for alive agents.
        """
        if port_range is None:
            port_range = range(min(AGENT_PORTS.values()), max(AGENT_PORTS.values()) + 1)

        # Build reverse port map
        port_to_agent = {p: n for n, p in AGENT_PORTS.items()}

        envs = []
        for port in port_range:
            agent_name = port_to_agent.get(port)
            if agent_name is None:
                continue
            alive, _ = cls._tcp_probe(host, port, probe_timeout)
            if alive:
                env = cls(
                    agent_name=agent_name,
                    host=host,
                    port=port,
                    **kwargs,
                )
                envs.append(env)
        return envs

    # ─── Helpers ─────────────────────────────────────────────

    @staticmethod
    def _tcp_probe(host: str, port: int, timeout: float = 0.5) -> Tuple[bool, float]:
        """TCP connect probe. Returns (alive, latency_seconds)."""
        import socket
        start = time.monotonic()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.close()
            elapsed = time.monotonic() - start
            return True, elapsed
        except (socket.timeout, ConnectionRefusedError, OSError):
            elapsed = time.monotonic() - start
            return False, elapsed

    # ─── Thorough exploration step — continuous mode ────────

    def explore(self, num_steps: int = 10, seed: Optional[int] = None,
                actions: Optional[List[Dict[str, Any]]] = None) -> List[StepResult]:
        """Run a sequence of exploration steps.

        Useful for gathering initial experience or warming up an agent.

        Args:
            num_steps: Number of steps to run.
            seed: Random seed for reproducibility.
            actions: Optional list of actions to use. If None, random cues
                     are generated.

        Returns:
            List of StepResult objects.
        """
        import random
        if seed is not None:
            random.seed(seed)

        if actions is None:
            actions = self._random_actions(num_steps)

        results = []
        self.reset()
        for action in actions[:num_steps]:
            result = self.step(action)
            results.append(result)
        return results

    def _random_actions(self, count: int) -> List[Dict[str, Any]]:
        """Generate random MIDI cue actions for exploration."""
        actions = []
        for _ in range(count):
            num_notes = random.randint(1, 6)
            notes = [random.randint(36, 96) for _ in range(num_notes)]
            actions.append({
                'notes': notes,
                'velocity': random.randint(30, 127),
                'bpm': random.choice([60, 80, 100, 120, 140, 160]),
            })
        return actions

    # ─── Dream Cycle ─────────────────────────────────────────

    def dream(self, memory_limit: int = 20) -> Optional[Dict[str, Any]]:
        """Trigger the character's dream cycle — consolidate memories.

        Should be called periodically (e.g. every N steps) for agents
        to reflect on their experiences.

        Returns:
            Dream consolidation report dict, or None if no character.
        """
        if self._character is None:
            return None
        return self._character.run_dream_cycle()

    # ─── Metadata ────────────────────────────────────────────

    def get_breakdown(self) -> Dict[str, Any]:
        """Return a detailed breakdown of the environment and character state."""
        info = {
            'agent': self._agent_name,
            'host': self._host,
            'port': self._port,
            'reward_mode': self._reward_mode.value,
            'step_count': self._step_count,
            'episode_reward': round(self._episode_reward, 2),
            'alive': self.agent_alive,
        }
        if self._character:
            info['character_name'] = self._character.agent_name
            info['character_level'] = self._character.level
            info['character_title'] = self._character.level_title
            info['character_class'] = self._character.class_name
            info['stats'] = self._character.stats.to_dict()
        return info

    def close(self):
        """Clean up HTTP client."""
        if self._http is not None:
            self._http.close()
            self._http = None

    def __repr__(self) -> str:
        return (f"<FleetMidiEnvironment agent={self._agent_name} "
                f"host={self._host}:{self._port} "
                f"mode={self._reward_mode.value} "
                f"steps={self._step_count}>")
