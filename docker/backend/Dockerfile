# ============================================================
# Edubest Backend - Multi-Stage Dockerfile
# ============================================================
# Stages:
#   base        - Shared Python environment
#   development - Dev with hot reload
#   production  - Optimized, minimal image
# ============================================================

# ---- Base Stage ----
FROM python:3.12-slim as base

# Install system dependencies required for psycopg2, Pillow, ReportLab
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ---- Development Stage ----
FROM base as development

COPY requirements/development.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Copy source (in dev, volume mount overrides this)
COPY . .

EXPOSE 8000

# ---- Production Stage ----
FROM base as production

# Install only production deps
COPY requirements/production.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Create non-root user for security
RUN groupadd -r edubest && useradd -r -g edubest edubest

# Copy application source
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput --settings=config.settings.production || true

# Set correct ownership
RUN chown -R edubest:edubest /app

USER edubest

EXPOSE 8000

# Use gunicorn for production
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "gthread", \
     "--threads", "2", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]
