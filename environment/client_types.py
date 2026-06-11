#!/usr/bin/env python3
"""
Ported from OpenEnv's client_types.py — type definitions for environment interactions.
"""

from dataclasses import dataclass
from typing import Generic, Optional, TypeVar


# Generic type for observations
ObsT = TypeVar("ObsT")
StateT = TypeVar("StateT")


@dataclass
class StepResult(Generic[ObsT]):
    """
    Ported from OpenEnv StepResult — represents the result of one environment step.

    Attributes:
        observation:
            The environment's observation after the action.
        reward (`float`, *optional*):
            Scalar reward for this step.
        done (`bool`, *optional*, defaults to `False`):
            Whether the episode is finished.
    """

    observation: ObsT
    reward: Optional[float] = None
    done: bool = False


@dataclass
class EnvironmentState(Generic[StateT]):
    """
    Internal state of an environment.
    """
    state: StateT
    metadata: dict[any, any]
