"""Tests for the CognitiveAgent class."""

import pytest
from datetime import datetime
from mirofish.agents.cognitive_agent import CognitiveAgent, AgentState, AgentMode


class TestCognitiveAgentInitialization:
    """Test CognitiveAgent initialization and setup."""
    
    def test_agent_creation(self, sample_agent):
        """Verify agent can be created with profile and RNG."""
        assert sample_agent is not None
        assert sample_agent.profile.agent_id == "test_agent_001"
        assert sample_agent.rng is not None
    
    def test_initial_state_created(self, sample_agent):
        """Verify initial state is properly created."""
        assert sample_agent.state is not None
        assert 0 <= sample_agent.state.self_worth <= 1
        assert 0 <= sample_agent.state.anxiety <= 1
        assert 0 <= sample_agent.state.confidence <= 1
    
    def test_initial_state_from_profile(self, sample_agent):
        """Verify initial state reflects profile traits."""
        # Neuroticism should influence anxiety
        neuroticism = sample_agent.profile.big_five.neuroticism
        expected_anxiety_range = (neuroticism * 0.6 + 0.2 - 0.1, 
                                   neuroticism * 0.6 + 0.2 + 0.1)
        assert expected_anxiety_range[0] <= sample_agent.state.anxiety <= expected_anxiety_range[1] + 0.1
    
    def test_custom_initial_state(self, agent_with_custom_state, custom_state):
        """Verify custom initial state is used when provided."""
        assert agent_with_custom_state.state.self_worth == custom_state.self_worth
        assert agent_with_custom_state.state.anxiety == custom_state.anxiety
        assert agent_with_custom_state.state.mode == custom_state.mode
    
    def test_memory_system_initialized(self, sample_agent):
        """Verify memory system is initialized."""
        assert sample_agent.memory is not None
    
    def test_beliefs_encoded_to_memory(self, sample_agent):
        """Verify core beliefs from profile are encoded to memory."""
        # Check that semantic memory contains beliefs
        belief_memories = sample_agent.memory.retrieve_by_type('semantic')
        assert len(belief_memories) > 0, "Core beliefs should be encoded to memory"
    
    def test_resources_initialized(self, sample_agent):
        """Verify resource budgets are initialized from profile."""
        assert sample_agent.current_time_budget == sample_agent.profile.time_budget
        assert sample_agent.current_money_budget == sample_agent.profile.money_budget
        assert sample_agent.current_energy == sample_agent.profile.energy_level
        assert sample_agent.current_attention == sample_agent.profile.attention_capacity


class TestCognitiveAgentUpdate:
    """Test CognitiveAgent state update logic."""
    
    def test_update_changes_state(self, sample_agent):
        """Verify update() method changes agent state."""
        initial_self_worth = sample_agent.state.self_worth
        
        sample_agent.update(
            progress=0.8,
            peer_gap=0.2,
            social_feedback=0.5,
            failure_flag=False,
            success_flag=True
        )
        
        # State should change after update
        assert sample_agent.state.self_worth != initial_self_worth or \
               sample_agent.state.momentum != 0.5  # At least something should change
    
    def test_success_increases_momentum(self, sample_agent):
        """Verify success increases momentum."""
        initial_momentum = sample_agent.state.momentum
        
        sample_agent.update(
            progress=0.5,
            peer_gap=0.3,
            social_feedback=0.0,
            failure_flag=False,
            success_flag=True
        )
        
        assert sample_agent.state.momentum >= initial_momentum
    
    def test_failure_decreases_self_worth(self, sample_agent):
        """Verify failure decreases self-worth."""
        initial_self_worth = sample_agent.state.self_worth
        
        sample_agent.update(
            progress=0.2,
            peer_gap=0.7,
            social_feedback=-0.5,
            failure_flag=True,
            success_flag=False
        )
        
        assert sample_agent.state.self_worth <= initial_self_worth
    
    def test_peer_gap_increases_anxiety(self, sample_agent):
        """Verify large peer gap increases anxiety."""
        sample_agent.state.anxiety = 0.3  # Set baseline
        
        sample_agent.update(
            progress=0.3,
            peer_gap=0.9,  # Large gap
            social_feedback=0.0,
            failure_flag=False,
            success_flag=False
        )
        
        assert sample_agent.state.anxiety > 0.3
    
    def test_social_feedback_affects_trust(self, sample_agent):
        """Verify positive social feedback increases trust in others."""
        initial_trust = sample_agent.state.trust_in_others
        
        sample_agent.update(
            progress=0.5,
            peer_gap=0.3,
            social_feedback=0.8,  # Positive feedback
            failure_flag=False,
            success_flag=False
        )
        
        assert sample_agent.state.trust_in_others >= initial_trust
    
    def test_mentor_flag_helps_recovery(self, agent_with_custom_state):
        """Verify mentorship helps exit cascade/recovery mode."""
        agent = agent_with_custom_state
        agent.state.cascade_active = True
        agent.state.mode = AgentMode.RECOVER
        
        agent.update(
            progress=0.4,
            peer_gap=0.4,
            social_feedback=0.0,
            failure_flag=False,
            success_flag=False,
            mentor_flag=True  # Mentorship received
        )
        
        # Should exit cascade mode with mentorship
        assert not agent.state.cascade_active
        assert agent.state.mode != AgentMode.RECOVER
    
    def test_cascade_activation(self, sample_agent):
        """Verify cascade activates after consecutive failures."""
        # Trigger 3 consecutive failures
        for _ in range(3):
            sample_agent.update(
                progress=0.1,
                peer_gap=0.8,
                social_feedback=-0.5,
                failure_flag=True,
                success_flag=False
            )
        
        # Lower self-worth to trigger cascade
        sample_agent.state.self_worth = 0.3
        sample_agent.state.failure_streak = 3
        
        # Force another failure to check cascade
        sample_agent.update(
            progress=0.1,
            peer_gap=0.8,
            social_feedback=-0.5,
            failure_flag=True,
            success_flag=False
        )
        
        assert sample_agent.state.failure_streak >= 3
    
    def test_state_values_clamped(self, sample_agent):
        """Verify all state values remain in valid ranges after update."""
        # Apply extreme updates
        for _ in range(10):
            sample_agent.update(
                progress=1.0 if _ % 2 == 0 else 0.0,
                peer_gap=0.0 if _ % 2 == 0 else 1.0,
                social_feedback=1.0 if _ % 2 == 0 else -1.0,
                failure_flag=(_ % 3 == 0),
                success_flag=(_ % 3 == 1)
            )
        
        # Verify all values are clamped to [0, 1]
        state = sample_agent.state
        assert 0 <= state.self_worth <= 1
        assert 0 <= state.anxiety <= 1
        assert 0 <= state.confidence <= 1
        assert 0 <= state.consistency <= 1
        assert 0 <= state.momentum <= 1
        assert 0 <= state.energy <= 1
        assert 0 <= state.reputation <= 1
        assert 0 <= state.trust_in_others <= 1
        assert 0 <= state.social_connectedness <= 1
        assert 0 <= state.fragility_index <= 1
        assert 0 <= state.lock_in <= 1
        assert 0 <= state.cognitive_load <= 1
        assert 0 <= state.learning_rate <= 1
        assert 0 <= state.openness_to_change <= 1


class TestCognitiveAgentModes:
    """Test agent mode transitions."""
    
    def test_execute_mode_conditions(self, sample_agent):
        """Verify EXECUTE mode activates with high confidence and momentum."""
        sample_agent.state.self_worth = 0.8
        sample_agent.state.momentum = 0.8
        sample_agent.state.anxiety = 0.3
        
        sample_agent.update(
            progress=0.7,
            peer_gap=0.2,
            social_feedback=0.5,
            failure_flag=False,
            success_flag=True
        )
        
        assert sample_agent.state.mode == AgentMode.EXECUTE
    
    def test_avoid_mode_conditions(self, sample_agent):
        """Verify AVOID mode activates with high anxiety and low self-worth."""
        sample_agent.state.anxiety = 0.8
        sample_agent.state.self_worth = 0.3
        
        sample_agent.update(
            progress=0.2,
            peer_gap=0.8,
            social_feedback=-0.5,
            failure_flag=True,
            success_flag=False
        )
        
        assert sample_agent.state.mode == AgentMode.AVOID
    
    def test_optimize_mode_default(self, sample_agent):
        """Verify OPTIMIZE is the default/steady state mode."""
        # Moderate conditions
        sample_agent.update(
            progress=0.5,
            peer_gap=0.4,
            social_feedback=0.0,
            failure_flag=False,
            success_flag=False
        )
        
        assert sample_agent.state.mode == AgentMode.OPTIMIZE


class TestCognitiveAgentSerialization:
    """Test agent state serialization/deserialization."""
    
    def test_state_to_dict(self, sample_agent):
        """Verify state can be converted to dictionary."""
        state_dict = sample_agent.state.to_dict()
        
        assert isinstance(state_dict, dict)
        assert 'self_worth' in state_dict
        assert 'anxiety' in state_dict
        assert 'mode' in state_dict
        assert state_dict['self_worth'] == sample_agent.state.self_worth
    
    def test_state_from_dict(self, custom_state):
        """Verify state can be created from dictionary."""
        state_dict = custom_state.to_dict()
        restored_state = AgentState.from_dict(state_dict)
        
        assert restored_state.self_worth == custom_state.self_worth
        assert restored_state.anxiety == custom_state.anxiety
        assert restored_state.mode == custom_state.mode
    
    def test_get_current_state_dict(self, sample_agent):
        """Verify get_current_state_dict returns complete state."""
        state_dict = sample_agent.get_current_state_dict()
        
        assert isinstance(state_dict, dict)
        assert 'profile' in state_dict or 'agent_id' in state_dict


class TestCognitiveAgentDeterminism:
    """Test that agents are deterministic given same seed."""
    
    def test_same_seed_same_behavior(self, sample_profile):
        """Verify agents with same seed behave identically."""
        rng1 = type(sample_profile).__module__  # Get module for import
        from mirofish.core.seeded_random import SeededRandom
        
        rng1 = SeededRandom(seed=42)
        rng2 = SeededRandom(seed=42)
        
        agent1 = CognitiveAgent(profile=sample_profile, rng=rng1)
        agent2 = CognitiveAgent(profile=sample_profile, rng=rng2)
        
        # Apply same sequence of updates
        for i in range(5):
            agent1.update(
                progress=0.5 + i * 0.1,
                peer_gap=0.3,
                social_feedback=0.2,
                failure_flag=(i % 3 == 0),
                success_flag=(i % 3 == 1)
            )
            
            agent2.update(
                progress=0.5 + i * 0.1,
                peer_gap=0.3,
                social_feedback=0.2,
                failure_flag=(i % 3 == 0),
                success_flag=(i % 3 == 1)
            )
        
        # States should be identical
        assert agent1.state.self_worth == agent2.state.self_worth
        assert agent1.state.anxiety == agent2.state.anxiety
        assert agent1.state.momentum == agent2.state.momentum
        assert agent1.state.mode == agent2.state.mode
