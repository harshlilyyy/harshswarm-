# =============================================================================
# SIMULATION ENGINE — Main Execution Loop
# =============================================================================
"""
The Simulation Engine orchestrates the complete simulation:
- Agent initialization and lifecycle
- Event processing
- Parallel execution support
- Checkpointing and restoration
- Metrics collection
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from ..core.seeded_random import SeededRandom
from ..world.world_model import WorldModel, WorldEntity, EntityType
from ..agents.cognitive_agent import CognitiveAgent, AgentMode
from ..agents.agent_profile import AgentProfile
from .scheduler import SimulationScheduler, SimulationEvent, EventType


@dataclass
class SimulationConfig:
    """Configuration for simulation run."""
    # Basic settings
    seed: int = 42
    num_agents: int = 100
    duration_hours: float = 24.0
    time_step_minutes: float = 15.0
    
    # Execution settings
    parallel: bool = True
    max_workers: int = 4
    checkpoint_interval_steps: int = 10
    
    # Behavior settings
    interaction_probability: float = 0.3
    event_injection_rate: float = 0.1
    
    # Output settings
    collect_metrics: bool = True
    metrics_interval_steps: int = 5
    verbose: bool = False


@dataclass
class SimulationResult:
    """Results from a completed simulation."""
    config: SimulationConfig
    start_time: datetime
    end_time: datetime
    final_world_state: Dict[str, Any]
    agent_states: Dict[str, Dict[str, Any]]
    metrics_history: List[Dict[str, Any]]
    events_log: List[Dict[str, Any]]
    checkpoints: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to dictionary."""
        return {
            "config": {
                "seed": self.config.seed,
                "num_agents": self.config.num_agents,
                "duration_hours": self.config.duration_hours,
            },
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "final_world_state": self.final_world_state,
            "agent_count": len(self.agent_states),
            "metrics_snapshots": len(self.metrics_history),
            "events_logged": len(self.events_log),
            "checkpoints": len(self.checkpoints),
            "statistics": self.statistics
        }


class SimulationEngine:
    """
    Main simulation execution engine.
    
    Orchestrates:
    - World model initialization
    - Agent population generation
    - Event scheduling and execution
    - Parallel agent updates
    - Metrics collection
    - Checkpointing
    
    Usage:
        config = SimulationConfig(num_agents=500, seed=42)
        engine = SimulationEngine(config)
        engine.initialize()
        result = engine.run()
    """
    
    def __init__(self, config: SimulationConfig):
        """
        Initialize simulation engine.
        
        Args:
            config: Simulation configuration
        """
        self.config = config
        self.rng = SeededRandom(config.seed)
        
        # Core components
        self.world: Optional[WorldModel] = None
        self.scheduler: Optional[SimulationScheduler] = None
        self.agents: Dict[str, CognitiveAgent] = {}
        
        # State tracking
        self.initialized = False
        self.running = False
        self.paused = False
        
        # Data collection
        self.metrics_history: List[Dict[str, Any]] = []
        self.events_log: List[Dict[str, Any]] = []
        self.checkpoints: List[Dict[str, Any]] = []
        
        # Threading
        self._lock = threading.Lock()
        self._executor: Optional[ThreadPoolExecutor] = None
    
    def initialize(self, world: Optional[WorldModel] = None):
        """
        Initialize simulation components.
        
        Args:
            world: Optional pre-built world model
        """
        # Create or use provided world model
        self.world = world or WorldModel("Simulation World")
        self.world.global_state["simulation_start"] = datetime.now()
        
        # Initialize scheduler
        self.scheduler = SimulationScheduler(
            start_time=self.world.global_state["current_datetime"]
        )
        
        # Generate agents
        self._generate_agents()
        
        # Schedule initial events
        self._schedule_initial_events()
        
        self.initialized = True
    
    def _generate_agents(self):
        """Generate agent population based on config."""
        for i in range(self.config.num_agents):
            # Create profile with some variation
            profile = self._create_agent_profile(i)
            
            # Create cognitive agent
            agent_rng = self.rng.fork(offset_seed=i)
            agent = CognitiveAgent(profile, agent_rng)
            
            # Add to world
            entity = self.world.create_entity(
                name=profile.name,
                entity_type=EntityType.AGENT,
                attributes={
                    "agent_id": profile.id,
                    "age": profile.age,
                    "location": profile.location,
                    "occupation": profile.occupation
                }
            )
            
            # Store agent
            self.agents[profile.id] = agent
            
            # Link agent to world entity
            entity.attributes["cognitive_agent"] = profile.id
    
    def _create_agent_profile(self, index: int) -> AgentProfile:
        """Create a single agent profile."""
        from ..agents.agent_profile import EducationLevel, EmploymentStatus, BigFive, SchwartzValues
        
        # Generate varied but realistic demographics
        ages = [18, 25, 35, 45, 55, 65]
        age = self.rng.choice(ages) + self.rng.randint(-3, 3)
        age = max(18, min(80, age))
        
        locations = ["Urban", "Suburban", "Rural"]
        location = self.rng.choice(locations)
        
        occupations = [
            "Software Engineer", "Teacher", "Nurse", "Manager",
            "Student", "Retired", "Artist", "Consultant"
        ]
        occupation = self.rng.choice(occupations)
        
        # Generate personality traits with normal distribution
        big_five = BigFive(
            openness=self.rng.truncated_normal(0.5, 0.15, 0.1, 0.9),
            conscientiousness=self.rng.truncated_normal(0.5, 0.15, 0.1, 0.9),
            extraversion=self.rng.truncated_normal(0.5, 0.15, 0.1, 0.9),
            agreeableness=self.rng.truncated_normal(0.5, 0.15, 0.1, 0.9),
            neuroticism=self.rng.truncated_normal(0.5, 0.15, 0.1, 0.9)
        )
        
        # Generate values
        schwartz = SchwartzValues(
            self_direction=self.rng.uniform(0.3, 0.8),
            stimulation=self.rng.uniform(0.3, 0.7),
            hedonism=self.rng.uniform(0.3, 0.7),
            achievement=self.rng.uniform(0.3, 0.8),
            power=self.rng.uniform(0.2, 0.6),
            security=self.rng.uniform(0.4, 0.8),
            conformity=self.rng.uniform(0.3, 0.7),
            tradition=self.rng.uniform(0.3, 0.7),
            benevolence=self.rng.uniform(0.4, 0.8),
            universalism=self.rng.uniform(0.3, 0.7)
        )
        
        # Generate political leaning (normal distribution around center)
        political = self.rng.truncated_normal(0.0, 0.3, -0.9, 0.9)
        
        return AgentProfile(
            id=f"agent_{index:05d}",
            name=f"Agent {index}",
            age=age,
            location=location,
            occupation=occupation,
            big_five=big_five,
            schwartz_values=schwartz,
            political_leaning=political,
            core_beliefs=self._generate_core_beliefs(big_five, schwartz, political),
            short_term_goals=["Complete current project", "Maintain social connections"],
            long_term_goals=["Career advancement", "Financial stability"]
        )
    
    def _generate_core_beliefs(self, big_five, schwartz, political) -> List[str]:
        """Generate core beliefs based on personality."""
        beliefs = []
        
        # Openness influences curiosity beliefs
        if big_five.openness > 0.6:
            beliefs.append("New experiences are valuable")
        else:
            beliefs.append("Tradition provides stability")
        
        # Conscientiousness influences work ethic
        if big_five.conscientiousness > 0.6:
            beliefs.append("Hard work leads to success")
        
        # Agreeableness influences social beliefs
        if big_five.agreeableness > 0.6:
            beliefs.append("Cooperation benefits everyone")
        else:
            beliefs.append("Competition drives progress")
        
        # Political leaning influences policy beliefs
        if political < -0.3:
            beliefs.append("Government should provide social safety nets")
        elif political > 0.3:
            beliefs.append("Individual responsibility is paramount")
        
        return beliefs
    
    def _schedule_initial_events(self):
        """Schedule initial simulation events."""
        step_delta = timedelta(minutes=self.config.time_step_minutes)
        
        # Schedule agent update events
        for agent_id in list(self.agents.keys())[:10]:  # First batch
            self.scheduler.schedule(
                handler=self._update_agent,
                delay=step_delta,
                event_type=EventType.AGENT_UPDATE,
                args=(agent_id,),
                metadata={"agent_id": agent_id}
            )
        
        # Schedule checkpoint events
        if self.config.checkpoint_interval_steps > 0:
            checkpoint_delta = step_delta * self.config.checkpoint_interval_steps
            self.scheduler.schedule(
                handler=self._checkpoint,
                delay=checkpoint_delta,
                event_type=EventType.CHECKPOINT,
                recurring=True,
                recurrence_interval=checkpoint_delta
            )
        
        # Schedule metrics collection
        if self.config.collect_metrics:
            metrics_delta = step_delta * self.config.metrics_interval_steps
            self.scheduler.schedule(
                handler=self._collect_metrics,
                delay=metrics_delta,
                event_type=EventType.METRICS_COLLECTION,
                recurring=True,
                recurrence_interval=metrics_delta
            )
    
    def _update_agent(self, agent_id: str):
        """Update a single agent's state."""
        if agent_id not in self.agents:
            return
        
        agent = self.agents[agent_id]
        
        # Generate round events
        progress = self.rng.uniform(0.3, 0.8)
        peer_gap = self.rng.uniform(0, 0.5)
        social_feedback = self.rng.uniform(-0.3, 0.3)
        failure_flag = self.rng.random() < 0.10
        success_flag = self.rng.random() < 0.25
        mentor_flag = self.rng.random() < 0.05
        
        # Update agent
        agent.update(
            progress=progress,
            peer_gap=peer_gap,
            social_feedback=social_feedback,
            failure_flag=failure_flag,
            success_flag=success_flag,
            mentor_flag=mentor_flag,
            current_time=self.scheduler.current_time
        )
        
        # Log event
        if self.config.verbose:
            self.events_log.append({
                "time": self.scheduler.current_time.isoformat(),
                "type": "agent_update",
                "agent_id": agent_id,
                "mode": agent.state.mode.name,
                "success": success_flag,
                "failure": failure_flag
            })
        
        # Schedule next update for this agent
        step_delta = timedelta(minutes=self.config.time_step_minutes)
        self.scheduler.schedule(
            handler=self._update_agent,
            delay=step_delta,
            event_type=EventType.AGENT_UPDATE,
            args=(agent_id,)
        )
        
        # Possibly schedule interactions
        if self.rng.random() < self.config.interaction_probability:
            self._schedule_interaction(agent_id)
    
    def _schedule_interaction(self, agent_id: str):
        """Schedule an interaction between agents."""
        if len(self.agents) < 2:
            return
        
        # Pick random other agent
        other_id = self.rng.choice([aid for aid in self.agents.keys() if aid != agent_id])
        
        self.scheduler.schedule(
            handler=self._agent_interaction,
            delay=timedelta(minutes=self.config.time_step_minutes / 2),
            event_type=EventType.AGENT_INTERACTION,
            args=(agent_id, other_id)
        )
    
    def _agent_interaction(self, agent1_id: str, agent2_id: str):
        """Process interaction between two agents."""
        if agent1_id not in self.agents or agent2_id not in self.agents:
            return
        
        agent1 = self.agents[agent1_id]
        agent2 = self.agents[agent2_id]
        
        # Simple trust-based interaction
        existing_trust = agent1.trust_network.get(agent2_id, 0.5)
        
        # Interaction outcome based on both agents' states
        compatibility = (
            (1 - abs(agent1.state.anxiety - agent2.state.anxiety)) *
            (1 - abs(agent1.state.self_worth - agent2.state.self_worth))
        )
        
        new_trust = existing_trust + (compatibility - 0.5) * 0.2
        agent1.establish_trust(agent2_id, new_trust)
        
        if self.config.verbose:
            self.events_log.append({
                "time": self.scheduler.current_time.isoformat(),
                "type": "interaction",
                "agent1": agent1_id,
                "agent2": agent2_id,
                "trust_change": new_trust - existing_trust
            })
    
    def _checkpoint(self):
        """Save simulation checkpoint."""
        checkpoint = self.world.save_checkpoint()
        self.checkpoints.append({
            "time": checkpoint.timestamp.isoformat(),
            "checksum": checkpoint.checksum,
            "entity_count": len(checkpoint.entities)
        })
        
        if self.config.verbose:
            print(f"Checkpoint saved at {checkpoint.timestamp}")
    
    def _collect_metrics(self):
        """Collect simulation metrics."""
        if not self.config.collect_metrics:
            return
        
        # Aggregate agent states
        modes = {}
        anxieties = []
        self_worths = []
        
        for agent in self.agents.values():
            mode = agent.state.mode.name
            modes[mode] = modes.get(mode, 0) + 1
            anxieties.append(agent.state.anxiety)
            self_worths.append(agent.state.self_worth)
        
        metrics = {
            "time": self.scheduler.current_time.isoformat(),
            "time_step": self.world.global_state.get("time_step", 0),
            "agent_modes": modes,
            "avg_anxiety": sum(anxieties) / len(anxieties) if anxieties else 0,
            "avg_self_worth": sum(self_worths) / len(self_worths) if self_worths else 0,
            "anxiety_std": self._std(anxieties),
            "self_worth_std": self._std(self_worths),
            "cascade_count": sum(1 for a in self.agents.values() if a.state.cascade_active)
        }
        
        self.metrics_history.append(metrics)
    
    def _std(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def run(self, blocking: bool = True) -> SimulationResult:
        """
        Run the simulation.
        
        Args:
            blocking: If True, run to completion; if False, return immediately
        
        Returns:
            SimulationResult (only if blocking=True)
        """
        if not self.initialized:
            raise RuntimeError("Simulation not initialized. Call initialize() first.")
        
        self.running = True
        self.paused = False
        
        # Calculate end time
        duration = timedelta(hours=self.config.duration_hours)
        end_time = self.scheduler.start_time + duration
        
        if self.config.parallel and self.config.max_workers > 1:
            self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        
        try:
            # Run simulation
            self.scheduler.run_until(end_time)
        finally:
            if self._executor:
                self._executor.shutdown(wait=True)
        
        self.running = False
        
        # Compile results
        return self._compile_results()
    
    def _compile_results(self) -> SimulationResult:
        """Compile simulation results."""
        # Collect final agent states
        agent_states = {
            aid: agent.get_current_state_dict()
            for aid, agent in self.agents.items()
        }
        
        # Calculate statistics
        total_updates = sum(len(a.state_history) for a in self.agents.values())
        cascade_agents = sum(1 for a in self.agents.values() if a.state.cascade_active)
        
        statistics = {
            "total_agent_updates": total_updates,
            "events_processed": self.scheduler.events_processed,
            "events_scheduled": self.scheduler.events_scheduled,
            "checkpoints_saved": len(self.checkpoints),
            "metrics_collected": len(self.metrics_history),
            "agents_in_cascade": cascade_agents,
            "cascade_rate": cascade_agents / len(self.agents) if self.agents else 0
        }
        
        return SimulationResult(
            config=self.config,
            start_time=self.scheduler.start_time,
            end_time=self.scheduler.current_time,
            final_world_state=self.world.get_state_snapshot(),
            agent_states=agent_states,
            metrics_history=self.metrics_history,
            events_log=self.events_log,
            checkpoints=self.checkpoints,
            statistics=statistics
        )
    
    def pause(self):
        """Pause simulation."""
        self.paused = True
    
    def resume(self):
        """Resume simulation."""
        self.paused = False
    
    def inject_event(self, event_data: Dict[str, Any]):
        """
        Inject a custom event into the simulation.
        
        Args:
            event_data: Event dictionary with targets, effects, etc.
        """
        self.world.add_event(event_data)
        affected = self.world.propagate_event_effects(event_data)
        
        self.events_log.append({
            "time": self.scheduler.current_time.isoformat(),
            "type": "injected_event",
            "event": event_data,
            "affected_agents": affected
        })
