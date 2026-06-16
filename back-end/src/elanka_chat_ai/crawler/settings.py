"""
Scrapy settings for eLanka Chat AI crawler.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Scrapy settings
BOT_NAME = 'elanka_chat_ai'

SPIDER_MODULES = ['elanka_chat_ai.crawler']
NEWSPIDER_MODULE = 'elanka_chat_ai.crawler'

# Obey robots.txt rules
ROBOTSTXT_OBEY = os.getenv('RESPECT_ROBOTS_TXT', 'true').lower() == 'true'

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 2

# Configure a delay for requests
DOWNLOAD_DELAY = float(os.getenv('CRAWL_DELAY', '1.0'))

# Disable cookies
COOKIES_ENABLED = False

# Disable Telnet Console
TELNETCONSOLE_ENABLED = False

# Override the default request headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'User-Agent': os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
}

# Enable and configure HTTP caching
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400  # 24 hours
HTTPCACHE_DIR = 'data/httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 400, 403, 404, 408]

# Playwright settings
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

PLAYWRIGHT_BROWSER_TYPE = "chromium"

PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "timeout": 60000,  # 60 seconds
}

# Twisted reactor
# NOTE: When running with crochet (API mode), don't set TWISTED_REACTOR
# Crochet manages the reactor automatically. Only set this for standalone crawling.
# TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Set settings whose default value is deprecated
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
FEED_EXPORT_ENCODING = 'utf-8'