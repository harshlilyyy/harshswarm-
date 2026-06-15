# Nyx · Decision Intelligence Simulator

<div align="center">

**A production-grade cognitive-social physics engine for modeling agent-based decision intelligence**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)

</div>

---

## 🌟 Overview

**Nyx** is a deterministic, seed-reproducible simulation engine that models agent-based decision intelligence using cognitive-social physics. It combines swarm intelligence with psychological modeling to simulate how autonomous agents make decisions, interact socially, and produce emergent collective behaviors.

The platform enables researchers and practitioners to:
- Simulate thousands of autonomous agents with rich psychological profiles
- Model complex social dynamics and cascading effects
- Run Monte Carlo predictions with full reproducibility
- Generate comprehensive reports with citations
- Compare counterfactual scenarios and timelines

## ✨ Key Features

### 🔬 Deterministic Simulation Engine
- **Full Reproducibility**: All randomness controlled via `SeededRandom` class — same seed produces identical outcomes
- **Cognitive Agents**: 10-dimensional psychological state machine including self-worth, anxiety, consistency, momentum, reputation, and more
- **Social Physics**: Agent interactions governed by empirically-grounded cognitive-social dynamics

### 🧠 Advanced Agent Modeling
Each agent maintains internal states across:
- **Self-Worth**: Core self-evaluation and confidence
- **Anxiety**: Stress response to uncertainty and peer comparison
- **Consistency**: Behavioral stability across situations
- **Momentum**: Accumulated forward progress energy
- **Reputation**: Social standing in the network
- **Opportunity Access**: Access to resources/connections
- **Fragility Index**: Susceptibility to cascading failures
- **Lock-in**: Resistance to behavioral change
- **Learning Rate**: Adaptation speed from experience
- **Energy**: Available cognitive/emotional resources

### 📊 Prediction & Analysis
- **Monte Carlo Sampling**: Run thousands of parallel simulations for probabilistic forecasting
- **Black Swan Detection**: Identify rare, high-impact events in simulation trajectories
- **Counterfactual Analysis**: Compare "what-if" scenarios side-by-side
- **Game Theory Insights**: Analyze strategic interactions and equilibria

### 🎨 Interactive Web Interface
Beautiful Streamlit-based UI featuring:
- Lavender Haze glassmorphism design
- Real-time simulation visualization
- Interactive parameter tuning
- Multi-trial statistical analysis
- Network graph visualization (optional)

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd workspace

# Install dependencies
pip install -r requirements.txt

# Install MiroFish package (optional)
pip install -e .
```

### Basic Usage

#### Running a Simulation

```python
from nyx_kernel import run_simulation, CognitiveAgent

# Configure simulation parameters
config = {
    "num_agents": 100,
    "num_rounds": 50,
    "seed": 42,
    "network_density": 0.1,
}

# Run deterministic simulation
results = run_simulation(config)

# Access agent states and metrics
print(f"Final round metrics: {results['metrics'][-1]}")
```

#### Monte Carlo Prediction

```python
from nyx_kernel import run_multi_trial, detect_black_swan

# Run multiple trials for statistical analysis
trials = run_multi_trial(
    num_trials=1000,
    num_agents=100,
    num_rounds=50,
    base_seed=42
)

# Detect black swan events
black_swans = detect_black_swan(trials, threshold=0.05)
print(f"Detected {len(black_swans)} rare events")
```

#### Counterfactual Analysis

```python
from nyx_kernel import run_counterfactual

# Compare baseline vs intervention scenario
baseline = run_simulation({"num_agents": 100, "seed": 42})
intervention = run_counterfactual(
    baseline,
    intervention_type="increase_opportunity",
    magnitude=0.3
)

# Analyze differences
print(f"Impact: {intervention['delta_metrics']}")
```

### Streamlit App

Launch the interactive web interface:

```bash
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501` with full simulation controls and visualization.

## 📦 Project Structure

```
workspace/
├── nyx_kernel.py          # Core deterministic simulation engine
├── streamlit_app.py       # Interactive web interface
├── setup.py               # Package installation script
├── requirements.txt       # Python dependencies
├── PERFORMANCE_OPTIMIZATIONS.md  # Performance documentation
└── mirofish/              # MiroFish swarm intelligence package
    ├── __init__.py        # Package exports
    ├── core/              # Core utilities (memory, random state)
    ├── agents/            # Agent profiles and cognitive models
    ├── world/             # World model and entity management
    ├── simulation/        # Simulation engine and scheduler
    ├── prediction/        # Monte Carlo sampling and forecasting
    ├── reports/           # Report generation system
    ├── ingestion/         # Seed material processing
    ├── api/               # API endpoints
    └── layer1/            # Base layer implementations
```

## 🔧 Configuration

### Simulation Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `num_agents` | int | 100 | Number of agents in simulation |
| `num_rounds` | int | 50 | Number of simulation rounds |
| `seed` | int | 42 | Random seed for reproducibility |
| `network_density` | float | 0.1 | Probability of connection between agents |
| `initial_energy` | float | 0.7 | Starting energy level for agents |
| `learning_rate` | float | 0.1 | Base learning rate for adaptation |

### Optional Dependencies

Enhanced functionality with optional packages:

```bash
# Graph visualization
pip install networkx matplotlib

# Interactive plots
pip install plotly

# AI integration
pip install openai google-generativeai
```

## 🧪 Testing

```bash
# Run tests (if pytest is installed)
pytest tests/

# Verify imports
python -c "from nyx_kernel import run_simulation; print('✓ Kernel loaded')"
python -c "import mirofish; print('✓ MiroFish package loaded')"
```

## 📈 Performance

See [PERFORMANCE_OPTIMIZATIONS.md](./PERFORMANCE_OPTIMIZATIONS.md) for detailed documentation on:
- Memory system optimizations (40-60% improvement)
- Simulation engine enhancements (15-25% improvement)
- Algorithm selection strategies
- Recommendations for large-scale deployments (1000+ agents)

Key optimizations include:
- Heap-based memory retrieval vs sorting
- Pre-allocated lists for metrics collection
- Multiplication over division for strength calculations
- Lazy loading and variable caching

## 🎯 Use Cases

### Research Applications
- **Social Dynamics**: Study emergence of norms, conventions, and cultural patterns
- **Behavioral Economics**: Model decision-making under uncertainty and social influence
- **Network Science**: Analyze cascade propagation and tipping points

### Business Applications
- **Market Simulation**: Predict consumer behavior and adoption curves
- **Organizational Design**: Optimize team structures and communication patterns
- **Risk Assessment**: Identify fragility and resilience in complex systems

### Policy Analysis
- **Intervention Testing**: Evaluate policy impacts before real-world deployment
- **Equity Analysis**: Model opportunity access and distributional effects
- **Crisis Response**: Simulate emergency scenarios and coordination strategies

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Code formatting
black .

# Type checking
mypy mirofish/
```

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **MiroFish Team** — Initial work and core development

## 🙏 Acknowledgments

- Cognitive psychology research on decision-making and social influence
- Complexity science and agent-based modeling community
- Open-source contributors and maintainers

## 📚 Citation

If you use Nyx in your research, please cite:

```bibtex
@software{nyx2024,
  author = {MiroFish Team},
  title = {Nyx: Decision Intelligence Simulator},
  year = {2024},
  url = {https://github.com/mirofish/nyx}
}
```

## 🌐 Contact

For questions, collaborations, or support:
- Open an issue on GitHub
- Join our community discussions

---

<div align="center">

**Built with 💜 for advancing decision intelligence research**

[Back to top](#-overview)

</div>
