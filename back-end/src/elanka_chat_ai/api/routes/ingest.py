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

from elanka_chat_ai.api.models import CrawlRequest, CrawlResponse, IngestResponse, ErrorResponse, TextIngestRequest
from elanka_chat_ai.crawler.manager import crawl_website
from elanka_chat_ai.processors.pdf_processor import process_pdf
from elanka_chat_ai.processors.docx_processor import process_docx
from elanka_chat_ai.api.dependencies import get_current_user, get_storage  # <--- DEPENDENCY IMPORT
from elanka_chat_ai.storage.mongodb import MongoDBStorage

router = APIRouter()


# ============================================================================
# BACKGROUND TASK STORAGE (In production, use Redis/Celery)
# ============================================================================

crawl_jobs = {}


def background_crawl_task(
    job_id: str, 
    url: str, 
    client_id: str,
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
    
    # Persist initial running status so get_crawl_status can find it after a reload
    from elanka_chat_ai.api.dependencies import get_storage
    storage = get_storage()
    
    try:
        crawl_jobs[job_id] = {"status": "running", "url": url}
        storage.db["crawl_status"].update_one(
            {"job_id": job_id},
            {"$set": {"status": "running", "url": url, "client_id": client_id}},
            upsert=True
        )
        
        logger.info(f"⏳ Calling crawl_website()...")
        result = crawl_website(
            url=url,
            client_id=client_id,
            max_depth=max_depth,
            follow_links=follow_links,
            use_playwright=use_playwright
        )
        
        logger.info(f"✅ Crawl completed successfully for job {job_id}")
        logger.info(f"   Result: {result}")
        
        completed_job = {
            "status": "completed",
            "url": url,
            "result": result
        }
        crawl_jobs[job_id] = completed_job
        storage.db["crawl_status"].update_one(
            {"job_id": job_id},
            {"$set": completed_job},
            upsert=True
        )
        
    except Exception as e:
        logger.error(f"❌ Crawl failed for job {job_id}")
        logger.error(f"   Error: {str(e)}")
        logger.error(f"   Traceback:\n{traceback.format_exc()}")
        
        failed_job = {
            "status": "failed",
            "url": url,
            "error": str(e)
        }
        crawl_jobs[job_id] = failed_job
        storage.db["crawl_status"].update_one(
            {"job_id": job_id},
            {"$set": failed_job},
            upsert=True
        )


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
    """Get the status of a crawl job. Falls back to MongoDB if the job was lost on a server reload."""
    # 1. Try fast in-memory lookup first
    if job_id in crawl_jobs:
        return crawl_jobs[job_id]
    
    # 2. Fall back to MongoDB (survives hot-reloads)
    from elanka_chat_ai.api.dependencies import get_storage
    storage = get_storage()
    doc = storage.db["crawl_status"].find_one({"job_id": job_id}, {"_id": 0})
    if doc:
        # Re-populate memory cache so future polls are fast
        crawl_jobs[job_id] = doc
        return doc
    
    raise HTTPException(
        status_code=404,
        detail={"error": "NotFound", "message": f"Job {job_id} not found"}
    )

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


@router.post(
    "/text",
    response_model=IngestResponse,
    responses={
        200: {"description": "Text processed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid text input"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Ingest raw text content",
    description="Submit raw text content (like copy-pasted info) for chunking and vector storage"
)
async def ingest_text(
    request: TextIngestRequest,
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """
    Ingest raw text content directly into the database.
    """
    try:
        client_id = current_user["_id"]
        # Generate a unique source identifier
        source_url = f"text://{uuid.uuid4().hex[:12]}/{request.title.replace(' ', '_')[:30]}"
        
        # Initialize components
        from elanka_chat_ai.processors.chunker import TextChunker
        from elanka_chat_ai.processors.embeddings import get_embedding_generator
        
        chunker = TextChunker(chunk_size=500, chunk_overlap=50)
        
        try:
            embedding_generator = get_embedding_generator("sentence_transformers")
            generate_embeddings = True
        except Exception as e:
            print(f"Warning: Failed to initialize embedding generator: {e}")
            generate_embeddings = False
            
        chunks = chunker.chunk_text(request.text, metadata={
            "source_url": source_url,
            "title": request.title
        })
        
        chunks_stored = 0
        for chunk in chunks:
            try:
                chunk_text = chunk['text']
                chunk_index = chunk['chunk_index']
                total_chunks = chunk['total_chunks']
                
                embedding = None
                if generate_embeddings:
                    embedding = embedding_generator.generate_embedding(chunk_text)
                    
                if embedding:
                    storage.store_document_with_embedding(
                        client_id=client_id,
                        content=chunk_text,
                        embedding=embedding,
                        source_url=source_url,
                        source_type="text",
                        title=request.title,
                        chunk_index=chunk_index,
                        total_chunks=total_chunks,
                        metadata={
                            "chunk_char_count": chunk['char_count']
                        }
                    )
                else:
                    storage.store_document(
                        client_id=client_id,
                        content=chunk_text,
                        source_url=source_url,
                        source_type="text",
                        title=request.title,
                        metadata={
                            "chunk_index": chunk_index,
                            "total_chunks": total_chunks,
                            "chunk_char_count": chunk['char_count']
                        }
                    )
                chunks_stored += 1
            except Exception as e:
                print(f"Failed to store raw text chunk {chunk_index}: {e}")
                continue
                
        # Log activity
        storage.log_activity(
            user_id=str(client_id),
            action_type="ingest_text",
            resource_type="document",
            resource_id=None,
            details={
                "title": request.title,
                "chunks_created": chunks_stored,
                "total_characters": len(request.text)
            }
        )
        
        return IngestResponse(
            success=True,
            filename=request.title,
            title=request.title,
            chunks_created=chunks_stored,
            total_characters=len(request.text),
            message="Raw text ingested and chunked successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalError",
                "message": str(e)
            }
        )