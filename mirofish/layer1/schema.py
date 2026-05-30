"""
MiroFish Layer 1: Knowledge Ingestion & World Graph Builder

This module defines the core schema for the World Graph, including
Node types, Edge types, and Provenance tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid


class NodeType(Enum):
    PERSON = "Person"
    ORGANIZATION = "Organization"
    PLACE = "Place"
    CONCEPT = "Concept"
    EVENT = "Event"


class EdgeType(Enum):
    INFLUENCE = "Influence"
    OWNERSHIP = "Ownership"
    FRIENDSHIP = "Friendship"
    COMPETITION = "Competition"
    MEMBERSHIP = "Membership"
    CAUSALITY = "Causality"


@dataclass
class Citation:
    """Tracks the source of information for scientific validity."""
    source_id: str
    source_type: str  # e.g., 'pdf', 'web', 'csv'
    chunk_id: Optional[str]
    page_number: Optional[int]
    url: Optional[str]
    retrieval_timestamp: datetime = field(default_factory=datetime.utcnow)
    extraction_confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "chunk_id": self.chunk_id,
            "page_number": self.page_number,
            "url": self.url,
            "retrieval_timestamp": self.retrieval_timestamp.isoformat(),
            "extraction_confidence": self.extraction_confidence
        }


@dataclass
class Node:
    """Base class for all World Graph nodes."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    aliases: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    source_citations: List[Citation] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_citation(self, citation: Citation):
        self.source_citations.append(citation)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "aliases": self.aliases,
            "properties": self.properties,
            "source_citations": [c.to_dict() for c in self.source_citations],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class Person(Node):
    demographics: Dict[str, Any] = field(default_factory=dict)
    influence_score: float = 0.0
    # Specific properties: age, gender, education, income, location_id

    def __post_init__(self):
        if not self.properties.get("type"):
            self.properties["type"] = NodeType.PERSON.value


@dataclass
class Organization(Node):
    org_type: str = ""  # corporation, government, NGO
    size: int = 0
    sector: str = ""
    hierarchy: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not self.properties.get("type"):
            self.properties["type"] = NodeType.ORGANIZATION.value


@dataclass
class Place(Node):
    geo_coordinates: Optional[Tuple[float, float]] = None
    place_type: str = ""  # city, country, building
    population: Optional[int] = None

    def __post_init__(self):
        if not self.properties.get("type"):
            self.properties["type"] = NodeType.PLACE.value


@dataclass
class Concept(Node):
    definition: str = ""
    domain: str = ""
    prevalence: float = 0.0

    def __post_init__(self):
        if not self.properties.get("type"):
            self.properties["type"] = NodeType.CONCEPT.value


@dataclass
class Event(Node):
    timestamp: Optional[datetime] = None
    duration: Optional[timedelta] = None
    magnitude: float = 0.0
    sentiment: float = 0.0  # -1.0 to 1.0
    location_id: Optional[str] = None

    def __post_init__(self):
        if not self.properties.get("type"):
            self.properties["type"] = NodeType.EVENT.value


@dataclass
class Edge:
    """Base class for all World Graph edges."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    edge_type: EdgeType = EdgeType.INFLUENCE
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source_citations: List[Citation] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_citation(self, citation: Citation):
        self.source_citations.append(citation)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "properties": self.properties,
            "confidence": self.confidence,
            "source_citations": [c.to_dict() for c in self.source_citations],
            "created_at": self.created_at.isoformat()
        }


# Specialized Edge Types with specific property validation logic could go here,
# but for flexibility, we use the generic Edge with typed properties.

@dataclass
class InfluenceEdge(Edge):
    strength: float = 0.0
    direction: str = "unidirectional"  # unidirectional, bidirectional

    def __post_init__(self):
        self.edge_type = EdgeType.INFLUENCE
        self.properties["strength"] = self.strength
        self.properties["direction"] = self.direction


@dataclass
class OwnershipEdge(Edge):
    percentage: float = 0.0

    def __post_init__(self):
        self.edge_type = EdgeType.OWNERSHIP
        self.properties["percentage"] = self.percentage


@dataclass
class FriendshipEdge(Edge):
    closeness: float = 0.0

    def __post_init__(self):
        self.edge_type = EdgeType.FRIENDSHIP
        self.properties["closeness"] = self.closeness


@dataclass
class CompetitionEdge(Edge):
    domain: str = ""
    intensity: float = 0.0

    def __post_init__(self):
        self.edge_type = EdgeType.COMPETITION
        self.properties["domain"] = self.domain
        self.properties["intensity"] = self.intensity


@dataclass
class MembershipEdge(Edge):
    role: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    def __post_init__(self):
        self.edge_type = EdgeType.MEMBERSHIP
        self.properties["role"] = self.role
        if self.start_date:
            self.properties["start_date"] = self.start_date.isoformat()
        if self.end_date:
            self.properties["end_date"] = self.end_date.isoformat()


@dataclass
class CausalityEdge(Edge):
    strength: float = 0.0
    lag: Optional[timedelta] = None

    def __post_init__(self):
        self.edge_type = EdgeType.CAUSALITY
        self.properties["strength"] = self.strength
        if self.lag:
            self.properties["lag_seconds"] = self.lag.total_seconds()
