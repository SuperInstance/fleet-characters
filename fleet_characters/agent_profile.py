"""
AgentCharacter — the complete identity object for a fleet-midi agent.

Wraps Stats + CharacterClass + CharacterArc + DreamCycle into one profile
that each agent carries. Stats grow from every request processed.
Class emerges from stats. The arc narrates the journey.
Dreams consolidate the memories.
"""

import random
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from .stats import Stats, StatName
from .class_ import CharacterClass, ClassProgression, AGENT_DEFAULT_CLASSES
from .arc import CharacterArc, Tone, NarrativeEvent, EventType
from .dream import DreamCycle, DreamScheduler, Experience


@dataclass
class AgentCharacter:
    """Complete identity for a fleet-midi agent.

    Combines:
    - Stats (6 stats grown through experience)
    - Class (emerges from stat distribution)
    - Arc (narrative of growth)
    - Dream cycle (REM-sleep memory consolidation)
    """
    agent_name: str
    domain: str  # chord, scale, melody, etc.

    # Identity
    stats: Stats = field(default_factory=Stats)
    class_progression: ClassProgression = field(default_factory=ClassProgression)
    arc: CharacterArc = None
    dream: DreamCycle = field(default_factory=DreamCycle)

    # Leveling
    level: int = 1
    xp: int = 0
    xp_to_next: int = 10
    total_requests: int = 0

    # Streaks
    success_streak: int = 0
    fail_streak: int = 0
    best_streak: int = 0
    worst_slump: int = 0

    # Class tracking
    current_class: CharacterClass = CharacterClass.UNDEFINED
    previous_class: Optional[CharacterClass] = None

    # Tick
    tick: int = 0

    def __post_init__(self):
        if self.arc is None:
            self.arc = CharacterArc.born(self.agent_name)

        # Set initial class from domain default
        initial_class = AGENT_DEFAULT_CLASSES.get(self.domain, CharacterClass.UNDEFINED)
        self.current_class = initial_class
        self.class_progression.record(self.level, initial_class, self.stats, "domain_default")

    def process_request(self, request_type: str = "cue", success: bool = True,
                        response_time_ms: float = 100.0) -> Dict[str, Any]:
        """Record that this agent processed a request. Stats grow naturally."""
        self.tick += 1
        self.total_requests += 1

        # Earn XP
        xp_gained = 1
        if success:
            xp_gained += 1
            self.success_streak += 1
            self.fail_streak = 0
            if self.success_streak > self.best_streak:
                self.best_streak = self.success_streak
            if self.success_streak > 0 and self.success_streak % 10 == 0:
                self.arc.record_streak(self.success_streak, self.tick)
        else:
            self.fail_streak += 1
            self.success_streak = 0
            if self.fail_streak > self.worst_slump:
                self.worst_slump = self.fail_streak
            if self.fail_streak > 0 and self.fail_streak % 3 == 0:
                self.arc.record_slump(self.fail_streak, self.tick)
            self.arc.record_encounter_lost(self.tick, f"failed_{request_type}")

        self.xp += xp_gained

        # Grow stats based on request type
        stat_growths = {
            'cue': StatName.PERCEPTION,
            'think': StatName.INTELLIGENCE,
        }
        stat = stat_growths.get(request_type, StatName.CHARISMA)
        self.stats.grow(stat, 0.3 if success else 0.1)
        self.stats.grow(StatName.CONSTITUTION, 0.1)

        # Speed affects dexterity
        if response_time_ms < 50:
            self.stats.grow(StatName.DEXTERITY, 0.4)
        elif response_time_ms < 200:
            self.stats.grow(StatName.DEXTERITY, 0.2)

        # Success affects charisma/wisdom
        if success:
            self.stats.grow(StatName.CHARISMA, 0.2)
            self.stats.grow(StatName.WISDOM, 0.1)

        # Check level up
        leveled_up = False
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.5)
            leveled_up = True
            self.arc.record_level_up(self.level, self.tick)

        # Check class emergence
        new_class = CharacterClass.from_stats(self.stats)
        class_changed = False
        if new_class != self.current_class and new_class != CharacterClass.UNDEFINED:
            self.previous_class = self.current_class
            old_name = self.current_class.name
            self.current_class = new_class
            self.class_progression.record(self.level, new_class, self.stats,
                                          "stat_emergence" if old_name == "Undefined" else "class_shift")
            if old_name == "Undefined":
                self.arc.record_class_emergence(new_class.name, self.tick)
            else:
                self.arc.record_class_shift(old_name, new_class.name, self.tick)
            class_changed = True

        # Record encounter if applicable
        if success and request_type == 'cue':
            self.arc.record_encounter_won(self.tick)

        # Record mastery milestones
        if self.total_requests == 100:
            self.arc.record_mastery("cue_analysis", self.tick)
        elif self.total_requests == 500:
            self.arc.record_mastery("ternary_routing", self.tick)
        elif self.total_requests == 1000:
            self.arc.record_mastery("domain_expertise", self.tick)

        # Record the experience for dreaming
        reward = 5.0 if success else -2.0
        self.dream.add_experience(Experience.simple(
            id=self.tick,
            input_=f"{request_type}:{self.domain}",
            success=success,
            reward=reward + (response_time_ms / 100.0),
            tick=self.tick,
        ))

        return {
            'leveled_up': leveled_up,
            'class_changed': class_changed,
            'new_class': new_class.name if class_changed else None,
            'xp': self.xp,
            'xp_to_next': self.xp_to_next,
        }

    def run_dream_cycle(self) -> Dict[str, Any]:
        """Trigger a dream cycle — agent consolidates memories."""
        report = self.dream.dream(20)
        return report.to_dict()

    @property
    def level_title(self) -> str:
        """Title based on level."""
        if self.level >= 50:
            return "Legendary"
        elif self.level >= 25:
            return "Elite"
        elif self.level >= 10:
            return "Veteran"
        elif self.level >= 5:
            return "Seasoned"
        return "Rising"

    @property
    def class_name(self) -> str:
        return self.current_class.name if self.current_class != CharacterClass.UNDEFINED else "Undefined"

    @property
    def class_description(self) -> str:
        return self.current_class.description

    @property
    def integration_score(self) -> float:
        """How well this agent integrates with others.
        Higher variance = more specialized = lower integration with generalists."""
        var = self.stats.variance()
        if var < 10:
            return 0.9  # Well-rounded, integrates easily
        elif var < 50:
            return 0.7
        elif var < 100:
            return 0.5
        else:
            return 0.3  # Highly specialized, harder to integrate

    def to_dict(self) -> dict:
        return {
            'agent': f"fleet-midi-{self.domain}",
            'name': self.agent_name,
            'domain': self.domain,
            'level': self.level,
            'title': self.level_title,
            'xp': self.xp,
            'xp_to_next': self.xp_to_next,
            'class': self.class_name,
            'class_description': self.class_description,
            'class_archetype': self.current_class.archetype.value,
            'previous_class': self.previous_class.name if self.previous_class else None,
            'class_trajectory': [c.name for c in self.class_progression.trajectory],
            'stats': self.stats.to_dict(),
            'total_requests': self.total_requests,
            'success_streak': self.success_streak,
            'best_streak': self.best_streak,
            'worst_slump': self.worst_slump,
            'integration_score': round(self.integration_score, 2),
            'arc': self.arc.to_dict(),
            'dream': self.dream.to_dict(),
            'tick': self.tick,
        }
