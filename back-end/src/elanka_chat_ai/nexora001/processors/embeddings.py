"""
Embedding generation for Nexora001.
Supports both local (sentence-transformers) and API-based embeddings.
"""

from typing import List, Optional, Union, Dict
import os
import numpy as np
from enum import Enum
import hashlib
import time


class EmbeddingProvider(Enum):
    """Available embedding providers."""
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    GOOGLE = "google"
    OPENAI = "openai"


class EmbeddingGenerator:
    """
    Generate embeddings for text chunks.
    
    Supports multiple embedding providers:
    - sentence-transformers (local, free)
    - Google Gemini API
    - OpenAI API
    """
    
    def __init__(
        self,
        provider: EmbeddingProvider = EmbeddingProvider.SENTENCE_TRANSFORMERS,
        model_name: Optional[str] = None
    ):
        """
        Initialize the embedding generator.
        
        Args:
            provider: Which embedding provider to use
            model_name: Optional specific model name
        """
        self.provider = provider
        self.model = None
        self.dimension = None
        self.cache: Dict[str, List[float]] = {}  # In-memory cache
        self.cache_hits = 0
        self.cache_misses = 0
        
        if provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            self._init_sentence_transformers(model_name)
        elif provider == EmbeddingProvider.GOOGLE:
            self._init_google(model_name)
        elif provider == EmbeddingProvider. OPENAI:
            self._init_openai(model_name)
    
    def _init_sentence_transformers(self, model_name: Optional[str] = None):
        """Initialize sentence-transformers (local embeddings)."""
        try:
            from sentence_transformers import SentenceTransformer
            import torch
            
            # Use a good general-purpose model
            model_name = model_name or 'all-MiniLM-L6-v2'
            
            # Auto-detect best device
            if torch.cuda.is_available():
                device = 'cuda'
                print(f"🚀 GPU detected: {torch.cuda.get_device_name(0)}")
            else:
                device = 'cpu'
                print("💻 Using CPU (no GPU detected)")
            
            print(f"Loading sentence-transformers model: {model_name} on {device}")
            self.model = SentenceTransformer(model_name, device=device)
            self.dimension = self.model.get_sentence_embedding_dimension()
            print(f"✓ Model loaded (dimension: {self.dimension})")
            
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
    
    def _init_google(self, model_name: Optional[str] = None):
        """Initialize Google Gemini embeddings."""
        try:
            import google.generativeai as genai
            
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not set")
            
            genai.configure(api_key=api_key)
            
            self.model_name = model_name or "models/embedding-001"
            self.dimension = 768  # Google embedding dimension
            
            print(f"✓ Google embeddings configured: {self.model_name}")
            
        except ImportError:
            raise ImportError(
                "google-generativeai not installed.  "
                "Install with: pip install google-generativeai"
            )
    
    def _init_openai(self, model_name: Optional[str] = None):
        """Initialize OpenAI embeddings."""
        try:
            from openai import OpenAI
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            
            self.model = OpenAI(api_key=api_key)
            self. model_name = model_name or "text-embedding-3-small"
            self.dimension = 1536  # OpenAI embedding dimension
            
            print(f"✓ OpenAI embeddings configured: {self.model_name}")
            
        except ImportError:
            raise ImportError(
                "openai not installed. "
                "Install with: pip install openai"
            )
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text with caching.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        # Create cache key from text hash
        cache_key = hashlib.md5(text.encode('utf-8')).hexdigest()
        
        # Check cache first
        if cache_key in self.cache:
            self.cache_hits += 1
            print(f"✓ Cache hit! (hits: {self.cache_hits}, misses: {self.cache_misses})")
            return self.cache[cache_key]
        
        # Cache miss - generate embedding
        self.cache_misses += 1
        start_time = time.time()
        
        if self.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            embedding = self._embed_sentence_transformers(text)
        elif self.provider == EmbeddingProvider.GOOGLE:
            embedding = self._embed_google(text)
        elif self.provider == EmbeddingProvider.OPENAI:
            embedding = self._embed_openai(text)
        
        elapsed = time.time() - start_time
        print(f"✓ Embedding generated in {elapsed:.2f}s (hits: {self.cache_hits}, misses: {self.cache_misses})")
        
        # Store in cache (limit cache size to 1000 entries)
        if len(self.cache) < 1000:
            self.cache[cache_key] = embedding
        
        return embedding
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch).
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if self.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            return self._embed_batch_sentence_transformers(texts)
        else:
            # For API providers, process one by one (or implement batch API calls)
            return [self.generate_embedding(text) for text in texts]
    
    def _embed_sentence_transformers(self, text: str) -> List[float]:
        """Generate embedding using sentence-transformers."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding. tolist()
    
    def _embed_batch_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch using sentence-transformers."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def _embed_google(self, text: str) -> List[float]:
        """Generate embedding using Google Gemini API."""
        import google.generativeai as genai
        
        result = genai.embed_content(
            model=self.model_name,
            content=text,
            task_type="retrieval_document"
        )
        
        return result['embedding']
    
    def _embed_openai(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        response = self.model.embeddings. create(
            model=self. model_name,
            input=text
        )
        
        return response.data[0].embedding
    
    def get_dimension(self) -> int:
        """Get the dimension of embeddings produced by this generator."""
        return self.dimension


# Convenience functions
def get_embedding_generator(
    provider: str = "sentence_transformers"
) -> EmbeddingGenerator:
    """
    Get an embedding generator instance.
    
    Args:
        provider: Provider name ("sentence_transformers", "google", "openai")
        
    Returns:
        EmbeddingGenerator instance
    """
    provider_enum = EmbeddingProvider(provider)
    return EmbeddingGenerator(provider_enum)


def generate_embedding(text: str, provider: str = "sentence_transformers") -> List[float]:
    """
    Quick function to generate a single embedding.
    
    Args:
        text: Text to embed
        provider: Provider to use
        
    Returns:
        Embedding vector
    """
    generator = get_embedding_generator(provider)
    return generator.generate_embedding(text)