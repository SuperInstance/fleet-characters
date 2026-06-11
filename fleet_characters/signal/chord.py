"""
Port of ternary-music: chord analysis using balanced ternary {-1, 0, +1}.

Reduces music theory to its essential ternary nature:
  - Tension  (+1) = Dominant, augmented, diminished chords
  - Neutral  ( 0) = Tonic, sus4, sus2, major 7th
  - Resolution(-1) = Subdominant, relative minor, perfect cadence

Scale degrees as ternary:
  - Stable  (+1) = Tonic (1), Perfect 5th (5)
  - Passing ( 0) = 2nd, 4th, 6th
  - Tendency (-1) = Leading tone (7), tritone
"""

import math
from typing import List, Tuple, Optional


# ─── Interval maps ────────────────────────────────────────────────

SEMITONE = 1
WHOLE_TONE = 2
MINOR_THIRD = 3
MAJOR_THIRD = 4
PERFECT_FOURTH = 5
TRITONE = 6
PERFECT_FIFTH = 7
MINOR_SIXTH = 8
MAJOR_SIXTH = 9
MINOR_SEVENTH = 10
MAJOR_SEVENTH = 11
OCTAVE = 12

# Chord quality → ternary tension
CHORD_TENSION: dict = {
    # Major-based
    'maj': 0, 'maj7': 0, 'sus2': 0, 'sus4': 0,
    'maj9': 0, 'maj13': 0, 'maj7#11': -1,
    # Minor-based
    'min': -1, 'min7': -1, 'min9': -1, 'min11': -1,
    'm7b5': 1, 'dim': 1, 'dim7': 1,
    # Dominant
    '7': 1, '9': 1, '13': 1, '7b9': 1, '7#9': 1,
    '7#11': 1, '7b5': 1, '7#5': 1, 'alt': 1,
    'aug': 1, 'aug7': 1, 'dim': 1,
    'power': 0,
}


def interval_semitones(note1: int, note2: int) -> int:
    """Get the interval in semitones between two MIDI notes (mod 12)."""
    return (note2 % 12 - note1 % 12) % 12


def _chord_type_from_intervals(intervals: List[int]) -> str:
    """Identify chord quality from sorted interval vector (excluding root)."""
    # Common chord patterns (intervals from root)
    patterns = {
        (4, 7): 'maj',                    # Major triad
        (3, 7): 'min',                    # Minor triad
        (4, 7, 11): 'maj7',               # Major 7th
        (3, 7, 10): 'min7',               # Minor 7th
        (4, 7, 10): '7',                  # Dominant 7th
        (3, 6): 'dim',                    # Diminished triad
        (3, 6, 9): 'dim7',               # Diminished 7th
        (3, 6, 10): 'm7b5',              # Half-diminished
        (4, 8): 'aug',                    # Augmented triad
        (4, 8, 11): 'aug7',              # Augmented 7th
        (5, 7): 'sus4',                  # Sus4
        (2, 7): 'sus2',                  # Sus2
        (4, 7, 10, 14): '9',            # Dominant 9th
        (4, 7, 10, 14, 17): '13',       # Dominant 13th
        (3, 7, 10, 14): 'min9',         # Minor 9th
        (0,): 'power',                   # Power chord (just root + 5th implied)
        (7,): 'power',                   # Power chord (root + 5th)
    }
    # Normalize: remove root (0), sort, deduplicate
    iv = sorted(set(i for i in intervals if i > 0 and i <= 12))
    return patterns.get(tuple(iv), 'maj')


def chord_tension(notes: List[int]) -> Tuple[str, int, float, int]:
    """
    Analyze a set of notes as a chord.
    
    Returns: (chord_type, root, tension, ternary_value)
    
    ternary_value: +1 = tense (dominant/aug/dim), 0 = neutral, -1 = resolved
    tension: 0.0-1.0 float scale
    """
    if not notes:
        return ('rest', 0, 0.0, 0)

    # Get unique pitch classes
    pitch_classes = sorted(set(n % 12 for n in notes))
    if len(pitch_classes) == 1:
        return ('unison', pitch_classes[0], 0.0, 0)
    if len(pitch_classes) == 2:
        iv = interval_semitones(pitch_classes[0], pitch_classes[1])
        # Perfect intervals are neutral
        if iv in (PERFECT_FIFTH, PERFECT_FOURTH, OCTAVE):
            return ('power', pitch_classes[0], 0.1, 0)
        # Dissonant intervals are tense
        if iv in (TRITONE, MINOR_SECOND := 1, MAJOR_SEVENTH):
            return ('dyad', pitch_classes[0], 0.8, 1)
        # Others are moderate
        return ('dyad', pitch_classes[0], 0.4, 0)

    # 3+ pitch classes — identify chord from intervals
    # Try each note as root
    best_root = pitch_classes[0]
    best_score = float('inf')
    best_type = 'maj'
    
    for candidate_root in pitch_classes:
        ivs = sorted((pc - candidate_root) % 12 for pc in pitch_classes)
        ctype = _chord_type_from_intervals(ivs)
        score = abs(len(ivs) - 3)  # Prefer triads
        if score < best_score:
            best_score = score
            best_root = candidate_root
            best_type = ctype

    # Map chord type to ternary tension
    tension_map = {
        'maj': 0, 'min': -1, 'maj7': 0, 'min7': -1, '7': 1,
        'dim': 1, 'dim7': 1, 'm7b5': 1, 'aug': 1, 'aug7': 1,
        'sus4': 0, 'sus2': 0, 'power': 0, '9': 1, '13': 1,
        'min9': -1, 'unison': 0, 'dyad': 0,
    }
    tension_val = tension_map.get(best_type, 0)
    tension_float = {
        1: 0.8, 0: 0.3, -1: 0.1,
    }.get(tension_val, 0.3)

    return (best_type, best_root, tension_float, tension_val)


def analyze_chord(notes: List[int], payload: dict = None) -> dict:
    """Full chord analysis for the chord fleet-midi agent (:2160)."""
    ctype, root, tension_float, tension_val = chord_tension(notes)
    
    if ctype == 'rest':
        return {'result': 'rest', 'ternary_vector': [0, 0, 0]}
    
    # Build ternary_vector: [tension, complexity, voicing_density]
    note_count = len(set(n % 12 for n in notes))  # unique pitch classes
    complexity = 1 if note_count > 3 else (0 if note_count > 1 else -1)
    voicing_density = 1 if len(notes) > 5 else (0 if len(notes) > 3 else -1)
    
    return {
        'result': ctype,
        'root': root,
        'tension': round(tension_float, 2),
        'note_count': note_count,
        'total_notes': len(notes),
        'pitch_classes': sorted(set(n % 12 for n in notes)),
        'ternary_vector': [tension_val, complexity, voicing_density],
    }


class TernaryChord:
    """A chord in ternary music theory — defined by its tension state."""
    
    TENSION = 1     # Dominant, augmented, diminished
    NEUTRAL = 0     # Tonic, sus, power
    RESOLUTION = -1 # Subdominant, minor
    
    def __init__(self, root: int, chord_type: str, tension: int):
        self.root = root
        self.chord_type = chord_type
        self.tension = tension
    
    @classmethod
    def from_notes(cls, notes: List[int]) -> 'TernaryChord':
        ctype, root, _, tension = chord_tension(notes)
        return cls(root, ctype, tension)
    
    def tension_curve(self, next_chord: 'TernaryChord') -> List[int]:
        """
        Return the ternary tension curve between two chords.
        Classic example: ii-V-I = [1, -1, 1] (tension buildup, resolution)
        """
        return [self.tension, next_chord.tension, -1 if next_chord.tension == -1 else 1]
    
    def __repr__(self):
        return f"TernaryChord(root={self.root}, type={self.chord_type}, tension={'T' if self.tension==1 else 'N' if self.tension==0 else 'R'})"
