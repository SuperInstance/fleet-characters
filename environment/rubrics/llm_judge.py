"""
LLM-as-a-judge rubric for reward computation — ported from OpenEnv.

Uses an LLM endpoint (via an async LLMClient protocol) to evaluate agent
actions/observations and produce a numeric score.

Examples:

    ```python
    client = OpenAIClient("http://localhost", 8000, model="meta-llama/...")
    judge = LLMJudge(
        prompt_template="Rate this solution:\\n{action}\\n\\nScore (0-1):",
        client=client,
    )
    score = await judge(action, observation)
    ```
"""

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .base import Rubric


class LLMClient(ABC):
    """Abstract LLM client that rubrics depend on.

    Provides a minimal interface for making async LLM completion calls.
    Implementations wrap OpenAI, vLLM, Anthropic, etc.
    """

    @abstractmethod
    async def complete(self, prompt: str) -> str:
        """Send a completion prompt and return the response text.

        Args:
            prompt: The full prompt string to send.

        Returns:
            `str`: The model's response text.
        """
        ...


class LLMJudge(Rubric):
    """Rubric that uses an LLM to evaluate agent actions/observations.

    The prompt template is formatted with ``{action}`` and ``{observation}``
    placeholders. The LLM response is parsed for a numeric score.

    Args:
        prompt_template (`str`):
            Template string with ``{action}`` and ``{observation}`` placeholders.
        client (`LLMClient`):
            An LLMClient-compatible instance for making LLM calls.
        score_pattern (`str`, *optional*):
            Regex to extract the score from the LLM response.
            Defaults to matching the first decimal number.
        default_score (`float`, *optional*, defaults to ``0.0``):
            Score returned when parsing fails.
        normalize (`bool`, *optional*, defaults to ``True``):
            If True, clamp extracted score to ``[0, 1]``.
        stat_growth_scale (`float`, *optional*, defaults to ``0.3``):
            Amount of stat growth to apply per successful high score.
    """

    def __init__(
        self,
        prompt_template: str,
        client: LLMClient,
        *,
        score_pattern: Optional[str] = None,
        default_score: float = 0.0,
        normalize: bool = True,
        stat_growth_scale: float = 0.3,
    ):
        super().__init__()
        self.prompt_template = prompt_template
        self._client = client
        self._score_pattern = re.compile(score_pattern or r"(\d+\.?\d*)")
        self.default_score = default_score
        self.normalize = normalize
        self.stat_growth_scale = stat_growth_scale

    async def forward(self, action: Any, observation: Any) -> float:
        """Evaluate by sending a prompt to the LLM and parsing the score.

        Args:
            action: The action taken by the agent.
            observation: The resulting observation.

        Returns:
            `float`: Parsed score from the LLM response (0.0-1.0).
        """
        prompt = self._render_prompt(action, observation)
        response = await self._client.complete(prompt)
        return self._parse_score(response)

    def _render_prompt(self, action: Any, observation: Any) -> str:
        """Format the prompt template with action and observation.

        Override in subclasses for custom prompt construction.
        """
        return self.prompt_template.format(action=action, observation=observation)

    def _parse_score(self, response: str) -> float:
        """Extract a numeric score from the LLM response.

        Uses the configured regex pattern to find the first match.
        Returns ``default_score`` if no match is found.

        Args:
            response: Raw LLM response text.

        Returns:
            `float`: Extracted and optionally normalized score.
        """
        match = self._score_pattern.search(response)
        if match is None:
            return self.default_score
        try:
            # Use first capture group if present, otherwise full match
            text = match.group(1) if match.lastindex else match.group(0)
            score = float(text)
        except (ValueError, IndexError):
            return self.default_score
        if self.normalize:
            score = max(0.0, min(1.0, score))
        return score

    # ------------------------------------------------------------------
    # Stat updates
    # ------------------------------------------------------------------

    def _apply_stat_growth(self, score: float, stats: "Stats") -> None:
        """Apply charisma growth based on LLM-judged quality score."""
        from fleet_characters.stats import StatName

        growth = score * self.stat_growth_scale
        if growth > 0:
            stats.grow(StatName.CHARISMA, growth)
            self._record_growth("charisma", growth)

    # ------------------------------------------------------------------
    # State serialization
    # ------------------------------------------------------------------

    def state_dict(self) -> Dict[str, Any]:
        """Serialize rubric configuration for checkpointing."""
        return {
            **super().state_dict(),
            "prompt_template": self.prompt_template,
            "score_pattern": self._score_pattern.pattern,
            "default_score": self.default_score,
            "normalize": self.normalize,
            "stat_growth_scale": self.stat_growth_scale,
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Load rubric configuration from checkpoint."""
        super().load_state_dict(state)
        if "prompt_template" in state:
            self.prompt_template = state["prompt_template"]
        if "score_pattern" in state:
            self._score_pattern = re.compile(state["score_pattern"])
        if "default_score" in state:
            self.default_score = state["default_score"]
        if "normalize" in state:
            self.normalize = state["normalize"]
        if "stat_growth_scale" in state:
            self.stat_growth_scale = state["stat_growth_scale"]
