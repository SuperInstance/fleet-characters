"""
AutoAction — action construction helpers for fleet-midi agent communication.

Provides utilities to build properly formatted cue and think payloads
that fleet-midi agent servers understand.

Cue (MIDI-mode) payload fields:
  - notes: List of MIDI note numbers
  - voice/payload: Additional parameters (velocity, bpm, cc, etc.)
  - Key used depends on agent domain (chord looks at notes, tempo at bpm, etc.)

Think (text-reasoning) payload fields:
  - task: Text description of the task
  - context: Dict of additional context (past results, current state, etc.)

Examples:
    >>> from fleet_characters.environment.auto.auto_action import CueBuilder, build_cue
    >>>
    >>> # Quick builder
    >>> cue = build_cue("chord", [60, 64, 67])
    >>> cue["notes"]
    [60, 64, 67]
    >>>
    >>> # Using CueBuilder for complex constructions
    >>> cue = CueBuilder("chord").notes(60, 64, 67).velocity(80).build()
    >>> cue["voice"]["velocity"]
    80
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union


# ─── Agent Domain Keys ─────────────────────────────────────────────────

# Which payload keys each agent primarily reads
AGENT_PAYLOAD_KEYS: Dict[str, List[str]] = {
    "chord": ["notes", "voice"],
    "scale": ["notes", "voice"],
    "voicing": ["notes", "voice"],
    "tempo": ["bpm", "tempo"],
    "cc": ["cc", "ccs", "delta"],
    "expression": ["expression", "cc"],
    "dynamics": ["velocity"],
    "pan": ["pan", "azimuth", "spatial"],
    "modulation": ["modulation", "mod", "rate", "lfo_rate"],
    "arp": ["notes", "voice"],
    "groove": ["swing", "groove"],
    "velocity": ["velocity", "accent"],
    "fx": ["fx", "effect", "wet", "mix"],
    "register": ["notes", "voice"],
    "melody": ["notes", "voice"],
    "bass": ["notes", "voice"],
}


# ─── build_cue — Quick Cue Builder ─────────────────────────────────────

def build_cue(
    agent_name: str,
    notes: Optional[List[int]] = None,
    payload: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Build a cue dict for a fleet-midi agent.

    The cue dict is the payload sent to POST /agent for MIDI-mode processing.
    Each agent's handler extracts domain-specific fields from the payload.

    Args:
        agent_name: Agent name (e.g., "chord", "tempo", "fx").
        notes: Optional list of MIDI note numbers (0-127).
        payload: Optional additional parameters dict.
        **kwargs: Extra fields merged into the outer dict.

    Returns:
        Cue dict ready for POST /agent.

    Examples:
        >>> build_cue("chord", [60, 64, 67])
        {'notes': [60, 64, 67]}

        >>> build_cue("tempo", bpm=140)
        {'bpm': 140}

        >>> build_cue("fx", payload={"fx": "delay", "wet": 75})
        {'voice': {'fx': 'delay', 'wet': 75}}
    """
    cue: Dict[str, Any] = {}

    if notes is not None:
        cue["notes"] = notes

    if payload is not None:
        cue["voice"] = payload

    if kwargs:
        cue.update(kwargs)

    return cue


# ─── build_think — Think Payload Builder ───────────────────────────────

def build_think(
    agent_name: str,
    task: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Build a think dict for a fleet-midi agent.

    The think dict is sent to POST /agent with type="think" for
    text-reasoning mode — the agent analyzes the task through its
    domain-specific lens and returns a ternary analysis.

    Args:
        agent_name: Agent name (e.g., "chord", "melody").
        task: Text description of the task to analyze.
        context: Optional dict of additional context (past results,
            current state, environment data).
        **kwargs: Extra fields merged into the outer dict.

    Returns:
        Think dict ready for POST /agent.

    Examples:
        >>> build_think("chord", "Analyze the harmonic movement")
        {'type': 'think', 'task': 'Analyze the harmonic movement', 'context': {}}

        >>> build_think("melody", "Create a descending line",
        ...             context={"style": "jazz", "root": 60})
        {'type': 'think', 'task': 'Create a descending line',
         'context': {'style': 'jazz', 'root': 60}}
    """
    think: Dict[str, Any] = {
        "type": "think",
        "task": task,
        "context": context or {},
    }

    if kwargs:
        think.update(kwargs)

    return think


# ─── CueBuilder Class ──────────────────────────────────────────────────

class CueBuilder:
    """Fluent builder for constructing complex cue payloads.

    Provides a chainable API for building agent-specific cue payloads
    with proper field placement (notes, voice payload, parameters).

    Examples:
        >>> cue = (CueBuilder("chord")
        ...     .notes(60, 64, 67)
        ...     .velocity(80)
        ...     .add_voice("expression", 100)
        ...     .build())
        >>> cue["notes"]
        [60, 64, 67]
        >>> cue["voice"]["velocity"]
        80
        >>> cue["voice"]["expression"]
        100

        >>> cue = (CueBuilder("tempo")
        ...     .bpm(140)
        ...     .add_voice("time_signature", "4/4")
        ...     .build())
        >>> cue["bpm"]
        140

        >>> # Multi-agent dispatch: build a cue, then fan-out to agents
        >>> chord_cue = CueBuilder("chord").notes(60, 64, 67).build()
    """

    def __init__(self, agent_name: str):
        """Initialize builder for a specific agent.

        Args:
            agent_name: Agent name (e.g., "chord", "tempo", "fx").
        """
        self._agent_name = agent_name
        self._notes: Optional[List[int]] = None
        self._voice: Dict[str, Any] = {}
        self._extra: Dict[str, Any] = {}

    def notes(self, *note_numbers: int) -> "CueBuilder":
        """Set MIDI note numbers for this cue.

        Args:
            *note_numbers: One or more MIDI note values (0-127).

        Returns:
            Self for chaining.
        """
        self._notes = list(note_numbers)
        return self

    def velocity(self, vel: int) -> "CueBuilder":
        """Set velocity in the voice payload.

        Relevant for: dynamics, velocity, expression agents.

        Args:
            vel: Velocity value (0-127).

        Returns:
            Self for chaining.
        """
        self._voice["velocity"] = vel
        return self

    def bpm(self, beats_per_minute: float) -> "CueBuilder":
        """Set BPM for tempo-related agents.

        Relevant for: tempo, groove.

        Args:
            beats_per_minute: Tempo in BPM.

        Returns:
            Self for chaining.
        """
        self._extra["bpm"] = beats_per_minute
        self._voice["bpm"] = beats_per_minute
        return self

    def cc(self, cc_value: int, delta: int = 0) -> "CueBuilder":
        """Set CC (control change) value.

        Relevant for: cc agent.

        Args:
            cc_value: CC value (0-127).
            delta: Change delta from previous value.

        Returns:
            Self for chaining.
        """
        self._voice["cc"] = cc_value
        self._voice["delta"] = delta
        return self

    def pan(self, pan_value: int) -> "CueBuilder":
        """Set pan/azimuth value.

        Relevant for: pan agent.

        Args:
            pan_value: Pan value (0-127, 64=center).

        Returns:
            Self for chaining.
        """
        self._voice["pan"] = pan_value
        return self

    def modulation(self, mod_value: int, rate: float = 2.0) -> "CueBuilder":
        """Set modulation parameters.

        Relevant for: modulation agent.

        Args:
            mod_value: Modulation depth (0-127).
            rate: LFO rate in Hz.

        Returns:
            Self for chaining.
        """
        self._voice["modulation"] = mod_value
        self._voice["rate"] = rate
        self._voice["lfo_rate"] = rate
        return self

    def swing(self, swing_amount: int) -> "CueBuilder":
        """Set swing/groove amount.

        Relevant for: groove agent.

        Args:
            swing_amount: Swing offset (0-100).

        Returns:
            Self for chaining.
        """
        self._voice["swing"] = swing_amount
        self._voice["groove"] = swing_amount
        return self

    def accent(self, accent_value: int) -> "CueBuilder":
        """Set accent value.

        Relevant for: velocity agent.

        Args:
            accent_value: Accent strength (-127 to 127).

        Returns:
            Self for chaining.
        """
        self._voice["accent"] = accent_value
        return self

    def fx(self, fx_type: str, wet: int = 50) -> "CueBuilder":
        """Set effect type and wet/dry mix.

        Relevant for: fx agent.

        Args:
            fx_type: Effect type name (e.g., "reverb", "delay", "chorus").
            wet: Wet/dry mix (0-100).

        Returns:
            Self for chaining.
        """
        self._voice["fx"] = fx_type
        self._voice["effect"] = fx_type
        self._voice["wet"] = wet
        self._voice["mix"] = wet
        return self

    def expression(self, expression_value: int) -> "CueBuilder":
        """Set expression/articulation value.

        Relevant for: expression agent.

        Args:
            expression_value: Expression CC value (0-127).

        Returns:
            Self for chaining.
        """
        self._voice["expression"] = expression_value
        self._voice["cc"] = expression_value
        return self

    def add_voice(self, key: str, value: Any) -> "CueBuilder":
        """Add an arbitrary key-value pair to the voice payload.

        Args:
            key: Field name.
            value: Field value.

        Returns:
            Self for chaining.
        """
        self._voice[key] = value
        return self

    def add_extra(self, key: str, value: Any) -> "CueBuilder":
        """Add an arbitrary key-value pair to the top-level cue dict.

        Args:
            key: Field name.
            value: Field value.

        Returns:
            Self for chaining.
        """
        self._extra[key] = value
        return self

    def build(self) -> Dict[str, Any]:
        """Build the final cue dict.

        Returns:
            Complete cue dict for POST /agent.
        """
        cue: Dict[str, Any] = {}

        if self._notes is not None:
            cue["notes"] = self._notes

        if self._voice:
            cue["voice"] = self._voice

        cue.update(self._extra)

        return cue

    @classmethod
    def from_dict(cls, agent_name: str, data: Dict[str, Any]) -> "CueBuilder":
        """Create a CueBuilder pre-populated from an existing dict.

        Extracts notes (list) and voice (dict) from the data if present.

        Args:
            agent_name: Agent name.
            data: Existing cue dict.

        Returns:
            CueBuilder instance with data applied.
        """
        builder = cls(agent_name)
        notes = data.get("notes")
        if isinstance(notes, list):
            builder._notes = list(notes)
        elif isinstance(notes, int):
            builder._notes = [notes]

        voice = data.get("voice", {})
        if isinstance(voice, dict):
            builder._voice = dict(voice)

        for k, v in data.items():
            if k not in ("notes", "voice"):
                builder._extra[k] = v

        return builder


# ─── Legacy Alias ──────────────────────────────────────────────────────

AutoAction = CueBuilder
"""Alias for backward compatibility with OpenEnv naming convention."""
