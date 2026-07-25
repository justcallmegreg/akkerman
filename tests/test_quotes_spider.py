"""Offline tests for the quotes spider extraction logic.

These build a fake Scrapy Response from a static HTML fixture so we can assert
the parsing/schema behaviour without hitting the network.
"""

from scrapy.http import HtmlResponse, Request

from akkerman.spiders.quotes import QuotesSpider

FIXTURE_HTML = """
<html><body>
  <div class="quote">
    <span class="text">\u201cA witty saying proves nothing.\u201d</span>
    <span>by <small class="author">Voltaire</small>
      <a href="/author/Voltaire">(about)</a>
    </span>
    <div class="tags">
      <a class="tag" href="/tag/wit">wit</a>
      <a class="tag" href="/tag/humor">humor</a>
    </div>
  </div>
  <nav><ul class="pager">
    <li class="next"><a href="/page/2/">Next</a></li>
  </ul></nav>
</body></html>
"""


def _make_response(url="https://quotes.toscrape.com/", body=FIXTURE_HTML):
    request = Request(url=url)
    return HtmlResponse(url=url, request=request, body=body.encode("utf-8"))


def test_parse_extracts_expected_fields():
    spider = QuotesSpider()
    results = list(spider.parse(_make_response()))

    items = [r for r in results if isinstance(r, dict) or hasattr(r, "keys")]
    assert len(items) == 1

    item = items[0]
    assert item["text"] == "A witty saying proves nothing."
    assert item["author"] == "Voltaire"
    assert item["author_url"] == "https://quotes.toscrape.com/author/Voltaire"
    assert item["tags"] == ["wit", "humor"]
    assert item["source_url"] == "https://quotes.toscrape.com/"
    assert item["scraped_at"]  # non-empty ISO timestamp


def test_parse_follows_pagination():
    spider = QuotesSpider()
    results = list(spider.parse(_make_response()))

    requests = [r for r in results if isinstance(r, Request)]
    assert len(requests) == 1
    assert requests[0].url == "https://quotes.toscrape.com/page/2/"


def test_no_pagination_when_absent():
    spider = QuotesSpider()
    html = '<html><body><div class="quote">'
    html += '<span class="text">x</span>'
    html += '<small class="author">A</small></div></body></html>'
    results = list(spider.parse(_make_response(body=html)))

    requests = [r for r in results if isinstance(r, Request)]
    assert requests == []
