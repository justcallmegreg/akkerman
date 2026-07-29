FROM python:3.11-slim

LABEL maintainer="Akkerman Backend"
LABEL description="Akkerman backend API service with Flask and SQLAlchemy"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 akkerman && chown -R akkerman:akkerman /app
USER akkerman

# Expose port for the Flask application
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/healthz')" || exit 1

# Run with Gunicorn in production
# - 4 workers for production (adjust based on CPU cores)
# - Bind to 0.0.0.0:5000 to be accessible from outside container
# - Timeout of 120 seconds for long-running requests
CMD ["gunicorn", \
     "--workers=4", \
     "--worker-class=sync", \
     "--bind=0.0.0.0:5000", \
     "--timeout=120", \
     "--access-logfile=-", \
     "--error-logfile=-", \
     "app:create_app()"]

