"""
Chat endpoints for RAG question answering.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from nexora001.api.models import ChatRequest, ChatResponse, Source, ErrorResponse, ChatbotSettings, UpdateChatbotSettingsRequest
from nexora001.api.dependencies import get_rag_pipeline, get_current_user, get_user_from_api_key, get_storage
from nexora001.rag.pipeline import RAGPipeline
from nexora001.storage.mongodb import MongoDBStorage

router = APIRouter()


# ============================================================================
# INTERNAL DASHBOARD ENDPOINT (JWT Authentication)
# ============================================================================

@router.post(
    "/",
    response_model=ChatResponse,
    responses={
        200: {"description": "Successful response"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Ask a question (Dashboard)",
    description="Ask a question and get an AI-generated answer with source citations. Requires JWT authentication."
)
async def chat_dashboard(
    request: ChatRequest,
    rag: RAGPipeline = Depends(get_rag_pipeline),
    current_user: dict = Depends(get_current_user)  # <--- JWT Authentication
):
    """
    Internal Chat (Dashboard): Uses JWT Authentication.
    
    The system will:
    1. Search for relevant documents in the knowledge base
    2. Retrieve the most similar content
    3. Generate an answer using Google Gemini AI
    4. Return the answer with source citations
    
    Only searches documents belonging to the authenticated user.
    """
    try:
        # Create a session ID linked to the user
        session_id = request.session_id or f"dash-{current_user['_id']}"
        
        # Ask the RAG system with client_id for data isolation
        result = rag.ask(
            query=request.message,
            client_id=current_user["_id"],  # <--- Data Isolation
            session_id=session_id,
            use_history=request.use_history
        )
        
        # Convert sources to response model
        sources = [
            Source(
                number=src['number'],
                title=src['title'],
                url=src['url'],
                score=src['score'],
                chunk_index=src.get('chunk_index')
            )
            for src in result['sources']
        ]
        
        return ChatResponse(
            answer=result['answer'],
            sources=sources,
            found_documents=result['found_documents'],
            session_id=session_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": str(e)
            }
        )


# ============================================================================
# PUBLIC WIDGET ENDPOINT (API Key Authentication)
# ============================================================================

@router.post(
    "/widget",
    response_model=ChatResponse,
    responses={
        200: {"description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Ask a question (Widget)",
    description="Public Chat (Widget): Uses API Key Authentication via X-API-Key header."
)
async def chat_widget(
    request: ChatRequest,
    x_api_key: str = Header(..., description="Client API Key"),
    rag: RAGPipeline = Depends(get_rag_pipeline),
    client_id: str = Depends(get_user_from_api_key),
    storage: MongoDBStorage = Depends(get_storage)
):
    """
    Public Chat (Widget): Uses API Key Authentication.
    
    The system will:
    1. Validate the API key from X-API-Key header
    2. Search for relevant documents belonging to the API key owner
    3. Retrieve the most similar content
    4. Generate an answer using Google Gemini AI
    5. Return the answer with source citations
    """
    try:
        # For public widgets, we rely on the client_id extracted from the key
        session_id = request.session_id or "anonymous-visitor"
        
        # Fetch chatbot settings for this client
        chatbot_settings = storage.get_chatbot_settings(client_id)
        
        # Use settings or defaults
        chatbot_name = chatbot_settings.get("chatbot_name", "AI Assistant") if chatbot_settings else "AI Assistant"
        chatbot_personality = chatbot_settings.get("chatbot_personality", "friendly and helpful") if chatbot_settings else "friendly and helpful"
        
        result = rag.ask(
            query=request.message,
            client_id=client_id,
            session_id=session_id,
            use_history=request.use_history,
            chatbot_name=chatbot_name,
            chatbot_personality=chatbot_personality
        )
        
        sources = [
            Source(
                number=src['number'],
                title=src['title'],
                url=src['url'],
                score=src['score'],
                chunk_index=src.get('chunk_index')
            )
            for src in result['sources']
        ]
        
        return ChatResponse(
            answer=result['answer'],
            sources=sources,
            found_documents=result['found_documents'],
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": str(e)
            }
        )


# ============================================================================
# HISTORY MANAGEMENT ENDPOINTS
# ============================================================================

@router.post(
    "/clear-history",
    summary="Clear conversation history",
    description="Clear the conversation history for a fresh start"
)
async def clear_history(rag: RAGPipeline = Depends(get_rag_pipeline)):
    """Clear conversation history."""
    try:
        rag.clear_history()
        return {"success": True, "message": "Conversation history cleared"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": str(e)
            }
        )


@router.get(
    "/history",
    summary="Get conversation history",
    description="Retrieve the conversation history"
)
async def get_history(rag: RAGPipeline = Depends(get_rag_pipeline)):
    """Get conversation history."""
    try:
        history = rag.get_history()
        return {"messages": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": str(e)
            }
        )


# ============================================================================
# CHATBOT SETTINGS ENDPOINTS
# ============================================================================

@router.get(
    "/widget-config",
    response_model=ChatbotSettings,
    summary="Get chatbot configuration for widget",
    description="Returns customized chatbot settings (name, greeting, personality) for the widget based on API key."
)
async def get_widget_config(
    x_api_key: str = Header(..., alias="X-API-KEY", description="Client API Key"),
    client_id: str = Depends(get_user_from_api_key),
    storage: MongoDBStorage = Depends(get_storage)
):
    """
    Public endpoint: Widget calls this on load to get custom branding.
    Authentication: API Key in header
    """
    try:
        # Get chatbot settings from database
        settings = storage.get_chatbot_settings(client_id)
        
        if not settings:
            # Return defaults if user not found
            return ChatbotSettings()
        
        return ChatbotSettings(**settings)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/widget-data-collection-config",
    summary="Get data collection configuration for widget",
    description="Returns data collection settings (fields, timing, message) for the widget."
)
async def get_widget_data_collection_config(
    x_api_key: str = Header(..., alias="X-API-KEY", description="Client API Key"),
    client_id: str = Depends(get_user_from_api_key),
    storage: MongoDBStorage = Depends(get_storage)
):
    """
    Public endpoint: Widget calls this to get data collection form configuration.
    Authentication: API Key in header
    """
    try:
        # Get data collection settings
        settings = storage.get_data_collection_settings(client_id)
        
        if not settings or not settings.get("enabled", False):
            # Return disabled state if not configured
            return {
                "enabled": False,
                "custom_fields": [],
                "data_collection_timing": "after_first_message",
                "data_collection_message": "Please share your details:"
            }
        
        return settings
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/settings/chatbot",
    response_model=ChatbotSettings,
    summary="Get chatbot settings",
    description="Retrieve current chatbot settings for authenticated user."
)
async def get_chatbot_settings_endpoint(
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """
    Dashboard endpoint: Get current chatbot settings.
    Authentication: JWT token
    """
    try:
        settings = storage.get_chatbot_settings(current_user["_id"])
        
        if not settings:
            return ChatbotSettings()
        
        return ChatbotSettings(**settings)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/settings/chatbot",
    response_model=ChatbotSettings,
    summary="Update chatbot settings",
    description="Allows authenticated admin to customize their chatbot's name, greeting, and personality."
)
async def update_chatbot_settings(
    request: UpdateChatbotSettingsRequest,
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """
    Dashboard endpoint: Admin updates chatbot branding.
    Authentication: JWT token
    """
    try:
        # Build update dictionary (only include fields that were provided)
        updates = {}
        if request.chatbot_name is not None:
            updates["chatbot_name"] = request.chatbot_name
        if request.chatbot_greeting is not None:
            updates["chatbot_greeting"] = request.chatbot_greeting
        if request.chatbot_personality is not None:
            updates["chatbot_personality"] = request.chatbot_personality
        if request.theme_color is not None:
            updates["theme_color"] = request.theme_color
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        # Update in database
        client_id = str(current_user["_id"])
        success = storage.update_chatbot_settings(client_id, updates)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update settings")
        
        # Return updated settings
        settings = storage.get_chatbot_settings(client_id)
        return ChatbotSettings(**settings)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TOKEN USAGE ANALYTICS ENDPOINT
# ============================================================================

@router.get(
    "/analytics/token-usage",
    summary="Get token usage analytics",
    description="Returns AI token usage statistics for the authenticated user."
)
async def get_token_usage(
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """
    Dashboard endpoint: Token usage analytics.
    Authentication: JWT token
    """
    try:
        stats = storage.get_token_usage_stats(current_user["_id"])
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))