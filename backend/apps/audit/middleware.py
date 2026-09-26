"""
apps/audit/middleware.py
========================
AuditMiddleware — captures request context (IP, user agent) for audit logging.

Why middleware instead of just signals?
- Signals fire at the model layer which has no HTTP context.
- This middleware stores IP/user-agent in thread-local storage where
  signal handlers and model save() methods can retrieve them.
- Also logs every authenticated request with its response status code.

Thread-local storage is safe because Django handles each HTTP request
in its own thread (or coroutine in async mode).
"""

import logging
import threading
import time
from typing import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)

# Thread-local storage for request context
# Keys: ip_address, user_agent, request (the full HttpRequest)
_thread_local = threading.local()


def get_current_request() -> HttpRequest | None:
    """
    Retrieve the current HTTP request from thread-local storage.
    Returns None if called outside a request context (e.g., in Celery tasks).
    """
    return getattr(_thread_local, "request", None)


def get_client_ip(request: HttpRequest) -> str | None:
    """
    Extract the real client IP from the request.

    Handles proxies (nginx, CloudFront) by checking X-Forwarded-For first.
    In production, ensure nginx sets this header correctly and strips
    untrusted IP values to prevent IP spoofing.

    Args:
        request: The Django HTTP request object.

    Returns:
        The client IP as a string, or None if not determinable.
    """
    # X-Forwarded-For: client, proxy1, proxy2
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # Take the first IP (leftmost) — the actual client IP
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class AuditMiddleware:
    """
    Django middleware that:
    1. Captures client IP and User-Agent from each request.
    2. Stores them in thread-local storage for access in signals/model saves.
    3. Attaches them to the request object for convenience in views.
    4. Logs authenticated requests with response status and duration.
    """

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request: capture context, call view, log result."""

        # Capture request context
        client_ip = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        # Store in thread-local for signal handlers and model methods
        _thread_local.request = request
        _thread_local.ip_address = client_ip
        _thread_local.user_agent = user_agent

        # Also attach to the request object for easy access in views
        request.audit_ip = client_ip
        request.audit_user_agent = user_agent

        # Record start time for response duration calculation
        start_time = time.monotonic()

        # Process the request
        response = self.get_response(request)

        # Log authenticated requests
        duration_ms = (time.monotonic() - start_time) * 1000

        if hasattr(request, "user") and request.user.is_authenticated:
            logger.debug(
                "API request: %s %s -> %d (%.0fms) by %s from %s",
                request.method,
                request.path,
                response.status_code,
                duration_ms,
                request.user.email,
                client_ip,
            )

            if response.status_code == 401:
                logger.warning(
                    "Unauthorized request: %s %s from %s (user: %s)",
                    request.method,
                    request.path,
                    client_ip,
                    request.user.email,
                )

        # Clean up thread-local storage to prevent memory leaks
        _thread_local.request = None
        _thread_local.ip_address = None
        _thread_local.user_agent = None

        return response
