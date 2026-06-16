"""
Simple runner script for eLanka Chat AI
"""
import sys
import os
from pathlib import Path

# 1. CRITICAL: Install Asyncio Reactor immediately
# This is required for Playwright/Scrapy compatibility.
# It must run before any other Twisted/Scrapy imports.
try:
    import asyncio
    from twisted.internet import asyncioreactor
    
    # Windows specific policy
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Install the reactor if not already installed
    if 'twisted.internet.reactor' not in sys.modules:
        asyncioreactor.install()
except Exception as e:
    print(f"Reactor setup warning: {e}")

# Add src to Python path
src_path = Path(__file__). parent / "src"
sys.path. insert(0, str(src_path))

# Now import and run
from elanka_chat_ai.main import main

if __name__ == "__main__":
    main()