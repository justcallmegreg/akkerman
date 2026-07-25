# akkerman — crawler task runner
#
# The two essential targets are:
#   make help    show the available commands (this is the default target)
#   make fetch   run the spiders to fetch the akkermandenhaag.nl data
#
# A handful of convenience targets round things out (install, test, clean,
# and single-stage / single-spider runs). Everything ultimately shells out to
# `scrapy`, so it works the same as running Scrapy by hand.

# ---------------------------------------------------------------------------
# Interpreter / tooling
# ---------------------------------------------------------------------------
# Prefer a local virtualenv at ./.venv if present, otherwise fall back to the
# python3 / scrapy on your PATH. Override with e.g. `make fetch PYTHON=python`.
VENV        := .venv
ifeq ($(wildcard $(VENV)/bin/python),)
PYTHON      ?= python3
SCRAPY      ?= scrapy
else
PYTHON      ?= $(VENV)/bin/python
SCRAPY      ?= $(VENV)/bin/scrapy
endif

# ---------------------------------------------------------------------------
# Spiders
# ---------------------------------------------------------------------------
PRODUCT_SPIDER  ?= akkerman_products
CATEGORY_SPIDER ?= akkerman_categories

# The specific product page we were asked to extract by default (name, price,
# stock, description, images, and per-nib variant stock for fountain pens).
PRODUCT_URL ?= https://akkermandenhaag.nl/collections/potloden/products/faber-castell-tafelpuntenslijper

# Optional selectors for the product stage. First non-empty wins:
#   ALL=1                       -> scrape the whole store
#   COLLECTIONS=vulpennen,...    -> scrape whole collection(s)
#   PRODUCT_URL=<url>            -> scrape a single product (default)
ifdef ALL
PRODUCT_ARGS := -a all=1
else ifdef COLLECTIONS
PRODUCT_ARGS := -a collections=$(COLLECTIONS)
else
PRODUCT_ARGS := -a url=$(PRODUCT_URL)
endif

# Escape hatch: run any spider with arbitrary args.
SPIDER ?=
ARGS   ?=

.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# help — describe the available commands
# ---------------------------------------------------------------------------
.PHONY: help
help:
	@echo "akkerman crawler — available commands:"
	@echo ""
	@echo "  make help              Show this help message (default)."
	@echo "  make fetch             Fetch the akkerman data -> data/*.parquet."
	@echo "                         Runs category discovery (if present), then"
	@echo "                         the product scraper."
	@echo ""
	@echo "  make fetch-products    Product crawl only (skip category discovery)."
	@echo "  make fetch-categories  Category discovery only."
	@echo "  make spiders           List available spiders."
	@echo "  make crawl SPIDER=<name> [ARGS=...]  Run a single spider by name."
	@echo "  make install           Create ./.venv and install runtime deps."
	@echo "  make test              Run the offline test suite (pytest)."
	@echo "  make clean             Remove crawled output and caches."
	@echo ""
	@echo "Product-stage selectors (first non-empty wins):"
	@echo "  make fetch ALL=1                          Scrape the whole store."
	@echo "  make fetch COLLECTIONS=vulpennen,potloden Scrape collection(s)."
	@echo "  make fetch PRODUCT_URL=<product page url> Scrape one product."
	@echo ""
	@echo "Output lands in data/<spider>_<UTC-timestamp>.parquet"

# ---------------------------------------------------------------------------
# fetch — launch the spiders to fetch the data (category discovery + products)
# ---------------------------------------------------------------------------
# Category discovery (teammate's akkerman_categories) is optional: it only runs
# if that spider is available on this branch, so `fetch` never hard-fails when
# the two branches haven't been merged yet.
.PHONY: fetch
fetch: fetch-categories fetch-products
	@echo ">> Done. See data/*.parquet"

.PHONY: fetch-categories
fetch-categories:
	@echo ">> Discovering product categories ($(CATEGORY_SPIDER))..."
	@if $(SCRAPY) list 2>/dev/null | grep -qx "$(CATEGORY_SPIDER)"; then \
		$(SCRAPY) crawl $(CATEGORY_SPIDER); \
	else \
		echo "   ($(CATEGORY_SPIDER) not available on this branch — skipping)"; \
	fi

.PHONY: fetch-products
fetch-products:
	@echo ">> Fetching product data ($(PRODUCT_SPIDER)) $(PRODUCT_ARGS)..."
	$(SCRAPY) crawl $(PRODUCT_SPIDER) $(PRODUCT_ARGS)

# ---------------------------------------------------------------------------
# Convenience targets
# ---------------------------------------------------------------------------
.PHONY: spiders
spiders:
	$(SCRAPY) list

.PHONY: crawl
crawl:
	@test -n "$(SPIDER)" || { echo "Usage: make crawl SPIDER=<name> [ARGS=...]"; exit 2; }
	$(SCRAPY) crawl $(SPIDER) $(ARGS)

.PHONY: install
install:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt

.PHONY: test
test:
	$(PYTHON) -m pytest -q

.PHONY: clean
clean:
	rm -f data/*.parquet
	rm -rf .scrapy .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
