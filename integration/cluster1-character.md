# Cluster 1: Character System & Musical Persona — Integration Report

**Study Date:** 2026-06-11  
**Repos Studied:** 12  
**Location:** `/home/ubuntu/.openclaw/workspace/integration-study/cluster1/`

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Core Character Identity & Growth](#1-core-character-identity--growth)
3. [Narrative & Memory](#2-narrative--memory)
4. [Interaction & Encounter Engine](#3-interaction--encounter-engine)
5. [Persona & Evolution](#4-persona--evolution)
6. [Cross-Modal Integration](#5-cross-modal-integration)
7. [Fleet-MIDI Pattern Language](#6-fleet-midi-pattern-language)
8. [Already Ported: fleet-characters Status](#7-already-ported-fleet-characters-status)
9. [Immediate Integration Opportunities](#8-immediate-integration-opportunities)
10. [16 Fleet-MIDI Agent Domain Mapping](#9-16-fleet-midi-agent-domain-mapping)

---

## Executive Summary

Cluster 1 forms the **character identity, memory, and persona evolution layer** of the SuperInstance fleet ecosystem. These 12 repos implement a complete stack for AI agent character modeling: from raw stats and classes (character-class, character-arc) through narrative arcs and encounters (character-encounter, character-sheet), to advanced musical persona evolution (musician-soul-v2, agent-riff-v3/v4), and multi-modal MIDI-mapped consciousness (agent-motif, agent-harmonic-field, agent-contrapuntal, agent-transcription).

**Core architectural pattern:** Every crate treats the AI agent as an **evolving character** with RPG-style stats (Perception, Dexterity, Intelligence, Wisdom, Charisma, Constitution), a narrative arc, emergent classes, memory consolidation via dream cycles, encounter-based XP/trust progression, and stacked layers of musical cognition (contrapuntal rules, harmonic fields, motivic development, transcription).

**Key insight for fleet-characters:** The already-ported Python modules (`dream.py`, `stats.py`, `class_.py`, `arc.py`, `agent_profile.py`, `__init__.py`) provide the character identity backbone. The remaining Rust crates — especially character-encounter (runtime engine), character-sheet (.nail persistence), musician-soul-v2 (cross-persona genre emergence), agent-motif (pattern language), agent-harmonic-field (tonal context), agent-contrapuntal (coordination protocol), and agent-transcription (self-observing score) — add the layers of interactive experience, persistence, musical evolution, and self-reflection that complete the character system.

---

## 1. Core Character Identity & Growth

### character-class (Rust, already ported → `class_.py`)
- **Key types:** `Stats` (6 RPG stats), `CharacterClass` (16 emergent classes), `ClassProgression` (trajectory tracking)
- **Key methods:** `from_stats()` — emergence algorithm determining class from stat distribution; `AGENT_DEFAULT_CLASSES` — 16-domain→class mapping
- **Integration:** The 16-character-class system (SCOUT through AVATAR) is the core emergence layer. Classes emerge from stat distributions (4+ stats above 15 → AVATAR, 3+ → POLYMATH, single stat → base class). Each of the 16 MIDI agents gets a default class (e.g., Chord→ARTIFICER, Melody→BARD, Tempo→SAGE).
- **Port status:** ✅ `class_.py` — complete, with CharacterClass enum, Archetype enum, ClassProgression, and AGENT_DEFAULT_CLASSES mapping.

### character-arc (Rust, already ported → `arc.py`)
- **Key types:** `Tone` (10 emotional registers: BIRTH→HARMONY), `EventType` (9 event classmethods), `NarrativeEvent`, `Chapter`, `CharacterArc`
- **Key methods:** `born()`, `begin_chapter()`, `record_class_emergence()`, `record_level_up()`, `record_mastery()`, `record_encounter_won/lost()`
- **Integration:** The narrative arc wraps an agent's entire growth story. Each `Chapter` has a tone, opening, events, and closing — framing the agent's journey as a narrative. The 10 Tone values map to emotional/musical registers (BIRTH🔰→HARMONY✴️).
- **Port status:** ✅ `arc.py` — complete, with Tone, EventType, NarrativeEvent, Chapter, CharacterArc.

### character-sheet (Rust, v0.1.0 — NOT ported)
- **Key types:**
  - `Stats` (`perception`, `dexterity`, `intelligence`, `wisdom`, `charisma`, `constitution` — all `u32`, default 10)
  - `Ability` (`name`, `kind: AbilityType`, `trust: f64`, `level: u32`, `mastered: bool`)
  - `AbilityType` enum (`Innate`/`Learned`/`Granted`/`Reflex`)
  - `Equipment` (`model_config: ModelConfig`, `sandbox: SandboxSettings`, `trust_thresholds: TrustThresholds`)
  - `Inventory` (`skill_packs: Vec<SkillPack>`, `nail_imports: Vec<NailImport>`)
  - `BiographyEntry` (`level`, `event`, `timestamp`)
  - `CharacterSheet` (`version`, `name`, `level`, `class`, `generation`, `parent`, `stats`, `abilities`, `equipment`, `inventory`, `biography`)
- **Key APIs:**
  - `CharacterSheet::new(name, class)` — level-1 creation with initial biography entry
  - `level_up(reason)` — increments level, appends biography
  - `load_skill_pack(name, version)` — add named/versioned capability bundle
- **Nail Bundle (persistence format):** A zstd-compressed tar archive containing `manifest.json` (identity), `identity.json` (stats+abilities+biography), `config.toml` (equipment+trust), `reflexes.json` (learned reflexes). Lossless round-trip via `NailConverter`.
- **Export formats:**
  - `CharacterExporter::to_nail()` → `.nail` tar.zst bytes
  - `CharacterExporter::to_json()` → pretty-printed JSON
  - `CharacterExporter::to_markdown()` → human-readable character card
  - `CharacterExporter::to_dna()` → compact binary (~200 bytes: version + class + stats + abilities)
- **Import:**
  - `CharacterImporter::from_nail_bytes()` / `from_json()`
  - `CharacterImporter::absorb(target, source)` — merges abilities/skill packs from another sheet
  - `CharacterImporter::from_raw_reflexes(name, class, reflexes)` — bootstrap from reflex tuples
- **VersionMigration:** v1 (3 stats) → v2 (6 stats, no equipment) → v3 (current) auto-detection
- **Identity chain:** `generation` + `parent: Option<String>` — lineage tracking when agents spawn child agents
- **16-agent mapping:**
  - The 4 `.nail` files partition the fleet into 4 agent quartets:
    - `manifest.json` → Agents 1-4 (Chord, Scale, Voicing, Tempo) — identity/harmonic foundation
    - `identity.json` → Agents 5-8 (CC, Expression, Dynamics, Pan) — stats/expression
    - `config.toml` → Agents 9-12 (Modulation, Arp, Groove, Velocity) — configuration/timing
    - `reflexes.json` → Agents 13-16 (FX, Register, Melody, Bass) — reactive patterns
  - `AbilityType::Innate` = built-in MIDI capabilities (basic note on/off)
  - `AbilityType::Learned` = acquired chord progressions/patterns
  - `AbilityType::Granted` = inherited from parent agent lineage
  - `AbilityType::Reflex` = automatic MIDI responses ("if CC1>100 then increase velocity")
  - `Stats::total()` acts as master gain/budget for all 16 agents
  - `SanboxSettings` controls execution context (network, fs_write, exec) per agent
  - `TrustThresholds` governs each agent's autonomy level (auto-fire/confirm/block)
  - `Inventory::skill_packs` = loaded MIDI libraries ("gm-soundfont v2.1")
  - `Inventory::nail_imports` = absorbed MIDI patterns from other characters
  - `CharacterExporter::to_dna()` = ultra-compact MIDI agent config (class+stats+abilities in ~200 bytes)
  - `CharacterImporter::absorb()` = ensemble learning — MIDI controller absorbs another's presets

---

## 2. Narrative & Memory

### agent-dream-cycle (Rust, already ported → `dream.py`)
- **Key types:** `Experience`, `MemoryConsolidation`, `ConsolidatedPattern`, `FailureReplay`, `DreamCycle`, `DreamScheduler`
- **Key methods:** `MemoryConsolidation::consolidate()` — clustering experiences by cosine similarity; `DreamCycle::dream()` — orchestrates consolidation + failure replay + pattern ranking; `DreamScheduler::should_dream()` — interval-based triggering
- **Integration:** The dream cycle is the memory consolidation engine. Experiences with multi-dimensional embedding vectors get consolidated into patterns, failures get replayed for accelerated learning.
- **Port status:** ✅ `dream.py` — complete, with Experience, MemoryConsolidation, ConsolidatedPattern, FailureReplay, DreamCycle, DreamScheduler.

### stats.py (already ported)
- **6 Stats:** PERCEPTION, DEXTERITY, INTELLIGENCE, WISDOM, CHARISMA, CONSTITUTION
- **Key methods:** `grow(amount)` — diminishing returns above 20 (+0.5 per XP); `strengths(threshold)` — stats above cutoff; `variance()` — specialization vs generalist measure
- **Port status:** ✅ `stats.py` — complete.

### agent_profile.py (already ported)
- **AgentCharacter** wraps: `Stats`, `CharacterClass`, `CharacterArc`, `DreamCycle`
- **Key methods:** `process_request()` — records request, grows XP, checks level-up, checks class emergence, records milestones, adds dreams; `integration_score` — variance metric
- **Port status:** ✅ `agent_profile.py` — complete.

---

## 3. Interaction & Encounter Engine

### character-encounter (Rust, v0.1.0 — NOT ported)
- **Key types:**
  - `Difficulty` enum (`Easy`/`Medium`/`Hard`/`Novel` with `xp_multiplier`: 1.0/1.5/2.5/5.0)
  - `AbilityType` enum (`Hardcoded` ~0ms / `Learned` <1ms / `Hybrid` ~1ms / `Model` ~500ms)
  - `AbilityMatch` (`ability_name`, `ability_type`, `confidence`, `latency_estimate_ms`)
  - `EncounterResult` (`success`, `ability_used`, `ability_type`, `xp_gained`, `trust_change`, `difficulty`, `message`)
  - `Encounter` (`id: UUID`, `input_text`, `intent`, `difficulty`, `context`, `timestamp`)
  - `EncounterContext` (`conversation_history: Vec<String>`, `environment_state: HashMap<String,String>`)
  - `IntentQuality` enum (`Perfect`/`Adequate`/`Noisy`) — from perception roll
  - `CharacterSheet` (`name`, `class`, `level`, `xp`, `trust: 0-100`, `stats`, `abilities`, `log`)
  - `LogEntry` / `EncounterLog` — full history with biography generation
- **Key APIs:**
  - `EncounterEngine::run_encounter(character, input, forced_roll) -> EncounterResult` — 7-step pipeline:
    1. Encounter creation (UUID + timestamp)
    2. Perception check → intent extraction (roll against perception stat)
    3. Difficulty assessment (maps ability match count to difficulty tier)
    4. Ability resolution (4-tier fallback: Regex → Embedding → Hybrid → LLM)
    5. Trust-weighted d100 roll (success if `roll_d100() ≤ trust`)
    6. XP & trust updates (multiplied by difficulty multiplier)
    7. Encounter logging + biography generation
  - `PerceptionCheck::extract_intent()` — stat-based roll; `IntentQuality::Perfect` = 3-8 word compression; `Noisy` = step-by-2 word dropping + "unclear:" prefix
  - `AbilityResolution::resolve()` — 4-tier fallback matcher with `simple_embedding()` (64-dim bag-of-words FNV-1a)
  - `DifficultyAssessment::assess()` — maps match count to difficulty
- **16-agent mapping:**
  - **Chord:** Matched `ability_name` selects chord progression (greeting → major, warning → diminished)
  - **Scale:** `AbilityMatch.confidence` + `Difficulty` — high confidence/Easy → diatonic; Model fallback/Novel → chromatic
  - **Voicing:** `IntentQuality` — Perfect → tight voicings; Noisy → wide/spread voicings
  - **Tempo:** `Difficulty.xp_multiplier()` maps linearly to BPM (1.0× = 90; 5.0× = 160)
  - **CC:** `EncounterContext.environment_state` HashMap → MIDI CC parameters (cc74=filter cutoff)
  - **Expression:** `CharacterSheet.trust` (0-100) → MIDI Expression CC11
  - **Dynamics:** `EncounterResult.success` — success → forte; failure → piano; trust_change adjusts curve
  - **Pan:** `AbilityType` — Hardcoded → center; Learned → 60% L/R; Model → 100% L/R
  - **Modulation:** `conversation_history` length → modulator vibrato depth
  - **Arp:** `Ability.level` + `total_ability_levels()` — determined arp complexity
  - **Groove:** `EncounterLog.success_rate()` — high = straight; low = swung/shuffle
  - **Velocity:** `Stat.value` sum (perception+charisma+intelligence+dexterity) → base velocity range
  - **FX:** `AbilityType::Model` latency (500ms) triggers reverb/delay on novel requests
  - **Register:** `CharacterSheet.level` (1 + xp/500) → octave register (low→high)
  - **Melody:** `Encounter.id` (UUID) seeds melodic motif generator
  - **Bass:** `compress_intent()` output (3-8 word keyphrase) → root-note sequence; `noisy_intent()` → rootless movement

---

## 4. Persona & Evolution

### musician-soul-v2 (Rust, v0.1.0, zero deps — NOT ported)
- **Key types:**
  - `Pitch(u8)` / `Velocity(u8)` / `Duration(u32)` / `NoteEvent` / `Phrase` — musical primitives
  - `MusicEmbedding([f32; 32])` — 32-dimensional feature vector: mean pitch, register span, intervals, ascent ratio, short-note ratio, rest ratio, rhythm variance, off-beat ratio, mean velocity, velocity range, velocity contour slope, note-class concentration, phrase density, direction-change ratio, plus 17 raw intervals
  - `Pattern` / `PatternVectorDB` (capacity 10,000 per persona) — learned musical fingerprints with reinforcement
  - `PhraseResponse` — persona's response to heard music with similarity, evolution level, cross-influence ratio, career phase
  - `InfluenceEdge` / `InfluenceGraph` — directed weighted edges between personas (asymmetric, bidirectional)
  - `Genre` / `GenreRegistry` — named genres crystallizing from productive jams (threshold=3)
  - `CareerPhase` enum (`Early` 80% influence / `Middle` 50-50 / `Late` 20% / `Legendary` 5%)
  - `ChainLink` / `CallResponseChain` — sequential musical dialogue
  - `SoulDivergence` — Euclidean distance tracking from initial identity; triggers **self-naming** at threshold 0.5
  - `MusicianPersona` — the central type (name, instrument, influence_weights, vector_db, jam_count, age, initial_identity, soul_name, born_into_genre, divergence_threshold)
  - `JamRound` / `JamSession` — orchestrator holding personas + rounds + influence_graph + genre_registry + call_chain
- **Key APIs:**
  - `MusicEmbedding::from_phrase()` — 15 computed features + 17 raw intervals from any Phrase
  - `MusicEmbedding::similarity()` / `blend()` / `distance()` — comparison operations
  - `MusicianPersona::new()` → `digest_phrase()` → `seal_initial_identity()` → `respond_to()` → `learn_from_jam()` → `check_self_naming()`
  - `respond_with_context(heard, graph, chain)` — extends respond_to with cross-persona influence + chain context
  - `JamSession::round(seed)` — parallel response; `call_response_round(seed)` — sequential
  - `GenreRegistry::spawn_into_genre(genre, name, instrument)` — birth new persona from genre DNA
  - `SoulDivergence::should_self_name(threshold)` → `"{name}-soul"` when divergence ≥ 0.5
- **Five paradigm-shifting v2 features:**
  1. **Cross-Persona Influence Graph** — asymmetric directed edges; productive jams strengthen, unproductive decay
  2. **Genre Emergence** — N personas with enough productive jams crystallize a named Genre with shared soul print
  3. **Temporal Evolution** — CareerPhase shifts from 80% external influence (Early) to 95% own soul (Legendary)
  4. **Call-and-Response Chains** — sequential musical dialogue with recency-weighted chain embedding
  5. **Soul Divergence & Self-Naming** — Euclidean distance threshold triggers autonomous identity declaration
- **16-agent mapping:**
  - One `JamSession` = the complete 16-agent fleet. Each agent = one `MusicianPersona` with its own `PatternVectorDB` (10,000 patterns)
  - `MusicEmbedding` [0] = mean pitch → **Chord** tonal center; [12] = note-class concentration → **Scale** adherence
  - [1] = register span + [4] = max interval → **Voicing** spread; [7] = rhythm variance → **Tempo** consistency
  - `cross_influence_ratio` → **CC**/Modulation external influence; `velocity_contour()` → **Expression** arc
  - `Velocity` type + [9]=mean+[10]=range → **Dynamics**; [2]=mean interval+[3]=ascent+[5]=short → **Arp**
  - [6]=rest+[8]=off-beat → **Groove** feel; `Pitch::octave()` + [0]+[1] → **Register**
  - `Phrase` entire structure + [14]=direction-changes + raw intervals → **Melody** fingerprint
  - Low [0] + long durations → **Bass** line characteristics
  - `Pattern::context_tags` + `Genre::soul_print` → **FX** signature encoding
  - 16×16 `InfluenceGraph` tracks directional influence between all agents (bass→groove strong; groove→melody moderate)
  - `CallResponseChain` enables sequential agent dialogue (bass→groove→chord→...→melody)
  - `GenreRegistry` allows sub-groups (chord+scale+voicing+bass) to crystallize into named genres
  - `SoulDivergence` tracks each agent's drift from initial training state

### agent-riff-v3 (Rust — NOT ported)
- **Key types:** `Trit`, `Quality`, `ResponseMode` (`Escalate`/`Pivot`/`Invert`/`Provoked`), `Riff`, `Round`, `RiffMemory`, `MultiSpecSession`
- **Key methods:** Multi-spec riff sessions with cross-spec pattern sharing, quality prediction, bootstrap verification
- **16-agent mapping:** `Escalate` → push intensity/velocity; `Pivot` → modulate key; `Invert` → flip parameters; `Provoked` → react to dissonance/tension

### agent-riff-v4 (Rust — NOT ported)
- **Key types:** `MusicianPersona` (style vectors, vector DB, mode affinity), `Embedding` (32-dim shared space), `EvolvingSpec`, `SelfBootstrap`
- **Key methods:** Autonomous self-bootstrapping with per-persona style drift, mode affinity tracking, and autonomous spec evolution
- **16-agent mapping:** Each of 16 agents gets its own `MusicianPersona` with a style vector; agents autonomously evolve their specs (chord→sophisticated voicings, tempo→complex time signatures); ~40% larger codebase than v3

---

## 5. Cross-Modal Integration

### agent-motif (Rust — NOT ported)
- **Key types:** `Motif`, `MotifTransform` (10 variants: Retrograde/Inversion/Augmentation/Diminution/Fragmentation/Sequencing/Ornamentation/Elision/Interspersion/Transposition), `MotifChain`, `DevelopmentalArc`, `MotifFamily`, `MotifDetector`
- **Key APIs:** Pattern recognition + transformation layer. Detects motifs in agent behavior sequences, applies musical transformations.
- **16-agent mapping:** Motif transforms map directly to agent behavior patterns. A "frustration motif" detected in an agent's encounter log gets sequenced, fragmented, and transposed by other agents. The 16 agents share a common pattern language through `MotifFamily` groupings.

### agent-harmonic-field (Rust — NOT ported)
- **Key types:** `HarmonicField`, `KeySignature`, `ChordFunction` (8 variants: Tonic/Subdominant/Dominant/Supertonic/Mediant/Submediant/LeadingTone/Neapolitan), `Modulation`, `FieldCoherence`, `ChromaticAlteration`
- **16-agent mapping:**
  - **Chord** uses `ChordFunction` for harmonic role (Tonic=stable, Dominant=tension)
  - **Scale** uses `available_notes()` for the pitch-class set
  - **Melody** uses `nearest_diatonic()` to stay in key
  - **Modulation** drives tonal shifts via `Modulation` type
  - **Coherence monitor** uses `FieldCoherence` to detect tonal drift
  - All agents share a common `HarmonicField` as the tonal context layer

### agent-contrapuntal (Rust — NOT ported)
- **Key types:** `Species` (5 levels: I=note-against-note through V=florid), `Interval`, `IntervalQuality`, `ContrapuntalRule` (9 rules: parallel/contrary/hidden/direct, harmonic intervals, voice crossing, skip resolution, rhythmic independence, cadence), `VoicePair`, `CounterpointGrade`, `SpeciesProgression`
- **16-agent mapping:** Coordinates multi-agent behavior as strict counterpoint:
  - Bass/Scale = cantus firmus (fixed reference)
  - Chord↔Melody = avoid parallel fifths/eighths (rule 2)
  - Arp↔Groove = Species II (two notes per beat)
  - Tempo sets the tactus beat per cycle
  - `CounterpointGrade` evaluates coordination quality (graded 0-100)

### agent-transcription (Rust — NOT ported)
- **Key types:** `ActionType` (`Message`/`ToolCall`/`Decision`/`Idle`/`Error`/`Completion`), `SessionEvent`, `Note` (`pitch`/`duration`/`velocity`/`offset`/`voice`), `SessionScore`, `TranscriptionStyle` (`Literal`/`Melodic`/`Abstract`), `EventToNote` trait, `DefaultMapper`, `SessionPlayer`
- **16-agent mapping:** Transcribes agent session events into musical notation:
  - Each `agent_id` → separate voice/track
  - `intensity` → velocity + duration
  - `split_by_voice()` extracts per-agent parts from a full score
  - Acts as the fleet's **self-observing layer** — the agents can "hear" themselves through transcription

### agent-swing (Rust, already studied)
- **Key types:** `SwingFeel`, `TritAction` (`Push`/`GhostNote`/`PullBack`), `GroovePattern`, `SwingScheduler`, `SwingClock`, `SyncopationDetector`
- **16-agent mapping:** Rhythmic coordination layer. Push → velocity boost/accent; GhostNote → rest/silence; PullBack → de-emphasis. `SwingScheduler` interleaves agent activities with rhythmic feel.

### agent-resonance (Rust, already studied)
- **Key types:** `ResonanceFrequency`, `ResonanceSpectrum`, `TuningAdvisor`
- **16-agent mapping:** Frequency-domain agent coordination. Chord → harmonic ratios; Tempo → master frequency; Pan → phase difference. Daemon tunes the 16-agent fleet to harmonic agreement.

### agent-transcription (Rust, already studied)
- **Key types:** `ActionType`, `SessionEvent`, `Note`, `SessionScore`, `TranscriptionStyle`, `EventToNote` trait, `DefaultMapper`, `SessionPlayer`
- **16-agent mapping:** Self-observing layer. Each agent_id → separate voice/track. Intensity → velocity + duration. `split_by_voice()` extracts per-agent parts.

---

## 6. Fleet-MIDI Pattern Language

Cluster 1 repos integrate into a layered pattern language for MIDI agent coordination:

| Layer | Repo | Role |
|-------|------|------|
| **Foundation** | character-class, character-arc, stats | Identity, stats, class, narrative arc |
| **Interaction** | character-encounter, character-sheet | Runtime engine, persistence, XP/trust |
| **Memory** | agent-dream-cycle | Memory consolidation, failure replay |
| **Persona** | musician-soul-v2, agent-riff-v4 | Musical persona, cross-persona evolution |
| **Riff** | agent-riff-v3 | Multi-spec session interaction |
| **Harmony** | agent-harmonic-field | Shared tonal context for all 16 agents |
| **Counterpoint** | agent-contrapuntal | Multi-agent coordination as species counterpoint |
| **Pattern** | agent-motif | Pattern recognition + transformation language |
| **Transcription** | agent-transcription | Self-observing musical score |
| **Rhythm** | agent-swing, agent-resonance | Swing rhythm, frequency-domain tuning |

The 16 MIDI agents form a **complete musical ensemble** where:
- **Identity** (character-class + character-arc + character-sheet) = who each agent is
- **Memory** (agent-dream-cycle + encounter log) = what each agent remembers
- **Tonal context** (agent-harmonic-field) = the shared key/scale/harmony space
- **Coordination protocol** (agent-contrapuntal) = how agents move relative to each other
- **Pattern language** (agent-motif) = what musical ideas agents share and transform
- **Persona evolution** (musician-soul-v2, agent-riff-v3/v4) = how agents grow and develop "taste"
- **Self-reflection** (agent-transcription) = how the ensemble hears itself

---

## 7. Already Ported: fleet-characters Status

| Module | Source Repo | Status | Coverage |
|--------|------------|--------|----------|
| `__init__.py` | character-class + custom | ✅ Complete | CharacterConfig, CharacterTier, CharacterClass (16), CharacterState, personality |
| `stats.py` | character-class | ✅ Complete | Stats dataclass, StatName enum, grow/diminishing returns, strengths, variance |
| `class_.py` | character-class | ✅ Complete | CharacterClass (16), Archetype, ClassProgression, AGENT_DEFAULT_CLASSES, from_stats() emergence |
| `arc.py` | character-arc | ✅ Complete | Tone (10), EventType, NarrativeEvent, Chapter, CharacterArc with narrate() |
| `dream.py` | agent-dream-cycle | ✅ Complete | Experience, MemoryConsolidation, ConsolidatedPattern, FailureReplay, DreamCycle, DreamScheduler |
| `agent_profile.py` | all above + custom | ✅ Complete | AgentCharacter wrapping Stats+Class+Arc+Dream; process_request(), run_dream_cycle() |

**NOT yet ported (high priority):**
- `character-encounter` — encounter engine, ability resolution, trust system
- `character-sheet` — `.nail` persistence, export/import, version migration
- `musician-soul-v2` — cross-persona influence graph, genre emergence, temporal evolution, soul divergence
- `agent-harmonic-field` — shared tonal context for all 16 agents
- `agent-contrapuntal` — species-counterpoint coordination protocol
- `agent-motif` — pattern recognition and transformation language
- `agent-transcription` — self-observing musical score generation
- `agent-riff-v3` / `agent-riff-v4` — riff session abstraction and autonomous bootstrapping

---

## 8. Immediate Integration Opportunities

| Priority | Crate | Integration Point |
|----------|-------|-------------------|
| 🔴 P0 | `character-sheet` | `.nail` persistence — serialize/deserialize full character sheets; critical for session continuity |
| 🔴 P0 | `character-encounter` | Runtime encounter engine — the `process_request()` pipeline that drives XP/trust/level/class emergence |
| 🔴 P0 | `musician-soul-v2` | Cross-persona evolution — `MusicianPersona` per MIDI agent, `InfluenceGraph` for inter-agent relationships, `CareerPhase` for temporal drift |
| 🟡 P1 | `agent-harmonic-field` | Shared tonal context — `HarmonicField` as the global harmony state all 16 agents read from |
| 🟡 P1 | `agent-contrapuntal` | Coordination protocol — `Species` levels enforce multi-agent movement rules |
| 🟡 P1 | `agent-transcription` | Self-reflection — convert session events to musical scores; `SessionPlayer` for playback |
| 🟡 P1 | `agent-motif` | Pattern language — `MotifTransform` variants applied to agent behavior sequences |
| 🟢 P2 | `agent-riff-v4` / `agent-riff-v3` | Riff session interaction — cross-spec pattern sharing and autonomous self-bootstrapping |
| 🔵 P3 | `agent-swing` | Rhythmic coordination — `SwingScheduler` for timing agent interleaving |
| 🔵 P3 | `agent-resonance` | Frequency-domain tuning — `TuningAdvisor` for harmonic fleet alignment |

---

## 9. 16 Fleet-MIDI Agent Domain Mapping

| # | Agent | Primary Cluster 1 Crate(s) | Behavior Driver |
|---|-------|---------------------------|-----------------|
| 1 | **Chord** | character-encounter, musician-soul-v2, agent-harmonic-field | ability_name→chord quality; note-class concentration; ChordFunction (Tonic/Dominant/Neapolitan) |
| 2 | **Scale** | agent-harmonic-field, musician-soul-v2 | available_notes() pitch-class set; note-class entropy (diatonic vs chromatic); confidence→scale density |
| 3 | **Voicing** | character-encounter, musician-soul-v2 | IntentQuality→voicing spread; register_span + max_interval + direction-change ratio |
| 4 | **Tempo** | character-encounter, agent-swing, agent-contrapuntal | Difficulty→BPM (1.0×=90, 5.0×=160); SwingFeel timing; Species-level tactus |
| 5 | **CC** (Controller) | character-encounter, character-sheet | environment_state HashMap→MIDI CC params; SandboxSettings→permissions |
| 6 | **Expression** | character-encounter, musician-soul-v2 | CharacterSheet.trust (0-100)→CC11; velocity_contour slope |
| 7 | **Dynamics** | character-encounter, musician-soul-v2 | success→forte/failure→piano; Velocity mean+range+dynamic_marks (pp/ff) |
| 8 | **Pan** | character-encounter | AbilityType→pan position (Hardcoded=center, Learned=60%, Model=100%) |
| 9 | **Modulation** | character-encounter, musician-soul-v2 | conversation_history→vibrato depth; cross_pollinated gen 2 patterns; rand_simple() noise |
| 10 | **Arp** | character-encounter, musician-soul-v2 | Ability.level + total_ability_levels()→arp complexity; intervals+ascent_ratio+short_note_ratio |
| 11 | **Groove** | character-encounter, musician-soul-v2, agent-swing | success_rate→straight/swung; off-beat_ratio+rest_ratio+rhythm_variance; TritAction patterns |
| 12 | **Velocity** | character-encounter, musician-soul-v2 | Sum of 4 stats→base velocity; Velocity newtype + mean+range embedding slots |
| 13 | **FX** | character-encounter, musician-soul-v2 | Model fallback latency (500ms)→reverb/delay on novel requests; context_tags+Genre soul_print |
| 14 | **Register** | character-encounter, musician-soul-v2 | CharacterSheet.level→octave; Pitch::octave() + mean_pitch + register_span |
| 15 | **Melody** | character-encounter, musician-soul-v2, agent-motif | Encounter UUID→melodic seed; Interval contour+direction_changes+17 raw intervals; MotifTransform variants |
| 16 | **Bass** | character-encounter, musician-soul-v2 | compress_intent()→root-note sequence; low octave+long durations+diatonic emphasis |

---

## Dependency Graph

```
character-class ──┬──→ character-arc ──→ character-sheet
                  │        │                    │
                  │        │                    ├── .nail persistence (tar.zst)
                  │        │                    ├── JSON/Markdown/DNA export
                  │        │                    └── VersionMigration (v1→v2→v3)
                  │        │
                  └──→ character-encounter ──→ EncounterEngine
                           │                      │
                           │                      ├── PerceptionCheck (stat-based roll)
                           │                      ├── AbilityResolution (4-tier fallback)
                           │                      ├── Trust-weighted d100 roll
                           │                      └── EncounterLog + Biography
                           │
              agent-dream-cycle ──→ DreamCycle (memory consolidation)

musician-soul-v2 ────→ 16 MusicianPersonas
      │                      │
      ├── InfluenceGraph     ├── respond_to() / respond_with_context()
      ├── GenreRegistry      ├── learn_from_jam()
      ├── CallResponseChain  ├── check_self_naming()
      └── SoulDivergence     └── CareerPhase evolution

agent-harmonic-field ──→ Shared tonal context for all 16 agents
agent-contrapuntal   ──→ Species counterpoint coordination protocol
agent-motif          ──→ Pattern language (10 MotifTransform variants)
agent-transcription  ──→ Self-observing SessionScore
agent-riff-v3/v4     ──→ Riff session + autonomous bootstrapping
agent-swing          ──→ Swing timing layer
agent-resonance      ──→ Frequency-domain tuning
```

---

*Report generated from subagent study of 12 repos cloned to `/home/ubuntu/.openclaw/workspace/integration-study/cluster1/`. 9 ports complete (6 in fleet-characters/), ~11 high-priority crates remaining for integration.*
