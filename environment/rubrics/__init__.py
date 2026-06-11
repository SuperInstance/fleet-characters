"""
Rubric scoring system for fleet-midi agents — ported from OpenEnv.

Rubrics compute reward signals from agent actions/observations and update
the agent's character stats. The API is modeled after PyTorch's nn.Module:
implement forward(), and the framework handles child registration and hooks.

Exports:
    Rubric — Abstract base class (nn.Module-style)
    LLMJudge — LLM-as-a-judge rubric
    TernaryAccuracyRubric — ternary vector quality scoring
    ResponseTimeRubric — response speed scoring
    HarmonicConsonanceRubric — chord/scale quality scoring
    RhythmAccuracyRubric — groove/tempo quality scoring
    CompositeFleetRubric — aggregates multiple rubrics
"""

from .base import Rubric
from .llm_judge import LLMJudge
from .fleet_rubrics import (
    TernaryAccuracyRubric,
    ResponseTimeRubric,
    HarmonicConsonanceRubric,
    RhythmAccuracyRubric,
    CompositeFleetRubric,
    SuccessBonusRubric,
    CompositeRubric,
)

__all__ = [
    # Core
    "Rubric",
    # LLM judge
    "LLMJudge",
    # Fleet-specialized
    "TernaryAccuracyRubric",
    "ResponseTimeRubric",
    "HarmonicConsonanceRubric",
    "RhythmAccuracyRubric",
    "CompositeFleetRubric",
    # Backward-compatible
    "SuccessBonusRubric",
    "CompositeRubric",
]
