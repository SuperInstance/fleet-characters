# Repo Split Analysis: fleet-env vs fleet-characters

## Current State

```
fleet-characters/
├── environment/              ← Standalone package (also symlinked into fleet_characters/)
│   ├── __init__.py
│   ├── client_types.py
│   ├── env_client.py
│   ├── fleet_env.py          ← LAZY runtime import from fleet_characters.agent_profile
│   ├── rubrics/
│   │   ├── __init__.py
│   │   ├── base.py           ← TYPE_CHECKING-only import from fleet_characters.stats
│   │   ├── fleet_rubrics.py  ← LAZY runtime import from fleet_characters.stats (in 5 methods)
│   │   └── llm_judge.py      ← LAZY runtime import from fleet_characters.stats
│   └── auto/
│       ├── __init__.py
│       ├── _discovery.py     ← Pure (requests, httpx)
│       ├── auto_action.py    ← Pure
│       └── auto_env.py       ← LAZY optional import from fleet_characters
│
└── fleet_characters/         ← The pip-installable package
    ├── __init__.py
    ├── stats.py
    ├── class_.py
    ├── arc.py
    ├── dream.py
    ├── agent_profile.py
    ├── signal/
    └── environment -> ../environment  ← SYMLINK
```

## Dependency Graph

```
fleet_characters package (no deps on environment):
  ├── stats.py       — pure
  ├── class_.py      → stats
  ├── arc.py         — pure
  ├── dream.py       — pure
  ├── agent_profile  → stats, class_, arc, dream
  └── signal/        — pure signal processing

environment package (OPTIONAL deps on fleet_characters, ALL runtime-lazy):
  ├── client_types   — pure
  ├── env_client     — pure
  ├── rubrics/
  │   ├── base       — TYPE_CHECKING import of Stats (resolved lazily)
  │   ├── fleet_rubrics → 5 x `from fleet_characters.stats import StatName`
  │   │                   inside _apply_stat_growth() methods
  │   └── llm_judge  → 1 x `from fleet_characters.stats import StatName`
  ├── auto/
  │   ├── _discovery — pure
  │   ├── auto_action — pure
  │   └── auto_env   → optional lazy imports from fleet_characters (try/except)
  └── fleet_env      → lazy `from fleet_characters.agent_profile import AgentCharacter`
                        inside _start_character()
```

## Key Finding

**The environment code is already ~90% decoupled.** All dependencies on `fleet_characters` are:
1. Inside method bodies (runtime-lazy)
2. In try/except ImportError guards (auto_env.py)
3. In TYPE_CHECKING blocks (resolved only for type hints)

No module-level `import fleet_characters` exists anywhere in the environment code.

## What Goes Where

### New Repo: `fleet-env` (fleet_env package)
```
fleet-env/
├── src/fleet_env/
│   ├── __init__.py          # Public API exports
│   ├── client_types.py      # StepResult, ObsT, StateT
│   ├── env_client.py        # EnvClient base class
│   ├── rubrics/
│   │   ├── __init__.py
│   │   ├── base.py          # Rubric ABC (nn.Module-style)
│   │   ├── base_stats.py    # NEW: StatBridge protocol for character integration
│   │   ├── success.py       # SuccessBonusRubric (generalized, no fleet deps)
│   │   ├── ternary.py       # TernaryAccuracyRubric (via StatBridge)
│   │   ├── timing.py        # ResponseTimeRubric (via StatBridge)
│   │   ├── harmonic.py      # HarmonicConsonanceRubric (via StatBridge)
│   │   ├── rhythm.py        # RhythmAccuracyRubric (via StatBridge)
│   │   ├── composite.py     # CompositeFleetRubric (via StatBridge)
│   │   └── llm_judge.py     # LLMJudge (via StatBridge)
│   ├── auto/
│   │   ├── __init__.py
│   │   ├── discovery.py     # Auto-discovery (was _discovery.py)
│   │   ├── actions.py       # Action builders (was auto_action.py)
│   │   └── env.py           # AutoEnv factory (was auto_env.py, no fleet-characters dep)
│   └── fleet_env.py         # FleetMidiEnvironment (via plugin pattern)
├── tests/
├── pyproject.toml           # Package metadata, optional dep on fleet-characters
└── README.md
```

### Stays in `fleet-characters`
```
fleet_characters/
├── __init__.py
├── stats.py
├── class_.py
├── arc.py
├── dream.py
├── agent_profile.py
└── signal/
```

## Refactoring Needed

### 1. Extract StatBridge Protocol (in `fleet_env/rubrics/base_stats.py`)
Create a protocol/interface for stat integration:
```python
from typing import Protocol


class StatName(Protocol):
    """Stat name enum that fleet-characters provides."""


class StatUpdater(Protocol):
    """Interface for stat update callbacks."""
    def grow(self, name: str, amount: float) -> None: ...
    def get(self, name: str) -> float: ...


class StatCallback(Protocol):
    """Mapping from rubric → what to grow."""
    def __call__(self, score: float, stats: StatUpdater) -> None: ...
```

### 2. Rewrite fleet_rubrics.py → Split into one file per rubric
Each rubric accepts a `stat_callback` parameter instead of importing `StatName` directly:
```python
class TernaryAccuracyRubric(Rubric):
    def __init__(self, stat_callback: Optional[StatCallback] = None, ...):
        self.stat_callback = stat_callback or default_stat_callbacks.TERNARY
```

### 3. Create fleet-characters → fleet-env adapter
In `fleet_characters` (or as an installable extra): register callbacks that use Stats:
```python
# fleet-characters/contrib/fleet_env_adapter.py
from fleet_env.rubrics.base_stats import StatCallback, StatUpdater
from fleet_characters.stats import Stats, StatName


class FleetStatsUpdater:
    def __init__(self, stats: Stats):
        self._stats = stats

    def grow(self, name: str, amount: float) -> None:
        self._stats.grow(StatName(name), amount)

    def get(self, name: str) -> float:
        return self._stats.get(StatName(name))
```

### 4. Decouple fleet_env.py from AgentCharacter
Replace the hard-coded `AgentCharacter` creation with a character factory plugin:
```python
# fleet_env.py
class CharacterPlugin(Protocol):
    def create(self, agent_name: str, domain: str, **kwargs) -> Any: ...
    def get_stats(self, character: Any) -> StatUpdater: ...


class FleetMidiEnvironment:
    def __init__(self, character_plugin: Optional[CharacterPlugin] = None, ...):
        self._character_plugin = character_plugin or NullCharacterPlugin()
```

### 5. Move auto_env's fleet-characters dep to plugin
The try/except ImportError in auto_env.py is fine as-is, or can use the same plugin pattern.

## Refactoring Order

| Step | What | Effort | Risk |
|------|------|--------|------|
| 1 | Extract `base_stats.py` protocol files | Small | None |
| 2 | Split `fleet_rubrics.py` into per-file rubrics with `stat_callback` | Medium | Low (no behavior change) |
| 3 | Create `fleet-characters/contrib/fleet_env_adapter.py` | Small | None |
| 4 | Refactor `fleet_env.py` CharacterPlugin | Medium | Low |
| 5 | Create `fleet-env` repo, copy files, set up pyproject.toml | Small | None |
| 6 | Replace symlink in fleet-characters with pip dependency | Small | Low (version pinning) |
| 7 | Update imports in agents that use fleet_env directly | Small | None |

## Future: fleet-midi-envs Meta-Package
```
fleet-midi-envs/          ← Thin meta-package
├── pyproject.toml        # Depends on: fleet-env, fleet-characters
└── src/fleet_midi_envs/
    ├── __init__.py       # Re-exports from both
    └── adapter.py        # Registers fleet-characters callbacks with fleet-env
```
This is what people install to get the full system. `fleet-env` alone for RL environments without character growth. `fleet-characters` alone for stats without environments.

## Summary

| Aspect | Current | After Split |
|--------|---------|-------------|
| fleet_characters depends on environment? | NO (env is symlinked, not imported) | NO |
| environment depends on fleet_characters? | YES (6 lazy runtime imports) | NO (via protocol/plugin) |
| Separate repos? | One monorepo | Two: fleet-env + fleet-characters |
| Integration point | Symlink | pip dependency + adapter plugin |
| Breaking changes? | None (backward-compat protocol) | None (same API) |
