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
├── Makefile                  # help + fetch shortcuts (canonical version lands via integration branch)
├── requirements.txt          # runtime dependencies
├── requirements-dev.txt      # + test tooling
├── scrapy.cfg                # Scrapy project entry point
├── akkerman/
│   ├── __init__.py
│   ├── settings.py           # politeness, throttling, pipeline config
│   ├── items.py              # structured output schema(s)
│   ├── pipelines.py          # ParquetPipeline (items -> Parquet)
│   └── spiders/
│       ├── quotes.py            # example spider (quotes.toscrape.com)
│       └── akkerman_brands.py   # brands available at akkermandenhaag.nl
├── tests/                    # offline extraction/schema tests
└── data/                     # output datasets (Parquet)
```

## Quick Start (Makefile)

A shared `Makefile` exposes the essential commands. Run `make` (or `make help`)
for a self-documenting list. The **canonical, multi-stage `Makefile`** is
maintained on the integration branch (`kain/akkerman/greg`), where `fetch` runs
all spiders in order — categories → **brands** → products — each stage guarded so
a missing spider is skipped, not fatal:

```bash
make                 # show the command list (same as `make help`)
make install         # create .venv and install dependencies
make fetch           # run all fetch stages (categories -> brands -> products)
make fetch-brands    # run just the akkerman_brands spider (this task)
```

The brands stage below uses the exact `scrapy crawl akkerman_brands` command
documented under **Running a Crawl**, so it works standalone regardless of the
Makefile.

## Crawlers

### `akkerman_brands` — brands sold at akkermandenhaag.nl

akkermandenhaag.nl is a Shopify storefront. Its product `vendor` field is always
the shop itself ("P.W. Akkerman Den Haag"), so it is useless as a brand. The
reliable brand signal is a **capitalised product tag** (e.g. `Montblanc`) that
also corresponds to a storefront **collection**. The spider therefore:

1. Pages through `/collections.json` to build a lookup of every collection
   handle/title (case- and punctuation-insensitive).
2. Pages through `/products.json` counting capitalised tags per distinct
   spelling.
3. Emits the tags that intersect the collection lookup as brands, choosing the
   **most frequent spelling** as canonical (e.g. `Caran d'Ache` over the rare
   `Caran D'ache`).

Run it:

```bash
make fetch-brands           # or: scrapy crawl akkerman_brands
```

**Output schema** (`BrandItem`) — `data/akkerman_brands_<UTC-timestamp>.parquet`
(a stable copy is also kept at `data/akkerman_brands_latest.parquet`):

| column           | type | description                                    |
|------------------|------|------------------------------------------------|
| `brand`          | str  | canonical brand display name                   |
| `handle`         | str  | matching collection handle (slug)              |
| `collection_url` | str  | absolute URL to the brand's collection page    |
| `product_count`  | int  | number of products tagged with this brand      |
| `scraped_at`     | str  | ISO 8601 UTC timestamp of the crawl            |
| `source`         | str  | source domain (`akkermandenhaag.nl`)           |

The latest run captured **50 brands** across ~3,900 products (top brands:
Montblanc, Lamy, Kaweco, Parker, Caran d'Ache).

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
scrapy crawl akkerman_brands
```

Output lands in `data/<spider>_<UTC-timestamp>.parquet`. Inspect it:

```python
import pandas as pd
df = pd.read_parquet("data/akkerman_brands_latest.parquet")
print(df.sort_values("product_count", ascending=False).head())
```

## Adding a New Crawler

1. **Define the schema.** Add an `Item` subclass in `akkerman/items.py` listing
   the exact fields you want to land.
2. **Write the spider.** Create `akkerman/spiders/<name>.py` with a
   `scrapy.Spider` subclass. Set `allowed_domains`, map extracted values onto
   your Item.
3. **Crawl.** `scrapy crawl <name>` — the `ParquetPipeline` writes the results
   automatically. No extra wiring needed.

Politeness defaults (robots.txt obedience, `DOWNLOAD_DELAY`, AutoThrottle) live
in `akkerman/settings.py`. Tune per-spider with `custom_settings` when needed.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

All tests parse static fixtures, so they run fully offline.
