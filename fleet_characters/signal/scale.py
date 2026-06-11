"""
Port of ternary-temperament: interval analysis and scale degree classification.

Scale degrees as ternary:
  Stable  (+1) = Tonic (1), Perfect 5th (5)
  Passing ( 0) = Supertonic (2), Subdominant (4), Submediant (6)
  Tendency (-1) = Leading tone (7), Tritone, Chromatic notes
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


# ─── Interval Representation ─────────────────────────────────────────

@dataclass
class Interval:
    """A musical interval in cents with name."""
    semitones: int
    cents: int
    name: str
    quality: str  # perfect, major, minor, augmented, diminished

    @classmethod
    def from_semitones(cls, st: int) -> 'Interval':
        mapping = {
            0:  ('Unison', 'perfect'),
            1:  ('Minor 2nd', 'minor'),
            2:  ('Major 2nd', 'major'),
            3:  ('Minor 3rd', 'minor'),
            4:  ('Major 3rd', 'major'),
            5:  ('Perfect 4th', 'perfect'),
            6:  ('Tritone', 'augmented'),
            7:  ('Perfect 5th', 'perfect'),
            8:  ('Minor 6th', 'minor'),
            9:  ('Major 6th', 'major'),
            10: ('Minor 7th', 'minor'),
            11: ('Major 7th', 'major'),
            12: ('Octave', 'perfect'),
        }
        name, quality = mapping.get(st % 12, (f'{st}-semitone', 'chromatic'))
        return cls(st, st * 100, name, quality)


class ScaleDegree(Enum):
    """Scale degrees with their ternary stability value."""
    TONIC = (0, "tonic", 1)       # Stable
    SUPERTONIC = (1, "supertonic", 0)   # Passing
    MEDIANT = (2, "mediant", 0)         # Passing
    SUBDOMINANT = (3, "subdominant", 0)  # Passing
    DOMINANT = (4, "dominant", 1)       # Stable
    SUBMEDIANT = (5, "submediant", 0)   # Passing
    LEADING_TONE = (6, "leading_tone", -1)  # Tendency

    def __init__(self, idx: int, name: str, ternary: int):
        self.degree_idx = idx
        self.degree_name = name
        self.ternary = ternary

    @classmethod
    def from_interval(cls, semitones_from_root: int) -> 'ScaleDegree':
        mapping = {
            0: cls.TONIC,
            1: cls.SUPERTONIC,
            2: cls.SUPERTONIC,  # Actually minor 2nd
            3: cls.MEDIANT,     # Minor 3rd
            4: cls.MEDIANT,     # Major 3rd
            5: cls.SUBDOMINANT,
            6: cls.SUBDOMINANT, # Actually tritone/augmented 4th
            7: cls.DOMINANT,    # Perfect 5th
            8: cls.SUBMEDIANT,  # Minor 6th
            9: cls.SUBMEDIANT,  # Major 6th
            10: cls.LEADING_TONE,  # Minor 7th
            11: cls.LEADING_TONE,  # Major 7th
        }
        return mapping.get(semitones_from_root % 12, cls.SUPERTONIC)


def analyze_scale(notes: List[int], payload: dict = None) -> dict:
    """
    Scale/mode analysis for the scale fleet-midi agent (:2161).
    
    Returns mode detection with ternary degree classification.
    """
    if not notes:
        return {'result': 'rest', 'ternary_vector': [0, 0, 0]}
    
    pitch_classes = sorted(set(n % 12 for n in notes))
    
    if len(pitch_classes) < 3:
        return {
            'result': 'insufficient_notes',
            'pitch_classes': pitch_classes,
            'ternary_vector': [0, 0, 0],
        }
    
    # Try each pitch class as tonic
    best_mode = 'unknown'
    best_score = float('inf')
    best_tonic = pitch_classes[0]
    
    mode_patterns = {
        'ionian':     [0, 2, 4, 5, 7, 9, 11],  # Major
        'dorian':     [0, 2, 3, 5, 7, 9, 10],
        'phrygian':   [0, 1, 3, 5, 7, 8, 10],
        'lydian':     [0, 2, 4, 6, 7, 9, 11],
        'mixolydian': [0, 2, 4, 5, 7, 9, 10],
        'aeolian':    [0, 2, 3, 5, 7, 8, 10],  # Natural minor
        'locrian':    [0, 1, 3, 5, 6, 8, 10],
        'harmonic_minor': [0, 2, 3, 5, 7, 8, 11],
        'melodic_minor':  [0, 2, 3, 5, 7, 9, 11],
        'pentatonic_major': [0, 2, 4, 7, 9],
        'pentatonic_minor': [0, 3, 5, 7, 10],
        'blues': [0, 3, 5, 6, 7, 10],
        'whole_tone': [0, 2, 4, 6, 8, 10],
        'octatonic': [0, 2, 3, 5, 6, 8, 9, 11],
    }
    
    for tonic in pitch_classes:
        relative_pcs = sorted((pc - tonic) % 12 for pc in pitch_classes)
        
        for mode, pattern in mode_patterns.items():
            # Check how many notes match the mode pattern
            matches = sum(1 for pc in relative_pcs if pc in pattern)
            non_matches = len(relative_pcs) - matches
            score = non_matches - matches  # Negative is better (more matches)
            
            if score < best_score:
                best_score = score
                best_mode = mode
                best_tonic = tonic
    
    # Detect direction and spread
    mn, mx = min(notes), max(notes)
    direction = 1 if len(notes) > 1 and notes[-1] > notes[0] else (
        -1 if len(notes) > 1 and notes[-1] < notes[0] else 0
    )
    spread = mx - mn
    
    # Classify the mode into a ternary comfort value
    stable_modes = {'ionian', 'aeolian', 'pentatonic_major', 'pentatonic_minor'}
    unstable_modes = {'locrian', 'whole_tone', 'octatonic', 'blues'}
    mode_ternary = 1 if best_mode in stable_modes else (
        -1 if best_mode in unstable_modes else 0
    )
    
    return {
        'result': best_mode,
        'tonic': best_tonic,
        'pitch_classes': relative_pcs if 'relative_pcs' in dir() else pitch_classes,
        'direction': direction,
        'spread': spread,
        'ternary_vector': [0, 1 if direction > 0 else (-1 if direction < 0 else 0), mode_ternary],
    }
