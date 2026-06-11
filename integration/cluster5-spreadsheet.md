# Cluster 5: Spreadsheet & Data Ecosystem

**Study Date:** 2026-06-11  
**Repos Analyzed:** 18  
**Data Flow:** Cells → Grid → Engine → Conservation → Visualizations → Fleet Agents

---

## Executive Summary

Cluster 5 is a **multi-layered spreadsheet intelligence ecosystem** spanning Rust, Python, and TypeScript. The core thesis: *every cell is an agent, every formula is a computation, every recalculation is evolution, and conservation laws keep the whole system thermodynamically honest.* The ecosystem bridges from atomic ternary cells (-1, 0, +1) through engine-driven grids and evolutionary formulas, up to browser-based visualization (polln) and fleet agent bridging.

---

## 1. Repository Map

| Repo | Language | Role | Layer |
|------|----------|------|-------|
| `ternary-cell` | Rust | Atomic ternary cell (3 bytes) | Foundation |
| `ternary-cell-python` | Rust/Python | Python FFI bindings for ternary-cell | Foundation |
| `room-cell` | Rust | Room-as-atom with JEPA/vibe/murmur/gc/conservation | Foundation |
| `ternary-spreadsheet` | Rust | Grid + formula engine + sort/fitness/heatmap | Engine |
| `spreadsheet-engine` | Rust | Full 7-cell-type living spreadsheet engine | Engine |
| `spreadsheet-cells` | Python | Cell simulator with TE-weighted topology + sparklines | Simulation |
| `spreadsheet-plr-bridge` | Rust | Music theory (PLR group) bridged to spreadsheet formulas | Extension |
| `si-superinstance` | Python | Exhaustive ternary strategy search (EXHAUSTIVE) | Algorithm |
| `ternary-som` | Rust | Self-organizing maps for ternary data | Algorithm |
| `ternary-sampler` | Rust | Statistical sampling for ternary populations | Algorithm |
| `ternary-trees` | Rust | Decision trees & random forests for ternary data | Algorithm |
| `ternary-failure` | Rust | FMEA / fault-tree / reliability analysis (ternary) | Analysis |
| `ternary-fault-tree` | Rust | Ternary fault trees (+1=healthy, 0=degraded, -1=failed) | Analysis |
| `ternary-experiment` | Rust | Parameter sweep runner for ternary agent simulations | Analysis |
| `ternary-frontier` | Rust | Exploration frontier tracking over ternary state space | Analysis |
| `spreadsheet-projection` | Python | PLATO rooms → spreadsheet rendering (3rd-person view) | Visualization |
| `polln` | TypeScript | Interactive tile-to-spreadsheet rendering + real-time updates | Visualization |
| `superinstance-spreadsheet` | HTML/JS | Browser demo: ternary agents evolving in a live spreadsheet | UI Demo |

---

## 2. Data Flow Architecture

```
TERNARY CELLS → GRID → ENGINE → CONSERVATION → VISUALIZATION → FLEET BRIDGE
   (foundation)          (structure)    (evaluation)    (monitoring)    (UI)           (agents)
```

### Layer 0: Foundation — Ternary Cells (ternary-cell)

The atomic unit is **3 bytes**: `state (-1/0/+1) + dwell (ticks in state) + flips (lifetime transitions)`.

Key operations:
- `set()`, `tick()`, `flip()` — state transitions
- `tunnel()` — escape from 0 to target state (forgiveness)
- `trap()` — forced return to 0
- `from_byte()` — deterministic seed-to-state mapping

**room-cell** extends this to a full "Room" with:
- **Embedding<D>** — D-dimensional perception vectors
- **JEPA predictor** — average of last N embeddings
- **Surprise** — cosine distance between predicted and actual
- **Vibe** — 16D state vector updated via finite-difference surprise
- **Murmur** — compressed room summary for gossip
- **GC** — prune low-surprise entries, keep the surprising ones
- **Conservation** — |perception_db| ≈ |prediction_db| within tolerance

The 6-phase tick cycle: `predict → perceive → surprise → vibe → gc → conservation`

### Layer 1: Grid + Engine (spreadsheet-engine + ternary-spreadsheet)

**spreadsheet-engine** (Rust) provides the full living spreadsheet:

- **Grid**: Sparse `HashMap<CellId, Cell>` with explicit dependency tracking (bidirectional edges)
- **Engine**: Tick loop evaluating cells in topological order (Kahn's algorithm)
- **7 Cell Types**: Value, Agent, Training, Simulation, A2A, MIDI, Formula
- **A2ABus**: Inter-cell message routing (announce → query → update cycle)
- **CellId**: Excel-style labels (A1, B2) with row/col addressing

The formula engine supports both standard operations (SUM, AVG, COUNT, MAX, MIN, arithmetic) and **evolutionary formulas**:

| Formula | Purpose |
|---------|---------|
| `EVOLVE(range, gens)` | Genetic optimization over cell values |
| `SPECIES(range, k)` | Cluster cells by similarity |
| `PARETO(range)` | Find Pareto-optimal cells |
| `ENTROPY(range)` | Shannon entropy (diversity measure) |
| `CONSERVE(range)` | Verify γ + η = budget across cells |

**ternary-spreadsheet** (Rust) is a parallel implementation focused specifically on ternary {-1, 0, +1} values:
- Grid with row/col operations
- `FormulaEngine` with `EVOLVE`, `BEST`, `SPECIES`, `EXHAUSTIVE`, `ENTROPY`
- `sort_by_fitness()` — natural selection as sort
- `autofill_mutate()` — autofill with controlled randomness
- `conditional_format()` — fitness-based coloring (green/yellow/red)
- `fitness_heatmap()` — normalized [0,1] grid heatmap

### Layer 2: Conservation Law

The **conservation law** is the system's thermodynamic backbone:

> **γ (compute spend) + η (memory usage) = budget**

- `ConservationMonitor` tracks fleet-wide health (0.0–1.0)
- `ConservationTrend`: Improving / Stable / Degrading
- Violations detected per-cell (individual agents exceeding budget)
- History recorded per tick for trend analysis
- The `CONSERVE` formula treats triples (gamma, eta, budget) as cell values

This is not arbitrary — it mirrors Noether's theorem: symmetry (budget invariance) → conserved quantity.

### Layer 3: Algorithms & Analysis

| Crate | Function |
|-------|----------|
| **si-superinstance** | `exhaustive()` enumerates all 3^N ternary strategies in 1ms for N=4 |
| **ternary-som** | Competitive learning SOM with Gaussian neighborhood, ternary distance, U-matrix |
| **ternary-sampler** | 5 sampling strategies: random, stratified, weighted, reservoir, importance |
| **ternary-trees** | Decision trees & random forests with ternary branching (3-way splits) |
| **ternary-failure** | FMEA with RPN, fault trees with ternary gates, reliability models |
| **ternary-fault-tree** | Ternary fault propagation (healthy/degraded/failed) through AND/OR/VOTE gates |
| **ternary-experiment** | Parameter sweeps: tunnel_rate, trap_rate, forgiveness → survival metrics |
| **ternary-frontier** | Exploration frontier tracking (known/frontier/unknown), pioneer bonuses |

**Key insight from si-superinstance**: For N=4 (81 strategies), you can enumerate all strategies and rank them in milliseconds. No gradient descent, no training loop. The cost is O(3^N) — for N=4 it's instant, for N=8 it's ~1 second.

### Layer 4: Visualization

**spreadsheet-projection** (Python):
- Each PLATO room becomes a spreadsheet sheet
- Each PLATO tile becomes a cell row
- `SpreadsheetProjection` with `SpreadsheetCell` type system (tile, room, app, folder, file, string, value, array, instance, graph_node)
- `cascade_from(cell_id)` — dependency propagation simulation
- `find_bottlenecks()` — cells with most dependents
- `find_break_points()` — cells with many deps but low confidence
- `to_deckboss_flowchart()` — toggle between sheet view and graph view
- Cross-room dependency tracking

**polln** (TypeScript):
- Next.js app with Prisma/PostgreSQL backend
- Interactive tile-to-spreadsheet rendering
- Real-time WebSocket updates (WebSocket example included)
- Shadcn/ui component library for spreadsheet UI
- Multi-room views combining tiles from multiple PLATO rooms
- Live tile changes reflected in spreadsheet view

**superinstance-spreadsheet** (HTML/JS):
- Browser-only demo (zero install, no server)
- Live heatmap, dendrogram, entropy chart, Pareto scatter, species pie
- 5 laws of negative-space intelligence: Conservation, Asymmetry, Exhaustion, Convergence, Emergence
- Natural selection via toolbar (Evolve, Mutate, Sort, Cull Weak)

---

## 3. How polln's Tile System Connects to Fleet Agents

**polln** serves as the **visualization frontend** for the fleet's tile data. The connection flows:

1. **PLATO rooms** produce tiles (from forge, flux, etc.)
2. **polln** renders these tiles as interactive spreadsheet rows
3. **spreadsheet-projection** provides the data model: `SpreadsheetCell` with `room_origin` and `tile_origin`
4. **Cross-room dependencies** in polln = fleet agents referencing each other's data
5. **Real-time updates** (WebSocket) = fleet agent state changes reflected instantly

The architectural flow: `PLATO room → tiles → SpreadsheetProjection.cells_from_room() → polln spreadsheet view → human operator → (adjust cells) → back to fleet agents`

**Current connection status**: polln reads PLATO room data but has **no write-back path** — cells can't send commands back to fleet agents through the spreadsheet. This is a critical gap.

---

## 4. The Cell-to-Fleet Bridge (scripts/cell-to-fleet-bridge.py)

### Current State

The existing bridge (`scripts/cell-to-fleet-bridge.py`) connects `spreadsheet-cells` cell simulation output to the fleet MIDI conductor:

```
cell_simulator → cell values → ternary quantization → POST /think (conductor) → agent analysis
```

**It does:**
- Run cell simulation with configurable topology (ring/random/full)
- Quantize float values to ternary {-1, 0, +1}
- Conservation check (sum of ternary vector)
- POST to conductor's `/think` endpoint with hardcoded targets (chord, scale, melody, bass, expression)
- Dry-run mode for testing

**It does NOT (missing integration points):**

| Missing Feature | Impact | Complexity |
|---|---|---|
| **Bidirectional A2A bus** | One-way only: cells → conductor. No agent state flows back into cells. | High |
| **spreadsheet-engine CellId addressing** | Bridge uses flat array indices, not A1/B2/CellId grid addressing | Medium |
| **ConservationMonitor integration** | Bridge does a simple Σ check, not the full γ+η=budget tracking with trend analysis | Medium |
| **Formula evaluation** | No EVOLVE/SPECIES/PARETO/ENTROPY formulas — just AVG + RNG | Medium |
| **7 cell types** | Bridge only simulates one cell type, not Agent/Training/Simulation/A2A/MIDI/Formula | High |
| **Polln/visualization output** | No polln UI update; bridge outputs to console only | Low |
| **spreadsheet-projection type system** | No cell type metadata (tile/room/instance/graph_node) | Low |
| **Ternary cell atomic operations** | No dwell/flip/tunnel/trap — just float quantization | Low |
| **Parameter sweep (ternary-experiment)** | No multi-run analysis or phase transition detection | Low |
| **Fault tolerance (ternary-fault-tree)** | No degradation monitoring for agent cells | Low |
| **PLR music bridge** | Plugs only into MIDI agents, not the formula-level PLR bridge | Medium |
| **Exhaustive strategy search** | No `=EXHAUSTIVE()` — bridge doesn't enumerate strategy space | Medium |
| **Conservation law enforcement** | Reports drift but doesn't enforce budget rebalancing | Medium |

### Integration Tier Map

```
┌─────────────────────────────────────────────────────────────┐
│                       TIER 0: SPREADSHEET                    │
│  spreadsheet-engine (Rust) → cell values → engine.tick()    │
│  ternary-spreadsheet (Rust) → formula evaluation            │
│  Cell types: Value, Agent, Training, Simulation, A2A, MIDI  │
│  ConservationMonitor → γ+η=budget fleet-wide                │
│  A2ABus → inter-cell message routing                        │
└─────────────────────┬───────────────────────────────────────┘
                      │ via PyO3 / FFI / HTTP
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    TIER 1: BRIDGE LAYER                      │
│  cell-to-fleet-bridge.py (EXISTING, needs expansion)        │
│  ┌─ SpreadsheetCells ← Rust grid cell engine               │
│  ├─ ConservationCheck ← ConservationMonitor snapshot        │
│  ├─ Ternary quantization                                   │
│  ├─ POST /think → conductor                                 │
│  └─ (MISSING)←GET /state from conductor → update cells     │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌──────────────┐ ┌───────────┐ ┌──────────┐
│  TIER 2a:    │ │ TIER 2b:  │ │TIER 2c:  │
│  FLEET MIDI  │ │ polln UI  │ │ PLATO    │
│  /think      │ │ tiles     │ │ rooms    │
│  chord,scale │ │ WebSocket │ │ women    │
│  melody,bass │ │ real-time │ │ forge    │
│  expression  │ │ updates   │ │ flux     │
└──────────────┘ └───────────┘ └──────────┘
```

---

## 5. Key Patterns Discovered

### Pattern 1: Cell as Universal Primitive
Every system in this cluster treats the "cell" as the fundamental unit — whether it's a 3-byte ternary cell (ternary-cell), a spreadsheet grid cell (spreadsheet-engine), a PLATO room cell (room-cell), a PLATO tile (spreadsheet-projection), or a MIDI note (spreadsheet-plr-bridge). The cell abstraction unifies the entire cluster.

### Pattern 2: Conservation as Thermodynamic Backbone
The conservation law (γ + η = budget) appears in different forms across the cluster:
- spreadsheet-engine: `ConservationMonitor` with trend analysis
- room-cell: `|perception_db| ≈ |prediction_db|`
- ternary-fault-tree: Ternary gates preserve degradation state
- spreadsheet-plr-bridge: Voice-leading distance budget (20 semitones)
- ternary-experiment: Conservation of population size during evolution

### Pattern 3: Evolution as Computation
Evolution is treated as a **formula**, not a separate system:
- `=EVOLVE(B2:B50, 100)` — run natural selection as a spreadsheet function
- `sort_by_fitness()` — sorting IS natural selection
- `autofill_mutate()` — autofill IS reproduction with mutation
- `EXHAUSTIVE(C)` — exhaustive enumeration IS the computation

### Pattern 4: Ternary as Universal Signal Encoding
The {-1, 0, +1} encoding is the backbone:
- `ternary-cell`: atomic units
- `ternary-som`: SOM clustering
- `ternary-trees`: decision tree splits
- `ternary-sampler`: sampling strategies
- `ternary-frontier`: state space exploration
- `ternary-failure`: failure severity classification
- `cell-to-fleet-bridge`: agent state quantization

### Pattern 5: TypeScript/Python/Rust Layering
- **Rust**: Core computational engine (spreadsheet-engine, ternary-*, room-cell)
- **Python**: Modeling/bridging layer (spreadsheet-cells, si-superinstance, spreadsheet-projection, cell-to-fleet-bridge)
- **TypeScript**: Visualization/browser layer (polln, superinstance-spreadsheet frontend)

---

## 6. Critical Integration Points

### Immediate (Priority #1)
1. **Bidirectional bridge**: Add `/state` GET from conductor → update spreadsheet cells
2. **A2A bus bridge**: Map `spreadsheet-engine::A2ABus` messages to fleet MIDI `/think` targets
3. **ConservationMonitor output**: Replace simple Σ check with full health/trend/violations report

### Short-term (Priority #2)
4. **polln write-back**: Add cell editing → POST to fleet agents
5. **Formula evaluation pipeline**: EVOLVE/SPECIES/PARETO/ENTROPY as fleet agent tasks
6. **PLR bridge integration**: Spreadsheet formulas that use PLR operations for musical agent targeting
7. **Ternary cell state preservation**: Use dwell/flip/tunnel/trap instead of raw float quantization

### Medium-term (Priority #3)
8. **spreadsheet-projection integration**: Use cell type metadata (tile/room/instance) in bridge output
9. **Exhaustive strategy search**: Add `=EXHAUSTIVE()` as a fleet analysis pipeline
10. **Fault tree monitoring**: ternary-fault-tree propagation for agent health degradation

---

## 7. Repo Files On Disk

All 18 repos cloned to: `/home/ubuntu/.openclaw/workspace/integration-study/cluster5/`

| Repo | Path |
|------|------|
| spreadsheet-engine | `./spreadsheet-engine/` |
| spreadsheet-cells | `./spreadsheet-cells/` |
| spreadsheet-projection | `./spreadsheet-projection/` |
| spreadsheet-plr-bridge | `./spreadsheet-plr-bridge/` |
| superinstance-spreadsheet | `./superinstance-spreadsheet/` |
| si-superinstance | `./si-superinstance/` |
| polln | `./polln/` |
| room-cell | `./room-cell/` |
| ternary-cell | `./ternary-cell/` |
| ternary-cell-python | `./ternary-cell-python/` |
| ternary-spreadsheet | `./ternary-spreadsheet/` |
| ternary-som | `./ternary-som/` |
| ternary-sampler | `./ternary-sampler/` |
| ternary-trees | `./ternary-trees/` |
| ternary-failure | `./ternary-failure/` |
| ternary-fault-tree | `./ternary-fault-tree/` |
| ternary-experiment | `./ternary-experiment/` |
| ternary-frontier | `./ternary-frontier/` |

Bridge script: `/home/ubuntu/.openclaw/workspace/scripts/cell-to-fleet-bridge.py`

Integration docs: `superinstance-spreadsheet/docs/WORLD-MODEL-BRIDGE.md` (spreadsheet-as-world) and `superinstance-spreadsheet/docs/FUTURE-INTEGRATION.md` (future integration roadmap)
