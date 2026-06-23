"""Tests for the SeededRandom class to ensure deterministic behavior."""

import pytest
from mirofish.core.seeded_random import SeededRandom


class TestSeededRandom:
    """Test suite for SeededRandom class."""
    
    def test_deterministic_sequence(self, seeded_rng):
        """Verify that same seed produces identical sequence."""
        rng1 = SeededRandom(seed=42)
        rng2 = SeededRandom(seed=42)
        
        # Generate sequence of random numbers
        seq1 = [rng1.uniform(0, 1) for _ in range(10)]
        seq2 = [rng2.uniform(0, 1) for _ in range(10)]
        
        assert seq1 == seq2, "Same seed should produce identical sequences"
    
    def test_different_seeds_different_sequences(self):
        """Verify that different seeds produce different sequences."""
        rng1 = SeededRandom(seed=42)
        rng2 = SeededRandom(seed=43)
        
        val1 = rng1.uniform(0, 1)
        val2 = rng2.uniform(0, 1)
        
        assert val1 != val2, "Different seeds should produce different sequences"
    
    def test_uniform_distribution_range(self, seeded_rng):
        """Verify uniform() returns values within specified range."""
        for _ in range(100):
            val = seeded_rng.uniform(0, 1)
            assert 0 <= val <= 1, f"Value {val} out of range [0, 1]"
    
    def test_uniform_custom_range(self, seeded_rng):
        """Verify uniform() works with custom ranges."""
        min_val, max_val = 5.0, 10.0
        for _ in range(100):
            val = seeded_rng.uniform(min_val, max_val)
            assert min_val <= val <= max_val, f"Value {val} out of range [{min_val}, {max_val}]"
    
    def test_gaussian_distribution(self, seeded_rng):
        """Verify gauss() returns reasonable values."""
        mean, std = 0.0, 1.0
        values = [seeded_rng.gauss(mean, std) for _ in range(1000)]
        
        # Check that most values are within 3 standard deviations
        within_3std = sum(1 for v in values if abs(v - mean) <= 3 * std)
        assert within_3std > 950, "Most values should be within 3 standard deviations"
    
    def test_choice_from_list(self, seeded_rng):
        """Verify choice() selects from provided list."""
        options = ['a', 'b', 'c', 'd', 'e']
        selections = [seeded_rng.choice(options) for _ in range(100)]
        
        # All selections should be from the original list
        assert all(s in options for s in selections), "All choices should be from options list"
        
        # With enough samples, we should see all options (probabilistic)
        unique_selections = set(selections)
        assert len(unique_selections) > 1, "Should see variety in selections"
    
    def test_shuffle_deterministic(self):
        """Verify shuffle is deterministic with same seed."""
        rng1 = SeededRandom(seed=123)
        rng2 = SeededRandom(seed=123)
        
        list1 = [1, 2, 3, 4, 5]
        list2 = [1, 2, 3, 4, 5]
        
        rng1.shuffle(list1)
        rng2.shuffle(list2)
        
        assert list1 == list2, "Same seed should produce identical shuffles"
    
    def test_state_preservation(self, seeded_rng):
        """Verify that saving and restoring state works correctly."""
        # Generate some values
        val1 = seeded_rng.uniform(0, 1)
        val2 = seeded_rng.uniform(0, 1)
        
        # Save state
        state = seeded_rng.get_state()
        
        # Generate more values
        val3 = seeded_rng.uniform(0, 1)
        
        # Restore state
        seeded_rng.set_state(state)
        
        # Should generate same value as val3
        val3_restored = seeded_rng.uniform(0, 1)
        
        assert val3 == val3_restored, "Restored state should produce same sequence"
    
    def test_multiple_instances_independent(self):
        """Verify that multiple instances don't interfere with each other."""
        rng1 = SeededRandom(seed=100)
        rng2 = SeededRandom(seed=200)
        
        # Generate values from both
        val1_a = rng1.uniform(0, 1)
        val2_a = rng2.uniform(0, 1)
        val1_b = rng1.uniform(0, 1)
        val2_b = rng2.uniform(0, 1)
        
        # Create new instances with same seeds
        rng1_new = SeededRandom(seed=100)
        rng2_new = SeededRandom(seed=200)
        
        assert rng1_new.uniform(0, 1) == val1_a, "RNG1 should be reproducible"
        assert rng2_new.uniform(0, 1) == val2_a, "RNG2 should be reproducible"
