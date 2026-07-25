"""Example spider: crawl quotes.toscrape.com into a structured schema.

quotes.toscrape.com is a public sandbox explicitly built for practising web
scraping, so it is safe and ethical to crawl. Use this spider as a template
for real targets: define an Item in akkerman/items.py, then map extracted
fields onto it here.

Run it with:

    scrapy crawl quotes

Output lands in data/quotes_<timestamp>.parquet.
"""

from __future__ import annotations

from datetime import datetime, timezone

import scrapy

from akkerman.items import QuoteItem


class QuotesSpider(scrapy.Spider):
    name = "quotes"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://quotes.toscrape.com/"]

    def parse(self, response):
        now = datetime.now(timezone.utc).isoformat()

        for quote in response.css("div.quote"):
            item = QuoteItem()
            item["text"] = quote.css("span.text::text").get(default="").strip("“”\"")
            item["author"] = quote.css("small.author::text").get(default="").strip()
            author_href = quote.css("span a::attr(href)").get()
            item["author_url"] = response.urljoin(author_href) if author_href else None
            item["tags"] = quote.css("div.tags a.tag::text").getall()
            item["scraped_at"] = now
            item["source_url"] = response.url
            yield item

        # Follow pagination.
        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
