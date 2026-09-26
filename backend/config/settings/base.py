"""
Edubest SaaS Platform — Base Django Settings
=============================================
Shared settings for all environments. Environment-specific files
(development.py, production.py) import this and override as needed.

Key architectural decisions:
- django-tenants: PostgreSQL schema isolation per school (tenant).
  SHARED_APPS live in the public schema (tenants, users, audit).
  TENANT_APPS are cloned into each school's private schema.
- Custom AUTH_USER_MODEL: email-based auth (no username).
- SimpleJWT: short-lived access tokens (15 min) + long refresh (7 days)
  so mobile/SPA clients stay logged in without constant re-auth.
- Redis: both cache backend AND Celery broker for consistency.
- drf-spectacular: auto-generates OpenAPI 3 schema from ViewSets.
"""

import os
from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Security — base values overridden per environment
# ---------------------------------------------------------------------------
SECRET_KEY = config("SECRET_KEY", default="change-me-in-production-secret-key-abc123")
DEBUG = False  # Always default to False; dev.py overrides to True
ALLOWED_HOSTS: list[str] = config("ALLOWED_HOSTS", default="*", cast=Csv())

# ---------------------------------------------------------------------------
# django-tenants: Schema-based multi-tenancy
# ---------------------------------------------------------------------------
# SHARED_APPS are installed in the public schema and are accessible
# to all tenants. Contains cross-tenant tables: Client, Domain, User, AuditLog.
SHARED_APPS = [
    # django-tenants MUST be first
    "django_tenants",
    # Django built-ins that live in public schema
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    # Third-party (shared)
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "django_celery_beat",
    # Our shared apps
    "apps.tenants",
    "apps.users",
    "apps.audit",
]

# TENANT_APPS are installed in each tenant's private schema.
# Do NOT include shared apps here — they would create duplicate tables.
TENANT_APPS = [
    "django.contrib.contenttypes",  # Required per-tenant for content types
    # Our tenant-scoped apps
    "apps.academics",
    "apps.attendance",
    "apps.exams",
    "apps.finance",
    "apps.messaging",
    "apps.admissions",
]

# django-tenants requires INSTALLED_APPS = SHARED_APPS + TENANT_APPS
# (minus duplicates). The helper below handles deduplication.
INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

# The model that represents a tenant (school)
TENANT_MODEL = "tenants.Client"
# The model that maps domains/subdomains to tenants
TENANT_DOMAIN_MODEL = "tenants.Domain"

# ---------------------------------------------------------------------------
# Database — Overridden in environment files
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": config("DB_NAME", default="edubest_db"),
        "USER": config("DB_USER", default="edubest_user"),
        "PASSWORD": config("DB_PASSWORD", default="edubest_pass"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
        "OPTIONS": {
            # Enforce SSL in production — overridden to {} in development
            "sslmode": config("DB_SSL_MODE", default="prefer"),
        },
    }
}

# Required by django-tenants to route tenant queries to proper schema
DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

# ---------------------------------------------------------------------------
# Custom User Model
# ---------------------------------------------------------------------------
# We use email as the unique identifier instead of username for a cleaner
# SaaS UX. All tenant users and platform admins share this model.
AUTH_USER_MODEL = "users.User"

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    # django-tenants middleware MUST be first — it sets the schema
    "django_tenants.middleware.main.TenantMainMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Our custom audit middleware — captures IP, user-agent, request context
    "apps.audit.middleware.AuditMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Password Validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = config("TIME_ZONE", default="Africa/Lagos")
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & Media Files
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# WhiteNoise compresses & caches static files without a CDN in dev/staging
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# Default primary key type
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    # JWT as the default auth — stateless, suitable for SPA/mobile
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        # Require auth by default; views can opt-out via permission_classes=[]
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Throttling — prevents brute-force and API abuse
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/hour",
        "user": "1000/hour",
    },
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
}

# ---------------------------------------------------------------------------
# SimpleJWT Configuration
# ---------------------------------------------------------------------------
SIMPLE_JWT = {
    # Short access token life forces frequent refresh — limits damage if leaked
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    # Refresh token stored securely on client, auto-rotated on each use
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    # Blacklist old refresh tokens after rotation to prevent reuse
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": config("JWT_SECRET_KEY", default=SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    # Include user role in token payload for frontend permission checks
    "TOKEN_OBTAIN_SERIALIZER": "apps.users.serializers.CustomTokenObtainPairSerializer",
}

# ---------------------------------------------------------------------------
# CORS — Cross-Origin Resource Sharing
# ---------------------------------------------------------------------------
# Allow specific origins in production (set via env). In dev, allow all.
CORS_ALLOWED_ORIGINS: list[str] = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://localhost:5173",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-tenant-id",  # Custom header for tenant identification in some flows
]

# ---------------------------------------------------------------------------
# Redis Cache
# ---------------------------------------------------------------------------
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Fail gracefully if Redis is down rather than crashing the app
            "IGNORE_EXCEPTIONS": True,
        },
        "KEY_PREFIX": "edubest",
        # Cache sessions in Redis for scalability across workers
        "TIMEOUT": 300,
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# ---------------------------------------------------------------------------
# Celery — Async task queue
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default=REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
# Celery Beat for scheduled tasks (fee reminders, report generation, etc.)
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_ALWAYS_EAGER = False  # Set True in tests to run tasks synchronously

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="Edubest <noreply@edubest.ng>")

# ---------------------------------------------------------------------------
# drf-spectacular (OpenAPI 3.0 schema generation)
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "Edubest School Management API",
    "DESCRIPTION": (
        "Production-grade multi-tenant SaaS API for school management. "
        "All tenant-scoped endpoints require a valid JWT Bearer token."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "TAGS": [
        {"name": "auth", "description": "Authentication & token management"},
        {"name": "tenants", "description": "Platform-level tenant management"},
        {"name": "users", "description": "User & role management"},
        {"name": "academics", "description": "Classes, subjects, students, teachers"},
        {"name": "attendance", "description": "Attendance tracking"},
        {"name": "exams", "description": "Exams, results & report cards"},
        {"name": "finance", "description": "Fees, invoices & payments"},
        {"name": "messaging", "description": "Internal messaging & announcements"},
        {"name": "admissions", "description": "Student admission applications"},
        {"name": "audit", "description": "Audit logs (admin only)"},
    ],
}

# ---------------------------------------------------------------------------
# Security Headers (base — production.py tightens these further)
# ---------------------------------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# ---------------------------------------------------------------------------
# File upload limits
# ---------------------------------------------------------------------------
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB
