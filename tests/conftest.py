"""Pytest fixtures and configuration for MiroFish tests."""

import pytest
from datetime import datetime

# Add workspace to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mirofish.core.seeded_random import SeededRandom
from mirofish.agents.agent_profile import AgentProfile, BigFive, SchwartzValues
from mirofish.agents.cognitive_agent import CognitiveAgent, AgentState, AgentMode
from mirofish.core.memory_system import MemorySystem


@pytest.fixture
def seeded_rng():
    """Create a seeded random number generator for deterministic tests."""
    return SeededRandom(seed=42)


@pytest.fixture
def default_big_five():
    """Create default Big Five personality traits."""
    return BigFive(
        openness=0.5,
        conscientiousness=0.5,
        extraversion=0.5,
        agreeableness=0.5,
        neuroticism=0.5
    )


@pytest.fixture
def default_values():
    """Create default Schwartz values."""
    return SchwartzValues()


@pytest.fixture
def sample_profile(default_big_five, default_values):
    """Create a sample agent profile for testing."""
    return AgentProfile(
        agent_id="test_agent_001",
        name="Test Agent",
        age=30,
        occupation="Software Engineer",
        education="Bachelor's Degree",
        big_five=default_big_five,
        values=default_values,
        core_beliefs=["I am capable", "Hard work pays off"],
        goals=["Complete project successfully", "Learn new skills"],
        time_budget=8.0,
        money_budget=1000.0,
        energy_level=0.7,
        attention_capacity=0.8
    )


@pytest.fixture
def sample_agent(sample_profile, seeded_rng):
    """Create a sample cognitive agent for testing."""
    return CognitiveAgent(profile=sample_profile, rng=seeded_rng)


@pytest.fixture
def custom_state():
    """Create a custom agent state for testing."""
    return AgentState(
        self_worth=0.6,
        anxiety=0.3,
        confidence=0.7,
        consistency=0.5,
        momentum=0.6,
        energy=0.8,
        reputation=0.5,
        trust_in_others=0.6,
        social_connectedness=0.5,
        fragility_index=0.2,
        lock_in=0.1,
        cognitive_load=0.3,
        learning_rate=0.15,
        openness_to_change=0.5,
        mode=AgentMode.OPTIMIZE,
        cascade_active=False,
        success_streak=0,
        failure_streak=0,
        active_goal="Test goal",
        emotional_state="neutral"
    )


@pytest.fixture
def agent_with_custom_state(sample_profile, seeded_rng, custom_state):
    """Create an agent with custom initial state."""
    return CognitiveAgent(
        profile=sample_profile,
        rng=seeded_rng,
        initial_state=custom_state
    )


@pytest.fixture
def memory_system():
    """Create a fresh memory system for testing."""
    return MemorySystem()


@pytest.fixture
def simulation_time():
    """Provide a fixed simulation time for deterministic tests."""
    return datetime(2024, 1, 1, 12, 0, 0)
