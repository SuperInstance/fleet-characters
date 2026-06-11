"""
Specialized rubrics for fleet-midi agent scoring.

Each rubric returns a float reward (0.0-1.0) and optionally updates the
agent's character stats via the ``_apply_stat_growth`` hook.

Rubrics:
    - TernaryAccuracyRubric — ternary vector quality → intelligence
    - ResponseTimeRubric — execution speed → dexterity
    - HarmonicConsonanceRubric — chord/scale quality → charisma
    - RhythmAccuracyRubric — groove/tempo quality → perception
    - CompositeFleetRubric — weighted aggregate of child rubrics
"""

import math
import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .base import Rubric


# ======================================================================
# Data containers for rubric inputs
# ======================================================================


@dataclass
class TernaryVector:
    """A ternary vector representing musical intent.

    Each element is -1 (negative/down), 0 (neutral/rest), or +1 (positive/up).
    Common in fleet-midi agents for encoding chord movements, velocity deltas,
    or expression contours.

    Attributes:
        data (List[int]):
            The ternary values. Each element should be -1, 0, or +1.
        target (List[int], *optional*):
            Ground-truth target vector for accuracy comparison.
    """

    data: List[int]
    target: Optional[List[int]] = None

    def __post_init__(self):
        # Clamp values to ternary range
        self.data = [max(-1, min(1, v)) for v in self.data]
        if self.target is not None:
            self.target = [max(-1, min(1, v)) for v in self.target]

    @property
    def magnitude(self) -> float:
        """L2 norm of the vector (sqrt of sum of squares)."""
        return math.sqrt(sum(v * v for v in self.data))

    @property
    def sparsity(self) -> float:
        """Fraction of non-zero elements (0.0 = all zeros, 1.0 = all ±1)."""
        if not self.data:
            return 0.0
        return sum(1 for v in self.data if v != 0) / len(self.data)

    @property
    def balance(self) -> float:
        """Balance of -1 vs +1 (0.0 = perfect balance, 1.0 = all one sign)."""
        pos = sum(1 for v in self.data if v > 0)
        neg = sum(1 for v in self.data if v < 0)
        total = pos + neg
        if total == 0:
            return 0.5  # neutral when no non-zero elements
        return abs(pos - neg) / total


@dataclass
class HarmonicAction:
    """A harmonic action — chord, scale, or voice leading event.

    Attributes:
        intervals (List[int]): Pitch intervals in semitones (e.g., [0, 4, 7] for C major).
        root (int, *optional*): Root pitch class (0 = C, 1 = C#, etc.).
        scale_degrees (List[int], *optional*): Expected scale degrees.
        chord_type (str, *optional*): e.g. ``"major"``, ``"minor"``, ``"dim7"``.
    """

    intervals: List[int]
    root: Optional[int] = None
    scale_degrees: Optional[List[int]] = None
    chord_type: Optional[str] = None


@dataclass
class RhythmAction:
    """A rhythm/groove action.

    Attributes:
        timestamps (List[float]): Onset times in beats.
        velocities (List[float], *optional*): Velocity values per hit (0.0-1.0).
        target_timestamps (List[float], *optional*): Expected reference timestamps.
        bpm (float, *optional*): Beats per minute for tempo context.
        swing_ratio (float, *optional*): Swing feel (0.5 = straight, >0.5 = swung).
    """

    timestamps: List[float]
    velocities: Optional[List[float]] = None
    target_timestamps: Optional[List[float]] = None
    bpm: Optional[float] = None
    swing_ratio: Optional[float] = None


# ======================================================================
# TernaryAccuracyRubric
# ======================================================================


class TernaryAccuracyRubric(Rubric):
    """Scores the quality of a ternary vector output.

    Evaluates:
        - Match accuracy when a target is available (``target`` in action).
        - Sparsity quality (not too sparse, not too dense).
        - Magnitude distribution (uniformity of -1/0/+1 usage).
        - Balance between positive and negative values.

    Intended stat growth: **intelligence** — higher scores reward better
    knowledge representation.

    Args:
        target_weight (`float`, *optional*, defaults to ``0.6``):
            Weight for target-vector accuracy.
        sparsity_weight (`float`, *optional*, defaults to ``0.2``):
            Weight for sparsity quality.
        balance_weight (`float`, *optional*, defaults to ``0.2``):
            Weight for sign balance.
        ideal_sparsity (`float`, *optional*, defaults to ``0.5``):
            Target sparsity fraction (deviation lowers score).
        stat_growth_scale (`float`, *optional*, defaults to ``0.5``):
            Amount of stat growth per unit score.
    """

    def __init__(
        self,
        target_weight: float = 0.6,
        sparsity_weight: float = 0.2,
        balance_weight: float = 0.2,
        ideal_sparsity: float = 0.5,
        stat_growth_scale: float = 0.5,
    ):
        super().__init__()
        self.target_weight = target_weight
        self.sparsity_weight = sparsity_weight
        self.balance_weight = balance_weight
        self.ideal_sparsity = ideal_sparsity
        self.stat_growth_scale = stat_growth_scale

    def forward(self, action: Any, observation: Any) -> float:
        """Score the ternary vector quality.

        Accepts:
            - ``action`` as a ``TernaryVector`` instance.
            - ``action`` as a bare list of ints.
            - ``observation`` containing a ``"ternary_vector"`` or ``"vector"`` key.

        Returns:
            `float`: Score in ``[0.0, 1.0]``.
        """
        vec = self._extract_vector(action, observation)
        if vec is None:
            return 0.0

        scores = []

        # 1. Target accuracy
        if vec.target is not None:
            acc = self._target_accuracy(vec.data, vec.target)
            scores.append(acc * self.target_weight)

        # 2. Sparsity quality
        sp = vec.sparsity
        dev = abs(sp - self.ideal_sparsity)
        sp_score = max(0.0, 1.0 - dev * 2.0)  # linear falloff
        scores.append(sp_score * self.sparsity_weight)

        # 3. Balance score
        bal = vec.balance
        bal_score = 1.0 - bal  # 0.0 = balanced → 1.0 score
        scores.append(bal_score * self.balance_weight)

        if not scores:
            # No target available — score based on structure alone
            scores.append(sp_score * 0.5)
            scores.append(bal_score * 0.5)

        return min(1.0, sum(scores))

    # ------------------------------------------------------------------
    # Stat: intelligence grows with better ternary quality
    # ------------------------------------------------------------------

    def _apply_stat_growth(self, score: float, stats: "Stats") -> None:
        from fleet_characters.stats import StatName

        growth = score * self.stat_growth_scale
        if growth > 0:
            stats.grow(StatName.INTELLIGENCE, growth)
            self._record_growth("intelligence", growth)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_vector(
        action: Any,
        observation: Any,
    ) -> Optional["TernaryVector"]:
        """Extract a TernaryVector from action/observation in various formats."""
        # Direct TernaryVector
        if isinstance(action, TernaryVector):
            return action

        # Bare list
        if isinstance(action, list):
            return TernaryVector(data=action)

        # Dict with known keys
        if isinstance(action, dict):
            if "ternary_vector" in action:
                data = action["ternary_vector"]
                target = action.get("target")
                return TernaryVector(data=data, target=target)
            if "vector" in action:
                data = action["vector"]
                target = action.get("target")
                return TernaryVector(data=data, target=target)

        # Check observation for relevant field
        if isinstance(observation, dict):
            if "ternary_vector" in observation:
                return TernaryVector(data=observation["ternary_vector"])
            if "vector" in observation:
                return TernaryVector(data=observation["vector"])

        return None

    @staticmethod
    def _target_accuracy(
        actual: List[int],
        target: List[int],
    ) -> float:
        """Compute element-wise match accuracy between two ternary vectors.

        Returns 0.0 if lengths differ or no matches.
        """
        if not actual or not target:
            return 0.0
        n = min(len(actual), len(target))
        if n == 0:
            return 0.0
        matches = sum(1 for i in range(n) if actual[i] == target[i])
        return matches / n

    def state_dict(self) -> Dict[str, Any]:
        return {
            **super().state_dict(),
            "target_weight": self.target_weight,
            "sparsity_weight": self.sparsity_weight,
            "balance_weight": self.balance_weight,
            "ideal_sparsity": self.ideal_sparsity,
            "stat_growth_scale": self.stat_growth_scale,
        }


# ======================================================================
# ResponseTimeRubric
# ======================================================================


class ResponseTimeRubric(Rubric):
    """Scores agent response speed.

    Faster responses yield higher scores with diminishing returns below a
    threshold. This rubric is designed to reward improvements in execution
    speed that reflect real agent growth.

    Intended stat growth: **dexterity** — faster agents gain more.

    Args:
        perfect_ms (`float`, *optional*, defaults to ``50.0``):
            Response times at or below this get a perfect 1.0 score.
        half_ms (`float`, *optional*, defaults to ``200.0``):
            Response time at which score is 0.5.
        zero_ms (`float`, *optional*, defaults to ``1000.0``):
            Response times at or above this get 0.0.
        stat_growth_scale (`float`, *optional*, defaults to ``0.4``):
            Amount of stat growth per unit score.
    """

    def __init__(
        self,
        perfect_ms: float = 50.0,
        half_ms: float = 200.0,
        zero_ms: float = 1000.0,
        stat_growth_scale: float = 0.4,
    ):
        super().__init__()
        self.perfect_ms = perfect_ms
        self.half_ms = half_ms
        self.zero_ms = zero_ms
        self.stat_growth_scale = stat_growth_scale

    def forward(self, action: Any, observation: Any) -> float:
        """Score based on response time.

        Extracts ``response_time_ms`` from:
            - ``action`` dict key ``"response_time_ms"``
            - ``observation`` dict key ``"response_time_ms"``
            - A bare number as ``action``

        Returns:
            `float`: Score in ``[0.0, 1.0]``.
        """
        rt = self._extract_response_time_ms(action, observation)
        if rt is None:
            return 0.5  # neutral when no timing data

        return self._score_from_ms(rt)

    def _apply_stat_growth(self, score: float, stats: "Stats") -> None:
        from fleet_characters.stats import StatName

        growth = score * self.stat_growth_scale
        if growth > 0:
            stats.grow(StatName.DEXTERITY, growth)
            self._record_growth("dexterity", growth)

    @staticmethod
    def _extract_response_time_ms(
        action: Any,
        observation: Any,
    ) -> Optional[float]:
        """Extract response time in ms from various formats."""
        # Direct number
        if isinstance(action, (int, float)):
            return float(action)

        # Dict key
        if isinstance(action, dict):
            rt = action.get("response_time_ms") or action.get("response_ms")
            if rt is not None:
                return float(rt)

        if isinstance(observation, dict):
            rt = observation.get("response_time_ms") or observation.get("response_ms")
            if rt is not None:
                return float(rt)

        return None

    def _score_from_ms(self, ms: float) -> float:
        """Map a response time in ms to a 0.0-1.0 score using an S-curve."""
        if ms <= self.perfect_ms:
            return 1.0
        if ms >= self.zero_ms:
            return 0.0

        # Exponential decay between thresholds
        t = (ms - self.perfect_ms) / (self.half_ms - self.perfect_ms)
        # S-curve: 1 / (1 + t^2) gives smooth falloff
        # At t=0: score=1.0; at t=1 (half_ms): score=0.5
        score = 1.0 / (1.0 + t * t)
        return max(0.0, min(1.0, score))

    def state_dict(self) -> Dict[str, Any]:
        return {
            **super().state_dict(),
            "perfect_ms": self.perfect_ms,
            "half_ms": self.half_ms,
            "zero_ms": self.zero_ms,
            "stat_growth_scale": self.stat_growth_scale,
        }


# ======================================================================
# HarmonicConsonanceRubric
# ======================================================================


class HarmonicConsonanceRubric(Rubric):
    """Scores the quality of a harmonic action (chord, scale, voice leading).

    Evaluates:
        - Interval consonance: how consonant the intervals are (P1, P5, M3 > m3, m7 > b2, TT).
        - Scale/resolution fit: how well the chord fits expected scale degrees.
        - Voice leading smoothness (reward small interval movements).

    Intended stat growth: **charisma** — harmonic quality reflects output richness.

    Args:
        interval_weight (`float`, *optional*, defaults to ``0.5``):
            Weight for raw interval consonance.
        scale_weight (`float`, *optional*, defaults to ``0.3``):
            Weight for scale-degree fit.
        voice_leading_weight (`float`, *optional*, defaults to ``0.2``):
            Weight for smooth voice leading.
        stat_growth_scale (`float`, *optional*, defaults to ``0.4``):
            Amount of stat growth per unit score.
    """

    # Consonance ratings per interval class (0-11 semitones)
    # Higher = more consonant. Full list for all 12 interval classes.
    INTERVAL_CONSONANCE: Dict[int, float] = {
        0: 1.0,   # unison / octave
        1: 0.1,   # minor second
        2: 0.3,   # major second
        3: 0.5,   # minor third
        4: 0.8,   # major third
        5: 0.9,   # perfect fourth
        6: 0.1,   # tritone
        7: 0.9,   # perfect fifth
        8: 0.5,   # minor sixth
        9: 0.8,   # major sixth
        10: 0.3,  # minor seventh
        11: 0.2,  # major seventh
    }

    # Scale-degree appropriateness (0 = root, 4 = fifth, etc.)
    SCALE_CONSONANCE: Dict[int, float] = {
        0: 1.0,   # root — perfect
        1: 0.4,   # b9 — tense
        2: 0.7,   # 9th — colorful
        3: 0.5,   # minor 3rd (blues)
        4: 0.9,   # major 3rd — strong
        5: 0.8,   # perfect 4th — strong
        6: 0.2,   # #11 / b5 — spicy
        7: 0.9,   # perfect 5th — strong
        8: 0.3,   # #5 / b13 — tense
        9: 0.7,   # 13th — lush
        10: 0.5,  # minor 7th — relaxed
        11: 0.4,  # major 7th — dreamy
    }

    def __init__(
        self,
        interval_weight: float = 0.5,
        scale_weight: float = 0.3,
        voice_leading_weight: float = 0.2,
        stat_growth_scale: float = 0.4,
    ):
        super().__init__()
        self.interval_weight = interval_weight
        self.scale_weight = scale_weight
        self.voice_leading_weight = voice_leading_weight
        self.stat_growth_scale = stat_growth_scale
        # Track previous intervals for voice leading smoothness
        self._prev_intervals: Optional[List[int]] = None

    def forward(self, action: Any, observation: Any) -> float:
        """Score harmonic quality.

        Accepts:
            - ``action`` as a ``HarmonicAction`` instance.
            - ``action`` dict with ``"intervals"`` key (optional root/scale_degrees).

        Returns:
            `float`: Score in ``[0.0, 1.0]``.
        """
        harmonic = self._extract_harmonic(action, observation)
        if harmonic is None or not harmonic.intervals:
            return 0.0

        scores = []

        # 1. Raw interval consonance
        cons_score = self._interval_consonance_score(harmonic.intervals)
        scores.append(cons_score * self.interval_weight)

        # 2. Scale degree fit
        if harmonic.scale_degrees:
            scale_score = self._scale_fit_score(
                harmonic.intervals, harmonic.scale_degrees
            )
            scores.append(scale_score * self.scale_weight)

        # 3. Voice leading smoothness (requires previous state)
        if self._prev_intervals is not None and len(self._prev_intervals) > 0:
            vl_score = self._voice_leading_score(
                self._prev_intervals, harmonic.intervals
            )
            scores.append(vl_score * self.voice_leading_weight)

        # Save for next call
        self._prev_intervals = list(harmonic.intervals)

        if not scores:
            return 0.5

        return min(1.0, sum(scores))

    def _apply_stat_growth(self, score: float, stats: "Stats") -> None:
        from fleet_characters.stats import StatName

        growth = score * self.stat_growth_scale
        if growth > 0:
            stats.grow(StatName.CHARISMA, growth)
            self._record_growth("charisma", growth)

    @staticmethod
    def _extract_harmonic(
        action: Any,
        observation: Any,
    ) -> Optional[HarmonicAction]:
        """Extract a HarmonicAction from various input formats."""
        if isinstance(action, HarmonicAction):
            return action

        if isinstance(action, dict):
            intervals = action.get("intervals")
            if intervals is not None:
                return HarmonicAction(
                    intervals=intervals,
                    root=action.get("root"),
                    scale_degrees=action.get("scale_degrees"),
                    chord_type=action.get("chord_type"),
                )

        if isinstance(observation, dict):
            intervals = observation.get("intervals")
            if intervals is not None:
                return HarmonicAction(intervals=intervals)

        return None

    def _interval_consonance_score(self, intervals: List[int]) -> float:
        """Compute average consonance of all intervals against root."""
        if not intervals:
            return 0.0

        # Only count intervals relative to root (skip unison)
        non_root = [abs(i % 12) for i in intervals if i % 12 != 0]
        if not non_root:
            return 1.0  # single note is perfectly consonant

        scores = [self.INTERVAL_CONSONANCE.get(i % 12, 0.3) for i in non_root]
        return statistics.mean(scores)

    def _scale_fit_score(
        self,
        intervals: List[int],
        scale_degrees: List[int],
    ) -> float:
        """Score how well chord intervals fit given scale degrees."""
        if not intervals or not scale_degrees:
            return 0.5

        pairs = zip(intervals, scale_degrees)
        scores = []
        for interval, degree in pairs:
            # Map interval to its scale degree position
            deg_class = degree % 12
            score = self.SCALE_CONSONANCE.get(deg_class, 0.5)
            scores.append(score)

        return statistics.mean(scores) if scores else 0.5

    @staticmethod
    def _voice_leading_score(
        prev: List[int],
        curr: List[int],
    ) -> float:
        """Score voice leading smoothness.

        Smaller interval movements = higher score. Reward common-tone
        retention and stepwise motion.
        """
        if not prev or not curr:
            return 0.5

        n = min(len(prev), len(curr))
        if n == 0:
            return 0.5

        total_motion = 0.0
        for i in range(n):
            motion = abs(curr[i] - prev[i])
            # Normalize: 0 semitones → 1.0, 12+ semitones → 0.0
            voice_score = max(0.0, 1.0 - motion / 12.0)
            total_motion += voice_score

        return total_motion / n

    def reset(self) -> None:
        super().reset()
        self._prev_intervals = None

    def state_dict(self) -> Dict[str, Any]:
        return {
            **super().state_dict(),
            "interval_weight": self.interval_weight,
            "scale_weight": self.scale_weight,
            "voice_leading_weight": self.voice_leading_weight,
            "stat_growth_scale": self.stat_growth_scale,
            "prev_intervals": self._prev_intervals,
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        super().load_state_dict(state)
        self._prev_intervals = state.get("prev_intervals")


# ======================================================================
# RhythmAccuracyRubric
# ======================================================================


class RhythmAccuracyRubric(Rubric):
    """Scores rhythm/groove quality.

    Evaluates:
        - Onset accuracy: deviation from target timestamps.
        - Groove consistency: inter-onset interval (IOI) regularity.
        - Velocity expression: dynamic range and articulation contrast.
        - Swing feel, when applicable.

    Intended stat growth: **perception** — tight rhythm requires good intent
    extraction (feeling the pulse).

    Args:
        onset_weight (`float`, *optional*, defaults to ``0.5``):
            Weight for onset timing accuracy.
        groove_weight (`float`, *optional*, defaults to ``0.3``):
            Weight for groove/IOI consistency.
        velocity_weight (`float`, *optional*, defaults to ``0.2``):
            Weight for velocity expression quality.
        max_offset_beats (`float`, *optional*, defaults to ``0.5``):
            Onset offset beyond which score is 0 for that hit.
        stat_growth_scale (`float`, *optional*, defaults to ``0.4``):
            Amount of stat growth per unit score.
    """

    def __init__(
        self,
        onset_weight: float = 0.5,
        groove_weight: float = 0.3,
        velocity_weight: float = 0.2,
        max_offset_beats: float = 0.5,
        stat_growth_scale: float = 0.4,
    ):
        super().__init__()
        self.onset_weight = onset_weight
        self.groove_weight = groove_weight
        self.velocity_weight = velocity_weight
        self.max_offset_beats = max_offset_beats
        self.stat_growth_scale = stat_growth_scale

    def forward(self, action: Any, observation: Any) -> float:
        """Score rhythm quality.

        Accepts:
            - ``action`` as a ``RhythmAction`` instance.
            - ``action`` dict with ``"timestamps"`` key.

        Returns:
            `float`: Score in ``[0.0, 1.0]``.
        """
        rhythm = self._extract_rhythm(action, observation)
        if rhythm is None or len(rhythm.timestamps) < 2:
            return 0.5  # Neutral for insufficient data

        scores = []

        # 1. Onset accuracy (requires targets)
        if rhythm.target_timestamps is not None:
            onset_score = self._onset_accuracy(
                rhythm.timestamps, rhythm.target_timestamps
            )
            scores.append(onset_score * self.onset_weight)

        # 2. Groove consistency (IOI regularity)
        groove_score = self._groove_consistency(rhythm.timestamps)
        scores.append(groove_score * self.groove_weight)

        # 3. Velocity expression
        if rhythm.velocities is not None and len(rhythm.velocities) > 1:
            vel_score = self._velocity_expression(rhythm.velocities)
            scores.append(vel_score * self.velocity_weight)

        if not scores:
            return groove_score

        return min(1.0, sum(scores))

    def _apply_stat_growth(self, score: float, stats: "Stats") -> None:
        from fleet_characters.stats import StatName

        growth = score * self.stat_growth_scale
        if growth > 0:
            stats.grow(StatName.PERCEPTION, growth)
            self._record_growth("perception", growth)

    @staticmethod
    def _extract_rhythm(
        action: Any,
        observation: Any,
    ) -> Optional[RhythmAction]:
        """Extract a RhythmAction from various input formats."""
        if isinstance(action, RhythmAction):
            return action

        if isinstance(action, dict):
            timestamps = action.get("timestamps")
            if timestamps is not None:
                return RhythmAction(
                    timestamps=timestamps,
                    velocities=action.get("velocities"),
                    target_timestamps=action.get("target_timestamps"),
                    bpm=action.get("bpm"),
                    swing_ratio=action.get("swing_ratio"),
                )

        if isinstance(observation, dict):
            timestamps = observation.get("timestamps")
            if timestamps is not None:
                return RhythmAction(timestamps=timestamps)

        return None

    @staticmethod
    def _onset_accuracy(
        timestamps: List[float],
        targets: List[float],
    ) -> float:
        """Score precision of onset timing vs target grid.

        Computes average offset against targets, normalized to [0, 1].
        """
        if not timestamps or not targets:
            return 0.0

        n = min(len(timestamps), len(targets))
        if n == 0:
            return 0.0

        total_score = 0.0
        for i in range(n):
            offset = abs(timestamps[i] - targets[i])
            # Gaussian-ish scoring: exp(-(offset * 4)^2)
            # At offset=0: score=1.0; at offset=0.5: score≈0.14
            score = math.exp(-((offset * 4) ** 2))
            total_score += score

        return total_score / n

    @staticmethod
    def _groove_consistency(timestamps: List[float]) -> float:
        """Score groove consistency from inter-onset intervals (IOIs).

        Low variance in IOIs = steady groove = higher score.
        """
        if len(timestamps) < 3:
            return 0.5

        iois = [
            timestamps[i + 1] - timestamps[i]
            for i in range(len(timestamps) - 1)
        ]
        if not iois:
            return 0.5

        mean_ioi = statistics.mean(iois)
        if mean_ioi == 0:
            return 0.0

        # Coefficient of variation (lower = more consistent)
        cv = statistics.stdev(iois) / mean_ioi
        # Normalize: cv=0 → 1.0, cv=0.5 → ~0.5, cv=1.0 → ~0.2
        return math.exp(-2.0 * cv)

    @staticmethod
    def _velocity_expression(velocities: List[float]) -> float:
        """Score velocity expression — dynamic range and variation.

        Rewards:
        - Good dynamic range (not all same velocity)
        - Articulation contrast (some accents)
        """
        if not velocities or len(velocities) < 2:
            return 0.5

        v_min, v_max = min(velocities), max(velocities)

        # Dynamic range score
        range_score = min(1.0, (v_max - v_min) * 2.0)

        # Variation score — entropy-like, higher is more expressive
        mean_v = statistics.mean(velocities)
        var_v = statistics.variance(velocities) if len(velocities) > 1 else 0.0
        var_score = min(1.0, var_v * 4.0)

        return 0.6 * range_score + 0.4 * var_score

    def state_dict(self) -> Dict[str, Any]:
        return {
            **super().state_dict(),
            "onset_weight": self.onset_weight,
            "groove_weight": self.groove_weight,
            "velocity_weight": self.velocity_weight,
            "max_offset_beats": self.max_offset_beats,
            "stat_growth_scale": self.stat_growth_scale,
        }


# ======================================================================
# SuccessBonusRubric — backward-compatible simple success/failure rubric
# ======================================================================


class SuccessBonusRubric(Rubric):
    """Simple success/failure rubric for backward compatibility.

    Returns a fixed bonus when the action succeeds, and zero on failure.
    Used as the default rubric by ``FleetMidiEnvironment`` when no rubric
    is explicitly provided.

    Args:
        success_bonus (`float`, *optional*, defaults to ``1.0``):
            Reward for successful actions.
        failure_bonus (`float`, *optional*, defaults to ``0.0``):
            Reward for failed actions.
        stat_growth_scale (`float`, *optional*, defaults to ``0.2``):
            Amount of stat growth per unit score.
    """

    def __init__(
        self,
        success_bonus: float = 1.0,
        failure_bonus: float = -1.0,
        stat_growth_scale: float = 0.2,
    ):
        super().__init__()
        self.success_bonus = success_bonus
        self.failure_bonus = failure_bonus
        self.stat_growth_scale = stat_growth_scale

    def forward(self, action: Any, observation: Any) -> float:
        """Score based on success/failure detection.

        Checks both ``action`` and ``observation`` for an
        ``"error"`` key or ``"status"`` set to ``"error"``.

        Returns:
            `float`: ``success_bonus`` on success, ``failure_bonus`` on failure.
        """
        for source in (action, observation):
            if isinstance(source, dict):
                has_error = (
                    "error" in source
                    or source.get("status") == "error"
                )
                if has_error:
                    return self.failure_bonus

        return self.success_bonus

    def _apply_stat_growth(self, score: float, stats: "Stats") -> None:
        from fleet_characters.stats import StatName
        growth = score * self.stat_growth_scale
        if growth > 0:
            stats.grow(StatName.CONSTITUTION, growth)
            self._record_growth("constitution", growth)

    def state_dict(self) -> Dict[str, Any]:
        return {
            **super().state_dict(),
            "success_bonus": self.success_bonus,
            "failure_bonus": self.failure_bonus,
            "stat_growth_scale": self.stat_growth_scale,
        }


# ======================================================================
# CompositeRubric — backward-compatible alias for CompositeFleetRubric
# ======================================================================


# ======================================================================
# CompositeFleetRubric
# ======================================================================


class CompositeFleetRubric(Rubric):
    """Aggregates multiple child rubrics into a single weighted score.

    Each child rubric contributes its score multiplied by its weight,
    and the weighted average becomes the composite reward. Child rubric
    stat growth is applied per-child when ``agent_stats`` is provided.

    Args:
        rubrics (`Dict[str, Rubric]`):
            Named child rubrics to aggregate.
        weights (`Dict[str, float]`, *optional*):
            Weight per rubric name. Defaults to equal weights if omitted.
        name (`str`, *optional*):
            Optional name for identification in fleet reports.
    """

    def __init__(
        self,
        rubrics: Optional[Dict[str, Rubric]] = None,
        weights: Optional[Dict[str, float]] = None,
        name: Optional[str] = None,
    ):
        super().__init__()
        self._composite_name = name
        self._rubric_registry: Dict[str, Rubric] = {}
        self._weights: Dict[str, float] = {}

        if rubrics:
            for rubric_name, rubric in rubrics.items():
                self.add_rubric(
                    rubric_name,
                    rubric,
                    weights.get(rubric_name) if weights else None,
                )

    def add_rubric(
        self,
        name: str,
        rubric: Rubric,
        weight: Optional[float] = None,
    ) -> None:
        """Register a child rubric with an optional weight.

        Args:
            name: Unique name for this child rubric.
            rubric: The rubric instance.
            weight: Relative weight (defaults to 1.0 / number of rubrics).
        """
        self._rubric_registry[name] = rubric
        # Auto-register as attribute for child tracking
        setattr(self, name, rubric)

        if weight is not None:
            self._weights[name] = weight
        else:
            self._weights[name] = 1.0

        # Rebalance: set each to equal weight
        n = len(self._rubric_registry)
        for key in self._rubric_registry:
            self._weights[key] = 1.0 / n

    def remove_rubric(self, name: str) -> None:
        """Remove a registered child rubric.

        Args:
            name: Name of rubric to remove.
        """
        if name in self._rubric_registry:
            del self._rubric_registry[name]
            self._weights.pop(name, None)
            # Remove from children tracking
            self._rubric_children.pop(name, None)

    def forward(self, action: Any, observation: Any) -> float:
        """Compute weighted aggregate of all child rubric scores.

        Args:
            action: The action taken by the agent.
            observation: The resulting observation.

        Returns:
            `float`: Weighted average score in ``[0.0, 1.0]``.
        """
        if not self._rubric_registry:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        # Normalize weights
        weight_sum = sum(self._weights.values())
        for name, rubric in self._rubric_registry.items():
            w = self._weights.get(name, 1.0)
            normalized_w = w / weight_sum if weight_sum > 0 else 1.0 / len(self._rubric_registry)

            # Evaluate child rubric (synchronous path — no agent_stats delegation here;
            # agent_stats is applied per-child in __call__)
            score = rubric(action, observation)
            weighted_sum += normalized_w * score
            total_weight += normalized_w

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _apply_stat_growth(self, score: float, stats: "Stats") -> None:
        """Delegate stat growth to child rubrics.

        The composite score triggers each child's stat growth proportionally.
        """
        for name, rubric in self._rubric_registry.items():
            w = self._weights.get(name, 1.0)
            weight_sum = sum(self._weights.values())
            normalized_w = w / weight_sum if weight_sum > 0 else 1.0 / len(self._rubric_registry)

            child_score = rubric.last_score if rubric.last_score is not None else 0.0
            rubric._apply_stat_growth(child_score * normalized_w, stats)

    @property
    def rubric_names(self) -> List[str]:
        """Names of all registered child rubrics."""
        return list(self._rubric_registry.keys())

    @property
    def rubric_weights(self) -> Dict[str, float]:
        """Current weight mapping."""
        return dict(self._weights)

    def last_scores(self) -> Dict[str, Optional[float]]:
        """Get the last score from each child rubric."""
        return {
            name: r.last_score
            for name, r in self._rubric_registry.items()
        }

    def report(self) -> Dict[str, Any]:
        """Generate a detailed score report."""
        total_weight = sum(self._weights.values()) if self._weights else 1.0
        details = {}
        weighted_sum = 0.0

        for name, rubric in self._rubric_registry.items():
            w = self._weights.get(name, 1.0)
            normalized_w = w / total_weight if total_weight > 0 else 1.0 / len(self._rubric_registry)
            score = rubric.last_score
            details[name] = {
                "score": score,
                "weight": w,
                "normalized_weight": round(normalized_w, 4),
                "contribution": round(score * normalized_w, 4) if score is not None else None,
                "stat_growth": rubric.stat_growth(),
            }
            if score is not None:
                weighted_sum += score * normalized_w

        return {
            "name": self._composite_name or "CompositeFleetRubric",
            "composite_score": round(weighted_sum, 4),
            "rubrics": details,
            "total_stat_growth": dict(self._stat_growth),
        }

    def reset(self) -> None:
        super().reset()
        for rubric in self._rubric_registry.values():
            rubric.reset()

    def state_dict(self) -> Dict[str, Any]:
        return {
            **super().state_dict(),
            "name": self._composite_name,
            "rubric_names": list(self._rubric_registry.keys()),
            "weights": dict(self._weights),
            "child_states": {
                name: r.state_dict() for name, r in self._rubric_registry.items()
            },
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        super().load_state_dict(state)
        self._composite_name = state.get("name")
        child_states = state.get("child_states", {})
        for name, child_state in child_states.items():
            if name in self._rubric_registry:
                self._rubric_registry[name].load_state_dict(child_state)


# ======================================================================
# CompositeRubric — backward-compatible alias
# ======================================================================


class CompositeRubric(CompositeFleetRubric):
    """Backward-compatible alias for ``CompositeFleetRubric``.

    Provided so that code importing ``CompositeRubric`` from
    ``.rubrics`` continues to work after the rename.
    """
    pass
