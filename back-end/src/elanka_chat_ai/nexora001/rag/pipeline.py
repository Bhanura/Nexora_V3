"""
Complete RAG pipeline that combines retrieval and generation.
"""

from typing import Dict, List, Optional
import sys
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nexora001.rag.retriever import DocumentRetriever
from nexora001.rag.generator import AnswerGenerator
from nexora001.storage.mongodb import get_storage


class RAGPipeline:
    """
    Complete RAG pipeline: Retrieve → Augment → Generate
    """
    
    def __init__(
        self,
        embedding_provider: str = "sentence_transformers",
        model_name: str = "gemini-2.5-flash",
        top_k: int = 5,
        min_similarity: float = 0.3,
        temperature: float = 0.7
    ):
        """
        Initialize the RAG pipeline.
        
        Args:
            embedding_provider: Embedding provider for retrieval
            model_name: Gemini model for generation
            top_k: Number of documents to retrieve
            min_similarity: Minimum similarity threshold
            temperature: LLM temperature
        """
        self.retriever = DocumentRetriever(
            embedding_provider=embedding_provider,
            top_k=top_k,
            min_similarity=min_similarity
        )
        
        self.generator = AnswerGenerator(
            model_name=model_name,
            temperature=temperature
        )
        
        self.conversation_history: List[Dict] = []
        self.executor = ThreadPoolExecutor(max_workers=2)  # For async DB operations
    
    def _save_chat_to_db(self, session_id: str, user_msg: str, assistant_msg: str):
        """Background task to save chat history to database."""
        try:
            from nexora001.storage.mongodb import get_storage
            with get_storage() as storage:
                storage.add_chat_message(session_id, "user", user_msg)
                storage.add_chat_message(session_id, "assistant", assistant_msg)
        except Exception as e:
            print(f"Warning: Failed to save chat history: {e}")

    def _log_token_usage_bg(self, client_id: str, session_id: str, prompt_tokens: int, completion_tokens: int, total_tokens: int):
        """Background task to log token usage details."""
        try:
            from nexora001.storage.mongodb import get_storage
            with get_storage() as storage:
                storage.log_token_usage(
                    client_id=client_id,
                    session_id=session_id or "dashboard-session",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens
                )
        except Exception as e:
            print(f"Warning: Failed to log token usage: {e}")
    
    def ask(
        self,
        query: str,
        client_id: str,
        session_id: str = None,
        use_history: bool = True,
        stream: bool = False,
        chatbot_name: str = "AI Assistant",
        chatbot_personality: str = "friendly and helpful"
    ) -> Dict:
        """
        Ask a question and get an answer.
        
        Args:
            query: User's question
            client_id: Client ID for data isolation
            session_id: Session ID for chat history (optional)
            use_history: Whether to use conversation history
            stream: Whether to stream the response
            chatbot_name: Custom bot name
            chatbot_personality: Custom personality traits
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        # Step 1: Retrieve relevant documents
        retrieval_result = self.retriever.retrieve_with_context(query, client_id)
        
        context = retrieval_result['context']
        sources = retrieval_result['sources']
        found_documents = retrieval_result['found_documents']
        
        # Step 2: Generate answer
        conversation = self.conversation_history if use_history else None
        
        if stream:
            # Return generator for streaming
            answer_generator = self.generator.generate_streaming_answer(
                query, context, conversation, chatbot_name, chatbot_personality
            )
            
            return {
                'answer': answer_generator,  # Generator object
                'sources': sources,
                'found_documents': found_documents,
                'streaming': True
            }
        else:
            # Generate the answer first (returns tuple: answer, prompt_t, comp_t, total_t)
            answer, prompt_tokens, completion_tokens, total_tokens = self.generator.generate_answer(
                query, context, conversation, chatbot_name, chatbot_personality
            )
            
            # Step 3: Save to Memory (In-Memory)
            self.conversation_history.append({'role': 'user', 'content': query})
            self.conversation_history.append({'role': 'assistant', 'content': answer})

            # Step 4: Save to Database and log token usage (Non-Blocking - Async)
            if session_id:
                # Submit to background thread - don't wait for completion
                self.executor.submit(self._save_chat_to_db, session_id, query, answer)

            if client_id and total_tokens > 0:
                self.executor.submit(
                    self._log_token_usage_bg,
                    str(client_id),
                    session_id,
                    prompt_tokens,
                    completion_tokens,
                    total_tokens
                )
            
            return {
                'answer': answer,
                'sources': sources,
                'found_documents': found_documents,
                'streaming': False
            }
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict]:
        """Get conversation history."""
        return self.conversation_history.copy()


# Convenience function
def create_rag_pipeline(**kwargs) -> RAGPipeline:
    """Create a RAG pipeline with custom settings."""
    return RAGPipeline(**kwargs)