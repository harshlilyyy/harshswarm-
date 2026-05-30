# =============================================================================
# MiroFish — Swarm-Intelligence Prediction Engine
# =============================================================================
"""
MiroFish Core Package

A production-grade, open-source swarm-intelligence prediction engine that:
1. Ingests arbitrary seed materials (news, policy, research, books, PDFs, etc.)
2. Transforms them into high-fidelity digital world models
3. Generates thousands of autonomous agents with rich psychological profiles
4. Enables emergent social behavior through natural language interaction
5. Runs time-based simulations with parallel execution and checkpointing
6. Predicts future states via Monte Carlo sampling
7. Produces comprehensive reports with citations
8. Allows post-simulation interaction and timeline comparison
9. Scales from 100 to 10,000+ agents on commodity hardware
10. Maintains scientific validity and reproducibility
"""

__version__ = "0.1.0"
__author__ = "MiroFish Team"

from .core.seeded_random import SeededRandom, RandomState
from .core.memory_system import MemoryType, MemoryEntry, MemorySystem
from .agents.agent_profile import AgentProfile, BigFive, SchwartzValues
from .agents.cognitive_agent import CognitiveAgent, AgentState, AgentMode
from .world.world_model import WorldModel, WorldEntity, WorldState, EntityType
from .simulation.scheduler import SimulationScheduler, SimulationEvent, EventType
from .simulation.engine import SimulationEngine, SimulationConfig, SimulationResult
from .prediction.monte_carlo import MonteCarloSampler, WorldSample, PredictionResult
from .reports.generator import ReportGenerator, ReportSection, ExecutiveSummary

__all__ = [
    # Core
    "SeededRandom",
    "RandomState",
    "MemoryType",
    "MemoryEntry", 
    "MemorySystem",
    # Agents
    "AgentProfile",
    "BigFive",
    "SchwartzValues",
    "CognitiveAgent",
    "AgentState",
    "AgentMode",
    # World
    "WorldModel",
    "WorldEntity",
    "WorldState",
    "EntityType",
    # Simulation
    "SimulationScheduler",
    "SimulationEvent",
    "EventType",
    "SimulationEngine",
    "SimulationConfig",
    "SimulationResult",
    # Prediction
    "MonteCarloSampler",
    "WorldSample",
    "PredictionResult",
    # Reports
    "ReportGenerator",
    "ReportSection",
    "ExecutiveSummary",
]
