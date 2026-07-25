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

# The product-data spider we care about (akkermandenhaag.nl, Shopify JSON).
PRODUCT_SPIDER  ?= akkerman_products

# Optional category-discovery spider contributed on a peer branch. `fetch`
# runs it if it exists and quietly skips it otherwise, so the product crawl
# never fails just because this spider isn't present.
CATEGORY_SPIDER ?= akkerman_categories

# Default target for `make fetch` with no arguments: the exact product page we
# have been extracting (name, price, stock, description, images, per-nib
# variant stock). Override with PRODUCT_URL=..., COLLECTIONS=... or ALL=1.
PRODUCT_URL ?= https://akkermandenhaag.nl/collections/potloden/products/faber-castell-tafelpuntenslijper
COLLECTIONS ?=
ALL         ?=

# Build the `-a` arguments for `akkerman_products` from the vars above.
# Precedence: ALL=1  >  COLLECTIONS=...  >  PRODUCT_URL=...
ifeq ($(strip $(ALL)),)
  ifeq ($(strip $(COLLECTIONS)),)
    PRODUCT_ARGS := -a url=$(PRODUCT_URL)
  else
    PRODUCT_ARGS := -a collections=$(COLLECTIONS)
  endif
else
  PRODUCT_ARGS := -a all=1
endif

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
		| awk 'BEGIN {FS = ":.*?## "} {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "Fetch examples:"
	@echo "  make fetch                                  # the default example product"
	@echo "  make fetch PRODUCT_URL=<product-page-url>   # one specific product"
	@echo "  make fetch COLLECTIONS=vulpennen,potloden   # whole collection(s)"
	@echo "  make fetch ALL=1                            # the entire store"
	@echo
	@echo "Config (override on the command line, e.g. make fetch PYTHON=python):"
	@echo "  PYTHON          = $(PYTHON)"
	@echo "  PRODUCT_SPIDER  = $(PRODUCT_SPIDER)"
	@echo "  CATEGORY_SPIDER = $(CATEGORY_SPIDER) (run if present)"

# ---------------------------------------------------------------------------
# Fetching data
# ---------------------------------------------------------------------------

.PHONY: fetch
fetch: fetch-categories fetch-products ## Fetch the akkerman data (categories if available, then products) -> data/*.parquet
	@echo "==> done. output in ./data/"

.PHONY: fetch-products
fetch-products: ## Fetch product data (name, price, stock, description, images, per-nib variants)
	@echo "==> crawling $(PRODUCT_SPIDER) $(PRODUCT_ARGS)"
	$(SCRAPY) crawl $(PRODUCT_SPIDER) $(PRODUCT_ARGS)

.PHONY: fetch-categories
fetch-categories: ## Discover categories via the peer spider if present (skipped if missing, never fails)
	@if $(SCRAPY) list 2>/dev/null | grep -qx "$(CATEGORY_SPIDER)"; then \
		echo "==> crawling $(CATEGORY_SPIDER)"; \
		$(SCRAPY) crawl $(CATEGORY_SPIDER); \
	else \
		echo "==> skipping category discovery ($(CATEGORY_SPIDER) not available)"; \
	fi

.PHONY: crawl
crawl: ## Run a single spider: make crawl SPIDER=<name> [ARGS="-a key=val"]
	@test -n "$(SPIDER)" || { echo "usage: make crawl SPIDER=<name> [ARGS=...]"; exit 2; }
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
