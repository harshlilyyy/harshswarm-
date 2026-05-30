"""
MiroFish Layer 1: Semantic Extraction

Extracts entities, relationships, temporal information, and sentiment
from document chunks using LLM-based or fallback NLP methods.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .schema import (
    Citation, Concept, Edge, Event, FriendshipEdge, InfluenceEdge,
    MembershipEdge, Node, NodeType, Organization, Person, Place
)
from .ingestion import DocumentChunk

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    """Represents an entity extracted from text."""
    name: str
    entity_type: NodeType
    aliases: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source_citations: List[Citation] = field(default_factory=list)
    
    def to_node(self) -> Node:
        """Convert to appropriate Node subclass."""
        if self.entity_type == NodeType.PERSON:
            return Person(
                name=self.name,
                aliases=self.aliases,
                properties=self.properties,
                demographics=self.properties.get("demographics", {}),
                influence_score=self.properties.get("influence_score", 0.0),
                source_citations=self.source_citations
            )
        elif self.entity_type == NodeType.ORGANIZATION:
            return Organization(
                name=self.name,
                aliases=self.aliases,
                properties=self.properties,
                org_type=self.properties.get("org_type", ""),
                size=self.properties.get("size", 0),
                sector=self.properties.get("sector", ""),
                source_citations=self.source_citations
            )
        elif self.entity_type == NodeType.PLACE:
            return Place(
                name=self.name,
                aliases=self.aliases,
                properties=self.properties,
                geo_coordinates=self.properties.get("geo_coordinates"),
                place_type=self.properties.get("place_type", ""),
                population=self.properties.get("population"),
                source_citations=self.source_citations
            )
        elif self.entity_type == NodeType.CONCEPT:
            return Concept(
                name=self.name,
                aliases=self.aliases,
                properties=self.properties,
                definition=self.properties.get("definition", ""),
                domain=self.properties.get("domain", ""),
                prevalence=self.properties.get("prevalence", 0.0),
                source_citations=self.source_citations
            )
        elif self.entity_type == NodeType.EVENT:
            return Event(
                name=self.name,
                aliases=self.aliases,
                properties=self.properties,
                timestamp=self.properties.get("timestamp"),
                duration=self.properties.get("duration"),
                magnitude=self.properties.get("magnitude", 0.0),
                sentiment=self.properties.get("sentiment", 0.0),
                location_id=self.properties.get("location_id"),
                source_citations=self.source_citations
            )
        else:
            return Node(
                name=self.name,
                aliases=self.aliases,
                properties=self.properties,
                source_citations=self.source_citations
            )


@dataclass
class ExtractedRelationship:
    """Represents a relationship extracted between entities."""
    source_entity: str
    target_entity: str
    relationship_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source_citations: List[Citation] = field(default_factory=list)
    
    def to_edge(self, entity_map: Dict[str, str]) -> Optional[Edge]:
        """
        Convert to appropriate Edge subclass.
        
        Args:
            entity_map: Mapping of entity names to node IDs
        
        Returns:
            Edge object or None if entities not found
        """
        source_id = entity_map.get(self.source_entity)
        target_id = entity_map.get(self.target_entity)
        
        if not source_id or not target_id:
            logger.warning(f"Entities not found for relationship: {self.source_entity} -> {self.target_entity}")
            return None
        
        edge_type_map = {
            "influence": InfluenceEdge,
            "ownership": lambda **kwargs: Edge(
                source_id=source_id, target_id=target_id, 
                edge_type="Ownership", properties={"percentage": kwargs.get("percentage", 0.0)},
                confidence=self.confidence, source_citations=self.source_citations
            ),
            "friendship": FriendshipEdge,
            "competition": lambda **kwargs: Edge(
                source_id=source_id, target_id=target_id,
                edge_type="Competition", 
                properties={"domain": kwargs.get("domain", ""), "intensity": kwargs.get("intensity", 0.0)},
                confidence=self.confidence, source_citations=self.source_citations
            ),
            "membership": MembershipEdge,
            "causality": lambda **kwargs: Edge(
                source_id=source_id, target_id=target_id,
                edge_type="Causality",
                properties={"strength": kwargs.get("strength", 0.0)},
                confidence=self.confidence, source_citations=self.source_citations
            ),
        }
        
        edge_class = edge_type_map.get(self.relationship_type.lower())
        if not edge_class:
            # Generic edge
            return Edge(
                source_id=source_id,
                target_id=target_id,
                properties=self.properties,
                confidence=self.confidence,
                source_citations=self.source_citations
            )
        
        # Handle special cases
        if callable(edge_class) and edge_class.__name__ == "Edge":
            return edge_class(**self.properties)
        
        try:
            edge = edge_class(
                source_id=source_id,
                target_id=target_id,
                confidence=self.confidence,
                source_citations=self.source_citations,
                **self.properties
            )
            return edge
        except Exception as e:
            logger.warning(f"Failed to create edge: {e}")
            return Edge(
                source_id=source_id,
                target_id=target_id,
                properties=self.properties,
                confidence=self.confidence,
                source_citations=self.source_citations
            )


@dataclass
class ExtractionResult:
    """Complete extraction result from a document chunk."""
    entities: List[ExtractedEntity] = field(default_factory=list)
    relationships: List[ExtractedRelationship] = field(default_factory=list)
    temporal_info: Dict[str, Any] = field(default_factory=dict)
    sentiment: float = 0.0
    chunk_citation: Optional[Citation] = None


class BaseExtractor(ABC):
    """Abstract base class for semantic extractors."""
    
    @abstractmethod
    def extract(self, chunk: DocumentChunk) -> ExtractionResult:
        """Extract entities and relationships from a chunk."""
        pass
    
    @abstractmethod
    def batch_extract(self, chunks: List[DocumentChunk]) -> List[ExtractionResult]:
        """Extract from multiple chunks."""
        pass


class RuleBasedExtractor(BaseExtractor):
    """
    Simple rule-based extractor using regex patterns.
    
    This is a fallback when LLM/NLP libraries are unavailable.
    In production, this should be replaced with LLM-based extraction.
    """
    
    def __init__(self):
        import re
        self.re = re
        # Simple patterns for demonstration
        self.person_pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b')
        self.org_pattern = re.compile(r'\b([A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*\s+(?:Inc|Ltd|Corp|LLC|Company|Organization|Agency|Department))\b')
        self.date_pattern = re.compile(r'\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b')
    
    def extract(self, chunk: DocumentChunk) -> ExtractionResult:
        entities = []
        relationships = []
        
        text = chunk.content
        
        # Extract potential person names (very naive)
        for match in self.person_pattern.finditer(text):
            name = match.group(1)
            # Filter out common false positives
            if name.lower() not in ['The', 'This', 'That', 'These', 'Those']:
                entities.append(ExtractedEntity(
                    name=name,
                    entity_type=NodeType.PERSON,
                    confidence=0.5,  # Low confidence for rule-based
                    source_citations=[chunk.citation]
                ))
        
        # Extract potential organizations
        for match in self.org_pattern.finditer(text):
            name = match.group(1)
            entities.append(ExtractedEntity(
                name=name,
                entity_type=NodeType.ORGANIZATION,
                confidence=0.6,
                source_citations=[chunk.citation]
            ))
        
        # Extract dates
        dates = []
        for match in self.date_pattern.finditer(text):
            dates.append(match.group(1))
        
        # Simple sentiment based on keyword counting
        positive_words = {'good', 'great', 'excellent', 'positive', 'success', 'growth', 'improve'}
        negative_words = {'bad', 'poor', 'negative', 'failure', 'decline', 'crisis', 'problem'}
        
        words = text.lower().split()
        pos_count = sum(1 for w in words if w in positive_words)
        neg_count = sum(1 for w in words if w in negative_words)
        total = pos_count + neg_count
        sentiment = (pos_count - neg_count) / max(total, 1)
        
        return ExtractionResult(
            entities=entities,
            relationships=relationships,
            temporal_info={"dates": dates},
            sentiment=sentiment,
            chunk_citation=chunk.citation
        )
    
    def batch_extract(self, chunks: List[DocumentChunk]) -> List[ExtractionResult]:
        return [self.extract(chunk) for chunk in chunks]


class LLMBasedExtractor(BaseExtractor):
    """
    LLM-based extractor using structured Pydantic output schemas.
    
    Requires an LLM client (OpenAI, Anthropic, local model via Ollama, etc.)
    Falls back to RuleBasedExtractor if LLM is unavailable.
    """
    
    def __init__(
        self,
        llm_client: Optional[Any] = None,
        model_name: str = "gpt-4",
        fallback_to_rules: bool = True
    ):
        self.llm_client = llm_client
        self.model_name = model_name
        self.fallback_extractor = RuleBasedExtractor() if fallback_to_rules else None
        
        if not llm_client:
            logger.warning("No LLM client provided. Using rule-based fallback.")
    
    def extract(self, chunk: DocumentChunk) -> ExtractionResult:
        if not self.llm_client:
            if self.fallback_extractor:
                return self.fallback_extractor.extract(chunk)
            raise RuntimeError("No extractor available")
        
        # Construct prompt for structured extraction
        prompt = self._build_extraction_prompt(chunk.content)
        
        try:
            # This is a placeholder for actual LLM API call
            # In production, use proper API with structured output
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert entity and relationship extractor."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            import json
            result_data = json.loads(response.choices[0].message.content)
            return self._parse_llm_response(result_data, chunk.citation)
            
        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}")
            if self.fallback_extractor:
                return self.fallback_extractor.extract(chunk)
            raise
    
    def batch_extract(self, chunks: List[DocumentChunk]) -> List[ExtractionResult]:
        # Could be parallelized in production
        return [self.extract(chunk) for chunk in chunks]
    
    def _build_extraction_prompt(self, text: str) -> str:
        return f"""
Extract entities and relationships from the following text.

Return JSON with this exact structure:
{{
    "entities": [
        {{
            "name": "Entity Name",
            "type": "Person|Organization|Place|Concept|Event",
            "aliases": [],
            "properties": {{}},
            "confidence": 0.95
        }}
    ],
    "relationships": [
        {{
            "source": "Entity A",
            "target": "Entity B",
            "type": "influence|ownership|friendship|competition|membership|causality",
            "properties": {{}},
            "confidence": 0.9
        }}
    ],
    "temporal_info": {{
        "dates": [],
        "sequences": []
    }},
    "sentiment": 0.5
}}

Text to analyze:
{text[:4000]}  # Truncate to avoid token limits
"""
    
    def _parse_llm_response(self, data: Dict[str, Any], citation: Citation) -> ExtractionResult:
        entities = []
        for ent_data in data.get("entities", []):
            entity_type = NodeType(ent_data.get("type", "Concept"))
            entities.append(ExtractedEntity(
                name=ent_data.get("name", ""),
                entity_type=entity_type,
                aliases=ent_data.get("aliases", []),
                properties=ent_data.get("properties", {}),
                confidence=ent_data.get("confidence", 0.8),
                source_citations=[citation]
            ))
        
        relationships = []
        for rel_data in data.get("relationships", []):
            relationships.append(ExtractedRelationship(
                source_entity=rel_data.get("source", ""),
                target_entity=rel_data.get("target", ""),
                relationship_type=rel_data.get("type", "influence"),
                properties=rel_data.get("properties", {}),
                confidence=rel_data.get("confidence", 0.8),
                source_citations=[citation]
            ))
        
        return ExtractionResult(
            entities=entities,
            relationships=relationships,
            temporal_info=data.get("temporal_info", {}),
            sentiment=data.get("sentiment", 0.0),
            chunk_citation=citation
        )


class HybridExtractor(BaseExtractor):
    """
    Combines multiple extraction strategies with confidence weighting.
    
    Uses LLM when available, falls back to transformers/spaCy, 
    and finally to rule-based methods.
    """
    
    def __init__(
        self,
        llm_extractor: Optional[LLMBasedExtractor] = None,
        transformer_model: Optional[str] = None,
        use_spacy: bool = False
    ):
        self.llm_extractor = llm_extractor
        self.transformer_model = transformer_model
        self.use_spacy = use_spacy
        self.rule_extractor = RuleBasedExtractor()
        
        # Load spaCy if requested
        self.nlp = None
        if use_spacy:
            try:
                import spacy
                self.nlp = spacy.load("en_core_web_sm")
            except ImportError:
                logger.warning("spaCy not installed")
            except OSError:
                logger.warning("spaCy model not downloaded. Run: python -m spacy download en_core_web_sm")
    
    def extract(self, chunk: DocumentChunk) -> ExtractionResult:
        # Try LLM first
        if self.llm_extractor and self.llm_extractor.llm_client:
            try:
                return self.llm_extractor.extract(chunk)
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}")
        
        # Try transformer-based extraction
        if self.transformer_model:
            try:
                return self._extract_with_transformers(chunk)
            except Exception as e:
                logger.warning(f"Transformer extraction failed: {e}")
        
        # Try spaCy
        if self.nlp:
            try:
                return self._extract_with_spacy(chunk)
            except Exception as e:
                logger.warning(f"spaCy extraction failed: {e}")
        
        # Fall back to rules
        return self.rule_extractor.extract(chunk)
    
    def _extract_with_transformers(self, chunk: DocumentChunk) -> ExtractionResult:
        """Use HuggingFace transformers for NER."""
        from transformers import pipeline
        
        ner_pipeline = pipeline("ner", model=self.transformer_model)
        entities_raw = ner_pipeline(chunk.content)
        
        entities = []
        for ent in entities_raw:
            entities.append(ExtractedEntity(
                name=ent['word'],
                entity_type=self._map_transformer_label(ent['entity']),
                confidence=ent['score'],
                source_citations=[chunk.citation]
            ))
        
        return ExtractionResult(
            entities=entities,
            relationships=[],
            temporal_info={},
            sentiment=0.0,
            chunk_citation=chunk.citation
        )
    
    def _extract_with_spacy(self, chunk: DocumentChunk) -> ExtractionResult:
        """Use spaCy for NER."""
        doc = self.nlp(chunk.content)
        
        entities = []
        for ent in doc.ents:
            entities.append(ExtractedEntity(
                name=ent.text,
                entity_type=self._map_spacy_label(ent.label_),
                confidence=0.8,
                source_citations=[chunk.citation]
            ))
        
        return ExtractionResult(
            entities=entities,
            relationships=[],
            temporal_info={},
            sentiment=0.0,
            chunk_citation=chunk.citation
        )
    
    def _map_transformer_label(self, label: str) -> NodeType:
        mapping = {
            'PER': NodeType.PERSON,
            'PERSON': NodeType.PERSON,
            'ORG': NodeType.ORGANIZATION,
            'LOC': NodeType.PLACE,
            'GPE': NodeType.PLACE,
            'MISC': NodeType.CONCEPT,
        }
        return mapping.get(label, NodeType.CONCEPT)
    
    def _map_spacy_label(self, label: str) -> NodeType:
        mapping = {
            'PERSON': NodeType.PERSON,
            'ORG': NodeType.ORGANIZATION,
            'GPE': NodeType.PLACE,
            'LOC': NodeType.PLACE,
            'DATE': NodeType.EVENT,
            'EVENT': NodeType.EVENT,
        }
        return mapping.get(label, NodeType.CONCEPT)
    
    def batch_extract(self, chunks: List[DocumentChunk]) -> List[ExtractionResult]:
        return [self.extract(chunk) for chunk in chunks]
