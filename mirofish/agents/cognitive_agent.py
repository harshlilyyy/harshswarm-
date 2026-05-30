# =============================================================================
# COGNITIVE AGENT — Full Psychological State Machine
# =============================================================================
"""
A cognitive agent with:
- Dynamic psychological state (10+ variables)
- Multi-component memory system
- Decision-making based on personality, values, and current state
- Natural language communication capability
- Social influence and relationship tracking
- Resource management (time, energy, attention, money)
- Mode-based behavior (EXECUTE, AVOID, RECOVER, OPTIMIZE, SPIKE)

Agents are fully deterministic given the same seed and inputs.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple, Set
import math

from ..core.seeded_random import SeededRandom
from ..core.memory_system import MemorySystem, MemoryType, MemoryEntry
from .agent_profile import AgentProfile, BigFive, SchwartzValues


class AgentMode(Enum):
    """
    Behavioral modes that determine agent decision-making style.
    
    Modes are determined by the interaction of anxiety, self-worth,
    momentum, and energy levels.
    """
    EXECUTE = auto()    # High confidence, high momentum - taking action
    OPTIMIZE = auto()   # Steady state - incremental improvement
    AVOID = auto()      # High anxiety, low self-worth - withdrawal
    RECOVER = auto()    # Cascade failure active - recovery mode
    SPIKE = auto()      # High arousal performance - stress + confidence


@dataclass
class AgentState:
    """
    Snapshot of agent's dynamic psychological state at a point in time.
    
    All variables are normalized to [0, 1] range unless otherwise noted.
    """
    # Core self-evaluation
    self_worth: float = 0.5
    anxiety: float = 0.3
    confidence: float = 0.5
    
    # Behavioral dynamics
    consistency: float = 0.5
    momentum: float = 0.5
    energy: float = 0.7
    
    # Social dimensions
    reputation: float = 0.5
    trust_in_others: float = 0.5
    social_connectedness: float = 0.5
    
    # Vulnerability factors
    fragility_index: float = 0.15
    lock_in: float = 0.1
    cognitive_load: float = 0.3
    
    # Learning & adaptation
    learning_rate: float = 0.15
    openness_to_change: float = 0.5
    
    # State tracking
    mode: AgentMode = AgentMode.OPTIMIZE
    cascade_active: bool = False
    success_streak: int = 0
    failure_streak: int = 0
    
    # Current focus
    active_goal: Optional[str] = None
    emotional_state: str = "neutral"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "self_worth": self.self_worth,
            "anxiety": self.anxiety,
            "confidence": self.confidence,
            "consistency": self.consistency,
            "momentum": self.momentum,
            "energy": self.energy,
            "reputation": self.reputation,
            "trust_in_others": self.trust_in_others,
            "social_connectedness": self.social_connectedness,
            "fragility_index": self.fragility_index,
            "lock_in": self.lock_in,
            "cognitive_load": self.cognitive_load,
            "learning_rate": self.learning_rate,
            "openness_to_change": self.openness_to_change,
            "mode": self.mode.name,
            "cascade_active": self.cascade_active,
            "success_streak": self.success_streak,
            "failure_streak": self.failure_streak,
            "active_goal": self.active_goal,
            "emotional_state": self.emotional_state
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentState':
        """Create AgentState from dictionary."""
        mode_str = data.get('mode', 'OPTIMIZE')
        mode = AgentMode[mode_str] if mode_str in AgentMode.__members__ else AgentMode.OPTIMIZE
        
        return cls(
            self_worth=data.get('self_worth', 0.5),
            anxiety=data.get('anxiety', 0.3),
            confidence=data.get('confidence', 0.5),
            consistency=data.get('consistency', 0.5),
            momentum=data.get('momentum', 0.5),
            energy=data.get('energy', 0.7),
            reputation=data.get('reputation', 0.5),
            trust_in_others=data.get('trust_in_others', 0.5),
            social_connectedness=data.get('social_connectedness', 0.5),
            fragility_index=data.get('fragility_index', 0.15),
            lock_in=data.get('lock_in', 0.1),
            cognitive_load=data.get('cognitive_load', 0.3),
            learning_rate=data.get('learning_rate', 0.15),
            openness_to_change=data.get('openness_to_change', 0.5),
            mode=mode,
            cascade_active=data.get('cascade_active', False),
            success_streak=data.get('success_streak', 0),
            failure_streak=data.get('failure_streak', 0),
            active_goal=data.get('active_goal'),
            emotional_state=data.get('emotional_state', 'neutral')
        )


class CognitiveAgent:
    """
    A fully-featured cognitive agent for swarm intelligence simulation.
    
    Combines:
    - Static profile (demographics, personality, values)
    - Dynamic state (mood, energy, momentum, etc.)
    - Memory system (episodic, semantic, working, reflective, emotional)
    - Decision-making logic
    - Communication capabilities
    - Social network integration
    
    All randomness is controlled via SeededRandom for reproducibility.
    """
    
    def __init__(self, profile: AgentProfile, rng: SeededRandom,
                 initial_state: Optional[AgentState] = None):
        """
        Initialize a cognitive agent.
        
        Args:
            profile: Static demographic and psychological profile
            rng: Seeded random number generator
            initial_state: Optional initial dynamic state
        """
        self.profile = profile
        self.rng = rng
        self.state = initial_state or self._create_initial_state()
        self.memory = MemorySystem()
        
        # Social network
        self.trust_network: Dict[str, float] = {}  # agent_id -> trust level
        self.influence_received: Dict[str, float] = {}  # agent_id -> influence weight
        self.influence_exerted: Dict[str, float] = {}  # agent_id -> influence weight
        
        # Communication history
        self.message_history: List[Dict[str, Any]] = []
        self.relationship_history: List[Dict[str, Any]] = []
        
        # State history for analysis
        self.state_history: List[Tuple[datetime, AgentState]] = []
        
        # Resources (dynamic)
        self.current_time_budget = profile.time_budget
        self.current_money_budget = profile.money_budget
        self.current_energy = profile.energy_level
        self.current_attention = profile.attention_capacity
        
        # Initialize memory with core beliefs from profile
        self._initialize_beliefs()
    
    def _create_initial_state(self) -> AgentState:
        """Create initial state based on profile traits."""
        # Neuroticism influences baseline anxiety
        base_anxiety = self.profile.big_five.neuroticism * 0.6 + 0.2
        
        # Conscientiousness influences consistency
        base_consistency = self.profile.big_five.conscientiousness * 0.6 + 0.3
        
        # Extraversion influences social connectedness
        base_social = self.profile.big_five.extraversion * 0.6 + 0.3
        
        # Agreeableness influences trust in others
        base_trust = self.profile.big_five.agreeableness * 0.5 + 0.3
        
        # Openness influences openness to change
        base_openness_change = self.profile.big_five.openness * 0.7 + 0.2
        
        return AgentState(
            self_worth=0.5 + self.rng.uniform(-0.15, 0.15),
            anxiety=base_anxiety,
            confidence=0.5 + self.rng.uniform(-0.1, 0.1),
            consistency=base_consistency,
            momentum=0.5 + self.rng.uniform(-0.1, 0.1),
            energy=self.profile.energy_level,
            reputation=0.5 + self.rng.uniform(-0.1, 0.1),
            trust_in_others=base_trust,
            social_connectedness=base_social,
            fragility_index=0.15 + self.rng.uniform(0, 0.1),
            lock_in=0.1 + self.rng.uniform(0, 0.1),
            cognitive_load=0.3 + self.rng.uniform(-0.1, 0.1),
            learning_rate=0.15 + self.rng.uniform(-0.05, 0.05),
            openness_to_change=base_openness_change,
            mode=AgentMode.OPTIMIZE,
            cascade_active=False,
            success_streak=0,
            failure_streak=0,
            emotional_state="neutral"
        )
    
    def _initialize_beliefs(self):
        """Encode core beliefs from profile into semantic memory."""
        for belief in self.profile.core_beliefs:
            self.memory.encode(
                content=belief,
                memory_type=MemoryType.SEMANTIC,
                importance=0.8,
                source="profile",
                key=f"belief:{belief[:30]}"
            )
    
    @staticmethod
    def clamp(val: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Clamp value to specified range."""
        return max(min_val, min(max_val, val))
    
    def update(self, progress: float, peer_gap: float, social_feedback: float,
               failure_flag: bool, success_flag: bool, 
               mentor_flag: bool = False, current_time: Optional[datetime] = None):
        """
        Update all psychological variables based on round events.
        
        Uses reduced-damping update equations for realistic dynamics.
        All changes are clamped to appropriate ranges.
        
        Args:
            progress: Task completion ratio (0-1)
            peer_gap: Normalized difference vs peers (0 = equal, 1 = far behind)
            social_feedback: Social validation signal (-1 to 1)
            failure_flag: Binary failure event occurred
            success_flag: Binary success event occurred
            mentor_flag: Mentorship/support received
            current_time: Current simulation time
        """
        s = self.state
        
        # Convert flags to numeric
        f_fail = 1.0 if failure_flag else 0.0
        f_succ = 1.0 if success_flag else 0.0
        f_mentor = 1.0 if mentor_flag else 0.0
        
        # === UPDATE CORE VARIABLES ===
        
        # Self-worth: Driven by progress, hurt by peer comparison and failure
        s.self_worth = self.clamp(
            s.self_worth 
            + 0.25 * progress 
            - 0.3 * max(peer_gap, 0) 
            + 0.15 * social_feedback 
            - 0.2 * f_fail
        )
        
        # Anxiety: Smoothed blend of current anxiety and new stressors
        raw_anxiety_change = peer_gap * 0.5 + f_fail * 0.5 - f_succ * 0.3
        s.anxiety = self.clamp(0.4 * s.anxiety + 0.6 * raw_anxiety_change)
        
        # Confidence: Based on self-worth and momentum
        s.confidence = self.clamp(0.6 * s.self_worth + 0.4 * s.momentum)
        
        # Consistency: Grows with stability, hurt by failures
        s.consistency = self.clamp(
            s.consistency 
            + 0.05 * (1 - peer_gap) 
            - 0.1 * f_fail
        )
        
        # Momentum: Built by success, destroyed by failure
        s.momentum = self.clamp(
            s.momentum 
            + 0.25 * f_succ 
            - 0.3 * f_fail
        )
        
        # Reputation: Earned through progress and social validation
        s.reputation = self.clamp(
            s.reputation 
            + 0.2 * progress 
            + 0.1 * social_feedback
        )
        
        # Trust in others: Affected by social feedback and mentorship
        s.trust_in_others = self.clamp(
            s.trust_in_others 
            + 0.1 * social_feedback 
            + 0.15 * f_mentor
        )
        
        # Social connectedness: Grows with positive interactions
        s.social_connectedness = self.clamp(
            s.social_connectedness 
            + 0.1 * (progress + social_feedback)
        )
        
        # Fragility index: Accumulates with failures (vulnerability memory)
        s.fragility_index = self.clamp(
            s.fragility_index 
            + 0.1 * f_fail
        )
        
        # Lock-in: Commitment grows with consistency
        s.lock_in = self.clamp(
            s.lock_in 
            + 0.1 * s.consistency
        )
        
        # Cognitive load: Increases with activity, decreases with rest
        s.cognitive_load = self.clamp(
            s.cognitive_load 
            + 0.1 * progress 
            - 0.05 * (1 - s.anxiety)
        )
        
        # Learning rate: Increases from failure, decreases from easy success
        s.learning_rate = self.clamp(
            s.learning_rate 
            + 0.1 * f_fail 
            - 0.05 * f_succ
        )
        
        # Energy: Base drain offset by success boost
        s.energy = self.clamp(
            s.energy 
            - 0.05 
            + 0.1 * f_succ
        )
        
        # === CASCADE LOGIC ===
        # Enter cascade if 3+ consecutive failures AND self-worth critically low
        if failure_flag:
            s.failure_streak += 1
            s.success_streak = 0
        elif success_flag:
            s.success_streak += 1
            s.failure_streak = 0
        
        if s.failure_streak >= 3 and s.self_worth < 0.4:
            s.cascade_active = True
        elif s.cascade_active and (success_flag or mentor_flag):
            s.cascade_active = False
            s.failure_streak = 0
        
        # === MODE TRANSITION ===
        # Priority order: RECOVER > SPIKE > AVOID > EXECUTE > OPTIMIZE
        if s.cascade_active:
            s.mode = AgentMode.RECOVER
            s.emotional_state = "distressed"
        elif s.anxiety > 0.7 and s.self_worth > 0.6:
            s.mode = AgentMode.SPIKE
            s.emotional_state = "aroused"
        elif s.anxiety > 0.6 and s.self_worth < 0.4:
            s.mode = AgentMode.AVOID
            s.emotional_state = "withdrawn"
        elif s.self_worth > 0.5 and s.momentum > 0.5:
            s.mode = AgentMode.EXECUTE
            s.emotional_state = "confident"
        else:
            s.mode = AgentMode.OPTIMIZE
            s.emotional_state = "steady"
        
        # Encode significant events to memory
        self._encode_event(progress, failure_flag, success_flag, current_time)
        
        # Save state snapshot
        self._save_state(current_time)
    
    def _encode_event(self, progress: float, failure_flag: bool, 
                      success_flag: bool, current_time: Optional[datetime]):
        """Encode significant events to episodic memory."""
        if not current_time:
            current_time = datetime.now()
        
        if success_flag:
            self.memory.encode(
                content=f"Success achieved with progress {progress:.2f}",
                memory_type=MemoryType.EPISODIC,
                importance=0.7,
                emotional_valence=0.6,
                source="experience"
            )
        elif failure_flag:
            self.memory.encode(
                content=f"Failure experienced with progress {progress:.2f}",
                memory_type=MemoryType.EPISODIC,
                importance=0.8,
                emotional_valence=-0.5,
                source="experience"
            )
    
    def _save_state(self, current_time: Optional[datetime] = None):
        """Record current state to history."""
        if not current_time:
            current_time = datetime.now()
        self.state_history.append((current_time, AgentState(
            self_worth=self.state.self_worth,
            anxiety=self.state.anxiety,
            confidence=self.state.confidence,
            consistency=self.state.consistency,
            momentum=self.state.momentum,
            energy=self.state.energy,
            reputation=self.state.reputation,
            trust_in_others=self.state.trust_in_others,
            social_connectedness=self.state.social_connectedness,
            fragility_index=self.state.fragility_index,
            lock_in=self.state.lock_in,
            cognitive_load=self.state.cognitive_load,
            learning_rate=self.state.learning_rate,
            openness_to_change=self.state.openness_to_change,
            mode=self.state.mode,
            cascade_active=self.state.cascade_active,
            success_streak=self.state.success_streak,
            failure_streak=self.state.failure_streak,
            active_goal=self.state.active_goal,
            emotional_state=self.state.emotional_state
        )))
    
    def establish_trust(self, other_agent_id: str, trust_level: float):
        """
        Establish or update trust relationship with another agent.
        
        Args:
            other_agent_id: ID of the other agent
            trust_level: Trust level (0-1)
        """
        self.trust_network[other_agent_id] = self.clamp(trust_level)
    
    def receive_influence(self, source_agent_id: str, influence_strength: float):
        """
        Record influence received from another agent.
        
        Args:
            source_agent_id: ID of influencing agent
            influence_strength: Strength of influence (0-1)
        """
        if source_agent_id in self.influence_received:
            # Decay existing and add new
            self.influence_received[source_agent_id] *= 0.9
            self.influence_received[source_agent_id] += influence_strength * 0.1
        else:
            self.influence_received[source_agent_id] = influence_strength
    
    def decide_action(self, available_actions: List[str], 
                      context: Dict[str, Any]) -> str:
        """
        Decide on an action based on current state, personality, and context.
        
        Uses weighted decision making influenced by:
        - Current mode (EXECUTE agents take risks, AVOID agents withdraw)
        - Personality traits (neuroticism affects risk tolerance)
        - Values (achievement-oriented agents prefer goal-progress actions)
        - Energy and cognitive load
        
        Args:
            available_actions: List of possible action identifiers
            context: Dictionary with situational information
        
        Returns:
            Selected action identifier
        """
        if not available_actions:
            return "wait"
        
        s = self.state
        p = self.profile
        
        # Calculate weights for each action
        weights = []
        for action in available_actions:
            weight = 0.5  # Base weight
            
            # Mode modifiers
            if s.mode == AgentMode.EXECUTE:
                if action in ["act", "engage", "compete"]:
                    weight += 0.3
                if action in ["withdraw", "avoid"]:
                    weight -= 0.3
            elif s.mode == AgentMode.AVOID:
                if action in ["withdraw", "avoid", "observe"]:
                    weight += 0.3
                if action in ["act", "engage", "compete"]:
                    weight -= 0.3
            elif s.mode == AgentMode.RECOVER:
                if action in ["rest", "seek_help", "reflect"]:
                    weight += 0.4
                if action in ["act", "compete"]:
                    weight -= 0.4
            
            # Personality modifiers
            if p.big_five.neuroticism > 0.7 and action in ["risk", "compete"]:
                weight -= 0.2
            if p.big_five.extraversion > 0.7 and action in ["engage", "communicate"]:
                weight += 0.2
            if p.big_five.conscientiousness > 0.7 and action in ["plan", "organize"]:
                weight += 0.2
            
            # Value modifiers
            if p.schwartz_values.achievement > 0.7 and action in ["achieve", "compete"]:
                weight += 0.2
            if p.schwartz_values.benevolence > 0.7 and action in ["help", "cooperate"]:
                weight += 0.2
            
            # Energy modifier
            if s.energy < 0.3 and action in ["rest", "observe"]:
                weight += 0.2
            if s.energy < 0.3 and action in ["act", "compete"]:
                weight -= 0.3
            
            weights.append(max(0.01, weight))
        
        # Select action based on weights
        selected = self.rng.weighted_choice(available_actions, weights)
        
        # Log decision
        self.message_history.append({
            "type": "decision",
            "action": selected,
            "context": context,
            "state_snapshot": s.to_dict()
        })
        
        return selected
    
    def communicate(self, message: str, recipient_ids: List[str], 
                    channel: str = "direct"):
        """
        Send a message to other agents.
        
        Args:
            message: Message content
            recipient_ids: List of recipient agent IDs
            channel: Communication channel type
        """
        comm_record = {
            "sender": self.profile.id,
            "recipients": recipient_ids,
            "message": message,
            "channel": channel,
            "timestamp": datetime.now(),
            "emotional_tone": self.state.emotional_state
        }
        self.message_history.append(comm_record)
    
    def process_message(self, message: Dict[str, Any], sender_id: str):
        """
        Process a received message and update internal state.
        
        Args:
            message: Message dictionary with content and metadata
            sender_id: ID of sending agent
        """
        # Check trust in sender
        trust = self.trust_network.get(sender_id, 0.5)
        
        # Emotional impact based on content and trust
        sentiment = message.get("sentiment", 0.0)
        emotional_impact = sentiment * trust * 0.1
        
        # Update emotional state slightly
        self.state.anxiety = self.clamp(self.state.anxiety - emotional_impact * 0.3)
        
        # Encode to memory if important
        if abs(sentiment) > 0.5 or trust > 0.7:
            self.memory.encode(
                content=f"Message from {sender_id}: {message.get('content', '')}",
                memory_type=MemoryType.EPISODIC,
                importance=abs(sentiment) * trust,
                emotional_valence=sentiment,
                source="communication"
            )
    
    def get_current_state_dict(self) -> Dict[str, Any]:
        """Return current state as dictionary."""
        return self.state.to_dict()
    
    def get_profile_dict(self) -> Dict[str, Any]:
        """Return profile as dictionary."""
        return self.profile.to_dict()
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of memory contents."""
        return self.memory.get_autobiographical_summary()
    
    def reflect(self) -> List[str]:
        """
        Perform self-reflection, generating insights from memories.
        
        Returns:
            List of reflective insights
        """
        insights = []
        
        # Retrieve significant episodic memories
        significant = self.memory.retrieve_by_type(MemoryType.EPISODIC, top_k=5)
        
        # Look for patterns
        successes = sum(1 for m in significant if m.emotional_valence > 0)
        failures = sum(1 for m in significant if m.emotional_valence < 0)
        
        if successes > failures * 2:
            insight = "I've been experiencing more successes than failures recently."
            insights.append(insight)
            self.memory.encode(
                content=insight,
                memory_type=MemoryType.REFLECTIVE,
                importance=0.6,
                source="reflection"
            )
        
        if self.state.failure_streak >= 2:
            insight = "I'm going through a difficult period and may need support."
            insights.append(insight)
            self.memory.encode(
                content=insight,
                memory_type=MemoryType.REFLECTIVE,
                importance=0.7,
                source="reflection"
            )
        
        return insights
