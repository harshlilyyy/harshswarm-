# =============================================================================
# DOCUMENT LOADER — Seed Material Ingestion
# =============================================================================
"""
Handles ingestion of seed materials:
- News articles
- Policy drafts
- Research reports
- Books and fiction
- PDFs
- Structured datasets
- Web content
- Transcripts
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
import hashlib


@dataclass
class SeedMaterial:
    """A piece of ingested seed material."""
    id: str
    title: str
    content: str
    source_type: str  # news, policy, research, book, pdf, dataset, web, transcript
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_entities: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "source_type": self.source_type,
            "metadata": self.metadata,
            "entity_count": len(self.extracted_entities),
            "created_at": self.created_at.isoformat()
        }


class DocumentLoader:
    """
    Loads and processes various document types for world model initialization.
    
    Features:
    - Multiple format support (text, PDF, JSON, CSV)
    - Entity extraction
    - Content summarization hooks
    - Metadata preservation
    """
    
    def __init__(self):
        self.loaded_materials: List[SeedMaterial] = []
    
    def load_text(self, text: str, title: str = "Untitled",
                  metadata: Optional[Dict] = None) -> SeedMaterial:
        """Load plain text content."""
        material = SeedMaterial(
            id=self._generate_id(text),
            title=title,
            content=text,
            source_type="text",
            metadata=metadata or {}
        )
        self.loaded_materials.append(material)
        return material
    
    def load_json(self, json_data: Dict, title: str = "Untitled") -> SeedMaterial:
        """Load structured JSON data."""
        import json
        content = json.dumps(json_data, indent=2)
        material = SeedMaterial(
            id=self._generate_id(content),
            title=title,
            content=content,
            source_type="dataset",
            metadata={"structured": True}
        )
        self.loaded_materials.append(material)
        return material
    
    def extract_simple_entities(self, material: SeedMaterial) -> List[Dict]:
        """
        Perform simple entity extraction from text.
        
        This is a placeholder - full implementation would use NLP.
        """
        entities = []
        content = material.content
        
        # Simple pattern matching (placeholder for real NLP)
        # Look for capitalized words that might be names
        import re
        potential_names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content[:1000])
        
        for name in set(potential_names[:20]):  # Limit to first 20 unique
            if len(name) > 2 and name not in ['The', 'This', 'That', 'These']:
                entities.append({
                    "name": name,
                    "type": "PERSON_OR_ORG",
                    "confidence": 0.5
                })
        
        material.extracted_entities = entities
        return entities
    
    def _generate_id(self, content: str) -> str:
        """Generate unique ID from content hash."""
        return hashlib.md5(content.encode()).hexdigest()[:16]
