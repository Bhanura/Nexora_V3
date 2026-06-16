"""
Hybrid storage: MongoDB for documents + Qdrant for vector search.
Best of both worlds - self-hosted and fast!
"""

from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Choose your vector search backend
USE_QDRANT = os.getenv("USE_QDRANT", "false").lower() == "true"

if USE_QDRANT:
    from nexora001.storage.qdrant_storage import get_qdrant
    print("✓ Using Qdrant for vector search (self-hosted)")
else:
    print("✓ Using MongoDB Atlas for vector search")


def store_document_with_vector(
    client_id: str,
    doc_id: str,
    content: str,
    embedding: List[float],
    metadata: Dict,
    mongo_storage
) -> bool:
    """
    Store document in MongoDB + embedding in Qdrant (if enabled).
    
    Args:
        client_id: Client ID
        doc_id: MongoDB document ID
        content: Document content
        embedding: 384-dim embedding vector
        metadata: Document metadata
        mongo_storage: MongoDB storage instance
        
    Returns:
        True if successful
    """
    if USE_QDRANT:
        # Store embedding in Qdrant for fast search
        qdrant = get_qdrant()
        return qdrant.store_embedding(
            doc_id=doc_id,
            embedding=embedding,
            client_id=client_id,
            content=content,
            metadata=metadata
        )
    return True


def vector_search(
    client_id: str,
    query_embedding: List[float],
    limit: int = 5,
    min_score: float = 0.0,
    mongo_storage=None
) -> List[Dict]:
    """
    Smart vector search: Qdrant if available, else MongoDB/Python.
    
    Args:
        client_id: Client ID for multi-tenancy
        query_embedding: Query vector
        limit: Number of results
        min_score: Minimum similarity score
        mongo_storage: MongoDB instance (fallback)
        
    Returns:
        List of similar documents
    """
    if USE_QDRANT:
        # Use Qdrant (fast, self-hosted)
        qdrant = get_qdrant()
        return qdrant.vector_search(
            client_id=client_id,
            query_embedding=query_embedding,
            limit=limit,
            min_score=min_score
        )
    else:
        # Use MongoDB (Atlas or Python fallback)
        if mongo_storage:
            return mongo_storage.vector_search(
                client_id=client_id,
                query_embedding=query_embedding,
                limit=limit,
                min_score=min_score
            )
        return []
