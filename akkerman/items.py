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
