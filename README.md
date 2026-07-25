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
│       └── quotes.py         # example spider (quotes.toscrape.com)
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
scrapy list                 # show available spiders
scrapy crawl quotes         # run the example spider
```

Output lands in `data/<spider>_<UTC-timestamp>.parquet`. Inspect it:

```python
import pandas as pd
df = pd.read_parquet("data/quotes_20250101T000000Z.parquet")
print(df.head())
```

## Adding a New Crawler

1. **Define the schema.** Add an `Item` subclass in `akkerman/items.py` listing
   the exact fields you want to land.
2. **Write the spider.** Create `akkerman/spiders/<name>.py` with a
   `scrapy.Spider` subclass. Set `allowed_domains`, `start_urls`, and map
   extracted values onto your Item in `parse`.
3. **Crawl.** `scrapy crawl <name>` — the `ParquetPipeline` writes the results
   automatically. No extra wiring needed.

Politeness defaults (robots.txt obedience, `DOWNLOAD_DELAY`, AutoThrottle) live
in `akkerman/settings.py`. Tune per-spider with `custom_settings` when needed.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

The example spider's tests parse a static HTML fixture, so they run fully
offline.
