"""Scrapy settings for the akkerman project.

Only a subset of the many available settings is defined here. For a full
reference see https://docs.scrapy.org/en/latest/topics/settings.html
"""

BOT_NAME = "akkerman"

SPIDER_MODULES = ["akkerman.spiders"]
NEWSPIDER_MODULE = "akkerman.spiders"

# --- Politeness / robots -------------------------------------------------
# Respect robots.txt rules by default (see README goal #1).
ROBOTSTXT_OBEY = True

# Identify the crawler honestly.
USER_AGENT = "akkerman (+https://github.com/akkerman-crawler)"

# --- Rate limiting -------------------------------------------------------
# Be a good citizen: throttle requests and back off automatically.
DOWNLOAD_DELAY = 1.0
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 4

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 30.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# --- Caching (handy during development) ----------------------------------
HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = ".scrapy/httpcache"

# --- Pipelines -----------------------------------------------------------
# The ParquetPipeline collects scraped items and writes them to a single
# Parquet file when the spider closes.
ITEM_PIPELINES = {
    "akkerman.pipelines.ParquetPipeline": 300,
}

# Directory where Parquet datasets are written (relative to project root).
PARQUET_OUTPUT_DIR = "data"
# Parquet compression codec: snappy | gzip | brotli | zstd | none
PARQUET_COMPRESSION = "snappy"

# --- Misc ----------------------------------------------------------------
# Retry transient failures.
RETRY_ENABLED = True
RETRY_TIMES = 3

# Encoding for exported feeds.
FEED_EXPORT_ENCODING = "utf-8"

# Use the modern asyncio reactor.
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Future-proof default for Scrapy request fingerprinting.
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"

LOG_LEVEL = "INFO"
