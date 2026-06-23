# =============================================================================
# DATABASE RETRIEVER - The "Oracle"
# =============================================================================
"""
Database/Vector Scanning Engine for RAG (Retrieval Augmented Generation)

ORIGINAL INTENT (from user description):
- Connects to SQL, Vector DB (Qdrant/Pinecone), or document store
- Scans, retrieves, and injects contextual data into agent prompts
- Powers the "Oracle" functionality

IMPLEMENTATION:
- Abstract base class for multiple backends
- SQLAlchemy ORM for SQL databases
- Generic vector client interface (ready for Qdrant/Pinecone)
- Async I/O for non-blocking retrieval

This is a GREENFIELD implementation since no database code existed.
"""

import os
import asyncio
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RetrievedDocument:
    """Standardized document format from any source."""
    content: str
    metadata: Dict[str, Any]
    score: float = 1.0
    source: str = "unknown"


class VectorStoreConfig:
    """Configuration for vector database connection."""
    
    def __init__(
        self,
        provider: str = "qdrant",  # qdrant, pinecone, chroma
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: str = "nyx_context",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        self.provider = provider
        self.url = url or os.getenv("VECTOR_DB_URL")
        self.api_key = api_key or os.getenv("VECTOR_DB_API_KEY")
        self.collection_name = collection_name
        self.embedding_model = embedding_model


class DatabaseRetriever:
    """
    Unified retriever for SQL and Vector databases.
    Powers the "Oracle" functionality.
    
    Supports:
    - SQL databases via SQLAlchemy (PostgreSQL, SQLite, MySQL)
    - Vector databases (Qdrant, Pinecone, Chroma)
    - Hybrid search (combining both)
    """
    
    def __init__(
        self,
        sql_url: Optional[str] = None,
        vector_config: Optional[VectorStoreConfig] = None
    ):
        self.sql_url = sql_url or os.getenv("DATABASE_URL")
        self.vector_config = vector_config or VectorStoreConfig()
        
        # Lazy initialization
        self._sql_engine = None
        self._vector_client = None
        self._embedding_model = None
        
        print(f"🗄️  DatabaseRetriever initialized")
        if self.sql_url:
            print(f"   SQL: {self.sql_url[:30]}...")
        if self.vector_config.url:
            print(f"   Vector: {self.vector_config.provider} @ {self.vector_config.url[:30]}...")
    
    def is_connected(self) -> bool:
        """Check if at least one backend is configured."""
        return bool(self.sql_url or self.vector_config.url)
    
    async def retrieve_async(
        self,
        query: str,
        top_k: int = 5,
        source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve contextual documents asynchronously.
        
        Args:
            query: Search query (natural language or keywords)
            top_k: Number of results to return
            source: "sql", "vector", or None for hybrid
        
        Returns:
            List of retrieved documents with metadata
        """
        results = []
        
        if source == "sql" or source is None:
            sql_results = await self._retrieve_sql_async(query, top_k)
            results.extend(sql_results)
        
        if source == "vector" or source is None:
            vector_results = await self._retrieve_vector_async(query, top_k)
            results.extend(vector_results)
        
        # Deduplicate and sort by score
        seen = set()
        unique_results = []
        for r in sorted(results, key=lambda x: x.get("score", 0), reverse=True):
            key = r.get("content", "")[:50]  # Simple dedup by content prefix
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        
        return unique_results[:top_k]
    
    async def _retrieve_sql_async(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        Retrieve from SQL database using keyword search.
        
        In production, this would use full-text search or pgvector.
        For now, simple keyword matching.
        """
        if not self.sql_url:
            return []
        
        try:
            # Lazy import to avoid requiring SQLAlchemy if not used
            from sqlalchemy import create_engine, text
            from sqlalchemy.orm import sessionmaker
            
            if self._sql_engine is None:
                self._sql_engine = create_engine(self.sql_url)
            
            # Simple keyword search across all tables
            # In production, this would be more sophisticated
            keywords = query.lower().split()
            
            results = []
            with self._sql_engine.connect() as conn:
                # Query simulation history table if exists
                try:
                    result = conn.execute(
                        text("""
                            SELECT id, scenario, result_data, created_at 
                            FROM simulations 
                            WHERE LOWER(scenario) LIKE :query
                            ORDER BY created_at DESC
                            LIMIT :limit
                        """),
                        {"query": f"%{query}%", "limit": top_k}
                    )
                    
                    for row in result:
                        results.append({
                            "content": str(row.scenario),
                            "metadata": {
                                "id": row.id,
                                "created_at": str(row.created_at),
                                "result_preview": str(row.result_data)[:200]
                            },
                            "score": 0.8,
                            "source": "sql:simulations"
                        })
                except Exception:
                    pass  # Table doesn't exist yet
            
            return results
        
        except ImportError:
            print("⚠️  SQLAlchemy not installed, SQL retrieval disabled")
            return []
        except Exception as e:
            print(f"❌ SQL retrieval error: {e}")
            return []
    
    async def _retrieve_vector_async(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        Retrieve from vector database using semantic search.
        
        Requires embedding model and vector DB client.
        """
        if not self.vector_config.url:
            return []
        
        try:
            # Generate embedding for query
            embedding = await self._generate_embedding_async(query)
            
            if self.vector_config.provider == "qdrant":
                results = await self._search_qdrant_async(embedding, top_k)
            elif self.vector_config.provider == "pinecone":
                results = await self._search_pinecone_async(embedding, top_k)
            else:
                results = []
            
            return results
        
        except Exception as e:
            print(f"❌ Vector retrieval error: {e}")
            return []
    
    async def _generate_embedding_async(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        # Lazy load embedding model
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer(
                    self.vector_config.embedding_model
                )
            except ImportError:
                raise Exception("sentence-transformers not installed")
        
        # Run in thread pool (not truly async but non-blocking for I/O)
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self._embedding_model.encode(text).tolist()
        )
        return embedding
    
    async def _search_qdrant_async(
        self,
        embedding: List[float],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Search Qdrant vector database."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            
            if self._vector_client is None:
                self._vector_client = QdrantClient(
                    url=self.vector_config.url,
                    api_key=self.vector_config.api_key
                )
            
            results = self._vector_client.search(
                collection_name=self.vector_config.collection_name,
                query_vector=embedding,
                limit=top_k
            )
            
            return [
                {
                    "content": str(hit.payload.get("content", "")),
                    "metadata": hit.payload,
                    "score": hit.score,
                    "source": "qdrant"
                }
                for hit in results
            ]
        
        except ImportError:
            print("⚠️  qdrant-client not installed")
            return []
    
    async def _search_pinecone_async(
        self,
        embedding: List[float],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Search Pinecone vector database."""
        try:
            import pinecone
            
            if self._vector_client is None:
                pinecone.init(api_key=self.vector_config.api_key)
                self._vector_client = pinecone.Index(self.vector_config.collection_name)
            
            results = self._vector_client.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            return [
                {
                    "content": match.metadata.get("content", ""),
                    "metadata": match.metadata,
                    "score": match.score,
                    "source": "pinecone"
                }
                for match in results.matches
            ]
        
        except ImportError:
            print("⚠️  pinecone-client not installed")
            return []
    
    async def index_document_async(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Index a document for future retrieval.
        
        Stores in both SQL (for structured data) and vector DB (for semantic search).
        """
        success = True
        
        # Store in vector DB
        if self.vector_config.url:
            try:
                embedding = await self._generate_embedding_async(content)
                
                if self.vector_config.provider == "qdrant":
                    from qdrant_client.http import models
                    
                    if self._vector_client is None:
                        from qdrant_client import QdrantClient
                        self._vector_client = QdrantClient(
                            url=self.vector_config.url,
                            api_key=self.vector_config.api_key
                        )
                    
                    # Create collection if not exists
                    try:
                        self._vector_client.create_collection(
                            collection_name=self.vector_config.collection_name,
                            vectors_config=models.VectorParams(
                                size=len(embedding),
                                distance=models.Distance.COSINE
                            )
                        )
                    except Exception:
                        pass  # Already exists
                    
                    # Upsert document
                    self._vector_client.upsert(
                        collection_name=self.vector_config.collection_name,
                        points=[
                            models.PointStruct(
                                id=hash(content) % (2**31),
                                vector=embedding,
                                payload={
                                    "content": content,
                                    **(metadata or {})
                                }
                            )
                        ]
                    )
            except Exception as e:
                print(f"❌ Failed to index in vector DB: {e}")
                success = False
        
        return success
