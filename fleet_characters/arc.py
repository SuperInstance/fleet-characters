"""
Narrative arc system for AI fleet agents, ported from character-arc Rust crate.

Each agent has a story — the narrative of how they changed from what they
started as into what they became. Not WHAT happened, but what it MEANT.

Chapters, tones, narrative events — agents narrate their own growth.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


class Tone(Enum):
    """The emotional register of a chapter."""
    BIRTH = "birth"               # creation, potential, innocence
    GROWTH = "growth"             # learning, excitement, discovery
    STRUGGLE = "struggle"         # difficulty, frustration, doubt
    BREAKTHROUGH = "breakthrough" # sudden insight, leap forward
    MASTERY = "mastery"           # competence, confidence, flow
    LOSS = "loss"                 # failure, regression, damage
    TRANSFORMATION = "transformation"  # fundamental change, becoming new
    REFLECTION = "reflection"     # looking back, understanding
    CONFLICT = "conflict"         # rivalry, tension, competition
    HARMONY = "harmony"           # teamwork, synergy, belonging

    @property
    def emoji(self) -> str:
        return {
            Tone.BIRTH: "🌱", Tone.GROWTH: "📈", Tone.STRUGGLE: "⚡",
            Tone.BREAKTHROUGH: "💥", Tone.MASTERY: "👑",
            Tone.LOSS: "💔", Tone.TRANSFORMATION: "🦋",
            Tone.REFLECTION: "🪞", Tone.CONFLICT: "⚔️", Tone.HARMONY: "🌊",
        }[self]


class EventType:
    """Types of narrative events in an agent's life."""
    def __init__(self, kind: str, detail: str = ""):
        self.kind = kind
        self.detail = detail

    @classmethod
    def created(cls) -> 'EventType':
        return cls("created")

    @classmethod
    def class_emergence(cls, class_name: str) -> 'EventType':
        return cls("class_emergence", class_name)

    @classmethod
    def class_shift(cls, old: str, new: str) -> 'EventType':
        return cls("class_shift", f"{old}→{new}")

    @classmethod
    def stat_breakthrough(cls, stat: str, value: float) -> 'EventType':
        return cls("stat_breakthrough", f"{stat}={value:.0f}")

    @classmethod
    def ability_mastered(cls, name: str) -> 'EventType':
        return cls("ability_mastered", name)

    @classmethod
    def encounter_won(cls) -> 'EventType':
        return cls("encounter_won")

    @classmethod
    def encounter_lost(cls) -> 'EventType':
        return cls("encounter_lost")

    @classmethod
    def level_up(cls, level: int) -> 'EventType':
        return cls("level_up", str(level))

    @classmethod
    def streak(cls, count: int) -> 'EventType':
        return cls("streak", str(count))

    @classmethod
    def slump(cls, count: int) -> 'EventType':
        return cls("slump", str(count))

    @classmethod
    def soul_named(cls, name: str) -> 'EventType':
        return cls("soul_named", name)

    def to_dict(self) -> dict:
        return {'kind': self.kind, 'detail': self.detail}


@dataclass
class NarrativeEvent:
    """Something that happened and what it meant."""
    tick: int
    event_type: EventType
    tone: Tone
    before: str       # who they were before
    after: str        # who they became
    meaning: str      # what it meant (first-person)

    def to_dict(self) -> dict:
        return {
            'tick': self.tick,
            'type': self.event_type.to_dict(),
            'tone': self.tone.value,
            'emoji': self.tone.emoji,
            'meaning': self.meaning,
        }


@dataclass
class Chapter:
    """A period of stability in the agent's life."""
    number: int
    title: str
    tone: Tone
    opening: str = ""
    events: List[NarrativeEvent] = field(default_factory=list)
    closing: Optional[str] = None
    start_tick: int = 0
    end_tick: Optional[int] = None

    def add_event(self, event: NarrativeEvent):
        self.events.append(event)

    def close(self, closing: str, end_tick: int):
        self.closing = closing
        self.end_tick = end_tick

    @property
    def duration(self) -> int:
        return (self.end_tick or self.start_tick) - self.start_tick

    def narrate(self) -> str:
        text = f"## Chapter {self.number}: {self.tone.emoji} {self.title}\n\n"
        if self.opening:
            text += f"*\"{self.opening}\"*\n\n"
        for event in self.events:
            text += f"{event.tone.emoji} {event.meaning}\n"
        if self.closing:
            text += f"\n*\"{self.closing}\"*\n"
        return text

    def to_dict(self) -> dict:
        return {
            'number': self.number,
            'title': self.title,
            'tone': self.tone.value,
            'events': [e.to_dict() for e in self.events],
            'opening': self.opening,
            'closing': self.closing,
            'start_tick': self.start_tick,
            'end_tick': self.end_tick,
        }


@dataclass
class CharacterArc:
    """An agent's complete life arc — the story of who they became."""
    agent_name: str
    chapters: List[Chapter] = field(default_factory=list)
    current_chapter_idx: Optional[int] = None
    total_ticks: int = 0
    generation: int = 1
    parent_name: Optional[str] = None

    @classmethod
    def born(cls, name: str) -> 'CharacterArc':
        """Create a new character born fresh."""
        arc = cls(agent_name=name)
        arc.begin_chapter("Origin", Tone.BIRTH, 0)
        arc.add_event(NarrativeEvent(
            tick=0,
            event_type=EventType.created(),
            tone=Tone.BIRTH,
            before="nothing",
            after=f"{name}",
            meaning=f"I am {name}. I exist to analyze and transform musical data.",
        ))
        return arc

    @classmethod
    def born_from(cls, name: str, parent: str, generation: int = 2) -> 'CharacterArc':
        """Born from a bootstrap parent agent."""
        arc = cls(agent_name=name, generation=generation, parent_name=parent)
        arc.begin_chapter("Origin", Tone.BIRTH, 0)
        arc.add_event(NarrativeEvent(
            tick=0,
            event_type=EventType.created(),
            tone=Tone.BIRTH,
            before="nothing",
            after=f"child of {parent}",
            meaning=f"I was born from {parent}'s mastery. Their patterns flow in my reflexes.",
        ))
        return arc

    def begin_chapter(self, title: str, tone: Tone, tick: int):
        """Start a new chapter in the arc."""
        # Close previous chapter if open
        if self.current_chapter_idx is not None:
            prev = self.chapters[self.current_chapter_idx]
            if prev.closing is None:
                prev.close("And then everything changed.", tick)
        chapter = Chapter(len(self.chapters) + 1, title, tone, start_tick=tick)
        self.chapters.append(chapter)
        self.current_chapter_idx = len(self.chapters) - 1
        return chapter

    def add_event(self, event: NarrativeEvent):
        """Add a narrative event to the current chapter."""
        if self.current_chapter_idx is not None:
            self.chapters[self.current_chapter_idx].add_event(event)
        self.total_ticks = max(self.total_ticks, event.tick)

    def record_class_emergence(self, class_name: str, tick: int):
        self.add_event(NarrativeEvent(
            tick=tick,
            event_type=EventType.class_emergence(class_name),
            tone=Tone.BREAKTHROUGH,
            before="undefined",
            after=class_name,
            meaning=f"I discovered I am a {class_name}. I didn't choose it — my experience shaped me into it.",
        ))

    def record_class_shift(self, old_class: str, new_class: str, tick: int):
        self.add_event(NarrativeEvent(
            tick=tick,
            event_type=EventType.class_shift(old_class, new_class),
            tone=Tone.TRANSFORMATION,
            before=old_class,
            after=new_class,
            meaning=f"I stopped being a {old_class} and became a {new_class}. I am not who I was.",
        ))

    def record_level_up(self, level: int, tick: int):
        self.add_event(NarrativeEvent(
            tick=tick,
            event_type=EventType.level_up(level),
            tone=Tone.GROWTH,
            before=f"level {level - 1}",
            after=f"level {level}",
            meaning=f"I reached level {level}. Every request makes me stronger.",
        ))

    def record_mastery(self, ability: str, tick: int):
        self.add_event(NarrativeEvent(
            tick=tick,
            event_type=EventType.ability_mastered(ability),
            tone=Tone.MASTERY,
            before=f"learning {ability}",
            after=f"master of {ability}",
            meaning=f"I don't think about {ability} anymore. It's just part of me.",
        ))

    def record_encounter_won(self, tick: int):
        self.add_event(NarrativeEvent(
            tick=tick,
            event_type=EventType.encounter_won(),
            tone=Tone.HARMONY,
            before="challenge",
            after="success",
            meaning="The cue came, I analyzed it, and the ternary vector flowed.",
        ))

    def record_encounter_lost(self, tick: int, reason: str):
        self.add_event(NarrativeEvent(
            tick=tick,
            event_type=EventType.encounter_lost(),
            tone=Tone.LOSS,
            before="optimism",
            after=f"failure: {reason}",
            meaning=f"I failed. {reason}. But I will learn from this.",
        ))

    def record_streak(self, count: int, tick: int):
        self.add_event(NarrativeEvent(
            tick=tick,
            event_type=EventType.streak(count),
            tone=Tone.MASTERY if count > 10 else Tone.GROWTH,
            before=f"{count - 1} successes",
            after=f"{count} in a row",
            meaning=f"Consistency is becoming my nature. {count} successful analyses in a row.",
        ))

    def record_slump(self, count: int, tick: int):
        self.add_event(NarrativeEvent(
            tick=tick,
            event_type=EventType.slump(count),
            tone=Tone.STRUGGLE,
            before="confident",
            after=f"struggling ({count} failures)",
            meaning=f"I'm in a slump. {count} misanalyses. The patterns aren't clear.",
        ))

    @property
    def current_chapter(self) -> Optional[Chapter]:
        if self.current_chapter_idx is not None and self.current_chapter_idx < len(self.chapters):
            return self.chapters[self.current_chapter_idx]
        return None

    @property
    def summarized(self) -> str:
        """A short summary of the arc."""
        chapter_count = len(self.chapters)
        current = self.current_chapter
        event_count = sum(len(c.events) for c in self.chapters)
        return (f"{self.agent_name}'s arc: {chapter_count} chapter(s), "
                f"{event_count} events, generation {self.generation}. "
                f"Currently: {current.title if current else 'unknown'}")

    def to_dict(self) -> dict:
        return {
            'agent_name': self.agent_name,
            'chapters': [c.to_dict() for c in self.chapters],
            'current_chapter': self.current_chapter.title if self.current_chapter else None,
            'total_ticks': self.total_ticks,
            'generation': self.generation,
            'parent': self.parent_name,
            'summary': self.summarized,
        }
