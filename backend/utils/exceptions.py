"""
Edubest - Custom Exception Handler
===================================
Provides consistent JSON error responses across the entire API.
All errors follow the same envelope format:

  {
    "success": false,
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "...",
      "details": {...}
    }
  }
"""

import logging
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """
    Custom DRF exception handler that wraps all errors in a consistent envelope.

    This ensures that every error response from the API has the same shape,
    making it easier for frontend clients to handle errors uniformly.
    """
    # Call DRF's default handler first to get the standard response
    response = exception_handler(exc, context)

    if response is not None:
        # DRF handled it — wrap in our envelope
        error_code = _get_error_code(exc)
        error_message = _get_error_message(exc, response)

        response.data = {
            "success": False,
            "error": {
                "code": error_code,
                "message": error_message,
                "details": _get_error_details(response.data),
            },
        }
    else:
        # Unhandled exception — return generic 500
        logger.error(
            "Unhandled exception in API",
            exc_info=exc,
            extra={"view": context.get("view"), "request": context.get("request")},
        )
        response = Response(
            {
                "success": False,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "An unexpected error occurred. Please try again later.",
                    "details": {},
                },
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _get_error_code(exc: Exception) -> str:
    """Map exception types to readable error codes."""
    from rest_framework.exceptions import (
        AuthenticationFailed,
        MethodNotAllowed,
        NotAuthenticated,
        NotFound,
        ParseError,
        PermissionDenied,
        Throttled,
        ValidationError,
    )

    error_map = {
        ValidationError: "VALIDATION_ERROR",
        NotAuthenticated: "AUTHENTICATION_REQUIRED",
        AuthenticationFailed: "AUTHENTICATION_FAILED",
        PermissionDenied: "PERMISSION_DENIED",
        NotFound: "NOT_FOUND",
        Http404: "NOT_FOUND",
        MethodNotAllowed: "METHOD_NOT_ALLOWED",
        Throttled: "RATE_LIMIT_EXCEEDED",
        ParseError: "PARSE_ERROR",
    }

    for exc_class, code in error_map.items():
        if isinstance(exc, exc_class):
            return code

    return "API_ERROR"


def _get_error_message(exc: Exception, response: Response) -> str:
    """Extract a human-readable message from the exception."""
    if hasattr(exc, "detail"):
        detail = exc.detail
        if isinstance(detail, str):
            return detail
        if isinstance(detail, list) and len(detail) > 0:
            return str(detail[0])
        if isinstance(detail, dict):
            # Return first error message from dict
            first_key = next(iter(detail))
            first_val = detail[first_key]
            if isinstance(first_val, list):
                return f"{first_key}: {first_val[0]}"
            return f"{first_key}: {first_val}"
    return "An error occurred."


def _get_error_details(data: Any) -> Any:
    """Normalize error details for consistent structure."""
    if isinstance(data, dict):
        # Remove 'detail' key if it's the only key
        if list(data.keys()) == ["detail"]:
            return {}
        return data
    if isinstance(data, list):
        return {"errors": data}
    return {}


class TenantNotFoundError(Exception):
    """Raised when a tenant subdomain is not found in the database."""
    pass


class SubscriptionExpiredError(Exception):
    """Raised when a school's subscription has expired."""
    pass


class InsufficientPermissionsError(PermissionDenied):
    """Raised when a user attempts an action they don't have permission for."""

    def __init__(self, permission_codename: str | None = None):
        if permission_codename:
            message = f"You don't have the required permission: '{permission_codename}'"
        else:
            message = "You don't have permission to perform this action."
        super().__init__(detail=message)
