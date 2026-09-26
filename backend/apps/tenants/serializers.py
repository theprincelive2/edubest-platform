"""
apps/tenants/serializers.py
============================
Serializers for tenant (school) management.
Used exclusively by platform admins to onboard new schools.
"""

from rest_framework import serializers

from apps.tenants.models import Client, Domain, SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Full plan detail for admin and public plan listing."""

    class Meta:
        model = SubscriptionPlan
        fields = [
            "id", "name", "display_name", "features",
            "max_students", "max_teachers",
            "price_monthly", "price_annually",
            "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class DomainSerializer(serializers.ModelSerializer):
    """Serializer for tenant domain records."""

    class Meta:
        model = Domain
        fields = ["id", "domain", "tenant", "is_primary", "created_at"]
        read_only_fields = ["id", "created_at"]


class ClientListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for tenant listing."""

    primary_domain = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            "id", "name", "schema_name", "school_code",
            "plan", "is_active", "primary_domain",
            "subscription_end", "created_at",
        ]
        read_only_fields = fields

    def get_primary_domain(self, obj: Client) -> str:
        return obj.primary_domain


class ClientDetailSerializer(serializers.ModelSerializer):
    """Full tenant detail for admin view."""

    domains = DomainSerializer(many=True, read_only=True)
    subscription_plan_detail = SubscriptionPlanSerializer(
        source="subscription_plan", read_only=True
    )

    class Meta:
        model = Client
        fields = [
            "id", "name", "schema_name", "school_code", "logo",
            "address", "phone", "email", "website", "plan",
            "subscription_plan", "subscription_plan_detail",
            "subscription_start", "subscription_end",
            "max_students", "is_active", "domains",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "schema_name", "created_at", "updated_at"]


class TenantCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new tenant (school) with its first domain
    and an initial school admin user.

    This is a compound operation:
    1. Create the Client (triggers schema creation)
    2. Create the Domain record
    3. Create the school admin user inside the new schema
    """

    # School info
    school_name = serializers.CharField(max_length=200)
    schema_name = serializers.CharField(
        max_length=63,
        help_text="PostgreSQL schema name. Lowercase, alphanumeric, underscores only.",
    )
    school_code = serializers.CharField(max_length=20)
    subdomain = serializers.CharField(
        max_length=63,
        help_text="Subdomain prefix (e.g., 'greenfield' → greenfield.edubest.ng).",
    )
    domain_suffix = serializers.CharField(
        max_length=100,
        default="edubest.ng",
        help_text="Domain suffix appended to subdomain.",
    )
    plan = serializers.ChoiceField(
        choices=["free", "basic", "premium", "enterprise"],
        default="free",
    )

    # School contact
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)

    # Initial admin user
    admin_email = serializers.EmailField(help_text="Email for the first school admin user.")
    admin_first_name = serializers.CharField(max_length=150)
    admin_last_name = serializers.CharField(max_length=150)
    admin_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )

    def validate_schema_name(self, value: str) -> str:
        """Ensure schema name is valid and not already taken."""
        import re
        if not re.match(r"^[a-z][a-z0-9_]*$", value):
            raise serializers.ValidationError(
                "Schema name must start with a letter and contain only lowercase "
                "letters, digits, and underscores."
            )
        if Client.objects.filter(schema_name=value).exists():
            raise serializers.ValidationError(f"Schema '{value}' is already in use.")
        return value

    def validate_school_code(self, value: str) -> str:
        """Ensure school code is unique."""
        if Client.objects.filter(school_code=value.upper()).exists():
            raise serializers.ValidationError(
                f"School code '{value}' is already assigned to another school."
            )
        return value.upper()

    def validate_subdomain(self, value: str) -> str:
        """Ensure the subdomain is not already registered."""
        import re
        if not re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", value.lower()):
            raise serializers.ValidationError(
                "Subdomain must be lowercase alphanumeric with optional hyphens."
            )
        return value.lower()
