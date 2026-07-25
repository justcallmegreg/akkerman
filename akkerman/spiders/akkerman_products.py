"""Spider for product pages on akkermandenhaag.nl (a Shopify storefront).

Why the JSON endpoint instead of parsing HTML?
----------------------------------------------
akkermandenhaag.nl runs on Shopify. Every product exposes a structured JSON
document at ``<product-url>.js`` which contains *exactly* the data we care
about — name, price, stock, description and, crucially, one entry per variant
(e.g. each fountain-pen nib size with its own SKU, price and ``available``
flag). Scraping this endpoint is:

* **Robust** — no brittle CSS selectors, no JS rendering required.
* **Complete** — per-variant stock is only reliably available here; the
  rendered page hides out-of-stock nibs behind client-side logic.
* **Polite & permitted** — robots.txt allows ``/products/*`` (only
  ``/recommendations/products`` and ``/cart.js`` are disallowed, and we do not
  touch those; recommendations are explicitly out of scope).

Usage
-----
Crawl a single product::

    scrapy crawl akkerman_products \
        -a url=https://akkermandenhaag.nl/collections/potloden/products/faber-castell-tafelpuntenslijper

Crawl every product in one or more collections::

    scrapy crawl akkerman_products -a collections=vulpennen,potloden

Crawl the whole store (all products)::

    scrapy crawl akkerman_products -a all=1
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from html import unescape
from urllib.parse import urljoin, urlparse

import scrapy

from akkerman.items import ProductItem

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _html_to_text(html: str | None) -> str:
    """Very small HTML -> text helper (no external deps)."""
    if not html:
        return ""
    # Turn block-ish tags into spaces so words don't run together.
    text = re.sub(r"(?i)<\s*(br|/p|/div|/li|/h[1-6])\s*/?>", " ", html)
    text = _TAG_RE.sub("", text)
    text = unescape(text)
    return _WS_RE.sub(" ", text).strip()


def _abs_url(url: str | None) -> str | None:
    """Protocol-relative Shopify CDN URLs (//cdn...) -> https URLs."""
    if not url:
        return None
    if url.startswith("//"):
        return "https:" + url
    return url


class AkkermanProductsSpider(scrapy.Spider):
    """Extract structured product data from akkermandenhaag.nl."""

    name = "akkerman_products"
    allowed_domains = ["akkermandenhaag.nl"]

    # Shopify money values are integers in the shop's minor currency unit
    # (cents for EUR). Divide by 100 for human-readable major units.
    MONEY_DIVISOR = 100.0
    CURRENCY = "EUR"

    def __init__(
        self,
        url: str | None = None,
        collections: str | None = None,
        all: str | None = None,  # noqa: A002 - matches -a all=1 CLI arg
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.start_url = url
        self.collections = (
            [c.strip() for c in collections.split(",") if c.strip()]
            if collections
            else []
        )
        self.crawl_all = str(all).lower() in {"1", "true", "yes"} if all else False

    # -- request generation ------------------------------------------------

    def _initial_requests(self):
        """Build the seed requests from the spider's -a arguments.

        Kept as a plain (sync) generator so it is trivial to unit-test; the
        async ``start()`` entrypoint below simply re-yields from it.
        """
        if self.start_url:
            yield scrapy.Request(self._to_js(self.start_url), self.parse_product)
        for handle in self.collections:
            yield scrapy.Request(
                f"https://{self.allowed_domains[0]}/collections/{handle}/products.json?limit=250&page=1",
                self.parse_collection,
                cb_kwargs={"collection": handle, "page": 1},
            )
        if self.crawl_all:
            yield scrapy.Request(
                f"https://{self.allowed_domains[0]}/products.json?limit=250&page=1",
                self.parse_all_products,
                cb_kwargs={"page": 1},
            )
        if not (self.start_url or self.collections or self.crawl_all):
            self.logger.error(
                "Nothing to crawl. Pass -a url=..., -a collections=a,b or -a all=1"
            )

    async def start(self):
        """Modern Scrapy (>=2.13) entrypoint for seed requests."""
        for request in self._initial_requests():
            yield request

    # Backwards-compat for Scrapy < 2.13, which calls start_requests().
    def start_requests(self):
        return self._initial_requests()

    @staticmethod
    def _to_js(product_url: str) -> str:
        """Normalise any product URL to its ``.js`` JSON endpoint."""
        product_url = product_url.split("?")[0].rstrip("/")
        if product_url.endswith((".js", ".json")):
            return product_url.rsplit(".", 1)[0] + ".js"
        return product_url + ".js"

    # -- collection / catalogue paging ------------------------------------

    def parse_collection(self, response, collection, page):
        data = json.loads(response.text)
        products = data.get("products", [])
        for handle in (p.get("handle") for p in products):
            if handle:
                yield response.follow(f"/products/{handle}.js", self.parse_product)
        if products:  # keep paging while pages are non-empty
            yield response.follow(
                f"/collections/{collection}/products.json?limit=250&page={page + 1}",
                self.parse_collection,
                cb_kwargs={"collection": collection, "page": page + 1},
            )

    def parse_all_products(self, response, page):
        data = json.loads(response.text)
        products = data.get("products", [])
        for handle in (p.get("handle") for p in products):
            if handle:
                yield response.follow(f"/products/{handle}.js", self.parse_product)
        if products:
            yield response.follow(
                f"/products.json?limit=250&page={page + 1}",
                self.parse_all_products,
                cb_kwargs={"page": page + 1},
            )

    # -- the actual product extraction ------------------------------------

    def parse_product(self, response):
        data = json.loads(response.text)
        yield self._build_item(data, response.url)

    def _build_item(self, data: dict, response_url: str) -> ProductItem:
        item = ProductItem()

        item["product_id"] = data.get("id")
        item["handle"] = data.get("handle")
        item["name"] = data.get("title")
        item["vendor"] = data.get("vendor")
        item["product_type"] = data.get("type")
        item["tags"] = data.get("tags") or []

        desc_html = data.get("description") or ""
        item["description_html"] = desc_html
        item["description_text"] = _html_to_text(desc_html)

        # Images: prefer high-res `media` src, fall back to `images`.
        images: list[str] = []
        for media in data.get("media") or []:
            if media.get("media_type") == "image":
                src = _abs_url(media.get("src"))
                if src and src not in images:
                    images.append(src)
        for raw in data.get("images") or []:
            src = _abs_url(raw)
            if src and src not in images:
                images.append(src)
        item["images"] = images

        item["price"] = self._money(data.get("price"))
        item["price_min"] = self._money(data.get("price_min"))
        item["price_max"] = self._money(data.get("price_max"))
        item["price_varies"] = bool(data.get("price_varies"))
        item["currency"] = self.CURRENCY

        item["available"] = bool(data.get("available"))

        # Option names describe what the variants vary on, e.g. ["Size"] for
        # a fountain pen where each variant is a nib size.
        item["option_names"] = [
            o.get("name") for o in (data.get("options") or []) if o.get("name")
        ]

        # One entry per variant. For fountain pens this yields one row per nib
        # size, each carrying its own price + `available` (in-stock) flag.
        variants = []
        for v in data.get("variants") or []:
            variants.append(
                {
                    "variant_id": v.get("id"),
                    "title": v.get("title"),
                    "sku": v.get("sku"),
                    "barcode": v.get("barcode"),
                    "options": v.get("options") or [],
                    "price": self._money(v.get("price")),
                    "compare_at_price": self._money(v.get("compare_at_price")),
                    "available": bool(v.get("available")),
                    "featured_image": _abs_url(
                        (v.get("featured_image") or {}).get("src")
                        if isinstance(v.get("featured_image"), dict)
                        else v.get("featured_image")
                    ),
                }
            )
        item["variants"] = variants

        # Canonical product page URL (not the .js endpoint).
        parsed = urlparse(response_url)
        canonical = f"{parsed.scheme}://{parsed.netloc}"
        canonical = urljoin(
            canonical, data.get("url") or f"/products/{data.get('handle')}"
        )
        item["source_url"] = canonical

        item["scraped_at"] = datetime.now(timezone.utc).isoformat()
        return item

    def _money(self, value) -> float | None:
        if value is None:
            return None
        try:
            return round(int(value) / self.MONEY_DIVISOR, 2)
        except (TypeError, ValueError):
            return None
