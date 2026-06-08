# =============================================================================
# WORLD MODEL — Digital Twin of Simulated Reality
# =============================================================================
"""
The World Model represents the complete state of the simulated environment:
- Entities (agents, organizations, locations, resources, concepts)
- Relationships between entities
- Environmental conditions and context
- Historical state tracking for replay and analysis
- Event propagation and causal chains

The world model is transformed from seed materials during initialization.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, Set, Tuple
import uuid


class EntityType(Enum):
    """Types of entities in the world model."""
    AGENT = auto()           # Individual cognitive agent
    ORGANIZATION = auto()    # Company, government, NGO, etc.
    LOCATION = auto()        # Geographic location
    RESOURCE = auto()        # Material or abstract resource
    EVENT = auto()           # Occurrence that affects the world
    CONCEPT = auto()         # Abstract idea, belief, meme
    DOCUMENT = auto()        # Text source (news, policy, research)
    MEDIA = auto()           # News outlet, social platform


@dataclass
class WorldEntity:
    """
    An entity in the world model.
    
    Attributes:
        id: Unique identifier
        name: Display name
        entity_type: Type of entity
        attributes: Key-value properties
        relationships: Connected entities with relationship types
        state: Current dynamic state
        metadata: Additional information
        created_at: When entity was added to world
        updated_at: Last modification time
    """
    id: str
    name: str
    entity_type: EntityType
    attributes: Dict[str, Any] = field(default_factory=dict)
    relationships: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_relationship(self, target_id: str, relationship_type: str,
                         strength: float = 1.0, **kwargs):
        """
        Add or update a relationship to another entity.
        
        Args:
            target_id: ID of the target entity
            relationship_type: Type of relationship (e.g., "knows", "works_for")
            strength: Relationship strength (0-1)
            **kwargs: Additional relationship properties
        """
        self.relationships[target_id] = {
            "type": relationship_type,
            "strength": strength,
            "updated_at": datetime.now(),
            **kwargs
        }
        self.updated_at = datetime.now()
    
    def remove_relationship(self, target_id: str):
        """Remove a relationship."""
        if target_id in self.relationships:
            del self.relationships[target_id]
            self.updated_at = datetime.now()
    
    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Get an attribute value."""
        return self.attributes.get(key, default)
    
    def set_attribute(self, key: str, value: Any):
        """Set an attribute value."""
        self.attributes[key] = value
        self.updated_at = datetime.now()
    
    def update_state(self, **kwargs):
        """Update dynamic state variables."""
        self.state.update(kwargs)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize entity to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type.name,
            "attributes": self.attributes.copy(),
            "relationships": {
                k: v.copy() for k, v in self.relationships.items()
            },
            "state": self.state.copy(),
            "metadata": self.metadata.copy(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorldEntity':
        """Create entity from dictionary."""
        entity_type_str = data.get('entity_type', 'AGENT')
        entity_type = EntityType[entity_type_str] if entity_type_str in EntityType.__members__ else EntityType.AGENT
        
        created_at = data.get('created_at')
        updated_at = data.get('updated_at')
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', 'Unknown'),
            entity_type=entity_type,
            attributes=data.get('attributes', {}),
            relationships=data.get('relationships', {}),
            state=data.get('state', {}),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(created_at) if created_at else datetime.now(),
            updated_at=datetime.fromisoformat(updated_at) if updated_at else datetime.now()
        )


@dataclass
class WorldState:
    """
    Complete snapshot of the world at a point in time.
    
    Used for checkpointing, replay, and counterfactual analysis.
    """
    timestamp: datetime
    entities: Dict[str, WorldEntity]
    global_state: Dict[str, Any]
    active_events: List[Dict[str, Any]]
    checksum: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize world state to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "entities": {k: v.to_dict() for k, v in self.entities.items()},
            "global_state": self.global_state.copy(),
            "active_events": [e.copy() for e in self.active_events],
            "checksum": self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorldState':
        """Create world state from dictionary."""
        entities = {
            k: WorldEntity.from_dict(v) 
            for k, v in data.get('entities', {}).items()
        }
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            entities=entities,
            global_state=data.get('global_state', {}),
            active_events=data.get('active_events', []),
            checksum=data.get('checksum', '')
        )


class WorldModel:
    """
    Complete digital twin of the simulated world.
    
    Manages:
    - Entity creation, update, and deletion
    - Relationship tracking and graph traversal
    - State history and checkpointing
    - Event propagation
    - Query and analysis
    
    The world model is populated from seed materials during initialization
    and evolves through simulation.
    """
    
    def __init__(self, name: str = "World"):
        """
        Initialize empty world model.
        
        Args:
            name: Name of this world instance
        """
        self.name = name
        self.entities: Dict[str, WorldEntity] = {}
        self.global_state: Dict[str, Any] = {
            "time_step": 0,
            "simulation_start": None,
            "current_datetime": datetime.now(),
            "environmental_factors": {}
        }
        self.active_events: List[Dict[str, Any]] = []
        
        # History for replay and analysis
        self.state_history: List[WorldState] = []
        self.checkpoint_interval: int = 10  # Save every N steps
        
        # Indexes for fast lookup
        self._entity_by_type: Dict[EntityType, Set[str]] = {t: set() for t in EntityType}
        self._entity_by_name: Dict[str, str] = {}  # name -> id
        self._relationship_index: Dict[str, Set[str]] = {}  # id -> connected ids
    
    def add_entity(self, entity: WorldEntity) -> str:
        """
        Add an entity to the world.
        
        Args:
            entity: Entity to add
        
        Returns:
            Entity ID
        """
        self.entities[entity.id] = entity
        self._entity_by_type[entity.entity_type].add(entity.id)
        self._entity_by_name[entity.name.lower()] = entity.id
        self._relationship_index[entity.id] = set()
        
        # Update reverse relationships
        for target_id in entity.relationships.keys():
            if target_id in self._relationship_index:
                self._relationship_index[target_id].add(entity.id)
            else:
                self._relationship_index[target_id] = {entity.id}
        
        return entity.id
    
    def create_entity(self, name: str, entity_type: EntityType,
                      attributes: Optional[Dict[str, Any]] = None,
                      **kwargs) -> WorldEntity:
        """
        Create and add a new entity.
        
        Args:
            name: Entity name
            entity_type: Type of entity
            attributes: Initial attributes
            **kwargs: Additional entity parameters
        
        Returns:
            Created WorldEntity
        """
        entity = WorldEntity(
            id=str(uuid.uuid4()),
            name=name,
            entity_type=entity_type,
            attributes=attributes or {},
            **kwargs
        )
        self.add_entity(entity)
        return entity
    
    def get_entity(self, entity_id: str) -> Optional[WorldEntity]:
        """Get entity by ID."""
        return self.entities.get(entity_id)
    
    def get_entity_by_name(self, name: str) -> Optional[WorldEntity]:
        """Get entity by name (case-insensitive)."""
        entity_id = self._entity_by_name.get(name.lower())
        return self.entities.get(entity_id) if entity_id else None
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[WorldEntity]:
        """Get all entities of a specific type."""
        ids = self._entity_by_type.get(entity_type, set())
        return [self.entities[eid] for eid in ids if eid in self.entities]
    
    def get_agents(self) -> List[WorldEntity]:
        """Get all agent entities."""
        return self.get_entities_by_type(EntityType.AGENT)
    
    def get_organizations(self) -> List[WorldEntity]:
        """Get all organization entities."""
        return self.get_entities_by_type(EntityType.ORGANIZATION)
    
    def remove_entity(self, entity_id: str):
        """
        Remove an entity from the world.
        
        Args:
            entity_id: ID of entity to remove
        """
        if entity_id not in self.entities:
            return
        
        entity = self.entities[entity_id]
        
        # Remove from indexes
        self._entity_by_type[entity.entity_type].discard(entity_id)
        self._entity_by_name.pop(entity.name.lower(), None)
        
        # Remove from relationship index
        connected = self._relationship_index.pop(entity_id, set())
        for connected_id in connected:
            self._relationship_index.get(connected_id, set()).discard(entity_id)
        
        # Remove relationships from other entities
        for other_id, other in self.entities.items():
            if entity_id in other.relationships:
                other.remove_relationship(entity_id)
        
        # Remove from main dict
        del self.entities[entity_id]
    
    def link_entities(self, source_id: str, target_id: str,
                      relationship_type: str, strength: float = 1.0,
                      **kwargs):
        """
        Create a bidirectional relationship between two entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relationship_type: Type of relationship
            strength: Relationship strength
            **kwargs: Additional relationship properties
        """
        source = self.entities.get(source_id)
        target = self.entities.get(target_id)
        
        if not source or not target:
            raise ValueError(f"Entity not found: {source_id if not source else target_id}")
        
        # Add forward relationship
        source.add_relationship(target_id, relationship_type, strength, **kwargs)
        
        # Add reverse relationship (inverse type)
        inverse_type = self._get_inverse_relationship(relationship_type)
        target.add_relationship(source_id, inverse_type, strength, **kwargs)
        
        # Update index
        self._relationship_index.setdefault(source_id, set()).add(target_id)
        self._relationship_index.setdefault(target_id, set()).add(source_id)
    
    def _get_inverse_relationship(self, rel_type: str) -> str:
        """Get inverse relationship type."""
        inverses = {
            "knows": "knows",
            "works_for": "employs",
            "employs": "works_for",
            "located_in": "contains",
            "contains": "located_in",
            "influences": "influenced_by",
            "influenced_by": "influences",
            "trusts": "trusted_by",
            "trusted_by": "trusts",
            "parent_of": "child_of",
            "child_of": "parent_of",
        }
        return inverses.get(rel_type, f"inverse_{rel_type}")
    
    def get_neighbors(self, entity_id: str, 
                      relationship_type: Optional[str] = None,
                      min_strength: float = 0.0) -> List[Tuple[WorldEntity, Dict[str, Any]]]:
        """
        Get neighboring entities connected by relationships.
        
        Args:
            entity_id: Center entity ID
            relationship_type: Filter by relationship type (optional)
            min_strength: Minimum relationship strength
        
        Returns:
            List of (entity, relationship_info) tuples
        """
        entity = self.entities.get(entity_id)
        if not entity:
            return []
        
        neighbors = []
        for target_id, rel_info in entity.relationships.items():
            if min_strength > 0 and rel_info.get('strength', 0) < min_strength:
                continue
            if relationship_type and rel_info.get('type') != relationship_type:
                continue
            
            target = self.entities.get(target_id)
            if target:
                neighbors.append((target, rel_info))
        
        return neighbors
    
    def add_event(self, event: Dict[str, Any]):
        """
        Add an active event to the world.
        
        Args:
            event: Event dictionary with type, description, effects, etc.
        """
        event['created_at'] = datetime.now()
        event['active'] = True
        self.active_events.append(event)
        
        # Also create an event entity for tracking
        event_entity = self.create_entity(
            name=event.get('name', f"Event_{len(self.active_events)}"),
            entity_type=EntityType.EVENT,
            attributes=event
        )
    
    def propagate_event_effects(self, event: Dict[str, Any], 
                                max_hops: int = 3) -> List[str]:
        """
        Propagate event effects through the relationship network.
        
        Uses spreading activation to determine which entities are affected.
        
        Args:
            event: Event dictionary
            max_hops: Maximum relationship hops to propagate
        
        Returns:
            List of affected entity IDs
        """
        affected = set()
        
        # Start with directly mentioned entities
        target_ids = event.get('targets', [])
        affected.update(target_ids)
        
        # Propagate through network
        current_frontier = set(target_ids)
        decay = event.get('propagation_decay', 0.5)
        strength = 1.0
        
        for hop in range(max_hops):
            next_frontier = set()
            strength *= decay
            
            for entity_id in current_frontier:
                neighbors = self.get_neighbors(entity_id, min_strength=strength)
                for neighbor, rel_info in neighbors:
                    if neighbor.id not in affected:
                        affected.add(neighbor.id)
                        next_frontier.add(neighbor.id)
            
            current_frontier = next_frontier
            if not current_frontier:
                break
        
        return list(affected)
    
    def advance_time(self, delta_seconds: float = 3600):
        """
        Advance the world clock.
        
        Args:
            delta_seconds: Time increment in seconds
        """
        self.global_state["time_step"] += 1
        current = self.global_state.get("current_datetime", datetime.now())
        from datetime import timedelta
        self.global_state["current_datetime"] = current + timedelta(seconds=delta_seconds)
    
    def save_checkpoint(self) -> WorldState:
        """
        Save current world state as checkpoint.
        
        Returns:
            Saved WorldState object
        """
        state = WorldState(
            timestamp=self.global_state.get("current_datetime", datetime.now()),
            entities={k: v for k, v in self.entities.items()},
            global_state=self.global_state.copy(),
            active_events=[e.copy() for e in self.active_events]
        )
        
        # Calculate simple checksum using SHA-256
        import hashlib
        state_dict = state.to_dict()
        checksum_data = str(sorted(state_dict.items()))
        state.checksum = hashlib.sha256(checksum_data.encode()).hexdigest()[:12]
        
        self.state_history.append(state)
        return state
    
    def restore_checkpoint(self, state: WorldState):
        """
        Restore world to a previous checkpoint.
        
        Args:
            state: WorldState to restore
        """
        self.entities = {k: v for k, v in state.entities.items()}
        self.global_state = state.global_state.copy()
        self.active_events = [e.copy() for e in state.active_events]
        
        # Rebuild indexes
        self._rebuild_indexes()
    
    def _rebuild_indexes(self):
        """Rebuild internal indexes from entities."""
        self._entity_by_type = {t: set() for t in EntityType}
        self._entity_by_name = {}
        self._relationship_index = {}
        
        for eid, entity in self.entities.items():
            self._entity_by_type[entity.entity_type].add(eid)
            self._entity_by_name[entity.name.lower()] = eid
            self._relationship_index[eid] = set(entity.relationships.keys())
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get summary of current world state."""
        return {
            "name": self.name,
            "time_step": self.global_state.get("time_step", 0),
            "current_datetime": self.global_state.get("current_datetime", datetime.now()).isoformat(),
            "entity_counts": {
                et.name: len(ids) for et, ids in self._entity_by_type.items()
            },
            "total_entities": len(self.entities),
            "active_events": len(self.active_events),
            "checkpoints_saved": len(self.state_history)
        }
    
    def query(self, query_str: str) -> List[WorldEntity]:
        """
        Simple query interface for finding entities.
        
        Supports basic filters like:
        - "type:AGENT" - all agents
        - "name:john" - entities with "john" in name
        - "attr:location:NYC" - entities with location=NYC
        
        Args:
            query_str: Query string
        
        Returns:
            Matching entities
        """
        results = list(self.entities.values())
        
        if not query_str:
            return results
        
        parts = query_str.split()
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                
                if key == "type":
                    try:
                        et = EntityType[value.upper()]
                        results = [e for e in results if e.entity_type == et]
                    except KeyError:
                        pass
                elif key == "name":
                    results = [e for e in results if value.lower() in e.name.lower()]
                elif key == "attr":
                    if ':' in value:
                        attr_key, attr_val = value.split(':', 1)
                        results = [
                            e for e in results 
                            if e.attributes.get(attr_key) == attr_val
                        ]
        
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize world model to dictionary."""
        return {
            "name": self.name,
            "global_state": self.global_state.copy(),
            "entities": {k: v.to_dict() for k, v in self.entities.items()},
            "active_events": [e.copy() for e in self.active_events],
            "checkpoint_count": len(self.state_history)
        }
