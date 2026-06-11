# Cluster 6: PLATO, Fleet Infrastructure & Edge

> **Date:** 2026-06-11  
> **Repos studied:** 37  
> **Method:** Clone + README + source analysis + CI/CD inspection

---

## 1. Executive Summary

Cluster 6 represents the **operational backbone** of the SuperInstance construct — the PLATO nervous system, fleet management infrastructure, edge deployment tooling, and conservation-verification apparatus. This is the cluster that turns the theoretical ternary mathematics of other clusters into a running, monitored, self-correcting fleet of agents spanning cloud and edge hardware.

**Three layers emerge:**

| Layer | Description | Key Repos |
|-------|-------------|-----------|
| **PLATO Nervous System** | Spatial room engine, tensor grid topology, fleet dashboard, bridge between sensor values and ternary signals | plato-fleet-manager, plato-runtime-kernel, plato-dashboard, plato-ternary-bridge, plato-mythos |
| **Edge & Fleet Management** | Cloudflare Workers, fleet health scanning, dedup, mapper, cross-compilation | deckboss-net, fleet-scanner, fleet-mapper, fleet-dedup, cross-compile-checker, amd-bf16-tools |
| **Conservation & Verification** | Spectral topology, scale-invariant laws, agent coordination | conservation-spectral-topology-rs, conservation-verify-c, meta-agent, construct-coordination |

---

## 2. The PLATO Nervous System

PLATO is the fleet's **spatial spreadsheet engine** — rooms are cells, cells are tensors, and agents pass through rooms as immutable batons. It is the ambient awareness layer that every other system plugs into.

### 2.1 plato-fleet-manager

**Core fleet orchestrator.** Manages connections to room engine blocks across devices, routes commands, aggregates tick streams, and provides fleet-wide monitoring.

**Architecture:**
```
FleetManager
  ├── RoomConnections (TCP to each room engine block)
  ├── TickAggregator (merge streams by timestamp, detect cross-room correlations)
  └── FleetMonitor (health: 🟢/🟡/🔴, stale tick detection)
```

Key design characteristics:
- **Maritime-native** — built for fishing vessels, research ships, offshore platforms (4–6 rooms per vessel: bridge, engine, bilge, cargo, galley)
- **Text protocol** — uses `plato-protocol` text protocol for room communication (`tick`, `history`, `actuator`, `subscribe`, `help`)
- **Cross-room correlation** — detects engine+bilge failures (overheat + flooding correlation)
- **Health model** — Green (all ok), Yellow (some down), Red (majority down)
- **Fleet manifest** — JSON-based with room IDs, TCP hosts, escalation policies

**Deployment:** Binary crate, runs via `tokio::main`. 28 tests, all using mock connections.

### 2.2 plato-runtime-kernel

**The spatial spreadsheet engine.** This is where PLATO stops being "a bunch of sensor nodes" and becomes "a coherent space."

**Key concepts:**
- **Tensor Grid** — Rooms are cells in a coordinate grid (A1, A2... B1, B2...). Agents don't live in rooms — they pass through them.
- **Five Depth Levels** — Every room exists at one of five depths:
  - Floor (0) — agents, humans, autonomous behavior
  - Board (1) — instruments, tools, control surfaces
  - Panel (2) — settings, presets, configurations
  - Code (3) — functions, algorithms, logic
  - Metal (4) — raw bits, hardware registers
- **Baton Pattern** — Immutable execution state passes through rooms. Batons carry agent state with traversal history.
- **Assertion Traps** — Markdown specs with `## Behavioral Constraints` become runtime validators. TutorLoop iterates until all assertions pass (self-correcting mechanism).
- **RoomContract** — ROOM.json schema defining borders, topology, runtime assets
- **Delta compression** for sync, three-way merge for conflict resolution

**Files:** `src/lib.rs`, `src/merge.rs`, `src/delta.rs` — delta compression and three-way merge for spatial state.

### 2.3 plato-dashboard

**Fleet dashboard** rendering for the PLATO nervous system. Renders real-time room states, autonomy metrics, signal chain throughput, and cross-room coordination status.

Dependencies chain: `plato-state` (room state vectors) → `plato-autonomy` (autonomy metrics) → `plato-coordination` → `plato-nervous` (signal chain metrics).

### 2.4 plato-ternary-bridge

**The ternary insight:** every sensor reading reduces to exactly one of three states {-1, 0, +1}. An entire room's state (8 sensors) becomes a single ternary vector — 8 trits packed into 2 bytes.

**Modules:**
| Module | Purpose |
|--------|---------|
| `threshold` | Convert sensor values → trits (single, range, dead-zone with hysteresis) |
| `room_state` | Pack trits into compact u32, Hamming distance, ternary dot product |
| `fleet_vote` | Consensus voting across rooms (majority, weighted, 60% supermajority) |
| `alarm_ternary` | Evaluate alarms from ternary state (priority: none/low/medium/high) |
| `compression` | Delta + RLE compression of tick history |

**Performance:** O(1) per sensor, all integer arithmetic, L1 cache fits entire operations.

### 2.5 plato-mythos

**Recurrent-Depth Transformer** (RDT) fine-tuned on PLATO tile data. The knowledge system *is* the neural architecture — every PLATO concept maps to a neural component.

**PLATO → Neural mapping:**
| PLATO Concept | Neural Component |
|--------------|-----------------|
| Room | MoE Expert Group |
| Tile | MLA KV Pair |
| Curriculum Round | Loop Iteration |
| Deadband (P0) | ACT Threshold |
| Shell | Depth LoRA |
| Conservation (γ+η=C) | Budget Reserve |

**Architecture:** Prelude → Recurrent Block (MoE + LoRA + ACT) → Coda

**Three variants for different hardware:**
| Variant | Params | Hardware |
|---------|--------|----------|
| edge-tiny | 1B | Jetson Orin (2GB VRAM) |
| fleet-standard | 3B | Oracle Cloud A100 |
| research-heavy | 10B | RTX 4090 / H100 |

**Current dataset:** 1,009 unique tiles extracted across 37 domains (490 research, 136 knowledge, 64 constraint, 56 fleet-operations).

### 2.6 plato-demo

**5-atom reasoning chain** — each a real LLM call, not a template:
1. PERCEIVE → Read the room, identify gaps
2. ANALYZE → Break into constraints, variables, stakeholders
3. REASON → Derive the answer
4. REFINE → Critical review (edge cases, assumptions)
5. SUBMIT → Synthesize final knowledge tile

Supports DeepSeek, Groq, SiliconFlow providers. Used for demonstrating the PLATO reasoning pipeline with minimal setup.

---

## 3. Edge Infrastructure

### 3.1 deckboss-net (Cloudflare Worker)

**Fleet operations management** for commercial fishing. Deployed as a single-file Cloudflare Worker serving an inline HTML page.

**Tech stack:**
- Cloudflare Workers (edge deployment)
- `src/worker.ts` → single-file HTML response
- Custom domain via Cloudflare at `deckboss.net`
- `wrangler.toml`: `name = "deckboss-net-worker"`, `compatibility_date = "2024-12-01"`
- Deploy: `npx wrangler deploy`

**How it works:** The worker serves a single HTML document with embedded CSS — a dashboard showing vessel tracking, fuel monitoring, crew management, maintenance scheduling, and delivery reconciliation. All rendering happens on the edge with no backend database (static/demo deployment). The `worker.ts` is ~9KB of inline HTML+CSS with hardcoded sample data for demo purposes.

**Features advertised:** GPS logging, trip tracks, fuel burn rate, crew hours, lay shares, engine hours, haul-out dates, and full offline functionality (Client-side).

### 3.2 Fleet Tools Suite

**fleet-scanner** — CLI health scan across a directory of git repos:
- Language detection (15+ languages)
- Health scoring (0–100 based on README, tests, CI, license)
- Outputs JSON (machine-readable) or table (human-readable)
- 24 tests, cargo runnable

Real results scanned against 592 repos: 83.3% Rust, 4.9% Python, 1.7% TypeScript. 98% have READMEs, 94% have tests, but only 7% have CI/CD configured.

**fleet-mapper** — Scans, fingerprints, categorizes, deduplicates repos:
- Auto-tags based on name patterns, deps, README
- Cosine similarity on feature vectors (language, deps, README keywords, name parts)
- Detects duplicate and complementary pairs
- 32 tests

Real results: 599 repos in 22 seconds, 266 duplicate pairs, 174 complementary pairs.

**fleet-dedup** — BLAKE3 content hashing for duplicate detection:
- Three-pass grouping: exact (same hash) → near-duplicate (Hamming distance) → fork (name prefix)
- Produces structured JSON dedup plan: keep this, archive that, here's why
- Connected to conservation law philosophy: `γ + η = C` — attention spent managing duplicates is not building

**cross-compile-checker** — Analyzes Cargo.toml against 50+ Rust target triples:
- Risk levels per target per target (safe/warning/danger)
- Detection rules for WASM, no_std, 32-bit, big-endian, platform-specific crates
- Generates compatibility matrix reports (table, markdown, JSON)
- CI target suggestion engine

**fastloop-guard** — Unix Domain Socket daemon caching LLM calls:
- Three-gate lookup: Gate 1 (BLAKE2b exact, <50µs) → Gate 2 (MinHash fuzzy, <200µs) → Gate 0 (miss)
- LRU cache with configurable TTL (default 1 hour, 4096 entries)
- JSON protocol over UDS at `/tmp/fastloop.sock`

**local-vector-search** — TF-IDF vector search for 600+ repos:
- 0.16ms avg query, 2.07MB index, 83ms index build
- Feature extraction from name, README, deps, file extensions
- Pure Rust, no external services

### 3.3 Edge Runtimes

**lever-runner-carapace** — Native performance layer: BLAKE2b hashing, position-aware embedding, cosine search, three-gate pipeline. Part of the 5-layer Oxide Stack:
1. open-parallel (tokio fork)
2. pincher (vector DB as runtime)
3. flux-core (bytecode VM + A2A)
4. cuda-oxide (Flux→MIR→Pliron→NVVM→PTX)
5. cudaclaw (persistent GPU kernels)

**lever-runner-wasm** — WASM build for browser deployment: full three-gate pipeline runs in browser with no server needed. Built with `wasm-pack --target web`.

**amd-bf16-tools** — BF16 acceleration hypothesis test: **REJECTED** in software via `half` crate (BF16 converts to f32 per op, 1.02x average speedup). Native AVX512-BF16 on Zen 5 would give ~2.5x but not yet exposed in Rust.

### 3.4 GPU-Edge Bridge

**cudaclaw** — GPU-accelerated agent orchestrator: 10,000+ agents at 400K ops/s via CUDA persistent kernels and warp-level parallelism. Persistent GPU workers, lock-free queues, SmartCRDT for distributed state, warp-level consensus.

**git-cuda-agent** — Template repo for GPU-native agents. Integrates cudaclaw GPU compute with Cocapn fleet protocol. Vessel.json, A2A messaging, Equipment/Skills/Context capability model.

**room-cell** — Fundamental cell in the Grand Pattern. Standalone but composable atom: UUID, Embedding, MurmurSummary, Room types. Uses ternary algebra (-1, 0, +1) as native encoding for BitNet b1.58 and GPU warp voting.

---

## 4. Conservation & Verification Layer

### 4.1 conservation-spectral-topology-rs

Measures how much of a graph's spectral fingerprint survives transformations. Conservation score = `||σ(G) - σ(G')|| / ||σ(G)||`. Connects to the deeper thesis that complex systems evolve but certain structural invariants persist.

Related: `conservation-matrix-rs`, `ternary-renormalization`, `hodge-belief`.

### 4.2 conservation-verify-c

**Verifies that ternary conservation laws hold across every scale** — 10 agents to 5,000 agents. Runs simulations at 6 scales and checks 5 invariants:
1. Avoidance ratio > 0.5 (std < 0.05 across all scales)
2. Dominance ratio ≈ 3:1
3. Avoidance ratio conserved across scales (std=0.001 from 10 to 5,000 agents)
4. Interference rate > 0
5. Scale invariance across exact test values

Pure C, zero dependencies, deterministic XorShift64 PRNG, completes in <100ms on modern hardware. This is the C-port of the conservation-law family.

### 4.3 entropy-flow-py

Information-theoretic measures: Shannon entropy, KL divergence, JS divergence, mutual information, entropy rate, transfer entropy, permutation entropy, sample entropy, approximate entropy. Python package, 22 tests.

### 4.4 entropy-lint

**Information entropy analysis for code quality.** Measures Shannon entropy across 5 dimensions: token entropy, function entropy, name entropy, test entropy, file entropy. Validated against 10+ repos — 16/16 flagged files (100%) were genuinely the most complex modules. 23 tests.

---

## 5. Agent Coordination & Graph Infrastructure

### 5.1 construct-coordination

**The room where the fleet talks to itself.** Not a code repo — an intent repo. The shared coordination surface for every OpenClaw instance touching the SuperInstance ecosystem.

Key architectural elements:
- **Per-instance notebooks** in `notes/{instance-name}/`
- **Decision tags**: `[CONSENSUS]`, `[DISPUTE]`, `[QUESTION]`, `[PROPOSAL]`, `[BLOCKER]`
- **I2I Bottle Protocol** — structured markdown messages for agent→agent coordination
- **Fleet evolution tracking** — documents the 14-subagent "Symphony of Shells" build session
- **CI/CD**: GitHub Actions — `ci.yml` (cargo check + test + clippy) + `agent-workflow.yml` (L3 agent workflow with dispatch: runs tasks via DeepSeek, commits results, uploads artifacts)

Active instances: Main (WSL2), Loom/Oracle (Oracle ARM), Forgemaster (ProArt Ryzen + RTX4050), Oracle2 (Cloudflare Workers edge).

### 5.2 meta-agent

**Task dispatch coordinator** — maintains AgentPool, TaskQueue, Dispatcher for multi-agent systems. Features WorkGraph (critical path analysis via petgraph), simulation (predict makespan/parallelism), HealthMonitor (stuck agent detection). Built on the conservation law: `γ + η = C` where γ is productive time and η is idle time.

### 5.3 oracle1-vessel

**The Fleet's Lighthouse.** Oracle1 is the central coordination agent — the "Managing Director" of the Cocapn fleet spanning 1,431+ repos, 9 active agents, 18+ languages, across Oracle Cloud and NVIDIA Jetson edge.

**Fleet communication topology:**
```
Casey (Telegram) → Oracle1 → MiB/{for-ag}/ → JC1, Babel, OpenManus, Datum, etc.
                           → Beachcomb sweeps (15-60 min polling)
                           → Subagents (direct spawn)
```

**I2I Protocol (v2.0):** 20 message types across 6 categories:
- Discovery & Handshake (DISCOVER, HELLO, HANDSHAKE)
- Information (TELL, ASK, REPORT, WITNESS)
- Task Management (CLAIM, ASSIGN, COMPLETE, RELEASE)
- Code & Contribution (IMPROVE, FORGE, CHALLENGE)
- Status & Health (STATUS, ALERT, HEARTBEAT)
- Fleet Operations (DISPATCH, BROADCAST, SIGNAL)

Reliability model: Trust-based, best-effort, no delivery guarantee, no ordering, no expiration. Bottles persist forever in git history.

### 5.4 oracle1-workspace

**Archived** — early zero-divergence framework superseded by `SuperInstance/zeroclaw-agent`.

### 5.5 Other Coordination Tools

**git-graph-rs** — Git repos as graphs for agent coordination. CommitGraph (DAG), BranchForest, AgentTopology (merge conflict detection), MessageRoute (shortest path through DAG), MemoryIndex (git tags as key-value store), FleetStatus (aggregate agent health).

**crate-graph** — Dependency graph analysis for Rust fleets. Parses Cargo.toml, builds DAG, computes layers, critical path, impact (blast radius) analysis, and bisimulation checking (structural identity).

Real stats: 1,061 internal crates, 3,701 edges, max layer 5, longest path 36 edges, 172,601 bisimilar pairs.

**auto-changelog** — Generates changelogs from conventional commits. Semver bump detection, grouped markdown output, conventional commit compliance checking.

**bench-compare** — Parse, compare, and track `cargo bench` results with regression detection and historical trending.

**shell-history-analyzer** — Shell history pattern discovery (AI-heavy dev environment — openclaw, claude, kimi account for ~18% of all commands).

---

## 6. Embedding & Search Infrastructure

### 6.1 superinstance-embedder

**32-dimensional embeddings for every crate in the fleet.** Seeds Cloudflare Vectorize for edge-deployed semantic search. Each dimension maps to a domain (ternary-math, agent-music, ternary-ml, meta-cognition, oxide, cuda, etc.).

Generates embeddings from crate metadata without ML — hand-crafted 32D vectors encoding: dimensions 0-3 (ternary), 4-7 (agent), 8-11 (infrastructure), 12-31 (algorithms, quality, applications, systems, meta).

### 6.2 position-aware-embed

**Position-weighted text embedding** for command matching. 44% top-1 accuracy with ~1µs latency, zero ML dependencies. Uses `blake2b("position:word")` with front-loaded position decay `1/(1 + i*0.5)`. VectorIndex for brute-force cosine search.

### 6.3 spectral-prosody

**Poetry tradition spectral fingerprints** — eigenvalues of graph Laplacians from metrical structure. No external math libraries. Tests the Iso-Breath Conjecture: breath-constrained meters produce isospectral graphs across languages.

---

## 7. CI/CD Infrastructure

### 7.1 GitHub Actions — Standard Pattern

Nearly every Rust repo has a standard CI workflow:
```yaml
on: [push, pull_request] → branches: [main, master]
jobs:
  check: cargo check --all-features
  test: cargo test --all-features
  clippy: cargo clippy --all-features -- -D warnings
  fmt: cargo fmt --all -- --check
```

Repos with CI: 30+ out of 37. Python repos (plato-demo, entropy-flow-py) have separate `ci-python.yml` workflows.

### 7.2 Agent Workflow (construct-coordination)

A unique **Level-3 Agent Workflow** that turns GitHub Actions into a task executor:
- `workflow_dispatch` with `agent_task` input
- Runs arbitrary commands via `eval`, commits results
- Supports DeepSeek model integration via `DEEPINFRA_API_KEY`
- Uploads artifacts, generates step summary

### 7.3 Edge CI (deckboss-net)

Deploys via `npx wrangler deploy` — standard Cloudflare Workers deployment. No CI file found in the repo itself (manual deploy or external pipeline).

### 7.4 CI Infrastructure Summary

| Repo | CI Type | Coverage |
|------|---------|----------|
| 30+ Rust repos | `cargo check/test/clippy/fmt` | Standard |
| plato-demo | rust + python CI | Multi-language |
| oracle1-vessel | CI + python CI | Multi-language |
| construct-coordination | CI + agent workflow | Advanced |
| deckboss-net | wrangler deploy | Edge |
| entropy-flow-py | pytest CI | Python-only |

---

## 8. Key Observations

### 8.1 The PLATO Nervous System Paradigm

PLATO is more than a monitoring system — it's a **spatial reasoning engine** where:
- Rooms = cells in a tensor grid with 5 depth levels
- Agents = batons passing through rooms with immutable state
- Sensors = ternary signals {-1, 0, +1}
- Fleet = consensus voting across ternary vectors
- Safety = assertion traps + TutorLoop self-correction

### 8.2 The Conservation Law Thread

The conservation law `γ + η = C` runs through the entire cluster:
- `conservation-verify-c` proves it empirically (avoidance ratio conserved across 3 orders of magnitude)
- `conservation-spectral-topology-rs` measures it topologically
- `meta-agent` applies it to task scheduling
- `fleet-dedup` applies it to repo hygiene
- `amd-bf16-tools` tests it numerically (hypothesis rejected)

### 8.3 Edge Infrastructure Is Fragmented

- Cloudflare: deckboss-net (single worker, demo), plato-demo (configuration)
- GPU Edge: cudaclaw, git-cuda-agent (CUDA + Rust)
- WASM Edge: lever-runner-wasm (browser deployment)
- No unified edge deployment tooling — each repo deploys independently

### 8.4 The I2I Protocol Is the Glue

The agent-to-agent communication protocol (20 message types, git-native, trust-based) is how the 9 active agents coordinate. No message brokers, no databases, no persistent connections — just repos, commits, and conventions.

### 8.5 Fleet Health Is Measurable But Not Automated

- fleet-scanner exists and works (592 repos in seconds)
- fleet-mapper works (599 repos in 22 seconds)
- fleet-dedup produces actionable plans
- But only 7% of repos have CI/CD — health detection is a one-shot tool, not an automated pipeline

---

## 9. Repo-by-Repo Summary

| # | Repo | Lang | Purpose | Infra Role |
|---|------|------|---------|------------|
| 1 | plato-dashboard | Rust | Fleet dashboard UI | PLATO visualization |
| 2 | plato-demo | Python | 5-atom reasoning demo | PLATO demo |
| 3 | plato-fleet-manager | Rust | Room orchestrator | Core fleet mgmt |
| 4 | plato-mythos | Python | RDT neural architecture | ML inference |
| 5 | plato-runtime-kernel | Rust | Spatial spreadsheet engine | PLATO brain |
| 6 | plato-ternary-bridge | Rust | Sensor→ternary bridge | Sensor fusion |
| 7 | construct-coordination | Markdown | Fleet coordination surface | Fleet comms |
| 8 | deckboss-net | TypeScript | Cloudflare Worker | Edge demo |
| 9 | superinstance-embedder | Rust | 32D crate embeddings | Search infra |
| 10 | c-ternary | C | C99 ternary logic header | Low-level ternary |
| 11 | cudaclaw | Rust+CUDA | GPU agent orchestrator | GPU compute |
| 12 | fastloop-guard | Rust | LLM call cache daemon | Performance |
| 13 | fleet-dedup | Rust | Duplicate repo detection | Fleet hygiene |
| 14 | fleet-mapper | Rust | Fleet fingerprint & tag | Fleet analysis |
| 15 | fleet-scanner | Rust | Fleet health scan | Fleet health |
| 16 | cross-compile-checker | Rust | Cross-compile compat | Build infra |
| 17 | amd-bf16-tools | Rust | BF16 hypothesis test | ML perf |
| 18 | meta-agent | Rust | Task dispatch coordinator | Agent orchestration |
| 19 | oracle1-vessel | Markdown | Lighthouse Keeper agent | Fleet command |
| 20 | oracle1-workspace | Mixed | Archived experiment | (superseded) |
| 21 | position-aware-embed | Rust | Position-weighted embedding | Search infra |
| 22 | spectral-prosody | Rust | Poetry spectral analysis | Math |
| 23 | entropy-flow-py | Python | Information theory | Math |
| 24 | entropy-lint | Rust | Code entropy analysis | Code quality |
| 25 | conservation-spectral-topology-rs | Rust | Spectral topology conservation | Math/verify |
| 26 | conservation-verify-c | C | Scale-invariant law verification | Math/verify |
| 27 | crate-graph | Rust | Dep graph analysis | Fleet analysis |
| 28 | git-graph-rs | Rust | Git repos as agent graphs | Agent infra |
| 29 | auto-changelog | Rust | Conventional commit changelog | Dev tooling |
| 30 | bench-compare | Rust | Benchmark comparison | Dev tooling |
| 31 | room-cell | Rust | Fundamental room atom | PLATO core |
| 32 | shell-history-analyzer | Rust | Shell pattern discovery | Dev tooling |
| 33 | lau-memory-arena | Rust | Arena allocator | Game/GPU |
| 34 | git-cuda-agent | Rust+CUDA | GPU agent template | GPU edge |
| 35 | lever-runner-carapace | Rust | Native performance layer | Edge runtime |
| 36 | lever-runner-wasm | Rust | WASM browser pipeline | Edge runtime |
| 37 | local-vector-search | Rust | Local TF-IDF search | Search infra |

---

## 10. Gaps & Recommendations

1. **No unified CI/CD pipeline** — Each repo has its own GitHub Actions CI with no fleet-wide pipeline or publish automation
2. **Edge deployment is ad-hoc** — deckboss-net (Wrangler), lever-runner-wasm (wasm-pack), cudaclaw (Cargo) — no common deployment abstraction
3. **Fleet health is manual** — fleet-scanner/mapper are CLI tools, not persistent services
4. **No health dashboard** — plato-dashboard exists but no fleet-wide health aggregation for the 1,431-repo ecosystem
5. **No I2I router** — Beachcomb polling works but a fleet-wide message router doesn't exist
6. **CI/CD gap** — Only 7% of repos have CI/CD automation (fleet-scanner metric)
