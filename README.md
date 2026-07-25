# akkerman

A collection of Python web crawlers/scrapers that extract data from websites and
land it in **structured, compact data formats** — Parquet by default.

## Project Goal

Build reliable, maintainable crawlers (using [Scrapy](https://scrapy.org/)) that:

1. **Crawl** target websites, respecting `robots.txt` and rate limits.
2. **Extract** the required fields into a well-defined schema (see `akkerman/items.py`).
3. **Store** the results in **Parquet** — columnar, compressed, and query-friendly —
   via the `ParquetPipeline`.

## Why Parquet?

- Columnar layout → efficient reads and analytics.
- Built-in compression → compact on-disk footprint.
- Rich typing and schema enforcement.
- First-class support in pandas, Polars, DuckDB, Spark, etc.

## Tech Stack

- **Python 3.10+**
- **Scrapy** — crawling framework
- **parsel** — HTML/XML parsing (ships with Scrapy)
- **pandas** + **pyarrow** — Parquet I/O

## Repository Layout

```
akkerman/
├── README.md
├── requirements.txt          # runtime dependencies
├── requirements-dev.txt      # + test tooling
├── scrapy.cfg                # Scrapy project entry point
├── akkerman/
│   ├── __init__.py
│   ├── settings.py           # politeness, throttling, pipeline config
│   ├── items.py              # structured output schema(s)
│   ├── pipelines.py          # ParquetPipeline (items -> Parquet)
│   └── spiders/
│       ├── quotes.py                # example spider (quotes.toscrape.com)
│       └── akkerman_categories.py   # Akkerman Den Haag product categories
├── tests/                    # offline extraction/schema tests
└── data/                     # output datasets (Parquet) — gitignored
```

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running a Crawl

```bash
scrapy list                       # show available spiders
scrapy crawl quotes               # run the example spider
scrapy crawl akkerman_categories  # Akkerman Den Haag product categories
```

Output lands in `data/<spider>_<UTC-timestamp>.parquet`. Inspect it:

```python
import pandas as pd
df = pd.read_parquet("data/quotes_20250101T000000Z.parquet")
print(df.head())
```

## Crawlers

### `quotes` — example (quotes.toscrape.com)

Reference spider showing the Item → Parquet flow. Safe to run; the target is a
public scraping sandbox.

### `akkerman_categories` — Akkerman Den Haag product categories

[Akkerman Den Haag](https://akkermandenhaag.nl/) (P.W. Akkerman) is a **Shopify**
storefront, where **product categories are modelled as Shopify _collections_**.
Rather than scrape brittle rendered navigation HTML, this spider reads the
public `/collections.json` storefront endpoint (paginated via
`?limit=250&page=N`), which returns clean, typed records for *every* published
collection.

It lands the full category taxonomy (~306 categories) into
`ProductCategoryItem` (see `akkerman/items.py`): `collection_id`, `title`,
`handle`, `description`, `url`, `products_count`, `image`, `published_at`,
`updated_at`, plus crawl metadata (`scraped_at`, `source_url`).

```bash
scrapy crawl akkerman_categories
```

This is intentionally a **first step**: fetching categories gives us the entry
points (each collection's `handle`/`url`) needed to later crawl the products
inside every category, e.g. via `…/collections/<handle>/products.json`.

> **Note on access:** `akkermandenhaag.nl` is fronted by bot protection that
> rejects the default project `USER_AGENT`. Set a browser-like UA when running
> against the live site:
>
> ```bash
> scrapy crawl akkerman_categories \
>   -s USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
> ```
>
> robots.txt allows `/collections/` and does not disallow `/collections.json`,
> so the crawl is compliant.

## Adding a New Crawler

1. **Define the schema.** Add an `Item` subclass in `akkerman/items.py` listing
   the exact fields you want to land.
2. **Write the spider.** Create `akkerman/spiders/<name>.py` with a
   `scrapy.Spider` subclass. Set `allowed_domains` and seed requests from the
   async `start()` method (Scrapy 2.13+), or use `start_urls` for simple cases,
   then map extracted values onto your Item in `parse`.
3. **Crawl.** `scrapy crawl <name>` — the `ParquetPipeline` writes the results
   automatically. No extra wiring needed.

Politeness defaults (robots.txt obedience, `DOWNLOAD_DELAY`, AutoThrottle) live
in `akkerman/settings.py`. Tune per-spider with `custom_settings` when needed.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

The spiders' tests parse static fixtures (HTML for `quotes`, JSON for
`akkerman_categories`), so they run fully offline.
