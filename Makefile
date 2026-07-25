# Makefile for the akkerman crawler project.
#
# The two essential targets are `help` (self-documenting command list) and
# `fetch` (launch the spider to scrape the brand data we've been building).
# Add a new target with a `## description` comment and it shows up in `help`
# automatically -- no manual upkeep required.

# ---------------------------------------------------------------------------
# Configuration (override on the command line, e.g. `make fetch SPIDER=quotes`)
# ---------------------------------------------------------------------------
# Prefer a project virtualenv if one exists, otherwise fall back to python3.
VENV        ?= .venv
PYTHON      ?= $(shell [ -x "$(VENV)/bin/python" ] && echo "$(VENV)/bin/python" || echo python3)
SCRAPY      ?= $(PYTHON) -m scrapy

# The spider that fetches the brand catalogue we've been talking about.
SPIDER      ?= akkerman_brands
DATA_DIR    ?= data

.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------

.PHONY: help
help: ## Show this help (list of available commands)
	@echo "akkerman crawler -- available commands:"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "} {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Config: PYTHON=$(PYTHON)  SPIDER=$(SPIDER)  DATA_DIR=$(DATA_DIR)"

.PHONY: fetch
fetch: ## Launch the spider to fetch the brand data into data/*.parquet
	@mkdir -p $(DATA_DIR)
	$(SCRAPY) crawl $(SPIDER)

.PHONY: crawl
crawl: ## Run any spider: make crawl SPIDER=<name>
	@mkdir -p $(DATA_DIR)
	$(SCRAPY) crawl $(SPIDER)

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
