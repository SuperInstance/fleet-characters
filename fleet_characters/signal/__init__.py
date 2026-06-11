"""
Signal processing and music cognition — Python ports from Cluster 4 Rust crates.

Each module ports a key Cluster 4 crate's semantics to pure Python,
replacing the heuristic-based algorithms in fleet-agent.py with
proper music theory and signal processing.

Modules:
- chord.py    — Port of ternary-music (TernaryChord, tension curves)
- scale.py    — Port of ternary-temperament (interval analysis)
- voicing.py  — Port of ternary-counterpoint (species counterpoint)
- rhythm.py   — Port of ternary-rhythm (Euclidean/Björklund patterns)
- melody.py   — Port of ternary-muse (pattern evolution)
- predict.py  — Port of ternary-predict (prediction-first perception)
"""

from .chord import TernaryChord, chord_tension, analyze_chord
from .scale import ScaleDegree, analyze_scale, Interval
from .voicing import VoiceState, SpeciesCounterpoint, analyze_voice_leading
from .rhythm import EuclideanPattern, analyze_rhythm
from .melody import MelodyContour, PatternAnalyzer, analyze_melody, Motif, ContourSegment, ContourShape

__all__ = [
    'TernaryChord', 'chord_tension', 'analyze_chord',
    'ScaleDegree', 'analyze_scale', 'Interval',
    'VoiceState', 'SpeciesCounterpoint', 'analyze_voice_leading',
    'EuclideanPattern', 'analyze_rhythm',
    'MelodyContour', 'PatternAnalyzer', 'analyze_melody', 'Motif', 'ContourSegment', 'ContourShape',
]
