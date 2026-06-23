# MiroFish Improvement Plan

This document outlines comprehensive improvements to be implemented across the MiroFish/Nyx codebase.

## Priority 1: Critical Issues (Implement First)

### 1.1 Add Comprehensive Test Suite
**Status**: No tests exist in the codebase

**Actions**:
- Create `tests/` directory structure
- Add unit tests for all core modules
- Add integration tests for simulation engine
- Add determinism verification tests
- Target: 80%+ code coverage

**Files to create**:
- `tests/__init__.py`
- `tests/test_cognitive_agent.py`
- `tests/test_memory_system.py`
- `tests/test_simulation_engine.py`
- `tests/test_seeded_random.py`
- `tests/test_world_model.py`
- `tests/conftest.py` (pytest fixtures)

### 1.2 Consolidate Duplicate Code
**Issue**: `nyx_kernel.py` (1572 lines) appears to duplicate functionality in `mirofish/` package

**Actions**:
- Audit `nyx_kernel.py` for unique functionality
- Migrate unique features to `mirofish/` package
- Deprecate or remove `nyx_kernel.py`
- Update imports in `streamlit_app.py`

### 1.3 Add Missing Type Hints
**Issue**: Several methods lack return type annotations

**Actions**:
- Add return type to `CognitiveAgent.update()` method
- Add complete type hints to all public APIs
- Run mypy for validation
- Add `py.typed` marker file

**Files to update**:
- All files in `mirofish/agents/`
- All files in `mirofish/simulation/`
- All files in `mirofish/core/`

### 1.4 Pin Dependency Versions
**Issue**: `requirements.txt` uses loose version constraints

**Current**:
```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
```

**Recommended**:
```
streamlit==1.31.0
pandas==2.1.4
numpy==1.26.3
plotly==5.18.0
networkx==3.2.1
matplotlib==3.8.2
openai==1.10.0
google-generativeai==0.3.2
```

**Actions**:
- Update `/workspace/requirements.txt` with exact versions
- Add `requirements-dev.txt` for development dependencies
- Update `setup.py` install_requires

---

## Priority 2: Performance Optimizations

### 2.1 NumPy Vectorization
**Issue**: Agent updates use Python loops instead of vectorized operations

**Current Pattern**:
```python
for agent in agents:
    agent.update(progress, peer_gap, ...)
```

**Optimized Pattern**:
```python
import numpy as np

# Vectorize state arrays
states = np.array([agent.state_vector() for agent in agents])
# Apply bulk updates
updated_states = self._vectorized_update(states, events)
# Distribute back
for i, agent in enumerate(agents):
    agent.apply_state_vector(updated_states[i])
```

**Expected Impact**: 10-100x speedup for large agent populations

**Files to update**:
- `mirofish/simulation/engine.py`
- `mirofish/agents/cognitive_agent.py` (add vectorization helpers)
- Create `mirofish/core/vectorized_ops.py`

### 2.2 Memory System Optimization
**Issue**: Memory encoding/retrieval may become bottleneck with large simulations

**Actions**:
- Add LRU caching for frequent retrievals
- Implement batch encoding
- Add memory compaction for old entries
- Profile memory operations under load

### 2.3 Parallel Execution Improvements
**Current**: Uses ThreadPoolExecutor (limited by GIL)

**Recommended**: Use ProcessPoolExecutor for CPU-bound agent updates

**Files to update**:
- `mirofish/simulation/engine.py`

---

## Priority 3: Code Quality & Maintainability

### 3.1 Extract Magic Numbers to Constants
**Issue**: Hardcoded values throughout codebase

**Examples from `cognitive_agent.py`**:
```python
# Line 272-278
s.self_worth = self.clamp(
    s.self_worth 
    + 0.25 * progress      # MAGIC NUMBER
    - 0.3 * max(peer_gap, 0)  # MAGIC NUMBER
    + 0.15 * social_feedback  # MAGIC NUMBER
    - 0.2 * f_fail       # MAGIC NUMBER
)
```

**Solution**: Create configuration module
```python
# mirofish/core/config.py
@dataclass
class AgentUpdateCoefficients:
    SELF_WORTH_PROGRESS_COEF: float = 0.25
    SELF_WORTH_PEER_GAP_COEF: float = 0.3
    SELF_WORTH_SOCIAL_COEF: float = 0.15
    SELF_WORTH_FAILURE_COEF: float = 0.2
    # ... etc
```

### 3.2 Improve Error Handling
**Actions**:
- Add custom exception classes
- Implement graceful degradation
- Add input validation
- Improve error messages

**Files to create**:
- `mirofish/core/exceptions.py`

### 3.3 Add Logging Throughout
**Current**: Minimal logging

**Actions**:
- Add structured logging at DEBUG, INFO, WARNING levels
- Log state transitions
- Log performance metrics
- Configure log rotation

---

## Priority 4: Documentation

### 4.1 API Documentation
**Actions**:
- Add Google-style docstrings to all public APIs
- Generate Sphinx documentation
- Add examples to docstrings
- Create API reference guide

**Files to create**:
- `docs/conf.py`
- `docs/index.rst`
- `docs/api/` directory

### 4.2 Mathematical Formulations
**Actions**:
- Document all update equations with mathematical notation
- Add references to psychology/behavioral economics literature
- Explain parameter choices

**File to create**:
- `docs/mathematical_model.md`

### 4.3 Architecture Decision Records (ADRs)
**Actions**:
- Document key architectural decisions
- Explain trade-offs considered
- Record context and consequences

**Directory to create**:
- `docs/adr/`
  - `001-use-seeded-random-for-determinism.md`
  - `002-agent-psychological-model.md`
  - `003-memory-system-design.md`

---

## Priority 5: Streamlit App Improvements

### 5.1 State Management
**Issue**: Streamlit app may have complex state management

**Actions**:
- Use `st.session_state` more systematically
- Separate UI state from simulation state
- Add state persistence option

### 5.2 Security
**Issue**: API keys may be exposed

**Actions**:
- Load API keys from environment variables only
- Never store keys in session state
- Add warning if keys are missing

### 5.3 Performance
**Actions**:
- Add `@st.cache_data` and `@st.cache_resource` decorators
- Implement incremental updates
- Add loading indicators
- Optimize Plotly chart rendering

---

## Priority 6: Advanced Features

### 6.1 Monte Carlo Enhancements
**Actions**:
- Add convergence diagnostics (Gelman-Rubin statistic)
- Implement sensitivity analysis (Sobol indices)
- Add confidence interval calculations
- Support for advanced sampling (Latin Hypercube, Quasi-Monte Carlo)

**Files to update**:
- `mirofish/prediction/monte_carlo.py`

### 6.2 Visualization Improvements
**Actions**:
- Add interactive Plotly charts
- Implement real-time simulation visualization
- Add network graph visualization
- Create dashboard templates

### 6.3 Configuration Management
**Actions**:
- Centralize all configuration
- Support YAML/JSON config files
- Add configuration validation
- Implement configuration profiles

**Files to create**:
- `mirofish/core/config_manager.py`

---

## Priority 7: Scalability

### 7.1 Database Backend
**Current**: In-memory storage only

**Actions**:
- Add SQLite support for small deployments
- Add PostgreSQL support for production
- Implement ORM layer (SQLAlchemy)
- Add migration scripts

### 7.2 Distributed Simulation
**Actions**:
- Add support for running simulations across multiple machines
- Implement message queue for agent communication
- Add distributed state management

---

## Implementation Roadmap

### Phase 1 (Week 1-2): Foundation
- [ ] Set up test infrastructure
- [ ] Write critical path tests
- [ ] Fix type hints
- [ ] Pin dependencies

### Phase 2 (Week 3-4): Performance
- [ ] Profile current performance
- [ ] Implement NumPy vectorization
- [ ] Optimize memory system
- [ ] Benchmark improvements

### Phase 3 (Week 5-6): Quality
- [ ] Extract constants
- [ ] Improve error handling
- [ ] Add comprehensive logging
- [ ] Code review and refactoring

### Phase 4 (Week 7-8): Documentation
- [ ] Write API docs
- [ ] Document mathematical model
- [ ] Create ADRs
- [ ] Write user guide

### Phase 5 (Ongoing): Features
- [ ] Enhance Monte Carlo
- [ ] Improve visualizations
- [ ] Add configuration management
- [ ] Explore scalability options

---

## Testing Strategy

### Unit Tests
Test individual functions and methods in isolation.

### Integration Tests
Test interactions between components.

### Property-Based Tests
Use Hypothesis library to generate test cases automatically.

### Determinism Tests
Verify that same seed produces identical results.

### Performance Tests
Benchmark critical paths and detect regressions.

---

## Success Metrics

1. **Code Coverage**: >80% line coverage, >70% branch coverage
2. **Performance**: 10x improvement in agent update throughput
3. **Type Safety**: Zero mypy errors
4. **Documentation**: 100% public API documented
5. **Reliability**: Zero unhandled exceptions in production
6. **Maintainability**: Cyclomatic complexity <10 for all functions

---

## Risk Mitigation

1. **Breaking Changes**: Use deprecation warnings, maintain backward compatibility
2. **Performance Regressions**: Add performance tests to CI
3. **Loss of Determinism**: Extensive testing of seeded random behavior
4. **Documentation Drift**: Integrate doc generation into CI/CD

---

## Tools & Technologies

- **Testing**: pytest, hypothesis, pytest-cov
- **Type Checking**: mypy, pyright
- **Linting**: black, isort, flake8, pylint
- **Documentation**: Sphinx, mkdocs
- **Profiling**: cProfile, py-spy, memory_profiler
- **CI/CD**: GitHub Actions

---

*Last updated: 2024*
*Version: 1.0*
