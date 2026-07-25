"""Offline tests for the akkerman_products spider.

These run against saved Shopify ``.js`` fixtures (see tests/fixtures/) so the
suite is fast and does not hit the network.
"""

import json
from pathlib import Path

import pytest
from scrapy.http import TextResponse

from akkerman.spiders.akkerman_products import (
    AkkermanProductsSpider,
    _html_to_text,
    _abs_url,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _response_from_fixture(name: str, url: str) -> TextResponse:
    body = (FIXTURES / name).read_bytes()
    return TextResponse(url=url, body=body, encoding="utf-8")


@pytest.fixture
def spider():
    return AkkermanProductsSpider()


# --- single-variant product (the sharpener from the task) ----------------

@pytest.fixture
def sharpener_item(spider):
    url = "https://akkermandenhaag.nl/products/faber-castell-tafelpuntenslijper.js"
    resp = _response_from_fixture("sharpener.js.json", url)
    items = list(spider.parse_product(resp))
    assert len(items) == 1
    return items[0]


def test_name_and_identity(sharpener_item):
    assert sharpener_item["name"] == "Faber-Castell tafelpuntenslijper"
    assert sharpener_item["handle"] == "faber-castell-tafelpuntenslijper"
    assert sharpener_item["vendor"] == "P.W. Akkerman Den Haag"


def test_price_converted_to_major_units(sharpener_item):
    # Shopify reports 988 cents -> 9.88 EUR
    assert sharpener_item["price"] == 9.88
    assert sharpener_item["currency"] == "EUR"
    assert sharpener_item["price_varies"] is False


def test_stock_flag(sharpener_item):
    assert sharpener_item["available"] is True


def test_images_are_absolute(sharpener_item):
    imgs = sharpener_item["images"]
    assert imgs, "expected at least one image"
    assert all(u.startswith("https://") for u in imgs)


def test_description_captured(sharpener_item):
    assert "<p>" in sharpener_item["description_html"]
    assert "puntenslijper" in sharpener_item["description_text"].lower()
    assert "<" not in sharpener_item["description_text"]  # tags stripped


def test_source_url_is_canonical_not_js(sharpener_item):
    assert sharpener_item["source_url"].endswith(
        "/products/faber-castell-tafelpuntenslijper"
    )
    assert ".js" not in sharpener_item["source_url"]


def test_single_variant_present(sharpener_item):
    assert len(sharpener_item["variants"]) == 1
    assert sharpener_item["variants"][0]["available"] is True


# --- multi-variant product (fountain pen with nib sizes) -----------------

@pytest.fixture
def pen_item(spider):
    url = "https://akkermandenhaag.nl/products/diplomat-aero-pure-black-limited-edition-vulpen.js"
    resp = _response_from_fixture("fountain_pen.js.json", url)
    return next(iter(spider.parse_product(resp)))


def test_nib_sizes_are_captured_as_variants(pen_item):
    # The dropdown for nib sizes shows up as one variant per nib.
    assert pen_item["option_names"] == ["Size"]
    titles = [v["title"] for v in pen_item["variants"]]
    assert "Fijn (F)" in titles
    assert "Medium (M)" in titles


def test_each_nib_has_its_own_stock_and_sku(pen_item):
    for v in pen_item["variants"]:
        assert "sku" in v and v["sku"]
        assert isinstance(v["available"], bool)  # per-nib stock preserved
        assert v["price"] is not None


def test_pen_price_in_major_units(pen_item):
    # 18099 cents -> 180.99 EUR
    assert pen_item["price"] == 180.99


# --- helper unit tests ---------------------------------------------------

def test_html_to_text_strips_and_collapses():
    assert _html_to_text("<p>Hello</p><p>World</p>") == "Hello World"
    assert _html_to_text("a<br>b   c") == "a b c"
    assert _html_to_text(None) == ""


def test_abs_url_handles_protocol_relative():
    assert _abs_url("//cdn.shopify.com/x.jpg") == "https://cdn.shopify.com/x.jpg"
    assert _abs_url("https://x/y.jpg") == "https://x/y.jpg"
    assert _abs_url(None) is None


def test_to_js_normalisation():
    to_js = AkkermanProductsSpider._to_js
    base = "https://akkermandenhaag.nl/collections/potloden/products/foo"
    assert to_js(base) == base + ".js"
    assert to_js(base + "/") == base + ".js"
    assert to_js(base + ".js") == base + ".js"
    assert to_js(base + ".json") == base + ".js"
    assert to_js(base + "?variant=1") == base + ".js"
