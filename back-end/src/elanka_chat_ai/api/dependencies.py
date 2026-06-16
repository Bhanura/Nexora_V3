"""
Shared dependencies for FastAPI routes. 
"""

import sys
from pathlib import Path
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from jose import jwt, JWTError
from bson import ObjectId
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from elanka_chat_ai.rag.pipeline import RAGPipeline
from elanka_chat_ai.storage.mongodb import MongoDBStorage
from elanka_chat_ai.api.security import oauth2_scheme, SECRET_KEY, ALGORITHM

# ============================================================================
# GLOBAL INSTANCES (Singletons)
# ============================================================================

_rag_pipeline: Optional[RAGPipeline] = None
_storage: Optional[MongoDBStorage] = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline instance (singleton)."""
    global _rag_pipeline
    
    if _rag_pipeline is None:
        from elanka_chat_ai.rag.pipeline import create_rag_pipeline
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
    x_api_key: str = Header(..., alias="X-API-KEY", description="API Key for Widget"),
    referer: Optional[str] = Header(None),
    origin: Optional[str] = Header(None),
    storage: MongoDBStorage = Depends(get_storage)
) -> str:
    """
    Validator for the Public Chat Widget.
    Includes domain whitelisting validation.
    Returns: client_id (str)
    """
    # 1. Fetch key document
    key_doc = storage.api_keys.find_one({"key": x_api_key})
    if not key_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
        
    # Check key status
    if key_doc.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive API Key"
        )
        
    # 2. Check if owner is banned
    client_id = key_doc["client_id"]
    user = storage.users.find_one({"_id": ObjectId(client_id)})
    if user and user.get('status') == 'banned':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended"
        )
        
    # 3. Update last_used
    from datetime import datetime
    storage.api_keys.update_one(
        {"_id": key_doc["_id"]},
        {"$set": {"last_used": datetime.utcnow()}}
    )
    
    # 4. Domain Whitelisting Validation
    allowed_domains = key_doc.get("allowed_domains", [])
    if allowed_domains:
        # Extract domain from Origin or Referer
        raw_url = origin or referer
        req_domain = ""
        if raw_url:
            if not raw_url.startswith(("http://", "https://")):
                raw_url = "https://" + raw_url
            try:
                parsed = urlparse(raw_url)
                req_domain = parsed.hostname or ""
            except Exception:
                pass
                
        if not req_domain:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Request blocked: Domain whitelisting is enabled but requesting domain could not be verified."
            )
            
        # Clean request domain (lowercase, remove port if any)
        req_domain = req_domain.lower().split(":")[0]
        
        # Check matching
        matched = False
        for domain in allowed_domains:
            domain = domain.strip().lower()
            if domain == "*" or req_domain == domain or req_domain.endswith("." + domain):
                matched = True
                break
                
        if not matched:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Request blocked: Domain '{req_domain}' is not whitelisted for this API key."
            )
            
    return str(client_id)