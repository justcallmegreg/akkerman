# akkerman — Makefile
#
# Essential entrypoints for the crawlers. Run `make` (or `make help`) to see
# every available command with a short description.
#
# Targets are self-documenting: any target followed by a `## comment` on the
# same line is picked up by `help` automatically, so keep those comments up to
# date when you add commands.

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Prefer a project virtualenv if one exists, otherwise fall back to whatever
# `python3` / `scrapy` is on PATH. Override with e.g. `make fetch PYTHON=python`.
VENV        ?= .venv
VENV_PYTHON := $(VENV)/bin/python
PYTHON      ?= $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),python3)
SCRAPY      ?= $(PYTHON) -m scrapy

# --- what `make fetch` scrapes ---------------------------------------------
# The akkerman_products spider takes one of three inputs. `fetch` uses whichever
# of these variables you set (checked in order), defaulting to the single
# example product page we have been working with.
#
#   make fetch                                   # the default example product
#   make fetch PRODUCT_URL=https://.../products/foo
#   make fetch COLLECTIONS=vulpennen,potloden    # whole collection(s)
#   make fetch ALL=1                             # the entire store
PRODUCT_URL ?= https://akkermandenhaag.nl/collections/potloden/products/faber-castell-tafelpuntenslijper
COLLECTIONS ?=
ALL         ?=

.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

.PHONY: help
help: ## Show this help (list of available commands)
	@echo "akkerman — available make commands:"
	@echo
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "} {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "Config (override on the command line, e.g. make fetch ALL=1):"
	@echo "  PYTHON      = $(PYTHON)"
	@echo "  PRODUCT_URL = $(PRODUCT_URL)"
	@echo "  COLLECTIONS = $(COLLECTIONS)"
	@echo "  ALL         = $(ALL)"

# ---------------------------------------------------------------------------
# Fetching data
# ---------------------------------------------------------------------------
#
# `fetch` runs the full pipeline in the agreed order:
#   1. akkerman_categories  — collection/category discovery (eniko's spider)
#   2. akkerman_products    — per-product data (name/price/stock/desc/images/nibs)
#
# Category discovery is optional: if the akkerman_categories spider is not
# installed yet, `fetch` prints a note and continues straight to products so it
# never fails on that account.

.PHONY: fetch
fetch: ## Fetch all akkerman data: discover categories, then crawl products -> data/*.parquet
	@if $(SCRAPY) list 2>/dev/null | grep -qx akkerman_categories; then \
		echo "==> [1/2] discovering categories (akkerman_categories)"; \
		$(SCRAPY) crawl akkerman_categories; \
	else \
		echo "==> [1/2] skipping category discovery (akkerman_categories spider not installed)"; \
	fi
	@echo "==> [2/2] crawling products"
	@if [ -n "$(ALL)" ]; then \
		echo "    whole store (all products)"; \
		$(SCRAPY) crawl akkerman_products -a all=1; \
	elif [ -n "$(COLLECTIONS)" ]; then \
		echo "    collections: $(COLLECTIONS)"; \
		$(SCRAPY) crawl akkerman_products -a collections=$(COLLECTIONS); \
	else \
		echo "    product: $(PRODUCT_URL)"; \
		$(SCRAPY) crawl akkerman_products -a url=$(PRODUCT_URL); \
	fi
	@echo "==> done. output in ./data/"

.PHONY: fetch-products
fetch-products: ## Fetch only product data (skip category discovery)
	@if [ -n "$(ALL)" ]; then \
		echo "==> crawling the whole store (all products)"; \
		$(SCRAPY) crawl akkerman_products -a all=1; \
	elif [ -n "$(COLLECTIONS)" ]; then \
		echo "==> crawling collections: $(COLLECTIONS)"; \
		$(SCRAPY) crawl akkerman_products -a collections=$(COLLECTIONS); \
	else \
		echo "==> crawling product: $(PRODUCT_URL)"; \
		$(SCRAPY) crawl akkerman_products -a url=$(PRODUCT_URL); \
	fi
	@echo "==> done. output in ./data/"

.PHONY: fetch-categories
fetch-categories: ## Fetch only category discovery data (akkerman_categories)
	$(SCRAPY) crawl akkerman_categories

.PHONY: crawl
crawl: ## Run a single spider by name: make crawl SPIDER=<name> [ARGS="-a k=v"]
	@test -n "$(SPIDER)" || { echo "usage: make crawl SPIDER=<name> [ARGS=\"-a k=v\"]"; exit 2; }
	$(SCRAPY) crawl $(SPIDER) $(ARGS)

.PHONY: spiders
spiders: ## List all available spiders
	$(SCRAPY) list

# ---------------------------------------------------------------------------
# Setup & quality
# ---------------------------------------------------------------------------

.PHONY: install
install: ## Install runtime dependencies (creates the .venv if missing)
	test -d $(VENV) || python3 -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.txt

.PHONY: install-dev
install-dev: install ## Install runtime + test/dev dependencies
	$(VENV_PYTHON) -m pip install -r requirements-dev.txt

.PHONY: test
test: ## Run the offline test suite
	$(PYTHON) -m pytest -q

.PHONY: clean
clean: ## Remove crawled output (data/*.parquet) and caches
	rm -f data/*.parquet
	rm -rf .scrapy .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
