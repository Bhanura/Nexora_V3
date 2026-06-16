"""
PDF document processing for Nexora001. 
Extracts text from PDF files using PyMuPDF.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, Optional, List
import sys

sys.path.insert(0, str(Path(__file__).parent. parent. parent))

from nexora001.processors.chunker import TextChunker
from nexora001.storage.mongodb import get_storage
from nexora001.processors.embeddings import get_embedding_generator


class PDFProcessor:
    """Process PDF documents and store in vector database."""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        generate_embeddings: bool = True
    ):
        """
        Initialize PDF processor.
        
        Args:
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            generate_embeddings: Whether to generate embeddings
        """
        self.chunker = TextChunker(chunk_size, chunk_overlap)
        self.generate_embeddings = generate_embeddings
        
        if generate_embeddings:
            self.embedding_generator = get_embedding_generator("sentence_transformers")
    
    def extract_text(self, pdf_path: str) -> Dict:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with text and metadata
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            # Open PDF
            doc = fitz. open(str(pdf_path))
            
            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(doc, 1):
                text = page.get_text()
                if text. strip():
                    text_parts.append(text)
            
            full_text = "\n\n".join(text_parts)
            
            # Extract metadata
            metadata = {
                "filename": pdf_path.name,
                "pages": len(doc),
                "author": doc. metadata.get("author", "Unknown"),
                "title": doc.metadata.get("title", pdf_path.stem),
                "subject": doc.metadata.get("subject", ""),
            }
            
            doc.close()
            
            return {
                "text": full_text,
                "metadata": metadata
            }
            
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {e}")
    
    def process_and_store(self, pdf_path: str, client_id: str, source_url: Optional[str] = None) -> Dict:
        """
        Process PDF and store in database.
        
        Args:
            pdf_path: Path to PDF file
            client_id: Client ID for multi-tenant data isolation
            source_url: Optional URL/identifier for the document
            
        Returns:
            Dictionary with processing statistics
        """
        # Extract text
        result = self.extract_text(pdf_path)
        text = result["text"]
        metadata = result["metadata"]
        
        if not text or len(text.strip()) < 100:
            return {
                "success": False,
                "error": "Insufficient text content in PDF",
                "chunks_created": 0
            }
        
        # Determine source URL
        if not source_url:
            source_url = f"file://{Path(pdf_path).absolute()}"
        
        # Chunk the text
        chunks = self. chunker.chunk_text(text, metadata={
            "source_url": source_url,
            "title": metadata["title"]
        })
        
        # Store chunks
        with get_storage() as storage:
            chunks_stored = 0
            
            for chunk in chunks:
                try:
                    chunk_text = chunk['text']
                    chunk_index = chunk['chunk_index']
                    total_chunks = chunk['total_chunks']
                    
                    # Generate embedding if enabled
                    embedding = None
                    if self. generate_embeddings:
                        embedding = self.embedding_generator.generate_embedding(chunk_text)
                    
                    # Store in MongoDB
                    if embedding:
                        storage.store_document_with_embedding(
                            client_id=client_id,
                            content=chunk_text,
                            embedding=embedding,
                            source_url=source_url,
                            source_type="pdf",
                            title=metadata["title"],
                            chunk_index=chunk_index,
                            total_chunks=total_chunks,
                            metadata={
                                "filename": metadata["filename"],
                                "pages": metadata["pages"],
                                "author": metadata["author"],
                                "chunk_char_count": chunk['char_count']
                            }
                        )
                    else:
                        storage.store_document(
                            client_id=client_id,
                            content=chunk_text,
                            source_url=source_url,
                            source_type="pdf",
                            title=metadata["title"],
                            metadata={
                                "filename": metadata["filename"],
                                "pages": metadata["pages"],
                                "author": metadata["author"],
                                "chunk_index": chunk_index,
                                "total_chunks": total_chunks,
                                "chunk_char_count": chunk['char_count']
                            }
                        )
                    
                    chunks_stored += 1
                    
                except Exception as e:
                    print(f"Failed to store chunk {chunk_index}: {e}")
                    continue
        
        return {
            "success": True,
            "filename": metadata["filename"],
            "title": metadata["title"],
            "pages": metadata["pages"],
            "chunks_created": chunks_stored,
            "total_characters": len(text)
        }


def process_pdf(pdf_path: str, source_url: Optional[str] = None, client_id: Optional[str] = None) -> Dict:
    """
    Convenience function to process a PDF file. 
    
    Args:
        pdf_path: Path to PDF file
        source_url: Optional URL/identifier
        client_id: Client ID for multi-tenant support
        
    Returns:
        Processing statistics
    """
    processor = PDFProcessor()
    return processor.process_and_store(pdf_path, client_id, source_url)