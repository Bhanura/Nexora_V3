"""
Crawler manager for running Scrapy spiders programmatically. 
"""

import sys
import logging
from pathlib import Path
from typing import Optional
from scrapy.crawler import CrawlerProcess
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
from crochet import setup, wait_for

# Initialize crochet (reactor already installed by run.py)
setup()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nexora001.crawler.spider import Nexora001Spider
from nexora001.crawler import settings as crawler_settings
from nexora001.storage.mongodb import get_storage


class CrawlerManager:
    """Manages web crawling operations."""
    
    def __init__(self):
        """Initialize the crawler manager."""
        self.process: Optional[CrawlerProcess] = None
        self.runner: Optional[CrawlerRunner] = None
        self._logging_configured = False
    
    def _configure_logging(self):
        """Configure logging for CrawlerRunner to display logs in console."""
        if not self._logging_configured:
            # Configure Scrapy's logging
            configure_logging(install_root_handler=True)
            
            # Also configure Python's root logger to ensure all logs go to console
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
                handlers=[logging.StreamHandler()]
            )
            
            self._logging_configured = True
    
    def crawl_url(
        self,
        url: str,
        client_id: str,
        max_depth: int = 2,
        follow_links: bool = True,
        use_playwright: bool = False
    ) -> dict:
        """
        Crawl a URL and store content in MongoDB.
        
        Args:
            url: The URL to crawl
            max_depth: Maximum crawl depth
            follow_links: Whether to follow internal links
            use_playwright: Whether to use Playwright for JavaScript rendering
            
        Returns:
            Dictionary with crawl statistics
        """
        
        # 1. CREATE JOB IN DB
        with get_storage() as storage:
            job_id = storage.create_crawl_job(
                client_id=client_id,
                url=url,
                options={
                    "max_depth": max_depth,
                    "playwright": use_playwright
                }
            )
        
        # Configure logging for CrawlerRunner (this was automatic with CrawlerProcess)
        self._configure_logging()
        
        # Create crawler settings
        # NOTE: Set TWISTED_REACTOR to None to disable reactor verification
        # since crochet has already installed its own reactor
        settings = {
            'ROBOTSTXT_OBEY': crawler_settings. ROBOTSTXT_OBEY,
            'CONCURRENT_REQUESTS': crawler_settings.CONCURRENT_REQUESTS,
            'DOWNLOAD_DELAY': crawler_settings. DOWNLOAD_DELAY,
            'COOKIES_ENABLED': crawler_settings.COOKIES_ENABLED,
            'TELNETCONSOLE_ENABLED': crawler_settings.TELNETCONSOLE_ENABLED,
            'DEFAULT_REQUEST_HEADERS': crawler_settings.DEFAULT_REQUEST_HEADERS,
            'HTTPCACHE_ENABLED': crawler_settings. HTTPCACHE_ENABLED,
            'HTTPCACHE_DIR': crawler_settings.HTTPCACHE_DIR,
            'LOG_LEVEL': 'INFO',
            'TWISTED_REACTOR': None  # Disable reactor verification - crochet manages it
        }
        
        # Add Playwright settings if enabled
        if use_playwright:
            settings['DOWNLOAD_HANDLERS'] = crawler_settings.DOWNLOAD_HANDLERS
            settings['PLAYWRIGHT_BROWSER_TYPE'] = crawler_settings.PLAYWRIGHT_BROWSER_TYPE
            settings['PLAYWRIGHT_LAUNCH_OPTIONS'] = crawler_settings.PLAYWRIGHT_LAUNCH_OPTIONS
            # Still keep TWISTED_REACTOR as None even with Playwright
        
        # Create process
        # self.process = CrawlerProcess(settings)
        # Create runner
        self.runner = CrawlerRunner(settings)
        
        # Run spider with crochet
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"📡 About to call _run_spider()...")
        
        self._run_spider(
            url=url,
            client_id=client_id,
            job_id=job_id,
            max_depth=max_depth,
            follow_links=follow_links,
            use_playwright=use_playwright
        )
        
        logger.info(f"✓ _run_spider() returned, crawl should be running in background...")

        # Add spider
        """
        self.process.crawl(
            Nexora001Spider,
            start_url=url,
            client_id=client_id,
            job_id=job_id,
            max_depth=max_depth,
            follow_links=follow_links,
            use_playwright=use_playwright 
        )"""
        
        # Start crawling (blocking)
        # self.process.start()
        
        return {
            "status": "completed",
            "job_id": job_id,
            "url": url,
            "client_id": client_id,
            "max_depth": max_depth,
            "playwright_enabled": use_playwright  # ADDED TO RESPONSE
        }

    @wait_for(timeout=3600)
    def _run_spider(self, url, client_id, job_id, max_depth, follow_links, use_playwright):
        """Run spider using crochet."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🕷️ Starting spider with crochet...")
        logger.info(f"   URL: {url}")
        logger.info(f"   Job ID: {job_id}")
        
        try:
            deferred = self.runner.crawl(
                Nexora001Spider,
                start_url=url,
                client_id=client_id,
                job_id=job_id,
                max_depth=max_depth,
                follow_links=follow_links,
                use_playwright=use_playwright
            )
            logger.info(f"✓ Spider crawl initiated, returning deferred...")
            return deferred
        except Exception as e:
            logger.error(f"❌ Error in _run_spider: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

def crawl_website(
    url: str,
    client_id: str,
    max_depth: int = 2,
    follow_links: bool = True,
    use_playwright: bool = False  # NEW PARAMETER
):
    """
    Convenience function to crawl a website. 
    
    Args:
        url: URL to crawl
        max_depth: Maximum depth
        follow_links: Whether to follow links
        use_playwright: Whether to use Playwright for JavaScript rendering
        
    Returns:
        Dictionary with crawl statistics
    """
    manager = CrawlerManager()
    return manager.crawl_url(url, client_id, max_depth, follow_links, use_playwright)