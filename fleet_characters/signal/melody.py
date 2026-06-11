#!/usr/bin/env python3
"""
Port of ternary-muse and agent-motif: Melody contour detection, pattern analysis, and motif tracking.

Provides motif detection, contour analysis, and pattern evolution for melody agents.
"""

from enum import Enum
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
import math


# ─── Contour Types ────────────────────────────────────────────────────

class ContourShape(Enum):
    """Shape of a melody contour segment."""
    FLAT = "flat"
    ASCENDING = "ascending"
    DESCENDING = "descending"
    CONCAVE = "concave"      # peak in middle
    CONVEX = "convex"       # valley in middle
    WILD = "wild"            # chaotic movement


@dataclass
class ContourSegment:
    """A segment of melody contour."""
    start_idx: int
    end_idx: int
    notes: List[int]
    shape: ContourShape
    direction: float  # +1 = up, -1 = down, 0=flat
    range_notes: int  # max - min
    average_pitch: float


@dataclass
class Motif:
    """A recurring musical motif/phrases."""
    note_sequence: List[int]
    intervals: List[int] = field(default_factory=list)
    name: str = ""
    occurrences: int = 1
    first_occurrence: int = 0
    last_occurrence: int = 0
    contour: ContourShape = ContourShape.FLAT
    confidence: float = 0.0

    def __post_init__(self):
        if not self.intervals and len(self.note_sequence) > 1:
            self.intervals = [self.note_sequence[i+1] - self.note_sequence[i] 
                             for i in range(len(self.note_sequence)-1)]


class MelodyContour:
    """Analyze melody contour and track motifs across sequences."""
    
    def __init__(self, min_motif_length: int = 2, max_motif_length: int = 16):
        self.min_motif_length = min_motif_length
        self.max_motif_length = max_motif_length
        self._history: List[Dict] = []
        self._motifs: Dict[str, Motif] = {}
        self._total_sequences = 0

    def analyze_sequence(self, notes: List[int], timestamp: Optional[int] = None) -> dict:
        """Analyze a full melody sequence for contour and motifs."""
        self._total_sequences += 1
        
        if len(notes) < 2:
            return {
                'shape': ContourShape.FLAT,
                'segments': [],
                'phrases': [],
                'motifs': []
            }
            
        # Split into segments and detect contours
        segments = self._split_into_segments(notes)
        contour_type = self._classify_overall_contour(segments)
        phrases = self._extract_phrases(notes)
        
        # Find motifs
        motifs = self._find_motifs(notes)
        
        # Update history
        if timestamp is None:
            timestamp = self._total_sequences
        self._history.append({
            'timestamp': timestamp,
            'notes': notes,
            'contour': contour_type.value,
            'motifs': [m.name for m in motifs.values()]
        })
        
        return {
            'total_notes': len(notes),
            'contour': contour_type.value,
            'segments': [{
                'shape': s.shape.value,
                'direction': s.direction,
                'range': s.range_notes,
                'avg_pitch': round(s.average_pitch, 1)
            } for s in segments],
            'phrases_count': len(phrases),
            'motifs': [{
                'name': m.name,
                'occurrences': m.occurrences,
                'first': m.first_occurrence,
                'last': m.last_occurrence,
                'confidence': round(m.confidence, 2)
            } for m in motifs.values()]
        }

    def _split_into_segments(self, notes: List[int]) -> List[ContourSegment]:
        """Split melody into contiguous contour segments."""
        if len(notes) < 2:
            return []
            
        segments = []
        current_start = 0
        
        # Calculate direction between consecutive notes
        directions = []
        for i in range(1, len(notes)):
            diff = notes[i] - notes[i-1]
            if diff > 0:
                directions.append(1)
            elif diff < 0:
                directions.append(-1)
            else:
                directions.append(0)
                
        # Find segment breaks where direction changes
        for i in range(1, len(directions)):
            if directions[i] != directions[i-1]:
                # Finalize segment current_start -> i
                segment_notes = notes[current_start:i+1]
                seg = ContourSegment(
                    start_idx=current_start,
                    end_idx=i+1,
                    notes=segment_notes,
                    shape=self._get_segment_shape(directions[current_start:i]),
                    direction=sum(directions[current_start:i])/len(directions[current_start:i]),
                    range_notes=max(segment_notes)-min(segment_notes),
                    average_pitch=sum(segment_notes)/len(segment_notes)
                )
                segments.append(seg)
                current_start = i+1
                
        # Add final segment
        if current_start < len(notes):
            segment_notes = notes[current_start:]
            seg = ContourSegment(
                start_idx=current_start,
                end_idx=len(notes),
                notes=segment_notes,
                shape=self._get_segment_shape(directions[current_start:]),
                direction=sum(directions[current_start:])/len(directions[current_start:]) if directions[current_start:] else 0,
                range_notes=max(segment_notes)-min(segment_notes),
                average_pitch=sum(segment_notes)/len(segment_notes)
            )
            segments.append(seg)
            
        return segments

    def _get_segment_shape(self, directions: List[int]) -> ContourShape:
        """Classify the shape of a single contour segment."""
        if not directions:
            return ContourShape.FLAT
            
        total = sum(directions)
        avg = total / len(directions)
        abs_total = sum(abs(d) for d in directions)
        
        if abs_total < 0.1:  # flat
            return ContourShape.FLAT
        elif avg > 0.5:      # mostly up
            return ContourShape.ASCENDING
        elif avg < -0.5:    # mostly down
            return ContourShape.DESCENDING
        else:
            # Check for concave/convex
            if len(directions) >= 3:
                first_dir = directions[0]
                mid_dir = directions[len(directions)//2]
                last_dir = directions[-1]
                if first_dir > 0 and last_dir < 0:
                    return ContourShape.CONCAVE
                elif first_dir < 0 and last_dir > 0:
                    return ContourShape.CONVEX
                    
        return ContourShape.WILD

    def _classify_overall_contour(self, segments: List[ContourSegment]) -> ContourShape:
        """Classify the overall contour of the entire melody."""
        if not segments:
            return ContourShape.FLAT
            
        total_direction = sum(s.direction for s in segments)
        avg_direction = total_direction / len(segments)
        
        if avg_direction > 0.5:
            return ContourShape.ASCENDING
        elif avg_direction < -0.5:
            return ContourShape.DESCENDING
        elif abs(avg_direction) < 0.1:
            return ContourShape.FLAT
        
        return ContourShape.WILD

    def _extract_phrases(self, notes: List[int], min_phrase: int = 2, max_phrase: int = 8) -> List[List[int]]:
        """Extract meaningful melodic phrases."""
        phrases = []
        # Simple phrase detection: group by contour changes
        segments = self._split_into_segments(notes)
        
        current_phrase = []
        for seg in segments:
            current_phrase.extend(seg.notes)
            if len(current_phrase) >= min_phrase:
                phrases.append(current_phrase.copy())
                current_phrase = []
                
        if current_phrase and len(current_phrase) >= min_phrase:
            phrases.append(current_phrase)
            
        return phrases

    def _find_motifs(self, notes: List[int]) -> Dict[str, Motif]:
        """Find and track recurring motifs/sequences."""
        found_motifs: Dict[str, Motif] = {}
        
        # Find all possible motif lengths
        for length in range(self.min_motif_length, min(self.max_motif_length, len(notes)) + 1):
            # Extract all substrings of this length
            for i in range(len(notes) - length + 1):
                motif_candidate = notes[i:i+length]
                motif_key = ",".join(map(str, motif_candidate))
                
                if motif_key in self._motifs:
                    # Update existing motif
                    m = self._motifs[motif_key]
                    m.occurrences += 1
                    m.last_occurrence = i + length
                    m.confidence = min(1.0, m.confidence + 0.1)
                else:
                    # New motif
                    intervals = [motif_candidate[j+1] - motif_candidate[j] for j in range(len(motif_candidate)-1)]
                    contour = self._classify_overall_contour(self._split_into_segments(motif_candidate))
                    m = Motif(
                        note_sequence=motif_candidate,
                        intervals=intervals,
                        name=f"MOTIF-{len(self._motifs)+1}",
                        first_occurrence=i+length,
                        last_occurrence=i+length,
                        contour=contour,
                        confidence=0.5
                    )
                    self._motifs[motif_key] = m
                    
                found_motifs[motif_key] = self._motifs[motif_key]
                
        return found_motifs


def analyze_melody(notes: List[int], payload: dict = None) -> dict:
    """Full melody analysis wrapper for the melody fleet-midi agent (:2174)."""
    analyzer = MelodyContour(
        min_motif_length=payload.get('min_motif', 2) if payload else 2,
        max_motif_length=payload.get('max_motif', 16) if payload else 16
    )
    
    analysis = analyzer.analyze_sequence(notes)
    
    # Add ternary vector
    contour_map = {
        ContourShape.FLAT: 0,
        ContourShape.ASCENDING: 1,
        ContourShape.DESCENDING: -1,
        ContourShape.CONCAVE: 0.5,
        ContourShape.CONVEX: -0.5,
        ContourShape.WILD: 0
    }
    
    ternary_vector = [
        contour_map[ContourShape(analysis['contour'])],
        min(1.0, len(notes) / 10.0),
        sum(1 for m in analysis['motifs'] if m['confidence'] > 0.7) / max(1, len(analysis['motifs']))
    ]
    
    return {
        **analysis,
        'ternary_vector': [round(v, 2) for v in ternary_vector],
        'total_motifs': len(analysis['motifs']),
        'motif_density': round(len(analysis['motifs'])/max(1, len(notes)), 3)
    }


class PatternAnalyzer:
    """Ported from ternary-predict: Prediction-first perception for melody recognition."""
    
    def __init__(self, history_length: int = 100):
        self.history: List[List[int]] = []
        self.history_length = history_length
        self.success_rate: float = 0.0
        
    def predict_next_note(self, current_sequence: List[int]) -> Optional[int]:
        """Predict the next note in a sequence using pattern matching."""
        if len(current_sequence) < 2:
            return None
            
        # Find similar sequences in history
        best_match = None
        best_similarity = 0.0
        target_length = min(len(current_sequence), 8)
        
        window = current_sequence[-target_length:]
        
        for past in self.history:
            if len(past) < target_length:
                continue
                
            # Calculate similarity
            similarity = 0.0
            for i in range(target_length):
                if past[len(past)-target_length+i] == window[i]:
                    similarity += 1
            similarity /= target_length
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = past[len(past)-target_length + target_length]
                
        if best_match and best_similarity > 0.5:
            self.success_rate += 0.1
            return best_match
            
        self.success_rate -= 0.05
        return None
    
    def add_history(self, sequence: List[int]):
        """Add a completed sequence to history."""
        self.history.append(sequence.copy())
        if len(self.history) > self.history_length:
            self.history.pop(0)


__all__ = [
    'MelodyContour', 'ContourSegment', 'ContourShape', 
    'Motif', 'analyze_melody', 'PatternAnalyzer'
]
