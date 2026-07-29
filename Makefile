# Makefile for the Akkerman monorepo project
#
# This Makefile orchestrates the full application stack (frontend + backend).
# The two essential targets are `help` (self-documenting) and `fetch` (run crawlers).
# Add a target with a `## description` comment and it auto-appears in `help`.
#
# Backend crawler stages (guarded):
#   1. akkerman_categories  (collection discovery)
#   2. akkerman_brands      (brand catalogue)
#   3. akkerman_products    (product details)

# ---------------------------------------------------------------------------
# Configuration (override on the command line, e.g. `make fetch ALL=1`)
# ---------------------------------------------------------------------------
# Prefer a backend project virtualenv if one exists, otherwise fall back to python3.
BACKEND_DIR ?= backend
VENV        ?= $(BACKEND_DIR)/.venv
PYTHON      ?= $(shell [ -x "$(VENV)/bin/python" ] && echo "$(VENV)/bin/python" || echo python3)
SCRAPY      ?= $(PYTHON) -m scrapy

DATA_DIR    ?= data
VERSION     ?= $(shell cat VERSION.txt 2>/dev/null || echo "0.1.0")

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
	@echo "Akkerman monorepo -- available commands:"
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
	@echo "Config: VERSION=$(VERSION)  PYTHON=$(PYTHON)  DATA_DIR=$(DATA_DIR)"

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
	@cd $(BACKEND_DIR) && if $(SCRAPY) list 2>/dev/null | grep -qx akkerman_categories; then \
		echo ">> stage: akkerman_categories"; \
		$(SCRAPY) crawl akkerman_categories; \
	else \
		echo ">> skip: akkerman_categories spider not present on this branch"; \
	fi

.PHONY: fetch-brands
fetch-brands: ## Fetch only the brand catalogue (akkerman_brands)
	@mkdir -p $(DATA_DIR)
	@cd $(BACKEND_DIR) && if $(SCRAPY) list 2>/dev/null | grep -qx akkerman_brands; then \
		echo ">> stage: akkerman_brands"; \
		$(SCRAPY) crawl akkerman_brands; \
	else \
		echo ">> skip: akkerman_brands spider not present on this branch"; \
	fi

.PHONY: fetch-products
fetch-products: ## Fetch only the product data (akkerman_products; honours selectors)
	@mkdir -p $(DATA_DIR)
	@cd $(BACKEND_DIR) && if ! $(SCRAPY) list 2>/dev/null | grep -qx akkerman_products; then \
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
# Docker Build Targets
# ---------------------------------------------------------------------------

.PHONY: docker-build
docker-build: ## Build Docker images for frontend and backend
	@echo ">> Building Docker images (version=$(VERSION))"
	docker build -t akkerman-backend:$(VERSION) -t akkerman-backend:latest $(BACKEND_DIR)
	docker build -t akkerman-frontend:$(VERSION) -t akkerman-frontend:latest frontend

.PHONY: docker-build-backend
docker-build-backend: ## Build only the backend Docker image
	@echo ">> Building backend Docker image (version=$(VERSION))"
	docker build -t akkerman-backend:$(VERSION) -t akkerman-backend:latest $(BACKEND_DIR)

.PHONY: docker-build-frontend
docker-build-frontend: ## Build only the frontend Docker image
	@echo ">> Building frontend Docker image (version=$(VERSION))"
	docker build -t akkerman-frontend:$(VERSION) -t akkerman-frontend:latest frontend

# ---------------------------------------------------------------------------
# Backend API Targets
# ---------------------------------------------------------------------------

.PHONY: run-backend
run-backend: ## Start the Flask backend development server
	@echo ">> Starting backend API server (development mode)"
	cd $(BACKEND_DIR) && $(PYTHON) app.py

.PHONY: test-backend
test-backend: ## Run backend API tests
	@echo ">> Running backend API tests"
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest test_app.py -v

.PHONY: healthz
healthz: ## Test the backend health endpoint
	@echo ">> Checking backend health endpoint"
	@curl -s http://localhost:5000/healthz | python3 -m json.tool || echo "Error: Backend not running on port 5000"

.PHONY: install-backend
install-backend: ## Install backend dependencies
	@echo ">> Installing backend dependencies"
	$(VENV)/bin/pip install -r $(BACKEND_DIR)/requirements.txt

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

.PHONY: version
version: ## Display the current version
	@echo "Akkerman version: $(VERSION)"

.PHONY: crawl
crawl: ## Run any spider by name: make crawl SPIDER=<name> [ARGS="-a k=v"]
	@mkdir -p $(DATA_DIR)
	cd $(BACKEND_DIR) && $(SCRAPY) crawl $(SPIDER) $(ARGS)

.PHONY: spiders
spiders: ## List the available spiders
	@cd $(BACKEND_DIR) && $(SCRAPY) list

.PHONY: install
install: ## Create a virtualenv and install runtime dependencies
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r $(BACKEND_DIR)/requirements.txt

.PHONY: install-dev
install-dev: install ## Install runtime + development dependencies
	$(VENV)/bin/pip install -r $(BACKEND_DIR)/requirements-dev.txt

.PHONY: test
test: ## Run the test suite
	$(PYTHON) -m pytest -q --rootdir=$(BACKEND_DIR)

.PHONY: clean
clean: ## Remove caches and generated artifacts (keeps committed datasets)
	rm -rf $(BACKEND_DIR)/.scrapy $(BACKEND_DIR)/.pytest_cache **/__pycache__ __pycache__
	find . -name '*.pyc' -delete
