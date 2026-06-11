# Cluster 3: Agent Systems & Coordination

> Study of the SuperInstance Rust ternary crate family across 35 repos covering agent orchestration, communication, consensus, routing, trust, and fleet management.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Agent Lifecycle & Leadership](#1-agent-lifecycle--leadership)
3. [Consensus & Decision-Making](#2-consensus--decision-making)
4. [Communication & Messaging](#3-communication--messaging)
5. [Spatial & Topological Organization](#4-spatial--topological-organization)
6. [Resource Management & Logistics](#5-resource-management--logistics)
7. [Trust & Relationship Dynamics](#6-trust--relationship-dynamics)
8. [Verification & Proof](#7-verification--proof)
9. [Ecosystem & Persistence](#8-ecosystem--persistence)
10. [Command & Control](#9-command--control)
11. [Integrated Fleet-MIDI Usage Guide](#10-integrated-fleet-midi-usage-guide)

---

## Executive Summary

Cluster 3 forms the **coordination and leadership layer** of the SuperInstance ternary fleet. These 35 repos implement a complete stack for multi-agent systems: from raw message passing (ternary-channel, ternary-bus) through consensus (ternary-paxos, ternary-quorum) and leadership (ternary-captain) to emergent ecosystem patterns (ternary-reef, ternary-symbiont).

**Core architectural pattern**: Every crate adopts the `{-1, 0, +1}` balanced ternary model — decisions, stances, priorities, weights, votes, and health states all collapse to tri-state. This isn't cosmetic; it maps directly to Kleene three-valued logic for verification (ternary-proof), Z₃ arithmetic for consensus (ternary-paxos), and five-stage trust progression (ternary-trust).

**Key insight for fleet-midi**: The conductor can use ternary-captain for leadership delegation, ternary-paxos for consensus about model routing decisions, and ternary-room with ternary-navigator for spatial agent organization. The whole becomes a coordinated fleet rather than a collection of independent agents.

---

## 1. Agent Lifecycle & Leadership

### ternary-agent
**Core agent abstraction.** Defines agent identity, state, and lifecycle within a ternary {-1, 0, +1} framework. The foundation that all other agent-related crates build on.

**Key patterns:**
- Ternary state machine for agent behavior
- Identity/role tracking
- Lifecycle hooks (init/run/terminate)

### ternary-captain
**Leadership pattern for fleet coordination.** A `Captain` struct leads a group of agents, supported by a `DecisionEngine` (ternary majority voting), `Delegator` (task assignment by specialization + fitness), `SituationRoom` (aggregates ternary sensor reports from agents), `FleetReport` (status aggregation), and `SuccessionPlan` (captain handoff).

**Key patterns:**
- `DecisionEngine::decide()` — majority vote on `{Neg, Zero, Pos}` votes
- `DecisionEngine::decide_weighted()` — weighted vote with per-agent weights
- `Delegator::assign()` — picks best-fit agent by specialization match + fitness score
- `SituationRoom::aggregate()` — ternary majority of agent reports
- `FleetReport::health()` — ratio of Ready agents to total
- `SuccessionPlan::heir()` / `promote_next()` — captain handoff line

**Fleet-midi integration:** The conductor directly maps to `Captain`. Each MIDI note channel can be a `Delegator` assignment. Model switching decisions use `DecisionEngine` with weighted votes from each active agent's performance metrics.

### ternary-navigator
**Wayfinding and pathfinding across rooms.** Ternary-weighted A* pathfinding where edges are `{Approach, Neutral, Avoid}` (-1, 0, +1). Avoid edges are excluded; Approach edges get cost reduction. Includes `RoutePlanner` (BFS multi-hop room routing), `DeadReckoning` (velocity-based position estimation), `Compass` (ternary direction classification), and `MapRoom` (spatial topology registry).

**Key patterns:**
- `PathFinder::find_path()` — A* with ternary cost adjustments
- `RoutePlanner::plan()` — BFS shortest room sequence
- `DeadReckoning::estimate()` / `correct()` — position drift + correction
- `MapRoom::closest_to()` — nearest room to position

**Fleet-midi integration:** Agent repertoire navigation. When agents need to sequence through their available models/skills, Navigator finds the path with preferred transitions. Avoid edges = conflicting states, Approach = synergistic transitions.

### ternary-ensign
**Specialist agent pattern.** An `Ensign` trait defines a domain specialist with `domain()` and `handle(task)`. Includes `EnsignRegistry` (domain→ensign map), `EnsignFactory` (on-demand creation via closures), `EnsignProxy` (API key/session management per domain), and `EnsignBridge` (domain→skill mapping with invocation log).

**Key patterns:**
- `EnsignRegistry::dispatch()` — route task to domain specialist
- `EnsignFactory::register()` / `create()` — lazy ensign creation
- `EnsignBridge::invoke()` — maps domains to construct-core skills

**Fleet-midi integration:** Each agent's specialized model (rhythm, melody, bass) becomes an Ensign loaded into the agent's repertoire. The conductor uses the Registry to dispatch musical tasks to the right specialist.

---

## 2. Consensus & Decision-Making

### ternary-paxos
**Full Paxos implementation in ~400 lines.** Classic two-phase consensus (`prepare → promise → accept → accepted → learner commits`) with ternary votes: `+1 (Accepted)`, `0 (Pending)`, `-1 (Rejected)`. Ballot monotonicity is the safety linchpin — higher ballots always win contention.

**Key patterns:**
- `Proposer` — drives rounds: `prepare()`, `receive_promise()`, `accept_request()`
- `Acceptor` — guards ballot monotonicity: `prepare()` → `Option<Promise>`, `accept()` → `Option<Accepted>`
- `Learner` — watches for majority quorum: `receive()`, `committed()`
- Safety: proposer *must* adopt highest previously-accepted value from promises

**Fleet-midi integration:** When multiple agents compete for the same resource (e.g., which model gets the next note), Paxos ensures **exactly one** wins without centralized coordination. The conductor can be the Proposer, agent types are Acceptors.

### ternary-quorum
**Distributed quorum voting with ternary options (`For`, `Abstain`, `Against`).** Configurable thresholds (simple majority, super-majority, unanimous). Multi-round voting with escalation. Vote tracking per agent per round prevents double-voting.

**Key patterns:**
- `QuorumThreshold::simple_majority()` / `super_majority()` / `unanimous()`
- `QuorumRound::advance()` — escalate to next voting round
- `QuorumConsensus::is_consensus()` — evaluates all rounds

### ternary-voting
**Voting system for ternary decisions.** Collects `{For, Against, Abstain}` votes from agents and resolves to a collective decision.

### ternary-agree (not in repo list — deduplicates to ternary-quorum/paxos)
For cluster 3 purposes, `ternary-quorum` and `ternary-paxos` cover the consensus surface area.

### ternary-negotiate
**Multi-agent negotiation using ternary stance space.** Agents adopt stances `{-1, 0, +1}` during negotiations. Supports multi-round bargaining with stance mutation.

**Fleet-midi integration:** Agents negotiate tempo, key, or instrument prioritization. Each agent starts with a stance, adjusts through negotiation rounds until consensus converges.

---

## 3. Communication & Messaging

### ternary-channel
**Inter-room messaging backbone.** Typed channels with ternary priority: `{Negative, Neutral, Positive}`. Supports direct messages, broadcast, reliable delivery with acknowledgments and retries, and multiplexing multiple logical channels over one connection.

**Key patterns:**
- `ChannelState::Open | Closed | Blocked` — connection lifecycle
- `TernaryPriority` — message ordering
- Reliable delivery: acknowledgment + retry mechanism
- Multiplexing: many logical channels per physical connection

**Fleet-midi integration:** Intra-fleet message bus for agent-to-agent communication. High-priority messages (conductor commands) use `TernaryPriority::Positive`, status updates use `Neutral`, debug logs use `Negative`.

### ternary-bus
**Message bus for inter-agent communication.** Pub/sub bus where agents subscribe to topics and receive published messages.

**Fleet-midi integration:** Event notification system — agents publish "model X completed" events, conductor subscribes to all agent events for global state visibility.

### ternary-mesh
**Dynamic mesh networking with ternary-weighted connections.** Agents discover each other and form dynamic network topologies. Connection weights use `{-1, 0, +1}` to express link quality/trust.

### ternary-network
**Network layer for distributed ternary systems.** Abstract network primitives with ternary state propagation.

### ternary-beacon
**Service discovery and node advertisement.** Agents broadcast their presence and capabilities via beacons. Other agents discover available services in the fleet.

**Fleet-midi integration:** Agents broadcast their available models/skills via beacons. The conductor discovers what every agent can do.

---

## 4. Spatial & Topological Organization

### ternary-room
**Room abstraction for multi-agent environments.** Rooms contain agents and environment state (key-value map). Doors with ternary access control (`Locked | Open | OneWay`). `RoomCoordinator` handles agent transfers between rooms, checking door permissions.

**Key patterns:**
- `DoorAccess::Locked | Open | OneWay(RoomId, RoomId)` — access control
- `RoomCoordinator::transfer()` — agent moves between rooms with door validation
- `RoomBuilder` — fluent builder for rooms with initial agents/env
- `RoomHistory` — append-only event log (agent enter/leave events)
- `RoomState` — snapshot/restore for save/load

**Fleet-midi integration:** Each model/skill is a "room" with its own environment context. The conductor — or the agent itself — uses RoomCoordinator to transfer agents between model rooms (e.g., from "rhythm generation" room to "melody harmonization" room).

### ternary-reef
**Coral reef ecosystem pattern for long-lived collective intelligence.** Models persistent fleet structures that grow over time: `Coral` (persistent structure with `Seedling → Juvenile → Adult → Ancient` stages), `Polyp` (individual agent with health/energy/bindings), `Symbiodinium` (energy provider), `ReefZone` (spatial partition), and `BleachingEvent` (stress testing).

**Key patterns:**
- `Coral::grow()` — accumulate growth points, advance stage
- `Reef::feed_cycle()` — symbionts provide energy to polyps
- `Reef::trigger_bleaching()` — stress event damages polyps/corals
- `Reef::recovery_cycle()` — polyps spend energy to recover health

**Fleet-midi integration:** The fleet's shared knowledge base and emergent behaviors. Coral = long-lived skill patterns that persist across sessions. Polyp = individual agent sessions. Symbiont = external data sources (MIDI input, audio analysis). Bleaching = system stress events (model failure, resource exhaustion).

### ternary-tidepool
**Small protected environments for agent experimentation.** Isolated sandbox environments where agents can be tested with configurable conditions, observed without side effects, drained and reset.

**Fleet-midi integration:** Sandbox for testing new models before production deployment. Agents get duplicated into a tidepool where experimental models can be tested against known inputs without affecting the live fleet.

### ternary-harbor
**Docking pattern for agent arrival and berth management.** Models how agents arrive at rooms, get assigned berths (`Dock`), receive assistance from pilots and tugs, and are protected by breakwaters during failures.

### ternary-anchor
**Stability and persistence for rooms.** Anchor states: `Stowed → Deployed → Set → Dragging`. Drift monitoring, weighing anchor, finding stable ground, designated anchorage zones.

---

## 5. Resource Management & Logistics

### ternary-cargo
**Resource transport and logistics between rooms.** `CargoHold` (storage with capacity), `CargoShip` (transport with load/travel/unload), `TradeRoute` (established routes with transport cost), `Manifest` (cargo declaration with conservation-law verification), `CargoInspector` (anti-smuggling checks), and `Smuggler` (stealth transport of negative-value resources).

**Key patterns:**
- `CargoHold::store()` / `withdraw()` — resource management with capacity
- `CargoShip::load()` / `travel()` / `unload()` — transport lifecycle
- `CargoInspector::full_inspect()` — conservation + contraband + manifest match
- `Smuggler::hide()` / `clean_manifest()` — adversarial transport

**Fleet-midi integration:** Model state transfer between agent rooms. When an agent transitions from "melody generation" to "harmonization," CargoShip transports the intermediate representation. CargoInspector validates data integrity.

### ternary-steward
**Resource stewardship and sustainable management.** Budgeting, auditing, sustainability measurement, conservation enforcement, reporting, and intergenerational equity for ternary resources. Maps to the conservation law enforcement layer.

**Fleet-midi integration:** Manages system resource budgets — CPU, memory, model slots. Steward enforces that total fleet resource usage stays within budget, prevents single agents from starving others.

### ternary-symbiont
**Symbiotic relationships between agents.** Models `Mutualism` (both benefit), `Commensalism` (one benefits, neutral other), `Parasitism` (one benefits, other harmed). Includes `SymbiosisDetector` (discovers beneficial partnerships) and `SymbiosisEvolver` (co-evolves partner agents).

**Key patterns:**
- `SymbiosisPair` / `ParasiticPair` / `CommensalPair` — relationship types
- `SymbiosisDetector` — discovers mutually beneficial combinations
- `SymbiosisEvolver` — iteratively improves symbiotic pairs

**Fleet-midi integration:** Detects when two agent types perform better together (e.g., rhythm + bass models have mutualistic synergy). Evolver tunes pairs for optimal joint output. Detects parasitic relationships where one agent consistently degrades another's output.

---

## 6. Trust & Relationship Dynamics

### ternary-trust
**Five-stage trust model:** `Hostile → Wary → Neutral → Friendly → Allied`. Bidirectional trust scores (-1.0 to +1.0) between agent pairs. Supports trust decay (fades toward zero), forgiveness (negative scores slowly recover), and `ReputationScore` (aggregate trust across the network).

**Key patterns:**
- `TrustStage::from_score()` — maps -1.0..+1.0 to five discrete stages
- `TrustEvent::positive()` / `negative()` / `betrayal()` — action deltas
- `TrustNetwork::tick()` — applies decay + forgiveness across all relations
- `ReputationScore::from_network()` — aggregate reputation for one agent

**Fleet-midi integration:** Agents track trust in other agents' model outputs. A model that produces bad output gets a negative trust event. Trust influences routing — the conductor prefers trusted agents for critical nodes and avoids hostile agents.

---

## 7. Verification & Proof

### ternary-proof
**Verification returning trivalent verdicts:** `Invalid (-1)`, `Inconclusive (0)`, `Valid (+1)`. Implements Kleene three-valued logic for composition: `AND = min`, `OR = max`. Supports `Assertion` (claim + evidence + confidence), `ProofChain` (sequential verification with all/any/majority strategies), and `ChallengeResponse` (fuzzy matching via Levenshtein similarity).

**Key patterns:**
- `VerifyResult::and()` / `or()` — Kleene lattice composition
- `ProofChain::verify_all()` / `verify_any()` / `verify_majority()` — multiple strategies
- `ChallengeResponse::verify()` — exact match → Valid, fuzzy → Inconclusive
- Confidence thresholds: ≥0.9 → Valid, ≥0.5 → Inconclusive, <0.5 → Invalid

**Fleet-midi integration:** Model output verification. Assertion verifies that a generated note sequence meets criteria (key, tempo, valid range). Inconclusive → route to secondary validator. Invalid → discard and retry. ProofChain aggregates multiple verification layers (melodic, harmonic, rhythmic).

---

## 8. Ecosystem & Persistence

### ternary-reef
*(Covered in section 4 — reef ecosystem for long-lived structures.)*

### ternary-cache
**Caching layer.** Stores frequently-accessed ternary values with invalidation policies.

### ternary-database
**Persistence layer for ternary state.** Structured storage for agent state, room state, and decisions.

### ternary-archive
**Archival storage for historical fleet data.** Records past decisions, agent states, and system events for audit and replay.

**Fleet-midi integration:** Archive records every model decision for post-hoc analysis and training data collection.

### ternary-reassembly
**Five-layer stack for state reconstruction.** Handles partial state recovery after failures.

### ternary-distributed
**Distributed systems primitives.** Shared state, leader election, distributed counters, and coordination across the ternary {-1, 0, +1} state space.

### ternary-locks
**Distributed locking.** Mutual exclusion for shared resources across the fleet.

---

## 9. Command & Control

### ternary-command
**Command parsing and dispatch with ternary outcomes.** `CommandParser` (text→parsed command), `CommandRegistry` (verb→handler map), `CommandHistory` (audit trail with agent/location/timestamp), `AliasSystem` (shortcut expansion). Every command resolves to `Success`, `Partial`, or `Failure`.

**Key patterns:**
- `CommandParser::parse()` — tokenize raw text into verb + args
- `CommandRegistry::register()` / `get()` — verb routing
- `CommandHistory::by_agent()` / `by_result()` — filtered audit
- `AliasSystem::resolve()` — alias expansion with argument preservation

**Fleet-midi integration:** Natural-language command interface for the conductor. "Play C major arpeggio" → parsed verb "play", args ["C", "major", "arpeggio"]. Registry dispatches to the appropriate model route.

### ternary-scheduler
**Task scheduling with ternary priority.** Jobs scheduled by priority `{-1, 0, +1}` with configurable scheduling policies.

### ternary-scheduling-v2
**Second-generation scheduling.** Enhanced scheduler with more sophisticated priority handling, preemption, and fairness guarantees.

### ternary-swarm
**Swarm coordination patterns.** Flocking, task distribution, and emergent behavior across large agent collectives.

### ternary-shipyard
**Fleet construction and maintenance.** Builds, configures, and maintains fleets of agents. The shipyard is where fleets are assembled before deployment.

---

## 10. Integrated Fleet-MIDI Usage Guide

### Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                ternary-captain                    │
│  (Conductor — DecisionEngine + Delegator +       │
│   SituationRoom + SuccessionPlan)                │
└────────────────┬────────────────────────────────┘
                 │ commands via ternary-command
                 │ votes via ternary-voting
    ┌────────────┴────────────┐
    ▼                        ▼
┌──────────────┐   ┌─────────────────────┐
│ ternary-room │   │ ternary-negotiate    │
│ (model env)  │   │ (agent stances)      │
│              │   └──────────┬──────────┘
│ ternary-     │              │ consensus via
│ navigator    │   ┌──────────▼──────────┐
│ (pathfinding)│   │ ternary-paxos       │
└──────┬───────┘   │ (consensus engine)  │
       │           └──────────┬──────────┘
       ▼                      ▼
┌──────────────────────────────────────────────┐
│ ternary-channel / ternary-bus / ternary-mesh  │
│ (inter-agent communication)                  │
├──────────────────────────────────────────────┤
│ ternary-trust                                 │
│ (agent reputation network)                   │
├──────────────────────────────────────────────┤
│ ternary-proof                                 │
│ (output verification)                        │
├──────────────────────────────────────────────┤
│ ternary-reef / ternary-archive                │
│ (persistence + long-term memory)             │
└──────────────────────────────────────────────┘
```

### Specific Fleet-MIDI Integration Paths

#### Path 1: Conductor as Captain
The conductor wraps `ternary-captain::Captain`:
- **Roster**: References to all active fleet-midi agents
- **DecisionEngine**: Routes note-generation decisions by weighted vote (each agent's fitness score = past output quality)
- **Delegator**: Assigns specific MIDI channels/voices to agents based on specialization ("melody", "bass", "rhythm")
- **SituationRoom**: Collects agent reports about their output quality, available models, energy state
- **SuccessionPlan**: If conductor goes down, next agent in line takes over

#### Path 2: Consensus-Based Model Selection
When multiple models compete for the same output slot:
1. Each model type is a `ternary-paxos::Acceptor`
2. The conductor is the `ternary-paxos::Proposer` with value = "use model X"
3. Agents vote `Accepted`, `Pending`, or `Rejected`
4. `ternary-paxos::Learner` detects majority → model is committed
5. Ballot mechanism handles contention (retries with higher ballots)

#### Path 3: Trust-Weighted Routing
1. Each agent maintains a `ternary-trust::TrustNetwork` of trust scores for peers
2. When an agent fails (produces bad output), apply `TrustEvent::negative()`
3. Success → `TrustEvent::positive()`, Betrayal → `TrustEvent::betrayal()`
4. ReputationScore influences which agents get which routing slots
5. `TrustNetwork::tick()` applies decay (trust fades) and forgiveness (negative scores recover)

#### Path 4: Verification Pipeline
Each output note sequence goes through:
1. `ternary-proof::Assertion` with confidence ≥0.9 for "in key", "in tempo", "valid range"
2. `ternary-proof::ProofChain::verify_all()` — all assertions must be Valid
3. If `Inconclusive`: route to a secondary validator agent
4. If `Invalid`: discard, trigger `TrustEvent::negative()` on source agent, retry with different model

#### Path 5: Spatial Navigation of Skills
1. Each skill/model is a `ternary-room::Room` with its own environment
2. Agents move between rooms via `ternary-room::RoomCoordinator::transfer()`
3. `ternary-navigator::PathFinder` finds optimal path through skill sequence
4. Avoid edges marked on skill transitions known to conflict
5. Approach edges on synergistic skill pairs

#### Path 6: Fleet Ecosystem Growth
1. `ternary-reef::Reef` tracks long-term fleet structures
2. Successful note patterns become Coral structures that persist across sessions
3. `ternary-reef::BleachingEvent` simulates model failures to test fleet resilience
4. `ternary-reef::feed_cycle()` models energy flow from input data to output generation

#### Path 7: Parasite Detection
1. `ternary-symbiont::SymbiosisDetector` monitors agent pair performance
2. When Agent A consistently degrades Agent B's output → Parasitic relationship detected
3. Conductor can dynamically reassign resources to break parasitic pairs
4. `ternary-symbiont::SymbiosisEvolver` tunes beneficial pairs over time

### Conductor State Machine

```
   ┌──────────────────────────────────────────────────┐
   │  Captain::new(id, quorum)                         │
   │  → enlist agents with AgentInfo (id, status,     │
   │     specialization, fitness)                     │
   │  → receive_report(agent_id, ternary_value)        │
   │  → delegate(task_id, task_type) → assigned agent  │
   │  → decide_from_votes(&[Ternary]) → collective     │
   │     decision                                     │
   └──────────────────────────────────────────────────┘
           │
           ▼
   ┌──────────────────────────────────────────────────┐
   │  Per tick:                                        │
   │  1. Process pending commands (ternary-command)    │
   │  2. Check in-flight tasks (Delegator)             │
   │  3. Run negotiation for contested resources       │
   │     (ternary-negotiate / ternary-paxos)           │
   │  4. Update situation room (SituationRoom)         │
   │  5. Verify outputs (ternary-proof)                │
   │  6. Update trust network (ternary-trust)          │
   │  7. Log to history (CommandHistory)               │
   │  8. Archive decisions (ternary-archive)           │
   └──────────────────────────────────────────────────┘
```

---

## Repository Inventory (35 repos)

| # | Repo | Category | Key Pattern |
|---|------|----------|-------------|
| 1 | ternary-agent | Core | Agent identity, state, lifecycle |
| 2 | ternary-shipyard | Fleet | Fleet construction and maintenance |
| 3 | ternary-scheduler | Scheduling | Priority-based {-1,0,+1} task scheduling |
| 4 | ternary-scheduling-v2 | Scheduling | Enhanced scheduling with preemption |
| 5 | ternary-swarm | Coordination | Swarm/emergent behavior patterns |
| 6 | ternary-route | Routing | Decision routing with ternary weights |
| 7 | ternary-negotiate | Consensus | Multi-agent negotiation, stance space |
| 8 | ternary-voting | Consensus | Vote collection and tallying |
| 9 | ternary-quorum | Consensus | Quorum formation, configurable thresholds |
| 10 | ternary-paxos | Consensus | Full Paxos in ~400 lines, 3-vote |
| 11 | ternary-trust | Relationships | 5-stage trust: Hostile→Allied |
| 12 | ternary-proof | Verification | Kleene K3 logic, fuzzy matching |
| 13 | ternary-command | C&C | Parsing, dispatch, history, aliases |
| 14 | ternary-ensign | Agent Roles | Domain specialist registry/factory |
| 15 | ternary-captain | Leadership | Captain → Delegator → FleetReport |
| 16 | ternary-navigator | Spatial | A* with Avoid/Neutral/Approach edges |
| 17 | ternary-cargo | Logistics | Transport, manifests, smuggling |
| 18 | ternary-room | Spatial | Rooms, doors, coordinator, history |
| 19 | ternary-reef | Ecosystem | Coral/polyp/symbiont/bleaching model |
| 20 | ternary-tidepool | Sandbox | Isolated experimentation environments |
| 21 | ternary-steward | Resources | Budgeting, conservation, sustainability |
| 22 | ternary-symbiont | Relationships | Mutualism/commensalism/parasitism |
| 23 | ternary-channel | Comms | Priority messaging, reliable delivery |
| 24 | ternary-anchor | Spatial | Position stability, drift, anchorage |
| 25 | ternary-harbor | Spatial | Docking, berths, pilots, breakwaters |
| 26 | ternary-beacon | Discovery | Service advertisement/node discovery |
| 27 | ternary-cache | Persistence | Caching with invalidation policies |
| 28 | ternary-locks | Coordination | Distributed mutual exclusion |
| 29 | ternary-bus | Comms | Pub/sub message bus |
| 30 | ternary-mesh | Networking | Dynamic mesh, weighted connections |
| 31 | ternary-network | Networking | Abstract network primitives |
| 32 | ternary-distributed | Distributed | Primitives: leader election, counters |
| 33 | ternary-reassembly | Persistence | Five-layer state reconstruction |
| 34 | ternary-database | Persistence | Structured ternary state storage |
| 35 | ternary-archive | Persistence | Historical audit/storage |

---

## Recommendation

For fleet-midi MVP, prioritize integration in this order:

1. **ternary-captain** — conductor leadership structure
2. **ternary-paxos** — model selection consensus
3. **ternary-trust** — agent reputation routing
4. **ternary-proof** — output verification pipeline
5. **ternary-room** + **ternary-navigator** — spatial skill organization
6. **ternary-symbiont** — beneficial pair detection
7. **ternary-reef** — long-term fleet persistence
8. **ternary-command** — conductor CLI/API
9. **ternary-archive** — decision audit trail
10. **ternary-steward** — resource budget enforcement
