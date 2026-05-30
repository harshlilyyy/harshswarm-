"""
MiroFish Layer 1: Ingestion Pipeline

Handles parsing of various document formats (PDF, HTML, text, CSV, etc.)
and chunks them for processing with provenance tracking.
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from .schema import Citation

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """A chunk of text extracted from a source document."""
    content: str
    citation: Citation
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseParser(ABC):
    """Abstract base class for document parsers."""
    
    @abstractmethod
    def parse(self, source: Union[str, Path, bytes]) -> Iterator[DocumentChunk]:
        """Parse a document and yield chunks."""
        pass
    
    def _create_citation(
        self,
        source_id: str,
        source_type: str,
        chunk_id: str,
        page_number: Optional[int] = None,
        url: Optional[str] = None,
        confidence: float = 1.0
    ) -> Citation:
        return Citation(
            source_id=source_id,
            source_type=source_type,
            chunk_id=chunk_id,
            page_number=page_number,
            url=url,
            retrieval_timestamp=datetime.utcnow(),
            extraction_confidence=confidence
        )
    
    def _generate_chunk_id(self, content: str, source_id: str, index: int) -> str:
        """Generate a unique chunk ID based on content hash."""
        hash_input = f"{source_id}:{index}:{content}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


class TextParser(BaseParser):
    """Parser for plain text files."""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def parse(self, source: Union[str, Path, bytes]) -> Iterator[DocumentChunk]:
        if isinstance(source, Path):
            source_id = str(source)
            source_type = "text_file"
            content = source.read_text(encoding="utf-8")
        elif isinstance(source, bytes):
            source_id = hashlib.sha256(source).hexdigest()[:16]
            source_type = "text_bytes"
            content = source.decode("utf-8")
        else:
            source_id = hashlib.sha256(source.encode()).hexdigest()[:16]
            source_type = "text_string"
            content = source
        
        chunks = self._chunk_text(content)
        
        for i, chunk_content in enumerate(chunks):
            chunk_id = self._generate_chunk_id(chunk_content, source_id, i)
            citation = self._create_citation(
                source_id=source_id,
                source_type=source_type,
                chunk_id=chunk_id,
                confidence=0.95
            )
            yield DocumentChunk(
                content=chunk_content,
                citation=citation,
                metadata={"char_start": i * (self.chunk_size - self.overlap)}
            )
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > self.chunk_size // 2:
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - self.overlap
        
        return chunks


class PDFParser(BaseParser):
    """
    Parser for PDF files.
    
    Uses PyMuPDF (fitz) if available, otherwise falls back to pypdf.
    For production, consider unstructured.io for better layout preservation.
    """
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._fitz = None
        self._pypdf = None
        
        # Try to import optional dependencies
        try:
            import fitz  # PyMuPDF
            self._fitz = fitz
        except ImportError:
            logger.warning("PyMuPDF not installed. PDF parsing will use fallback.")
        
        if not self._fitz:
            try:
                from pypdf import PdfReader
                self._pypdf = PdfReader
            except ImportError:
                logger.warning("pypdf not installed. PDF parsing unavailable.")
    
    def parse(self, source: Union[str, Path]) -> Iterator[DocumentChunk]:
        if not (self._fitz or self._pypdf):
            raise RuntimeError("No PDF library available. Install PyMuPDF or pypdf.")
        
        source_path = Path(source) if isinstance(source, str) else source
        source_id = str(source_path.absolute())
        
        if self._fitz:
            yield from self._parse_with_fitz(source_path, source_id)
        else:
            yield from self._parse_with_pypdf(source_path, source_id)
    
    def _parse_with_fitz(self, path: Path, source_id: str) -> Iterator[DocumentChunk]:
        doc = self._fitz.open(path)
        chunk_index = 0
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            if not text.strip():
                continue
            
            # Create chunks from page text
            chunks = self._chunk_text(text)
            for chunk_content in chunks:
                chunk_id = self._generate_chunk_id(chunk_content, source_id, chunk_index)
                citation = self._create_citation(
                    source_id=source_id,
                    source_type="pdf",
                    chunk_id=chunk_id,
                    page_number=page_num + 1,
                    confidence=0.9
                )
                yield DocumentChunk(
                    content=chunk_content,
                    citation=citation,
                    metadata={"page": page_num + 1}
                )
                chunk_index += 1
        
        doc.close()
    
    def _parse_with_pypdf(self, path: Path, source_id: str) -> Iterator[DocumentChunk]:
        reader = self._pypdf(path)
        chunk_index = 0
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text or not text.strip():
                continue
            
            chunks = self._chunk_text(text)
            for chunk_content in chunks:
                chunk_id = self._generate_chunk_id(chunk_content, source_id, chunk_index)
                citation = self._create_citation(
                    source_id=source_id,
                    source_type="pdf",
                    chunk_id=chunk_id,
                    page_number=page_num + 1,
                    confidence=0.85
                )
                yield DocumentChunk(
                    content=chunk_content,
                    citation=citation,
                    metadata={"page": page_num + 1}
                )
                chunk_index += 1
    
    def _chunk_text(self, text: str) -> List[str]:
        """Simple chunking strategy for PDF text."""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk.strip())
            start = end - self.overlap
        
        return chunks


class HTMLParser(BaseParser):
    """
    Parser for HTML/web content.
    
    Uses BeautifulSoup if available.
    """
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._bs4 = None
        
        try:
            from bs4 import BeautifulSoup
            self._bs4 = BeautifulSoup
        except ImportError:
            logger.warning("BeautifulSoup not installed. HTML parsing unavailable.")
    
    def parse(self, source: Union[str, Path]) -> Iterator[DocumentChunk]:
        if not self._bs4:
            raise RuntimeError("BeautifulSoup not installed.")
        
        if isinstance(source, (str, Path)) and Path(source).exists():
            path = Path(source)
            source_id = str(path.absolute())
            source_type = "html_file"
            content = path.read_text(encoding="utf-8")
        else:
            source_id = hashlib.sha256(str(source).encode()).hexdigest()[:16]
            source_type = "html_string"
            content = str(source)
        
        soup = self._bs4(content, 'html.parser')
        
        # Remove script and style elements
        for tag in soup(['script', 'style']):
            tag.decompose()
        
        text = soup.get_text(separator='\n')
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = '\n'.join(lines)
        
        chunks = self._chunk_text(clean_text)
        for i, chunk_content in enumerate(chunks):
            chunk_id = self._generate_chunk_id(chunk_content, source_id, i)
            citation = self._create_citation(
                source_id=source_id,
                source_type=source_type,
                chunk_id=chunk_id,
                url=source_id if source_type == "html_string" else None,
                confidence=0.85
            )
            yield DocumentChunk(
                content=chunk_content,
                citation=citation,
                metadata={}
            )
    
    def _chunk_text(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk.strip())
            start = end - self.overlap
        
        return chunks


class CSVParser(BaseParser):
    """Parser for tabular data (CSV, TSV)."""
    
    def __init__(self, delimiter: str = ','):
        self.delimiter = delimiter
    
    def parse(self, source: Union[str, Path]) -> Iterator[DocumentChunk]:
        import csv
        
        if isinstance(source, (str, Path)) and Path(source).exists():
            path = Path(source)
            source_id = str(path.absolute())
            source_type = "csv_file"
            file_obj = open(path, 'r', encoding='utf-8')
            should_close = True
        else:
            source_id = hashlib.sha256(str(source).encode()).hexdigest()[:16]
            source_type = "csv_string"
            from io import StringIO
            file_obj = StringIO(source)
            should_close = False
        
        try:
            reader = csv.DictReader(file_obj, delimiter=self.delimiter)
            headers = reader.fieldnames or []
            
            for row_idx, row in enumerate(reader):
                # Convert row to natural language representation
                row_text = ", ".join(f"{k}: {v}" for k, v in row.items() if v)
                
                chunk_id = self._generate_chunk_id(row_text, source_id, row_idx)
                citation = self._create_citation(
                    source_id=source_id,
                    source_type=source_type,
                    chunk_id=chunk_id,
                    confidence=0.95
                )
                yield DocumentChunk(
                    content=row_text,
                    citation=citation,
                    metadata={"row_index": row_idx, "headers": headers}
                )
        finally:
            if should_close:
                file_obj.close()


class IngestionPipeline:
    """
    Main pipeline orchestrating document ingestion.
    
    Routes documents to appropriate parsers based on type.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 200,
        parsers: Optional[Dict[str, BaseParser]] = None
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.parsers = parsers or self._default_parsers()
    
    def _default_parsers(self) -> Dict[str, BaseParser]:
        return {
            "text": TextParser(self.chunk_size, self.overlap),
            "txt": TextParser(self.chunk_size, self.overlap),
            "pdf": PDFParser(self.chunk_size, self.overlap),
            "html": HTMLParser(self.chunk_size, self.overlap),
            "htm": HTMLParser(self.chunk_size, self.overlap),
            "csv": CSVParser(),
        }
    
    def ingest(self, source: Union[str, Path], source_type: Optional[str] = None) -> Iterator[DocumentChunk]:
        """
        Ingest a document and yield chunks.
        
        Args:
            source: Path to file or content string
            source_type: Optional hint for parser selection
        
        Yields:
            DocumentChunk objects with content and provenance
        """
        path = Path(source) if isinstance(source, (str, Path)) else None
        
        if source_type is None and path and path.exists():
            source_type = path.suffix.lstrip('.').lower()
        elif source_type is None:
            source_type = "text"  # Default to text parser
        
        parser = self.parsers.get(source_type)
        if not parser:
            # Fallback to text parser
            logger.warning(f"No parser for type '{source_type}', using text parser")
            parser = TextParser(self.chunk_size, self.overlap)
        
        yield from parser.parse(source)
    
    def ingest_batch(
        self,
        sources: List[Union[str, Path]],
        source_types: Optional[List[str]] = None
    ) -> Iterator[DocumentChunk]:
        """Ingest multiple documents."""
        if source_types is None:
            source_types = [None] * len(sources)
        
        for source, source_type in zip(sources, source_types):
            yield from self.ingest(source, source_type)
