"""
Base Rubric class for reward computation — ported from OpenEnv.

Rubrics compute rewards from actions and observations. The API is modeled
after PyTorch's nn.Module: users implement forward(), and the framework
handles child registration and hooks.

This port extends the OpenEnv design with optional agent profile integration:
rubrics can update fleet-midi agent character stats based on scores.

Import via:
    from fleet_characters.environment.rubrics import Rubric
"""

import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Protocol,
    Tuple,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from fleet_characters.stats import Stats


class StatCallback(Protocol):
    """Protocol for stat update callbacks invoked after scoring.

    A rubric may use this to grow agent stats as a reward for good performance.
    """

    def __call__(self, stat_name: str, amount: float) -> None:
        ...


@dataclass
class RubricScore:
    """Result container returned by rubric scoring.

    Attributes:
        reward (`float`): The reward value (typically 0.0 to 1.0).
        metadata (`Dict[str, Any]`, *optional*): Additional diagnostic info.
    """

    reward: float
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Rubric(ABC):
    """Abstract base class for reward computation.

    A Rubric computes a reward signal from an action and observation.
    Subclasses implement forward() to define the reward logic.

    Child rubrics are auto-registered when assigned as attributes,
    enabling hierarchical composition and introspection.

    Extends the OpenEnv design with an optional ``agent_stats`` reference
    that rubrics can use to update character stats based on scores.

    Examples:

        ```python
        class MyRubric(Rubric):
            def forward(self, action, observation) -> float:
                return 1.0 if action.valid else 0.0

        rubric = MyRubric()
        reward = rubric(action, observation)
        ```
    """

    _rubric_children: Dict[str, "Rubric"]
    _forward_hooks: List[Callable]
    _forward_pre_hooks: List[Callable]
    last_score: Optional[float]

    # Maps stat names to cumulative growth per rubric instance
    _stat_growth: Dict[str, float]

    def __init__(self):
        # Use object.__setattr__ to avoid triggering __setattr__ during init
        object.__setattr__(self, "_rubric_children", {})
        object.__setattr__(self, "_forward_hooks", [])
        object.__setattr__(self, "_forward_pre_hooks", [])
        object.__setattr__(self, "last_score", None)
        object.__setattr__(self, "_stat_growth", {})

    def __setattr__(self, name: str, value: Any) -> None:
        # Auto-register child rubrics when assigned as attributes
        if isinstance(value, Rubric):
            self._rubric_children[name] = value
        object.__setattr__(self, name, value)

    def __call__(
        self,
        action: Any,
        observation: Any,
        agent_stats: Optional["Stats"] = None,
    ) -> float:
        """Evaluate the rubric with hooks.

        Args:
            action: The action taken by the agent.
            observation: The resulting observation.
            agent_stats: Optional Stats instance to update from the score.

        Returns:
            `float`: Reward value (typically 0.0 to 1.0).
        """
        # Check if forward method is async BEFORE calling it
        if inspect.iscoroutinefunction(self.forward):
            # Async path — pre-hooks will be called in _call_async
            result = self.forward(action, observation)
            return self._call_async(action, observation, result, agent_stats)
        else:
            # Sync path — call pre-hooks BEFORE forward()
            for hook in self._forward_pre_hooks:
                hook(self, action, observation)
            result = self.forward(action, observation)
            return self._call_sync(action, observation, result, agent_stats)

    def _call_sync(
        self,
        action: Any,
        observation: Any,
        result: float,
        agent_stats: Optional["Stats"] = None,
    ) -> float:
        """Synchronous call path."""
        self.last_score = result

        # Update agent stats from the score
        if agent_stats is not None:
            self._apply_stat_growth(result, agent_stats)

        # Post-forward hooks
        for hook in self._forward_hooks:
            hook(self, action, observation, result)

        return result

    async def _call_async(
        self,
        action: Any,
        observation: Any,
        result_coro,
        agent_stats: Optional["Stats"] = None,
    ) -> float:
        """Asynchronous call path."""
        # Pre-forward hooks
        for hook in self._forward_pre_hooks:
            if inspect.iscoroutinefunction(hook):
                await hook(self, action, observation)
            else:
                hook(self, action, observation)

        # Await the forward result
        result = await result_coro
        self.last_score = result

        # Update agent stats from the score
        if agent_stats is not None:
            self._apply_stat_growth(result, agent_stats)

        # Post-forward hooks
        for hook in self._forward_hooks:
            if inspect.iscoroutinefunction(hook):
                await hook(self, action, observation, result)
            else:
                hook(self, action, observation, result)

        return result

    @abstractmethod
    def forward(self, action: Any, observation: Any) -> float:
        """Compute the reward. Implement this in subclasses.

        Args:
            action: The action taken by the agent.
            observation: The resulting observation.

        Returns:
            `float`: Reward value (typically 0.0 to 1.0).
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Stat integration
    # ------------------------------------------------------------------

    def _apply_stat_growth(self, score: float, stats: "Stats") -> None:
        """Apply stat growth based on score. Override in subclasses.

        Called automatically by __call__ when ``agent_stats`` is provided.

        Args:
            score: The computed reward (0.0-1.0).
            stats: The agent's Stats instance to update.
        """
        pass

    def _record_growth(self, stat_name: str, amount: float) -> None:
        """Track cumulative growth for a stat across calls.

        Args:
            stat_name: Name of the stat (e.g., ``"intelligence"``).
            amount: Amount of growth applied.
        """
        self._stat_growth[stat_name] = (
            self._stat_growth.get(stat_name, 0.0) + amount
        )

    def stat_growth(self) -> Dict[str, float]:
        """Get cumulative stat growth from this rubric.

        Returns:
            `Dict[str, float]`: Mapping of stat names to total growth amounts.
        """
        return dict(self._stat_growth)

    def reset_stat_growth(self) -> None:
        """Reset cumulative stat growth tracking."""
        self._stat_growth.clear()

    # ------------------------------------------------------------------
    # Hooks
    # ------------------------------------------------------------------

    def register_forward_hook(
        self, hook: Callable[["Rubric", Any, Any, float], None]
    ) -> None:
        """Register a hook called after forward().

        Args:
            hook (`Callable`):
                Callable with signature (rubric, action, observation, result).
        """
        self._forward_hooks.append(hook)

    def register_forward_pre_hook(
        self, hook: Callable[["Rubric", Any, Any], None]
    ) -> None:
        """Register a hook called before forward().

        Args:
            hook (`Callable`):
                Callable with signature (rubric, action, observation).
        """
        self._forward_pre_hooks.append(hook)

    # ------------------------------------------------------------------
    # Child / tree introspection
    # ------------------------------------------------------------------

    def children(self) -> Iterator["Rubric"]:
        """Iterate over immediate child rubrics."""
        yield from self._rubric_children.values()

    def named_children(self) -> Iterator[Tuple[str, "Rubric"]]:
        """Iterate over immediate child rubrics with names."""
        yield from self._rubric_children.items()

    def rubrics(self) -> Iterator["Rubric"]:
        """Iterate over all descendant rubrics (depth-first)."""
        for child in self._rubric_children.values():
            yield child
            yield from child.rubrics()

    def named_rubrics(self, prefix: str = "") -> Iterator[Tuple[str, "Rubric"]]:
        """Iterate over all descendant rubrics with dot-separated names."""
        for name, child in self._rubric_children.items():
            full_name = f"{prefix}.{name}" if prefix else name
            yield full_name, child
            yield from child.named_rubrics(full_name)

    def get_rubric(self, path: str) -> "Rubric":
        """Access a nested rubric by dot-separated path.

        Args:
            path (`str`): Dot-separated path (e.g., ``"accuracy.ternary"``).

        Returns:
            `Rubric`: The rubric at the specified path.

        Raises:
            KeyError: If the path does not exist.
        """
        parts = path.split(".")
        current = self
        for part in parts:
            if part not in current._rubric_children:
                raise KeyError(f"Rubric path not found: {path}")
            current = current._rubric_children[part]
        return current

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def score(
        self,
        action: Any,
        observation: Any,
        previous_observation: Optional[Any] = None,
    ) -> float:
        """Score alias for backward compatibility with environment code.

        Delegates to ``__call__(action, observation)``.
        Some environments pass ``previous_observation`` as context;
        subclasses may override this method to use it.

        Args:
            action: The action taken by the agent.
            observation: The resulting observation.
            previous_observation: Optional previous observation for context.

        Returns:
            `float`: Reward value (typically 0.0 to 1.0).
        """
        return self(action, observation)

    def reset(self) -> None:
        """Reset any internal state. Override in subclasses if needed."""
        self.last_score = None
        self._stat_growth.clear()

    def state_dict(self) -> Dict[str, Any]:
        """Serialize rubric configuration for checkpointing."""
        return {
            "last_score": self.last_score,
            "stat_growth": dict(self._stat_growth),
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Load rubric configuration from checkpoint."""
        if "last_score" in state:
            object.__setattr__(self, "last_score", state["last_score"])
        if "stat_growth" in state:
            object.__setattr__(self, "_stat_growth", dict(state["stat_growth"]))
