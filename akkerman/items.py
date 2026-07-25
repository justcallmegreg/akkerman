"""Item definitions — the structured schema that scraped data lands in.

Each Item subclass defines a well-defined schema (README goal #2). Keeping
fields explicit makes the resulting Parquet schema stable and self-documenting.
"""

import scrapy


class QuoteItem(scrapy.Item):
    """A single quote scraped from quotes.toscrape.com (example template)."""

    text = scrapy.Field()          # str  — the quote text
    author = scrapy.Field()        # str  — author name
    author_url = scrapy.Field()    # str  — absolute URL to the author page
    tags = scrapy.Field()          # list[str] — associated tags
    scraped_at = scrapy.Field()    # str  — ISO 8601 UTC timestamp
    source_url = scrapy.Field()    # str  — page the quote was scraped from


class BrandItem(scrapy.Item):
    """A single brand available at akkermandenhaag.nl.

    Brands are derived from a Shopify storefront: the ``vendor`` field is the
    shop itself ("P.W. Akkerman Den Haag") and is useless as a brand, so the
    real brand signal is a capitalised product *tag* that also corresponds to a
    storefront *collection*. We intersect the two to keep only genuine brands.
    """

    brand = scrapy.Field()          # str  — canonical brand display name
    handle = scrapy.Field()         # str  — matching collection handle (slug), if any
    collection_url = scrapy.Field() # str  — absolute URL to the brand's collection page
    product_count = scrapy.Field()  # int  — number of products tagged with this brand
    scraped_at = scrapy.Field()     # str  — ISO 8601 UTC timestamp
    source = scrapy.Field()         # str  — data source domain
