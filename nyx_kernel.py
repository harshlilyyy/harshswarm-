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
from functools import lru_cache


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
        
        # Cache frequently used values
        sw = self.self_worth
        anx = self.anxiety
        cons = self.consistency
        mom = self.momentum
        rep = self.reputation
        opp = self.opportunity_access
        frag = self.fragility_index
        lock = self.lock_in
        lr = self.learning_rate
        energy = self.energy
        
        # === REDUCED-DAMPING UPDATE EQUATIONS ===
        
        # Self-worth: Driven by progress, hurt by peer comparison and failure
        self.self_worth = self.clamp(
            sw + 0.25 * progress - 0.3 * max(peer_gap, 0) + 0.15 * social_feedback - 0.2 * f_fail
        )
        
        # Anxiety: Smoothed blend of current anxiety and new stressors
        self.anxiety = self.clamp(0.4 * anx + 0.6 * (peer_gap * 0.5 + f_fail * 0.5 - f_succ * 0.3))
        
        # Consistency: Grows with stability, hurt by failures
        self.consistency = self.clamp(cons + 0.05 * (1 - peer_gap) - 0.1 * f_fail)
        
        # Momentum: Built by success, destroyed by failure (no quadratic damping)
        self.momentum = self.clamp(mom + 0.25 * f_succ - 0.3 * f_fail)
        
        # Reputation: Earned through progress and social validation
        self.reputation = self.clamp(rep + 0.2 * progress + 0.1 * social_feedback)
        
        # Opportunity access: Unlocks when consistency × reputation threshold met
        threshold_bonus = 0.2 if (self.consistency * self.reputation > 0.4) else 0.0
        self.opportunity_access = self.clamp(opp + threshold_bonus + 0.15 * f_mentor)
        
        # Fragility index: Accumulates with failures (vulnerability memory)
        self.fragility_index = self.clamp(frag + 0.1 * f_fail)
        
        # Lock-in: Commitment grows with consistency
        self.lock_in = self.clamp(lock + 0.1 * self.consistency)
        
        # Learning rate: Increases from failure (lessons), decreases from easy success
        self.learning_rate = self.clamp(lr + 0.1 * f_fail - 0.05 * f_succ)
        
        # Energy: Base drain offset by success boost
        self.energy = self.clamp(energy - 0.05 + 0.1 * f_succ)
        
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
            total_weight = 0.0
            weighted_diff = 0.0
            for other in agents:
                if other.name != agent.name:
                    w = influence[other.name][agent.name]
                    total_weight += w
                    weighted_diff += w * abs(other.reputation - agent.reputation)
            
            if total_weight > 0:
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
    n_agents = len(agents)
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
    max_centrality = 0.0
    for agent in agents:
        out_strength = sum(influence[agent.name].values())
        if out_strength > max_centrality:
            max_centrality = out_strength
    max_possible = (n_agents - 1) * 0.9  # max weight 0.9 per edge
    centralization = (max_centrality / max_possible) if max_possible > 0 else 0
    
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
            total_weight = 0.0
            weighted_diff = 0.0
            for other in agents_pert:
                if other.name != agent.name:
                    w = influence[other.name][agent.name]
                    total_weight += w
                    weighted_diff += w * abs(other.reputation - agent.reputation)
            
            if total_weight > 0:
                peer_gap = weighted_diff / total_weight
            else:
                peer_gap = 0.5
            
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
# 5. VISUALIZATION & EXPORT TOOLS
# =============================================================================

def export_to_csv(result: Dict[str, Any], filename: str = "simulation_output.csv") -> str:
    """
    Export simulation state history to CSV format.
    
    Args:
        result: Simulation result dictionary from run_simulation()
        filename: Output filename
    
    Returns:
        Path to created file
    """
    import csv
    
    state_history = result.get("state_history", [])
    if not state_history:
        raise ValueError("No state history to export")
    
    agent_names = list(state_history[0].keys())
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        header = ["round"]
        for name in agent_names:
            header.extend([f"{name}_{var}" for var in [
                "self_worth", "anxiety", "consistency", "momentum", 
                "reputation", "opportunity_access", "fragility_index",
                "lock_in", "learning_rate", "energy", "mode"
            ]])
        writer.writerow(header)
        
        # Data rows
        for round_idx, round_states in enumerate(state_history):
            row = [round_idx]
            for name in agent_names:
                state = round_states.get(name, {})
                row.extend([
                    state.get("self_worth", 0),
                    state.get("anxiety", 0),
                    state.get("consistency", 0),
                    state.get("momentum", 0),
                    state.get("reputation", 0),
                    state.get("opportunity_access", 0),
                    state.get("fragility_index", 0),
                    state.get("lock_in", 0),
                    state.get("learning_rate", 0),
                    state.get("energy", 0),
                    state.get("mode", "")
                ])
            writer.writerow(row)
    
    return filename


def export_for_visualization(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare simulation data for visualization libraries (matplotlib, plotly, etc.).
    
    Returns:
        Dictionary with time_series, agents_data, outcome_data ready for plotting
    """
    state_history = result.get("state_history", [])
    agents = result.get("agents", [])
    outcome = result.get("outcome_vector", {})
    
    # Time series data per agent
    time_series = {}
    if state_history:
        agent_names = list(state_history[0].keys())
        for name in agent_names:
            time_series[name] = {
                "rounds": list(range(len(state_history))),
                "self_worth": [s[name]["self_worth"] for s in state_history],
                "anxiety": [s[name]["anxiety"] for s in state_history],
                "momentum": [s[name]["momentum"] for s in state_history],
                "reputation": [s[name]["reputation"] for s in state_history],
                "energy": [s[name]["energy"] for s in state_history],
                "mode": [s[name]["mode"] for s in state_history]
            }
    
    # Final agent comparison data
    agents_data = []
    for agent in agents:
        agents_data.append({
            "name": agent.name,
            "self_worth": agent.self_worth,
            "anxiety": agent.anxiety,
            "momentum": agent.momentum,
            "reputation": agent.reputation,
            "mode": agent.mode,
            "cascade_active": agent.cascade_active
        })
    
    return {
        "time_series": time_series,
        "agents_data": agents_data,
        "outcome_data": outcome,
        "seed": result.get("seed", 0)
    }


# =============================================================================
# 6. ADVANCED METRICS & ANALYTICS
# =============================================================================

def compute_system_health(agents: List[CognitiveAgent]) -> Dict[str, float]:
    """
    Compute overall system health metrics.
    
    Returns:
        Dictionary with health_score, stability_index, resilience_score, risk_level
    """
    n = len(agents)
    if n == 0:
        return {"health_score": 0.0, "stability_index": 0.0, "resilience_score": 0.0, "risk_level": "UNKNOWN"}
    
    # Aggregate metrics
    avg_self_worth = sum(a.self_worth for a in agents) / n
    avg_anxiety = sum(a.anxiety for a in agents) / n
    avg_momentum = sum(a.momentum for a in agents) / n
    avg_energy = sum(a.energy for a in agents) / n
    
    # Count cascade failures
    cascade_count = sum(1 for a in agents if a.cascade_active)
    
    # Mode distribution
    mode_counts = {}
    for a in agents:
        mode_counts[a.mode] = mode_counts.get(a.mode, 0) + 1
    
    # Health score: weighted combination of positive indicators
    health_score = (
        0.3 * avg_self_worth +
        0.25 * avg_momentum +
        0.25 * avg_energy +
        0.2 * (1 - avg_anxiety)
    )
    
    # Stability index: inverse of variance in key metrics
    sw_variance = sum((a.self_worth - avg_self_worth) ** 2 for a in agents) / n
    anx_variance = sum((a.anxiety - avg_anxiety) ** 2 for a in agents) / n
    stability_index = 1.0 - min(1.0, (sw_variance + anx_variance) / 2)
    
    # Resilience score: ability to recover (high learning_rate + low fragility)
    avg_learning = sum(a.learning_rate for a in agents) / n
    avg_fragility = sum(a.fragility_index for a in agents) / n
    resilience_score = avg_learning * (1 - avg_fragility)
    
    # Risk level classification
    if cascade_count > n * 0.3 or health_score < 0.3:
        risk_level = "CRITICAL"
    elif cascade_count > 0 or health_score < 0.5:
        risk_level = "HIGH"
    elif health_score < 0.7 or avg_anxiety > 0.5:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"
    
    return {
        "health_score": round(health_score, 4),
        "stability_index": round(stability_index, 4),
        "resilience_score": round(resilience_score, 4),
        "risk_level": risk_level,
        "cascade_count": cascade_count,
        "avg_self_worth": round(avg_self_worth, 4),
        "avg_anxiety": round(avg_anxiety, 4)
    }


def compute_network_centrality(influence: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    Compute network centrality metrics for the influence graph.
    
    Returns:
        Dictionary with degree_centrality, betweenness_approx, hub_scores, authority_scores
    """
    agents = list(influence.keys())
    n = len(agents)
    
    if n == 0:
        return {"degree_centrality": {}, "betweenness_approx": {}, "hub_scores": {}, "authority_scores": {}}
    
    # Out-degree centrality (influence exerted)
    out_degree = {}
    for agent in agents:
        out_degree[agent] = sum(influence[agent].values())
    
    # In-degree centrality (influence received)
    in_degree = {}
    for agent in agents:
        in_degree[agent] = sum(influence[other][agent] for other in agents if other != agent)
    
    # Normalize
    max_possible = (n - 1) * 0.9
    degree_centrality = {
        agent: {
            "out": out_degree[agent] / max_possible if max_possible > 0 else 0,
            "in": in_degree[agent] / max_possible if max_possible > 0 else 0
        }
        for agent in agents
    }
    
    # Simplified hub scores (iterative approximation)
    hub_scores = {agent: 1.0 for agent in agents}
    authority_scores = {agent: 1.0 for agent in agents}
    
    for _ in range(10):  # Power iteration
        # Update authorities
        for agent in agents:
            authority_scores[agent] = sum(hub_scores[other] * influence[other][agent] 
                                          for other in agents if other != agent)
        
        # Update hubs
        for agent in agents:
            hub_scores[agent] = sum(authority_scores[other] * influence[agent][other] 
                                    for other in agents if other != agent)
        
        # Normalize
        max_hub = max(hub_scores.values()) or 1
        max_auth = max(authority_scores.values()) or 1
        hub_scores = {k: v / max_hub for k, v in hub_scores.items()}
        authority_scores = {k: v / max_auth for k, v in authority_scores.items()}
    
    return {
        "degree_centrality": degree_centrality,
        "hub_scores": hub_scores,
        "authority_scores": authority_scores,
        "total_edges": n * (n - 1),
        "avg_out_strength": sum(out_degree.values()) / n if n > 0 else 0
    }


def detect_trends(time_series: Dict[str, List[float]], window: int = 3) -> Dict[str, str]:
    """
    Detect trends in time series data using simple moving average.
    
    Args:
        time_series: Dictionary mapping variable names to lists of values
        window: Window size for moving average
    
    Returns:
        Dictionary mapping variable names to trend direction ("INCREASING", "DECREASING", "STABLE")
    """
    trends = {}
    
    for var_name, values in time_series.items():
        if len(values) < window + 1:
            trends[var_name] = "INSUFFICIENT_DATA"
            continue
        
        # Compare recent average to earlier average
        recent_avg = sum(values[-window:]) / window
        earlier_avg = sum(values[-2*window:-window]) / window if len(values) >= 2*window else values[0]
        
        change_pct = (recent_avg - earlier_avg) / (earlier_avg + 0.001)  # Avoid division by zero
        
        if change_pct > 0.1:
            trends[var_name] = "INCREASING"
        elif change_pct < -0.1:
            trends[var_name] = "DECREASING"
        else:
            trends[var_name] = "STABLE"
    
    return trends


# =============================================================================
# 7. SCENARIO BUILDER & PARAMETER SWEEPS
# =============================================================================

@dataclass
class ScenarioConfig:
    """Configuration for custom simulation scenarios."""
    name: str
    rounds: int = 10
    seed: int = 42
    agent_count: int = 5
    failure_rate: float = 0.10
    success_rate: float = 0.25
    mentor_rate: float = 0.05
    initial_self_worth_range: Tuple[float, float] = (0.35, 0.65)
    initial_anxiety_range: Tuple[float, float] = (0.2, 0.45)
    influence_density: float = 0.8  # Fraction of possible edges
    special_conditions: Dict[str, Any] = field(default_factory=dict)


def run_custom_scenario(config: ScenarioConfig) -> Dict[str, Any]:
    """
    Run simulation with custom scenario parameters.
    
    Args:
        config: ScenarioConfig object with custom parameters
    
    Returns:
        Simulation result dictionary with additional scenario metadata
    """
    rng = SeededRandom(config.seed)
    
    # Create agents with custom initialization
    agent_names = [f"Agent_{i}" for i in range(config.agent_count)]
    agents = []
    
    for name in agent_names:
        agent = CognitiveAgent.__new__(CognitiveAgent)
        agent.name = name
        agent.rng = rng
        
        # Custom initialization ranges
        agent.self_worth = CognitiveAgent.clamp(rng.uniform(*config.initial_self_worth_range))
        agent.anxiety = CognitiveAgent.clamp(rng.uniform(*config.initial_anxiety_range))
        agent.consistency = CognitiveAgent.clamp(0.5 + rng.uniform(-0.1, 0.1))
        agent.momentum = CognitiveAgent.clamp(0.5 + rng.uniform(-0.1, 0.1))
        agent.reputation = CognitiveAgent.clamp(0.5 + rng.uniform(-0.1, 0.1))
        agent.opportunity_access = CognitiveAgent.clamp(0.5 + rng.uniform(-0.1, 0.1))
        agent.fragility_index = CognitiveAgent.clamp(0.15 + rng.uniform(0, 0.1))
        agent.lock_in = CognitiveAgent.clamp(0.1 + rng.uniform(0, 0.1))
        agent.learning_rate = CognitiveAgent.clamp(0.15 + rng.uniform(-0.05, 0.05))
        agent.energy = CognitiveAgent.clamp(0.7 + rng.uniform(-0.1, 0.15))
        
        agent.mode = "EXECUTE"
        agent.cascade_active = False
        agent.success_streak = 0
        agent.failure_streak = 0
        agent.intent_target = None
        agent.emotional_anchor = None
        agent.history = []
        
        agents.append(agent)
    
    # Build influence matrix with custom density
    influence = {}
    for i, a1 in enumerate(agents):
        influence[a1.name] = {}
        for j, a2 in enumerate(agents):
            if i != j and rng.random() < config.influence_density:
                influence[a1.name][a2.name] = rng.uniform(0.1, 0.9)
            else:
                influence[a1.name][a2.name] = 0.0
    
    # Run simulation with custom rates
    state_history = []
    
    for round_num in range(config.rounds):
        round_states = {}
        
        for agent in agents:
            # Compute peer gap
            total_weight = 0.0
            weighted_diff = 0.0
            for other in agents:
                if other.name != agent.name:
                    w = influence[other.name][agent.name]
                    total_weight += w
                    weighted_diff += w * abs(other.reputation - agent.reputation)
            
            peer_gap = weighted_diff / total_weight if total_weight > 0 else 0.5
            
            # Generate events with custom rates
            progress = rng.uniform(0.3, 0.8)
            social_feedback = rng.uniform(-0.3, 0.3)
            failure_flag = rng.random() < config.failure_rate
            success_flag = rng.random() < config.success_rate
            mentor_flag = rng.random() < config.mentor_rate
            
            # Apply special conditions
            if config.special_conditions.get("high_pressure"):
                agent.anxiety = CognitiveAgent.clamp(agent.anxiety + 0.1)
            if config.special_conditions.get("supportive_environment"):
                mentor_flag = mentor_flag or rng.random() < 0.15
            
            agent.update(progress, peer_gap, social_feedback, failure_flag, success_flag, mentor_flag)
            round_states[agent.name] = agent.get_current_state_dict()
        
        state_history.append(round_states)
    
    # Compute outcomes
    n_agents = len(agents)
    rep_values = [a.reputation for a in agents]
    opp_values = [a.opportunity_access for a in agents]
    trust_values = [a.lock_in for a in agents]
    
    outcome_vector = {
        "reputation_mean": sum(rep_values) / n_agents,
        "inequality": sum((x - sum(opp_values)/n_agents) ** 2 for x in opp_values) / n_agents,
        "trust_proxy": sum(trust_values) / n_agents,
        "centralization": max(sum(influence[a.name].values()) for a in agents) / ((n_agents - 1) * 0.9)
    }
    
    return {
        "state_history": state_history,
        "outcome_vector": outcome_vector,
        "agents": agents,
        "influence": influence,
        "seed": config.seed,
        "scenario_name": config.name,
        "scenario_config": {
            "rounds": config.rounds,
            "agent_count": config.agent_count,
            "failure_rate": config.failure_rate,
            "success_rate": config.success_rate,
            "mentor_rate": config.mentor_rate
        }
    }


def run_parameter_sweep(param_name: str, param_values: List[Any], 
                        base_config: ScenarioConfig) -> Dict[str, Any]:
    """
    Run multiple simulations sweeping one parameter.
    
    Args:
        param_name: Name of parameter to sweep
        param_values: List of values to try
        base_config: Base scenario configuration
    
    Returns:
        Dictionary with results per parameter value and optimal value
    """
    results = {}
    
    for value in param_values:
        config = deepcopy(base_config)
        setattr(config, param_name, value)
        config.seed = base_config.seed + hash(str(value)) % 10000
        
        try:
            result = run_custom_scenario(config)
            results[str(value)] = {
                "outcome": result["outcome_vector"],
                "health": compute_system_health(result["agents"]),
                "full_result": result
            }
        except Exception as e:
            results[str(value)] = {"error": str(e)}
    
    # Find optimal value based on health score
    best_value = None
    best_health = -1
    
    for value_str, data in results.items():
        if "health" in data:
            health_score = data["health"].get("health_score", 0)
            if health_score > best_health:
                best_health = health_score
                best_value = value_str
    
    return {
        "parameter": param_name,
        "values_tested": param_values,
        "results": results,
        "optimal_value": best_value,
        "optimal_health_score": best_health
    }


# =============================================================================
# 8. SENSITIVITY ANALYSIS
# =============================================================================

def sensitivity_analysis(agent_names: List[str], rounds: int = 10, 
                         base_seed: int = 42, num_samples: int = 20) -> Dict[str, Any]:
    """
    Perform sensitivity analysis on all initial agent parameters.
    
    Tests how much each initial parameter affects final outcomes.
    
    Returns:
        Dictionary with sensitivity_scores, ranked_parameters, recommendations
    """
    base_result = run_simulation(agent_names, rounds, base_seed)
    base_outcome = base_result["outcome_vector"]
    
    sensitivity_scores = {}
    
    # Parameters to test
    params_to_test = [
        "self_worth", "anxiety", "consistency", "momentum",
        "reputation", "opportunity_access", "fragility_index",
        "lock_in", "learning_rate", "energy"
    ]
    
    for param in params_to_test:
        perturbations = []
        
        for i in range(num_samples):
            # Random perturbation ±20%
            delta = (i - num_samples/2) / (num_samples/2) * 0.2
            cf_result = run_counterfactual(agent_names, rounds, base_seed, param, delta * 100)
            
            # Measure impact on reputation_mean
            impact = abs(cf_result["delta"]["reputation_mean"])
            perturbations.append(impact)
        
        # Average sensitivity
        avg_sensitivity = sum(perturbations) / len(perturbations) if perturbations else 0
        max_sensitivity = max(perturbations) if perturbations else 0
        
        sensitivity_scores[param] = {
            "average_impact": round(avg_sensitivity, 4),
            "max_impact": round(max_sensitivity, 4),
            "std_impact": round((sum((x - avg_sensitivity)**2 for x in perturbations) / len(perturbations))**0.5, 4) if perturbations else 0
        }
    
    # Rank parameters by sensitivity
    ranked = sorted(sensitivity_scores.items(), 
                   key=lambda x: x[1]["average_impact"], reverse=True)
    
    # Generate recommendations
    recommendations = []
    if ranked:
        most_sensitive = ranked[0][0]
        least_sensitive = ranked[-1][0]
        recommendations.append(f"Highest leverage parameter: {most_sensitive}")
        recommendations.append(f"Most robust parameter: {least_sensitive}")
        recommendations.append("Focus interventions on high-sensitivity parameters for maximum impact")
    
    return {
        "sensitivity_scores": sensitivity_scores,
        "ranked_parameters": ranked,
        "recommendations": recommendations,
        "base_outcome": base_outcome
    }


# =============================================================================
# 9. SAVE/LOAD SIMULATION STATE
# =============================================================================

def save_simulation(result: Dict[str, Any], filename: str = "simulation_state.json") -> str:
    """
    Save simulation state to JSON file for later analysis or continuation.
    
    Args:
        result: Simulation result dictionary
        filename: Output filename
    
    Returns:
        Path to saved file
    """
    import json
    
    # Convert agents to serializable format
    agents_data = []
    for agent in result.get("agents", []):
        agents_data.append({
            "name": agent.name,
            "self_worth": agent.self_worth,
            "anxiety": agent.anxiety,
            "consistency": agent.consistency,
            "momentum": agent.momentum,
            "reputation": agent.reputation,
            "opportunity_access": agent.opportunity_access,
            "fragility_index": agent.fragility_index,
            "lock_in": agent.lock_in,
            "learning_rate": agent.learning_rate,
            "energy": agent.energy,
            "mode": agent.mode,
            "cascade_active": agent.cascade_active,
            "success_streak": agent.success_streak,
            "failure_streak": agent.failure_streak
        })
    
    save_data = {
        "state_history": result.get("state_history", []),
        "outcome_vector": result.get("outcome_vector", {}),
        "agents": agents_data,
        "influence": result.get("influence", {}),
        "seed": result.get("seed", 0),
        "metadata": {
            "saved_at": "manual",
            "version": "2.0"
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(save_data, f, indent=2)
    
    return filename


def load_simulation(filename: str) -> Dict[str, Any]:
    """
    Load simulation state from JSON file.
    
    Args:
        filename: Path to saved simulation file
    
    Returns:
        Simulation result dictionary (agents as dicts, not objects)
    """
    import json
    
    with open(filename, 'r') as f:
        loaded_data = json.load(f)
    
    return loaded_data


def resume_simulation(loaded_data: Dict[str, Any], additional_rounds: int = 5) -> Dict[str, Any]:
    """
    Resume a saved simulation for additional rounds.
    
    Note: This recreates agent objects and continues from their saved state.
    Exact determinism may vary due to RNG state not being fully preserved.
    
    Args:
        loaded_data: Data from load_simulation()
        additional_rounds: Number of additional rounds to run
    
    Returns:
        Extended simulation result
    """
    agents_data = loaded_data.get("agents", [])
    influence = loaded_data.get("influence", {})
    seed = loaded_data.get("seed", 42)
    
    # Recreate agents with saved states
    rng = SeededRandom(seed + 99999)  # Different seed for continuation
    agents = []
    
    for data in agents_data:
        agent = CognitiveAgent.__new__(CognitiveAgent)
        agent.name = data["name"]
        agent.rng = rng
        
        agent.self_worth = data["self_worth"]
        agent.anxiety = data["anxiety"]
        agent.consistency = data["consistency"]
        agent.momentum = data["momentum"]
        agent.reputation = data["reputation"]
        agent.opportunity_access = data["opportunity_access"]
        agent.fragility_index = data["fragility_index"]
        agent.lock_in = data["lock_in"]
        agent.learning_rate = data["learning_rate"]
        agent.energy = data["energy"]
        agent.mode = data["mode"]
        agent.cascade_active = data["cascade_active"]
        agent.success_streak = data["success_streak"]
        agent.failure_streak = data["failure_streak"]
        agent.intent_target = None
        agent.emotional_anchor = None
        agent.history = []
        
        agents.append(agent)
    
    # Continue simulation
    agent_list = agents
    state_history = list(loaded_data.get("state_history", []))
    
    for round_num in range(additional_rounds):
        round_states = {}
        
        for agent in agent_list:
            total_weight = 0.0
            weighted_diff = 0.0
            for other in agent_list:
                if other.name != agent.name:
                    w = influence[other.name][agent.name]
                    total_weight += w
                    weighted_diff += w * abs(other.reputation - agent.reputation)
            
            peer_gap = weighted_diff / total_weight if total_weight > 0 else 0.5
            
            progress = rng.uniform(0.3, 0.8)
            social_feedback = rng.uniform(-0.3, 0.3)
            failure_flag = rng.random() < 0.10
            success_flag = rng.random() < 0.25
            mentor_flag = rng.random() < 0.05
            
            agent.update(progress, peer_gap, social_feedback, failure_flag, success_flag, mentor_flag)
            round_states[agent.name] = agent.get_current_state_dict()
        
        state_history.append(round_states)
    
    # Recompute outcomes
    n_agents = len(agent_list)
    rep_values = [a.reputation for a in agent_list]
    opp_values = [a.opportunity_access for a in agent_list]
    trust_values = [a.lock_in for a in agent_list]
    
    outcome_vector = {
        "reputation_mean": sum(rep_values) / n_agents,
        "inequality": sum((x - sum(opp_values)/n_agents) ** 2 for x in opp_values) / n_agents,
        "trust_proxy": sum(trust_values) / n_agents,
        "centralization": max(sum(influence[a.name].values()) for a in agent_list) / ((n_agents - 1) * 0.9)
    }
    
    return {
        "state_history": state_history,
        "outcome_vector": outcome_vector,
        "agents": agent_list,
        "influence": influence,
        "seed": seed,
        "resumed": True,
        "additional_rounds": additional_rounds
    }


# =============================================================================
# 10. BATCH PROCESSING & COMPARATIVE ANALYSIS
# =============================================================================

def batch_compare_scenarios(scenario_configs: List[ScenarioConfig]) -> Dict[str, Any]:
    """
    Run and compare multiple scenarios side-by-side.
    
    Args:
        scenario_configs: List of ScenarioConfig objects
    
    Returns:
        Comparative analysis with rankings and insights
    """
    results = []
    
    for config in scenario_configs:
        result = run_custom_scenario(config)
        health = compute_system_health(result["agents"])
        
        results.append({
            "scenario_name": config.name,
            "config": {
                "rounds": config.rounds,
                "agent_count": config.agent_count,
                "failure_rate": config.failure_rate,
                "success_rate": config.success_rate,
                "mentor_rate": config.mentor_rate
            },
            "outcome": result["outcome_vector"],
            "health": health,
            "black_swan": detect_black_swan(result["agents"], result["state_history"]),
            "full_result": result
        })
    
    # Rank by health score
    ranked_by_health = sorted(results, 
                             key=lambda x: x["health"]["health_score"], 
                             reverse=True)
    
    # Rank by reputation
    ranked_by_reputation = sorted(results,
                                  key=lambda x: x["outcome"]["reputation_mean"],
                                  reverse=True)
    
    # Rank by stability
    ranked_by_stability = sorted(results,
                                 key=lambda x: x["health"]["stability_index"],
                                 reverse=True)
    
    # Generate comparative insights
    insights = []
    if len(results) >= 2:
        best_health = ranked_by_health[0]
        worst_health = ranked_by_health[-1]
        
        insights.append(f"Best scenario: {best_health['scenario_name']} (health: {best_health['health']['health_score']:.3f})")
        insights.append(f"Worst scenario: {worst_health['scenario_name']} (health: {worst_health['health']['health_score']:.3f})")
        
        # Identify key differentiators
        if best_health["config"]["mentor_rate"] > worst_health["config"]["mentor_rate"]:
            insights.append("Higher mentorship rate correlates with better outcomes")
        if best_health["config"]["failure_rate"] < worst_health["config"]["failure_rate"]:
            insights.append("Lower failure rate improves system health")
    
    return {
        "scenarios_tested": len(results),
        "results": results,
        "rankings": {
            "by_health": [r["scenario_name"] for r in ranked_by_health],
            "by_reputation": [r["scenario_name"] for r in ranked_by_reputation],
            "by_stability": [r["scenario_name"] for r in ranked_by_stability]
        },
        "insights": insights,
        "best_overall": ranked_by_health[0]["scenario_name"] if results else None
    }


# =============================================================================
# 11. FORECASTING & PREDICTION
# =============================================================================

def forecast_trajectory(result: Dict[str, Any], forecast_rounds: int = 5) -> Dict[str, Any]:
    """
    Forecast agent trajectories based on current trends.
    
    Uses linear extrapolation from recent history.
    
    Args:
        result: Simulation result
        forecast_rounds: Number of rounds to forecast
    
    Returns:
        Dictionary with forecasts per agent and confidence intervals
    """
    state_history = result.get("state_history", [])
    agents = result.get("agents", [])
    
    if len(state_history) < 3:
        return {"error": "Insufficient history for forecasting", "forecast_rounds": forecast_rounds}
    
    forecasts = {}
    
    for agent in agents:
        # Get last 3 rounds of data
        recent_states = state_history[-3:]
        
        forecast_data = {
            "current_state": agent.get_current_state_dict(),
            "projections": []
        }
        
        # Simple linear extrapolation for key variables
        for var in ["self_worth", "anxiety", "momentum", "reputation", "energy"]:
            values = [s[agent.name][var] for s in recent_states]
            
            # Calculate trend
            if len(values) >= 2:
                trend = (values[-1] - values[0]) / (len(values) - 1)
            else:
                trend = 0
            
            # Project forward
            projections = []
            for i in range(1, forecast_rounds + 1):
                projected = values[-1] + trend * i
                projected = max(0.0, min(1.0, projected))  # Clamp
                projections.append(round(projected, 4))
            
            forecast_data[f"{var}_trend"] = round(trend, 4)
            forecast_data[f"{var}_forecast"] = projections
        
        # Predict mode based on projected values
        final_sw = forecast_data["self_worth_forecast"][-1] if forecast_data["self_worth_forecast"] else agent.self_worth
        final_anx = forecast_data["anxiety_forecast"][-1] if forecast_data["anxiety_forecast"] else agent.anxiety
        
        if final_anx > 0.6 and final_sw < 0.4:
            predicted_mode = "AVOID"
        elif final_sw > 0.5 and forecast_data.get("momentum_trend", 0) > 0:
            predicted_mode = "EXECUTE"
        else:
            predicted_mode = "OPTIMIZE"
        
        forecast_data["predicted_mode"] = predicted_mode
        
        forecasts[agent.name] = forecast_data
    
    return {
        "forecasts": forecasts,
        "forecast_horizon": forecast_rounds,
        "method": "linear_extrapolation",
        "confidence": "low" if len(state_history) < 5 else "medium" if len(state_history) < 10 else "high"
    }


# =============================================================================
# END OF NYX KERNEL
# =============================================================================
