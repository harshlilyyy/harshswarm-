# =============================================================================
# SEEDED RANDOM — Deterministic PRNG for Reproducible Simulations
# =============================================================================
"""
All randomness in MiroFish flows through this class.
Same seed → identical outcomes across all scales and platforms.
"""

import random
from typing import List, TypeVar, Sequence, Optional
from dataclasses import dataclass


T = TypeVar('T')


@dataclass
class RandomState:
    """Snapshot of RNG state for checkpointing."""
    seed: int
    internal_state: tuple
    gauss_next: Optional[float]


class SeededRandom:
    """
    A wrapper around Python's random.Random that ensures full determinism.
    
    Features:
    - Seed-based reproducibility
    - State checkpointing for simulation branching
    - Multiple distribution support
    - Thread-safe operation (when used with per-thread instances)
    
    Usage:
        rng = SeededRandom(42)
        val = rng.random()           # 0-1 float
        val = rng.uniform(0, 1)      # range
        val = rng.gauss(0, 1)        # normal distribution
        choice = rng.choice([a, b, c])
        state = rng.get_state()      # for checkpointing
        rng.set_state(state)         # restore state
    """
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self._rng = random.Random(seed)
    
    def random(self) -> float:
        """Return random float in [0.0, 1.0)."""
        return self._rng.random()
    
    def uniform(self, low: float, high: float) -> float:
        """Return random float in [low, high)."""
        return self._rng.uniform(low, high)
    
    def gauss(self, mu: float, sigma: float) -> float:
        """Return random float from Gaussian distribution."""
        return self._rng.gauss(mu, sigma)
    
    def truncated_normal(self, mu: float, sigma: float, lower: float, upper: float) -> float:
        """
        Return random float from truncated normal distribution.
        
        Useful for psychological variables bounded to [0, 1].
        """
        while True:
            val = self.gauss(mu, sigma)
            if lower <= val <= upper:
                return val
    
    def beta(self, alpha: float, beta: float) -> float:
        """Return random float from Beta distribution."""
        return self._rng.beta(alpha, beta)
    
    def choice(self, seq: Sequence[T]) -> T:
        """Return random element from sequence."""
        return self._rng.choice(seq)
    
    def choices(self, population: Sequence[T], weights: Sequence[float] = None, k: int = 1) -> List[T]:
        """Return k random elements from population with optional weights."""
        return self._rng.choices(population, weights=weights, k=k)
    
    def sample(self, population: Sequence[T], k: int) -> List[T]:
        """Return k unique random elements from population."""
        return self._rng.sample(population, k)
    
    def randint(self, low: int, high: int) -> int:
        """Return random integer in [low, high]."""
        return self._rng.randint(low, high)
    
    def randrange(self, start: int, stop: int = None, step: int = 1) -> int:
        """Return random integer from range."""
        return self._rng.randrange(start, stop, step)
    
    def shuffle(self, seq: List[T]) -> List[T]:
        """Return shuffled copy of sequence."""
        result = seq.copy()
        self._rng.shuffle(result)
        return result
    
    def permutation(self, seq: Sequence[T]) -> List[T]:
        """Return random permutation of sequence."""
        return self.shuffle(list(seq))
    
    def weighted_choice(self, items: Sequence[T], weights: Sequence[float]) -> T:
        """
        Return random element based on weights.
        
        Args:
            items: Sequence of items to choose from
            weights: Sequence of weights (need not sum to 1)
        
        Returns:
            Selected item
        """
        total = sum(weights)
        normalized = [w / total for w in weights]
        r = self.random()
        cumulative = 0.0
        for item, weight in zip(items, normalized):
            cumulative += weight
            if r < cumulative:
                return item
        return items[-1]
    
    def get_state(self) -> RandomState:
        """
        Get current RNG state for checkpointing.
        
        Returns:
            RandomState object containing seed, internal state, and gauss cache
        """
        internal = self._rng.getstate()
        # Access private _gauss_next for Box-Muller transform state
        gauss_next = getattr(self._rng, '_gauss_next', None)
        return RandomState(
            seed=self.seed,
            internal_state=internal,
            gauss_next=gauss_next
        )
    
    def set_state(self, state: RandomState):
        """
        Restore RNG state from checkpoint.
        
        Args:
            state: RandomState object from get_state()
        """
        self.seed = state.seed
        self._rng.setstate(state.internal_state)
        if state.gauss_next is not None:
            setattr(self._rng, '_gauss_next', state.gauss_next)
    
    def fork(self, offset_seed: int = 0) -> 'SeededRandom':
        """
        Create a new SeededRandom with derived seed.
        
        Useful for creating independent RNG streams for parallel agents.
        
        Args:
            offset_seed: Additional offset to differentiate streams
        
        Returns:
            New SeededRandom instance
        """
        new_seed = self.seed * 1000003 + offset_seed + self.randint(0, 1000000)
        return SeededRandom(new_seed)
    
    def reset(self):
        """Reset to initial seed state."""
        self._rng = random.Random(self.seed)
