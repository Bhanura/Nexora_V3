from datetime import timedelta, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from nexora001.api.security import create_access_token, verify_password, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from nexora001.api.dependencies import get_storage, get_current_user
from nexora001.storage.mongodb import MongoDBStorage

router = APIRouter()

# --- Models ---

class PasswordChange(BaseModel):
    new_password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserProfile(BaseModel):
    name: str
    email: str
    role: str
    id: str

class UpdateProfileRequest(BaseModel):
    name: str
    email: EmailStr

class ApiKeyResponse(BaseModel):
    key: str

# --- Routes ---

@router.post("/register")
async def register(
    user_in: UserRegister,
    storage: MongoDBStorage = Depends(get_storage)
):
    """Register a new client account."""
    if storage.users.find_one({"email": user_in.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = get_password_hash(user_in.password)
    user_id = storage.create_user(user_in.email, hashed_pw, user_in.name)
    
    return {"message": "Account created successfully", "user_id": user_id}

@router.post("/login")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    storage: MongoDBStorage = Depends(get_storage)
):
    """
    OAuth2 compatible token login. 
    Use this to get a 'Bearer' token for all other endpoints.
    """
    # 1. Find User
    # Note: Using your existing password hashing method (SHA256)
    user = storage.users.find_one({"email": form_data.username})
    
    # 2. Verify Password
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Check Status
    if user.get("status") == "banned":
        raise HTTPException(status_code=400, detail="Account is banned")
    
    # 3.5. Update last login timestamp and login count
    storage.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"last_login": datetime.utcnow()},
            "$inc": {"login_count": 1}
        }
    )
    
    # 3.6. Log activity
    storage.log_activity(
        user_id=str(user["_id"]),
        action_type="login",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    # 4. Generate Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "role": user.get("role", "client")},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user.get("role", "client"),
        "name": user.get("name")
    }

@router.get("/me", response_model=UserProfile)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Get current user profile."""
    return UserProfile(
        name=current_user.get("name", ""),
        email=current_user["email"],
        role=current_user.get("role", "client"),
        id=current_user["_id"]
    )

@router.put("/me")
async def update_profile(
    updates: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """Update profile details."""
    success = storage.update_user_profile(current_user["_id"], updates.dict())
    if not success:
        raise HTTPException(status_code=400, detail="Update failed")
    return {"message": "Profile updated"}

@router.post("/api-key", response_model=ApiKeyResponse)
async def generate_api_key(
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """Generate or retrieve the Widget API Key."""
    key = storage.get_or_create_api_key(current_user["_id"])
    return {"key": key}

@router.put("/password")
async def change_password(
    data: PasswordChange,
    storage: MongoDBStorage = Depends(get_storage),
    current_user: dict = Depends(get_current_user)
):
    """Allow logged-in user to change their password."""
    new_hash = get_password_hash(data.new_password)
    success = storage.update_password(current_user["_id"], new_hash)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password")
    return {"message": "Password updated successfully"}

@router.get("/storage")
async def get_user_storage_stats(
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """Get current user's storage statistics and usage."""
    user_id = current_user["_id"]
    storage_info = storage.calculate_user_storage(user_id)
    return storage_info

# ============================================================================
# API KEY MANAGEMENT ENDPOINTS
# ============================================================================

class CreateApiKeyRequest(BaseModel):
    name: str

class ApiKeyListResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    status: str
    created_at: str
    last_used: Optional[str]
    revoked_at: Optional[str]

class ApiKeyDetailResponse(BaseModel):
    id: str
    name: str
    key: str
    key_prefix: str
    status: str
    created_at: str
    last_used: Optional[str]

class UpdateApiKeyNameRequest(BaseModel):
    name: str

@router.get("/api-keys", response_model=List[ApiKeyListResponse])
async def list_api_keys(
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """Get all API keys for the current user."""
    keys = storage.list_user_api_keys(current_user["_id"])
    return [
        ApiKeyListResponse(
            id=key["_id"],
            name=key.get("name", "Legacy API Key"),  # Handle old keys without name
            key_prefix=key.get("key_prefix", key.get("key", "")[:10] + "..."),  # Generate prefix if missing
            status=key.get("status", "active"),  # Default to active for old keys
            created_at=key.get("created_at", ""),
            last_used=key.get("last_used"),
            revoked_at=key.get("revoked_at")
        )
        for key in keys
    ]

@router.post("/api-keys", response_model=ApiKeyDetailResponse)
async def create_new_api_key(
    request: CreateApiKeyRequest,
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """Create a new API key with a custom name."""
    # Check if user has reached the limit (5 keys max)
    existing_keys = storage.list_user_api_keys(current_user["_id"])
    if len(existing_keys) >= 5:
        raise HTTPException(status_code=400, detail="Maximum API key limit reached (5 keys)")
    
    new_key = storage.create_api_key(current_user["_id"], request.name)
    
    # Get the created key details
    key_doc = storage.api_keys.find_one({"key": new_key})
    
    return ApiKeyDetailResponse(
        id=str(key_doc["_id"]),
        name=key_doc["name"],
        key=key_doc["key"],
        key_prefix=key_doc["key_prefix"],
        status=key_doc["status"],
        created_at=key_doc["created_at"].isoformat(),
        last_used=key_doc.get("last_used").isoformat() if key_doc.get("last_used") else None
    )

@router.get("/api-keys/{key_id}", response_model=ApiKeyDetailResponse)
async def get_api_key_details(
    key_id: str,
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """Get full details of a specific API key including the actual key value."""
    key_doc = storage.get_api_key_details(key_id, current_user["_id"])
    if not key_doc:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return ApiKeyDetailResponse(
        id=str(key_doc["_id"]),
        name=key_doc["name"],
        key=key_doc["key"],
        key_prefix=key_doc["key_prefix"],
        status=key_doc["status"],
        created_at=key_doc["created_at"].isoformat() if isinstance(key_doc["created_at"], datetime) else key_doc["created_at"],
        last_used=key_doc.get("last_used").isoformat() if key_doc.get("last_used") and isinstance(key_doc.get("last_used"), datetime) else key_doc.get("last_used")
    )

@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """Permanently delete an API key."""
    success = storage.delete_api_key(key_id, current_user["_id"])
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key deleted successfully"}

@router.post("/api-keys/{key_id}/regenerate", response_model=ApiKeyDetailResponse)
async def regenerate_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """Regenerate an API key (creates new key value but keeps same name)."""
    new_key = storage.regenerate_api_key(key_id, current_user["_id"])
    if not new_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Get the regenerated key details
    key_doc = storage.api_keys.find_one({"key": new_key})
    
    return ApiKeyDetailResponse(
        id=str(key_doc["_id"]),
        name=key_doc["name"],
        key=key_doc["key"],
        key_prefix=key_doc["key_prefix"],
        status=key_doc["status"],
        created_at=key_doc["created_at"].isoformat(),
        last_used=key_doc.get("last_used").isoformat() if key_doc.get("last_used") else None
    )

@router.patch("/api-keys/{key_id}")
async def update_api_key_name(
    key_id: str,
    request: UpdateApiKeyNameRequest,
    current_user: dict = Depends(get_current_user),
    storage: MongoDBStorage = Depends(get_storage)
):
    """Update the name of an API key."""
    success = storage.update_api_key_name(key_id, current_user["_id"], request.name)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key name updated successfully"}