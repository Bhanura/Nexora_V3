"""
API routes for user data collection (Feature 2).
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from nexora001.api.models import (
    UserDataCollectionSettings,
    UpdateDataCollectionSettingsRequest,
    UserDataSubmission,
    UserSubmissionRecord,
    SubmissionListResponse
)
from nexora001.api.dependencies import get_current_user, get_user_from_api_key, get_storage
from nexora001.storage.mongodb import MongoDBStorage
from nexora001.services.email_service import get_email_service

router = APIRouter(prefix="/api", tags=["data-collection"])


@router.get("/settings/data-collection", response_model=UserDataCollectionSettings)
async def get_data_collection_settings(
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """Get user data collection settings for the current client."""
    client_id = str(current_user["_id"])
    
    settings = storage.get_data_collection_settings(client_id)
    
    if settings is None:
        # Return defaults if not configured yet
        return UserDataCollectionSettings(
            enabled=False,
            custom_fields=[],
            data_collection_timing="after_first_message",
            data_collection_message="Please share your details:",
            notification_emails=[]
        )
    
    return UserDataCollectionSettings(**settings)


@router.put("/settings/data-collection")
async def update_data_collection_settings(
    request: UpdateDataCollectionSettingsRequest,
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """Update user data collection settings."""
    client_id = str(current_user["_id"])
    
    # Build update dict from non-None values
    updates = {}
    if request.enabled is not None:
        updates["enabled"] = request.enabled
    if request.custom_fields is not None:
        # Convert Pydantic models to dicts
        updates["custom_fields"] = [field.dict() for field in request.custom_fields]
    if request.data_collection_timing is not None:
        updates["data_collection_timing"] = request.data_collection_timing
    if request.data_collection_message is not None:
        updates["data_collection_message"] = request.data_collection_message
    if request.notification_emails is not None:
        updates["notification_emails"] = request.notification_emails
    
    success = storage.update_data_collection_settings(client_id, updates)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update settings")
    
    return {"success": True, "message": "Settings updated successfully"}


@router.post("/user-data/submit")
async def submit_user_data(
    submission: UserDataSubmission,
    x_api_key: str = Header(..., alias="X-API-KEY"),
    client_id: str = Depends(get_user_from_api_key),
    storage: MongoDBStorage = Depends(get_storage)
):
    """
    Submit user data from widget (public endpoint with API key auth).
    Sends email notifications to configured addresses.
    """
    # Get data collection settings to check if enabled
    settings = storage.get_data_collection_settings(client_id)
    if not settings or not settings.get("enabled", False):
        raise HTTPException(status_code=400, detail="Data collection is not enabled")
    
    # Save submission to database
    submission_id = storage.save_user_submission(
        client_id=client_id,
        session_id=submission.session_id,
        submitted_data=submission.submitted_data
    )
    
    # Send email notifications if configured
    notification_emails = settings.get("notification_emails", [])
    if notification_emails:
        # Get client name for email
        user = storage.get_user_by_id(client_id)
        client_name = user.get("name", "Client") if user else "Client"
        
        email_service = get_email_service()
        email_service.send_submission_notification(
            recipient_emails=notification_emails,
            client_name=client_name,
            submitted_data=submission.submitted_data,
            session_id=submission.session_id
        )
    
    return {
        "success": True,
        "submission_id": submission_id,
        "message": "Data submitted successfully"
    }


@router.get("/user-data/submissions", response_model=SubmissionListResponse)
async def get_user_submissions(
    page: int = 1,
    page_size: int = 50,
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """Get all user data submissions for the current client."""
    client_id = str(current_user["_id"])
    
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 50
    
    submissions, total = storage.get_user_submissions(client_id, page, page_size)
    
    # Convert to response models
    submission_records = [
        UserSubmissionRecord(
            submission_id=sub["submission_id"],
            client_id=sub["client_id"],
            session_id=sub["session_id"],
            submitted_data=sub["submitted_data"],
            submitted_at=sub["submitted_at"]
        )
        for sub in submissions
    ]
    
    return SubmissionListResponse(
        submissions=submission_records,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/user-data/submissions/{submission_id}")
async def delete_user_submission(
    submission_id: str,
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """Delete a specific user data submission."""
    client_id = str(current_user["_id"])
    
    success = storage.delete_user_submission(submission_id, client_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Submission not found or access denied")
    
    return {"success": True, "message": "Submission deleted successfully"}
