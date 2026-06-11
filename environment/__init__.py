"""
fleet-characters environment system — refactored from HuggingFace OpenEnv.

Provides Gymnasium-style async/sync environments for agent training,
rubric-based scoring, auto-discovery, and agent world model integration.

Pattern:
1. Environment provides reset()/step()/observe() interface
2. Rubrics compute reward from action/observations
3. AutoEnv discovers environment types
4. Character system tracks stats from training cycles
"""

# Core types
from .client_types import StepResult, ObsT, StateT
from .env_client import (EnvClient, GenericEnvClient, SyncWrapper, WebSocketTransport,
                          AgentResponse, CueObservation, CueRequest,
                          compute_reward, compute_reward_simple, make_env)
from .rubrics import Rubric, LLMJudge, SuccessBonusRubric, CompositeRubric
from .auto import AutoEnv
from .fleet_env import FleetMidiEnvironment

__all__ = [
    # Types
    'StepResult', 'ObsT', 'StateT',
    # Core clients
    'EnvClient', 'GenericEnvClient', 'SyncWrapper',
    # Transport
    'WebSocketTransport',
    # Domain types
    'AgentResponse', 'CueObservation', 'CueRequest',
    # Reward utils
    'compute_reward', 'compute_reward_simple',
    # Factory
    'make_env',
    # Rubrics
    'Rubric', 'LLMJudge', 'SuccessBonusRubric', 'CompositeRubric',
    # Auto discovery
    'AutoEnv',
    # Fleet-specific
    'FleetMidiEnvironment',
]
