"""
Qdrant vector storage for fast similarity search.
Self-hosted alternative to MongoDB Atlas Vector Search.
"""

from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, 
    FieldCondition, MatchValue
)
import os
from dotenv import load_dotenv
import time

load_dotenv()


class QdrantStorage:
    """
    Qdrant vector database client for fast similarity search.
    """
    
    def __init__(self, url: Optional[str] = None):
        """
        Initialize Qdrant client.
        
        Args:
            url: Qdrant server URL (default: from env or localhost)
        """
        self.url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.client = QdrantClient(url=self.url)
        self.collection_name = "nexora_embeddings"
        
        # Create collection if it doesn't exist
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                print(f"Creating Qdrant collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,  # all-MiniLM-L6-v2 dimension
                        distance=Distance.COSINE
                    )
                )
                print(f"✓ Collection created: {self.collection_name}")
            else:
                print(f"✓ Collection exists: {self.collection_name}")
                
        except Exception as e:
            print(f"Error ensuring collection: {e}")
    
    def store_embedding(
        self,
        doc_id: str,
        embedding: List[float],
        client_id: str,
        content: str,
        metadata: Dict
    ) -> bool:
        """
        Store a document embedding in Qdrant.
        
        Args:
            doc_id: Unique document ID (MongoDB ObjectId)
            embedding: 384-dim embedding vector
            client_id: Client ID for multi-tenancy
            content: Document content
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        try:
            point = PointStruct(
                id=doc_id,
                vector=embedding,
                payload={
                    "client_id": client_id,
                    "content": content,
                    "metadata": metadata
                }
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            return True
            
        except Exception as e:
            print(f"Error storing embedding: {e}")
            return False
    
    def vector_search(
        self,
        client_id: str,
        query_embedding: List[float],
        limit: int = 5,
        min_score: float = 0.0
    ) -> List[Dict]:
        """
        Fast vector similarity search.
        
        Args:
            client_id: Filter by client ID
            query_embedding: Query vector
            limit: Number of results
            min_score: Minimum similarity score
            
        Returns:
            List of similar documents with scores
        """
        start = time.time()
        
        try:
            # Search with client_id filter
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=min_score,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="client_id",
                            match=MatchValue(value=client_id)
                        )
                    ]
                )
            )
            
            elapsed = time.time() - start
            
            # Format results
            formatted = []
            for hit in results:
                formatted.append({
                    "_id": hit.id,
                    "content": hit.payload.get("content", ""),
                    "metadata": hit.payload.get("metadata", {}),
                    "similarity_score": hit.score
                })
            
            print(f"✅ Qdrant Vector Search: {len(formatted)} results in {elapsed:.3f}s")
            return formatted
            
        except Exception as e:
            print(f"❌ Qdrant search error: {e}")
            return []
    
    def delete_by_client(self, client_id: str) -> int:
        """Delete all embeddings for a client."""
        try:
            result = self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="client_id",
                            match=MatchValue(value=client_id)
                        )
                    ]
                )
            )
            return result
        except Exception as e:
            print(f"Error deleting client embeddings: {e}")
            return 0
    
    def count_vectors(self, client_id: Optional[str] = None) -> int:
        """Count total vectors (optionally filtered by client)."""
        try:
            result = self.client.count(
                collection_name=self.collection_name,
                count_filter=Filter(
                    must=[
                        FieldCondition(
                            key="client_id",
                            match=MatchValue(value=client_id)
                        )
                    ]
                ) if client_id else None
            )
            return result.count
        except Exception as e:
            print(f"Error counting vectors: {e}")
            return 0


# Singleton instance
_qdrant_instance = None

def get_qdrant() -> QdrantStorage:
    """Get or create Qdrant storage instance."""
    global _qdrant_instance
    if _qdrant_instance is None:
        _qdrant_instance = QdrantStorage()
    return _qdrant_instance
