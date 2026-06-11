"""
Six core stats for AI agent characters, ported from character-class Rust crate.

Stats grow through agent experience — each request processed, each cue analyzed,
each think task performed. Class emerges from stat distribution.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple


class StatName(Enum):
    PERCEPTION = "perception"      # Intent extraction quality (cue/think accuracy)
    DEXTERITY = "dexterity"        # Execution speed (response time)
    INTELLIGENCE = "intelligence"  # Knowledge representation (ternary vector quality)
    WISDOM = "wisdom"              # Trust calibration (confidence accuracy)
    CHARISMA = "charisma"          # Output quality (result richness)
    CONSTITUTION = "constitution"  # Reliability (uptime, error recovery)

    def as_str(self) -> str:
        return self.value


@dataclass
class Stats:
    MAX_STAT: float = 50.0  # Hard cap — no stat goes above this
    MIN_STAT: float = 3.0   # Floor — stats can't drop below viable minimum

    perception: float = 10.0
    dexterity: float = 10.0
    intelligence: float = 10.0
    wisdom: float = 10.0
    charisma: float = 10.0
    constitution: float = 10.0

    @classmethod
    def level_one(cls) -> 'Stats':
        """Starting stats for a fresh agent."""
        return cls()

    def average(self) -> float:
        return (self.perception + self.dexterity + self.intelligence +
                self.wisdom + self.charisma + self.constitution) / 6.0

    def total(self) -> float:
        return (self.perception + self.dexterity + self.intelligence +
                self.wisdom + self.charisma + self.constitution)

    def variance(self) -> float:
        """How spread out the stats are — low variance = balanced."""
        avg = self.average()
        return ((self.perception - avg) ** 2 + (self.dexterity - avg) ** 2 +
                (self.intelligence - avg) ** 2 + (self.wisdom - avg) ** 2 +
                (self.charisma - avg) ** 2 + (self.constitution - avg) ** 2) / 6.0

    def highest(self) -> Tuple[StatName, float]:
        candidates = [(StatName.PERCEPTION, self.perception),
                      (StatName.DEXTERITY, self.dexterity),
                      (StatName.INTELLIGENCE, self.intelligence),
                      (StatName.WISDOM, self.wisdom),
                      (StatName.CHARISMA, self.charisma),
                      (StatName.CONSTITUTION, self.constitution)]
        return max(candidates, key=lambda x: x[1])

    def lowest(self) -> Tuple[StatName, float]:
        candidates = [(StatName.PERCEPTION, self.perception),
                      (StatName.DEXTERITY, self.dexterity),
                      (StatName.INTELLIGENCE, self.intelligence),
                      (StatName.WISDOM, self.wisdom),
                      (StatName.CHARISMA, self.charisma),
                      (StatName.CONSTITUTION, self.constitution)]
        return min(candidates, key=lambda x: x[1])

    def get(self, name: StatName) -> float:
        return {StatName.PERCEPTION: self.perception,
                StatName.DEXTERITY: self.dexterity,
                StatName.INTELLIGENCE: self.intelligence,
                StatName.WISDOM: self.wisdom,
                StatName.CHARISMA: self.charisma,
                StatName.CONSTITUTION: self.constitution}[name]

    def grow(self, name: StatName, amount: float = 0.5):
        """Grow a specific stat. Diminishing returns above 20. Clamped to [MIN_STAT, MAX_STAT].
        
        Negative amounts are treated as a no-op (stats only grow or stay;
        decay happens through stat decay, not direct negative growth).
        """
        if amount <= 0:
            return  # Stats only grow — no decay through grow()
        current = self.get(name)
        if current >= Stats.MAX_STAT:
            return  # Already at max — no more growth
        # Diminishing returns: harder to increase as stat gets higher
        if current < 20:
            multiplier = 1.0
        elif current < 30:
            multiplier = 0.5
        elif current < 40:
            multiplier = 0.25
        else:
            multiplier = 0.1
        delta = amount * multiplier
        new_val = min(current + delta, Stats.MAX_STAT)
        setattr(self, name.value, new_val)

    def strengths(self, threshold: float = 15.0) -> List[Tuple[StatName, float]]:
        """Stats above the threshold — this agent's strengths."""
        all_stats = [(StatName.PERCEPTION, self.perception),
                     (StatName.DEXTERITY, self.dexterity),
                     (StatName.INTELLIGENCE, self.intelligence),
                     (StatName.WISDOM, self.wisdom),
                     (StatName.CHARISMA, self.charisma),
                     (StatName.CONSTITUTION, self.constitution)]
        return [(n, v) for n, v in all_stats if v >= threshold]

    def to_dict(self) -> dict:
        return {
            'perception': round(self.perception, 1),
            'dexterity': round(self.dexterity, 1),
            'intelligence': round(self.intelligence, 1),
            'wisdom': round(self.wisdom, 1),
            'charisma': round(self.charisma, 1),
            'constitution': round(self.constitution, 1),
            'average': round(self.average(), 1),
            'variance': round(self.variance(), 1),
        }

    def __str__(self) -> str:
        return (f"PER:{self.perception:.1f} DEX:{self.dexterity:.1f} "
                f"INT:{self.intelligence:.1f} WIS:{self.wisdom:.1f} "
                f"CHA:{self.charisma:.1f} CON:{self.constitution:.1f}")
