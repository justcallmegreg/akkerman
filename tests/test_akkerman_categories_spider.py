"""Offline tests for the akkerman_categories spider extraction logic.

These build a fake Scrapy Response from a static JSON fixture (mirroring the
shape of akkermandenhaag.nl's /collections.json endpoint) so we can assert the
parsing/schema behaviour without hitting the network.
"""

import json

from scrapy.http import Request, TextResponse

from akkerman.spiders.akkerman_categories import AkkermanCategoriesSpider

# A trimmed, representative sample of the real /collections.json payload,
# including the image-as-object and null-image variants and an empty
# description that the spider must normalise.
FIXTURE = {
    "collections": [
        {
            "id": 189260234891,
            "title": "4YOU",
            "handle": "4you",
            "description": "",
            "published_at": "2020-09-07T16:41:57+02:00",
            "updated_at": "2026-07-25T13:04:54+02:00",
            "image": None,
            "products_count": 26,
        },
        {
            "id": 189187063947,
            "title": "Akkerman",
            "handle": "akkerman",
            "description": "<p>Eigen producten.</p>",
            "published_at": "2020-09-03T13:03:20+02:00",
            "updated_at": "2026-07-25T13:04:54+02:00",
            "image": {"src": "https://cdn.shop/akkerman.png"},
            "products_count": 75,
        },
    ]
}


def _make_response(payload, page=1, url=None):
    url = url or (
        "https://akkermandenhaag.nl/collections.json?limit=250&page=%d" % page
    )
    request = Request(url=url, cb_kwargs={"page": page})
    body = json.dumps(payload).encode("utf-8")
    return TextResponse(url=url, request=request, body=body, encoding="utf-8")


def test_parse_extracts_expected_fields():
    spider = AkkermanCategoriesSpider()
    response = _make_response(FIXTURE, page=1)
    results = list(spider.parse(response, page=1))

    items = [r for r in results if not isinstance(r, Request)]
    assert len(items) == 2

    first = items[0]
    assert first["collection_id"] == 189260234891
    assert first["title"] == "4YOU"
    assert first["handle"] == "4you"
    assert first["description"] == ""            # empty string preserved
    assert first["url"] == "https://akkermandenhaag.nl/collections/4you"
    assert first["products_count"] == 26
    assert first["image"] is None
    assert first["published_at"] == "2020-09-07T16:41:57+02:00"
    assert first["updated_at"] == "2026-07-25T13:04:54+02:00"
    assert first["scraped_at"]                    # non-empty ISO timestamp
    assert first["source_url"] == response.url

    second = items[1]
    # image object is flattened to its src.
    assert second["image"] == "https://cdn.shop/akkerman.png"
    assert second["url"] == "https://akkermandenhaag.nl/collections/akkerman"


def test_parse_paginates_on_full_page():
    spider = AkkermanCategoriesSpider()
    # Build a full page (== PAGE_SIZE items) to trigger a next-page request.
    full = {
        "collections": [
            {
                "id": i,
                "title": f"C{i}",
                "handle": f"c{i}",
                "description": "",
                "published_at": "2020-01-01T00:00:00+00:00",
                "updated_at": "2020-01-01T00:00:00+00:00",
                "image": None,
                "products_count": 1,
            }
            for i in range(spider.PAGE_SIZE)
        ]
    }
    results = list(spider.parse(_make_response(full, page=1), page=1))

    requests = [r for r in results if isinstance(r, Request)]
    assert len(requests) == 1
    assert "page=2" in requests[0].url


def test_no_pagination_on_partial_page():
    spider = AkkermanCategoriesSpider()
    results = list(spider.parse(_make_response(FIXTURE, page=3), page=3))
    requests = [r for r in results if isinstance(r, Request)]
    assert requests == []


def test_empty_page_stops_and_yields_nothing():
    spider = AkkermanCategoriesSpider()
    results = list(spider.parse(_make_response({"collections": []}, page=4), page=4))
    assert results == []


def test_malformed_json_is_handled():
    spider = AkkermanCategoriesSpider()
    url = "https://akkermandenhaag.nl/collections.json?limit=250&page=1"
    request = Request(url=url, cb_kwargs={"page": 1})
    response = TextResponse(url=url, request=request, body=b"not json", encoding="utf-8")
    results = list(spider.parse(response, page=1))
    assert results == []
