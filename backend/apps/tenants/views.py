"""
apps/tenants/views.py
=====================
ViewSet for managing school tenants — accessible only to platform admins.

The `create_tenant` action is the core onboarding flow:
1. Validates all fields
2. Creates the Client record (auto-creates PostgreSQL schema)
3. Creates the Domain record pointing to the new schema
4. Switches to the new schema context
5. Creates the school admin user inside the new schema
6. Returns a success response with connection details

All operations are wrapped in a transaction to ensure atomicity.
"""

import logging
from typing import Any

from django.db import transaction
from django_tenants.utils import schema_context
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.tenants.models import Client, Domain, SubscriptionPlan
from apps.tenants.serializers import (
    ClientDetailSerializer,
    ClientListSerializer,
    SubscriptionPlanSerializer,
    TenantCreateSerializer,
)
from apps.users.permissions import IsPlatformAdmin

logger = logging.getLogger(__name__)


class TenantViewSet(viewsets.ModelViewSet):
    """
    Platform admin ViewSet for managing school tenants.

    Endpoints:
      GET    /api/v1/tenants/              — List all schools
      POST   /api/v1/tenants/              — Create a new school (use create_tenant action)
      GET    /api/v1/tenants/{id}/         — School detail
      PATCH  /api/v1/tenants/{id}/         — Update school settings
      DELETE /api/v1/tenants/{id}/         — Delete school (hard delete — use with care!)
      POST   /api/v1/tenants/create/       — Onboard new school with admin user
      POST   /api/v1/tenants/{id}/suspend/ — Suspend school access
      POST   /api/v1/tenants/{id}/activate/ — Reactivate suspended school
    """

    queryset = Client.objects.prefetch_related("domains").order_by("name")
    permission_classes = [IsPlatformAdmin]
    filterset_fields = ["plan", "is_active"]
    search_fields = ["name", "school_code", "email"]
    ordering_fields = ["name", "created_at", "plan"]

    def get_serializer_class(self):
        if self.action == "list":
            return ClientListSerializer
        if self.action == "create_tenant":
            return TenantCreateSerializer
        return ClientDetailSerializer

    @action(detail=False, methods=["post"], url_path="create")
    def create_tenant(self, request: Request) -> Response:
        """
        POST /api/v1/tenants/create/

        Onboard a new school with a single API call.
        Creates:
          - PostgreSQL schema for the school
          - Client record with school details
          - Domain record (subdomain mapping)
          - School admin user inside the new schema

        This action is atomic — if any step fails, all changes are rolled back.
        """
        serializer = TenantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        full_domain = f"{data['subdomain']}.{data['domain_suffix']}"

        try:
            with transaction.atomic():
                # ---------------------------------------------------------------
                # Step 1: Create the Client (triggers schema creation)
                # ---------------------------------------------------------------
                client = Client.objects.create(
                    schema_name=data["schema_name"],
                    name=data["school_name"],
                    school_code=data["school_code"],
                    plan=data["plan"],
                    email=data.get("email", ""),
                    phone=data.get("phone", ""),
                    address=data.get("address", ""),
                    is_active=True,
                )
                logger.info(f"Created tenant schema: {client.schema_name}")

                # ---------------------------------------------------------------
                # Step 2: Create the Domain record
                # ---------------------------------------------------------------
                Domain.objects.create(
                    domain=full_domain,
                    tenant=client,
                    is_primary=True,
                )
                logger.info(f"Created domain: {full_domain}")

                # ---------------------------------------------------------------
                # Step 3: Create the school admin inside the new schema
                # ---------------------------------------------------------------
                with schema_context(client.schema_name):
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    admin_user = User.objects.create_user(
                        email=data["admin_email"],
                        password=data["admin_password"],
                        first_name=data["admin_first_name"],
                        last_name=data["admin_last_name"],
                        role="school_admin",
                        is_staff=True,
                    )
                    logger.info(f"Created school admin: {admin_user.email} in schema {client.schema_name}")

            return Response(
                {
                    "detail": "School onboarded successfully.",
                    "tenant": ClientDetailSerializer(client, context={"request": request}).data,
                    "admin_email": admin_user.email,
                    "portal_url": f"https://{full_domain}",
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:
            logger.error(f"Tenant creation failed: {exc}", exc_info=True)
            return Response(
                {"detail": f"Tenant creation failed: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"], url_path="suspend")
    def suspend(self, request: Request, pk: Any = None) -> Response:
        """
        POST /api/v1/tenants/{id}/suspend/
        Suspend a school (marks is_active=False). Users cannot log in.
        """
        client = self.get_object()
        client.is_active = False
        client.save(update_fields=["is_active", "updated_at"])
        logger.info(f"Suspended tenant: {client.schema_name} by {request.user.email}")
        return Response({"detail": f"Tenant '{client.name}' has been suspended."})

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request: Request, pk: Any = None) -> Response:
        """
        POST /api/v1/tenants/{id}/activate/
        Reactivate a suspended school.
        """
        client = self.get_object()
        client.is_active = True
        client.save(update_fields=["is_active", "updated_at"])
        logger.info(f"Activated tenant: {client.schema_name} by {request.user.email}")
        return Response({"detail": f"Tenant '{client.name}' has been activated."})


class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing subscription plans.
    Platform admins can CRUD plans; all authenticated users can list/retrieve.
    """

    queryset = SubscriptionPlan.objects.filter(is_active=True).order_by("price_monthly")
    serializer_class = SubscriptionPlanSerializer
    filterset_fields = ["name", "is_active"]
    search_fields = ["name", "display_name"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            from rest_framework.permissions import IsAuthenticated
            return [IsAuthenticated()]
        return [IsPlatformAdmin()]
