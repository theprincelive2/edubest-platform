"""
Edubest — Development Settings
================================
Overrides for local development. Never use in production.
Enables debug toolbar, verbose logging, and relaxed security.
"""

from .base import *  # noqa: F401, F403
from decouple import config

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
DEBUG = True
SECRET_KEY = config("SECRET_KEY", default="dev-insecure-secret-key-abc123xyz")
ALLOWED_HOSTS = ["*", "localhost", "127.0.0.1", ".localhost"]

# ---------------------------------------------------------------------------
# Database — local PostgreSQL instance
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": config("DB_NAME", default="edubest_dev"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default="postgres"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
        # No SSL for local dev
        "OPTIONS": {},
    }
}

# ---------------------------------------------------------------------------
# Email — print to console instead of sending real emails
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ---------------------------------------------------------------------------
# Django Debug Toolbar
# ---------------------------------------------------------------------------
INSTALLED_APPS = INSTALLED_APPS + ["debug_toolbar"]  # noqa: F405
MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
] + MIDDLEWARE  # noqa: F405

INTERNAL_IPS = ["127.0.0.1"]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,  # noqa: F405
}

# ---------------------------------------------------------------------------
# CORS — allow all origins in dev
# ---------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True

# ---------------------------------------------------------------------------
# Celery — run tasks synchronously in dev for easy debugging
# Flip to False to test real async behavior with a local Redis + worker
# ---------------------------------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = config("CELERY_EAGER", default=True, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = True

# ---------------------------------------------------------------------------
# Cache — use local memory in dev (faster, no Redis dependency)
# Set REDIS_CACHE=true to use Redis for testing cache behavior
# ---------------------------------------------------------------------------
USE_REDIS_CACHE = config("REDIS_CACHE", default=False, cast=bool)
if not USE_REDIS_CACHE:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }

# ---------------------------------------------------------------------------
# Logging — more verbose in dev
# ---------------------------------------------------------------------------
LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["django"]["level"] = "DEBUG"  # noqa: F405

# ---------------------------------------------------------------------------
# Media files served by Django dev server
# ---------------------------------------------------------------------------
# In production, nginx or S3 handles media. In dev, Django serves them.
MEDIA_URL = "/media/"
