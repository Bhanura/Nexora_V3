"""
MongoDB storage operations for eLanka Chat AI - Multi-Tenant Edition.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from bson import ObjectId
import os
import secrets
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the project root explicitly (prevents loading wrong .env file)
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env", override=True)

class MongoDBStorage:
    def __init__(self, uri: Optional[str] = None, database: Optional[str] = None):
        self.uri = uri or os.getenv("MONGODB_URI")
        self.database_name = database or os.getenv("MONGODB_DATABASE", "elanka_chat_ai")
        
        if not self.uri:
            raise ValueError("MongoDB URI not provided")
        
        self.client: MongoClient = MongoClient(self.uri)
        self.db: Database = self.client[self.database_name]
        
        # --- UPDATED COLLECTIONS ---
        self.users: Collection = self.db["users"]            # NEW: Stores user creds
        self.documents: Collection = self.db["documents"]
        self.crawl_jobs: Collection = self.db["crawl_jobs"]
        self.api_keys: Collection = self.db["api_keys"]      # NEW: Stores widget keys
        self.chat_sessions: Collection = self.db["chat_sessions"]  # NEW: Stores chat history
        self.user_submissions: Collection = self.db["user_submissions"]  # FEATURE 2: User data submissions
        self.activity_logs: Collection = self.db["activity_logs"]  # PHASE 3: Activity logging
        self.token_usage: Collection = self.db["token_usage"]  # NEW: AI token usage tracking
        
        self._create_indexes()
    
    def _create_indexes(self):
        """Create indexes safely, handling conflicts."""
        try:
            # NEW: Filter by client_id first, then source_url
            self.documents.create_index([("client_id", ASCENDING), ("metadata.source_url", ASCENDING)])
        except Exception:
            pass  # Index already exists
        
        try:
            self.users.create_index("email", unique=True)
        except Exception:
            pass
        
        try:
            self.api_keys.create_index("key", unique=True)
        except Exception:
            pass
        
        try:
            self.crawl_jobs.create_index([("client_id", ASCENDING)])
        except Exception:
            pass
        
        try:
            self.chat_sessions.create_index("session_id", unique=True)
        except Exception:
            pass
        
        try:
            self.user_submissions.create_index([("client_id", ASCENDING), ("submitted_at", ASCENDING)])
        except Exception:
            pass
        
        try:
            self.activity_logs.create_index([("user_id", ASCENDING), ("timestamp", ASCENDING)])
        except Exception:
            pass
        
        try:
            self.activity_logs.create_index("timestamp", expireAfterSeconds=7776000)  # 90 days retention
        except Exception:
            pass

        try:
            self.token_usage.create_index([("client_id", ASCENDING), ("timestamp", ASCENDING)])
        except Exception:
            pass
        
        # For last_active, keep the existing index with TTL if it exists
        # Don't try to recreate it
        try:
            existing_indexes = self.chat_sessions.index_information()
            if "last_active_1" not in existing_indexes:
                # Only create if it doesn't exist at all
                self.chat_sessions.create_index("last_active", expireAfterSeconds=1800)
        except Exception:
            pass  # Index exists or cannot be created

    # ==========================================
    # 1. AUTH & USER MANAGEMENT
    # ==========================================
    def create_user(self, email: str, password_hash: str, name: str) -> str:
        user = {
            "email": email,
            "password_hash": password_hash,
            "name": name,
            "role": "client_admin",
            "created_at": datetime.utcnow(),
            "status": "active",
            # Chatbot customization defaults
            "chatbot_name": "AI Assistant",
            "chatbot_greeting": "Hello! How can I help you today?",
            "chatbot_personality": "friendly and helpful",
            "theme_color": "#007bff",
            "reset_code": None,
            "reset_code_expires": None
        }
        return str(self.users.insert_one(user).inserted_id)

    def update_user_profile(self, user_id: str, updates: Dict) -> bool:
            """Update user details (name, email, etc)."""
            # Protect against changing role/id/password via this simple method
            safe_updates = {k: v for k, v in updates.items() if k in ['name', 'email']}
            if not safe_updates: return False
            
            result = self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": safe_updates}
            )
            return result.modified_count > 0

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        return self.users.find_one({"_id": ObjectId(user_id)})

    def update_chatbot_settings(self, client_id: str, settings: Dict) -> bool:
        """Update chatbot customization settings for a client."""
        result = self.users.update_one(
            {"_id": ObjectId(client_id)},
            {"$set": settings}
        )
        return result.matched_count > 0

    def get_chatbot_settings(self, client_id: str) -> Optional[Dict]:
        """Retrieve chatbot settings for a client with defaults."""
        user = self.users.find_one({"_id": ObjectId(client_id)})
        if not user:
            return None
        
        return {
            "chatbot_name": user.get("chatbot_name", "AI Assistant"),
            "chatbot_greeting": user.get("chatbot_greeting", "Hello! How can I help you today?"),
            "chatbot_personality": user.get("chatbot_personality", "friendly and helpful"),
            "theme_color": user.get("theme_color", "#007bff")
        }

    # ==========================================
    # 2. API KEY
    # ==========================================

    def get_or_create_api_key(self, client_id: str) -> str:
        """Return existing active key if found, otherwise create new one. Legacy method for backward compatibility."""
        existing = self.api_keys.find_one({"client_id": client_id, "status": "active"})
        if existing:
            return existing["key"]
            
        # Create new key with default name
        return self.create_api_key(client_id, "Default API Key")
    
    def create_api_key(self, client_id: str, name: str) -> str:
        """Create a new API key with a name."""
        key = f"nx_{secrets.token_urlsafe(24)}"
        key_prefix = key[:10] + "..."
        
        self.api_keys.insert_one({
            "key": key,
            "key_prefix": key_prefix,
            "client_id": client_id,
            "name": name,
            "status": "active",
            "created_at": datetime.utcnow(),
            "last_used": None,
            "revoked_at": None,
            "revoked_by": None,
            "allowed_domains": []
        })
        return key
    
    def list_user_api_keys(self, client_id: str) -> List[Dict]:
        """Get all API keys for a user."""
        keys = list(self.api_keys.find(
            {"client_id": client_id}
        ).sort("created_at", -1))
        
        for key in keys:
            key["_id"] = str(key["_id"])
            # Handle legacy keys without new schema fields
            if "name" not in key:
                key["name"] = "Legacy API Key"
            if "key_prefix" not in key and "key" in key:
                key["key_prefix"] = key["key"][:10] + "..."
            if "status" not in key:
                key["status"] = "active"
            # Format dates
            if key.get("created_at"):
                key["created_at"] = key["created_at"].isoformat() if hasattr(key["created_at"], "isoformat") else str(key["created_at"])
            if key.get("last_used"):
                key["last_used"] = key["last_used"].isoformat() if hasattr(key["last_used"], "isoformat") else str(key["last_used"])
            if key.get("revoked_at"):
                key["revoked_at"] = key["revoked_at"].isoformat() if hasattr(key["revoked_at"], "isoformat") else str(key["revoked_at"])
            # Remove the actual key from response for security
            key.pop("key", None)
        
        return keys
    
    def get_api_key_details(self, key_id: str, client_id: str) -> Optional[Dict]:
        """Get full details of a specific API key including the actual key value."""
        key_doc = self.api_keys.find_one({"_id": ObjectId(key_id), "client_id": client_id})
        if key_doc:
            key_doc["_id"] = str(key_doc["_id"])
            return key_doc
        return None
    
    def delete_api_key(self, key_id: str, client_id: str) -> bool:
        """Permanently delete an API key (client admin action)."""
        result = self.api_keys.delete_one({"_id": ObjectId(key_id), "client_id": client_id})
        return result.deleted_count > 0
    
    def revoke_api_key(self, key_id: str, admin_id: str, notification_msg: str = None) -> bool:
        """Revoke an API key (super admin action). Keeps in DB but makes unusable."""
        result = self.api_keys.update_one(
            {"_id": ObjectId(key_id)},
            {
                "$set": {
                    "status": "revoked",
                    "revoked_at": datetime.utcnow(),
                    "revoked_by": admin_id
                }
            }
        )
        
        if result.modified_count > 0:
            # Get the key to find client_id and send notification
            key_doc = self.api_keys.find_one({"_id": ObjectId(key_id)})
            if key_doc:
                msg = notification_msg or "Your API key was revoked. Please contact admins for more information."
                self.create_notification(key_doc["client_id"], msg, "warning")
        
        return result.modified_count > 0
    
    def regenerate_api_key(self, key_id: str, client_id: str) -> Optional[str]:
        """Regenerate an API key (keeps same name and metadata)."""
        old_key = self.api_keys.find_one({"_id": ObjectId(key_id), "client_id": client_id})
        if not old_key:
            return None
        
        new_key = f"nx_{secrets.token_urlsafe(24)}"
        new_key_prefix = new_key[:10] + "..."
        
        self.api_keys.update_one(
            {"_id": ObjectId(key_id)},
            {
                "$set": {
                    "key": new_key,
                    "key_prefix": new_key_prefix,
                    "status": "active",
                    "created_at": datetime.utcnow(),
                    "last_used": None,
                    "revoked_at": None,
                    "revoked_by": None
                }
            }
        )
        return new_key
    
    def update_api_key_name(self, key_id: str, client_id: str, new_name: str) -> bool:
        """Update the name of an API key."""
        result = self.api_keys.update_one(
            {"_id": ObjectId(key_id), "client_id": client_id},
            {"$set": {"name": new_name}}
        )
        return result.modified_count > 0

    def update_api_key(self, key_id: str, client_id: str, updates: Dict) -> bool:
        """Update fields of an API key."""
        set_fields = {}
        if "name" in updates:
            set_fields["name"] = updates["name"]
        if "allowed_domains" in updates:
            domains = []
            for d in updates["allowed_domains"]:
                d_clean = d.strip().lower()
                if d_clean:
                    domains.append(d_clean)
            set_fields["allowed_domains"] = domains
            
        if not set_fields:
            return False
            
        result = self.api_keys.update_one(
            {"_id": ObjectId(key_id), "client_id": str(client_id)},
            {"$set": set_fields}
        )
        return result.modified_count > 0 or result.matched_count > 0

    def validate_api_key(self, key: str) -> Optional[str]:
        """Validate API key and return client_id if valid and active."""
        doc = self.api_keys.find_one({"key": key})
        if doc:
            # Check if key is active
            if doc.get("status") != "active":
                return None
            
            # Check if user is banned
            user = self.users.find_one({"_id": ObjectId(doc['client_id'])})
            if user and user.get('status') == 'banned':
                return None
            
            # Update last_used timestamp
            self.api_keys.update_one(
                {"_id": doc["_id"]},
                {"$set": {"last_used": datetime.utcnow()}}
            )
            
            return doc['client_id']
        return None

    # ==========================================
    # 3. SUPER ADMIN ACTIONS
    # ==========================================

    def get_all_users(self) -> List[Dict]:
        users = list(self.users.find({}, {"password_hash": 0}))
        for user in users:
            uid = str(user["_id"])
            user["doc_count"] = self.documents.count_documents({"client_id": uid})
            user["api_keys"] = self.api_keys.count_documents({"client_id": uid})
        return users
    
    def calculate_user_storage(self, client_id: str) -> Dict[str, Any]:
        """Calculate total storage used by user (all data types)."""
        try:
            import sys
            
            # 1. Document files (actual uploaded files)
            docs = list(self.documents.find({"client_id": client_id}))
            doc_size = sum(doc.get("file_size", 0) for doc in docs)
            doc_count = len(docs)
            
            # 2. Qdrant vectors (embeddings)
            vector_count = 0
            vector_size = 0
            try:
                from qdrant_client import QdrantClient
                qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
                qdrant = QdrantClient(url=qdrant_url)
                collection_name = f"client_{client_id}"
                collection_info = qdrant.get_collection(collection_name)
                vector_count = collection_info.vectors_count or 0
                # Estimate: ~1KB per vector (768 dimensions * 4 bytes + metadata)
                vector_size = vector_count * 1024
            except Exception:
                pass  # Collection doesn't exist or Qdrant unavailable
            
            # 3. Chat sessions (conversation history)
            chat_sessions = list(self.chat_sessions.find({"client_id": client_id}))
            chat_size = sum(sys.getsizeof(str(session)) for session in chat_sessions)
            chat_count = len(chat_sessions)
            
            # 4. Crawl jobs (scraped web content)
            crawl_jobs = list(self.crawl_jobs.find({"client_id": client_id}))
            crawl_size = sum(sys.getsizeof(str(job)) for job in crawl_jobs)
            crawl_count = len(crawl_jobs)
            
            # 5. User submissions (form data from Feature 2)
            submissions = list(self.user_submissions.find({"client_id": client_id}))
            submission_size = sum(sys.getsizeof(str(sub)) for sub in submissions)
            submission_count = len(submissions)
            
            # 6. Document metadata and chunks (stored in MongoDB)
            # Estimate: Each document has chunks stored as text
            metadata_size = 0
            for doc in docs:
                # Chunks are typically stored in document or separate collection
                chunks = doc.get("chunks", [])
                metadata_size += sys.getsizeof(str(chunks))
            
            # Calculate totals
            total_bytes = (
                doc_size +           # Actual files
                vector_size +        # Qdrant vectors
                chat_size +          # Chat history
                crawl_size +         # Crawled content
                submission_size +    # Form submissions
                metadata_size        # Chunks & metadata
            )
            total_mb = round(total_bytes / (1024 * 1024), 2)
            
            return {
                "total_bytes": total_bytes,
                "total_mb": total_mb,
                "documents_bytes": doc_size,
                "vectors_bytes": vector_size,
                "chat_sessions_bytes": chat_size,
                "crawl_jobs_bytes": crawl_size,
                "submissions_bytes": submission_size,
                "metadata_bytes": metadata_size,
                "vector_count": vector_count,
                "document_count": doc_count,
                "chat_session_count": chat_count,
                "crawl_job_count": crawl_count,
                "submission_count": submission_count,
                "breakdown": {
                    "documents": f"{round(doc_size / (1024 * 1024), 2)} MB",
                    "vectors": f"{round(vector_size / (1024 * 1024), 2)} MB",
                    "chats": f"{round(chat_size / (1024 * 1024), 2)} MB",
                    "crawls": f"{round(crawl_size / (1024 * 1024), 2)} MB",
                    "submissions": f"{round(submission_size / (1024 * 1024), 2)} MB",
                    "metadata": f"{round(metadata_size / (1024 * 1024), 2)} MB"
                }
            }
        except Exception as e:
            # Return empty stats on error
            return {
                "total_bytes": 0,
                "total_mb": 0.0,
                "documents_bytes": 0,
                "vectors_bytes": 0,
                "chat_sessions_bytes": 0,
                "crawl_jobs_bytes": 0,
                "submissions_bytes": 0,
                "metadata_bytes": 0,
                "vector_count": 0,
                "document_count": 0,
                "chat_session_count": 0,
                "crawl_job_count": 0,
                "submission_count": 0,
                "breakdown": {}
            }
    
    def get_all_users_with_storage(self) -> List[Dict]:
        """Get all users with storage calculations included."""
        users = list(self.users.find({}, {"password_hash": 0}))
        for user in users:
            uid = str(user["_id"])
            user["api_keys"] = self.api_keys.count_documents({"client_id": uid})
            user["storage"] = self.calculate_user_storage(uid)
        return users

    def set_user_status(self, email: str, status: str) -> bool:
        """Ban or Unban a user (status: 'active' or 'banned')."""
        result = self.users.update_one(
            {"email": email},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0

    def delete_user_full(self, email: str) -> int:
        """
        Hard Delete: Removes User + Documents + Keys + Jobs + Chats.
        Returns total deleted count.
        """
        user = self.users.find_one({"email": email})
        if not user: return 0
        
        uid = str(user["_id"])
        
        # Cascade delete
        d1 = self.documents.delete_many({"client_id": uid}).deleted_count
        d2 = self.api_keys.delete_many({"client_id": uid}).deleted_count
        d3 = self.crawl_jobs.delete_many({"client_id": uid}).deleted_count
        d4 = self.users.delete_one({"_id": user["_id"]}).deleted_count
        
        return d1 + d2 + d3 + d4

    # ==========================================
    # 4. DOCUMENT MANAGEMENT
    # ==========================================
    def store_document(self, client_id: str, content: str, source_url: str, source_type: str = "web", title: str = None, metadata: Dict = None) -> str:
        # NOTICE: client_id is now the FIRST required argument
        doc = {
            "client_id": client_id,  # <--- DATA ISOLATION
            "content": content,
            "metadata": {
                "source_url": source_url,
                "source_type": source_type,
                "title": title or source_url,
                "crawled_at": datetime.utcnow(),
                **(metadata or {})
            }
        }
        return str(self.documents.insert_one(doc).inserted_id)

    def store_document_with_embedding(self, client_id: str, content: str, embedding: List[float], source_url: str, source_type: str = "web", title: str = None, chunk_index: int = 0, total_chunks: int = 1, metadata: Dict = None) -> str:
        doc = {
            "client_id": client_id,  # <--- DATA ISOLATION
            "content": content,
            "embedding": embedding,
            "metadata": {
                "source_url": source_url,
                "source_type": source_type,
                "title": title or source_url,
                "crawled_at": datetime.utcnow(),
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
                **(metadata or {})
            }
        }
        return str(self.documents.insert_one(doc).inserted_id)

    # --- UPDATED SEARCH METHODS ---
    def vector_search(self, client_id: str, query_embedding: List[float],
                    limit: int = 5, min_score: float = 0.0) -> List[Dict]:
        """
        Optimized vector search using MongoDB Atlas Search.
        Falls back to Python if Atlas Search fails.
        """
        import time
        
        try:
            # Try MongoDB Atlas Vector Search first (FAST - 0.1-0.3s)
            start = time.time()
            
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",
                        "path": "embedding",
                        "queryVector": query_embedding,
                        "numCandidates": min(limit * 20, 200),
                        "limit": limit,
                        "filter": {"client_id": client_id}
                    }
                },
                {
                    "$match": {
                        "$expr": {"$gte": [{"$meta": "vectorSearchScore"}, min_score]}
                    }
                },
                {
                    "$project": {
                        "content": 1,
                        "metadata": 1,
                        "similarity_score": {"$meta": "vectorSearchScore"},
                        "_id": 1
                    }
                }
            ]
            
            results = list(self.documents.aggregate(pipeline))
            elapsed = time.time() - start
            
            if len(results) == 0:
                print(f"⚠️  Atlas Search returned 0 results")
                print(f"   Checking total docs for client: {client_id}")
                total = self.documents.count_documents({"client_id": client_id, "embedding": {"$exists": True}})
                print(f"   Total docs available: {total}")
                if total == 0:
                    print(f"   ❌ No documents found for this client!")
                else:
                    print(f"   ⚠️  Documents exist but similarity too low. Try lowering min_score.")
            else:
                print(f"✅ Atlas Vector Search: {len(results)} results in {elapsed:.3f}s")
            
            return results
            
        except Exception as e:
            # Fallback to Python implementation (SLOW - 8-12s)
            print(f"⚠️  Atlas Vector Search unavailable: {str(e)[:100]}")
            print(f"   Falling back to Python search (slower)")
            
            start = time.time()
            candidates = list(self.documents.find(
                {"client_id": client_id, "embedding": {"$exists": True}}, 
                {"content": 1, "embedding": 1, "metadata": 1}
            ))
            
            results = []
            for doc in candidates:
                score = self._cosine_similarity(query_embedding, doc['embedding'])
                if score >= min_score:
                    doc['similarity_score'] = score
                    del doc['embedding']
                    results.append(doc)
            
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            elapsed = time.time() - start
            print(f"⚠️  Python Search: {len(results[:limit])} results in {elapsed:.3f}s")
            return results[:limit]

    
    def close(self):
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def url_exists(self, client_id: str, source_url: str) -> bool:
        """Check if a URL has already been crawled by THIS client."""
        return self.documents.count_documents(
            {"client_id": client_id, "metadata.source_url": source_url}
        ) > 0

    def count_documents(self, client_id: str) -> int:
        """Count total documents for a specific client."""
        return self.documents.count_documents({"client_id": client_id})

    def delete_document_by_id(self, client_id: str, doc_id: str) -> bool:
        """Delete a single document chunk by its MongoDB _id."""
        try:
            # We must convert the string ID to a MongoDB ObjectId
            from bson import ObjectId
            result = self.documents.delete_one(
                {"_id": ObjectId(doc_id), "client_id": client_id}
            )
            return result.deleted_count > 0
        except Exception:
            return False

    def delete_by_url(self, client_id: str, source_url: str) -> int:
        """Delete a client's documents for a specific URL."""
        result = self.documents.delete_many(
            {"client_id": client_id, "metadata.source_url": source_url}
        )
        return result.deleted_count
    
    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2): 
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0: 
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def add_chat_message(self, session_id: str, role: str, content: str):
        """Add a message to a chat session."""
        self.chat_sessions.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": {"role": role, "content": content, "timestamp": datetime.utcnow()}},
                "$set": {"last_active": datetime.utcnow()}
            },
            upsert=True
        )

    def delete_chat_session(self, session_id: str) -> bool:
        """Delete a chat session's history."""
        result = self.chat_sessions.delete_one({"session_id": session_id})
        return result.deleted_count > 0

    # ==========================================
    # 6. CRAWL JOB MANAGEMENT
    # ==========================================

    def create_crawl_job(self, client_id: str, url: str, options: Dict = None) -> str:
        """Create a new crawl job record."""
        job = {
            "client_id": client_id,
            "url": url,
            "status": "running",
            "pages_crawled": 0,
            "documents_created": 0,
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "error_message": None,
            "options": options or {}
        }
        result = self.crawl_jobs.insert_one(job)
        return str(result.inserted_id)

    def update_crawl_job(self, job_id: str, status: str = None, pages_crawled: int = None, documents_created: int = None, error_message: str = None):
        """Update an existing crawl job."""
        updates = {}
        if status:
            updates["status"] = status
            if status in ["completed", "failed"]:
                updates["completed_at"] = datetime.utcnow()
        
        if pages_crawled is not None:
            updates["pages_crawled"] = pages_crawled
        if documents_created is not None:
            updates["documents_created"] = documents_created
        if error_message:
            updates["error_message"] = error_message
        
        if updates:
            self.crawl_jobs.update_one(
                {"_id": ObjectId(job_id)}, 
                {"$set": updates}
            )

    def get_user_crawl_jobs(self, client_id: str, limit: int = 20, skip: int = 0) -> List[Dict]:
        """Get recent crawl jobs for a specific user."""
        jobs = list(
            self.crawl_jobs.find({"client_id": client_id})
            .sort("started_at", -1)  # Most recent first
            .skip(skip)
            .limit(limit)
        )
        
        # Convert ObjectId to string
        for job in jobs:
            job["_id"] = str(job["_id"])
            if job.get("started_at"):
                job["started_at"] = job["started_at"].isoformat()
            if job.get("completed_at"):
                job["completed_at"] = job["completed_at"].isoformat()
        
        return jobs

    # ==========================================
    # 7. SUPER ADMIN METHODS
    # ==========================================
    
    def get_all_users(self) -> List[Dict]:
        """Super Admin: Get list of all clients with usage stats."""
        users = list(self.users.find({}, {"password_hash": 0})) # Hide passwords
        
        # Attach usage stats to each user
        for user in users:
            user_id = str(user["_id"])
            user["doc_count"] = self.documents.count_documents({"client_id": user_id})
            user["api_keys"] = self.api_keys.count_documents({"client_id": user_id})
            
        return users

    def ban_user(self, email: str) -> bool:
        """Super Admin: Ban a client."""
        result = self.users.update_one(
            {"email": email},
            {"$set": {"status": "banned"}}
        )
        return result.modified_count > 0

    def unban_user(self, email: str) -> bool:
        """Super Admin: Activate a client."""
        result = self.users.update_one(
            {"email": email},
            {"$set": {"status": "active"}}
        )
        return result.modified_count > 0
        
    def validate_api_key(self, key: str) -> Optional[str]:
        """Widget: Get client_id from API key."""
        doc = self.api_keys.find_one({"key": key})
        if doc:
            # Check if the OWNER is banned
            user = self.users.find_one({"_id": ObjectId(doc['client_id'])})
            if user and user.get('status') == 'banned':
                return None
            return doc['client_id']
        return None
    
    def get_stats(self, client_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about documents in the database."""
        try:
            # Build filter
            filter_query = {}
            if client_id:
                filter_query["client_id"] = client_id
            
            # Total documents
            total_documents = self.documents.count_documents(filter_query)
            
            # Get unique sources
            sources_pipeline = [
                {"$match": filter_query} if filter_query else {"$match": {}},
                {"$group": {"_id": "$metadata.source_url"}},
                {"$count": "total"}
            ]
            sources_result = list(self.documents.aggregate(sources_pipeline))
            unique_sources = sources_result[0]["total"] if sources_result else 0
            
            # Calculate average chunk size
            avg_pipeline = [
                {"$match": filter_query} if filter_query else {"$match": {}},
                {"$group": {"_id": None, "avg_size": {"$avg": {"$strLenCP": "$content"}}}}
            ]
            avg_result = list(self.documents.aggregate(avg_pipeline))
            avg_chunk_size = int(avg_result[0]["avg_size"]) if avg_result else 0
            
            # Get list of sources
            sources_list_pipeline = [
                {"$match": filter_query} if filter_query else {"$match": {}},
                {"$group": {
                    "_id": "$metadata.source_url",
                    "count": {"$sum": 1},
                    "type": {"$first": "$metadata.source_type"},
                    "total_characters": {"$sum": {"$strLenCP": "$content"}},
                    "crawled_at": {"$first": "$metadata.crawled_at"}
                }},
                {"$limit": 100}  # Limit to avoid huge result sets
            ]
            sources_data = list(self.documents.aggregate(sources_list_pipeline))
            sources = [
                {
                    "url": item["_id"],
                    "count": item["count"],
                    "type": item.get("type", "unknown"),
                    "total_characters": item.get("total_characters", 0),
                    "crawled_at": item.get("crawled_at")
                }
                for item in sources_data
            ]
            
            return {
                "total_documents": total_documents,
                "unique_sources": unique_sources,
                "avg_chunk_size": avg_chunk_size,
                "sources": sources
            }
        except Exception as e:
            # Return empty stats on error
            return {
                "total_documents": 0,
                "unique_sources": 0,
                "avg_chunk_size": 0,
                "sources": []
            }
            
# --- NOTIFICATIONS SYSTEM ---
    def create_notification(self, user_id: str, message: str, type: str = "info") -> bool:
        """Create a notification for a specific user."""
        self.db["notifications"].insert_one({
            "user_id": user_id,
            "message": message,
            "type": type, # 'info', 'warning', 'promo'
            "read": False,
            "created_at": datetime.utcnow()
        })
        return True

    def get_user_notifications(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get unread or recent notifications."""
        return list(self.db["notifications"].find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit))

    def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark as read."""
        res = self.db["notifications"].update_one(
            {"_id": ObjectId(notification_id), "user_id": user_id},
            {"$set": {"read": True}}
        )
        return res.modified_count > 0
    
    # --- UPDATED AUTH ---
    def update_password(self, user_id: str, new_hash: str) -> bool:
        """Update user password."""
        res = self.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password_hash": new_hash}}
        )
        return res.modified_count > 0
    
    # ==========================================
    # 9. USER DATA COLLECTION (FEATURE 2)
    # ==========================================
    
    def update_data_collection_settings(self, client_id: str, settings: Dict[str, Any]) -> bool:
        """Update user data collection settings for a client."""
        # Build $set dict only with provided fields
        set_fields = {}
        if "enabled" in settings:
            set_fields["data_collection_enabled"] = settings["enabled"]
        if "custom_fields" in settings:
            set_fields["custom_fields"] = settings["custom_fields"]
        if "data_collection_timing" in settings:
            set_fields["data_collection_timing"] = settings["data_collection_timing"]
        if "data_collection_message" in settings:
            set_fields["data_collection_message"] = settings["data_collection_message"]
        if "notification_emails" in settings:
            set_fields["notification_emails"] = settings["notification_emails"]
        
        if not set_fields:
            return False
        
        result = self.users.update_one(
            {"_id": ObjectId(client_id)},
            {"$set": set_fields}
        )
        return result.modified_count > 0 or result.matched_count > 0
    
    def get_data_collection_settings(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get user data collection settings for a client."""
        user = self.users.find_one({"_id": ObjectId(client_id)})
        if not user:
            return None
        
        return {
            "enabled": user.get("data_collection_enabled", False),
            "custom_fields": user.get("custom_fields", []),
            "data_collection_timing": user.get("data_collection_timing", "after_first_message"),
            "data_collection_message": user.get("data_collection_message", "Please share your details:"),
            "notification_emails": user.get("notification_emails", [])
        }
    
    def save_user_submission(
        self,
        client_id: str,
        session_id: str,
        submitted_data: Dict[str, Any]
    ) -> str:
        """
        Save a user data submission.
        
        Returns:
            Submission ID
        """
        submission = {
            "client_id": client_id,
            "session_id": session_id,
            "submitted_data": submitted_data,
            "submitted_at": datetime.utcnow()
        }
        result = self.user_submissions.insert_one(submission)
        return str(result.inserted_id)
    
    def get_user_submissions(
        self,
        client_id: str,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get user submissions for a client with pagination.
        
        Returns:
            Tuple of (submissions list, total count)
        """
        query = {"client_id": client_id}
        
        total = self.user_submissions.count_documents(query)
        
        submissions = list(
            self.user_submissions
            .find(query)
            .sort("submitted_at", -1)
            .skip((page - 1) * page_size)
            .limit(page_size)
        )
        
        # Convert ObjectId to string
        for sub in submissions:
            sub["submission_id"] = str(sub.pop("_id"))
        
        return submissions, total
    
    def delete_user_submission(self, submission_id: str, client_id: str) -> bool:
        """
        Delete a user submission (only if it belongs to the client).
        
        Returns:
            True if deleted, False if not found or not owned by client
        """
        result = self.user_submissions.delete_one({
            "_id": ObjectId(submission_id),
            "client_id": client_id
        })
        return result.deleted_count > 0

    # ==========================================
    # 10. ACTIVITY LOGGING
    # ==========================================
    def log_activity(
        self,
        user_id: str,
        action_type: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Log user activity for audit trail.
        
        Args:
            user_id: User performing the action
            action_type: Type of action (login, logout, upload, delete, create, update, etc.)
            resource_type: Type of resource (document, api_key, user, chat_session, etc.)
            resource_id: ID of the resource affected
            details: Additional context (e.g., filename, previous values)
            ip_address: User's IP address
            user_agent: User's browser/client info
            
        Returns:
            Activity log ID
        """
        log_entry = {
            "user_id": user_id,
            "action_type": action_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow()
        }
        return str(self.activity_logs.insert_one(log_entry).inserted_id)
    
    def get_activity_logs(
        self,
        user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        skip: int = 0
    ) -> tuple[List[Dict], int]:
        """
        Retrieve activity logs with filtering and pagination.
        
        Returns:
            Tuple of (logs list, total count)
        """
        query = {}
        
        if user_id:
            query["user_id"] = user_id
        if action_type:
            query["action_type"] = action_type
        if resource_type:
            query["resource_type"] = resource_type
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date
        
        total = self.activity_logs.count_documents(query)
        logs = list(
            self.activity_logs
            .find(query)
            .sort("timestamp", -1)
            .skip(skip)
            .limit(limit)
        )
        
        # Convert ObjectId to string
        for log in logs:
            log["_id"] = str(log["_id"])
        
        return logs, total
    
    def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get activity summary for a user over the last N days.
        
        Returns:
            Dictionary with action type counts and recent activities
        """
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get action type counts
        pipeline = [
            {"$match": {"user_id": user_id, "timestamp": {"$gte": start_date}}},
            {"$group": {"_id": "$action_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        action_counts = {item["_id"]: item["count"] for item in self.activity_logs.aggregate(pipeline)}
        
        # Get recent activities
        recent_logs = list(
            self.activity_logs
            .find({"user_id": user_id})
            .sort("timestamp", -1)
            .limit(10)
        )
        
        for log in recent_logs:
            log["_id"] = str(log["_id"])
        
        return {
            "action_counts": action_counts,
            "recent_activities": recent_logs,
            "total_actions": sum(action_counts.values())
        }

    def log_token_usage(self, client_id: str, session_id: str, prompt_tokens: int, completion_tokens: int, total_tokens: int, model: str = "gemini-2.5-flash"):
        """Log AI token usage."""
        self.token_usage.insert_one({
            "client_id": client_id,
            "session_id": session_id,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "model": model,
            "timestamp": datetime.utcnow()
        })

    def get_token_usage_stats(self, client_id: str) -> Dict:
        """Get token usage statistics for a client."""
        pipeline = [
            {"$match": {"client_id": client_id}},
            {"$group": {
                "_id": None,
                "total_tokens": {"$sum": "$total_tokens"},
                "total_prompt_tokens": {"$sum": "$prompt_tokens"},
                "total_completion_tokens": {"$sum": "$completion_tokens"}
            }}
        ]
        result = list(self.token_usage.aggregate(pipeline))
        if not result:
            return {
                "total_tokens": 0,
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "daily_usage": [],
                "top_sessions": []
            }

        stats = result[0]
        del stats["_id"]

        # Daily usage
        daily_pipeline = [
            {"$match": {"client_id": client_id}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                "total_tokens": {"$sum": "$total_tokens"}
            }},
            {"$sort": {"_id": 1}}
        ]
        stats["daily_usage"] = list(self.token_usage.aggregate(daily_pipeline))

        # Top active sessions
        session_pipeline = [
            {"$match": {"client_id": client_id}},
            {"$group": {
                "_id": "$session_id",
                "total_tokens": {"$sum": "$total_tokens"}
            }},
            {"$sort": {"total_tokens": -1}},
            {"$limit": 10}
        ]
        stats["top_sessions"] = list(self.token_usage.aggregate(session_pipeline))

        return stats

    def get_all_users_token_usage(self, days: int = 30) -> List[Dict[str, Any]]:
        """Super Admin: Get aggregate token usage for all users."""
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {"$group": {
                "_id": "$client_id",
                "total_tokens": {"$sum": "$total_tokens"},
                "prompt_tokens": {"$sum": "$prompt_tokens"},
                "completion_tokens": {"$sum": "$completion_tokens"},
                "request_count": {"$sum": 1}
            }}
        ]
        results = list(self.token_usage.aggregate(pipeline))
        usage_by_client = {item["_id"]: item for item in results}
        
        # Merge with user details
        users = list(self.users.find({}, {"password_hash": 0}))
        for user in users:
            uid = str(user["_id"])
            stats = usage_by_client.get(uid, {
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "request_count": 0
            })
            user["token_usage"] = {
                "total_tokens": stats["total_tokens"],
                "prompt_tokens": stats["prompt_tokens"],
                "completion_tokens": stats["completion_tokens"],
                "request_count": stats["request_count"]
            }
            # Make sure _id is string
            user["_id"] = str(user["_id"])
            if "created_at" in user and hasattr(user["created_at"], "isoformat"):
                user["created_at"] = user["created_at"].isoformat()
        return users

def get_storage():
    return MongoDBStorage()