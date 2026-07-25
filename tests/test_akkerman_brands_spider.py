"""Offline tests for the akkerman_brands spider extraction logic.

We feed the spider fake ``collections.json`` / ``products.json`` responses so we
can assert the brand-intersection + casing-merge behaviour without any network.
"""

import json

from scrapy.http import Request, TextResponse

from akkerman.spiders.akkerman_brands import AkkermanBrandsSpider, BASE

COLLECTIONS = {
    "collections": [
        {"handle": "montblanc", "title": "Montblanc"},
        {"handle": "caran-dache-1", "title": "Caran d'Ache"},
        {"handle": "leuchtturm-1917", "title": "Leuchtturm1917"},
        {"handle": "balpennen", "title": "Balpennen"},  # a category, not a brand
    ]
}

PRODUCTS = {
    "products": [
        {"title": "Pen A", "tags": ["zwart", "Montblanc"]},
        {"title": "Pen B", "tags": ["Montblanc", "rood"]},
        # two casing spellings of the same brand; the frequent one must win
        {"title": "Pen C", "tags": ["Caran d'Ache"]},
        {"title": "Pen D", "tags": ["Caran d'Ache"]},
        {"title": "Pen E", "tags": ["Caran D'ache"]},
        {"title": "Notebook", "tags": ["Leuchtturm1917"]},
        # a capitalised tag that is NOT a collection -> not a brand
        {"title": "Random", "tags": ["Limited"]},
        # a lowercase category tag matching a collection -> skipped (not a brand)
        {"title": "Cat", "tags": ["balpennen"]},
    ]
}


def _json_response(url, payload):
    request = Request(url=url)
    body = json.dumps(payload).encode("utf-8")
    return TextResponse(url=url, request=request, body=body, encoding="utf-8")


def _run_spider():
    spider = AkkermanBrandsSpider()
    # 1. feed collections (single page -> triggers products request)
    list(spider.parse_collections(
        _json_response(f"{BASE}/collections.json", COLLECTIONS), page=1))
    # 2. feed products (single page -> emits brands)
    results = list(spider.parse_products(
        _json_response(f"{BASE}/products.json", PRODUCTS), page=1))
    items = [r for r in results if not isinstance(r, Request)]
    return {i["brand"]: i for i in items}


def test_only_collection_backed_brands_are_emitted():
    brands = _run_spider()
    # "Limited" is capitalised but not a collection -> excluded.
    assert "Limited" not in brands
    # "balpennen" is a collection but a lowercase category tag -> excluded.
    assert "Balpennen" not in brands
    assert set(brands) == {"Montblanc", "Caran d'Ache", "Leuchtturm1917"}


def test_product_counts_are_correct():
    brands = _run_spider()
    assert brands["Montblanc"]["product_count"] == 2
    # all three Caran spellings collapse into one brand
    assert brands["Caran d'Ache"]["product_count"] == 3
    assert brands["Leuchtturm1917"]["product_count"] == 1


def test_canonical_spelling_is_most_frequent():
    brands = _run_spider()
    # "Caran d'Ache" (x2) must beat "Caran D'ache" (x1)
    assert brands["Caran d'Ache"]["brand"] == "Caran d'Ache"


def test_collection_url_and_metadata():
    brands = _run_spider()
    mb = brands["Montblanc"]
    assert mb["handle"] == "montblanc"
    assert mb["collection_url"] == f"{BASE}/collections/montblanc"
    assert mb["source"] == "akkermandenhaag.nl"
    assert mb["scraped_at"]  # non-empty ISO timestamp
