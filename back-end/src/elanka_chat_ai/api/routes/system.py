"""
System endpoints for status, documents management, etc.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from elanka_chat_ai.api.models import (
    SystemStatus,
    DocumentInfo,
    DocumentListResponse,
    DeleteResponse,
    ErrorResponse
)
from elanka_chat_ai.api.dependencies import get_storage, get_rag_pipeline, get_current_user  # <--- ADDED get_current_user
from elanka_chat_ai.storage.mongodb import MongoDBStorage
from elanka_chat_ai.rag.pipeline import RAGPipeline

router = APIRouter()


# ============================================================================
# STATUS ENDPOINTS
# ============================================================================

@router.get(
    "/status",
    response_model=SystemStatus,
    summary="Get system status",
    description="Get the current status of the eLanka Chat AI system"
)
async def get_status(
    storage: MongoDBStorage = Depends(get_storage),
    rag: RAGPipeline = Depends(get_rag_pipeline)
):
    """Get system status."""
    try:
        # Get document stats
        stats = storage.get_stats()
        
        # Check database connection
        db_connected = storage.db is not None
        
        # Get embedding info
        embeddings_enabled = rag.retriever.embedding_generator is not None
        embedding_dim = None
        if embeddings_enabled: 
            embedding_dim = rag.retriever.embedding_generator.get_dimension()
        
        return SystemStatus(
            status="operational" if db_connected else "down",
            database_connected=db_connected,
            total_documents=stats['total_documents'],
            unique_sources=stats['unique_sources'],
            embeddings_enabled=embeddings_enabled,
            embedding_dimension=embedding_dim,
            llm_provider="Google Gemini 2.5 Flash",
            version="1.0.0"
        )
        
    except Exception as e: 
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": str(e)
            }
        )


# ============================================================================
# DOCUMENT MANAGEMENT ENDPOINTS
# ============================================================================

@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List all documents",
    description="Get a paginated list of all indexed documents"
)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    source_type: Optional[str] = Query(None, description="Filter by type: web, pdf, docx"),
    storage: MongoDBStorage = Depends(get_storage),
    current_user: dict = Depends(get_current_user)  # <--- Security Guard
):
    """List all indexed documents with pagination."""
    try:
        # Build filter with client_id restriction
        client_id = current_user["_id"]
        
        stats = storage.get_stats(client_id)
        
        documents = []
        for doc in stats['sources']:
            documents.append(DocumentInfo(
                id=doc['url'],
                title=doc['url'],
                url=doc['url'],
                source_type=doc['type'],
                created_at=doc.get('crawled_at', datetime.now()),
                chunk_count=doc['count'],
                total_characters=doc.get('total_characters', 0)
            ))
        
        return DocumentListResponse(
            documents=documents,
            total=len(documents),
            page=1,
            page_size=len(documents)
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": str(e)
            }
        )


@router.get(
    "/documents/stats",
    summary="Get document statistics",
    description="Get detailed statistics about indexed documents"
)
async def get_documents_stats(storage: MongoDBStorage = Depends(get_storage)):
    """Get detailed document statistics."""
    try:
        # Get stats
        stats = storage.get_stats()
        
        # Get breakdown by type - use storage.documents
        type_pipeline = [
            {
                "$group": {
                    "_id": "$metadata.source_type",
                    "count": {"$sum": 1}
                }
            }
        ]
        type_stats = list(storage.documents.aggregate(type_pipeline))
        
        return {
            "total_documents": stats['total_documents'],
            "unique_sources": stats['unique_sources'],
            "average_chunk_size": stats['avg_chunk_size'],
            "by_type": {item['_id']: item['count'] for item in type_stats},
            "sources": stats['sources']
        }
        
    except Exception as e: 
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": str(e)
            }
        )


@router.delete(
    "/documents",
    response_model=DeleteResponse,
    summary="Delete a document by ID",
    description="Delete a single document by its ID"
)
async def delete_document(
    doc_id: str = Query(..., description="Document ID to delete"),
    storage: MongoDBStorage = Depends(get_storage),
    current_user: dict = Depends(get_current_user)  # <--- Added authentication
):
    """Delete a single document by ID."""
    try:
        client_id = current_user["_id"]
        success = storage.delete_document_by_id(client_id, doc_id)
        
        if not success:
            return DeleteResponse(
                success=False,
                deleted_count=0,
                message="Document not found or not authorized to delete"
            )
            
        return DeleteResponse(
            success=True,
            deleted_count=1,
            message="Document deleted"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": str(e)
            }
        )


@router.delete(
    "/documents/by-source",
    response_model=DeleteResponse,
    summary="Delete documents by source URL",
    description="Delete all documents from a specific source URL"
)
async def delete_documents_by_source(
    source_url: str = Query(..., description="Source URL to delete"),
    storage: MongoDBStorage = Depends(get_storage),
    current_user: dict = Depends(get_current_user)  # <--- Added authentication
):
    """Delete all documents from a specific source URL."""
    try:
        client_id = current_user["_id"]
        # Modified to only delete documents belonging to the current user
        filter_query = {
            "metadata.source_url": source_url,
            "client_id": client_id
        }
        result = storage.documents.delete_many(filter_query)
        
        if result.deleted_count == 0:
            return DeleteResponse(
                success=False,
                deleted_count=0,
                message=f"No documents found for URL: {source_url}"
            )
        
        return DeleteResponse(
            success=True,
            deleted_count=result.deleted_count,
            message=f"Successfully deleted {result.deleted_count} documents from {source_url}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": str(e)
            }
        )


@router.delete(
    "/documents/all",
    response_model=DeleteResponse,
    summary="Delete all documents",
    description="⚠️ WARNING: Delete ALL documents from the database"
)
async def delete_all_documents(
    confirm: bool = Query(False, description="Must be true to confirm deletion"),
    storage: MongoDBStorage = Depends(get_storage),
    current_user: dict = Depends(get_current_user)  # <--- Added authentication
):
    """⚠️ WARNING: Delete ALL documents from the database."""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ConfirmationRequired",
                "message": "Set confirm=true to delete all documents"
            }
        )
    
    try:
        client_id = current_user["_id"]
        # Modified to only delete documents belonging to the current user
        result = storage.documents.delete_many({"client_id": client_id})
        
        return DeleteResponse(
            success=True,
            deleted_count=result.deleted_count,
            message=f"Deleted all {result.deleted_count} documents for user"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": str(e)
            }
        )

@router.get(
    "/analytics/tokens",
    summary="Get token usage analytics",
    description="Retrieve token usage statistics for the authenticated client."
)
async def get_token_analytics(
    days: int = Query(30, ge=1, le=90, description="Number of days of data to retrieve"),
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    try:
        stats = storage.get_token_usage_stats(str(current_user["_id"]), days=days)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/analytics/super-admin/tokens",
    summary="Get token usage for all users (Super Admin)",
    description="Retrieve aggregated token usage statistics for all clients. Requires super_admin role."
)
async def get_super_admin_token_analytics(
    days: int = Query(30, ge=1, le=90, description="Number of days of data to retrieve"),
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    if current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Only super_admin is authorized to view this resource")
        
    try:
        stats = storage.get_all_users_token_usage(days=days)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))