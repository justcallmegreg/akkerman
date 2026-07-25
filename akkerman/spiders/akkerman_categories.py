"""Spider: crawl product categories from akkermandenhaag.nl.

akkermandenhaag.nl (P.W. Akkerman Den Haag) is a **Shopify** storefront. In
Shopify, product categories are modelled as *collections*, and the storefront
exposes them through the public, crawlable ``/collections.json`` endpoint
(``Allow: /`` in robots.txt). Compared to scraping the rendered navigation HTML
this endpoint is:

* structured (stable JSON schema — no brittle CSS selectors),
* complete (every published collection, not just the ones in the menu), and
* paginated deterministically via ``?page=N``.

This spider fetches the categories *first* — they are the entry points we need
before crawling the products inside each one. Each collection also carries a
``handle`` from which the per-category product endpoint can later be derived:
``/collections/<handle>/products.json``.

Run it with:

    scrapy crawl akkerman_categories

Output lands in data/akkerman_categories_<timestamp>.parquet.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import scrapy

from akkerman.items import ProductCategoryItem


class AkkermanCategoriesSpider(scrapy.Spider):
    name = "akkerman_categories"
    allowed_domains = ["akkermandenhaag.nl"]

    # Shopify caps collections.json at 250 records per page; we page until an
    # empty response is returned.
    PAGE_SIZE = 250
    BASE_URL = "https://akkermandenhaag.nl"

    async def start(self):
        # Scrapy >= 2.13 entry point. The default implementation only reads
        # ``start_urls``; we need a custom first request, so we override it.
        yield self._collections_request(page=1)

    def start_requests(self):
        # Backward-compatibility shim for Scrapy < 2.13, where ``start()`` does
        # not exist and ``start_requests()`` is the entry point instead.
        yield self._collections_request(page=1)

    def _collections_request(self, page: int) -> scrapy.Request:
        url = f"{self.BASE_URL}/collections.json?limit={self.PAGE_SIZE}&page={page}"
        return scrapy.Request(
            url,
            callback=self.parse,
            cb_kwargs={"page": page},
        )

    def parse(self, response, page: int):
        now = datetime.now(timezone.utc).isoformat()

        try:
            payload = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error("Non-JSON response on page %d from %s", page, response.url)
            return

        collections = payload.get("collections", [])
        if not collections:
            # Empty page → we've walked past the last page; stop paginating.
            return

        for col in collections:
            handle = col.get("handle")
            image = col.get("image")
            item = ProductCategoryItem()
            item["collection_id"] = col.get("id")
            item["title"] = col.get("title")
            item["handle"] = handle
            item["description"] = col.get("description") or ""
            item["url"] = f"{self.BASE_URL}/collections/{handle}" if handle else None
            item["products_count"] = col.get("products_count")
            # Shopify returns image as an object (or null); keep just the src.
            item["image"] = image.get("src") if isinstance(image, dict) else image
            item["published_at"] = col.get("published_at")
            item["updated_at"] = col.get("updated_at")
            item["scraped_at"] = now
            item["source_url"] = response.url
            yield item

        # A full page likely means there is another; follow it.
        if len(collections) == self.PAGE_SIZE:
            yield self._collections_request(page=page + 1)
