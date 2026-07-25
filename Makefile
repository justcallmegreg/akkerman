# Makefile for the akkerman crawler project.
#
# The two essential targets are `help` (a self-documenting command list) and
# `fetch` (launch the spiders to scrape the akkermandenhaag.nl data we've been
# building). Add a new target with a `## description` comment and it shows up
# in `help` automatically -- no manual upkeep required.
#
# `fetch` runs the full pipeline in three guarded stages, in order:
#   1. akkerman_categories  (collection discovery -- eniko)
#   2. akkerman_brands      (brand catalogue    -- kain)
#   3. akkerman_products    (product details    -- greg)
# Each stage is optional: if its spider isn't present on the current branch,
# the stage prints a note and is skipped rather than failing the whole run.

# ---------------------------------------------------------------------------
# Configuration (override on the command line, e.g. `make fetch ALL=1`)
# ---------------------------------------------------------------------------
# Prefer a project virtualenv if one exists, otherwise fall back to python3.
VENV        ?= .venv
PYTHON      ?= $(shell [ -x "$(VENV)/bin/python" ] && echo "$(VENV)/bin/python" || echo python3)
SCRAPY      ?= $(PYTHON) -m scrapy

DATA_DIR    ?= data

# Product-stage selectors (checked in order: PRODUCT_URL, COLLECTIONS, ALL).
# Default (none set) crawls the example product page.
PRODUCT_URL ?=
COLLECTIONS ?=
ALL         ?=

# Generic spider override for the `crawl` target.
SPIDER      ?= akkerman_products
ARGS        ?=

.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------

.PHONY: help
help: ## Show this help (list of available commands)
	@echo "akkerman crawler -- available commands:"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "} {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "fetch runs three guarded stages, in order:"
	@echo "  1. akkerman_categories   collection discovery"
	@echo "  2. akkerman_brands       brand catalogue"
	@echo "  3. akkerman_products     product details (name/price/stock/images/nibs)"
	@echo ""
	@echo "Product-stage selectors (for fetch / fetch-products):"
	@echo "  make fetch                                  crawl the example product"
	@echo "  make fetch PRODUCT_URL=https://.../products/<handle>"
	@echo "  make fetch COLLECTIONS=vulpennen,potloden   crawl whole collection(s)"
	@echo "  make fetch ALL=1                            crawl the entire store"
	@echo ""
	@echo "Config: PYTHON=$(PYTHON)  DATA_DIR=$(DATA_DIR)"

# ---------------------------------------------------------------------------
# Fetch pipeline
# ---------------------------------------------------------------------------

.PHONY: fetch
fetch: ## Fetch all akkerman data: categories -> brands -> products (each guarded)
	@mkdir -p $(DATA_DIR)
	@$(MAKE) --no-print-directory fetch-categories
	@$(MAKE) --no-print-directory fetch-brands
	@$(MAKE) --no-print-directory fetch-products

.PHONY: fetch-categories
fetch-categories: ## Fetch only the collection-discovery data (akkerman_categories)
	@mkdir -p $(DATA_DIR)
	@if $(SCRAPY) list 2>/dev/null | grep -qx akkerman_categories; then \
		echo ">> stage: akkerman_categories"; \
		$(SCRAPY) crawl akkerman_categories; \
	else \
		echo ">> skip: akkerman_categories spider not present on this branch"; \
	fi

.PHONY: fetch-brands
fetch-brands: ## Fetch only the brand catalogue (akkerman_brands)
	@mkdir -p $(DATA_DIR)
	@if $(SCRAPY) list 2>/dev/null | grep -qx akkerman_brands; then \
		echo ">> stage: akkerman_brands"; \
		$(SCRAPY) crawl akkerman_brands; \
	else \
		echo ">> skip: akkerman_brands spider not present on this branch"; \
	fi

.PHONY: fetch-products
fetch-products: ## Fetch only the product data (akkerman_products; honours selectors)
	@mkdir -p $(DATA_DIR)
	@if ! $(SCRAPY) list 2>/dev/null | grep -qx akkerman_products; then \
		echo ">> skip: akkerman_products spider not present on this branch"; \
	elif [ -n "$(PRODUCT_URL)" ]; then \
		echo ">> stage: akkerman_products (url=$(PRODUCT_URL))"; \
		$(SCRAPY) crawl akkerman_products -a url="$(PRODUCT_URL)"; \
	elif [ -n "$(COLLECTIONS)" ]; then \
		echo ">> stage: akkerman_products (collections=$(COLLECTIONS))"; \
		$(SCRAPY) crawl akkerman_products -a collections="$(COLLECTIONS)"; \
	elif [ -n "$(ALL)" ]; then \
		echo ">> stage: akkerman_products (entire store)"; \
		$(SCRAPY) crawl akkerman_products -a all=1; \
	else \
		echo ">> stage: akkerman_products (default example product)"; \
		$(SCRAPY) crawl akkerman_products; \
	fi

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

.PHONY: crawl
crawl: ## Run any spider by name: make crawl SPIDER=<name> [ARGS="-a k=v"]
	@mkdir -p $(DATA_DIR)
	$(SCRAPY) crawl $(SPIDER) $(ARGS)

.PHONY: spiders
spiders: ## List the available spiders
	$(SCRAPY) list

.PHONY: install
install: ## Create a virtualenv and install runtime dependencies
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt

.PHONY: install-dev
install-dev: install ## Install runtime + development dependencies
	$(VENV)/bin/pip install -r requirements-dev.txt

.PHONY: test
test: ## Run the test suite
	$(PYTHON) -m pytest -q

.PHONY: clean
clean: ## Remove caches and generated artifacts (keeps committed datasets)
	rm -rf .scrapy .pytest_cache **/__pycache__ __pycache__
	find . -name '*.pyc' -delete
