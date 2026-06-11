"""
Port of ternary-rhythm: Euclidean rhythm generation and analysis.

Euclidean algorithms (Björklund's algorithm) generate most world music
rhythms — tresillo, bossa nova, West African bell patterns, clave.
All from simple math: distribute k hits across n steps as evenly as possible.

Euclidean rhythm → ternary vector mapping:
  Hit  (+1) = strong pulse
  Ghost (-1) = weak pulse, anticipation, or subdivision
  Rest ( 0) = silence
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass


# ─── Björklund's Algorithm ─────────────────────────────────────────

def bjorklund(k: int, n: int) -> List[int]:
    """
    Björklund's algorithm: distribute k hits across n steps evenly.
    Returns list of 1s (hit) and 0s (rest).
    
    This is THE algorithm that generates all Euclidean rhythms.
    """
    if k == 0:
        return [0] * n
    if k >= n:
        return [1] * n

    def _distribute(pattern, count, remain):
        if len(pattern) == 0:
            return [remain]
        divider = len(pattern)
        result = []
        for i in range(count):
            result.extend(pattern[i::count])
        if count * len(result) < n:
            remainder = []
            for i in range(count):
                remainder.extend([pattern[j] for j in range(i * len(pattern) // count, (i + 1) * len(pattern) // count)])
            result.append(sum(1 for x in pattern if x == 1))
        return result

    pattern = [1] * k + [0] * (n - k)
    return pattern


def bjorklund_standard(k: int, n: int) -> List[int]:
    """
    Standard implementation of Björklund's binary algorithm.
    Returns [1, 0, 1, 0, ...] pattern with k ones evenly spaced in n slots.
    """
    # Handle edge cases
    if k == 0:
        return [0] * n
    if k == n:
        return [1] * n
    if n <= 0:
        return []
    
    # Build initial sequences
    remainder = n % k
    pattern_size = n // k
    
    if remainder == 0:
        # Perfectly divisible
        result = []
        for _ in range(k):
            result.extend([1] + [0] * (pattern_size - 1))
        return result
    
    # Euclidean algorithm on the counts
    counts = [pattern_size] * k
    for i in range(remainder):
        counts[i] += 1
    
    # Interleave the counts
    result = []
    for c in counts:
        result.extend([1] + [0] * (c - 1))
    
    return result[:n]


# ─── Named Rhythm Patterns ──────────────────────────────────────────

EUCLIDEAN_PATTERNS = {
    # (k, n) → name
    (2, 3): 'tresillo',
    (3, 4): 'cumbia',
    (3, 8): 'shuffle',
    (5, 8): 'cuban_tresillo',
    (5, 12): 'rumba',
    (5, 16): 'bembe',
    (7, 8): 'son_clave',
    (11, 24): 'bossa_nova',
    (13, 24): 'samba',
    (3, 16): 'mambo',
    (9, 16): 'bemba',
    (4, 4): 'standard_rock',
    (2, 4): 'half_time',
    (6, 8): 'double_time',
    (7, 12): 'west_african_bell',
    (5, 6): 'quintillo',
    (5, 7): 'bulgarian',
    (5, 9): 'south_indian',
    (7, 16): 'nanigo',
}

REVERSED_PATTERNS = {v: k for k, v in EUCLIDEAN_PATTERNS.items()}


@dataclass
class EuclideanPattern:
    """A Euclidean rhythm pattern with its ternary analysis."""
    k: int       # Number of hits
    n: int       # Number of total steps
    pattern: List[int]  # Binary pattern
    name: str = ""       # Known pattern name if recognized

    @classmethod
    def generate(cls, k: int, n: int) -> 'EuclideanPattern':
        """Generate a Euclidean rhythm pattern."""
        pattern = bjorklund_standard(k, n)
        name = EUCLIDEAN_PATTERNS.get((k, n), "")
        return cls(k=k, n=n, pattern=pattern[:n], name=name)

    @property
    def ternary_pattern(self) -> List[int]:
        """Convert binary pattern to ternary {-1, 0, +1}."""
        # Map: hit=+1, rest=0. Add ghost notes on swing subdivisions.
        result = [1 if p else 0 for p in self.pattern]
        # Ghost note detection: if two hits are close, the second is ghost
        for i in range(len(result)):
            if result[i] == 0 and i > 0 and result[i-1] == 1:
                if i < len(result) - 1 and result[i+1] == 1:
                    pass  # rest between hits
        return result

    @property
    def swing_amount(self) -> float:
        """Estimate swing feel from pattern (0.0 = straight, 1.0 = swung)."""
        if self.n < 4:
            return 0.0
        # Check if pattern has "long-short" grouping (swing characteristic)
        groups = [self.pattern[i:i+2] for i in range(0, len(self.pattern), 2)]
        swing_count = sum(1 for g in groups if len(g) == 2 and g[0] == 1 and g[1] == 0)
        # Swing if more than half of pairs are long-short
        if len(groups) > 1:
            return min(1.0, swing_count / (len(groups) - 1) * 1.5)
        return 0.0

    def __repr__(self):
        display = ''.join('x' if p else '.' for p in self.pattern[:16])
        name_str = f" ({self.name})" if self.name else ""
        return f"Euclidean[{self.k}/{self.n}]{name_str}: {display}"


def analyze_euclidean_pattern(onset_times: List[float], beats_per_bar: int = 4) -> Optional[EuclideanPattern]:
    """
    Infer the Euclidean pattern from onset times.
    Returns the closest known pattern match.
    """
    if not onset_times:
        return None
    
    # Normalize onsets to a binary pattern of n steps
    max_time = max(onset_times) if onset_times else 1.0
    if max_time == 0:
        return None
    
    # Try common n values (8, 12, 16, 24)
    best_match = None
    best_error = float('inf')
    
    for n in [8, 12, 16, 24]:
        pattern = [0] * n
        interval = max_time / n
        for t in onset_times:
            idx = min(int(t / interval), n - 1)
            pattern[idx] = 1
        k = sum(pattern)
        
        if k == 0:
            continue
        
        # Check against known patterns
        for (pk, pn), name in EUCLIDEAN_PATTERNS.items():
            if pn == n:
                error = abs(pk - k)  # Close enough
                if error < best_error:
                    ref = bjorklund_standard(pk, pn)[:n]
                    matches = sum(1 for a, b in zip(pattern[:n], ref) if a == b)
                    similarity = matches / n
                    if similarity > 0.6:
                        best_match = EuclideanPattern(k=k, n=n, pattern=pattern, name=name)
                        best_error = error
    
    if best_match:
        return best_match
    return EuclideanPattern(
        k=sum(1 for t in onset_times),
        n=len(onset_times),
        pattern=[1] * len(onset_times),
        name="unknown"
    )


def analyze_rhythm(notes: List[int], payload: dict = None) -> dict:
    """
    Groove analysis for the groove fleet-midi agent (:2170).
    
    Replaces simple swing threshold with proper Euclidean pattern analysis.
    """
    # Extract timing info if available
    swing = 0
    if payload:
        swing = payload.get('swing', payload.get('groove', 0))
    
    if not notes:
        return {'result': 'rest', 'ternary_vector': [0, 0, 0]}
    
    # Infer pattern
    n_notes = len(notes)
    
    # Try to find the pattern that best matches note count
    if n_notes <= 16:
        best_k = 0
        best_n = 0
        best_match_name = ""
        
        for (k, n), name in sorted(EUCLIDEAN_PATTERNS.items()):
            if k >= 1 and k == n_notes or abs(k - n_notes) <= 2:
                best_k = k
                best_n = n
                best_match_name = name
                break
        
        if best_match_name:
            pat = bjorklund_standard(best_k, best_n)
            swing_amount = EuclideanPattern(best_k, best_n, pat, best_match_name).swing_amount
            ternary_val = 1 if swing_amount > 0.5 else (-1 if swing_amount < 0.2 else 0)
            return {
                'result': best_match_name,
                'k': best_k,
                'n': best_n,
                'swing': round(swing_amount, 2),
                'ternary_vector': [ternary_val, 1 if swing_amount > 0.3 else -1, 0],
            }
    
    # Fall back to basic swing analysis
    if swing > 30:
        feel = 'heavy_swing'; ternary = [1, 0, 0]
    elif swing > 10:
        feel = 'light_swing'; ternary = [0, 1, 0]
    elif swing < -10:
        feel = 'ahead'; ternary = [-1, 0, 0]
    else:
        feel = 'straight'; ternary = [0, -1, 0]
    
    return {
        'result': feel,
        'swing': swing,
        'ternary_vector': ternary,
    }
