"""Spider: extract the available *brands* from akkermandenhaag.nl.

akkermandenhaag.nl is a Shopify storefront. Shopify exposes two public JSON
endpoints we rely on:

* ``/collections.json`` — the catalogue of collections (brands, product series
  and categories all live here as ``handle`` + ``title`` pairs).
* ``/products.json``    — every product, including its ``tags``.

Why not just use the product ``vendor``? Because on this store the vendor is
always the shop itself ("P.W. Akkerman Den Haag"), which is useless as a brand.
The reliable brand signal is a *capitalised tag* on a product (e.g. ``Montblanc``)
that *also* corresponds to a collection. We therefore:

1. Page through ``collections.json`` and build a normalised lookup of every
   collection handle and title.
2. Page through ``products.json`` and count the capitalised tags, tracking each
   distinct spelling.
3. Keep only tags that intersect the collection lookup — those are the brands —
   choosing the most frequent spelling as canonical (so ``Caran d'Ache`` beats
   the rare ``Caran D'ache``).

Run it with::

    scrapy crawl akkerman_brands

Output lands in ``data/akkerman_brands_<timestamp>.parquet``.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from urllib.parse import urlencode

import scrapy

from akkerman.items import BrandItem

BASE = "https://akkermandenhaag.nl"
PAGE_LIMIT = 250  # Shopify hard cap per page.

# Browser-like headers: the plain Scrapy UA gets throttled / blocked on the
# JSON endpoints, so we present as a real browser and accept gzip.
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9,nl;q=0.8",
}


def _norm(s: str) -> str:
    """Normalise a name for casing/punctuation-insensitive comparison."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


class AkkermanBrandsSpider(scrapy.Spider):
    name = "akkerman_brands"
    allowed_domains = ["akkermandenhaag.nl"]

    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": BROWSER_HEADERS,
        # Be gentle on the API and honour Retry-After up to a full minute.
        "DOWNLOAD_DELAY": 0.6,
        "AUTOTHROTTLE_MAX_DELAY": 60.0,
        "RETRY_TIMES": 5,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # normalised collection name -> handle
        self._collection_norms: dict[str, str] = {}
        # normalised brand -> total product count
        self._tag_counter: Counter = Counter()
        # normalised brand -> {spelling: count}  (to pick canonical spelling)
        self._spellings: dict[str, Counter] = defaultdict(Counter)

    # --- entrypoint ------------------------------------------------------
    # Scrapy >=2.13 drives the engine from the async ``start()`` coroutine;
    # older versions use ``start_requests()``. We provide both so the spider
    # works across versions.
    async def start(self):
        yield self._collections_request(page=1)

    def start_requests(self):
        yield self._collections_request(page=1)

    # --- 1. collections --------------------------------------------------
    def _collections_request(self, page: int) -> scrapy.Request:
        qs = urlencode({"limit": PAGE_LIMIT, "page": page})
        return scrapy.Request(
            f"{BASE}/collections.json?{qs}",
            callback=self.parse_collections,
            cb_kwargs={"page": page},
            dont_filter=True,
        )

    def parse_collections(self, response, page: int):
        data = json.loads(response.text)
        collections = data.get("collections", [])
        for c in collections:
            handle = c.get("handle", "")
            title = c.get("title", "")
            if handle:
                self._collection_norms.setdefault(_norm(handle), handle)
            if title:
                self._collection_norms.setdefault(_norm(title), handle or _norm(title))
        self.logger.info(
            "collections page %d: %d collections (running total %d)",
            page, len(collections), len(self._collection_norms),
        )
        if len(collections) == PAGE_LIMIT:
            yield self._collections_request(page + 1)
        else:
            yield self._products_request(page=1)

    # --- 2. products -----------------------------------------------------
    def _products_request(self, page: int) -> scrapy.Request:
        qs = urlencode({"limit": PAGE_LIMIT, "page": page})
        return scrapy.Request(
            f"{BASE}/products.json?{qs}",
            callback=self.parse_products,
            cb_kwargs={"page": page},
            dont_filter=True,
        )

    def parse_products(self, response, page: int):
        data = json.loads(response.text)
        products = data.get("products", [])
        for p in products:
            for tag in p.get("tags", []):
                if not tag or not tag[:1].isupper():
                    continue  # brands are capitalised; skip colour/category tags
                n = _norm(tag)
                self._tag_counter[n] += 1
                self._spellings[n][tag] += 1
        self.logger.info("products page %d: %d products", page, len(products))
        if len(products) == PAGE_LIMIT:
            yield self._products_request(page + 1)
        else:
            yield from self._emit_brands()

    # --- 3. emit ---------------------------------------------------------
    def _emit_brands(self):
        now = datetime.now(timezone.utc).isoformat()
        emitted = 0
        for norm_name, count in sorted(self._tag_counter.items()):
            if norm_name not in self._collection_norms:
                continue  # tag is not a collection -> not a brand
            handle = self._collection_norms[norm_name]
            # canonical spelling = most frequently seen spelling
            canonical = self._spellings[norm_name].most_common(1)[0][0]
            item = BrandItem()
            item["brand"] = canonical
            item["handle"] = handle
            item["collection_url"] = f"{BASE}/collections/{handle}" if handle else None
            item["product_count"] = int(count)
            item["scraped_at"] = now
            item["source"] = "akkermandenhaag.nl"
            emitted += 1
            yield item
        self.logger.info("emitted %d brands", emitted)
