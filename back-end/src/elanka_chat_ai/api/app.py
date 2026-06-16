"""
Main FastAPI application for eLanka Chat AI API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from elanka_chat_ai.api.routes import chat, ingest, system, auth, admin, notification, data_collection


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="eLanka Chat AI API",
    description="AI-Powered Knowledge Base with RAG (Retrieval-Augmented Generation)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ============================================================================
# CORS MIDDLEWARE
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    chat.router,
    prefix="/api/chat",
    tags=["Chat"]
)

app.include_router(
    ingest.router,
    prefix="/api/ingest",
    tags=["Ingestion"]
)

app.include_router(
    system.router,
    prefix="/api",
    tags=["System"]
)

app.include_router(
    admin.router,
    prefix="/api/admin",
    tags=["Super Admin"]  # <--- Add admin router
)

app.include_router(
    notification.router, 
    prefix="/api/notifications", 
    tags=["Notifications"]
)

app.include_router(
    data_collection.router,
    tags=["Data Collection"]
)

# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
def root():
    """Root endpoint - API information."""
    return {
        "name": "eLanka Chat AI API",
        "version": "1.0.0",
        "description": "AI-Powered Knowledge Base with RAG",
        "docs": "/docs",
        "endpoints": {
            "auth": "/api/auth",
            "chat": "/api/chat",
            "ingest_url": "/api/ingest/url",
            "ingest_file": "/api/ingest/file",
            "status": "/api/status",
            "documents": "/api/documents",
            "admin": "/api/admin"  # <--- Added admin endpoint
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    print("🚀 eLanka Chat AI API starting...")
    print("📚 Loading embedding model...")
    # Warm up the RAG pipeline
    from elanka_chat_ai.api.dependencies import get_rag_pipeline
    get_rag_pipeline()
    print("✅ API ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("👋 eLanka Chat AI API shutting down...")
    from elanka_chat_ai.api.dependencies import reset_dependencies
    reset_dependencies()