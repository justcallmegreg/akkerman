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
├── Makefile                  # `make help`, `make fetch`, … (see Quickstart)
├── requirements.txt          # runtime dependencies
├── requirements-dev.txt      # + test tooling
├── scrapy.cfg                # Scrapy project entry point
├── akkerman/
│   ├── __init__.py
│   ├── settings.py           # politeness, throttling, pipeline config
│   ├── items.py              # structured output schema(s)
│   ├── pipelines.py          # ParquetPipeline (items -> Parquet)
│   └── spiders/
│       ├── quotes.py             # example spider (quotes.toscrape.com)
│       ├── akkerman_products.py  # akkermandenhaag.nl product scraper
│       └── akkerman_brands.py    # brands available at akkermandenhaag.nl
├── tests/                    # offline extraction/schema tests (+ fixtures/)
└── data/                     # output datasets (Parquet) — gitignored
```

## Quickstart (make)

A `Makefile` wraps the essential commands. Run `make` on its own (or `make help`)
to list them:

```bash
make            # or: make help   → show all commands
make install    # create .venv and install runtime deps
make fetch      # fetch the akkerman data → data/*.parquet
```

`make fetch` runs the full pipeline in three **guarded** stages, in order:

1. **Category discovery** via `akkerman_categories` (collection discovery).
2. **Brand catalogue** via `akkerman_brands`.
3. **Product crawl** via `akkerman_products`.

Every stage is *optional*: if a stage's spider isn't present on your branch,
`fetch` prints a note and continues — it never fails on that account.

By default the product stage scrapes the single example product page. Point it at
whatever you need via variables (checked in order — `PRODUCT_URL`, then
`COLLECTIONS`, then `ALL`):

```bash
make fetch                                    # the default example product
make fetch PRODUCT_URL=https://akkermandenhaag.nl/collections/vulpennen/products/<handle>
make fetch COLLECTIONS=vulpennen,potloden     # whole collection(s)
make fetch ALL=1                              # the entire store
```

Run just one stage:

```bash
make fetch-categories    # category discovery only
make fetch-brands        # brand catalogue only
make fetch-products      # products only (honours the selectors above)
```

Other handy targets:

```bash
make spiders                       # list available spiders
make crawl SPIDER=quotes           # run a single spider by name
make crawl SPIDER=akkerman_products ARGS="-a all=1"
make test                          # run the offline test suite
make clean                         # remove crawled output and caches
```

The Makefile automatically uses `./.venv` if it exists; otherwise it falls back
to `python3` on your `PATH`. Override the interpreter with `make fetch PYTHON=python`.

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
scrapy crawl akkerman_products
scrapy crawl akkerman_brands
```

Output lands in `data/<spider>_<UTC-timestamp>.parquet`. Inspect it:

```python
import pandas as pd
df = pd.read_parquet("data/akkerman_brands_latest.parquet")
print(df.sort_values("product_count", ascending=False).head())
```

## Spider: `akkerman_products` (akkermandenhaag.nl)

Scrapes product data from **akkermandenhaag.nl**, a Shopify storefront.

Rather than parsing brittle HTML, it reads each product's Shopify JSON endpoint
(`<product-url>.js`). That document contains everything we need — and is the
*only* reliable source of **per-variant stock**: for a fountain pen, each nib
size (F, M, …) is a separate variant with its own price and in-stock flag, so we
never lose the fact that one nib can be available while another is sold out.

Extracted per product (`ProductItem` in `akkerman/items.py`):

| Field | Meaning |
|-------|---------|
| `name`, `vendor`, `product_type`, `tags`, `handle`, `product_id` | Identity |
| `images` | List of absolute CDN image URLs |
| `price`, `price_min`, `price_max`, `price_varies`, `currency` | Pricing (EUR, major units) |
| `available` | Whether **any** variant is in stock |
| `description_html`, `description_text` | Description (raw + plain text) |
| `option_names` | What the variants vary on, e.g. `["Size"]` for nib sizes |
| `variants` | One entry per variant: `title`, `sku`, `price`, **`available`** (per-nib stock), `options`, image |
| `source_url`, `scraped_at` | Provenance |

Product recommendations are intentionally **not** scraped (and `robots.txt`
disallows `/recommendations/products` anyway).

### Usage

```bash
# One product (any product/collection URL works; it's normalised to .js):
scrapy crawl akkerman_products \
  -a url=https://akkermandenhaag.nl/collections/potloden/products/faber-castell-tafelpuntenslijper

# Every product in one or more collections:
scrapy crawl akkerman_products -a collections=vulpennen,potloden

# The whole store:
scrapy crawl akkerman_products -a all=1
```

Or via the Makefile: `make fetch`, `make fetch COLLECTIONS=vulpennen`, `make fetch ALL=1`.

Reading nib-level stock back out of the Parquet file:

```python
import pandas as pd
df = pd.read_parquet("data/akkerman_products_<ts>.parquet")
row = df.iloc[0]
for v in row["variants"]:
    print(v["title"], "in stock:" , v["available"])
```

## Spider: `akkerman_brands` (akkermandenhaag.nl)

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
scrapy crawl akkerman_brands
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

## Adding a New Crawler

1. **Define the schema.** Add an `Item` subclass in `akkerman/items.py` listing
   the exact fields you want to land.
2. **Write the spider.** Create `akkerman/spiders/<name>.py` with a
   `scrapy.Spider` subclass. Set `allowed_domains`, seed requests (via
   `start_urls` or an async `start()` method), and map extracted values onto
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

Tests run fully offline against saved fixtures (static HTML for `quotes`, saved
Shopify JSON in `tests/fixtures/` for `akkerman_products`).
