# NYX PHOENIX MIGRATION — DISCOVERY REPORT
## Principal Staff Architect & Cognitive Systems Engineer Analysis

---

## EXECUTIVE SUMMARY

This report documents the archaeological audit of the legacy Streamlit-based NYX Decision Intelligence Simulator, preparing for its migration to an enterprise-grade, decoupled N-tier architecture.

---

## STEP A: DATA FLOW ANALYSIS

### Current Data Flow (Streamlit Monolith)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CURRENT STREAMLIT ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────────────────┘

User Input (Browser)
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  streamlit_app.py (Monolithic Script)                                    │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 1. UI Layer (st.text_input, st.button, st.tabs, etc.)              │  │
│  │    - Scenario configuration                                        │  │
│  │    - Agent presets selection                                       │  │
│  │    - Round count, seed settings                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│       │                                                                   │
│       ▼                                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 2. Session State Management (st.session_state)                     │  │
│  │    - scenario_history[]                                            │  │
│  │    - bookmarked_results[]                                          │  │
│  │    - question_thread[]                                             │  │
│  │    - comparison_scenarios[]                                        │  │
│  │    - agent_presets{}                                               │  │
│  │    - sim_result, debate_log, multi_trial_result                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│       │                                                                   │
│       ▼                                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 3. API Provider Selection (get_providers())                        │  │
│  │    - Reads from st.secrets                                         │  │
│  │    - Supports: Groq, SambaNova, Cerebras, Google, Mistral,         │  │
│  │      Cohere, OpenRouter, HuggingFace                               │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│       │                                                                   │
│       ▼                                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 4. Fallback Generator (generate_with_fallback)                     │  │
│  │    - Iterates through providers sequentially                       │  │
│  │    - Catches exceptions and retries next provider                  │  │
│  │    - Returns first successful response                             │  │
│  │    - NO circuit breaker, NO rate limit tracking                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│       │                                                                   │
│       ▼                                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 5. Core Kernel Invocation                                          │  │
│  │    - run_simulation() → CognitiveAgent.update() loop               │  │
│  │    - detect_black_swan() → Fragility analysis                      │  │
│  │    - run_counterfactual() → Alternative scenario testing           │  │
│  │    - run_multi_trial() → Statistical aggregation                   │  │
│  │    - game_theory_insights() → Nash equilibrium analysis            │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│       │                                                                   │
│       ▼                                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 6. Visualization Layer                                             │  │
│  │    - Plotly sparklines                                             │  │
│  │    - NetworkX graphs (optional)                                    │  │
│  │    - Pandas DataFrames                                             │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│       │                                                                   │
│       ▼                                                                   │
│  Rerender Entire Page (Streamlit limitation)                             │
└──────────────────────────────────────────────────────────────────────────┘
```

### Detailed Request-Response Chain

1. **User submits scenario** → `st.text_input` / `st.selectbox` captures input
2. **Session state updated** → `st.session_state.sim_result = None` (reset)
3. **API key lookup** → `get_providers()` scans `st.secrets` for available keys
4. **Fallback chain activation** → `generate_with_fallback(prompt, system, preferred_provider)`
   - Tries each provider in order
   - No intelligent rotation (dumb sequential retry)
   - No cooldown for failed providers
5. **Kernel execution** → `run_simulation(agent_names, rounds, seed)`
   - Creates `SeededRandom(seed)` for determinism
   - Instantiates `CognitiveAgent` objects
   - Runs deterministic update loop
6. **Result rendering** → Tabbed interface with metrics, sparklines, agent cards
7. **Full page rerender** → Every interaction triggers complete script re-execution

---

## STEP B: GOLDEN CORE IDENTIFICATION

### Modules/Functions That MUST Be Preserved

#### From `nyx_kernel.py` (The Deterministic Engine)

| Component | Type | Purpose | Preservation Priority |
|-----------|------|---------|----------------------|
| `SeededRandom` | Class | Deterministic PRNG wrapper | CRITICAL - Ensures reproducibility |
| `AgentState` | dataclass | State snapshot container | CRITICAL - Data structure |
| `CognitiveAgent` | Class | 10-variable psychological model | CRITICAL - Core simulation logic |
| `CognitiveAgent.update()` | Method | State transition equations | CRITICAL - The "physics engine" |
| `CognitiveAgent.get_current_state_dict()` | Method | Serialization helper | HIGH - API response format |
| `run_simulation()` | Function | Main simulation orchestrator | CRITICAL - Primary entry point |
| `detect_black_swan()` | Function | Fragility detection algorithm | HIGH - Advanced analytics |
| `run_counterfactual()` | Function | What-if scenario runner | MEDIUM - Premium feature |
| `run_multi_trial()` | Function | Monte-Carlo style aggregation | MEDIUM - Statistical power |
| `game_theory_insights()` | Function | Nash equilibrium analysis | MEDIUM - Advanced analytics |

#### From `streamlit_app.py` (UI & Integration Logic)

| Component | Type | Purpose | Preservation Priority |
|-----------|------|---------|----------------------|
| `get_providers()` | Function | API key discovery from secrets | HIGH - Must adapt to env vars |
| `generate_with_fallback()` | Function | Multi-provider LLM fallback | CRITICAL - Must enhance with circuit breaker |
| `DebateAgent` | Class | LLM-powered debate participant | MEDIUM - Optional feature |
| `run_standard_debate()` | Function | Multi-round debate orchestration | MEDIUM - Optional feature |
| `render_mode_badge()` | Function | UI helper for mode visualization | LOW - Replace with React components |
| `plot_sparkline()` | Function | Plotly chart generator | LOW - Replace with Recharts/D3 |

### Functions to WRAP (not rewrite)

```python
# These must be imported directly into FastAPI backend:
from nyx_kernel import (
    SeededRandom,
    CognitiveAgent,
    run_simulation,
    detect_black_swan,
    run_counterfactual,
    run_multi_trial,
    game_theory_insights
)

# Enhanced wrapper needed:
# generate_with_fallback → services/fallback.py (add circuit breaker)
```

---

## STEP C: BOTTLENECK DIAGNOSIS

### Critical Limitations in Current Architecture

#### 1. Streamlit Session State Anti-Patterns

**Problem:** `st.session_state` is ephemeral and tied to browser session
```python
# Current implementation (fragile):
if "sim_result" not in st.session_state:
    st.session_state.sim_result = None

# Issues:
# - Lost on page refresh
# - No persistence across devices
# - Race conditions in multi-user scenarios
# - Cannot scale horizontally
```

**Impact:** Zero durability, no audit trail, impossible to resume simulations

#### 2. Synchronous Blocking API Calls

**Problem:** `generate_with_fallback()` blocks entire thread
```python
# Current implementation (blocking):
for p in providers:
    try:
        resp = model.generate_content(full_prompt, request_options={"timeout": 10})
        return resp.text.strip(), p["name"]
    except Exception:
        time.sleep(0.5)  # Blocks everything!
        continue
```

**Impact:** 
- UI freezes during API calls
- No concurrent request handling
- Wasted compute resources
- Poor user experience under load

#### 3. No Rate Limit Intelligence

**Problem:** Dumb sequential retry without learning
```python
# Current: Always tries same order, even if provider just failed
providers = [p for p in providers if p["name"] == preferred] + [...]
for p in providers:
    # Blindly tries each, no memory of recent failures
```

**Impact:** 
- Repeated 429 errors
- Wasted API quota
- No adaptive throttling
- Cascading failures possible

#### 4. No Real-Time Streaming

**Problem:** All-or-nothing response delivery
```python
# Current: Wait for full simulation, then render
result = run_simulation(...)  # Blocks for seconds
st.write(result)  # Dump everything at once
```

**Impact:**
- Users stare at spinner
- No progress visibility
- Cannot cancel mid-simulation
- Poor perceived performance

#### 5. Monolithic Script Structure

**Problem:** Everything in one file (`streamlit_app.py` = 1435 lines)
```
Issues:
- No separation of concerns
- Impossible to unit test individual components
- Tight coupling between UI and business logic
- No API abstraction layer
```

#### 6. Database/Vector Scanning Gap

**Current State:** NO database integration exists
```python
# Missing entirely:
# - No SQL persistence
# - No vector embeddings
# - No RAG pipeline
# - No historical data storage
```

**Note:** User mentioned this as planned functionality ("Oracle"), but it's not implemented yet. This is a GREENFIELD opportunity.

---

## ARCHITECTURAL DEBT SUMMARY

| Issue | Severity | Technical Debt Score | Migration Effort |
|-------|----------|---------------------|------------------|
| Session state fragility | HIGH | 8/10 | Medium |
| Synchronous blocking | HIGH | 9/10 | Low (async wrap) |
| No circuit breaker | CRITICAL | 10/10 | Medium |
| No streaming | MEDIUM | 6/10 | High (WebSocket infra) |
| Monolithic structure | HIGH | 8/10 | High (refactor) |
| No persistence | MEDIUM | 7/10 | Medium (DB integration) |

---

## RECOMMENDED MIGRATION PRIORITY

1. **Phase 1:** Extract Golden Core → `backend/core/nyx_kernel.py` (direct copy)
2. **Phase 2:** Build FastAPI wrapper with async endpoints
3. **Phase 3:** Implement Circuit Breaker + Weighted Round-Robin
4. **Phase 4:** Add WebSocket streaming for real-time ticks
5. **Phase 5:** Build Next.js frontend with live dashboard
6. **Phase 6:** Add SQLite/Postgres persistence layer
7. **Phase 7:** Implement Vector DB RAG pipeline (greenfield)

---

*Report Generated by Principal Staff Architect & Cognitive Systems Engineer*
*Date: 2025-01-XX*
*Classification: INTERNAL - PHOENIX MIGRATION*
