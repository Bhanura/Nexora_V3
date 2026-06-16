"""
Document retrieval for RAG system. 
Finds relevant documents based on semantic similarity. 
"""

from typing import List, Dict, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent. parent. parent))

from nexora001.storage.mongodb import get_storage
from nexora001.processors.embeddings import get_embedding_generator


class DocumentRetriever:
    """
    Retrieves relevant documents for a given query.
    """
    
    def __init__(
        self,
        embedding_provider: str = "sentence_transformers",
        top_k: int = 5,
        min_similarity: float = 0.3
    ):
        """
        Initialize the retriever.
        
        Args:
            embedding_provider: Embedding provider to use
            top_k: Number of documents to retrieve
            min_similarity: Minimum similarity threshold
        """
        self.embedding_generator = get_embedding_generator(embedding_provider)
        self.top_k = top_k
        self.min_similarity = min_similarity
    
    def retrieve(self, query: str, client_id: str) -> List[Dict]:
        """
        Retrieve relevant documents for a query. 
        
        Args:
            query: User's question
            
        Returns:
            List of relevant document chunks with metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)
        
        # Debug logging
        print(f"🔍 Searching for client_id: {client_id}")
        print(f"   Query: {query[:100]}...")
        print(f"   Min similarity: {self.min_similarity}")
        
        # Search for similar documents
        with get_storage() as storage:
            results = storage.vector_search(
                client_id=client_id,
                query_embedding=query_embedding,
                limit=self.top_k,
                min_score=self.min_similarity
            )
    # return results

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'content': result. get('content', ''),
                'score': result.get('similarity_score', 0.0),
                'metadata': result.get('metadata', {}),
                'id': str(result.get('_id', ''))
            })
        
        return formatted_results
    
    def retrieve_with_context(self, query: str, client_id: str) -> Dict:
        """
        Retrieve documents and prepare context for LLM.
        
        Args:
            query: User's question
            
        Returns:
            Dictionary with context and sources
        """
        results = self.retrieve(query, client_id)
        
        if not results:
            return {
                'context': '',
                'sources': [],
                'found_documents': 0
            }
        
        # Build context string with more metadata
        context_parts = []
        sources = []
        
        for i, result in enumerate(results, 1):
            content = result['content']
            metadata = result['metadata']
            score = result['score']
            
            # Optimize: Truncate very long content to reduce LLM processing time
            max_chars = 800  # Limit each chunk to 800 chars
            if len(content) > max_chars:
                content = content[:max_chars] + "..."
            
            # Add to context with better formatting
            title = metadata.get('title', 'Unknown')
            url = metadata.get('source_url', 'Unknown')
            
            # Simplified context format - less tokens
            context_parts.append(
                f"[{i}] {title}\n{content}\n"
            )
            
            # Add to sources
            sources.append({
                'number': i,
                'title': title,
                'url': url,
                'score': score,
                'chunk_index': metadata.get('chunk_index', 0)
            })
        
        context = "\n" + "="*80 + "\n".join(context_parts)
        
        return {
            'context': context,
            'sources': sources,
            'found_documents': len(results)
        }