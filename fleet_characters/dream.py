"""
Dream cycle system for AI fleet agents, ported from agent-dream-cycle Rust crate.

Offline memory consolidation — REM sleep for agents. Agents that never pause
to reflect accumulate raw experiences but never extract patterns.

The dream cycle pauses normal execution, replays failures at high speed,
and compresses recent experiences into long-term patterns.
"""

import math
from typing import List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class Experience:
    """A record of a past interaction that may be replayed during dreaming."""
    id: int
    input_: str
    output: str
    success: bool
    reward: float
    embedding: List[float]
    tick: int

    def __post_init__(self):
        if not self.embedding:
            self.embedding = [self.reward]

    @classmethod
    def simple(cls, id: int, input_: str, success: bool, reward: float, tick: int) -> 'Experience':
        """Create a simple experience with a scalar embedding."""
        return cls(id=id, input_=input_, output="", success=success,
                    reward=reward, embedding=[reward], tick=tick)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'input': self.input_[:80],
            'output': self.output[:80],
            'success': self.success,
            'reward': self.reward,
            'tick': self.tick,
        }


@dataclass
class ConsolidatedPattern:
    """Compressed pattern extracted from multiple experiences."""
    description: str
    avg_reward: float
    sample_count: int
    tags: List[str]
    is_success_pattern: bool

    def to_dict(self) -> dict:
        return {
            'description': self.description,
            'avg_reward': round(self.avg_reward, 2),
            'sample_count': self.sample_count,
            'tags': self.tags,
            'type': 'success' if self.is_success_pattern else 'failure',
        }


@dataclass
class FailureReplayResult:
    """Result of a failure replay session."""
    failures_replayed: List[Experience] = field(default_factory=list)
    patterns_found: List[ConsolidatedPattern] = field(default_factory=list)
    suggestions: List[Tuple[str, str]] = field(default_factory=list)
    improvement_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            'failures_replayed': len(self.failures_replayed),
            'patterns_found': [p.to_dict() for p in self.patterns_found],
            'suggestions': [{'what': s[0], 'why': s[1]} for s in self.suggestions],
            'improvement_score': round(self.improvement_score, 2),
        }


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    min_len = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(min_len))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


@dataclass
class MemoryConsolidation:
    """Compresses recent experiences into long-term patterns."""
    experiences: List[Experience] = field(default_factory=list)
    patterns: List[ConsolidatedPattern] = field(default_factory=list)
    min_experiences: int = 3

    def add_experience(self, exp: Experience):
        self.experiences.append(exp)

    def failures(self) -> List[Experience]:
        return [e for e in self.experiences if not e.success]

    def successes(self) -> List[Experience]:
        return [e for e in self.experiences if e.success]

    def consolidate(self) -> int:
        """Run consolidation. Returns number of new patterns created."""
        if len(self.experiences) < self.min_experiences:
            return 0

        failure_data = [e.reward for e in self.experiences if not e.success]
        success_data = [e.reward for e in self.experiences if e.success]
        rewards = sorted([e.reward for e in self.experiences])
        new_patterns = 0

        # Pattern: low-reward failures
        if failure_data:
            avg = sum(failure_data) / len(failure_data)
            self.patterns.append(ConsolidatedPattern(
                description=f"Low-reward failure pattern (avg: {avg:.2f})",
                avg_reward=avg,
                sample_count=len(failure_data),
                tags=["failure", "low-reward"],
                is_success_pattern=False,
            ))
            new_patterns += 1

        # Pattern: high-reward successes
        if success_data:
            avg = sum(success_data) / len(success_data)
            self.patterns.append(ConsolidatedPattern(
                description=f"High-reward success pattern (avg: {avg:.2f})",
                avg_reward=avg,
                sample_count=len(success_data),
                tags=["success", "high-reward"],
                is_success_pattern=True,
            ))
            new_patterns += 1

        # Pattern: reward distribution quartiles
        if len(rewards) >= 4:
            q1 = rewards[len(rewards) // 4]
            q3 = rewards[3 * len(rewards) // 4]
            bottom_count = sum(1 for r in rewards if r <= q1)
            self.patterns.append(ConsolidatedPattern(
                description=f"Reward distribution: Q1={q1:.2f}, Q3={q3:.2f}",
                avg_reward=(q1 + q3) / 2.0,
                sample_count=bottom_count,
                tags=["distribution", "quartile"],
                is_success_pattern=False,
            ))
            new_patterns += 1

        return new_patterns

    def __len__(self) -> int:
        return len(self.experiences)

    def to_dict(self) -> dict:
        return {
            'total_experiences': len(self.experiences),
            'failures': len(self.failures()),
            'successes': len(self.successes()),
            'patterns': [p.to_dict() for p in self.patterns],
        }


@dataclass
class FailureReplay:
    """Replays failures in embedding space to find improvement opportunities."""
    speed: float = 2.0

    def replay(self, consolidation: MemoryConsolidation) -> FailureReplayResult:
        """Replay failures and find closest success matches."""
        failures = consolidation.failures()
        successes = consolidation.successes()

        if not failures:
            return FailureReplayResult()

        result = FailureReplayResult(failures_replayed=failures)
        avg_failure_reward = sum(e.reward for e in failures) / len(failures)

        for failure in failures:
            # Find closest success by cosine similarity
            best_match = None
            best_sim = float('-inf')
            for success in successes:
                sim = cosine_similarity(failure.embedding, success.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_match = success

            if best_match and best_sim > 0.3:
                result.suggestions.append((
                    f"Input '{failure.input_[:40]}' (r={failure.reward:.1f}) → try '{best_match.output[:40]}'",
                    f"Similar success: '{best_match.input_[:40]}' (r={best_match.reward:.1f})",
                ))

        avg_success_reward = (sum(e.reward for e in successes) / len(successes)
                              if successes else 0.0)
        result.improvement_score = (avg_success_reward - avg_failure_reward) * self.speed

        return result


@dataclass
class ConsolidationReport:
    """Report generated after a dream cycle completes."""
    experiences_processed: int
    failures_replayed: int
    new_patterns: int
    improvement_score: float
    suggestions_count: int
    duration_ticks: int
    summary: str

    @classmethod
    def from_results(cls, exp_count: int, fail_count: int, new_patterns: int,
                     replay_result: FailureReplayResult, duration: int) -> 'ConsolidationReport':
        summary = (f"Dream cycle complete: processed {exp_count} experiences, "
                   f"replayed {fail_count} failures, learned {new_patterns} new patterns. "
                   f"Improvement: {replay_result.improvement_score:.2f}")
        return cls(
            experiences_processed=exp_count,
            failures_replayed=fail_count,
            new_patterns=new_patterns,
            improvement_score=replay_result.improvement_score,
            suggestions_count=len(replay_result.suggestions),
            duration_ticks=duration,
            summary=summary,
        )

    def to_dict(self) -> dict:
        return {
            'experiences_processed': self.experiences_processed,
            'failures_replayed': self.failures_replayed,
            'new_patterns': self.new_patterns,
            'improvement_score': round(self.improvement_score, 2),
            'suggestions_count': self.suggestions_count,
            'duration_ticks': self.duration_ticks,
            'summary': self.summary,
        }


@dataclass
class DreamCycle:
    """Orchestrator — pauses agent, replays failures, consolidates memories."""
    consolidation: MemoryConsolidation = field(default_factory=MemoryConsolidation)
    replay: FailureReplay = field(default_factory=FailureReplay)
    is_dreaming: bool = False
    cycles_completed: int = 0
    reports: List[ConsolidationReport] = field(default_factory=list)

    def add_experience(self, exp: Experience):
        self.consolidation.add_experience(exp)

    def dream(self, duration_ticks: int = 10) -> ConsolidationReport:
        """Enter dream state: consolidate + replay."""
        self.is_dreaming = True
        exp_count = len(self.consolidation)
        fail_count = len(self.consolidation.failures())
        replay_result = self.replay.replay(self.consolidation)
        new_patterns = self.consolidation.consolidate()
        report = ConsolidationReport.from_results(exp_count, fail_count,
                                                   new_patterns, replay_result,
                                                   duration_ticks)
        self.is_dreaming = False
        self.cycles_completed += 1
        self.reports.append(report)
        return report

    @property
    def last_report(self) -> Optional[ConsolidationReport]:
        return self.reports[-1] if self.reports else None

    def to_dict(self) -> dict:
        return {
            'is_dreaming': self.is_dreaming,
            'cycles_completed': self.cycles_completed,
            'consolidation': self.consolidation.to_dict() if self.consolidation else {},
            'last_report': self.last_report.to_dict() if self.last_report else None,
        }


@dataclass
class DreamScheduler:
    """Scheduler for periodic dream cycles."""
    interval: int = 100  # Dream every N ticks
    current_tick: int = 0
    dream_cycle: DreamCycle = field(default_factory=DreamCycle)
    dream_ticks: List[int] = field(default_factory=list)

    def tick(self) -> Optional[ConsolidationReport]:
        """Advance one tick. Returns report if dream triggered."""
        self.current_tick += 1
        if self.current_tick > 0 and self.current_tick % self.interval == 0:
            self.dream_ticks.append(self.current_tick)
            return self.dream_cycle.dream(self.interval)
        return None

    def to_dict(self) -> dict:
        return {
            'interval': self.interval,
            'current_tick': self.current_tick,
            'dream_ticks': self.dream_ticks[-5:] if self.dream_ticks else [],
            'next_dream_in': self.interval - (self.current_tick % self.interval),
            'dream_cycle': self.dream_cycle.to_dict(),
        }
