"""
System health monitoring utilities for Nexora001.
"""

import psutil
import os
from typing import Dict, Any
from datetime import datetime


def get_system_metrics() -> Dict[str, Any]:
    """
    Collect system resource metrics.
    
    Returns:
        Dictionary containing CPU, memory, disk metrics
    """
    # CPU Usage
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    
    # Memory Usage
    memory = psutil.virtual_memory()
    memory_total_gb = memory.total / (1024 ** 3)
    memory_used_gb = memory.used / (1024 ** 3)
    memory_available_gb = memory.available / (1024 ** 3)
    memory_percent = memory.percent
    
    # Disk Usage
    disk = psutil.disk_usage('/')
    disk_total_gb = disk.total / (1024 ** 3)
    disk_used_gb = disk.used / (1024 ** 3)
    disk_free_gb = disk.free / (1024 ** 3)
    disk_percent = disk.percent
    
    # Network Stats
    net_io = psutil.net_io_counters()
    bytes_sent_mb = net_io.bytes_sent / (1024 ** 2)
    bytes_recv_mb = net_io.bytes_recv / (1024 ** 2)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "cpu": {
            "usage_percent": round(cpu_percent, 2),
            "cores": cpu_count,
            "status": "critical" if cpu_percent > 90 else "warning" if cpu_percent > 70 else "healthy"
        },
        "memory": {
            "total_gb": round(memory_total_gb, 2),
            "used_gb": round(memory_used_gb, 2),
            "available_gb": round(memory_available_gb, 2),
            "usage_percent": round(memory_percent, 2),
            "status": "critical" if memory_percent > 90 else "warning" if memory_percent > 75 else "healthy"
        },
        "disk": {
            "total_gb": round(disk_total_gb, 2),
            "used_gb": round(disk_used_gb, 2),
            "free_gb": round(disk_free_gb, 2),
            "usage_percent": round(disk_percent, 2),
            "status": "critical" if disk_percent > 85 else "warning" if disk_percent > 70 else "healthy"
        },
        "network": {
            "bytes_sent_mb": round(bytes_sent_mb, 2),
            "bytes_recv_mb": round(bytes_recv_mb, 2)
        }
    }


def get_database_metrics(storage) -> Dict[str, Any]:
    """
    Collect MongoDB database metrics.
    
    Args:
        storage: MongoDBStorage instance
        
    Returns:
        Dictionary containing database statistics
    """
    try:
        # MongoDB Stats
        db_stats = storage.db.command("dbStats")
        
        # Collection counts
        collections = {
            "users": storage.users.count_documents({}),
            "documents": storage.documents.count_documents({}),
            "chat_sessions": storage.chat_sessions.count_documents({}),
            "crawl_jobs": storage.crawl_jobs.count_documents({}),
            "api_keys": storage.api_keys.count_documents({}),
            "activity_logs": storage.activity_logs.count_documents({})
        }
        
        # Database size
        data_size_mb = db_stats.get("dataSize", 0) / (1024 ** 2)
        storage_size_mb = db_stats.get("storageSize", 0) / (1024 ** 2)
        index_size_mb = db_stats.get("indexSize", 0) / (1024 ** 2)
        
        return {
            "status": "healthy",
            "connected": True,
            "database_name": storage.database_name,
            "collections": collections,
            "total_documents": sum(collections.values()),
            "data_size_mb": round(data_size_mb, 2),
            "storage_size_mb": round(storage_size_mb, 2),
            "index_size_mb": round(index_size_mb, 2),
            "total_size_mb": round(data_size_mb + storage_size_mb + index_size_mb, 2)
        }
    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "error": str(e)
        }


def get_qdrant_metrics(storage) -> Dict[str, Any]:
    """
    Collect Qdrant vector database metrics.
    
    Args:
        storage: MongoDBStorage instance (for accessing qdrant client)
        
    Returns:
        Dictionary containing Qdrant statistics
    """
    try:
        from nexora001.storage.qdrant_storage import get_qdrant
        
        qdrant_storage = get_qdrant()
        client = qdrant_storage.client
        collections = client.get_collections().collections
        
        total_vectors = 0
        collection_stats = []
        
        for collection in collections:
            try:
                info = client.get_collection(collection.name)
                vector_count = info.points_count
                total_vectors += vector_count
                
                collection_stats.append({
                    "name": collection.name,
                    "vectors": vector_count,
                    "status": "healthy"
                })
            except:
                collection_stats.append({
                    "name": collection.name,
                    "vectors": 0,
                    "status": "error"
                })
        
        return {
            "status": "healthy",
            "connected": True,
            "total_collections": len(collections),
            "total_vectors": total_vectors,
            "collections": collection_stats
        }
    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "error": str(e)
        }
