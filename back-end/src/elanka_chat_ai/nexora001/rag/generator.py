"""
Answer generation using Google Gemini AI.
"""

import os
from typing import Optional, Dict, List
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class AnswerGenerator:
    """
    Generates answers using Google Gemini AI.
    """
    
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """
        Initialize the answer generator.
        
        Args:
            model_name: Gemini model to use
            temperature: Creativity (0.0-1.0)
            max_tokens: Maximum response length
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set")
        
        genai.configure(api_key=api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
        )
        
        self.system_prompt = """You are an intelligent AI assistant that helps users.

Your responsibilities:
1. Answer questions based on the provided context documents
2. If the documents contain relevant information, use it to provide a helpful answer
3. If the documents don't directly answer the question but contain related information, explain what you found
4. Only say "I don't have enough information" if the documents are completely unrelated to the question
5. Be comprehensive and helpful while staying accurate to the source material
6. Use a friendly, professional tone

Guidelines:
- Extract and synthesize information from multiple documents when relevant
- If asked a broad question (like "What is X? "), provide a clear explanation using the available context
- Connect information across documents to give complete answers
- Provide direct answers without mentioning source document numbers or citations
- Do not use brackets like [Document 1] or [Source 2] in your final response
- Just provide the correct answer politely"""
    
    def generate_answer(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None,
        chatbot_name: str = "AI Assistant",
        chatbot_personality: str = "friendly and helpful"
    ) -> tuple:
        """
        Generate an answer based on query and context.
        
        Args:
            query: User's question
            context: Retrieved document context
            conversation_history: Previous conversation (optional)
            chatbot_name: Custom bot name
            chatbot_personality: Custom personality traits
            
        Returns:
            Tuple of (Generated answer, prompt_tokens, completion_tokens, total_tokens)
        """
        # Build prompt
        prompt = self._build_prompt(query, context, conversation_history, chatbot_name, chatbot_personality)
        
        try:
            # Generate response
            response = self. model.generate_content(prompt)
            
            # Handle both simple and complex responses
            answer = ""
            try:
                # Try simple text access first
                answer = response.text. strip()
            except (ValueError, AttributeError):
                # Response is not simple text, extract from parts
                if hasattr(response, 'parts'):
                    for part in response.parts:
                        if hasattr(part, 'text'):
                            answer += part.text
                elif hasattr(response, 'candidates') and response.candidates:
                    # Fallback: extract from candidates
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text'):
                            answer += part.text
                
                answer = answer.strip()
            
            # Extract token counts
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                prompt_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                completion_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
                total_tokens = getattr(response.usage_metadata, 'total_token_count', 0)
            
            return (answer if answer else "I don't have enough information to answer that.", prompt_tokens, completion_tokens, total_tokens)
            
        except Exception as e:
            return (f"Error generating answer: {e}", 0, 0, 0)
    
    def _build_prompt(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None,
        chatbot_name: str = "AI Assistant",
        chatbot_personality: str = "friendly and helpful"
    ) -> str:
        """
        Build the complete prompt for the LLM.
        
        Args:
            query: User's question
            context: Retrieved documents
            conversation_history: Previous messages
            chatbot_name: Custom bot name
            chatbot_personality: Custom personality traits
            
        Returns:
            Complete prompt string
        """
        # Dynamic system prompt
        system_prompt = f"""You are {chatbot_name}, an intelligent AI assistant that helps users understand technical documentation.

Your personality: {chatbot_personality}

Your responsibilities:
1. Answer questions based on the provided context documents
2. If the documents contain relevant information, use it to provide a helpful answer
3. If the documents don't directly answer the question but contain related information, explain what you found
4. Only say "I don't have enough information" if the documents are completely unrelated to the question
5. Be comprehensive and helpful while staying accurate to the source material
6. Use a {chatbot_personality} tone

Guidelines:
- Extract and synthesize information from multiple documents when relevant
- If asked a broad question (like "What is X?"), provide a clear explanation using the available context
- Connect information across documents to give complete answers
- Provide direct answers without mentioning source document numbers or citations
- Do not use brackets like [Document 1] or [Source 2] in your final response
- When asked who you are, respond as {chatbot_name}
- Just provide the correct answer politely"""
        
        prompt_parts = [system_prompt, ""]
        
        # Add conversation history if available
        if conversation_history:
            prompt_parts.append("Previous conversation:")
            for msg in conversation_history[-3:]:  # Last 3 messages
                role = msg. get('role', 'user')
                content = msg.get('content', '')
                prompt_parts.append(f"{role. title()}: {content}")
            prompt_parts.append("")
        
        # Add context documents
        if context:
            prompt_parts. append("Context Documents:")
            prompt_parts.append(context)
            prompt_parts.append("")
        
        # Add current query
        prompt_parts.append(f"User Question: {query}")
        prompt_parts.append("")
        prompt_parts.append("Your Answer:")
        
        return "\n".join(prompt_parts)
    
    def generate_streaming_answer(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None,
        chatbot_name: str = "AI Assistant",
        chatbot_personality: str = "friendly and helpful"
    ):
        """
        Generate answer with streaming (for real-time display).
        
        Args:
            query: User's question
            context: Retrieved documents
            conversation_history: Previous conversation
            chatbot_name: Custom bot name
            chatbot_personality: Custom personality traits
            
        Yields:
            Chunks of generated text
        """
        prompt = self._build_prompt(query, context, conversation_history, chatbot_name, chatbot_personality)
        
        try:
            response = self.model.generate_content(prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            yield f"Error: {e}"