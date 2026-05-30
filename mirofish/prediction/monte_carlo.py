# =============================================================================
# MONTE CARLO SAMPLER — Parallel World Simulation
# =============================================================================
"""
Monte Carlo sampling for prediction:
- Run 100-1000+ parallel world simulations
- Extract causal chains
- Perform counterfactual analysis
- Quantify uncertainty and confidence
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import statistics
import threading

from ..core.seeded_random import SeededRandom
from ..simulation.engine import SimulationEngine, SimulationConfig, SimulationResult


@dataclass
class WorldSample:
    """
    A single sampled world from Monte Carlo simulation.
    
    Attributes:
        sample_id: Unique identifier
        seed: Random seed used
        outcome: Final outcome metrics
        trajectory: Time-series of key metrics
        causal_chain: Key events that led to outcome
        probability: Estimated probability of this outcome
    """
    sample_id: int
    seed: int
    outcome: Dict[str, Any]
    trajectory: List[Dict[str, Any]]
    causal_chain: List[Dict[str, Any]]
    probability: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "seed": self.seed,
            "outcome": self.outcome,
            "trajectory_length": len(self.trajectory),
            "causal_chain_length": len(self.causal_chain),
            "probability": self.probability
        }


@dataclass
class PredictionResult:
    """
    Aggregated results from Monte Carlo prediction.
    
    Attributes:
        samples: Individual world samples
        outcome_distribution: Distribution of outcomes
        confidence_intervals: Confidence bounds for predictions
        most_likely_scenario: Most probable outcome
        alternative_scenarios: Other significant outcomes
        uncertainty_metrics: Measures of prediction uncertainty
        causal_insights: Common causal patterns
    """
    samples: List[WorldSample]
    outcome_distribution: Dict[str, Any]
    confidence_intervals: Dict[str, Tuple[float, float]]
    most_likely_scenario: Dict[str, Any]
    alternative_scenarios: List[Dict[str, Any]]
    uncertainty_metrics: Dict[str, float]
    causal_insights: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "num_samples": len(self.samples),
            "outcome_distribution": self.outcome_distribution,
            "confidence_intervals": {
                k: list(v) for k, v in self.confidence_intervals.items()
            },
            "most_likely_scenario": self.most_likely_scenario,
            "alternative_scenarios_count": len(self.alternative_scenarios),
            "uncertainty_metrics": self.uncertainty_metrics,
            "causal_insights_count": len(self.causal_insights),
            "metadata": self.metadata
        }


class MonteCarloSampler:
    """
    Monte Carlo sampler for swarm intelligence prediction.
    
    Runs multiple parallel simulations with varied seeds and parameters
    to generate a distribution of possible futures.
    
    Features:
    - Parallel execution (threading or multiprocessing)
    - Adaptive sampling (focus on high-variance regions)
    - Early stopping (convergence detection)
    - Counterfactual analysis
    - Causal chain extraction
    
    Usage:
        sampler = MonteCarloSampler(base_config)
        result = sampler.run(num_samples=500, parallel=True)
    """
    
    def __init__(self, base_config: SimulationConfig):
        """
        Initialize sampler.
        
        Args:
            base_config: Base simulation configuration
        """
        self.base_config = base_config
        self._lock = threading.Lock()
        self._completed_samples = 0
        self._total_samples = 0
    
    def run(self, num_samples: int = 100,
            parallel: bool = True,
            max_workers: int = 4,
            use_processes: bool = False,
            adaptive: bool = False,
            early_stopping: bool = True,
            convergence_threshold: float = 0.01,
            progress_callback: Optional[Callable[[int, int], None]] = None) -> PredictionResult:
        """
        Run Monte Carlo sampling.
        
        Args:
            num_samples: Number of world samples to generate
            parallel: Enable parallel execution
            max_workers: Maximum parallel workers
            use_processes: Use processes instead of threads (for true parallelism)
            adaptive: Adaptively sample high-variance regions
            early_stopping: Stop early if converged
            convergence_threshold: Threshold for convergence detection
            progress_callback: Callback(current, total) for progress updates
        
        Returns:
            PredictionResult with aggregated predictions
        """
        self._completed_samples = 0
        self._total_samples = num_samples
        
        samples: List[WorldSample] = []
        executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
        
        if parallel and max_workers > 1:
            with executor_class(max_workers=max_workers) as executor:
                # Submit all samples
                futures = {}
                for i in range(num_samples):
                    sample_seed = self.base_config.seed * 1000003 + i
                    future = executor.submit(
                        self._run_single_sample,
                        i, sample_seed
                    )
                    futures[future] = i
                
                # Collect results
                for future in as_completed(futures):
                    sample = future.result()
                    samples.append(sample)
                    
                    with self._lock:
                        self._completed_samples += 1
                        if progress_callback:
                            progress_callback(self._completed_samples, num_samples)
                    
                    # Check early stopping
                    if early_stopping and len(samples) >= 20:
                        if self._check_convergence(samples, convergence_threshold):
                            break
        else:
            # Sequential execution
            for i in range(num_samples):
                sample_seed = self.base_config.seed * 1000003 + i
                sample = self._run_single_sample(i, sample_seed)
                samples.append(sample)
                
                self._completed_samples += 1
                if progress_callback:
                    progress_callback(self._completed_samples, num_samples)
        
        # Aggregate results
        return self._aggregate_results(samples)
    
    def _run_single_sample(self, sample_id: int, seed: int) -> WorldSample:
        """Run a single simulation sample."""
        # Create config with unique seed
        config = SimulationConfig(
            seed=seed,
            num_agents=self.base_config.num_agents,
            duration_hours=self.base_config.duration_hours,
            time_step_minutes=self.base_config.time_step_minutes,
            parallel=False,  # Disable internal parallelism for samples
            verbose=False
        )
        
        # Run simulation
        engine = SimulationEngine(config)
        engine.initialize()
        result = engine.run(blocking=True)
        
        # Extract outcome
        outcome = self._extract_outcome(result)
        
        # Extract trajectory from metrics
        trajectory = result.metrics_history
        
        # Extract causal chain from events
        causal_chain = self._extract_causal_chain(result)
        
        return WorldSample(
            sample_id=sample_id,
            seed=seed,
            outcome=outcome,
            trajectory=trajectory,
            causal_chain=causal_chain
        )
    
    def _extract_outcome(self, result: SimulationResult) -> Dict[str, Any]:
        """Extract key outcome metrics from simulation result."""
        stats = result.statistics
        
        # Calculate aggregate agent state
        agent_modes = {}
        anxieties = []
        self_worths = []
        
        for agent_state in result.agent_states.values():
            mode = agent_state.get('mode', 'OPTIMIZE')
            agent_modes[mode] = agent_modes.get(mode, 0) + 1
            anxieties.append(agent_state.get('anxiety', 0.5))
            self_worths.append(agent_state.get('self_worth', 0.5))
        
        total_agents = len(result.agent_states)
        
        return {
            "cascade_rate": stats.get('cascade_rate', 0),
            "agents_in_cascade": stats.get('agents_in_cascade', 0),
            "avg_anxiety": sum(anxieties) / len(anxieties) if anxieties else 0,
            "avg_self_worth": sum(self_worths) / len(self_worths) if self_worths else 0,
            "mode_distribution": agent_modes,
            "dominant_mode": max(agent_modes, key=agent_modes.get) if agent_modes else "UNKNOWN",
            "polarization": self._calculate_polarization(anxieties, self_worths),
            "stability_score": self._calculate_stability(agent_modes, total_agents)
        }
    
    def _calculate_polarization(self, anxieties: List[float], 
                                self_worths: List[float]) -> float:
        """Calculate population polarization score."""
        if len(anxieties) < 2:
            return 0.0
        
        anxiety_std = statistics.stdev(anxieties)
        self_worth_std = statistics.stdev(self_worths)
        
        # Higher std = more polarization
        return (anxiety_std + self_worth_std) / 2
    
    def _calculate_stability(self, modes: Dict[str, int], 
                            total: int) -> float:
        """Calculate stability score based on mode distribution."""
        if total == 0:
            return 0.0
        
        # EXECUTE and OPTIMIZE are stable modes
        stable_count = modes.get('EXECUTE', 0) + modes.get('OPTIMIZE', 0)
        
        # RECOVER and AVOID are unstable
        unstable_count = modes.get('RECOVER', 0) + modes.get('AVOID', 0)
        
        if unstable_count == 0:
            return 1.0
        
        return stable_count / total
    
    def _extract_causal_chain(self, result: SimulationResult) -> List[Dict[str, Any]]:
        """Extract key causal events from simulation."""
        causal_events = []
        
        # Look for significant events in the log
        for event in result.events_log:
            if event.get('type') in ['agent_update', 'interaction']:
                if event.get('success') or event.get('failure'):
                    causal_events.append({
                        "time": event.get('time'),
                        "type": event.get('type'),
                        "effect": "success" if event.get('success') else "failure",
                        "agent": event.get('agent_id')
                    })
        
        # Sort by time and take most significant
        causal_events.sort(key=lambda e: e.get('time', ''))
        return causal_events[-20:]  # Last 20 significant events
    
    def _check_convergence(self, samples: List[WorldSample], 
                          threshold: float) -> bool:
        """Check if sampling has converged."""
        if len(samples) < 20:
            return False
        
        # Check convergence of cascade rate
        recent = samples[-20:]
        cascade_rates = [s.outcome.get('cascade_rate', 0) for s in recent]
        
        if len(cascade_rates) < 2:
            return False
        
        # Calculate rolling variance
        mean = sum(cascade_rates) / len(cascade_rates)
        variance = sum((x - mean) ** 2 for x in cascade_rates) / len(cascade_rates)
        std = variance ** 0.5
        
        return std < threshold
    
    def _aggregate_results(self, samples: List[WorldSample]) -> PredictionResult:
        """Aggregate samples into prediction result."""
        if not samples:
            return self._empty_result()
        
        # Calculate outcome distribution
        cascade_rates = [s.outcome.get('cascade_rate', 0) for s in samples]
        anxiety_values = [s.outcome.get('avg_anxiety', 0.5) for s in samples]
        self_worth_values = [s.outcome.get('avg_self_worth', 0.5) for s in samples]
        stability_scores = [s.outcome.get('stability_score', 0.5) for s in samples]
        
        # Find most likely scenario
        mode_counts = {}
        for s in samples:
            mode = s.outcome.get('dominant_mode', 'UNKNOWN')
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        most_likely_mode = max(mode_counts, key=mode_counts.get)
        most_likely_probability = mode_counts[most_likely_mode] / len(samples)
        
        # Calculate confidence intervals (95%)
        def confidence_interval(values: List[float]) -> Tuple[float, float]:
            if len(values) < 2:
                return (0.0, 1.0)
            sorted_vals = sorted(values)
            lower_idx = int(len(sorted_vals) * 0.025)
            upper_idx = int(len(sorted_vals) * 0.975)
            return (sorted_vals[lower_idx], sorted_vals[upper_idx])
        
        ci_cascade = confidence_interval(cascade_rates)
        ci_anxiety = confidence_interval(anxiety_values)
        ci_self_worth = confidence_interval(self_worth_values)
        ci_stability = confidence_interval(stability_scores)
        
        # Calculate uncertainty metrics
        uncertainty = {
            "cascade_uncertainty": statistics.stdev(cascade_rates) if len(cascade_rates) > 1 else 0,
            "anxiety_uncertainty": statistics.stdev(anxiety_values) if len(anxiety_values) > 1 else 0,
            "scenario_entropy": self._calculate_entropy(mode_counts, len(samples)),
            "prediction_confidence": 1.0 - (statistics.stdev(stability_scores) if len(stability_scores) > 1 else 0)
        }
        
        # Extract causal insights
        causal_insights = self._aggregate_causal_chains([s.causal_chain for s in samples])
        
        # Identify alternative scenarios
        alternative_scenarios = self._identify_alternatives(samples, most_likely_mode)
        
        return PredictionResult(
            samples=samples,
            outcome_distribution={
                "cascade_rate": {
                    "mean": sum(cascade_rates) / len(cascade_rates),
                    "min": min(cascade_rates),
                    "max": max(cascade_rates),
                    "std": statistics.stdev(cascade_rates) if len(cascade_rates) > 1 else 0
                },
                "anxiety": {
                    "mean": sum(anxiety_values) / len(anxiety_values),
                    "min": min(anxiety_values),
                    "max": max(anxiety_values)
                },
                "self_worth": {
                    "mean": sum(self_worth_values) / len(self_worth_values),
                    "min": min(self_worth_values),
                    "max": max(self_worth_values)
                },
                "dominant_modes": mode_counts
            },
            confidence_intervals={
                "cascade_rate": ci_cascade,
                "avg_anxiety": ci_anxiety,
                "avg_self_worth": ci_self_worth,
                "stability": ci_stability
            },
            most_likely_scenario={
                "dominant_mode": most_likely_mode,
                "probability": most_likely_probability,
                "description": self._describe_scenario(most_likely_mode)
            },
            alternative_scenarios=alternative_scenarios,
            uncertainty_metrics=uncertainty,
            causal_insights=causal_insights,
            metadata={
                "total_samples": len(samples),
                "seeds_used": [s.seed for s in samples[:10]],  # First 10 seeds
                "sampling_complete": self._completed_samples >= self._total_samples
            }
        )
    
    def _calculate_entropy(self, counts: Dict[str, int], 
                          total: int) -> float:
        """Calculate entropy of scenario distribution."""
        if total == 0:
            return 0.0
        
        entropy = 0.0
        for count in counts.values():
            if count > 0:
                p = count / total
                entropy -= p * (p and math.log2(p) or 0)
        
        return entropy
    
    def _describe_scenario(self, mode: str) -> str:
        """Generate human-readable scenario description."""
        descriptions = {
            "EXECUTE": "High-confidence action-taking dominates; population actively pursuing goals",
            "OPTIMIZE": "Steady improvement mode; balanced approach with incremental progress",
            "AVOID": "Withdrawal behavior prevalent; high anxiety and low self-worth across population",
            "RECOVER": "Cascade failures active; significant portion of population in recovery",
            "SPIKE": "High-arousal performance state; stress combined with confidence"
        }
        return descriptions.get(mode, "Mixed/uncertain behavioral pattern")
    
    def _aggregate_causal_chains(self, chains: List[List[Dict]]) -> List[Dict]:
        """Aggregate causal chains from multiple samples."""
        # Count event types
        event_counts = {}
        for chain in chains:
            for event in chain:
                event_type = f"{event.get('type')}:{event.get('effect', 'neutral')}"
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Return most common patterns
        sorted_events = sorted(event_counts.items(), key=lambda x: -x[1])
        return [
            {"pattern": k, "frequency": v, "proportion": v / len(chains)}
            for k, v in sorted_events[:10]
        ]
    
    def _identify_alternatives(self, samples: List[WorldSample], 
                               primary_mode: str) -> List[Dict[str, Any]]:
        """Identify alternative scenarios."""
        mode_samples = {}
        for s in samples:
            mode = s.outcome.get('dominant_mode', 'UNKNOWN')
            if mode not in mode_samples:
                mode_samples[mode] = []
            mode_samples[mode].append(s)
        
        alternatives = []
        for mode, mode_samps in mode_samples.items():
            if mode == primary_mode:
                continue
            
            avg_cascade = sum(s.outcome.get('cascade_rate', 0) for s in mode_samps) / len(mode_samps)
            
            alternatives.append({
                "scenario": mode,
                "probability": len(mode_samps) / len(samples),
                "avg_cascade_rate": avg_cascade,
                "sample_count": len(mode_samps),
                "description": self._describe_scenario(mode)
            })
        
        # Sort by probability
        alternatives.sort(key=lambda x: -x['probability'])
        return alternatives[:5]  # Top 5 alternatives
    
    def _empty_result(self) -> PredictionResult:
        """Return empty prediction result."""
        return PredictionResult(
            samples=[],
            outcome_distribution={},
            confidence_intervals={},
            most_likely_scenario={"dominant_mode": "UNKNOWN", "probability": 0},
            alternative_scenarios=[],
            uncertainty_metrics={"prediction_confidence": 0},
            causal_insights=[]
        )
    
    def run_counterfactual(self, intervention: Dict[str, Any],
                          num_samples: int = 50) -> Dict[str, Any]:
        """
        Run counterfactual analysis with intervention.
        
        Args:
            intervention: Dictionary describing intervention to apply
            num_samples: Number of samples to run
        
        Returns:
            Comparison between factual and counterfactual outcomes
        """
        # Run baseline
        baseline = self.run(num_samples=num_samples // 2, parallel=True)
        
        # Run with intervention (modify config)
        # This is a simplified version - full implementation would
        # modify simulation parameters based on intervention
        counterfactual_config = SimulationConfig(
            seed=self.base_config.seed + 999999,
            num_agents=self.base_config.num_agents,
            duration_hours=self.base_config.duration_hours,
            interaction_probability=intervention.get('interaction_modifier', 1.0) * self.base_config.interaction_probability
        )
        
        counterfactual_sampler = MonteCarloSampler(counterfactual_config)
        counterfactual = counterfactual_sampler.run(num_samples=num_samples // 2, parallel=True)
        
        # Compare outcomes
        baseline_cascade = baseline.outcome_distribution.get('cascade_rate', {}).get('mean', 0)
        counterfactual_cascade = counterfactual.outcome_distribution.get('cascade_rate', {}).get('mean', 0)
        
        return {
            "intervention": intervention,
            "baseline_cascade_rate": baseline_cascade,
            "counterfactual_cascade_rate": counterfactual_cascade,
            "effect_size": counterfactual_cascade - baseline_cascade,
            "baseline_samples": len(baseline.samples),
            "counterfactual_samples": len(counterfactual.samples)
        }


# Import math for entropy calculation
import math
