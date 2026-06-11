# Fleet Character System — Master Integration Plan

**Generated:** 2026-06-11  
**Sources:** 7 cluster reports (2,222 lines), 200+ SuperInstance repos analyzed  
**Author:** oracle2 (Claude Code + Kimi CLI + DeepSeek V4 Flash)

---

## The Big Picture

The SuperInstance fleet has **200+ repos** across 7 clusters, but they're islands. This plan connects them into a unified agent ecosystem:

```
                        ╔═══════════════════════╗
                        ║    PLATO NERVOUS      ║  ← Cluster 6: Room topology,
                        ║       SYSTEM          ║     fleet manager, const-coord
                        ╚════════════╤══════════╝
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
       ┌──────┴──────┐       ┌──────┴──────┐       ┌──────┴──────┐
       │   FLEET     │       │   16 FLEET  │       │  EDGE/NEBULA│
       │  CHARACTER  │◄─────►│  MIDI AGENTS│◄─────►│  WORKER     │
       │   SYSTEM    │       │ (oracle2)   │       │ (deckboss)  │
       └──────┬──────┘       └──────┬──────┘       └──────┬──────┘
              │                     │                     │
       ┌──────┴──────┐       ┌──────┴──────┐       ┌──────┴──────┐
       │ Cluster 1   │       │  Cluster 4   │       │  Cluster 6  │
       │ Character   │       │  Signal/Music│       │  PLATO Infra│
       │ (identitiy) │       │  (algorithms)│       │  (scaffold) │
       └──────┬──────┘       └──────┬──────┘       └──────┬──────┘
              │                     │                     │
       ┌──────┴──────────────────────┴──────────────────────┴──────┐
       │                    CLUSTER 2                              │
       │         Ternary Math Foundation (Z₃ arithmetic)           │
       └───────────────────────────────────────────────────────────┘
```

---

## Priority Matrix

| Priority | Integration | Clusters Involved | Effort | Impact |
|----------|-------------|-------------------|--------|--------|
| 🔴 P0 | **Port signal/music algos** to fleet-agent.py | C4 → fleet-agent | 3 days | HIGH |
| 🔴 P0 | **Character endpoints** (GET /sheet, POST /dream) | C1 → fleet-agent | 1 day | HIGH |
| 🟡 P1 | **Ternary-captain conductor** — leadership delegation | C3 → conductor | 2 days | HIGH |
| 🟡 P1 | **Cell-to-fleet bidirectional bridge** | C5 → fleet-bridge | 2 days | MED |
| 🟢 P2 | **PLATO room injection** — agents as room entities | C6 → PLATO | 3 days | MED |
| 🟢 P2 | **Active inference agents** — surprise-driven reasoning | C7 → agent-think | 3 days | MED |
| 🔵 P3 | **Deckboss fleet edge** — CF Worker agent health | C6 → nebula | 1 day | LOW |
| 🔵 P3 | **polln character dashboard** — agent visualization | C5 → dashboard | 2 days | LOW |
| 🔵 P3 | **Competitive evolution** — agent-riff v4 duels | C1 → arena | 3 days | LOW |

---

## P0 Implementation Plan

### P0-1: Port Cluster 4 → fleet-agent.py (Highest ROI)

Each agent method in fleet-agent.py currently uses simple heuristics (thresholds, direction checks). Cluster 4 provides mature Rust implementations that can be ported or FFI'd.

**Replacement Map:**

| Agent Port | Current Heuristic | Cluster 4 Replacement | Lines |
|------------|-------------------|----------------------|-------|
| chord (:2160) | major/minor/power guess | ternary-music TernaryChord | ~80 |
| scale (:2161) | mode guess by spread | ternary-temperament intervals | ~60 |
| voicing (:2162) | brightness count | ternary-counterpoint species | ~100 |
| tempo (:2163) | bpm thresholds | ternary-tempo time perception | ~50 |
| groove (:2170) | swing threshold | ternary-rhythm Björklund | ~70 |
| melody (:2174) | contour (first/last) | ternary-muse pattern + motif | ~80 |
| bass (:2175) | step pattern | ternary-kuramoto phase | ~60 |

**Files to modify:**
- `fleet-agent/fleet-agent.py` — Replace heuristic methods with proper ports
- `fleet-characters/fleet_characters/signal/` — New module for signal processing ports

### P0-2: Character Endpoints

Already designed in fleet-characters/:

| Endpoint | Method | Description |
|----------|--------|-------------|
| GET /character | GET | Full character profile (stats, class, arc, dream) |
| GET /sheet | GET | Character sheet snapshot (exportable) |
| POST /think | POST → character | Processes cue + updates stats |
| POST /dream | POST | Trigger dream cycle |
| POST /encounter | POST | Challenge-mode request |

---

## Architecture Decisions

### Why not FFI to Rust crates directly?

The 200+ Rust crates are mature but:
1. **ARM64 compilation** — Oracle is aarch64, some crates have x86_64-specific SIMD
2. **Python ecosystem** — The fleet-agent.py is pure Python. Adding Rust compilation would break the simple deployment model
3. **FFI overhead** — Each MIDI request is <5ms; FFI call overhead (0.5-1ms) would be 10-20% of total time

**Decision:** Port key algorithms to Python with same semantics. Use Rust for heavy computation only where Python is >10x slower (ternary-core's matmul, ternary-sheaf's cohomology).

### Three-tier architecture

```
┌────────────────────────────────────────────────────────────────────┐
│  Tier 1: Fleet Character System (Python, no deps)                  │
│  fleet-characters/fleet_characters/                                │
│  - Stats, class emergence, arc narrative, dream cycles             │
│  - Ported signal/music algorithms from Cluster 4                   │
│  - No external dependencies — pure Python 3.10+                    │
├────────────────────────────────────────────────────────────────────┤
│  Tier 2: Fleet Agent Bridge (Python + HTTP + systemd)              │
│  fleet-agent/fleet-agent.py + fleet-characters/characters-agent.py │
│  - 16 agent processes with character identity                     │
│  - I2I protocol for cross-agent communication                     │
│  - systemd services for dream scheduling                          │
├────────────────────────────────────────────────────────────────────┤
│  Tier 3: Fleet Infrastructure (Rust + TypeScript + CF Workers)      │
│  - ternary-core, ternary-sheaf for heavy computation               │
│  - polln for visualization                                          │
│  - deckboss-net for edge health checks                             │
│  - PLATO room integration for spatial awareness                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## File Map

```
fleet-characters/
├── fleet_characters/
│   ├── __init__.py          # Package init (done)
│   ├── stats.py             # 6 stats, growth functions (done)
│   ├── class_.py            # 16-class emergence (done)
│   ├── arc.py               # Narrative arc, chapters (done)
│   ├── dream.py             # Dream cycle, consolidation (done)
│   ├── agent_profile.py     # Combined character wrapper (done)
│   ├── signal/              # ← NEW: Cluster 4 ports
│   │   ├── __init__.py
│   │   ├── chord.py         # ternary-music port
│   │   ├── scale.py         # ternary-temperament port
│   │   ├── voicing.py       # ternary-counterpoint port
│   │   ├── rhythm.py        # ternary-rhythm port
│   │   ├── melody.py        # ternary-muse port
│   │   └── predict.py       # ternary-predict port
│   └── coordination/        # ← NEW: Cluster 3 ports
│       ├── __init__.py
│       ├── leadership.py    # ternary-captain port
│       ├── consensus.py     # ternary-paxos port
│       └── trust.py         # ternary-trust port
├── integration/
│   ├── cluster1-character.md          (done)
│   ├── cluster2-ternary-math.md       (done)
│   ├── cluster3-agent-systems.md      (done)
│   ├── cluster4-signal-music.md       (done)
│   ├── cluster5-spreadsheet.md        (done)
│   ├── cluster6-plato-infra.md        (done)
│   ├── cluster7-special-science.md    (done)
│   └── INTEGRATION-MASTER-PLAN.md     (this file)
├── characters-agent.py     # ← NEW: fleet-agent.py with character
├── README.md               # ← needs update
└── setup.py                # ← needs creation
```

---

## Metric Targets

After full integration:

| Metric | Current | Target |
|--------|---------|--------|
| Agent identity | Stateless | 16 unique characters |
| Agent memory | None | Dream-consolidated patterns |
| Cross-agent coordination | None | I2I + captain leadership |
| Signal processing | Heuristics | Proper algorithmic (ported) |
| Visualization | None | polln character dashboard |
| Edge monitoring | None | deckboss health checks |
| Evolutionary pressure | None | agent-riff duels |

---

## Next Steps

### Immediate (this session):
1. ✅ All 7 cluster reports complete
2. ✅ Integration plan written
3. 🔴 **Build signal/ ports** (Cluster 4 → Python)
4. 🔴 **Build characters-agent.py** (character endpoints)

### Next session:
5. Build coordination/ ports (Cluster 3 → Python)  
6. Polln dashboard integration
7. Deckboss edge worker
8. Agent-riff competitive loop
