from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from nexora001.api.dependencies import get_current_active_superuser, get_storage
from nexora001.storage.mongodb import MongoDBStorage
from pydantic import BaseModel
import secrets
from nexora001.api.security import get_password_hash

router = APIRouter()

# --- Admin Models ---

class AdminCreateUser(BaseModel):
    email: str
    name: str

class AdminNotification(BaseModel):
    email: str # Send to specific user by email
    message: str
    type: str = "info"

class AdminUserList(BaseModel):
    id: str
    email: str
    name: str
    role: str
    status: str
    doc_count: int
    api_keys: int
    storage_mb: float = 0.0
    last_login: Optional[datetime] = None

class UserAction(BaseModel):
    email: str

# --- Endpoints ---

@router.get("/users", response_model=List[AdminUserList])
async def list_all_users(
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: List all registered clients with statistics and storage usage."""
    users = storage.get_all_users_with_storage()
    
    # Format for response
    result = []
    for u in users:
        storage_info = u.get("storage", {})
        result.append(AdminUserList(
            id=str(u["_id"]),
            email=u["email"],
            name=u.get("name", ""),
            role=u.get("role", "client"),
            status=u.get("status", "active"),
            doc_count=storage_info.get("document_count", 0),
            api_keys=u.get("api_keys", 0),
            storage_mb=storage_info.get("total_mb", 0.0),
            last_login=u.get("last_login")
        ))
    return result

@router.post("/ban")
async def ban_user(
    action: UserAction,
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: Ban a client account."""
    user = storage.users.find_one({"email": action.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if storage.set_user_status(action.email, "banned"):
        # Log admin action
        storage.log_activity(
            user_id=str(admin["_id"]),
            action_type="ban_user",
            resource_type="user",
            resource_id=str(user["_id"]),
            details={"target_email": action.email, "admin_email": admin["email"]}
        )
        return {"message": f"User {action.email} has been BANNED"}
    raise HTTPException(status_code=404, detail="User not found")

@router.post("/unban")
async def unban_user(
    action: UserAction,
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: Unban a client account."""
    user = storage.users.find_one({"email": action.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if storage.set_user_status(action.email, "active"):
        # Log admin action
        storage.log_activity(
            user_id=str(admin["_id"]),
            action_type="unban_user",
            resource_type="user",
            resource_id=str(user["_id"]),
            details={"target_email": action.email, "admin_email": admin["email"]}
        )
        return {"message": f"User {action.email} has been ACTIVATED"}
    raise HTTPException(status_code=404, detail="User not found")

@router.delete("/client")
async def delete_client(
    email: str,
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: Permanently delete a client and ALL their data."""
    user = storage.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log before deletion
    storage.log_activity(
        user_id=str(admin["_id"]),
        action_type="delete_user",
        resource_type="user",
        resource_id=str(user["_id"]),
        details={"target_email": email, "admin_email": admin["email"]}
    )
    
    count = storage.delete_user_full(email)
    if count > 0:
        return {"message": f"Permanently deleted user and {count} related records"}
    raise HTTPException(status_code=404, detail="User not found")

@router.post("/client", response_model=dict)
async def create_client_manually(
    user_in: AdminCreateUser,
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: Create a client manually and generate a temp password."""
    if storage.users.find_one({"email": user_in.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate random 12-char password
    temp_password = secrets.token_urlsafe(12)
    hashed_pw = get_password_hash(temp_password) # Make sure get_password_hash is imported from security
    
    user_id = storage.create_user(user_in.email, hashed_pw, user_in.name)
    
    # Log admin action
    storage.log_activity(
        user_id=str(admin["_id"]),
        action_type="create_user",
        resource_type="user",
        resource_id=user_id,
        details={"created_email": user_in.email, "admin_email": admin["email"]}
    )
    
    # Return the password so Admin can copy it
    return {
        "message": "User created",
        "user_id": user_id,
        "email": user_in.email,
        "temporary_password": temp_password 
    }

@router.post("/notify")
async def send_notification(
    note: AdminNotification,
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: Send an internal message to a client."""
    target_user = storage.users.find_one({"email": note.email})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    storage.create_notification(str(target_user["_id"]), note.message, note.type)
    return {"message": "Notification sent"}

@router.get("/user/{user_id}/details")
async def get_user_details(
    user_id: str,
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: Get comprehensive user information including widget settings."""
    from bson import ObjectId
    
    user = storage.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get documents
    documents = list(storage.documents.find(
        {"client_id": user_id},
        {"filename": 1, "file_size": 1, "uploaded_at": 1, "status": 1, "metadata": 1}
    ))
    
    # Convert ObjectId to string for JSON serialization
    for doc in documents:
        doc["_id"] = str(doc["_id"])
        if "uploaded_at" in doc:
            doc["uploaded_at"] = doc["uploaded_at"].isoformat() if hasattr(doc["uploaded_at"], "isoformat") else str(doc["uploaded_at"])
    
    # Get API keys
    api_keys = list(storage.api_keys.find(
        {"client_id": user_id},
        {"key_prefix": 1, "name": 1, "status": 1, "created_at": 1, "last_used": 1, "revoked_at": 1, "revoked_by": 1}
    ))
    
    for key in api_keys:
        key["_id"] = str(key["_id"])
        # Handle legacy keys
        if "name" not in key:
            key["name"] = "Legacy API Key"
        if "status" not in key:
            key["status"] = "active"
        if "created_at" in key:
            key["created_at"] = key["created_at"].isoformat() if hasattr(key["created_at"], "isoformat") else str(key["created_at"])
        if "last_used" in key:
            key["last_used"] = key["last_used"].isoformat() if hasattr(key["last_used"], "isoformat") else str(key["last_used"])
        if "revoked_at" in key and key["revoked_at"]:
            key["revoked_at"] = key["revoked_at"].isoformat() if hasattr(key["revoked_at"], "isoformat") else str(key["revoked_at"])
    
    # Get chat sessions (recent 20)
    chat_sessions = list(storage.chat_sessions.find(
        {"client_id": user_id}
    ).sort("created_at", -1).limit(20))
    
    for session in chat_sessions:
        session["_id"] = str(session["_id"])
        if "created_at" in session:
            session["created_at"] = session["created_at"].isoformat() if hasattr(session["created_at"], "isoformat") else str(session["created_at"])
        if "updated_at" in session:
            session["updated_at"] = session["updated_at"].isoformat() if hasattr(session["updated_at"], "isoformat") else str(session["updated_at"])
    
    # Get chatbot/widget customization settings
    chatbot_settings = storage.get_chatbot_settings(user_id) or {}
    
    # Get storage breakdown
    storage_info = storage.calculate_user_storage(user_id)
    
    # Format user info
    user_info = {
        "_id": str(user["_id"]),
        "email": user["email"],
        "name": user.get("name"),
        "role": user.get("role"),
        "status": user.get("status"),
        "created_at": user.get("created_at").isoformat() if user.get("created_at") and hasattr(user.get("created_at"), "isoformat") else None,
        "last_login": user.get("last_login").isoformat() if user.get("last_login") and hasattr(user.get("last_login"), "isoformat") else None,
        "login_count": user.get("login_count", 0)
    }
    
    return {
        "user": user_info,
        "documents": documents,
        "api_keys": api_keys,
        "chat_sessions": chat_sessions,
        "chatbot_settings": chatbot_settings,
        "storage": storage_info
    }

@router.delete("/user/{user_id}/document/{doc_id}")
async def delete_user_document(
    user_id: str,
    doc_id: str,
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: Delete specific user document and its vectors."""
    from bson import ObjectId
    
    # Get document info before deletion
    doc = storage.documents.find_one({"_id": ObjectId(doc_id), "client_id": user_id})
    
    success = storage.delete_document(user_id, doc_id)
    if success:
        # Log admin action
        storage.log_activity(
            user_id=str(admin["_id"]),
            action_type="delete_document",
            resource_type="document",
            resource_id=doc_id,
            details={
                "target_user_id": user_id,
                "filename": doc.get("filename") if doc else None,
                "admin_email": admin["email"]
            }
        )
        return {"message": "Document deleted successfully"}
    raise HTTPException(status_code=404, detail="Document not found")

@router.post("/user/{user_id}/api-key/{key_id}/revoke")
async def revoke_user_api_key(
    user_id: str,
    key_id: str,
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: Revoke user's API key (makes it unusable but keeps in DB)."""
    from bson import ObjectId
    
    # Get key info before revocation
    key = storage.api_keys.find_one({"_id": ObjectId(key_id), "client_id": user_id})
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Revoke the key (changes status, sends notification)
    success = storage.revoke_api_key(key_id, str(admin["_id"]))
    
    if success:
        # Log admin action
        storage.log_activity(
            user_id=str(admin["_id"]),
            action_type="revoke_api_key",
            resource_type="api_key",
            resource_id=key_id,
            details={
                "target_user_id": user_id,
                "key_name": key.get("name"),
                "key_prefix": key.get("key_prefix"),
                "admin_email": admin["email"]
            }
        )
        return {"message": "API key revoked successfully. User has been notified."}
    
    raise HTTPException(status_code=500, detail="Failed to revoke API key")

# --- Activity Log Endpoints ---

@router.get("/activity-logs")
async def get_activity_logs(
    user_id: Optional[str] = None,
    action_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: Get activity logs with filtering."""
    # Parse dates if provided
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    
    logs, total = storage.get_activity_logs(
        user_id=user_id,
        action_type=action_type,
        resource_type=resource_type,
        start_date=start_dt,
        end_date=end_dt,
        limit=limit,
        skip=skip
    )
    
    # Enrich logs with user info
    for log in logs:
        user = storage.users.find_one({"_id": ObjectId(log["user_id"])})
        log["user_email"] = user.get("email") if user else "Unknown"
        log["user_name"] = user.get("name") if user else "Unknown"
        
        # Format timestamp
        if "timestamp" in log and hasattr(log["timestamp"], "isoformat"):
            log["timestamp"] = log["timestamp"].isoformat()
    
    return {
        "logs": logs,
        "total": total,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit
    }

@router.get("/user/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    days: int = 30,
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: Get activity summary for specific user."""
    summary = storage.get_user_activity_summary(user_id, days)
    
    # Format timestamps in recent activities
    for activity in summary["recent_activities"]:
        if "timestamp" in activity and hasattr(activity["timestamp"], "isoformat"):
            activity["timestamp"] = activity["timestamp"].isoformat()
    
    return summary

# --- System Health Endpoints ---

@router.get("/system/health")
async def get_system_health(
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: Get comprehensive system health metrics."""
    from nexora001.api.health_monitor import get_system_metrics, get_database_metrics, get_qdrant_metrics
    
    system_metrics = get_system_metrics()
    database_metrics = get_database_metrics(storage)
    qdrant_metrics = get_qdrant_metrics(storage)
    
    # Overall health status
    statuses = [
        system_metrics["cpu"]["status"],
        system_metrics["memory"]["status"],
        system_metrics["disk"]["status"],
        database_metrics["status"],
        qdrant_metrics["status"]
    ]
    
    overall_status = "critical" if "critical" in statuses else "warning" if "warning" in statuses else "healthy"
    
    return {
        "overall_status": overall_status,
        "timestamp": system_metrics["timestamp"],
        "system": system_metrics,
        "mongodb": database_metrics,
        "qdrant": qdrant_metrics
    }

# --- Bulk Operations Endpoints ---

class BulkUserAction(BaseModel):
    user_ids: List[str]

class BulkBanAction(BaseModel):
    user_ids: List[str]
    action: str  # "ban" or "unban"

@router.post("/bulk/ban")
async def bulk_ban_users(
    action_data: BulkBanAction,
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: Bulk ban or unban multiple users."""
    results = {"success": [], "failed": []}
    
    for user_id in action_data.user_ids:
        try:
            user = storage.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                results["failed"].append({"user_id": user_id, "error": "User not found"})
                continue
            
            status = "banned" if action_data.action == "ban" else "active"
            storage.set_user_status(user["email"], status)
            
            # Log activity
            storage.log_activity(
                user_id=str(admin["_id"]),
                action_type=f"{action_data.action}_user",
                resource_type="user",
                resource_id=user_id,
                details={"target_email": user["email"], "admin_email": admin["email"], "bulk_operation": True}
            )
            
            results["success"].append(user_id)
        except Exception as e:
            results["failed"].append({"user_id": user_id, "error": str(e)})
    
    return results

@router.post("/bulk/delete")
async def bulk_delete_users(
    action_data: BulkUserAction,
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: Bulk delete multiple users and their data."""
    results = {"success": [], "failed": []}
    
    for user_id in action_data.user_ids:
        try:
            user = storage.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                results["failed"].append({"user_id": user_id, "error": "User not found"})
                continue
            
            # Log before deletion
            storage.log_activity(
                user_id=str(admin["_id"]),
                action_type="delete_user",
                resource_type="user",
                resource_id=user_id,
                details={"target_email": user["email"], "admin_email": admin["email"], "bulk_operation": True}
            )
            
            count = storage.delete_user_full(user["email"])
            results["success"].append({"user_id": user_id, "deleted_records": count})
        except Exception as e:
            results["failed"].append({"user_id": user_id, "error": str(e)})
    
    return results

@router.get("/export/users")
async def export_users_csv(
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: Export all users to CSV format."""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    users = list(storage.users.find())
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "id", "email", "name", "role", "status", "created_at", "last_login", "login_count"
    ])
    writer.writeheader()
    
    for user in users:
        writer.writerow({
            "id": str(user["_id"]),
            "email": user.get("email", ""),
            "name": user.get("name", ""),
            "role": user.get("role", ""),
            "status": user.get("status", "active"),
            "created_at": user.get("created_at", ""),
            "last_login": user.get("last_login", ""),
            "login_count": user.get("login_count", 0)
        })
    
    # Log export action
    storage.log_activity(
        user_id=str(admin["_id"]),
        action_type="export_users",
        resource_type="users",
        details={"format": "csv", "total_users": len(users), "admin_email": admin["email"]}
    )
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users_export.csv"}
    )

# --- GDPR Compliance Endpoints ---

@router.get("/gdpr/export/{user_id}")
async def gdpr_data_export(
    user_id: str,
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: Export all data for a user (GDPR compliance)."""
    import json
    from fastapi.responses import StreamingResponse
    import io
    
    user = storage.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Collect all user data
    data = {
        "user_profile": {
            "id": str(user["_id"]),
            "email": user.get("email"),
            "name": user.get("name"),
            "role": user.get("role"),
            "status": user.get("status"),
            "created_at": str(user.get("created_at")),
            "last_login": str(user.get("last_login")),
            "login_count": user.get("login_count", 0)
        },
        "documents": [],
        "chat_sessions": [],
        "api_keys": [],
        "crawl_jobs": [],
        "activity_logs": []
    }
    
    # Documents
    documents = list(storage.documents.find({"client_id": user_id}))
    for doc in documents:
        doc["_id"] = str(doc["_id"])
        data["documents"].append(doc)
    
    # Chat sessions
    sessions = list(storage.chat_sessions.find({"client_id": user_id}))
    for session in sessions:
        session["_id"] = str(session["_id"])
        data["chat_sessions"].append(session)
    
    # API keys
    keys = list(storage.api_keys.find({"client_id": user_id}))
    for key in keys:
        key["_id"] = str(key["_id"])
        data["api_keys"].append(key)
    
    # Crawl jobs
    crawls = list(storage.crawl_jobs.find({"client_id": user_id}))
    for crawl in crawls:
        crawl["_id"] = str(crawl["_id"])
        data["crawl_jobs"].append(crawl)
    
    # Activity logs
    logs = list(storage.activity_logs.find({"user_id": user_id}))
    for log in logs:
        log["_id"] = str(log["_id"])
        if "timestamp" in log:
            log["timestamp"] = str(log["timestamp"])
        data["activity_logs"].append(log)
    
    # Log GDPR export
    storage.log_activity(
        user_id=str(admin["_id"]),
        action_type="gdpr_export",
        resource_type="user",
        resource_id=user_id,
        details={"target_email": user.get("email"), "admin_email": admin["email"]}
    )
    
    # Create JSON file
    json_str = json.dumps(data, indent=2, default=str)
    output = io.BytesIO(json_str.encode())
    
    return StreamingResponse(
        output,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=gdpr_export_{user_id}.json"}
    )

# --- Analytics Endpoints ---

@router.get("/analytics/overview")
async def get_analytics_overview(
    days: int = 30,
    storage: MongoDBStorage = Depends(get_storage),
    admin: dict = Depends(get_current_active_superuser)
):
    """Super Admin: Get platform analytics for the last N days."""
    from datetime import timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # User registrations over time
    registrations = list(storage.users.aggregate([
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]))
    
    # Document uploads over time
    uploads = list(storage.documents.aggregate([
        {"$match": {"uploaded_at": {"$gte": start_date}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$uploaded_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]))
    
    # Activity by type
    activity_types = list(storage.activity_logs.aggregate([
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {"_id": "$action_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))
    
    # Storage by user (top 10)
    users_with_storage = storage.get_all_users_with_storage()
    top_storage_users = sorted(
        [{"email": u["email"], "storage_mb": u.get("storage", {}).get("total_mb", 0)} 
         for u in users_with_storage],
        key=lambda x: x["storage_mb"],
        reverse=True
    )[:10]
    
    # Active users (logged in within period)
    active_users = storage.users.count_documents({"last_login": {"$gte": start_date}})
    total_users = storage.users.count_documents({})
    
    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "registrations_over_time": registrations,
        "uploads_over_time": uploads,
        "activity_by_type": activity_types,
        "top_storage_users": top_storage_users,
        "active_users": active_users,
        "total_users": total_users,
        "activity_rate": round((active_users / total_users * 100) if total_users > 0 else 0, 2)
    }