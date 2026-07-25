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


class ProductItem(scrapy.Item):
    """A single product scraped from akkermandenhaag.nl (a Shopify store).

    One item is emitted per product. Variant-level data (e.g. fountain-pen
    nib sizes, each with their own price and stock status) is nested in the
    ``variants`` list so that per-nib availability is preserved.
    """

    # --- identity ---------------------------------------------------------
    product_id = scrapy.Field()      # int  — Shopify product id
    handle = scrapy.Field()          # str  — URL slug
    name = scrapy.Field()            # str  — product title
    vendor = scrapy.Field()          # str  — brand / vendor
    product_type = scrapy.Field()    # str  — Shopify product type
    tags = scrapy.Field()            # list[str]

    # --- content ----------------------------------------------------------
    description_html = scrapy.Field()  # str — raw description HTML
    description_text = scrapy.Field()  # str — description as plain text
    images = scrapy.Field()            # list[str] — absolute image URLs

    # --- pricing (product level; may vary across variants) ----------------
    price = scrapy.Field()             # float — representative price (major units)
    price_min = scrapy.Field()         # float
    price_max = scrapy.Field()         # float
    price_varies = scrapy.Field()      # bool
    currency = scrapy.Field()          # str  — ISO currency code

    # --- stock ------------------------------------------------------------
    available = scrapy.Field()         # bool — any variant in stock?

    # --- variants (nib sizes, colours, etc.) ------------------------------
    # Each entry: {variant_id, title, sku, options, price, available, ...}
    variants = scrapy.Field()          # list[dict]
    option_names = scrapy.Field()      # list[str] — e.g. ["Size"]

    # --- provenance -------------------------------------------------------
    source_url = scrapy.Field()        # str  — canonical product page URL
    scraped_at = scrapy.Field()        # str  — ISO 8601 UTC timestamp
