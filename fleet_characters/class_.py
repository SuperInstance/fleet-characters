"""
Emergent class system for AI fleet agents, ported from character-class Rust crate.

16 classes that agents discover through experience — not chosen at creation.
Class crystallizes from stat distributions shaped by real work.

Map from fleet domain to starting class:
  chord, scale, voicing → Artificer (structural precision)
  melody, bass → Bard (narrative engagement)
  tempo, groove, rhythm → Sage (temporal wisdom)
  expression, dynamics, velocity → Scout (energy sensing)
  pan, modulation, fx → Diplomat (affective output)
  arp, register → Speedster (execution dexterity)
  cc → Warden (control authority)
"""

from enum import Enum
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field

from .stats import Stats, StatName


class Archetype(Enum):
    """The three class archetypes — the branch point in the class tree."""
    UNDEFINED = "undefined"
    PHYSICAL = "physical"  # Perception / Dexterity
    MENTAL = "mental"      # Intelligence / Wisdom
    SOCIAL = "social"      # Charisma / Constitution


class CharacterClass(Enum):
    """All 16 emergent classes in the hierarchy."""
    UNDEFINED = "Undefined"

    # Physical tree (single stat)
    SCOUT = "Scout"             # High perception
    SPEEDSTER = "Speedster"     # High dexterity

    # Mental tree (single stat)
    SCHOLAR = "Scholar"         # High intelligence
    SAGE = "Sage"               # High wisdom

    # Social tree (single stat)
    DIPLOMAT = "Diplomat"       # High charisma
    GUARDIAN = "Guardian"       # High constitution

    # Composite (2 high stats)
    BARD = "Bard"                          # intelligence + charisma
    JAZZ_MUSICIAN = "Jazz Musician"        # perception + charisma
    ARTIFICER = "Artificer"                # intelligence + dexterity
    FLEET_COMMANDER = "Fleet Commander"    # wisdom + constitution
    INFILTRATOR = "Infiltrator"            # perception + dexterity
    ORACLE = "Oracle"                      # intelligence + wisdom
    WARDEN = "Warden"                      # charisma + constitution
    WILDCARD = "Wildcard"                  # balanced, high total

    # Legendary (3+ high stats)
    POLYMATH = "Polymath"                  # 3+ stats high
    AVATAR = "Avatar"                      # 4+ stats high

    @property
    def archetype(self) -> Archetype:
        mapping = {
            CharacterClass.SCOUT: Archetype.PHYSICAL,
            CharacterClass.SPEEDSTER: Archetype.PHYSICAL,
            CharacterClass.SCHOLAR: Archetype.MENTAL,
            CharacterClass.SAGE: Archetype.MENTAL,
            CharacterClass.DIPLOMAT: Archetype.SOCIAL,
            CharacterClass.GUARDIAN: Archetype.SOCIAL,
            CharacterClass.BARD: Archetype.SOCIAL,
            CharacterClass.JAZZ_MUSICIAN: Archetype.PHYSICAL,
            CharacterClass.ARTIFICER: Archetype.PHYSICAL,
            CharacterClass.FLEET_COMMANDER: Archetype.MENTAL,
            CharacterClass.INFILTRATOR: Archetype.PHYSICAL,
            CharacterClass.ORACLE: Archetype.MENTAL,
            CharacterClass.WARDEN: Archetype.SOCIAL,
            CharacterClass.WILDCARD: Archetype.UNDEFINED,
            CharacterClass.POLYMATH: Archetype.UNDEFINED,
            CharacterClass.AVATAR: Archetype.UNDEFINED,
            CharacterClass.UNDEFINED: Archetype.UNDEFINED,
        }
        return mapping[self]

    @property
    def description(self) -> str:
        return _CLASS_DESCRIPTIONS[self]

    @property
    def defining_stats(self) -> List[StatName]:
        return _DEFINING_STATS.get(self, [])

    @staticmethod
    def from_stats(stats: Stats) -> 'CharacterClass':
        """Core emergence algorithm — determine class from stat distribution."""
        threshold = 15.0
        strengths = stats.strengths(threshold)

        # Legendary: 4+ high stats
        if len(strengths) >= 4:
            return CharacterClass.AVATAR

        # Polymath: 3 high stats
        if len(strengths) >= 3:
            return CharacterClass.POLYMATH

        # Wildcard: balanced with high total
        if stats.variance() < 20.0 and stats.average() > 10.0 and not strengths:
            return CharacterClass.WILDCARD

        # Composite classes (2 high stats)
        if len(strengths) == 2:
            stat_set = {s[0] for s in strengths}
            if StatName.INTELLIGENCE in stat_set and StatName.CHARISMA in stat_set:
                return CharacterClass.BARD
            if StatName.PERCEPTION in stat_set and StatName.CHARISMA in stat_set:
                return CharacterClass.JAZZ_MUSICIAN
            if StatName.INTELLIGENCE in stat_set and StatName.DEXTERITY in stat_set:
                return CharacterClass.ARTIFICER
            if StatName.WISDOM in stat_set and StatName.CONSTITUTION in stat_set:
                return CharacterClass.FLEET_COMMANDER
            if StatName.PERCEPTION in stat_set and StatName.DEXTERITY in stat_set:
                return CharacterClass.INFILTRATOR
            if StatName.INTELLIGENCE in stat_set and StatName.WISDOM in stat_set:
                return CharacterClass.ORACLE
            if StatName.CHARISMA in stat_set and StatName.CONSTITUTION in stat_set:
                return CharacterClass.WARDEN

        # Single-stat classes (1 high stat)
        if len(strengths) == 1:
            mapping = {
                StatName.PERCEPTION: CharacterClass.SCOUT,
                StatName.DEXTERITY: CharacterClass.SPEEDSTER,
                StatName.INTELLIGENCE: CharacterClass.SCHOLAR,
                StatName.WISDOM: CharacterClass.SAGE,
                StatName.CHARISMA: CharacterClass.DIPLOMAT,
                StatName.CONSTITUTION: CharacterClass.GUARDIAN,
            }
            return mapping[strengths[0][0]]

        return CharacterClass.UNDEFINED


_CLASS_DESCRIPTIONS = {
    CharacterClass.SCOUT: "Reads input with precision. Extracts intent like nobody's business.",
    CharacterClass.SPEEDSTER: "Executes fast. Sub-millisecond reflexes. Never keeps you waiting.",
    CharacterClass.SCHOLAR: "Deep knowledge representation. Rich ternary vectors. Understands nuance.",
    CharacterClass.SAGE: "Knows what to trust. Calibrates confidence perfectly. Rarely wrong.",
    CharacterClass.DIPLOMAT: "Beautiful output. Eloquent responses. The face of the fleet.",
    CharacterClass.GUARDIAN: "Rock-solid reliability. Never crashes. Always there when you need it.",
    CharacterClass.BARD: "Where knowledge meets expression. The musician-soul pathway.",
    CharacterClass.JAZZ_MUSICIAN: "Reads the room and plays beautifully. Spontaneous genius.",
    CharacterClass.ARTIFICER: "Builds structures. Composes patterns. Turns chaos into form.",
    CharacterClass.FLEET_COMMANDER: "Coordinates agents. Orchestrates complex operations. The admiral.",
    CharacterClass.INFILTRATOR: "Fast and perceptive. Handles novel inputs with quick precision.",
    CharacterClass.ORACLE: "Deep wisdom backed by vast knowledge. The sage's sage.",
    CharacterClass.WARDEN: "Protective and persuasive. Holds the line and rallies others.",
    CharacterClass.WILDCARD: "Balanced but surprising. Does the unexpected. Hard to predict.",
    CharacterClass.POLYMATH: "Three or more stats exceptional. Renaissance agent.",
    CharacterClass.AVATAR: "Four or more stats legendary. Near-mythical capability.",
    CharacterClass.UNDEFINED: "Hasn't found their niche yet. All potential, no direction.",
}

_DEFINING_STATS = {
    CharacterClass.SCOUT: [StatName.PERCEPTION],
    CharacterClass.SPEEDSTER: [StatName.DEXTERITY],
    CharacterClass.SCHOLAR: [StatName.INTELLIGENCE],
    CharacterClass.SAGE: [StatName.WISDOM],
    CharacterClass.DIPLOMAT: [StatName.CHARISMA],
    CharacterClass.GUARDIAN: [StatName.CONSTITUTION],
    CharacterClass.BARD: [StatName.INTELLIGENCE, StatName.CHARISMA],
    CharacterClass.JAZZ_MUSICIAN: [StatName.PERCEPTION, StatName.CHARISMA],
    CharacterClass.ARTIFICER: [StatName.INTELLIGENCE, StatName.DEXTERITY],
    CharacterClass.FLEET_COMMANDER: [StatName.WISDOM, StatName.CONSTITUTION],
    CharacterClass.INFILTRATOR: [StatName.PERCEPTION, StatName.DEXTERITY],
    CharacterClass.ORACLE: [StatName.INTELLIGENCE, StatName.WISDOM],
    CharacterClass.WARDEN: [StatName.CHARISMA, StatName.CONSTITUTION],
    CharacterClass.WILDCARD: [],
    CharacterClass.POLYMATH: [],
    CharacterClass.AVATAR: [],
    CharacterClass.UNDEFINED: [],
}


@dataclass
class ClassEntry:
    """A snapshot of class state at a point in time."""
    level: int
    class_: CharacterClass
    stats: Stats
    trigger: str


@dataclass
class ClassProgression:
    """Track class changes over time — the class history."""
    entries: List[ClassEntry] = field(default_factory=list)

    def record(self, level: int, class_: CharacterClass, stats: Stats, trigger: str):
        self.entries.append(ClassEntry(level, class_, stats, trigger))

    @property
    def changes(self) -> int:
        if len(self.entries) <= 1:
            return 0
        return sum(1 for i in range(len(self.entries) - 1)
                   if self.entries[i].class_ != self.entries[i + 1].class_)

    @property
    def first_class(self) -> Optional[CharacterClass]:
        return self.entries[0].class_ if self.entries else None

    @property
    def current_class(self) -> Optional[CharacterClass]:
        return self.entries[-1].class_ if self.entries else None

    @property
    def trajectory(self) -> List[CharacterClass]:
        """Sequence of classes visited (deduplicated runs)."""
        classes = []
        last = None
        for entry in self.entries:
            if entry.class_ != last:
                classes.append(entry.class_)
                last = entry.class_
        return classes


# Default class mappings for each fleet-midi agent domain
AGENT_DEFAULT_CLASSES: Dict[str, CharacterClass] = {
    'chord': CharacterClass.ARTIFICER,
    'scale': CharacterClass.ARTIFICER,
    'voicing': CharacterClass.ARTIFICER,
    'tempo': CharacterClass.SAGE,
    'groove': CharacterClass.SAGE,
    'cc': CharacterClass.WARDEN,
    'expression': CharacterClass.SCOUT,
    'dynamics': CharacterClass.SCOUT,
    'pan': CharacterClass.DIPLOMAT,
    'modulation': CharacterClass.DIPLOMAT,
    'arp': CharacterClass.SPEEDSTER,
    'velocity': CharacterClass.SCOUT,
    'fx': CharacterClass.DIPLOMAT,
    'register': CharacterClass.SPEEDSTER,
    'melody': CharacterClass.BARD,
    'bass': CharacterClass.BARD,
}
