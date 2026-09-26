"""
Edubest — Production Settings
==============================
Tight security, S3 storage, Sentry error tracking, HTTPS enforcement.
All sensitive values MUST come from environment variables — never hardcoded.
"""

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *  # noqa: F401, F403
from decouple import config

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
DEBUG = False
SECRET_KEY = config("SECRET_KEY")  # Required — no default in production
ALLOWED_HOSTS: list[str] = config("ALLOWED_HOSTS", cast=lambda v: [s.strip() for s in v.split(",")])

# ---------------------------------------------------------------------------
# HTTPS & Security Headers
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000        # 1 year HSTS
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# ---------------------------------------------------------------------------
# Content Security Policy (django-csp)
# Prevents XSS by controlling which sources browsers trust
# ---------------------------------------------------------------------------
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)

# ---------------------------------------------------------------------------
# Database — production PostgreSQL with SSL
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 600,  # Persistent connections for performance
        "OPTIONS": {
            "sslmode": "require",
        },
    }
}

# ---------------------------------------------------------------------------
# AWS S3 Storage — media files in production
# Static files served by WhiteNoise (already configured in base)
# ---------------------------------------------------------------------------
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="us-east-1")
AWS_S3_CUSTOM_DOMAIN = config("AWS_S3_CUSTOM_DOMAIN", default=None)
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = "private"  # Files private by default; use pre-signed URLs
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_QUERYSTRING_AUTH = True  # Use pre-signed URLs for private media

MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"

# ---------------------------------------------------------------------------
# Email — production SMTP (e.g. SendGrid, AWS SES)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")

# ---------------------------------------------------------------------------
# CORS — strict whitelist in production
# ---------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    cast=lambda v: [s.strip() for s in v.split(",")],
)

# ---------------------------------------------------------------------------
# Sentry — error monitoring and performance tracing
# ---------------------------------------------------------------------------
SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(transaction_style="url"),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        # Capture 10% of transactions for performance monitoring
        traces_sample_rate=0.1,
        # Capture 10% of sessions for profiling
        profiles_sample_rate=0.1,
        send_default_pii=False,  # GDPR compliance — no PII in Sentry
        environment="production",
    )

# ---------------------------------------------------------------------------
# Logging — structured logs for production log aggregator (e.g. CloudWatch)
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
        if False  # Enable when python-json-logger is installed
        else "verbose",
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "apps": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
