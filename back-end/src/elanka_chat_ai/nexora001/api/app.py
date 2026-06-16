"""
Main FastAPI application for Nexora001 API.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import io
import traceback
from pathlib import Path

# Fix Windows console encoding for emoji support
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# pyrefly: ignore [missing-import]
from nexora001.api.routes import chat, ingest, system, auth, admin, notification, data_collection


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
# GLOBAL EXCEPTION HANDLER (Debug)
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(f"[ERROR] Unhandled exception on {request.url}: {exc}\n{tb}", flush=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": tb}
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
            "admin": "/api/admin"
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
    print("[STARTUP] eLanka Chat AI API starting...")
    print("[STARTUP] Loading embedding model...")
    # Warm up the RAG pipeline
    from nexora001.api.dependencies import get_rag_pipeline
    get_rag_pipeline()
    print("[STARTUP] API ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("[SHUTDOWN] eLanka Chat AI API shutting down...")
    from nexora001.api.dependencies import reset_dependencies
    reset_dependencies()