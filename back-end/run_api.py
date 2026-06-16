"""
Run the eLanka Chat AI API server. 

Usage:
    python run_api.py
    
    Then visit: http://localhost:8000/docs
"""

import uvicorn
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    """Run the API server."""
    print("=" * 70)
    print("🚀 Starting eLanka Chat AI API Server")
    print("=" * 70)
    print()
    print("📚 API Documentation:  http://localhost:8000/docs")
    print("📖 ReDoc: http://localhost:8000/redoc")
    print("🔧 OpenAPI JSON: http://localhost:8000/openapi.json")
    print()
    print("Press CTRL+C to stop the server")
    print("=" * 70)
    print()
    
    uvicorn.run(
        "elanka_chat_ai.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )


if __name__ == "__main__":
    main()