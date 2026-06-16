"""
Text chunking utilities for Nexora001. 
Splits documents into optimal chunks for RAG.
"""

from typing import List, Dict, Optional
import re


class TextChunker:
    """
    Intelligent text chunking for RAG systems.
    
    Chunks text while trying to preserve semantic meaning by:
    - Respecting sentence boundaries
    - Keeping paragraphs together when possible
    - Adding overlap between chunks for context
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separator: str = "\n\n"
    ):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            separator: Primary separator for splitting (default: paragraph breaks)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
    
    def chunk_text(self, text: str, metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: The text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text or len(text. strip()) == 0:
            return []
        
        # Clean the text
        text = self._clean_text(text)
        
        # Split into chunks
        chunks = self._split_text(text)
        
        # Create chunk objects with metadata
        chunk_objects = []
        for i, chunk_text in enumerate(chunks):
            chunk_obj = {
                "text": chunk_text,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "char_count": len(chunk_text),
                "metadata": metadata or {}
            }
            chunk_objects.append(chunk_obj)
        
        return chunk_objects
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re. sub(r'\s+', ' ', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _split_text(self, text: str) -> List[str]:
        """
        Split text into chunks intelligently.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        
        # Try to split by paragraphs first
        paragraphs = text.split(self.separator)
        
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(para) + len(self.separator) > self. chunk_size:
                
                # If current chunk has content, save it
                if current_chunk:
                    chunks.append(current_chunk. strip())
                    
                    # Start new chunk with overlap
                    overlap_text = self._get_overlap(current_chunk)
                    current_chunk = overlap_text + para
                else:
                    # Paragraph itself is too long, split by sentences
                    if len(para) > self.chunk_size:
                        sentence_chunks = self._split_by_sentences(para)
                        chunks.extend(sentence_chunks[:-1])
                        current_chunk = sentence_chunks[-1] if sentence_chunks else ""
                    else:
                        current_chunk = para
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += self.separator + para
                else:
                    current_chunk = para
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """
        Split text by sentences when paragraphs are too long.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        # Simple sentence splitting (can be improved with nltk)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    overlap_text = self._get_overlap(current_chunk)
                    current_chunk = overlap_text + sentence
                else:
                    # Even single sentence is too long, split by words
                    if len(sentence) > self.chunk_size:
                        word_chunks = self._split_by_words(sentence)
                        chunks.extend(word_chunks[:-1])
                        current_chunk = word_chunks[-1] if word_chunks else ""
                    else:
                        current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunks. append(current_chunk.strip())
        
        return chunks
    
    def _split_by_words(self, text: str) -> List[str]:
        """
        Split text by words as last resort.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        current_chunk = ""
        
        for word in words:
            if len(current_chunk) + len(word) + 1 > self. chunk_size:
                if current_chunk:
                    chunks. append(current_chunk.strip())
                    overlap_words = current_chunk.split()[-self.chunk_overlap // 10:]
                    current_chunk = " ".join(overlap_words) + " " + word
                else:
                    # Single word is too long, just add it
                    chunks.append(word)
                    current_chunk = ""
            else:
                if current_chunk:
                    current_chunk += " " + word
                else:
                    current_chunk = word
        
        if current_chunk:
            chunks. append(current_chunk.strip())
        
        return chunks
    
    def _get_overlap(self, text: str) -> str:
        """
        Get overlap text from the end of a chunk.
        
        Args:
            text: Source text
            
        Returns:
            Overlap text
        """
        if len(text) <= self.chunk_overlap:
            return text + " "
        
        # Try to get complete sentences for overlap
        overlap_text = text[-self.chunk_overlap:]
        
        # Find the start of a sentence
        sentence_start = max(
            overlap_text.find('.  '),
            overlap_text. find('! '),
            overlap_text.find('? ')
        )
        
        if sentence_start > 0:
            overlap_text = overlap_text[sentence_start + 2:]
        
        return overlap_text. strip() + " " if overlap_text. strip() else ""


def chunk_document(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    metadata: Optional[Dict] = None
) -> List[Dict]:
    """
    Convenience function to chunk a document.
    
    Args:
        text: Text to chunk
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
        metadata: Optional metadata
        
    Returns:
        List of chunk dictionaries
    """
    chunker = TextChunker(chunk_size, chunk_overlap)
    return chunker.chunk_text(text, metadata)