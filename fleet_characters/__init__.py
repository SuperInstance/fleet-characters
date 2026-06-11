"""
fleet_characters — Agent identity, class, narrative arc, and dream cycles.

Ports character-class, character-arc, and agent-dream-cycle Rust crates
to Python for direct integration into the 16 fleet-midi agents.

Each agent becomes a character with:
  - Six evolving stats (perception, dexterity, intelligence, wisdom, charisma, constitution)
  - Emergent class (16 classes discovered through experience)
  - Narrative arc (first-person story of growth)
  - Dream cycles (REM-sleep memory consolidation)
"""

from .stats import Stats, StatName
from .class_ import CharacterClass, ClassProgression, Archetype, AGENT_DEFAULT_CLASSES
from .arc import Tone, NarrativeEvent, EventType, Chapter, CharacterArc
from .dream import Experience, ConsolidationReport, MemoryConsolidation, FailureReplay, DreamCycle, DreamScheduler
from .agent_profile import AgentCharacter

__all__ = [
    'Stats', 'StatName',
    'CharacterClass', 'ClassProgression', 'Archetype', 'AGENT_DEFAULT_CLASSES',
    'Tone', 'NarrativeEvent', 'EventType', 'Chapter', 'CharacterArc',
    'Experience', 'ConsolidationReport', 'MemoryConsolidation', 'FailureReplay', 'DreamCycle', 'DreamScheduler',
    'AgentCharacter',
]
