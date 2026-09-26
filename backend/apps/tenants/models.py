"""
apps/tenants/models.py
======================
Tenant models for the Edubest SaaS platform.

Architecture:
- `Client` inherits TenantMixin (django-tenants) and represents a school.
  Each Client gets its own PostgreSQL schema, isolating all school data.
- `Domain` inherits DomainMixin and maps subdomains to Clients.
  e.g., greenfield.edubest.ng → schema: greenfield
- `SubscriptionPlan` defines the available SaaS tiers with feature flags
  and student limits. Stored in the public schema (shared across all tenants).
"""

from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

from apps.audit.mixins import AuditableMixin


class SubscriptionPlan(AuditableMixin, models.Model):
    """
    Represents a SaaS subscription tier (Free, Basic, Premium, Enterprise).
    Plans define what features are available and how many students are allowed.
    Stored in the public schema — shared across all tenants.
    """

    PLAN_CHOICES = [
        ("free", "Free"),
        ("basic", "Basic"),
        ("premium", "Premium"),
        ("enterprise", "Enterprise"),
    ]

    name = models.CharField(
        max_length=50,
        choices=PLAN_CHOICES,
        unique=True,
        help_text="Plan tier identifier.",
    )
    display_name = models.CharField(max_length=100, help_text="Human-readable plan name.")
    features = models.JSONField(
        default=dict,
        help_text=(
            "JSON object of feature flags and limits. "
            "Example: {'can_export_pdf': true, 'sms_notifications': false}"
        ),
    )
    max_students = models.PositiveIntegerField(
        default=100,
        help_text="Maximum number of active students allowed on this plan.",
    )
    max_teachers = models.PositiveIntegerField(default=20)
    price_monthly = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text="Monthly subscription price in NGN (or configured currency).",
    )
    price_annually = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text="Annual subscription price — typically discounted vs. 12x monthly.",
    )
    is_active = models.BooleanField(default=True, help_text="Inactive plans are hidden from signup.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["price_monthly"]
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

    def __str__(self) -> str:
        return f"{self.display_name} (₦{self.price_monthly}/mo)"


class Client(AuditableMixin, TenantMixin):
    """
    Represents a school tenant on the Edubest platform.

    TenantMixin provides:
      - schema_name: the PostgreSQL schema for this school
      - auto_create_schema: whether to create schema on save (default True)

    Each school gets a completely isolated database schema. Cross-schema
    queries are not possible — this is enforced at the DB driver level
    by django-tenants' custom PostgreSQL backend.
    """

    PLAN_CHOICES = [
        ("free", "Free"),
        ("basic", "Basic"),
        ("premium", "Premium"),
        ("enterprise", "Enterprise"),
    ]

    # -----------------------------------------------------------------------
    # Identity
    # -----------------------------------------------------------------------
    name = models.CharField(max_length=200, help_text="Official school name.")
    school_code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique alphanumeric code for the school (e.g., GFS001).",
    )
    logo = models.ImageField(
        upload_to="tenant_logos/",
        null=True,
        blank=True,
        help_text="School logo displayed on reports and the portal.",
    )

    # -----------------------------------------------------------------------
    # Contact
    # -----------------------------------------------------------------------
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True, help_text="Primary contact email for the school.")
    website = models.URLField(blank=True)

    # -----------------------------------------------------------------------
    # Subscription
    # -----------------------------------------------------------------------
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default="free",
        help_text="Current subscription tier.",
    )
    subscription_plan = models.ForeignKey(
        SubscriptionPlan,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clients",
        help_text="Linked plan object with detailed feature flags.",
    )
    subscription_start = models.DateField(
        null=True, blank=True, help_text="Date when subscription began."
    )
    subscription_end = models.DateField(
        null=True, blank=True, help_text="Date when subscription expires."
    )
    max_students = models.PositiveIntegerField(
        default=100,
        help_text="Student cap enforced at enrollment. Synced from plan but can be overridden.",
    )

    # -----------------------------------------------------------------------
    # Status
    # -----------------------------------------------------------------------
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive tenants cannot log in. Used for suspensions.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # django-tenants: creates the schema automatically when Client is saved
    auto_create_schema = True

    class Meta:
        ordering = ["name"]
        verbose_name = "School Tenant"
        verbose_name_plural = "School Tenants"

    def __str__(self) -> str:
        return f"{self.name} [{self.schema_name}] — {self.get_plan_display()}"

    @property
    def primary_domain(self) -> str:
        """Return the primary domain/subdomain for this tenant."""
        domain = self.domains.filter(is_primary=True).first()
        return domain.domain if domain else self.schema_name


class Domain(AuditableMixin, DomainMixin):
    """
    Maps a hostname (subdomain) to a Client tenant.

    DomainMixin provides:
      - domain: the full hostname (e.g., greenfield.edubest.ng)
      - tenant: FK to the Client model
      - is_primary: whether this is the primary domain for the tenant

    Multiple domains can point to one tenant (useful for custom domains
    in the Premium/Enterprise plan).
    """

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["domain"]
        verbose_name = "Tenant Domain"
        verbose_name_plural = "Tenant Domains"

    def __str__(self) -> str:
        primary = " [primary]" if self.is_primary else ""
        return f"{self.domain}{primary} → {self.tenant.name}"
