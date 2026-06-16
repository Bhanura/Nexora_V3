"""
Shared dependencies for FastAPI routes. 
"""

import sys
from pathlib import Path
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from jose import jwt, JWTError

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nexora001.rag.pipeline import RAGPipeline
from nexora001.storage.mongodb import MongoDBStorage
from nexora001.api.security import oauth2_scheme, SECRET_KEY, ALGORITHM

# ============================================================================
# GLOBAL INSTANCES (Singletons)
# ============================================================================

_rag_pipeline: Optional[RAGPipeline] = None
_storage: Optional[MongoDBStorage] = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline instance (singleton)."""
    global _rag_pipeline
    
    if _rag_pipeline is None:
        from nexora001.rag.pipeline import create_rag_pipeline
        _rag_pipeline = create_rag_pipeline(
            embedding_provider="sentence_transformers",
            model_name="gemini-2.5-flash",
            top_k=5,
            min_similarity=0.3
        )
    
    return _rag_pipeline


def get_storage() -> MongoDBStorage:
    """Get or create storage instance (singleton)."""
    global _storage
    
    if _storage is None:
        _storage = MongoDBStorage()
    
    return _storage


def reset_dependencies():
    """Reset all singletons (useful for testing)."""
    global _rag_pipeline, _storage
    _rag_pipeline = None
    _storage = None

#=============================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    storage: MongoDBStorage = Depends(get_storage)
) -> dict:
    """
    Validates JWT token and returns the user object.
    Acts as the 'Security Guard' for protected routes.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # Get user from DB
    user = storage.users.find_one({"email": email})
    if user is None:
        raise credentials_exception
        
    # Check if banned
    if user.get("status") == "banned":
        raise HTTPException(status_code=403, detail="Account suspended")
        
    # Convert ObjectId to string for easy API usage
    user["_id"] = str(user["_id"])
    return user

async def get_current_active_superuser(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Validator for Super Admin routes."""
    if current_user.get("role") != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges"
        )
    return current_user

async def get_user_from_api_key(
    x_api_key: str = Header(..., description="API Key for Widget"),
    storage: MongoDBStorage = Depends(get_storage)
) -> str:
    """
    Validator for the Public Chat Widget.
    Returns: client_id (str)
    """
    client_id = storage.validate_api_key(x_api_key)
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API Key"
        )
    return client_id