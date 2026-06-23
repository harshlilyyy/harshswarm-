# =============================================================================
# NYX KERNEL — Deterministic Cognitive-Social Physics Engine
# =============================================================================
"""
Nyx Kernel v2.0
A fully deterministic, seed-reproducible simulation engine for modeling
agent-based decision intelligence using cognitive-social physics.

All randomness is controlled via SeededRandom class. Same seed → identical outcomes.
"""

import random
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from copy import deepcopy


# =============================================================================
# 1. SEEDED PRNG — Deterministic Random Number Generator
# =============================================================================
class SeededRandom:
    """
    A wrapper around Python's random.Random that ensures full determinism.
    All simulation randomness flows through this class.
    
    Usage:
        rng = SeededRandom(42)
        val = rng.random()      # 0-1 float
        val = rng.uniform(0, 1) # range
        val = rng.gauss(0, 1)   # normal distribution
        choice = rng.choice([a, b, c])
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
    
    def choice(self, seq: list):
        """Return random element from sequence."""
        return self._rng.choice(seq)
    
    def randint(self, low: int, high: int) -> int:
        """Return random integer in [low, high]."""
        return self._rng.randint(low, high)
    
    def shuffle(self, seq: list) -> list:
        """Return shuffled copy of sequence."""
        result = seq.copy()
        self._rng.shuffle(result)
        return result


# =============================================================================
# 2. COGNITIVE AGENT — 10-Dimensional Psychological State Machine
# =============================================================================
@dataclass
class AgentState:
    """Snapshot of agent state at a given round."""
    self_worth: float
    anxiety: float
    consistency: float
    momentum: float
    reputation: float
    opportunity_access: float
    fragility_index: float
    lock_in: float
    learning_rate: float
    energy: float
    mode: str
    cascade_active: bool
    success_streak: int
    failure_streak: int


class CognitiveAgent:
    """
    A cognitive agent with 10 internal psychological variables (all 0-1 scale).
    
    Variables:
    - self_worth: Core self-evaluation and confidence
    - anxiety: Stress response to uncertainty and peer comparison
    - consistency: Behavioral stability across situations
    - momentum: Accumulated forward progress energy
    - reputation: Social standing in the network
    - opportunity_access: Access to resources/connections
    - fragility_index: Susceptibility to cascading failures
    - lock_in: Commitment to current strategy/path
    - learning_rate: Adaptation speed from feedback
    - energy: Available cognitive/emotional capacity
    
    Modes:
    - AVOID: Withdrawal due to high anxiety + low self-worth
    - RECOVER: Active recovery from cascade failure
    - EXECUTE: High-confidence action mode
    - OPTIMIZE: Balanced improvement mode
    - SPIKE: High-arousal performance state
    """
    
    def __init__(self, name: str, rng: SeededRandom):
        self.name = name
        self.rng = rng
        
        # Initialize 10 core variables with small random variation around baseline
        self.self_worth = self.clamp(0.5 + rng.uniform(-0.15, 0.15))
        self.anxiety = self.clamp(0.3 + rng.uniform(-0.1, 0.15))
        self.consistency = self.clamp(0.5 + rng.uniform(-0.1, 0.1))
        self.momentum = self.clamp(0.5 + rng.uniform(-0.1, 0.1))
        self.reputation = self.clamp(0.5 + rng.uniform(-0.1, 0.1))
        self.opportunity_access = self.clamp(0.5 + rng.uniform(-0.1, 0.1))
        self.fragility_index = self.clamp(0.15 + rng.uniform(0, 0.1))
        self.lock_in = self.clamp(0.1 + rng.uniform(0, 0.1))
        self.learning_rate = self.clamp(0.15 + rng.uniform(-0.05, 0.05))
        self.energy = self.clamp(0.7 + rng.uniform(-0.1, 0.15))
        
        # State tracking
        self.mode = "EXECUTE"
        self.cascade_active = False
        self.success_streak = 0
        self.failure_streak = 0
        self.intent_target = None
        self.emotional_anchor = None
        
        # History of all states (for analysis)
        self.history: List[AgentState] = []
    
    @staticmethod
    def clamp(val: float) -> float:
        """Clamp value to [0, 1] range."""
        return max(0.0, min(1.0, val))
    
    def update(self, progress: float, peer_gap: float, social_feedback: float,
               failure_flag: bool, success_flag: bool, mentor_flag: bool = False):
        """
        Update all 10 psychological variables based on round events.
        
        Uses reduced-damping update equations for realistic dynamics.
        All changes are clamped to [0, 1] range.
        
        Args:
            progress: Task completion ratio (0-1)
            peer_gap: Normalized difference vs peers (0 = equal, 1 = far behind)
            social_feedback: Social validation signal (-1 to 1)
            failure_flag: Binary failure event occurred
            success_flag: Binary success event occurred
            mentor_flag: Mentorship/support received
        """
        # Convert flags to numeric
        f_fail = 1.0 if failure_flag else 0.0
        f_succ = 1.0 if success_flag else 0.0
        f_mentor = 1.0 if mentor_flag else 0.0
        
        # === REDUCED-DAMPING UPDATE EQUATIONS ===
        
        # Self-worth: Driven by progress, hurt by peer comparison and failure
        self.self_worth = self.clamp(
            self.self_worth 
            + 0.25 * progress 
            - 0.3 * max(peer_gap, 0) 
            + 0.15 * social_feedback 
            - 0.2 * f_fail
        )
        
        # Anxiety: Smoothed blend of current anxiety and new stressors
        raw_anxiety_change = peer_gap * 0.5 + f_fail * 0.5 - f_succ * 0.3
        self.anxiety = self.clamp(0.4 * self.anxiety + 0.6 * raw_anxiety_change)
        
        # Consistency: Grows with stability, hurt by failures
        self.consistency = self.clamp(
            self.consistency 
            + 0.05 * (1 - peer_gap) 
            - 0.1 * f_fail
        )
        
        # Momentum: Built by success, destroyed by failure (no quadratic damping)
        self.momentum = self.clamp(
            self.momentum 
            + 0.25 * f_succ 
            - 0.3 * f_fail
        )
        
        # Reputation: Earned through progress and social validation
        self.reputation = self.clamp(
            self.reputation 
            + 0.2 * progress 
            + 0.1 * social_feedback
        )
        
        # Opportunity access: Unlocks when consistency × reputation threshold met
        threshold_bonus = 0.2 if (self.consistency * self.reputation > 0.4) else 0.0
        self.opportunity_access = self.clamp(
            self.opportunity_access 
            + threshold_bonus 
            + 0.15 * f_mentor
        )
        
        # Fragility index: Accumulates with failures (vulnerability memory)
        self.fragility_index = self.clamp(
            self.fragility_index 
            + 0.1 * f_fail
        )
        
        # Lock-in: Commitment grows with consistency
        self.lock_in = self.clamp(
            self.lock_in 
            + 0.1 * self.consistency
        )
        
        # Learning rate: Increases from failure (lessons), decreases from easy success
        self.learning_rate = self.clamp(
            self.learning_rate 
            + 0.1 * f_fail 
            - 0.05 * f_succ
        )
        
        # Energy: Base drain offset by success boost
        self.energy = self.clamp(
            self.energy 
            - 0.05 
            + 0.1 * f_succ
        )
        
        # === CASCADE LOGIC ===
        # Enter cascade if 3+ consecutive failures AND self-worth critically low
        if failure_flag:
            self.failure_streak += 1
            self.success_streak = 0
        elif success_flag:
            self.success_streak += 1
            self.failure_streak = 0
        else:
            # No event - maintain streaks
            pass
        
        if self.failure_streak >= 3 and self.self_worth < 0.4:
            self.cascade_active = True
        elif self.cascade_active and (success_flag or mentor_flag):
            # Exit cascade on success or mentorship
            self.cascade_active = False
            self.failure_streak = 0
        
        # === MODE TRANSITION ===
        # Priority order: RECOVER > SPIKE > AVOID > EXECUTE > OPTIMIZE
        if self.cascade_active:
            self.mode = "RECOVER"
        elif self.anxiety > 0.7 and self.self_worth > 0.6:
            self.mode = "SPIKE"  # High arousal performance
        elif self.anxiety > 0.6 and self.self_worth < 0.4:
            self.mode = "AVOID"  # Withdrawal
        elif self.self_worth > 0.5 and self.momentum > 0.5:
            self.mode = "EXECUTE"  # Confident action
        else:
            self.mode = "OPTIMIZE"  # Steady improvement
        
        # Save state snapshot to history
        self._save_state()
    
    def _save_state(self):
        """Record current state to history."""
        state = AgentState(
            self_worth=self.self_worth,
            anxiety=self.anxiety,
            consistency=self.consistency,
            momentum=self.momentum,
            reputation=self.reputation,
            opportunity_access=self.opportunity_access,
            fragility_index=self.fragility_index,
            lock_in=self.lock_in,
            learning_rate=self.learning_rate,
            energy=self.energy,
            mode=self.mode,
            cascade_active=self.cascade_active,
            success_streak=self.success_streak,
            failure_streak=self.failure_streak
        )
        self.history.append(state)
    
    def get_current_state_dict(self) -> Dict[str, Any]:
        """Return current state as dictionary."""
        return {
            "self_worth": self.self_worth,
            "anxiety": self.anxiety,
            "consistency": self.consistency,
            "momentum": self.momentum,
            "reputation": self.reputation,
            "opportunity_access": self.opportunity_access,
            "fragility_index": self.fragility_index,
            "lock_in": self.lock_in,
            "learning_rate": self.learning_rate,
            "energy": self.energy,
            "mode": self.mode,
            "cascade_active": self.cascade_active,
            "success_streak": self.success_streak,
            "failure_streak": self.failure_streak
        }


# =============================================================================
# 3. MAIN SIMULATION ENGINE
# =============================================================================
def run_simulation(agent_names: List[str], rounds: int = 8, seed: int = 42) -> Dict[str, Any]:
    """
    Run a complete cognitive-social simulation.
    
    Args:
        agent_names: List of agent names
        rounds: Number of simulation rounds
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary containing:
        - state_history: List of round-by-round state dictionaries
        - outcome_vector: Aggregate metrics (reputation_mean, inequality, trust_proxy, centralization)
        - agents: List of CognitiveAgent objects
        - influence: Influence matrix (adjacency dict)
        - seed: The seed used
    """
    rng = SeededRandom(seed)
    
    # Create agents
    agents = [CognitiveAgent(name, rng) for name in agent_names]
    n_agents = len(agents)
    
    # Build dense influence matrix (directed weighted graph)
    # influence[i][j] = how much agent i influences agent j
    influence = {}
    for i, a1 in enumerate(agents):
        influence[a1.name] = {}
        for j, a2 in enumerate(agents):
            if i != j:
                # Random weight 0.1-0.9
                influence[a1.name][a2.name] = rng.uniform(0.1, 0.9)
            else:
                influence[a1.name][a2.name] = 0.0
    
    state_history = []
    
    # Run simulation rounds
    for round_num in range(rounds):
        round_states = {}
        
        for agent in agents:
            # Compute peer_gap: weighted average of reputation differences
            total_weight = sum(influence[other.name][agent.name] for other in agents if other.name != agent.name)
            if total_weight > 0:
                weighted_diff = sum(
                    influence[other.name][agent.name] * abs(other.reputation - agent.reputation)
                    for other in agents if other.name != agent.name
                )
                peer_gap = weighted_diff / total_weight
            else:
                peer_gap = 0.5
            
            # Generate round events (deterministic via seeded RNG)
            progress = rng.uniform(0.3, 0.8)
            social_feedback = rng.uniform(-0.3, 0.3)
            failure_flag = rng.random() < 0.10  # 10% chance
            success_flag = rng.random() < 0.25  # 25% chance
            mentor_flag = rng.random() < 0.05   # 5% chance
            
            # Update agent state
            agent.update(progress, peer_gap, social_feedback, failure_flag, success_flag, mentor_flag)
            
            # Store state
            round_states[agent.name] = agent.get_current_state_dict()
        
        state_history.append(round_states)
    
    # Compute outcome vector
    rep_values = [a.reputation for a in agents]
    opp_values = [a.opportunity_access for a in agents]
    trust_values = [a.lock_in for a in agents]
    
    reputation_mean = sum(rep_values) / n_agents
    
    # Inequality = variance of opportunity access
    opp_mean = sum(opp_values) / n_agents
    inequality = sum((x - opp_mean) ** 2 for x in opp_values) / n_agents
    
    # Trust proxy = mean lock-in
    trust_proxy = sum(trust_values) / n_agents
    
    # Centralization = degree centrality of influence graph
    # (normalized sum of outgoing influence weights)
    centrality_scores = []
    for agent in agents:
        out_strength = sum(influence[agent.name].values())
        centrality_scores.append(out_strength)
    max_possible = (n_agents - 1) * 0.9  # max weight 0.9 per edge
    centralization = (max(centrality_scores) / max_possible) if max_possible > 0 else 0
    
    outcome_vector = {
        "reputation_mean": reputation_mean,
        "inequality": inequality,
        "trust_proxy": trust_proxy,
        "centralization": centralization
    }
    
    return {
        "state_history": state_history,
        "outcome_vector": outcome_vector,
        "agents": agents,
        "influence": influence,
        "seed": seed
    }


# =============================================================================
# 4. ADVANCED ANALYSIS FUNCTIONS
# =============================================================================

def detect_black_swan(agents: List[CognitiveAgent], state_history: List[Dict]) -> Dict[str, Any]:
    """
    Detect the most fragile assumption in the simulation.
    
    Identifies agents with high anxiety (>0.6) and low self_worth (<0.45),
    then picks the one with maximum anxiety * (1 - self_worth).
    
    Returns:
        Dictionary with assumption, why_fragile, break_scenario, impact
    """
    if not state_history:
        return {
            "assumption": "No data available",
            "why_fragile": "Simulation did not produce results",
            "break_scenario": "N/A",
            "impact": "Unknown"
        }
    
    # Use final round states
    final_states = state_history[-1]
    
    candidates = []
    for name, state in final_states.items():
        anxiety = state["anxiety"]
        self_worth = state["self_worth"]
        if anxiety > 0.6 and self_worth < 0.45:
            fragility_score = anxiety * (1 - self_worth)
            candidates.append((name, fragility_score, state))
    
    if not candidates:
        # No obvious black swan - pick most anxious agent
        most_anxious = max(final_states.items(), key=lambda x: x[1]["anxiety"])
        return {
            "assumption": f"Stability of {most_anxious[0]}",
            "why_fragile": f"Elevated anxiety ({most_anxious[1]['anxiety']:.2f}) without critical self-worth drop",
            "break_scenario": "Unexpected external shock could trigger cascade",
            "impact": "Moderate - localized disruption"
        }
    
    # Pick most fragile
    candidates.sort(key=lambda x: x[1], reverse=True)
    name, score, state = candidates[0]
    
    return {
        "assumption": f"{name}'s continued participation",
        "why_fragile": f"High anxiety ({state['anxiety']:.2f}) + low self-worth ({state['self_worth']:.2f})",
        "break_scenario": f"A single additional failure could push {name} into cascade failure",
        "impact": f"Critical - fragility score {score:.3f}. May trigger network contagion."
    }


def run_counterfactual(agent_names: List[str], rounds: int, seed: int,
                       variable: str, delta_percent: float) -> Dict[str, Any]:
    """
    Run a counterfactual simulation where one variable is perturbed.
    
    Args:
        agent_names: List of agent names
        rounds: Number of rounds
        seed: Base seed
        variable: Variable to perturb (e.g., "anxiety", "self_worth")
        delta_percent: Percentage change (e.g., 20 for +20%)
    
    Returns:
        Dictionary with original_outcome, perturbed_outcome, delta
    """
    # Run original
    original_result = run_simulation(agent_names, rounds, seed)
    original_outcome = original_result["outcome_vector"]
    
    # Run perturbed (use different seed to avoid exact same random sequence)
    perturbed_seed = seed + 10000
    rng = SeededRandom(perturbed_seed)
    
    agents_pert = [CognitiveAgent(name, rng) for name in agent_names]
    
    # Apply perturbation to initial state
    multiplier = 1.0 + (delta_percent / 100.0)
    for agent in agents_pert:
        if hasattr(agent, variable):
            current_val = getattr(agent, variable)
            new_val = CognitiveAgent.clamp(current_val * multiplier)
            setattr(agent, variable, new_val)
    
    # Run simulation for perturbed agents
    n_agents = len(agents_pert)
    influence = {}
    for i, a1 in enumerate(agents_pert):
        influence[a1.name] = {}
        for j, a2 in enumerate(agents_pert):
            influence[a1.name][a2.name] = rng.uniform(0.1, 0.9) if i != j else 0.0
    
    for _ in range(rounds):
        for agent in agents_pert:
            total_weight = sum(influence[other.name][agent.name] for other in agents_pert if other.name != agent.name)
            peer_gap = 0.5
            if total_weight > 0:
                weighted_diff = sum(
                    influence[other.name][agent.name] * abs(other.reputation - agent.reputation)
                    for other in agents_pert if other.name != agent.name
                )
                peer_gap = weighted_diff / total_weight
            
            progress = rng.uniform(0.3, 0.8)
            social_feedback = rng.uniform(-0.3, 0.3)
            failure_flag = rng.random() < 0.10
            success_flag = rng.random() < 0.25
            mentor_flag = rng.random() < 0.05
            
            agent.update(progress, peer_gap, social_feedback, failure_flag, success_flag, mentor_flag)
    
    # Compute perturbed outcome
    rep_values = [a.reputation for a in agents_pert]
    opp_values = [a.opportunity_access for a in agents_pert]
    trust_values = [a.lock_in for a in agents_pert]
    
    perturbed_outcome = {
        "reputation_mean": sum(rep_values) / n_agents,
        "inequality": sum((x - sum(opp_values)/n_agents) ** 2 for x in opp_values) / n_agents,
        "trust_proxy": sum(trust_values) / n_agents,
        "centralization": original_outcome["centralization"]  # Same structure
    }
    
    # Compute deltas
    delta = {
        "reputation_mean": perturbed_outcome["reputation_mean"] - original_outcome["reputation_mean"],
        "inequality": perturbed_outcome["inequality"] - original_outcome["inequality"],
        "trust_proxy": perturbed_outcome["trust_proxy"] - original_outcome["trust_proxy"]
    }
    
    return {
        "original_outcome": original_outcome,
        "perturbed_outcome": perturbed_outcome,
        "delta": delta,
        "variable": variable,
        "delta_percent": delta_percent
    }


def run_multi_trial(agent_names: List[str], rounds: int, base_seed: int,
                    num_trials: int = 50) -> Dict[str, Any]:
    """
    Run multiple trials with sequential seeds and compute statistics.
    
    Args:
        agent_names: List of agent names
        rounds: Number of rounds per trial
        base_seed: Starting seed
        num_trials: Number of trials to run
    
    Returns:
        Dictionary with mean, std, clusters, all_outcomes
    """
    all_outcomes = []
    
    for i in range(num_trials):
        seed = base_seed + i
        result = run_simulation(agent_names, rounds, seed)
        all_outcomes.append(result["outcome_vector"])
    
    # Extract metrics
    rep_means = [o["reputation_mean"] for o in all_outcomes]
    trust_proxies = [o["trust_proxy"] for o in all_outcomes]
    inequalities = [o["inequality"] for o in all_outcomes]
    centralizations = [o["centralization"] for o in all_outcomes]
    
    # Compute mean and std
    def mean(lst):
        return sum(lst) / len(lst)
    
    def std(lst):
        m = mean(lst)
        variance = sum((x - m) ** 2 for x in lst) / len(lst)
        return math.sqrt(variance)
    
    stats = {
        "reputation_mean": {"mean": mean(rep_means), "std": std(rep_means)},
        "trust_proxy": {"mean": mean(trust_proxies), "std": std(trust_proxies)},
        "inequality": {"mean": mean(inequalities), "std": std(inequalities)},
        "centralization": {"mean": mean(centralizations), "std": std(centralizations)}
    }
    
    # Simple k-means clustering (k=3) on reputation_mean and trust_proxy
    # Using manual implementation to avoid sklearn dependency
    clusters = _simple_kmeans(rep_means, trust_proxies, k=3, max_iter=20)
    
    return {
        "stats": stats,
        "clusters": clusters,
        "num_trials": num_trials,
        "all_outcomes": all_outcomes
    }


def _simple_kmeans(x_vals: List[float], y_vals: List[float], k: int = 3, max_iter: int = 20) -> List[Dict]:
    """
    Simple k-means clustering without sklearn.
    Clusters points (x, y) into k groups.
    """
    n = len(x_vals)
    if n < k:
        return [{"id": i, "size": 1, "center": (x_vals[i] if i < n else 0, y_vals[i] if i < n else 0)} 
                for i in range(n)]
    
    # Initialize centroids evenly spaced
    points = list(zip(x_vals, y_vals))
    points_sorted = sorted(points, key=lambda p: p[0] + p[1])
    step = n // k
    centroids = [points_sorted[i * step] for i in range(k)]
    
    assignments = [0] * n
    
    for _ in range(max_iter):
        # Assign points to nearest centroid
        for i, point in enumerate(points):
            min_dist = float('inf')
            best_cluster = 0
            for c_idx, centroid in enumerate(centroids):
                dist = (point[0] - centroid[0]) ** 2 + (point[1] - centroid[1]) ** 2
                if dist < min_dist:
                    min_dist = dist
                    best_cluster = c_idx
            assignments[i] = best_cluster
        
        # Update centroids
        new_centroids = []
        for c_idx in range(k):
            cluster_points = [points[i] for i in range(n) if assignments[i] == c_idx]
            if cluster_points:
                cx = sum(p[0] for p in cluster_points) / len(cluster_points)
                cy = sum(p[1] for p in cluster_points) / len(cluster_points)
                new_centroids.append((cx, cy))
            else:
                new_centroids.append(centroids[c_idx])
        
        if new_centroids == centroids:
            break
        centroids = new_centroids
    
    # Build cluster summary
    cluster_summary = []
    for c_idx in range(k):
        size = sum(1 for a in assignments if a == c_idx)
        cluster_summary.append({
            "id": c_idx,
            "size": size,
            "center": centroids[c_idx]
        })
    
    return cluster_summary


def game_theory_insights(agents: List[CognitiveAgent]) -> Dict[str, Any]:
    """
    Analyze agent modes for game-theoretic patterns.
    
    Returns:
        Dictionary with mode_counts, dominant_strategy, nash_analysis, summary
    """
    mode_counts = {}
    for agent in agents:
        mode = agent.mode
        mode_counts[mode] = mode_counts.get(mode, 0) + 1
    
    # Find dominant strategy (if >50% in same mode)
    n_agents = len(agents)
    dominant_strategy = None
    for mode, count in mode_counts.items():
        if count > n_agents / 2:
            dominant_strategy = mode
            break
    
    # Nash-like analysis
    nash_analysis = []
    if mode_counts.get("EXECUTE", 0) == n_agents:
        nash_analysis.append("All agents in EXECUTE mode - potential coordination equilibrium")
    elif mode_counts.get("AVOID", 0) > n_agents / 3:
        nash_analysis.append("Significant avoidance behavior - possible tragedy of the commons")
    elif mode_counts.get("RECOVER", 0) > 0:
        nash_analysis.append("Cascade failures detected - system instability warning")
    elif mode_counts.get("SPIKE", 0) > n_agents / 3:
        nash_analysis.append("High-arousal state prevalent - risk of burnout or breakthrough")
    
    if not nash_analysis:
        nash_analysis.append("Mixed strategy equilibrium - diverse behavioral patterns")
    
    # Generate summary text
    summary_parts = []
    for mode in ["EXECUTE", "OPTIMIZE", "AVOID", "RECOVER", "SPIKE"]:
        count = mode_counts.get(mode, 0)
        if count > 0:
            summary_parts.append(f"{count}x {mode}")
    
    return {
        "mode_counts": mode_counts,
        "dominant_strategy": dominant_strategy,
        "nash_analysis": nash_analysis,
        "summary": ", ".join(summary_parts) if summary_parts else "No agents analyzed"
    }


# =============================================================================
# END OF NYX KERNEL
# =============================================================================
