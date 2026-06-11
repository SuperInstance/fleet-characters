# Cluster 4: Signal Processing & Music Cognition — Integration Report

**Study Date:** 2026-06-11
**Repos Studied:** 36
**Method:** Claude Code (claude-sonnet-4) — README + src/lib.rs analysis
**Fleet Target:** 16 fleet-midi agents, fleet-agent.py

---

## Executive Summary

Cluster 4 is a complete **ternary audio processing and music cognition ecosystem** — 36 Rust crates implementing everything from raw waveform generation to sophisticated music theory analysis using the balanced ternary {-1, 0, +1} formalism.

**Core thesis:** Audio and music are *fundamentally ternary* — tension/release, hit/silence/ghost, predicted/unexpected. Three values are optimal for representing musical information, and these crates prove it mathematically.

---

## Most Significant Discoveries

### ternary-music — Music theory reduced to ternary essential
- **Key types:** `TernaryChord` (tension/neutral/resolution), `ScaleDegree` (stable/passing/tendency)
- **Key functions:** `tension_curve()` captures emotional arc in sequences like `[1, -1, 1]` (ii-V-I)
- **Key insight:** Instead of classifying 24+ chord qualities, ternary-music reduces to 3 tension states:
  - `+1` = Tension (dominant, augmented, dimished)
  - `0` = Neutral (tonic, sus4, sus2)
  - `-1` = Resolution (subdominant, relative minor)
- **Integration Potential:**
  - **HIGH** — Directly replaces chord agent's heuristic (major/minor/power classification) with proper ternary music theory
  - The chord agent's ternary vector `[+1|0|-1, 0, 0]` maps exactly to ternary-music's chord tension model
  - Scale degree classification (stable=+1, passing=0, tendency=-1) maps to scale agent output

### ternary-signals — Fixed-point signal processing
- **Key types:** Q16.16 fixed-point format, `SignalFrame`, `Spectrum`
- **Key functions:** Integer-only DFT/IDFT, autocorrelation, spectral density, frequency detection
- **Key insight:** Full integer-only signal processing—no FPU needed. Suitable for `no_std` embedded environments
- **Integration Potential:**
  - **MEDIUM** — Pre-processing layer for MIDI input before it reaches fleet agents
  - If OpenSMILE bridge sends raw spectral data, ternary-signals can extract features
  - Not directly replacing agent algorithms, but could improve input signal quality

### ternary-kuramoto — Proof of ternary synchronization limits
- **Key types:** `KuramotoOscillator`, `PhaseState`, `OrderParameter`
- **Key finding:** Proves ternary systems *cannot fully synchronize*
  - 120° sectors create a "1/3 dead zone" that absorbs coherence
  - The 0 state acts as a "phase insulator"
- **Integration Potential:**
  - **HIGH** — Explains why the 16 fleet-midi agents will never perfectly agree
  - The "1/3 dead zone" is a *feature*, not a bug — creative tension between agents
  - Conductor should expect ~33% disagreement between agents on any given cue
  - Conservation law implications: Σ(ternary) ≠ 0 due to phase insulator effect

### ternary-predict — Prediction-first perception
- **Key types:** `Predictor`, `Surprise`, `AdaptiveDeadband`
- **Key insight:** Sensors report only *surprises* — prediction errors that exceed an adaptive threshold
  - Models human perception: "you don't feel your shoes, you feel the ground through them"
  - Deadband widens for reliable signals, narrows for unreliable ones
- **Integration Potential:**
  - **HIGH** — Replace "send everything" agent polling with prediction-driven updates
  - An agent that's "bored" (nothing surprising) polls less — saves CPU
  - An agent that's "surprised" (unexpected input) becomes more attentive
  - Character wisdom stat could map to deadband width — wise agents are harder to surprise

### ternary-muse — Creative inspiration engine
- **Key types:** `Pattern`, `AestheticScore`, `Genome`, `Fitness`
- **Key functions:** Genetic algorithm evolving patterns based on aesthetic scoring
- **Key insight:** "Creativity in a constrained system: the constraints ARE the creativity"
- **Integration Potential:**
  - **MEDIUM** — Creative mode for agents: ask "what would be the most interesting response?"
  - New `/improvise` endpoint per agent for non-deterministic creative output
  - Backs the narrative arc: "and then I tried something new..."

### ternary-rhythm — Euclidean rhythm generator
- **Key types:** `EuclideanPattern`, `Bjorklund`, `OnsetVector`
- **Key functions:** Björklund's algorithm, Euclidean string generation
- **Key insight:** Euclidean algorithms generate most world music rhythms — tresillo, bossa nova, West African bell patterns
- **Integration Potential:**
  - **HIGH** — Replace the groove agent's simple swing heuristic with proper Euclidean rhythm analysis
  - Euclidean patterns directly map to ternary vectors: hit=+1, ghost=-1, rest=0
  - Groove agent becomes pattern-matched to known world rhythms

### ternary-temperament — Musical tuning systems
- **Key types:** `Temperament`, `Interval`, `Cents`, `JustIntonationRatio`
- **Key functions:** Equal temperament, just intonation, Pythagorean tuning conversions
- **Integration Potential:**
  - **MEDIUM** — The scale agent inputs note-on events but assumes 12-TET. ternary-temperament enables microtonal analysis
  - Register agent's brightness detection gains temperament awareness

### ternary-ear — Auditory perception model
- **Key types:** `AuditoryScene`, `Stream`, `AuditoryObject`
- **Key functions:** Stream segregation (Bregman's model), auditory object grouping
- **Integration Potential:**
  - **HIGH** — The fleet needs scene-level understanding, not just per-cue responses
  - Conductor currently routes single cues; ternary-ear enables "what is the listener hearing?"
  - Stream segregation = which agent's output the listener is tracking

### ternary-polyrhythm — Polyrhythm analysis
- **Key types:** `Polyrhythm`, `TimeSignature`, `Subdivision`
- **Key functions:** Polyrhythm resolution, polymeter detection, simultaneous time signatures
- **Integration Potential:**
  - **MEDIUM** — Groove and tempo agents currently handle single time signatures. Polyrhythm enables 3:4, 5:4, 7:8 and complex time

### ternary-counterpoint — Classical voice leading
- **Key types:** `SpeciesCounterpoint`, `VoicePair`, `Motion`
- **Key functions:** 5 species analysis, parallel/perpendicular/contrary motion detection
- **Integration Potential:**
  - **HIGH** — Directly replaces voicing agent's brightness heuristic with proper species counterpoint validation
  - Bass + voicing agents get voice leading constraints: avoid parallel fifths/octaves
  - New `/counterpoint` endpoint for composer-mode analysis

---

## Integration Map: What Replaces What

| Fleet Agent | Current Algorithm | Cluster 4 Replacement | Priority |
|-------------|-------------------|----------------------|----------|
| chord | Major/minor/power heuristic | ternary-music TernaryChord | 🔴 HIGH |
| scale | Mode guess (pentatonic/diatonic/chromatic) | ternary-music ScaleDegree + ternary-temperament | 🔴 HIGH |
| voicing | Brightness heuristic | ternary-counterpoint species analysis + ternary-ear stream segregation | 🔴 HIGH |
| tempo | BPM threshold (fast/moderate/slow) | ternary-tempo time perception + ternary-polyrhythm | 🟡 MEDIUM |
| groove | Swing threshold | ternary-rhythm Euclidean pattern matching | 🔴 HIGH |
| expression | Intensity threshold | ternary-predict surprise detection | 🟡 MEDIUM |
| dynamics | Direction threshold | ternary-signals envelope detection | 🟡 MEDIUM |
| arp | Direction check | ternary-motion trajectory analysis | 🟢 LOW |
| melody | Contour detection | ternary-muse pattern evolution + ternary-motif | 🟡 MEDIUM |
| bass | Step pattern | ternary-counterpoint bass constraints + ternary-kuramoto phase sync | 🟡 MEDIUM |
| pan | Position threshold | ternary-spiral spatial movement | 🟢 LOW |
| modulation | Rate threshold | ternary-resonance harmonic modulation + ternary-echo delay | 🟡 MEDIUM |
| fx | Wet/dry threshold | ternary-warp transform processing | 🟢 LOW |
| register | Average + brightness | ternary-signals spectral density + ternary-observatory range detection | 🟢 LOW |

---

## The Phase Insulator Effect

The most profound discovery from Cluster 4: **the ternary kuramoto model proves that ternary systems cannot fully synchronize.** The 120° sectors create a 1/3 dead zone. The 0 state acts as a phase insulator.

**Implications for the fleet:**
- The conductor should **never expect consensus** across all 16 agents
- ~33% disagreement is *mathematically guaranteed*, not a bug
- This is the source of creative tension in the system
- The character system's `integration_score` should account for this — agents are inherently designed to not-synchronize
- Conservation law correction: Σ(ternary_vector) for the fleet will never be 0 — there's always a residue due to phase insulation
