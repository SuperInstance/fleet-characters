"""
Port of ternary-counterpoint: species counterpoint voice leading analysis.

Five species of counterpoint encoded as ternary {-1, 0, +1} constraints:
  +1 = Acceptable motion
   0 = Context-dependent (acceptable in some positions)
  -1 = Forbidden (parallel fifths, direct octaves, etc.)
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass

# ─── Interval constants ──────────────────────────────────────────────

UNISON = 0
MINOR_SECOND = 1
MAJOR_SECOND = 2
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

PERFECT_INTERVALS = {UNISON, PERFECT_FOURTH, PERFECT_FIFTH, OCTAVE}
IMPERFECT_INTERVALS = {MINOR_THIRD, MAJOR_THIRD, MINOR_SIXTH, MAJOR_SIXTH}
DISSONANT_INTERVALS = {MINOR_SECOND, MAJOR_SECOND, TRITONE, MINOR_SEVENTH, MAJOR_SEVENTH}


# ─── Motion Types ────────────────────────────────────────────────────

class Motion:
    """Types of voice motion between two notes."""
    PARALLEL = "parallel"        # Both voices move same direction, same interval
    SIMILAR = "similar"          # Both move same direction, different interval
    CONTRARY = "contrary"        # Opposite directions
    OBLIQUE = "oblique"          # One stays, one moves


def classify_motion(voice1_a: int, voice1_b: int, voice2_a: int, voice2_b: int) -> str:
    """Classify the motion between two voices."""
    d1 = voice1_b - voice1_a
    d2 = voice2_b - voice2_a
    
    if d1 == 0 and d2 == 0:
        return Motion.OBLIQUE
    if d1 == 0 or d2 == 0:
        return Motion.OBLIQUE
    
    if (d1 > 0 and d2 > 0) or (d1 < 0 and d2 < 0):
        # Same direction
        interval_a = abs(voice1_a - voice2_a)
        interval_b = abs(voice1_b - voice2_b)
        if abs(d1) == abs(d2) or interval_a == interval_b:
            return Motion.PARALLEL
        return Motion.SIMILAR
    
    return Motion.CONTRARY


# ─── Counterpoint Rules ──────────────────────────────────────────────

def check_parallel_perfect(voice1: List[int], voice2: List[int]) -> List[Tuple[int, str]]:
    """Forbidden: parallel perfect intervals (unison, fifth, octave)."""
    violations = []
    for i in range(1, min(len(voice1), len(voice2))):
        prev_int = abs(voice1[i-1] - voice2[i-1]) % 12
        curr_int = abs(voice1[i] - voice2[i]) % 12
        
        motion = classify_motion(voice1[i-1], voice1[i], voice2[i-1], voice2[i])
        
        if motion == Motion.PARALLEL:
            if prev_int in PERFECT_INTERVALS and curr_int == prev_int:
                violations.append((i, f"parallel perfect interval ({prev_int} semitones)"))
    
    return violations


def check_direct_octave(voice1: List[int], voice2: List[int]) -> List[Tuple[int, str]]:
    """Forbidden: similar motion into a perfect interval."""
    violations = []
    for i in range(1, min(len(voice1), len(voice2))):
        curr_int = abs(voice1[i] - voice2[i]) % 12
        motion = classify_motion(voice1[i-1], voice1[i], voice2[i-1], voice2[i])
        
        if motion == Motion.SIMILAR and curr_int in PERFECT_INTERVALS:
            violations.append((i, f"direct (similar) motion into {curr_int}-semitone interval"))
    
    return violations


def check_voice_crossing(voice1: List[int], voice2: List[int]) -> List[Tuple[int, str]]:
    """Forbidden: voices crossing each other."""
    violations = []
    for i in range(len(voice1)):
        if (voice1[i] > voice2[i]):  # Assuming voice1 should be higher
            violations.append((i, f"voice crossing at position {i}"))
    return violations


def check_range(notes: List[int], low: int, high: int) -> List[Tuple[int, str]]:
    """Check if notes are within a reasonable range."""
    violations = []
    for i, n in enumerate(notes):
        if n < low:
            violations.append((i, f"note {n} below range {low}"))
        elif n > high:
            violations.append((i, f"note {n} above range {high}"))
    return violations


def voice_leading_score(voice1: List[int], voice2: List[int]) -> float:
    """
    Score voice leading quality (1.0 = perfect, 0.0 = terrible).
    
    Factors:
    - Parallel perfect intervals (-0.5 per violation)
    - Direct octaves/fifths (-0.3 per violation)
    - Voice crossing (-0.2 per violation)
    - Large leaps (-0.1 per leap > 8 semitones)
    """
    score = 1.0
    score -= len(check_parallel_perfect(voice1, voice2)) * 0.5
    score -= len(check_direct_octave(voice1, voice2)) * 0.3
    score -= len(check_voice_crossing(voice1, voice2)) * 0.2
    
    for i in range(1, len(voice1)):
        leap = abs(voice1[i] - voice1[i-1])
        if leap > 8:
            score -= 0.1
    
    return max(0.0, min(1.0, score))


@dataclass
class VoiceState:
    """Current state of a voice in the harmonic texture."""
    notes: List[int]           # Current notes active
    range_low: int = 48        # C3 default
    range_high: int = 84       # C6 default
    voice_name: str = "Voice"

    @property
    def is_active(self) -> bool:
        return len(self.notes) > 0

    @property
    def average(self) -> float:
        return sum(self.notes) / len(self.notes) if self.notes else 0


@dataclass
class SpeciesCounterpoint:
    """
    First species counterpoint (note-against-note) analysis.
    
    Checks voice pairs for counterpoint rule violations and returns
    a ternary compatibility score.
    """
    voices: List[VoiceState]

    def analyze_pair(self, v1_idx: int, v2_idx: int) -> dict:
        """Analyze a pair of voices for counterpoint quality."""
        v1 = self.voices[v1_idx]
        v2 = self.voices[v2_idx]

        if not v1.is_active or not v2.is_active:
            return {'voice_pair': f"{v1.voice_name} × {v2.voice_name}",
                    'quality': 'inactive', 'ternary': 0}

        # Build note sequences for analysis
        # In real counterpoint, each voice has a melody;
        # here we use sorted notes as a proxy
        seq1 = sorted(v1.notes)
        seq2 = sorted(v2.notes)

        if len(seq1) < 2 or len(seq2) < 2:
            # Monophonic analysis: just check current interval
            curr_int = abs(min(v1.notes) - min(v2.notes)) % 12
            if curr_int in DISSONANT_INTERVALS:
                quality = 'dissonant'
                ternary = -1
            elif curr_int in IMPERFECT_INTERVALS:
                quality = 'consonant_imperfect'
                ternary = 0
            else:
                quality = 'consonant_perfect'
                ternary = 1
            return {'voice_pair': f"{v1.voice_name} × {v2.voice_name}",
                    'quality': quality, 'ternary': ternary}

        # Score counterpoint quality
        score = voice_leading_score(seq1, seq2)
        
        if score > 0.8:
            quality = 'excellent'
            ternary = 1
        elif score > 0.6:
            quality = 'good'
            ternary = 0
        elif score > 0.3:
            quality = 'acceptable'
            ternary = 0
        else:
            quality = 'poor'
            ternary = -1

        violations = (check_parallel_perfect(seq1, seq2) +
                      check_direct_octave(seq1, seq2) +
                      check_voice_crossing(seq1, seq2))

        return {
            'voice_pair': f"{v1.voice_name} × {v2.voice_name}",
            'quality': quality,
            'score': round(score, 2),
            'ternary': ternary,
            'violations': [v[1] for v in violations[:5]],
        }

    def analyze_all(self) -> dict:
        """Analyze all pairs in the texture."""
        pairs = []
        for i in range(len(self.voices)):
            for j in range(i + 1, len(self.voices)):
                pairs.append(self.analyze_pair(i, j))

        avg_score = sum(p.get('score', 0.5) for p in pairs) / len(pairs) if pairs else 0
        overall = 1 if avg_score > 0.7 else (-1 if avg_score < 0.4 else 0)

        return {
            'pairs': pairs,
            'avg_score': round(avg_score, 2),
            'overall_ternary': overall,
            'voice_count': len(self.voices),
        }


def analyze_voice_leading(notes: List[int], payload: dict = None) -> dict:
    """
    Voice leading analysis for the voicing fleet-midi agent (:2162).
    
    Replaces brightness heuristic with proper counterpoint constraints.
    Returns ternary compatibility and voice quality metrics.
    """
    if not notes:
        return {'result': 'rest', 'ternary_vector': [0, 0, 0]}

    # Group notes by potential voice
    # Heuristic: each octave range is a "voice"
    voices = {}
    for n in notes:
        octave = n // 12
        if octave not in voices:
            voices[octave] = []
        voices[octave].append(n)

    voice_states = [VoiceState(names, voice_name=f"Voice_{octave}")
                    for octave, names in sorted(voices.items())]

    cp = SpeciesCounterpoint(voice_states)
    analysis = cp.analyze_all()

    # Brightness heuristic (preserved from original)
    root = min(notes) % 12
    intervals = sorted((n % 12 for n in notes))
    unique = [(i - root) % 12 for i in intervals if (i - root) % 12 in range(12)]
    brightness = sum(1 for iv in unique if iv in (0, 4, 7, 11))

    return {
        'result': analysis['quality_good'] if analysis.get('pairs') else 'analyzed',
        'brightness': brightness,
        'voice_count': analysis['voice_count'],
        'avg_counterpoint_score': analysis['avg_score'],
        'voice_pairs': [{
            'pair': p['voice_pair'],
            'quality': p.get('quality', 'unknown'),
            'ternary': p.get('ternary', 0),
        } for p in analysis.get('pairs', [])],
        'ternary_vector': [analysis['overall_ternary'],
                          1 if brightness >= 3 else (-1 if brightness <= 1 else 0),
                          0],
    }
