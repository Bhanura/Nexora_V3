"""
Scrapy settings for Nexora001 crawler.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Scrapy settings
BOT_NAME = 'nexora001'

SPIDER_MODULES = ['nexora001.crawler']
NEWSPIDER_MODULE = 'nexora001.crawler'

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
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
    'User-Agent': os.getenv('USER_AGENT', 'Nexora001-Bot/1.0'),
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