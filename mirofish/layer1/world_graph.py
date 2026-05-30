"""
MiroFish Layer 1: World Graph Database

In-memory graph database with Neo4j/Kuzu compatibility layer.
Supports temporal queries, versioning, and efficient traversal.
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Iterator
from threading import RLock

from .schema import (
    Citation, Edge, EdgeType, Node, NodeType,
    Person, Organization, Place, Concept, Event
)
from .extraction import ExtractedEntity, ExtractedRelationship, ExtractionResult

logger = logging.getLogger(__name__)


class TemporalIndex:
    """Index for time-based queries on nodes and edges."""
    
    def __init__(self):
        # Map of timestamp -> set of node/edge IDs
        self.node_timeline: Dict[datetime, Set[str]] = defaultdict(set)
        self.edge_timeline: Dict[datetime, Set[str]] = defaultdict(set)
    
    def add_node(self, node_id: str, timestamp: datetime):
        self.node_timeline[timestamp].add(node_id)
    
    def add_edge(self, edge_id: str, timestamp: datetime):
        self.edge_timeline[timestamp].add(edge_id)
    
    def get_nodes_at_time(self, timestamp: datetime, tolerance_seconds: int = 3600) -> Set[str]:
        """Get all nodes that existed at a given time."""
        result = set()
        for ts, node_ids in self.node_timeline.items():
            if abs((ts - timestamp).total_seconds()) <= tolerance_seconds:
                result.update(node_ids)
        return result
    
    def get_edges_at_time(self, timestamp: datetime, tolerance_seconds: int = 3600) -> Set[str]:
        """Get all edges that existed at a given time."""
        result = set()
        for ts, edge_ids in self.edge_timeline.items():
            if abs((ts - timestamp).total_seconds()) <= tolerance_seconds:
                result.update(edge_ids)
        return result


class GraphSnapshot:
    """Represents a point-in-time snapshot of the graph."""
    
    def __init__(self, snapshot_id: str, timestamp: datetime):
        self.snapshot_id = snapshot_id
        self.timestamp = timestamp
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}
    
    def add_node(self, node: Node):
        self.nodes[node.id] = node
    
    def add_edge(self, edge: Edge):
        self.edges[edge.id] = edge


class WorldGraph:
    """
    In-memory graph database with temporal support.
    
    Designed to be compatible with Neo4j or Kuzu for persistence.
    Supports:
    - Node and edge CRUD operations
    - Entity disambiguation and merging
    - Temporal queries (time-travel)
    - Snapshotting and versioning
    - Efficient neighborhood traversal
    """
    
    def __init__(self, enable_temporal: bool = True):
        self.enable_temporal = enable_temporal
        
        # Core storage
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}
        
        # Indexes
        self.name_to_id: Dict[str, Set[str]] = defaultdict(set)
        self.type_to_ids: Dict[NodeType, Set[str]] = defaultdict(set)
        self.adjacency: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        
        # Temporal indexing
        self.temporal_index = TemporalIndex() if enable_temporal else None
        self.snapshots: Dict[str, GraphSnapshot] = {}
        
        # Thread safety
        self._lock = RLock()
        
        # Statistics
        self.created_at = datetime.utcnow()
        self.last_modified = datetime.utcnow()
    
    def add_node(self, node: Node, upsert: bool = True) -> str:
        """
        Add a node to the graph.
        
        Args:
            node: Node to add
            upsert: If True, merge with existing node if name matches
        
        Returns:
            Node ID
        """
        with self._lock:
            # Check for existing node with same name
            if upsert and node.name:
                existing_ids = self.name_to_id.get(node.name.lower(), set())
                if existing_ids:
                    # Merge with first existing node
                    existing_id = list(existing_ids)[0]
                    existing_node = self.nodes[existing_id]
                    self._merge_nodes(existing_node, node)
                    return existing_id
            
            # Add new node
            self.nodes[node.id] = node
            
            # Update indexes
            if node.name:
                self.name_to_id[node.name.lower()].add(node.id)
            for alias in node.aliases:
                self.name_to_id[alias.lower()].add(node.id)
            
            node_type = NodeType(node.properties.get("type", "Concept"))
            self.type_to_ids[node_type].add(node.id)
            
            # Temporal indexing
            if self.temporal_index:
                self.temporal_index.add_node(node.id, node.created_at)
            
            self.last_modified = datetime.utcnow()
            return node.id
    
    def add_edge(self, edge: Edge) -> str:
        """Add an edge to the graph."""
        with self._lock:
            self.edges[edge.id] = edge
            
            # Update adjacency list
            self.adjacency[edge.source_id][edge.target_id].append(edge.id)
            
            # For bidirectional relationships
            if edge.properties.get("direction") == "bidirectional":
                self.adjacency[edge.target_id][edge.source_id].append(edge.id)
            
            # Temporal indexing
            if self.temporal_index:
                self.temporal_index.add_edge(edge.id, edge.created_at)
            
            self.last_modified = datetime.utcnow()
            return edge.id
    
    def _merge_nodes(self, existing: Node, new: Node):
        """Merge new node into existing node."""
        # Merge aliases
        for alias in new.aliases:
            if alias not in existing.aliases:
                existing.aliases.append(alias)
        
        # Merge properties (new values override)
        existing.properties.update(new.properties)
        
        # Merge citations
        for citation in new.source_citations:
            if citation not in existing.source_citations:
                existing.source_citations.append(citation)
        
        # Update specific fields for specialized node types
        if isinstance(existing, Person) and isinstance(new, Person):
            existing.demographics.update(new.demographics)
            existing.influence_score = max(existing.influence_score, new.influence_score)
        
        existing.updated_at = datetime.utcnow()
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_edge(self, edge_id: str) -> Optional[Edge]:
        """Get an edge by ID."""
        return self.edges.get(edge_id)
    
    def get_nodes_by_name(self, name: str) -> List[Node]:
        """Get nodes by name (case-insensitive)."""
        ids = self.name_to_id.get(name.lower(), set())
        return [self.nodes[nid] for nid in ids if nid in self.nodes]
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[Node]:
        """Get all nodes of a specific type."""
        ids = self.type_to_ids.get(node_type, set())
        return [self.nodes[nid] for nid in ids if nid in self.nodes]
    
    def get_neighbors(
        self,
        node_id: str,
        direction: str = "outgoing",
        edge_types: Optional[List[EdgeType]] = None
    ) -> List[Tuple[Node, Edge]]:
        """
        Get neighboring nodes.
        
        Args:
            node_id: Source node ID
            direction: 'outgoing', 'incoming', or 'both'
            edge_types: Filter by edge types (optional)
        
        Returns:
            List of (neighbor_node, connecting_edge) tuples
        """
        results = []
        
        if direction in ("outgoing", "both"):
            for target_id, edge_ids in self.adjacency.get(node_id, {}).items():
                for edge_id in edge_ids:
                    edge = self.edges.get(edge_id)
                    if edge and (not edge_types or edge.edge_type in edge_types):
                        target_node = self.nodes.get(target_id)
                        if target_node:
                            results.append((target_node, edge))
        
        if direction in ("incoming", "both"):
            for source_id, targets in self.adjacency.items():
                if node_id in targets:
                    for edge_id in targets[node_id]:
                        edge = self.edges.get(edge_id)
                        if edge and (not edge_types or edge.edge_type in edge_types):
                            source_node = self.nodes.get(source_id)
                            if source_node:
                                results.append((source_node, edge))
        
        return results
    
    def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5
    ) -> Optional[List[Tuple[Node, Edge]]]:
        """
        Find a path between two nodes using BFS.
        
        Returns:
            List of (node, edge) tuples representing the path, or None if no path exists
        """
        if start_id == end_id:
            return [(self.nodes.get(start_id), None)]
        
        visited = {start_id}
        queue = [(start_id, [])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            neighbors = self.get_neighbors(current_id, direction="outgoing")
            for neighbor_node, edge in neighbors:
                if neighbor_node.id == end_id:
                    return path + [(neighbor_node, edge)]
                
                if neighbor_node.id not in visited and len(path) < max_depth:
                    visited.add(neighbor_node.id)
                    queue.append((neighbor_node.id, path + [(neighbor_node, edge)]))
        
        return None
    
    def create_snapshot(self, snapshot_id: Optional[str] = None) -> GraphSnapshot:
        """Create a point-in-time snapshot of the graph."""
        snapshot_id = snapshot_id or f"snapshot_{datetime.utcnow().isoformat()}"
        snapshot = GraphSnapshot(snapshot_id, datetime.utcnow())
        
        with self._lock:
            for node in self.nodes.values():
                snapshot.add_node(node)
            for edge in self.edges.values():
                snapshot.add_edge(edge)
        
        self.snapshots[snapshot_id] = snapshot
        return snapshot
    
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore the graph to a previous snapshot."""
        snapshot = self.snapshots.get(snapshot_id)
        if not snapshot:
            return False
        
        with self._lock:
            self.nodes = dict(snapshot.nodes)
            self.edges = dict(snapshot.edges)
            
            # Rebuild indexes
            self._rebuild_indexes()
        
        return True
    
    def _rebuild_indexes(self):
        """Rebuild all indexes from current nodes and edges."""
        self.name_to_id.clear()
        self.type_to_ids.clear()
        self.adjacency.clear()
        
        for node in self.nodes.values():
            if node.name:
                self.name_to_id[node.name.lower()].add(node.id)
            for alias in node.aliases:
                self.name_to_id[alias.lower()].add(node.id)
            
            node_type = NodeType(node.properties.get("type", "Concept"))
            self.type_to_ids[node_type].add(node.id)
        
        for edge in self.edges.values():
            self.adjacency[edge.source_id][edge.target_id].append(edge.id)
            if edge.properties.get("direction") == "bidirectional":
                self.adjacency[edge.target_id][edge.source_id].append(edge.id)
    
    def apply_extraction_result(self, result: ExtractionResult) -> Dict[str, str]:
        """
        Apply extraction results to the graph.
        
        Returns:
            Mapping of entity names to node IDs
        """
        entity_map = {}
        
        # First pass: create/update nodes
        for entity in result.entities:
            node = entity.to_node()
            node_id = self.add_node(node, upsert=True)
            entity_map[entity.name] = node_id
            
            # Also map aliases
            for alias in entity.aliases:
                entity_map[alias] = node_id
        
        # Second pass: create edges
        for relationship in result.relationships:
            edge = relationship.to_edge(entity_map)
            if edge:
                self.add_edge(edge)
        
        return entity_map
    
    def query(
        self,
        node_type: Optional[NodeType] = None,
        name_pattern: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 100
    ) -> List[Node]:
        """
        Query nodes with filters.
        
        Args:
            node_type: Filter by node type
            name_pattern: Substring match on name/aliases
            min_confidence: Minimum confidence score
            limit: Maximum results
        
        Returns:
            List of matching nodes
        """
        results = []
        
        candidates = self.nodes.values()
        if node_type:
            candidates = self.get_nodes_by_type(node_type)
        
        for node in candidates:
            # Confidence filter (based on citations)
            if node.source_citations:
                avg_confidence = sum(c.extraction_confidence for c in node.source_citations) / len(node.source_citations)
                if avg_confidence < min_confidence:
                    continue
            
            # Name pattern filter
            if name_pattern:
                pattern_lower = name_pattern.lower()
                if pattern_lower not in node.name.lower():
                    if not any(pattern_lower in alias.lower() for alias in node.aliases):
                        continue
            
            results.append(node)
            if len(results) >= limit:
                break
        
        return results
    
    def statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "nodes_by_type": {nt.value: len(ids) for nt, ids in self.type_to_ids.items()},
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "snapshots": len(self.snapshots)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Export graph as dictionary."""
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges.values()],
            "statistics": self.statistics()
        }
    
    def export_neo4j_cypher(self) -> str:
        """
        Generate Neo4j Cypher statements for importing the graph.
        
        Returns:
            String containing Cypher CREATE statements
        """
        statements = []
        
        # Create constraints
        statements.append("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Node) REQUIRE n.id IS UNIQUE;")
        
        # Create nodes
        for node in self.nodes.values():
            node_type = node.properties.get("type", "Node")
            labels = [f":{node_type}"]
            
            props = []
            props.append(f"id: '{node.id}'")
            props.append(f"name: '{node.name.replace("'", "\\'")}'")
            
            if node.aliases:
                aliases_str = ", ".join(f"'{a}'" for a in node.aliases)
                props.append(f"aliases: [{aliases_str}]")
            
            for key, value in node.properties.items():
                if isinstance(value, str):
                    props.append(f"{key}: '{value.replace("'", "\\'")}'")
                elif isinstance(value, (int, float)):
                    props.append(f"{key}: {value}")
            
            props_str = ", ".join(props)
            statements.append(f"CREATE ({' '.join(labels)} {{{props_str}}});")
        
        # Create edges
        for edge in self.edges.values():
            props = []
            props.append(f"id: '{edge.id}'")
            props.append(f"type: '{edge.edge_type.value}'")
            props.append(f"confidence: {edge.confidence}")
            
            for key, value in edge.properties.items():
                if isinstance(value, str):
                    props.append(f"{key}: '{value.replace("'", "\\'")}'")
                elif isinstance(value, (int, float)):
                    props.append(f"{key}: {value}")
            
            props_str = ", ".join(props)
            statements.append(
                f"MATCH (a {{id: '{edge.source_id}'}}), (b {{id: '{edge.target_id}'}}) "
                f"CREATE (a)-[:{edge.edge_type.value} {{{props_str}}}]->(b);"
            )
        
        return "\n".join(statements)
