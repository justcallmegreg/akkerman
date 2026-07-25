"""Item definitions — the structured schema that scraped data lands in.

Each Item subclass defines the well-defined schema referenced in the README
(goal #2). Keeping fields explicit makes the resulting Parquet schema stable
and self-documenting.
"""

import scrapy


class QuoteItem(scrapy.Item):
    """A single quote scraped from quotes.toscrape.com.

    This is the example schema shipped with the project. Add your own Item
    subclasses for new targets.
    """

    text = scrapy.Field()          # str  — the quote text
    author = scrapy.Field()        # str  — author name
    author_url = scrapy.Field()    # str  — absolute URL to the author page
    tags = scrapy.Field()          # list[str] — associated tags
    scraped_at = scrapy.Field()    # str  — ISO 8601 UTC timestamp
    source_url = scrapy.Field()    # str  — page the quote was scraped from


class ProductCategoryItem(scrapy.Item):
    """A product category (Shopify "collection") from akkermandenhaag.nl.

    akkermandenhaag.nl is a Shopify storefront, so its product categories are
    exposed as *collections*. The public ``/collections.json`` endpoint returns
    them as structured JSON, which maps cleanly onto the fields below.

    This is intentionally the *first* landing step: categories give us the
    entry points (handles/URLs) needed to later crawl the products within each
    one.
    """

    collection_id = scrapy.Field()    # int  — Shopify collection id
    title = scrapy.Field()            # str  — human-readable category name
    handle = scrapy.Field()           # str  — URL slug (unique per store)
    description = scrapy.Field()      # str  — HTML description (may be empty)
    url = scrapy.Field()              # str  — absolute collection URL
    products_count = scrapy.Field()   # int  — number of products in category
    image = scrapy.Field()           # str | None — collection image URL
    published_at = scrapy.Field()     # str  — ISO 8601 publish timestamp
    updated_at = scrapy.Field()       # str  — ISO 8601 last-update timestamp
    scraped_at = scrapy.Field()       # str  — ISO 8601 UTC scrape timestamp
    source_url = scrapy.Field()       # str  — endpoint the data came from
