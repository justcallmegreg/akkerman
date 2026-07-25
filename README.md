# akkerman

A collection of Python web crawlers/scrapers that extract data from websites and
land it in **structured, compact data formats** — Parquet by default.

## Project Goal

Build reliable, maintainable crawlers (using [Scrapy](https://scrapy.org/) or
lightweight `requests` + `parsel` scripts) that:

1. **Crawl** target websites, respecting `robots.txt` and rate limits.
2. **Extract** the required fields into a well-defined schema.
3. **Store** the results in **Parquet** — columnar, compressed, and query-friendly —
   with an option to fall back to CSV/JSON when needed.

## Why Parquet?

- Columnar layout → efficient reads and analytics.
- Built-in compression → compact on-disk footprint.
- Rich typing and schema enforcement.
- First-class support in pandas, Polars, DuckDB, Spark, etc.

## Tech Stack

- **Python 3.10+**
- **Scrapy** — crawling framework
- **parsel** — HTML/XML parsing
- **pandas** + **pyarrow** — Parquet I/O

## Repository Layout

```
akkerman/
├── README.md
├── requirements.txt
├── .gitignore
├── spiders/          # Scrapy spiders / standalone scrapers
└── data/             # Output datasets (Parquet) — gitignored
```

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Status

🚧 Early scaffolding. Point the crawler at a target site and define the desired
schema to begin.
