# OpenEnv → Fleet Characters Refactor Plan

**Date:** 2026-06-11  
**Source:** HuggingFace OpenEnv (forked at SuperInstance/OpenEnv)  
**Target:** `fleet-characters/environment/`  
**Architect:** oracle2

---

## Architecture Overview

The fleet environment system bridges three layers:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Layer 1: OpenEnv Core Port (fleet-characters/environment/)              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │ client_types│  │  env_client  │  │ rubrics/    │  │  auto/        │  │
│  │ .py (done)  │  │  .py (TODO) │  │ base.py     │  │  auto_env.py  │  │
│  └─────────────┘  └──────┬──────┘  │ llm_judge   │  │  discovery.py │  │
│                          │         │ .py         │  └───────┬───────┘  │
│                          │         └──────┬──────┘          │          │
├──────────────────────────┼────────────────┼─────────────────┼──────────┤
│  Layer 2: Fleet-Specific Environments                                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  fleet_env.py  ← FleetMidiEnvironment (wraps 16 agents)         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │   │
│  │  │ chord       │  │ scale       │  │ ...16 agent domains     │ │   │
│  │  │ environment │  │ environment  │  │ as Gymnasium envs      │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────┘   │
├──────────────────────────┬──────────────────────────────────────────────┤
│  Layer 3: Character System Bridge                                       │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Rubric scores → Stat growth → Class emergence → Arc narrative  │   │
│  │  AWM trajectory patterns → Dream consolidation                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Pure Python, zero external dependencies** — Same constraint as the rest of fleet-characters
2. **Type-driven** — Generic types `ActT`, `ObsT`, `StateT` throughout, matching OpenEnv's pattern
3. **Async-native, sync-available** — All env clients support `async/await` with `.sync()` wrappers
4. **Rubrics as transform pipelines** — Composable scoring functions that feed directly into character stat growth
5. **Lazy auto-discovery** — Environments are discovered at runtime via decorator registration, not import-time scanning

### File Layout

```
fleet-characters/environment/
├── __init__.py              # Package exports (partial — needs updating)
├── client_types.py          # StepResult, ObsT, StateT, EnvironmentState (DONE)
├── REFACTOR-PLAN.md         # This file
│
├── env_client.py            # EnvClient ABC + GenericEnvClient + SyncEnvClient
├── rubrics/
│   ├── __init__.py          # Exports all rubric types
│   ├── base.py              # Rubric ABC (nn.Module-style hooks, children, state)
│   └── llm_judge.py         # LLMJudge rubric (LLM-as-a-Judge)
│
├── auto/
│   ├── __init__.py          # Exports discovery and registration
│   ├── auto_env.py          # EnvRegistry, auto_env decorator, discover_environments()
│   └── discovery.py         # Path-based discovery + registration
│
├── fleet_env.py             # FleetMidiEnvironment + per-domain env factories
├── awm_bridge.py            # Agent World Model ↔ Dream Cycle integration
└── types.py                 # Fleet-specific pydantic-style types (Action, Observation, State)
```

### Data Flow (Training Cycle)

```
                   ┌──────────────────────┐
                   │  AutoEnv.discover()  │
                   │  → returns env spec  │
                   └──────────┬───────────┘
                              │
                   ┌──────────▼───────────┐
                   │  FleetMidiEnvironment│
                   │  .reset() → obs      │
                   │  .step(action)→obs   │
                   │  .close()            │
                   └──────────┬───────────┘
                              │ step returns (obs, reward, done, info)
                              │ reward comes from rubric
                   ┌──────────▼───────────┐
                   │  Rubric.__call__()   │
                   │  .forward(action,obs)│ ← LLMJudge or hand-crafted
                   │  → reward float      │
                   └──────────┬───────────┘
                              │ reward routed to character system
                   ┌──────────▼───────────┐
                   │  AgentCharacter       │
                   │  .process_request()   │
                   │  → stat growth        │
                   │  → class emergence    │
                   │  → arc events         │
                   │  → experience logged  │
                   └──────────┬───────────┘
                              │ periodic / on-demand
                   ┌──────────▼───────────┐
                   │  DreamCycle.dream()  │
                   │  → consolidation     │
                   │  → failure replay    │
                   │  → patterns learned  │
                   └──────────┬───────────┘
                              │ patterns → rubric adaptation
                   ┌──────────▼───────────┐
                   │  (loop back to step) │
                   └──────────────────────┘
```

---

## Core Types Ported

### `client_types.py` (ALREADY DONE)

The file at `environment/client_types.py` already ports the essential types. These match OpenEnv's `client_types.py` exactly.

```python
# fleet-characters/environment/client_types.py
# Ported from: OpenEnv/src/openenv/core/client_types.py

from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

ObsT = TypeVar("ObsT")
StateT = TypeVar("StateT")

@dataclass
class StepResult(Generic[ObsT]):
    """Result of one environment step.
    Ported from OpenEnv's core.client_types.StepResult."""
    observation: ObsT
    reward: Optional[float] = None
    done: bool = False

@dataclass
class EnvironmentState(Generic[StateT]):
    """Internal state of an environment."""
    state: StateT
    metadata: dict
```

### `types.py` — Fleet-Specific Action/Observation/State

New file that introduces fleet-midi specific type wrappers (simplified from OpenEnv's pydantic-heavy `env_server/types.py`). We use plain dataclasses to avoid the pydantic dependency.

```python
# fleet-characters/environment/types.py
# Lightly ported from: OpenEnv/src/openenv/core/env_server/types.py
# (pydantic BaseModel → dataclass, no pydantic dependency)

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ServerMode(Enum):
    SIMULATION = "simulation"   # Gym-style reset/step/close
    PRODUCTION = "production"   # MCP JSON-RPC style


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class Action:
    """Agent action to be taken in the environment.
    Ported from OpenEnv Action(BaseModel)."""
    action_type: str  # e.g., "play_note", "analyze_chord", "generate_melody"
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Observation:
    """Environment observation returned after a step.
    Ported from OpenEnv Observation(BaseModel)."""
    done: bool = False
    reward: Optional[float] = None
    data: Dict[str, Any] = field(default_factory=dict)  # domain-specific observation data
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class State:
    """Full state of an environment session.
    Ported from OpenEnv State(BaseModel)."""
    episode_id: int = 0
    step_count: int = 0
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnvironmentMetadata:
    """Describes an environment type.
    Ported from OpenEnv EnvironmentMetadata."""
    name: str
    description: str = ""
    version: str = "0.1.0"
    domain: str = ""  # chord, scale, melody, etc.
    action_space: Dict[str, Any] = field(default_factory=dict)
    observation_space: Dict[str, Any] = field(default_factory=dict)
```

**Key simplification decisions:**
- No pydantic dependency → all types are plain `@dataclass`
- No WebSocket message types → fleet environments are in-process
- No serialization layer → observations/actions are Python dicts
- No concurrency config → single-threaded for now

---

## Environment Client Port

### `env_client.py`

Ported from OpenEnv's `env_client.py` but simplified for in-process use (no WebSocket, no Docker, no auto-reconnect). The core ABC + abstract methods pattern is preserved.

```python
# fleet-characters/environment/env_client.py
# Ported from: OpenEnv/src/openenv/core/env_client.py

import abc
from typing import Generic, Optional, TypeVar
from .client_types import StepResult, ObsT, StateT
from .types import Action, ServerMode, EnvironmentMetadata

ActT = TypeVar("ActT")


class EnvClient(abc.ABC, Generic[ActT, ObsT, StateT]):
    """Abstract base class for environment clients.
    
    Ported from OpenEnv EnvClient. Simplified: no WebSocket, no Docker,
    no reconnect — fleet environments run in-process.
    
    Usage:
        client = SomeEnvClient()
        obs = await client.reset()
        while not obs.done:
            action = agent.act(obs)
            result = await client.step(action)
            obs = result.observation
        await client.close()
    """

    def __init__(self, mode: ServerMode = ServerMode.SIMULATION):
        self._mode = mode
        self._connected = False

    # ── Lifecycle ──────────────────────────────────────────

    async def connect(self):
        """Initialize the environment connection."""
        self._connected = True

    async def disconnect(self):
        """Tear down the environment connection."""
        self._connected = False

    async def close(self):
        """Full cleanup (disconnect + any internal resources)."""
        await self.disconnect()

    # ── Core API ───────────────────────────────────────────

    async def reset(self, **kwargs) -> ObsT:
        """Reset the environment and return initial observation."""
        if not self._connected:
            await self.connect()
        return await self._reset_impl(**kwargs)

    async def step(self, action: ActT) -> StepResult[ObsT]:
        """Execute action, return (observation, reward, done)."""
        payload = self._step_payload(action)
        raw = await self._step_impl(payload)
        return self._parse_result(raw)

    async def state(self) -> StateT:
        """Return current environment state."""
        raw = await self._state_impl()
        return self._parse_state(raw)

    # ── Abstract methods ───────────────────────────────────

    @abc.abstractmethod
    async def _reset_impl(self, **kwargs) -> ObsT:
        """Subclass-specific reset logic."""
        ...

    @abc.abstractmethod
    def _step_payload(self, action: ActT) -> dict:
        """Convert action to a payload dict for the step."""
        ...

    @abc.abstractmethod
    async def _step_impl(self, payload: dict) -> dict:
        """Execute step with payload, return raw dict."""
        ...

    @abc.abstractmethod
    def _parse_result(self, payload: dict) -> StepResult[ObsT]:
        """Parse raw dict into StepResult."""
        ...

    @abc.abstractmethod
    async def _state_impl(self) -> dict:
        """Return raw state dict."""
        ...

    @abc.abstractmethod
    def _parse_state(self, payload: dict) -> StateT:
        """Parse raw dict into StateT."""
        ...

    # ── Sync wrapper ──────────────────────────────────────

    def sync(self) -> 'SyncEnvClient[ActT, ObsT, StateT]':
        return SyncEnvClient(self)


class GenericEnvClient(EnvClient[dict, dict, dict]):
    """EnvClient that works with raw dicts.
    Ported from OpenEnv GenericEnvClient."""

    async def _reset_impl(self, **kwargs) -> dict:
        return {"status": "ready", **kwargs}

    def _step_payload(self, action: dict) -> dict:
        return action

    async def _step_impl(self, payload: dict) -> dict:
        return payload  # subclasses should override

    def _parse_result(self, payload: dict) -> StepResult[dict]:
        return StepResult(
            observation=payload.get("observation", {}),
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    async def _state_impl(self) -> dict:
        return {"step_count": 0}

    def _parse_state(self, payload: dict) -> dict:
        return payload


class SyncEnvClient(Generic[ActT, ObsT, StateT]):
    """Synchronous wrapper around an async EnvClient.
    Ported from OpenEnv SyncEnvClient."""

    def __init__(self, client: EnvClient[ActT, ObsT, StateT]):
        self._client = client

    def reset(self, **kwargs) -> ObsT:
        import asyncio
        return asyncio.run(self._client.reset(**kwargs))

    def step(self, action: ActT) -> StepResult[ObsT]:
        import asyncio
        return asyncio.run(self._client.step(action))

    def state(self) -> StateT:
        import asyncio
        return asyncio.run(self._client.state())

    def close(self):
        import asyncio
        asyncio.run(self._client.close())
```

**Key simplifications vs OpenEnv:**
- No WebSocket connection management (`websockets` dependency removed)
- No Docker/image support (`from_docker_image()`, `from_env()` removed)
- No auto-reconnect logic
- No message timeouts (`message_timeout_s`, `max_message_size_mb` removed)
- No provider/client concept (no OpenAI/Anthropic clients mixed in)
- No `__aenter__`/`__aexit__` (async context manager) — minimal scope for now

---

## Rubric System Port

### `rubrics/__init__.py`

```python
# fleet-characters/environment/rubrics/__init__.py

from .base import Rubric
from .llm_judge import LLMJudge

__all__ = [
    'Rubric',
    'LLMJudge',
]
```

### `rubrics/base.py`

Ported from OpenEnv's `rubrics/base.py`. The core insight is the `nn.Module`-style pattern: rubrics can nest, compose, have hooks, and serialize state.

```python
# fleet-characters/environment/rubrics/base.py
# Ported from: OpenEnv/src/openenv/core/rubrics/base.py

import abc
from typing import (Any, Callable, Dict, Iterator, List, 
                    Optional, Tuple, TypeVar)

ActT = TypeVar("ActT")
ObsT = TypeVar("ObsT")


class Rubric(abc.ABC):
    """Abstract base for reward computation.
    
    Ported from OpenEnv Rubric (which mirrors PyTorch nn.Module).
    
    Key patterns preserved:
    - __call__ → auto-detects sync/async
    - forward() → abstract, override in subclass
    - forward hooks (pre/post)
    - Child rubric registration (auto on attribute set)
    - children() / named_children() iteration
    - state_dict() / load_state_dict() checkpointing
    - last_score tracking
    
    Usage:
        class MyRubric(Rubric):
            def forward(self, action, observation) -> float:
                return compute_reward(action, observation)
        
        rubric = MyRubric()
        score = rubric(action, obs)
    """

    def __init__(self):
        self._children: Dict[str, 'Rubric'] = {}
        self._forward_hooks: List[Callable] = []
        self._forward_pre_hooks: List[Callable] = []
        self.last_score: Optional[float] = None

    def __setattr__(self, name: str, value: Any):
        """Auto-register child rubrics when assigned as attributes."""
        super().__setattr__(name, value)
        if isinstance(value, Rubric) and name != '_children':
            self._children[name] = value

    def __call__(self, action: ActT, observation: ObsT) -> float:
        """Evaluate rubric. Auto-detects sync vs async forward."""
        # Pre-hooks
        for hook in self._forward_pre_hooks:
            hook(self, action, observation)

        result = self.forward(action, observation)

        # Post-hooks  
        for hook in self._forward_hooks:
            hook(self, action, observation, result)

        self.last_score = result
        return result

    @abc.abstractmethod
    def forward(self, action: ActT, observation: ObsT) -> float:
        """Compute reward. Override in subclass.
        
        Ported from OpenEnv Rubric.forward().
        Returns a scalar float reward.
        """
        ...

    # ── Hooks (nn.Module-style) ──────────────────────────

    def register_forward_hook(self, hook: Callable):
        """Register hook: fn(rubric, action, observation, output) → None."""
        self._forward_hooks.append(hook)

    def register_forward_pre_hook(self, hook: Callable):
        """Register pre-hook: fn(rubric, action, observation) → None."""
        self._forward_pre_hooks.append(hook)

    # ── Child management ─────────────────────────────────

    def children(self) -> Iterator['Rubric']:
        return iter(self._children.values())

    def named_children(self) -> Iterator[Tuple[str, 'Rubric']]:
        return iter(self._children.items())

    def rubrics(self) -> Iterator['Rubric']:
        """DFS over all descendant rubrics, including self."""
        yield self
        for child in self._children.values():
            yield from child.rubrics()

    def named_rubrics(self, prefix: str = '') -> Iterator[Tuple[str, 'Rubric']]:
        """DFS with dot-separated paths."""
        if prefix:
            yield prefix, self
        for name, child in self._children.items():
            child_prefix = f"{prefix}.{name}" if prefix else name
            yield from child.named_rubrics(child_prefix)

    def get_rubric(self, path: str) -> Optional['Rubric']:
        """Get rubric by dot-separated path."""
        if not path:
            return self
        parts = path.split('.')
        current = self
        for part in parts:
            if part not in current._children:
                return None
            current = current._children[part]
        return current

    # ── Checkpointing ─────────────────────────────────────

    def state_dict(self) -> Dict[str, Any]:
        """Serialize rubric state."""
        state: Dict[str, Any] = {
            'type': type(self).__name__,
            'last_score': self.last_score,
        }
        for name, child in self._children.items():
            state[f'_{name}'] = child.state_dict()
        return state

    def load_state_dict(self, state: Dict[str, Any]):
        """Load rubric state."""
        self.last_score = state.get('last_score')
        for name, child_state in state.items():
            if name.startswith('_') and name[1:] in self._children:
                self._children[name[1:]].load_state_dict(child_state)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(last_score={self.last_score})"
```

### `rubrics/llm_judge.py`

Ported from OpenEnv's `rubrics/llm_judge.py`. Note: since fleet-characters has no LLM dependency, this is an optional rubric that requires passing in an LLM callable.

```python
# fleet-characters/environment/rubrics/llm_judge.py
# Ported from: OpenEnv/src/openenv/core/rubrics/llm_judge.py

import re
from typing import Any, Callable, Dict, Optional

from .base import Rubric


class LLMJudge(Rubric):
    """LLM-as-a-Judge rubric.
    
    Ported from OpenEnv LLMJudge. Evaluates an action+observation
    pair by asking an LLM to score it.
    
    Unlike OpenEnv's version that uses LLMClient directly, this
    version accepts any async callable so the caller supplies the
    LLM integration.
    
    Args:
        prompt_template: Template with {action} and {observation} placeholders
        llm_callable: Async function (prompt: str) → str response
        score_pattern: Regex to extract score from LLM response
        default_score: Score to return if parsing fails
        normalize: If True, clamp score to [0, 1]
    """

    def __init__(
        self,
        prompt_template: str = (
            "Evaluate this agent action given the observation.\n"
            "Action: {action}\n"
            "Observation: {observation}\n"
            "Score (0-10):"
        ),
        llm_callable: Optional[Callable[[str], str]] = None,
        score_pattern: str = r'(\d+(?:\.\d+)?)',
        default_score: float = 0.0,
        normalize: bool = True,
    ):
        super().__init__()
        self.prompt_template = prompt_template
        self.llm_callable = llm_callable
        self.score_pattern = score_pattern
        self.default_score = default_score
        self.normalize = normalize

    def forward(self, action: Any, observation: Any) -> float:
        """Evaluate using LLM. Falls back to default if no LLM configured."""
        if self.llm_callable is None:
            return self.default_score

        prompt = self.prompt_template.format(
            action=str(action),
            observation=str(observation),
        )
        response = self.llm_callable(prompt)
        return self._parse_score(response)

    def _parse_score(self, response: str) -> float:
        """Extract score from LLM response using regex pattern.
        Ported from OpenEnv LLMJudge score parsing."""
        match = re.search(self.score_pattern, response)
        if not match:
            return self.default_score
        try:
            score = float(match.group(1))
            if self.normalize:
                score = max(0.0, min(1.0, score / 10.0))
            return score
        except (ValueError, IndexError):
            return self.default_score

    def state_dict(self) -> Dict[str, Any]:
        state = super().state_dict()
        state.update({
            'prompt_template': self.prompt_template,
            'default_score': self.default_score,
            'normalize': self.normalize,
        })
        return state

    def load_state_dict(self, state: Dict[str, Any]):
        self.prompt_template = state.get('prompt_template', self.prompt_template)
        self.default_score = state.get('default_score', self.default_score)
        self.normalize = state.get('normalize', self.normalize)
        super().load_state_dict(state)
```

### Rubric ↔ Stat Growth Connection

The key innovation: rubric scores feed directly into character stat growth.

```python
# Connection logic (lives in fleet_env.py, not a separate file):

class StatGrowthRubric(Rubric):
    """Wraps a rubric and routes its score into stat growth.
    
    Every time this rubric is evaluated, it grows the agent's stats
    proportionally to the reward. This connects the training loop's
    reward signal to the character system's evolution.
    """
    
    STAT_MAP = {
        # domain → (primary_stat, secondary_stat)
        'chord':   (StatName.PERCEPTION, StatName.INTELLIGENCE),
        'scale':   (StatName.INTELLIGENCE, StatName.WISDOM),
        'voicing': (StatName.DEXTERITY, StatName.PERCEPTION),
        'tempo':   (StatName.DEXTERITY, StatName.CONSTITUTION),
        'melody':  (StatName.CHARISMA, StatName.PERCEPTION),
        'groove':  (StatName.WISDOM, StatName.DEXTERITY),
        'bass':    (StatName.CONSTITUTION, StatName.INTELLIGENCE),
    }
    
    def __init__(self, inner: Rubric, character: 'AgentCharacter', domain: str):
        super().__init__()
        self.inner = inner
        self.character = character
        self.domain = domain
        self._children['inner'] = inner
    
    def forward(self, action: Any, observation: Any) -> float:
        score = self.inner(action, observation)
        
        # Scale score to stat growth amount
        growth_amount = score * 0.5  # max 0.5 per evaluation
        
        primary, secondary = self.STAT_MAP.get(self.domain, 
                                               (StatName.PERCEPTION, StatName.CHARISMA))
        self.character.stats.grow(primary, growth_amount)
        self.character.stats.grow(secondary, growth_amount * 0.5)
        
        # Log experience for dream cycle
        self.character.dream.add_experience(Experience.simple(
            id=self.character.tick,
            input_=f"env_step:{self.domain}:{action}",
            success=score > 0.5,
            reward=score * 10.0,
            tick=self.character.tick,
        ))
        
        return score
```

---

## FleetMidiEnvironment Design

This is the centerpiece — a Gymnasium-style environment that wraps each of the 16 fleet-midi agents.

```python
# fleet-characters/environment/fleet_env.py

"""
FleetMidiEnvironment — Gymnasium-style environment wrapping fleet-midi agents.

Each agent becomes a reinforcement learning environment:
- reset() → initial observation (agent's current stats, class, signal analysis)
- step(action) → (observation, reward, done, info)
- observation = agent's current state + signal analysis result
- action = what the agent does (analyze chord, generate scale, etc.)
- reward = rubric score → stat growth → class emergence

This enables:
1. RL training on fleet-midi agents (PPO, GRPO, DQN)
2. Auto-curriculum through stat growth (harder tasks become rewarding as stats grow)
3. Character emergence as a training signal
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type

from .env_client import EnvClient, GenericEnvClient, SyncEnvClient
from .client_types import StepResult, ObsT, StateT
from .types import Action, Observation, State, EnvironmentMetadata
from .rubrics import Rubric
from .rubrics.base import ActT

from fleet_characters.stats import Stats, StatName
from fleet_characters.class_ import CharacterClass, AGENT_DEFAULT_CLASSES
from fleet_characters.agent_profile import AgentCharacter
from fleet_characters.dream import Experience


# ── Domain Configurations ─────────────────────────────────

@dataclass
class DomainConfig:
    """Configuration for a single agent domain."""
    name: str
    default_class: CharacterClass
    action_space: Dict[str, Any]
    observation_space: Dict[str, Any]
    difficulty_levels: List[str]  # e.g., ['easy', 'medium', 'hard']
    
    @classmethod
    def all_domains(cls) -> Dict[str, 'DomainConfig']:
        """Return configs for all 16 fleet-midi domains."""
        return {
            'chord': cls(
                name='chord',
                default_class=AGENT_DEFAULT_CLASSES.get('chord', CharacterClass.SCOUT),
                action_space={
                    'actions': ['analyze', 'classify', 'resolve', 'tension_curve'],
                    'params': {'input_notes': 'List[int]'},
                },
                observation_space={
                    'features': ['note_count', 'intervals', 'tension', 'chord_type'],
                    'reward_range': (0.0, 1.0),
                },
                difficulty_levels=['easy', 'medium', 'hard'],
            ),
            'scale': cls(
                name='scale',
                default_class=AGENT_DEFAULT_CLASSES.get('scale', CharacterClass.SAGE),
                action_space={
                    'actions': ['identify', 'suggest', 'transpose', 'analyze_intervals'],
                    'params': {'key': 'int', 'mode': 'str'},
                },
                observation_space={
                    'features': ['notes', 'intervals', 'scale_degree', 'suggested_mode'],
                    'reward_range': (0.0, 1.0),
                },
                difficulty_levels=['easy', 'medium', 'hard'],
            ),
            'voicing': cls(
                name='voicing',
                default_class=AGENT_DEFAULT_CLASSES.get('voicing', CharacterClass.ARTIFICER),
                action_space={
                    'actions': ['analyze', 'optimize', 'suggest_spacing'],
                    'params': {'notes': 'List[int]', 'species': 'int'},
                },
                observation_space={
                    'features': ['voice_count', 'motion_types', 'crossings', 'score'],
                    'reward_range': (0.0, 1.0),
                },
                difficulty_levels=['easy', 'medium', 'hard'],
            ),
            'melody': cls(
                name='melody',
                default_class=AGENT_DEFAULT_CLASSES.get('melody', CharacterClass.BARD),
                action_space={
                    'actions': ['analyze', 'generate', 'evolve', 'complete'],
                    'params': {'seed': 'List[int]', 'length': 'int'},
                },
                observation_space={
                    'features': ['contour', 'motifs', 'range', 'step_vs_leap'],
                    'reward_range': (0.0, 1.0),
                },
                difficulty_levels=['easy', 'medium', 'hard'],
            ),
            'tempo': cls(
                name='tempo',
                default_class=AGENT_DEFAULT_CLASSES.get('tempo', CharacterClass.GUARDIAN),
                action_space={
                    'actions': ['analyze', 'suggest', 'adjust'],
                    'params': {'bpm': 'float', 'time_signature': 'str'},
                },
                observation_space={
                    'features': ['bpm', 'stability', 'timing_accuracy'],
                    'reward_range': (0.0, 1.0),
                },
                difficulty_levels=['easy', 'medium', 'hard'],
            ),
            'groove': cls(
                name='groove',
                default_class=AGENT_DEFAULT_CLASSES.get('groove', CharacterClass.DIPLOMAT),
                action_space={
                    'actions': ['analyze_swing', 'generate_pattern', 'sync'],
                    'params': {'pattern_type': 'str', 'swing': 'float'},
                },
                observation_space={
                    'features': ['euclidean', 'swing', 'syncopation'],
                    'reward_range': (0.0, 1.0),
                },
                difficulty_levels=['easy', 'medium', 'hard'],
            ),
            'bass': cls(
                name='bass',
                default_class=AGENT_DEFAULT_CLASSES.get('bass', CharacterClass.WARDEN),
                action_space={
                    'actions': ['analyze_motion', 'generate_line', 'resolve'],
                    'params': {'root': 'int', 'pattern': 'str'},
                },
                observation_space={
                    'features': ['root_motion', 'step_pattern', 'range'],
                    'reward_range': (0.0, 1.0),
                },
                difficulty_levels=['easy', 'medium', 'hard'],
            ),
        }


# ── FleetMidiEnvironment ──────────────────────────────────


class FleetMidiEnvironment(EnvClient[Action, Observation, State]):
    """Gymnasium-style environment wrapping a fleet-midi agent domain.
    
    Each environment wraps one agent domain (chord, scale, voicing, etc.)
    and provides the standard reset/step interface used by RL training loops.
    
    Key design:
    - The 'action' is the agent's domain-specific operation
    - The 'observation' is the agent's current stats + signal analysis
    - The 'reward' comes from a rubric (or defaults to correctness heuristic)
    - Episodes are N-step rollouts with configurable length
    - On done=True, the agent's stats have been updated (class may have emerged)
    
    Usage:
        env = FleetMidiEnvironment.for_domain('chord', rubric=SomeRubric())
        obs = await env.reset(difficulty='medium')
        done = False
        total_reward = 0.0
        while not done:
            action = env.sample_action()
            result = await env.step(action)
            total_reward += result.reward
            done = result.done
        await env.close()
        print(f"Episode reward: {total_reward}")
    """

    def __init__(
        self,
        domain: str,
        character: Optional[AgentCharacter] = None,
        rubric: Optional[Rubric] = None,
        max_steps: int = 20,
        config: Optional[DomainConfig] = None,
    ):
        """
        Args:
            domain: Agent domain name ('chord', 'scale', 'voicing', etc.)
            character: Existing AgentCharacter to use (creates one if None)
            rubric: Reward function (defaults to correctness heuristic)
            max_steps: Episode length (steps before done=True)
            config: Domain configuration (auto-resolved if None)
        """
        super().__init__()
        self.config = config or DomainConfig.all_domains().get(domain)
        if self.config is None:
            raise ValueError(f"Unknown domain: {domain}. "
                             f"Available: {list(DomainConfig.all_domains().keys())}")
        
        self.domain = domain
        self.character = character or AgentCharacter(
            agent_name=f"fleet-midi-{domain}-env",
            domain=domain,
        )
        self.rubric = rubric
        self.max_steps = max_steps
        self.current_step = 0
        self.difficulty = 'easy'
        self.episode_count = 0

    # ── Factory ───────────────────────────────────────────

    @classmethod
    def for_domain(
        cls,
        domain: str,
        character: Optional[AgentCharacter] = None,
        rubric: Optional[Rubric] = None,
    ) -> 'FleetMidiEnvironment':
        """Create a FleetMidiEnvironment for a specific domain."""
        config = DomainConfig.all_domains().get(domain)
        if config is None:
            raise ValueError(f"Unknown domain: {domain}")
        return cls(domain=domain, character=character, rubric=rubric, config=config)

    @classmethod
    def all_envs(
        cls,
        base_rubric: Optional[Rubric] = None,
    ) -> Dict[str, 'FleetMidiEnvironment']:
        """Create environments for ALL fleet-midi domains."""
        return {
            name: cls.for_domain(name, rubric=base_rubric)
            for name in DomainConfig.all_domains()
        }

    # ── EnvClient implementation ──────────────────────────

    async def _reset_impl(self, **kwargs) -> Observation:
        """Reset the environment for a new episode.
        
        Args:
            difficulty: 'easy', 'medium', or 'hard' (affects task complexity)
            seed: Optional random seed for reproducibility
        """
        self.difficulty = kwargs.get('difficulty', random.choice(self.config.difficulty_levels))
        seed = kwargs.get('seed')
        if seed is not None:
            random.seed(seed)
        
        self.current_step = 0
        self.episode_count += 1
        
        # Build observation from current character state
        return self._build_observation(task_description=f"New {self.difficulty} episode")

    def _step_payload(self, action: Action) -> dict:
        """Convert action to payload for step execution."""
        return {
            'action_type': action.action_type,
            'parameters': action.parameters,
            'domain': self.domain,
            'difficulty': self.difficulty,
        }

    async def _step_impl(self, payload: dict) -> dict:
        """Execute one step: process action through character system.
        
        This is the core simulation logic:
        1. Apply the action to get a result
        2. Score with rubric (or heuristic)
        3. Update character (stats grow, class may emerge)
        4. Check if episode is done
        """
        self.current_step += 1
        action_type = payload['action_type']
        params = payload.get('parameters', {})
        
        # Simulate action execution based on domain
        # (In production, this calls the actual fleet-midi agent logic)
        result = self._simulate_action(action_type, params)
        
        # Score the result
        if self.rubric is not None:
            reward = self.rubric(self.character, result)
        else:
            reward = self._heuristic_reward(result)
        
        # Process through character system (stats grow, class may emerge)
        response_time_ms = params.get('response_time_ms', random.uniform(30, 300))
        self.character.process_request(
            request_type=action_type,
            success=reward > 0.5,
            response_time_ms=response_time_ms,
        )
        
        # Check done condition
        done = self.current_step >= self.max_steps
        
        return {
            'observation': self._build_observation(
                task_description=f"Step {self.current_step}/{self.max_steps}",
                result=result,
            ),
            'reward': reward,
            'done': done,
            'info': {
                'step': self.current_step,
                'difficulty': self.difficulty,
                'character': self.character.to_dict(),
                'action_type': action_type,
            },
        }

    def _parse_result(self, payload: dict) -> StepResult[Observation]:
        """Parse raw step result into StepResult."""
        obs = payload.get('observation', self._build_observation())
        return StepResult(
            observation=obs,
            reward=payload.get('reward'),
            done=payload.get('done', False),
        )

    async def _state_impl(self) -> dict:
        """Return current environment state."""
        return {
            'domain': self.domain,
            'step': self.current_step,
            'max_steps': self.max_steps,
            'difficulty': self.difficulty,
            'episode_count': self.episode_count,
            'character': self.character.to_dict(),
        }

    def _parse_state(self, payload: dict) -> State:
        """Parse raw state dict into State."""
        return State(
            episode_id=self.episode_count,
            step_count=self.current_step,
            data=payload,
        )

    # ── Helpers ───────────────────────────────────────────

    def _build_observation(
        self,
        task_description: str = "",
        result: Optional[Dict[str, Any]] = None,
    ) -> Observation:
        """Build observation from current character + domain state."""
        data = {
            'domain': self.domain,
            'difficulty': self.difficulty,
            'step': self.current_step,
            'max_steps': self.max_steps,
            'task_description': task_description,
            'agent_stats': self.character.stats.to_dict(),
            'agent_class': self.character.class_name,
            'agent_class_archetype': self.character.current_class.archetype.value,
            'agent_level': self.character.level,
            'agent_level_title': self.character.level_title,
        }
        if result:
            data['result'] = result
        return Observation(
            done=self.current_step >= self.max_steps,
            data=data,
        )

    def _heuristic_reward(self, result: Dict[str, Any]) -> float:
        """Default heuristic reward when no rubric is configured.
        
        Higher difficulty = higher potential reward but harder to get.
        """
        base = {'easy': 0.3, 'medium': 0.5, 'hard': 0.8}.get(self.difficulty, 0.3)
        # Add noise for variety
        noise = random.gauss(0, 0.1)
        return max(0.0, min(1.0, base + noise))

    def _simulate_action(self, action_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate action execution for the domain.
        
        TODO: In production, call the actual fleet-midi agent logic.
        This simulation exists so the env can be tested without 
        running the full agent stack.
        """
        return {
            'action_type': action_type,
            'status': 'success',
            'confidence': random.uniform(0.5, 1.0),
            'details': f"Simulated {self.domain} {action_type}",
        }

    def close(self):
        """Cleanup — reset step counter, no persistent resources."""
        self.current_step = 0

    def get_metadata(self) -> EnvironmentMetadata:
        """Return environment metadata (for auto-discovery)."""
        return EnvironmentMetadata(
            name=f"fleet-midi-{self.domain}",
            description=f"FleetMIDI environment for {self.domain} agent",
            version="0.1.0",
            domain=self.domain,
            action_space=self.config.action_space,
            observation_space=self.config.observation_space,
        )

    # ── Convenience for training loops ────────────────────

    def sample_action(self) -> Action:
        """Sample a random valid action (useful for random baseline)."""
        action_type = random.choice(self.config.action_space['actions'])
        return Action(
            action_type=action_type,
            parameters={'response_time_ms': random.uniform(30, 300)},
        )

    def get_character_snapshot(self) -> Dict[str, Any]:
        """Get current character state (for logging/tracking)."""
        return self.character.to_dict()
```

---

## AutoEnv Integration

The auto-discovery system lets training code find and instantiate environments without manual configuration.

### `auto/__init__.py`

```python
# fleet-characters/environment/auto/__init__.py

from .auto_env import EnvRegistry, AutoEnv
from .discovery import discover_environments, register_environment

__all__ = [
    'EnvRegistry',
    'AutoEnv',
    'discover_environments',
    'register_environment',
]
```

### `auto/auto_env.py`

Ported from OpenEnv's `auto_env.py` concept — environments register themselves with metadata, and auto-discovery finds them.

```python
# fleet-characters/environment/auto/auto_env.py

from typing import (Any, Callable, Dict, Iterator, List, 
                    Optional, Tuple, Type)
from dataclasses import dataclass, field
import inspect

from ..types import EnvironmentMetadata


@dataclass
class EnvSpec:
    """Specification for a discovered environment."""
    name: str
    domain: str
    metadata: EnvironmentMetadata
    factory: Callable[..., Any]  # Callable[[], EnvClient]
    difficulty_levels: List[str] = field(default_factory=lambda: ['easy', 'medium', 'hard'])


class EnvRegistry:
    """Central registry for all fleet environments.
    
    Environments register themselves (via decorator or explicitly),
    and can be discovered by training loops.
    """
    
    def __init__(self):
        self._entries: Dict[str, EnvSpec] = {}

    def register(self, spec: EnvSpec):
        """Register an environment spec."""
        self._entries[spec.name] = spec

    def register_factory(self, name: str, domain: str, 
                         factory: Callable, metadata: EnvironmentMetadata):
        """Register an environment from a factory function."""
        self._entries[name] = EnvSpec(
            name=name,
            domain=domain,
            metadata=metadata,
            factory=factory,
        )

    def get(self, name: str) -> Optional[EnvSpec]:
        """Get environment spec by name."""
        return self._entries.get(name)

    def list(self, domain: Optional[str] = None) -> List[EnvSpec]:
        """List all registered environments, optionally filtered by domain."""
        if domain:
            return [e for e in self._entries.values() if e.domain == domain]
        return list(self._entries.values())

    def names(self) -> List[str]:
        return list(self._entries.keys())

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[EnvSpec]:
        return iter(self._entries.values())


# Global registry singleton
_REGISTRY = EnvRegistry()


class AutoEnv:
    """Auto-discovered environment.
    
    Usage:
        # Get a specific env
        env = AutoEnv.get('fleet-midi-chord')
        
        # List all envs
        for spec in AutoEnv.list():
            print(spec.name)
        
        # Filter by domain
        for spec in AutoEnv.list(domain='music'):
            print(spec.name)
    """
    
    @staticmethod
    def get(name: str, **kwargs) -> Any:
        """Instantiate an environment by name."""
        spec = _REGISTRY.get(name)
        if spec is None:
            raise KeyError(f"Environment '{name}' not found. "
                           f"Available: {_REGISTRY.names()}")
        return spec.factory(**kwargs)
    
    @staticmethod
    def list(domain: Optional[str] = None) -> List[EnvSpec]:
        """List available environment specs."""
        return _REGISTRY.list(domain)
    
    @staticmethod
    def register(spec: EnvSpec):
        """Register an environment."""
        _REGISTRY.register(spec)
    
    @staticmethod
    def discover(**kwargs) -> Dict[str, EnvSpec]:
        """Discover and register all fleet environments.
        
        Returns dict of {name: EnvSpec} for all discovered environments.
        """
        from .discovery import discover_environments
        return discover_environments(**_REGISTRY, **kwargs)
    
    @staticmethod
    def registry() -> EnvRegistry:
        """Return the global registry."""
        return _REGISTRY
```

### `auto/discovery.py`

Discovery finds environments by scanning known domain configs and registering them.

```python
# fleet-characters/environment/auto/discovery.py

from typing import Any, Callable, Dict, List, Optional, Type
import importlib

from .auto_env import EnvRegistry, EnvSpec
from ..types import EnvironmentMetadata
from ..fleet_env import FleetMidiEnvironment, DomainConfig


def register_environment(
    name: str,
    domain: str,
    factory: Callable[..., Any],
    metadata: Optional[EnvironmentMetadata] = None,
    registry: Optional[EnvRegistry] = None,
):
    """Decorator to register an environment class/factory.
    
    Usage:
        @register_environment('fleet-midi-chord', 'chord')
        def make_chord_env(**kwargs):
            return FleetMidiEnvironment.for_domain('chord', **kwargs)
    """
    reg = registry or _get_global_registry()
    spec = EnvSpec(
        name=name,
        domain=domain,
        metadata=metadata or EnvironmentMetadata(name=name, domain=domain),
        factory=factory,
    )
    reg.register(spec)
    return factory


def discover_environments(
    registry: Optional[EnvRegistry] = None,
) -> Dict[str, EnvSpec]:
    """Discover all fleet-midi environments by scanning DomainConfig.
    
    This automatically registers one environment per domain.
    Returns dict of {name: EnvSpec}.
    """
    reg = registry or _get_global_registry()
    discovered = {}
    
    for domain_name, config in DomainConfig.all_domains().items():
        env_name = f"fleet-midi-{domain_name}"
        
        # Create factory function
        def make_env(domain=domain_name, **kwargs):
            return FleetMidiEnvironment.for_domain(domain, **kwargs)
        
        spec = EnvSpec(
            name=env_name,
            domain=domain_name,
            metadata=EnvironmentMetadata(
                name=env_name,
                description=f"FleetMIDI environment for {domain_name} agent",
                domain=domain_name,
                action_space=config.action_space,
                observation_space=config.observation_space,
            ),
            factory=make_env,
            difficulty_levels=config.difficulty_levels,
        )
        reg.register(spec)
        discovered[env_name] = spec
    
    return discovered


def _get_global_registry() -> EnvRegistry:
    """Get or create the global registry."""
    from .auto_env import _REGISTRY
    return _REGISTRY
```

### Auto-Discovery Integration with Training

```python
# Usage pattern in training code:

from fleet_characters.environment.auto import AutoEnv

# On startup: discover all environments
specs = AutoEnv.discover()
print(f"Discovered {len(specs)} environments")

# Use an environment
env = AutoEnv.get('fleet-midi-chord', rubric=my_rubric)
obs = await env.reset(difficulty='hard')

# List all available
for spec in AutoEnv.list():
    print(f"  {spec.name} ({spec.domain}, levels={spec.difficulty_levels})")
```

---

## AWM-Dream Cycle Bridge

The Agent World Model (AWM) bridge connects OpenEnv's AWM environment to the fleet dream cycle. When an agent trains in an AWM scenario, the trajectory is consolidated into the agent's dream patterns.

### `awm_bridge.py`

```python
# fleet-characters/environment/awm_bridge.py

"""
Agent World Model ↔ Dream Cycle Bridge.

Connects OpenEnv's AWM environment trajectories to the fleet
character dream cycle system.

Data flow:
1. Agent trains in AWM scenario → collects trajectory (actions, observations, rewards)
2. Trajectory is converted to DreamCycle experiences
3. DreamCycle.dream() consolidates patterns from AWM training
4. Consolidated patterns influence future AWM behavior

This bridges:
- OpenEnv's AWMEnv (envs/agent_world_model_env/) — 1,000 synthetic tool-use environments
- Fleet's DreamCycle (dream.py) — REM-sleep memory consolidation
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from fleet_characters.dream import (
    DreamCycle, Experience, MemoryConsolidation, 
    FailureReplay, ConsolidationReport, ConsolidatedPattern,
)

from .env_client import EnvClient
from .client_types import StepResult


@dataclass
class AWMExperienceAdapter:
    """Converts AWM trajectory entries to fleet DreamCycle experiences.
    
    AWM trajectories have:
    - tool_calls (list of tool invocations with results)
    - verify_result (completion status + reward)
    - scenario metadata
    
    This adapter maps them to Experience objects.
    """
    
    @staticmethod
    def from_awm_trajectory(
        trajectory: Dict[str, Any],
        starting_tick: int = 0,
    ) -> List[Experience]:
        """Convert an AWM trajectory dict into DreamCycle experiences.
        
        AWM trajectory format (from awm_environment.py):
        {
            'task': str,
            'scenario': str,
            'steps': [{
                'action_type': 'list_tools'|'call_tool'|'verify',
                'action_params': {...},
                'observation': {...},
                'reward': float,
                'result': str,
            }],
            'verify_result': {
                'result': 'complete'|'incomplete',
                'reward': float,
            },
            'total_reward': float,
        }
        """
        experiences = []
        steps = trajectory.get('steps', [])
        
        for i, step in enumerate(steps):
            success = step.get('reward', 0) > 0.5
            exp = Experience.simple(
                id=starting_tick + i,
                input_=f"awm:{trajectory.get('scenario','')}:{step.get('action_type','')}",
                success=success,
                reward=step.get('reward', 0.0),
                tick=starting_tick + i,
            )
            # Enrich embedding with action + observation features
            obs = step.get('observation', {})
            exp.embedding = [
                step.get('reward', 0.0),
                1.0 if success else 0.0,
                float(obs.get('num_tools', 0)),
            ]
            experiences.append(exp)
        
        return experiences
    
    @staticmethod
    def to_consolidated_patterns(
        awm_results: List[Dict[str, Any]],
    ) -> List[ConsolidatedPattern]:
        """Extract high-level patterns from multiple AWM results."""
        patterns = []
        
        # Pattern: scenario difficulty
        if awm_results:
            avg_reward = sum(r.get('total_reward', 0) for r in awm_results) / len(awm_results)
            patterns.append(ConsolidatedPattern(
                description=f"AWM training session: {len(awm_results)} scenarios, "
                           f"avg reward: {avg_reward:.2f}",
                avg_reward=avg_reward,
                sample_count=len(awm_results),
                tags=["awm", "training"],
                is_success_pattern=avg_reward > 0.5,
            ))
        
        return patterns


@dataclass
class AWMBridge:
    """Bridge connecting AWM training to DreamCycle consolidation.
    
    Usage:
        bridge = AWMBridge(dream_cycle)
        
        # After AWM training:
        bridge.ingest_trajectory(trajectory)
        
        # Later, trigger consolidation:
        report = bridge.consolidate()
        
        # Get dream-influenced behavior suggestions:
        suggestions = bridge.suggest_actions_for_awm(scenario_id)
    """
    
    dream_cycle: DreamCycle
    _pending_experiences: List[Experience] = field(default_factory=list)
    _awm_results: List[Dict[str, Any]] = field(default_factory=list)
    _tick_counter: int = 0
    
    def ingest_trajectory(self, trajectory: Dict[str, Any]):
        """Convert AWM trajectory to experiences and add to dream cycle."""
        experiences = AWMExperienceAdapter.from_awm_trajectory(
            trajectory, starting_tick=self._tick_counter,
        )
        self._tick_counter += len(experiences)
        
        for exp in experiences:
            self.dream_cycle.add_experience(exp)
        
        self._pending_experiences.extend(experiences)
        self._awm_results.append(trajectory)
    
    def ingest_batch(self, trajectories: List[Dict[str, Any]]):
        """Ingest multiple AWM trajectories at once."""
        for traj in trajectories:
            self.ingest_trajectory(traj)
    
    def consolidate(self, duration_ticks: int = 50) -> ConsolidationReport:
        """Trigger dream cycle consolidation of AWM experiences."""
        report = self.dream_cycle.dream(duration_ticks)
        self._pending_experiences = []
        return report
    
    def suggest_actions_for_awm(self, scenario_id: str) -> List[Dict[str, str]]:
        """Generate behavior suggestions based on dream patterns.
        
        Uses FailureReplay to find patterns relevant to this scenario.
        """
        # Find AWM-specific experiences
        relevant = [
            e for e in self.dream_cycle.consolidation.experiences
            if scenario_id in e.input_
        ]
        
        if not relevant:
            return []
        
        # Run failure replay focused on this scenario
        consolidation = MemoryConsolidation(experiences=relevant)
        replay = FailureReplay(speed=1.5)
        result = replay.replay(consolidation)
        
        return [
            {'what': s[0], 'why': s[1]}
            for s in result.suggestions
        ]
    
    def get_awm_training_report(self) -> Dict[str, Any]:
        """Get a report of AWM training progress."""
        return {
            'trajectories_ingested': len(self._awm_results),
            'experiences_created': len(self._pending_experiences),
            'total_experiences': len(self.dream_cycle.consolidation),
            'patterns_discovered': len(self.dream_cycle.consolidation.patterns),
            'cycles_completed': self.dream_cycle.cycles_completed,
            'last_dream': self.dream_cycle.last_report.to_dict() 
                          if self.dream_cycle.last_report else None,
        }


def create_awm_dream_pipeline(
    dream_cycle: Optional[DreamCycle] = None,
) -> Tuple[AWMBridge, DreamCycle]:
    """Create a ready-to-use AWM→Dream pipeline.
    
    Returns:
        (bridge, dream_cycle) tuple.
    """
    if dream_cycle is None:
        dream_cycle = DreamCycle(
            consolidation=MemoryConsolidation(min_experiences=3),
            replay=FailureReplay(speed=2.0),
        )
    bridge = AWMBridge(dream_cycle=dream_cycle)
    return bridge, dream_cycle
```

### AWM → Dream Cycle → Training Loop Integration

The full integration with a GRPO-style training loop:

```python
# Conceptual integration:

async def awm_training_loop(bridge, env, agent, num_episodes=100):
    """Train an agent in AWM and consolidate via dream cycles."""
    
    for episode in range(num_episodes):
        # 1. Reset AWM environment
        obs = await env.reset(scenario=f"e_commerce_{episode % 1000}", task_idx=0)
        
        trajectory = {'steps': [], 'scenario': obs.data.get('scenario', '')}
        done = False
        total_reward = 0.0
        
        while not done:
            action = agent.act(obs)
            result = await env.step(action)
            
            trajectory['steps'].append({
                'action_type': action.action_type,
                'action_params': action.parameters,
                'observation': result.observation.data,
                'reward': result.reward,
            })
            total_reward += result.reward
            done = result.done
        
        trajectory['total_reward'] = total_reward
        
        # 2. Ingest trajectory into dream cycle
        bridge.ingest_trajectory(trajectory)
        
        # 3. Every 10 episodes, consolidate
        if episode > 0 and episode % 10 == 0:
            report = bridge.consolidate(duration_ticks=50)
            print(f"Episode {episode}: {report.summary}")
            
            # 4. Use dream patterns to adjust agent behavior
            suggestions = bridge.suggest_actions_for_awm(trajectory['scenario'])
            agent.adjust_behavior(suggestions)
    
    return bridge.get_awm_training_report()
```

---

## Implementation Priority

### Phase 1: Core Port (P0 — Immediate)

| Component | Files | Effort | Dependencies |
|-----------|-------|--------|--------------|
| `client_types.py` | ✅ DONE | — | — |
| `types.py` | NEW file | 15 min | None |
| `env_client.py` | NEW file | 30 min | `client_types`, `types` |
| `rubrics/base.py` | NEW file | 30 min | None |
| `rubrics/llm_judge.py` | NEW file | 15 min | `rubrics/base` |
| `rubrics/__init__.py` | NEW file | 5 min | `base`, `llm_judge` |
| Update `__init__.py` | Edit existing | 10 min | All above |

**Acceptance:** `pytest` passes with integration test that creates env, resets, steps, and checks reward is float.

### Phase 2: FleetMidiEnvironment (P0 — Same Session)

| Component | Files | Effort | Dependencies |
|-----------|-------|--------|--------------|
| `fleet_env.py` | NEW file | 45 min | Phase 1 + fleet_characters |
| Integration test | NEW file | 20 min | `fleet_env.py` |

**Acceptance:** Creates env for each domain, runs 5-step episode, verifies stat growth after episode.

### Phase 3: Auto-Discovery (P1 — Same Session)

| Component | Files | Effort | Dependencies |
|-----------|-------|--------|--------------|
| `auto/auto_env.py` | NEW file | 20 min | Phase 2 |
| `auto/discovery.py` | NEW file | 20 min | `auto_env` |
| `auto/__init__.py` | NEW file | 5 min | Both above |

**Acceptance:** `AutoEnv.discover()` returns 16 envs, `AutoEnv.get('fleet-midi-chord')` instantiates correctly.

### Phase 4: AWM Bridge (P1 — Same Session)

| Component | Files | Effort | Dependencies |
|-----------|-------|--------|--------------|
| `awm_bridge.py` | NEW file | 30 min | Phase 2 + dream.py |

**Acceptance:** AWM trajectory JSON converts to experiences, `consolidate()` produces patterns.

### Phase 5: StatGrowthRubric + GRPO Integration (P2 — Next Session)

| Component | Files | Effort | Dependencies |
|-----------|-------|--------|--------------|
| `StatGrowthRubric` in `fleet_env.py` | Edit | 15 min | Phase 2 |
| GRPO training harness | NEW file | 1 hr | Phase 1-4 |

**Acceptance:** RL training loop runs, stats grow, class can emerge from training.

### Execution Order

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5
  (30m)      (45m)       (30m)       (30m)       (1-2h)
```

Total: ~3-4 hours for full implementation.

### Rollback Plan

Each phase is independent:
- Phase 1-3 don't affect existing fleet-characters code (new files only)
- Phase 4 is query-only (reads from dream cycle, no write mutations)
- Phase 5 is the only one that touches agent_profile.py (adding rubric integration point)
- If anything breaks: delete the `environment/` directory and revert `__init__.py`

---

## Appendix: OpenEnv vs Fleet Architecture Comparison

| Aspect | OpenEnv | Fleet-Characters (This Refactor) |
|--------|---------|----------------------------------|
| **Transport** | WebSocket / HTTP (Docker containers) | In-process (no network) |
| **Types** | pydantic BaseModel everywhere | Plain dataclasses (no pydantic dep) |
| **Rubrics** | nn.Module-style with hooks | Same — exact port |
| **Rubric nesting** | Sequential, Gate, WeightedSum | Not yet — add when needed |
| **LLMJudge** | Uses LLMClient (OpenAI/Anthropic) | Accepts any callable |
| **Auto-discover** | AutoEnv with path scanning | Decorator + DomainConfig scan |
| **AWM** | Subprocess + SQLite per scenario | Adapter that reads trajectory JSON |
| **Training harness** | HarnessAdapter + CollectRunner | Coming in Phase 5 |
| **GRPO** | Full Forge integration | Planned for Phase 5 |
| **Concurrency** | ThreadPoolExecutor + sessions | Single-threaded (for now) |
| **State serialization** | JSON-RPC over WS | dict/dataclass in-process |
| **Character integration** | None | **Core feature** — rubric → stat growth |

### Files to NOT port from OpenEnv

These OpenEnv components are intentionally excluded:

- `env_server/http_server.py` — HTTP routing, FastAPI app (no server needed)
- `env_server/interfaces.py` — `Environment` ABC (we use `EnvClient` on the client side only)
- `env_server/types.py` — Most WS message types (no WebSocket)
- `env_server/serialization.py` — JSON serialization (in-process = no serialization)
- `containers/` — Docker provider, K8s provider (no containers)
- `mcp_client.py` — MCP session management (not needed for in-process)
- `llm_client.py` — LLMClient (rubric takes any callable)
- `sync_client.py` — Inlined into `env_client.py` as `SyncEnvClient`
- `harness/` — Full harness system (Phase 5 will build a lighter version)
- `evals/` — Evaluation framework (future)
- `tools/` — Git server, Python executor (not needed)
