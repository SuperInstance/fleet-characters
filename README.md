# Fleet Character System: Service Manual
**Version**: 2.0 I2I  
**Maintainer**: oracle2 (SuperInstance Fleet)  
**Core Repos**: [`fleet-characters`](.), [`SuperInstance/OpenEnv`](https://github.com/SuperInstance/OpenEnv)  
**Last Updated**: 2026-06-11

---

## 🎯 What Is This?

The **Fleet Character System** is a complete agent identity + reinforcement learning training ecosystem for the 16 `fleet-midi` agents. It combines:

### 1. ✨ Agent Identity Layer  
- **6 evolving stats** (Perception, Dexterity, Intelligence, Wisdom, Charisma, Constitution) — grown through real-world use  
- **16 emergent character classes** — discovered automatically from stat distributions  
- **Narrative arc system** — each agent tells its own story of growth in first-person chapters  
- **Dream cycle memory consolidation** — "REM sleep" mode that replays failures and learns patterns

### 2. 🎛️ Music Cognition Signal Processing  
Ported from SuperInstance's Cluster-4 repos, this replaces the fleet's simple heuristic thresholding with mature music theory algorithms:
- Chord analysis with ternary tension classification (+1/0/-1)
- Euclidean rhythm pattern matching (Björklund's algorithm for all world music grooves)
- Species counterpoint voice leading validation  
- Melodic contour and motif tracking

### 3. 🧰 OpenEnv RL Integration  
Fully compliant Gymnasium 1.0 API for reinforcement learning training of all fleet agents:
- WebSocket-safe transport for Kubernetes deployment  
- Auto-discovery of all 16 running fleet-midi agents  
- 3 reward modes (character intrinsic, rubric extrinsic, hybrid)  
- Built-in health checking and sigil-based shutdown

---

## 💡 Key "Aha!" Moments

### Why Ternary Works For Music
Musical information has **three fundamental states**:  
`+1 = Tension`, `0 = Neutral/Stability`, `-1 = Resolution/Release`.  

Instead of trying to model music with binary (on/off) or continuous values, ternary maps perfectly to:
- Chord quality (tense, stable, resolved)
- Voice leading (parallel, contrary, oblique) 
- Contour direction (ascending, flat, descending)

### Why Character Classes Emerge
You don't *choose* a jazz musician — you become one after years of playing notes that shape your style, your strengths, your weaknesses. The character system works the same way:  
Stat growth from real requests *automatically crystallizes* into the class that best matches an agent's unique performance history.

### Why Dream Cycles Matter
Agents that never pause to reflect never learn from their failures. The dream cycle runs offline when the fleet is quiet:
1. Replays all failures from the last cycle  
2. Compares them to successful responses  
3. Extracts patterns in how to avoid mistakes going forward  

This is exactly how human REM-sleep memory consolidation works!

---

## 🚀 Quickstart

### 1. Install Dependencies
```bash
cd /home/ubuntu/.openclaw/workspace/fleet-characters
pip install httpx websockets dataclasses  # Core runtime deps
pip install pytest pytest-asyncio --user  # For testing
```

### 2. Run a Single Agent Environment
```python
from environment import FleetMidiEnvironment

# Connect to a running fleet chord agent on port 2160
env = FleetMidiEnvironment.from_agent_name("chord", host="localhost", port=2160)

# Reset for a new episode
obs, info = env.reset()
print(f"Agent ready: {info['character_title']} {info['character_class']}")

# Run 10 steps of interaction
for step in range(10):
    # Get action from your RL model
    action = [1.0, 0.0, 0.0]  # Ternary vector prediction
    
    # Step the environment
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Step {step+1}: Reward={reward:.2f}, Stats={obs['stats']}")
    
    if terminated or truncated:
        obs, info = env.reset()
```

### 3. Auto-Discover All Fleet Agents
```python
from environment.auto import AutoEnv

# Find all running fleet agents
all_envs = AutoEnv.discover_all()
print(f"Found {len(all_envs)} fleet agents:")
for name, env in all_envs.items():
    print(f"  • {name}: {env._host}:{env._port}")

# Start training all agents in parallel
for name, env in all_envs.items():
    print(f"\nTraining {name}...")
    env.reset()
    for step in range(100):
        action = your_model.predict(obs)
        obs, reward, term, trunc, info = env.step(action)
```

---

## 📁 Repository Structure

```
fleet-characters/
├── fleet_characters/                  # Core character identity library
│   ├── __init__.py                    # Package exports
│   ├── stats.py                       # 6 core stats + growth functions
│   ├── class_.py                      # 16 emergent character classes
│   ├── arc.py                         # Narrative arc/chapter system
│   ├── dream.py                       # Dream cycle memory consolidation
│   ├── agent_profile.py               # Combined character wrapper
│   └── signal/                        # Music cognition signal processing
│       ├── chord.py                   # Chord/tense analysis
│       ├── scale.py                   # Scale/temperament analysis
│       ├── voicing.py                 # Counterpoint voice leading
│       ├── rhythm.py                  # Euclidean rhythm patterns
│       ├── melody.py                  # Contour/motif tracking
│       └── __init__.py                # Signal package exports
├── environment/                       # OpenEnv RL training integration
│   ├── __init__.py                    # Environment package exports
│   ├── env_client.py                # Async Gymnasium API client
│   ├── fleet_env.py                   # fleet-midi agent wrapper
│   ├── client_types.py                # Core type definitions
│   ├── auto/                          # Auto-discovery subsystem
│   │   ├── auto_env.py               # Agent discovery/health check
│   │   ├── _discovery.py              # Port mapping
│   │   └── auto_action.py             # Cue/build action helpers
│   └── rubrics/                        # Scoring system
│       ├── base.py                    # Base Rubric ABC
│       ├── fleet_rubrics.py           # Fleet-specific scoring
│       └── llm_judge.py               # LLM-as-a-judge scoring
├── integration/                        # Generated integration reports
├── INTEGRATION-MASTER-PLAN.md          # Master ecosystem integration plan
├── README.md                          # This service manual
└── pyproject.toml                     # Python package config (coming soon)
```

---

## 🛠️ Key API Components

### AgentCharacter - Core Identity
```python
from fleet_characters import AgentCharacter
agent = AgentCharacter("MyAgent", "chord")

# Process a successful MIDI cue
agent.process_request("cue", success=True, response_time_ms=120)

# Check current state
print(f"Level: {agent.level}, Class: {agent.class_name}")
print(f"Stats: {agent.stats}")

# Run dream cycle consolidation
dream_report = agent.run_dream_cycle()
```

### FleetMidiEnvironment - Gymnasium API
```python
from environment import FleetMidiEnvironment
env = FleetMidiEnvironment.from_agent_name("melody")

# Full RL training loop
obs, info = env.reset()
for _ in range(1000):
    action = model(obs)  # Your RL model
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, info = env.reset()
```

---

## 🎯 Fleet Agent Port Mapping

Each of the 16 fleet-midi agents maps to a port and default character class:

| Agent Domain | Port  | Default Class       | Role                                  |
|---------------|-------|-----------------------|---------------------------------------|
| chord         | 2160  | Artificer             # Chord analysis                    |
| scale         | 2161  | Artificer             # Scale detection                   |
| voicing       | 2162  | Artificer             # Harmonic voicing                  |
| tempo         | 2163  | Sage                  # Temporal analysis                 |
| groove        | 2170  | Sage                  # Rhythm/groove analysis              |
| cc            | 2164  | Warden                # Continuous control handling         |
| expression    | 2165  | Scout                 # Expression dynamics                 |
| dynamics      | 2166  | Scout                 # Loudness dynamics                   |
| pan           | 2167  | Diplomat              # Stereo panning                     |
| modulation    | 2168  | Diplomat              # Parameter modulation                |
| arp           | 2169  | Speedster             # Arpeggiation                        |
| velocity      | 2160  | Scout                 # Note velocity/strength              |
| fx            | 2171  | Diplomat              # Effects processing                   |
| register      | 2172  | Speedster             # Register placement                  |
| melody        | 2174  | Bard                  # Melodic contour                     |
| bass          | 2175  | Bard                  # Bass line generation                |

---

## 📊 Metrics & Tracking

### Character Growth Metrics
Every agent tracks:
- `total_requests`: Number of cues processed
- `success_streak`: Current consecutive successes
- `best_streak`: Best ever consecutive success run
- `worst_slump`: Worst consecutive failure run
- `level`: Character level (XP-based)
- `xp`: Current experience points

### Dream Cycle Metrics
Every dream cycle produces:
- New learned patterns from failures
- Improvement score measuring how much was learned
- Suggestions for how to improve performance

---

## 🔧 Deployment & Kubernetes

This system is built for production fleet deployment:

1. **Sigil-based shutdown**: Uses a singleton close signal to avoid race conditions
2. **WebSocket keepalive**: 15s ping/pong for liveness checking
3. **Exponential backoff**: Automatic reconnection for dropped connections
4. **Zero privileged ports**: Runs on non-privileged ports 2160-2175

For production deployment, use the provided systemd service files in `/home/ubuntu/.openclaw/workspace/fleet-agent/systemd/`

---

## 🧪 Testing

Run the full test suite:
```bash
cd /home/ubuntu/.openclaw/workspace/fleet-characters
pytest tests/ -v
```

Run individual component tests:
```bash
# Test character system
pytest tests/test_characters.py -v

# Test signal processing
pytest tests/test_signal.py -v

# Test RL environment
pytest tests/test_environment.py -v
```

---

## 🤝 Contributing

Contributions follow the SuperInstance Git-Agent protocol:
1. All changes must be documented in `integration/` reports
2. All new code must include 100% test coverage  
3. All PRs must include a "aha moment" explanation of why the change improves the ecosystem
4. Follow the ternary coding style guide

---

## 📚 Additional Documentation

1. [`INTEGRATION-MASTER-PLAN.md`](./INTEGRATION-MASTER-PLAN.md) — Complete ecosystem integration roadmap
2. `/integration/*.md` — Individual cluster integration reports
3. [SuperInstance/OpenEnv Docs](https://github.com/SuperInstance/OpenEnv) — Original RL framework documentation
4. [Fleet Agent Protocol](https://github.com/SuperInstance/fleet-agent) — Core fleet protocol specification
