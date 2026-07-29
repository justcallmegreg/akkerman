# Akkerman

A modern full-stack web application combining web crawling/scraping capabilities with a web frontend interface.

## Overview

This project is structured as a monorepo with two main components:

- **Frontend** — User-facing web application (see [`frontend/README.md`](frontend/README.md))
- **Backend** — Web crawler/scraper infrastructure (see [`backend/README.md`](backend/README.md))

## Project Structure

```
.
├── VERSION.txt                 # Semantic versioning (used across application)
├── Makefile                    # Build orchestration and CI/CD
├── LICENSE.md                  # Commercial license (Gergo Nagy)
├── README.md                   # This file
│
├── frontend/
│   ├── README.md               # Frontend documentation
│   ├── Dockerfile              # Container configuration
│   └── ...                      # Frontend source and config
│
├── backend/
│   ├── README.md               # Backend documentation
│   ├── Dockerfile              # Container configuration
│   ├── requirements.txt         # Python runtime dependencies
│   ├── requirements-dev.txt     # Python development dependencies
│   ├── akkerman/                # Scrapy crawler implementation
│   ├── tests/                   # Test suite
│   └── ...                      # Backend source and config
│
└── data/                        # Output datasets (Parquet format, gitignored)
```

## Version

Current version: **0.1.0** (see `VERSION.txt`)

All components reference this central version file for consistency across the application.

## Getting Started

### Prerequisites

- Python 3.10+ (for backend)
- Node.js 16+ (for frontend, if applicable)
- Docker (for containerized deployment)

### Installation

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend:**

```bash
cd frontend
# Installation instructions TBD
```

### Running Locally

Use the `Makefile` for convenient command orchestration:

```bash
make help          # Show all available commands
make install       # Install backend dependencies
make test          # Run test suite
make fetch         # Execute the full crawler pipeline
```

## License

This project is licensed under a **Commercial License** held by **Gergo Nagy**, compliant with Dutch law.

See [`LICENSE.md`](LICENSE.md) for full licensing terms.

## Deployment

Both `frontend/` and `backend/` include `Dockerfile` configurations for containerized deployment. CI/CD pipelines can be orchestrated via the `Makefile`.

For detailed build and deployment instructions, see the respective component READMEs.

---

**Copyright © Gergo Nagy. All rights reserved.**
