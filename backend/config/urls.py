"""
Edubest — Master URL Configuration
====================================
Tenant-aware routing via django-tenants. The TenantMainMiddleware resolves
the incoming hostname to a schema, then the appropriate URL conf is loaded.

Two URL conf files exist:
  - config/urls.py (this file) — tenant-aware app URLs
  - config/urls_public.py      — public schema URLs (tenant admin, docs)
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# ---------------------------------------------------------------------------
# Admin site customisation
# ---------------------------------------------------------------------------
admin.site.site_header = "Edubest Administration"
admin.site.site_title = "Edubest Admin Portal"
admin.site.index_title = "Welcome to Edubest Platform"

# ---------------------------------------------------------------------------
# URL patterns
# These are tenant-scoped — each school's subdomain loads this conf after
# the middleware sets the correct PostgreSQL schema.
# ---------------------------------------------------------------------------
urlpatterns = [
    # Django admin — accessible per tenant
    path("admin/", admin.site.urls),

    # ---------------------------------------------------------------------------
    # API v1 — all application endpoints
    # ---------------------------------------------------------------------------
    path("api/v1/", include("api.v1.urls")),

    # ---------------------------------------------------------------------------
    # Authentication endpoints (SimpleJWT)
    # ---------------------------------------------------------------------------
    path("api/v1/auth/", include("apps.users.auth_urls")),

    # ---------------------------------------------------------------------------
    # OpenAPI Schema + Interactive Docs
    # Accessible at /api/schema/, /api/docs/, /api/redoc/
    # ---------------------------------------------------------------------------
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

# ---------------------------------------------------------------------------
# Serve media files in development (nginx/S3 handles this in production)
# ---------------------------------------------------------------------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
