"""
apps/tenants/admin.py
=====================
Django admin registrations for the tenants app.
Accessible to platform admins via /admin/.
"""

from django.contrib import admin

from apps.tenants.models import Client, Domain, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """Admin for managing SaaS subscription tiers."""

    list_display = ["display_name", "name", "max_students", "price_monthly", "price_annually", "is_active"]
    list_filter = ["name", "is_active"]
    search_fields = ["name", "display_name"]
    ordering = ["price_monthly"]
    fieldsets = (
        ("Plan Info", {"fields": ("name", "display_name", "is_active")}),
        ("Limits", {"fields": ("max_students", "max_teachers")}),
        ("Pricing", {"fields": ("price_monthly", "price_annually")}),
        ("Features", {"fields": ("features",), "classes": ("collapse",)}),
    )


class DomainInline(admin.TabularInline):
    """Inline domain editor within Client admin."""
    model = Domain
    extra = 1
    fields = ["domain", "is_primary"]


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Admin for managing school tenants."""

    list_display = [
        "name", "schema_name", "school_code", "plan",
        "is_active", "subscription_end", "created_at",
    ]
    list_filter = ["plan", "is_active"]
    search_fields = ["name", "school_code", "email", "schema_name"]
    readonly_fields = ["schema_name", "created_at", "updated_at"]
    inlines = [DomainInline]
    ordering = ["name"]
    fieldsets = (
        ("School Identity", {"fields": ("name", "schema_name", "school_code", "logo")}),
        ("Contact", {"fields": ("email", "phone", "address", "website")}),
        ("Subscription", {
            "fields": ("plan", "subscription_plan", "subscription_start", "subscription_end", "max_students")
        }),
        ("Status", {"fields": ("is_active", "created_at", "updated_at")}),
    )

    actions = ["suspend_tenants", "activate_tenants"]

    def suspend_tenants(self, request, queryset):
        """Bulk suspend selected tenants."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} tenant(s) suspended.")
    suspend_tenants.short_description = "Suspend selected tenants"

    def activate_tenants(self, request, queryset):
        """Bulk activate selected tenants."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} tenant(s) activated.")
    activate_tenants.short_description = "Activate selected tenants"


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Admin for managing tenant domain mappings."""

    list_display = ["domain", "tenant", "is_primary", "created_at"]
    list_filter = ["is_primary"]
    search_fields = ["domain", "tenant__name"]
    ordering = ["domain"]
