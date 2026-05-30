# =============================================================================
# MEMORY SYSTEM — Multi-Component Memory Architecture
# =============================================================================
"""
Agents possess five distinct memory systems:
1. Episodic: Specific events with timestamps and emotional valence
2. Semantic: General knowledge and facts about the world
3. Working: Short-term active context (limited capacity)
4. Reflective: Self-referential memories and identity updates
5. Emotional: Affective associations with entities and concepts

Each memory type has different encoding, retention, and retrieval dynamics.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Set, Any, Tuple
import math


class MemoryType(Enum):
    """Types of memory in the cognitive architecture."""
    EPISODIC = auto()    # Specific events ("what happened")
    SEMANTIC = auto()    # General knowledge ("what is true")
    WORKING = auto()     # Active context ("what I'm thinking about now")
    REFLECTIVE = auto()  # Self-concept updates ("what I learned about myself")
    EMOTIONAL = auto()   # Affective associations ("how I feel about X")


@dataclass
class MemoryEntry:
    """
    A single memory unit with metadata.
    
    Attributes:
        content: The actual memory content (text or structured data)
        memory_type: Type of memory (episodic, semantic, etc.)
        timestamp: When the memory was encoded
        importance: Salience weight (0-1), affects retention
        emotional_valence: Positive/negative charge (-1 to +1)
        decay_rate: How quickly memory fades (0-1 per time unit)
        retrieval_count: Number of times accessed (strengthens memory)
        last_retrieved: Timestamp of last access
        associations: Linked memory IDs for network effects
        source: Origin (perception, inference, communication)
        confidence: Certainty level (0-1)
    """
    content: Any
    memory_type: MemoryType
    timestamp: datetime
    importance: float = 0.5
    emotional_valence: float = 0.0
    decay_rate: float = 0.01
    retrieval_count: int = 0
    last_retrieved: Optional[datetime] = None
    associations: Set[int] = field(default_factory=set)
    source: str = "perception"
    confidence: float = 1.0
    id: int = field(default_factory=lambda: id(object()))
    
    def strength(self, current_time: datetime) -> float:
        """
        Calculate current memory strength based on decay and usage.
        
        Uses Ebbinghaus forgetting curve with retrieval reinforcement.
        
        Args:
            current_time: Current simulation time
        
        Returns:
            Memory strength in [0, 1]
        """
        if self.last_retrieved is None:
            age = (current_time - self.timestamp).total_seconds() / 3600  # hours
        else:
            age = (current_time - self.last_retrieved).total_seconds() / 3600
        
        # Ebbinghaus forgetting: S(t) = S0 * e^(-λt)
        base_decay = math.exp(-self.decay_rate * age)
        
        # Retrieval reinforcement: each retrieval strengthens by ~10%
        retrieval_boost = 1.0 + 0.1 * min(self.retrieval_count, 10)
        
        # Importance acts as ceiling
        max_strength = self.importance
        
        return min(max_strength, base_decay * retrieval_boost)
    
    def retrieve(self, current_time: datetime):
        """Mark memory as retrieved, strengthening it."""
        self.retrieval_count += 1
        self.last_retrieved = current_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize memory entry to dictionary."""
        return {
            "id": self.id,
            "content": str(self.content),
            "memory_type": self.memory_type.name,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "emotional_valence": self.emotional_valence,
            "decay_rate": self.decay_rate,
            "retrieval_count": self.retrieval_count,
            "last_retrieved": self.last_retrieved.isoformat() if self.last_retrieved else None,
            "associations": list(self.associations),
            "source": self.source,
            "confidence": self.confidence
        }


@dataclass
class MemorySystem:
    """
    Complete memory architecture for an agent.
    
    Manages encoding, storage, retrieval, and forgetting across all memory types.
    Implements capacity limits and competitive retrieval dynamics.
    
    Attributes:
        working_capacity: Maximum items in working memory (typically 7±2)
        episodic_capacity: Maximum episodic memories retained
        semantic_capacity: Maximum semantic knowledge units
        consolidation_threshold: Strength needed for long-term storage
    """
    working_capacity: int = 7
    episodic_capacity: int = 1000
    semantic_capacity: int = 5000
    consolidation_threshold: float = 0.3
    
    # Memory stores
    _episodic: List[MemoryEntry] = field(default_factory=list)
    _semantic: Dict[str, MemoryEntry] = field(default_factory=dict)
    _working: List[MemoryEntry] = field(default_factory=list)
    _reflective: List[MemoryEntry] = field(default_factory=list)
    _emotional: Dict[str, MemoryEntry] = field(default_factory=dict)
    
    # Metadata
    _next_id: int = 0
    _current_time: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Initialize empty memory stores."""
        self._episodic = []
        self._semantic = {}
        self._working = []
        self._reflective = []
        self._emotional = {}
        self._next_id = 0
    
    def set_current_time(self, time: datetime):
        """Update internal clock for decay calculations."""
        self._current_time = time
    
    def encode(self, content: Any, memory_type: MemoryType, 
               importance: float = 0.5, emotional_valence: float = 0.0,
               decay_rate: float = 0.01, source: str = "perception",
               key: Optional[str] = None) -> MemoryEntry:
        """
        Encode a new memory into the appropriate store.
        
        Args:
            content: Memory content
            memory_type: Type of memory to encode
            importance: Initial salience (0-1)
            emotional_valence: Emotional charge (-1 to +1)
            decay_rate: Forgetting rate
            source: Origin of memory
            key: Unique key for semantic/emotional memories
        
        Returns:
            Created MemoryEntry
        """
        entry = MemoryEntry(
            content=content,
            memory_type=memory_type,
            timestamp=self._current_time,
            importance=importance,
            emotional_valence=emotional_valence,
            decay_rate=decay_rate,
            source=source,
            id=self._next_id
        )
        self._next_id += 1
        
        # Route to appropriate store
        if memory_type == MemoryType.WORKING:
            self._working.append(entry)
            # Enforce capacity limit
            if len(self._working) > self.working_capacity:
                self._forget_working()
        elif memory_type == MemoryType.EPISODIC:
            self._episodic.append(entry)
            if len(self._episodic) > self.episodic_capacity:
                self._forget_episodic()
        elif memory_type == MemoryType.SEMANTIC:
            if key is None:
                key = str(content)[:50]  # Use content snippet as key
            self._semantic[key] = entry
        elif memory_type == MemoryType.REFLECTIVE:
            self._reflective.append(entry)
        elif memory_type == MemoryType.EMOTIONAL:
            if key is None:
                raise ValueError("Emotional memories require a key (entity/concept)")
            self._emotional[key] = entry
        
        return entry
    
    def retrieve_by_type(self, memory_type: MemoryType, 
                         query: Optional[Any] = None,
                         top_k: int = 5) -> List[MemoryEntry]:
        """
        Retrieve memories of specified type, optionally filtered by query.
        
        Uses spreading activation for associative retrieval.
        
        Args:
            memory_type: Type of memories to retrieve
            query: Optional query to match against content
            top_k: Maximum number of memories to return
        
        Returns:
            List of retrieved memories, sorted by strength
        """
        candidates = []
        
        if memory_type == MemoryType.WORKING:
            candidates = self._working.copy()
        elif memory_type == MemoryType.EPISODIC:
            candidates = [m for m in self._episodic if m.strength(self._current_time) > 0.1]
        elif memory_type == MemoryType.SEMANTIC:
            candidates = list(self._semantic.values())
        elif memory_type == MemoryType.REFLECTIVE:
            candidates = self._reflective
        elif memory_type == MemoryType.EMOTIONAL:
            candidates = list(self._emotional.values())
        
        # Filter by query if provided
        if query is not None:
            query_str = str(query).lower()
            candidates = [
                m for m in candidates 
                if query_str in str(m.content).lower()
            ]
        
        # Sort by strength
        candidates.sort(key=lambda m: m.strength(self._current_time), reverse=True)
        
        # Mark as retrieved
        for memory in candidates[:top_k]:
            memory.retrieve(self._current_time)
        
        return candidates[:top_k]
    
    def retrieve_emotional(self, entity_key: str) -> Optional[float]:
        """
        Get emotional association with an entity.
        
        Args:
            entity_key: Entity/concept identifier
        
        Returns:
            Emotional valence (-1 to +1) or None if no association
        """
        if entity_key in self._emotional:
            entry = self._emotional[entity_key]
            entry.retrieve(self._current_time)
            return entry.emotional_valence
        return None
    
    def update_emotional(self, entity_key: str, valence: float, 
                        importance: float = 0.5):
        """
        Update or create emotional association.
        
        Args:
            entity_key: Entity/concept identifier
            valence: New emotional valence (-1 to +1)
            importance: Salience of this association
        """
        if entity_key in self._emotional:
            # Blend with existing emotion
            existing = self._emotional[entity_key]
            existing.emotional_valence = 0.7 * existing.emotional_valence + 0.3 * valence
            existing.importance = max(existing.importance, importance)
        else:
            self.encode(
                content=f"Emotional response to {entity_key}",
                memory_type=MemoryType.EMOTIONAL,
                importance=importance,
                emotional_valence=valence,
                key=entity_key
            )
    
    def get_autobiographical_summary(self) -> Dict[str, Any]:
        """
        Generate summary of agent's memory state.
        
        Returns:
            Dictionary with memory statistics and recent significant events
        """
        # Find most important episodic memories
        significant_events = sorted(
            self._episodic,
            key=lambda m: m.importance * m.strength(self._current_time),
            reverse=True
        )[:10]
        
        # Count memories by type
        emotional_profile = {
            k: v.emotional_valence 
            for k, v in self._emotional.items()
        }
        
        return {
            "episodic_count": len(self._episodic),
            "semantic_count": len(self._semantic),
            "working_count": len(self._working),
            "reflective_count": len(self._reflective),
            "emotional_count": len(self._emotional),
            "significant_events": [e.to_dict() for e in significant_events],
            "emotional_profile": emotional_profile
        }
    
    def _forget_working(self):
        """Remove weakest working memory item."""
        if not self._working:
            return
        self._working.sort(key=lambda m: m.strength(self._current_time))
        self._working.pop(0)
    
    def _forget_episodic(self):
        """Remove weakest episodic memory."""
        if not self._episodic:
            return
        self._episodic.sort(key=lambda m: m.strength(self._current_time))
        self._episodic.pop(0)
    
    def consolidate(self):
        """
        Move important working memories to episodic/semantic storage.
        
        Called periodically during simulation to manage memory flow.
        """
        to_consolidate = [
            m for m in self._working 
            if m.strength(self._current_time) > self.consolidation_threshold
        ]
        
        for memory in to_consolidate:
            if memory.memory_type == MemoryType.WORKING:
                # Promote to episodic
                memory.memory_type = MemoryType.EPISODIC
                self._episodic.append(memory)
                self._working.remove(memory)
    
    def clear(self):
        """Clear all memory stores."""
        self._episodic.clear()
        self._semantic.clear()
        self._working.clear()
        self._reflective.clear()
        self._emotional.clear()
        self._next_id = 0
