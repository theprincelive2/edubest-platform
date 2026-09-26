"""
Edubest - Shared Utilities
===========================
Common helper functions used across all apps.
"""

import re
import uuid
from datetime import date, datetime
from typing import Any


def generate_unique_code(prefix: str, length: int = 6) -> str:
    """
    Generate a unique alphanumeric code with a given prefix.

    Example:
        generate_unique_code('ADM', 6) → 'ADM-A3F92C'
    """
    unique_part = uuid.uuid4().hex[:length].upper()
    return f"{prefix}-{unique_part}"


def slugify_school_name(name: str) -> str:
    """
    Convert a school name to a URL-safe subdomain slug.

    Example:
        slugify_school_name('Greenfield Academy') → 'greenfield-academy'
    """
    name = name.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)   # Remove special chars
    name = re.sub(r"[\s_-]+", "-", name)    # Replace spaces with hyphens
    name = re.sub(r"^-+|-+$", "", name)     # Strip leading/trailing hyphens
    return name


def calculate_grade(score: float, grading_scale: list[dict]) -> str:
    """
    Calculate letter grade from a numeric score using a school's grading scale.

    Args:
        score: Numeric score (0-100)
        grading_scale: List of dicts with min_score, max_score, grade_letter

    Returns:
        Grade letter string (e.g., 'A', 'B+', 'F')
    """
    for grade_entry in sorted(grading_scale, key=lambda x: x["min_score"], reverse=True):
        if grade_entry["min_score"] <= score <= grade_entry["max_score"]:
            return grade_entry["grade_letter"]
    return "F"


def calculate_gpa(score: float, grading_scale: list[dict]) -> float:
    """Calculate GPA points from a numeric score."""
    for grade_entry in sorted(grading_scale, key=lambda x: x["min_score"], reverse=True):
        if grade_entry["min_score"] <= score <= grade_entry["max_score"]:
            return grade_entry.get("gpa_point", 0.0)
    return 0.0


def calculate_age(date_of_birth: date) -> int:
    """Calculate age in years from a date of birth."""
    today = date.today()
    return today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )


def format_currency(amount: float, currency: str = "NGN") -> str:
    """Format a currency amount with symbol."""
    symbols = {
        "NGN": "₦",
        "USD": "$",
        "GBP": "£",
        "EUR": "€",
        "GHS": "₵",
        "KES": "KSh",
    }
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def generate_receipt_number() -> str:
    """Generate a unique payment receipt number."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique = uuid.uuid4().hex[:4].upper()
    return f"RCP-{timestamp}-{unique}"


def mask_sensitive_data(data: dict[str, Any], sensitive_fields: list[str]) -> dict[str, Any]:
    """
    Mask sensitive fields in a dictionary for safe logging.

    Example:
        mask_sensitive_data({'email': 'a@b.com', 'password': 'secret'}, ['password'])
        → {'email': 'a@b.com', 'password': '***'}
    """
    masked = dict(data)
    for field in sensitive_fields:
        if field in masked:
            masked[field] = "***REDACTED***"
    return masked


def paginate_queryset(queryset, page: int, page_size: int) -> dict[str, Any]:
    """Simple pagination utility for querysets."""
    total = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    items = queryset[start:end]

    return {
        "count": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end < total,
        "has_previous": page > 1,
        "results": items,
    }


def get_client_ip(request) -> str:
    """
    Extract the real client IP address from a Django request.

    Handles X-Forwarded-For header for requests behind a proxy (nginx).
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2)
        # The first one is the original client IP
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "0.0.0.0")
    return ip
