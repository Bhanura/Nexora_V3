"""
Ingestion endpoints for crawling URLs and uploading files. 
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends, Query
import uuid
import shutil
import tempfile
from pathlib import Path
from typing import Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from nexora001.api.models import CrawlRequest, CrawlResponse, IngestResponse, ErrorResponse
from nexora001.crawler.manager import crawl_website
from nexora001.processors.pdf_processor import process_pdf
from nexora001.processors.docx_processor import process_docx
from nexora001.api.dependencies import get_current_user, get_storage  # <--- DEPENDENCY IMPORT
from nexora001.storage.mongodb import MongoDBStorage

router = APIRouter()


# ============================================================================
# BACKGROUND TASK STORAGE (In production, use Redis/Celery)
# ============================================================================

crawl_jobs = {}


def background_crawl_task(
    job_id: str, 
    url: str, 
    client_id: str,  # <--- ADDED client_id parameter
    max_depth: int, 
    follow_links: bool, 
    use_playwright: bool
):
    """Background task for crawling."""
    import logging
    import traceback
    
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 Starting background crawl task for job {job_id}")
    logger.info(f"   URL: {url}")
    logger.info(f"   Client ID: {client_id}")
    logger.info(f"   Max depth: {max_depth}")
    logger.info(f"   Playwright: {use_playwright}")
    
    try:
        crawl_jobs[job_id] = {"status": "running", "url": url}
        
        # Perform crawl with client_id
        logger.info(f"⏳ Calling crawl_website()...")
        result = crawl_website(
            url=url,
            client_id=client_id,  # <--- Passing the ID
            max_depth=max_depth,
            follow_links=follow_links,
            use_playwright=use_playwright
        )
        
        logger.info(f"✅ Crawl completed successfully for job {job_id}")
        logger.info(f"   Result: {result}")
        
        crawl_jobs[job_id] = {
            "status": "completed",
            "url": url,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"❌ Crawl failed for job {job_id}")
        logger.error(f"   Error: {str(e)}")
        logger.error(f"   Traceback:\n{traceback.format_exc()}")
        
        crawl_jobs[job_id] = {
            "status": "failed",
            "url": url,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


# ============================================================================
# URL CRAWLING ENDPOINTS
# ============================================================================

@router.post(
    "/url",
    response_model=CrawlResponse,
    responses={
        200: {"description": "Crawl job started"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Crawl a website URL",
    description="Submit a URL for crawling. The crawl will run in the background."
)
async def ingest_url(
    request: CrawlRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)  # <--- Security Guard
):
    """
    Start crawling a website URL.
    
    The crawler will:
    1. Fetch the page (with optional JavaScript rendering)
    2. Extract text content
    3. Follow internal links up to specified depth
    4. Chunk and store content with embeddings
    
    Returns a job_id to track progress.
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Add to background tasks with client_id
        background_tasks.add_task(
            background_crawl_task,
            job_id,
            str(request.url),
            current_user["_id"],  # <--- Extracted from Token
            request.max_depth,
            request.follow_links,
            request.use_playwright
        )
        
        # Store initial status
        crawl_jobs[job_id] = {
            "status": "queued",
            "url": str(request.url)
        }
        
        return CrawlResponse(
            job_id=job_id,
            status="queued",
            url=str(request.url),
            message="Crawl job queued for client"  # <--- Updated message
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
    "/url/{job_id}",
    summary="Get crawl job status",
    description="Check the status of a crawl job"
)
async def get_crawl_status(job_id: str):
    """Get the status of a crawl job."""
    if job_id not in crawl_jobs:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": f"Job {job_id} not found"}
        )
    
    return crawl_jobs[job_id]

@router.get(
    "/jobs",
    summary="Get user's crawl jobs",
    description="Retrieve crawl job history for the logged-in user"
)
async def get_user_jobs(
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    storage: MongoDBStorage = Depends(get_storage),
    current_user: dict = Depends(get_current_user)
):
    """Get crawl jobs for the current user."""
    try:
        client_id = current_user["_id"]
        jobs = storage.get_user_crawl_jobs(client_id, limit, skip)
        total = storage.crawl_jobs.count_documents({"client_id": client_id})
        
        return {
            "jobs": jobs,
            "total": total
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalError", "message": str(e)}
        )


# ============================================================================
# FILE UPLOAD ENDPOINTS
# ============================================================================

@router.post(
    "/file",
    response_model=IngestResponse,
    responses={
        200: {"description": "File processed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid file format"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Upload and process a document",
    description="Upload a PDF or DOCX file for processing and indexing"
)
async def ingest_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),  # <--- Security Guard
    storage: MongoDBStorage = Depends(get_storage)
):
    """
    Upload and process a document file.
    
    Supported formats: 
    - PDF (.pdf)
    - Word Document (.docx)
    
    The file will be: 
    1. Saved temporarily
    2. Text extracted
    3. Chunked intelligently
    4. Embedded and stored in database
    """
    try:
        # Validate file type
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in ['.pdf', '.docx']: 
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "InvalidFileType",
                    "message": f"Unsupported file type: {file_ext}. Supported: .pdf, .docx"
                }
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            # Save uploaded file
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        
        try:
            client_id = current_user["_id"]
            source_url = f"file://{file.filename}"
            
            # Process based on file type with client_id
            if file_ext == '.pdf':
                result = process_pdf(temp_path, source_url=source_url, client_id=client_id)
            elif file_ext == '.docx':
                result = process_docx(temp_path, source_url=source_url, client_id=client_id)
            
            # Clean up temp file
            Path(temp_path).unlink()
            
            if not result['success']:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "ProcessingError",
                        "message": result.get('error', 'Failed to process file')
                    }
                )
            
            # Log document upload activity
            storage.log_activity(
                user_id=str(client_id),
                action_type="upload",
                resource_type="document",
                resource_id=result.get('doc_id'),
                details={
                    "filename": file.filename,
                    "file_type": file_ext,
                    "chunks_created": result['chunks_created'],
                    "total_characters": result['total_characters']
                }
            )
            
            return IngestResponse(
                success=True,
                filename=file.filename,
                title=result.get('title', file.filename),
                chunks_created=result['chunks_created'],
                total_characters=result['total_characters'],
                message="File processed successfully"  # <--- Updated message
            )
            
        except Exception as e:
            # Clean up on error
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            raise e
        
    except HTTPException: 
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": str(e)
            }
        )