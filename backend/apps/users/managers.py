"""
apps/users/managers.py
======================
Custom manager for the Edubest User model.

Why a custom manager?
- Our User model uses `email` as the USERNAME_FIELD instead of `username`.
- Django's built-in UserManager assumes a `username` field exists.
- We must override create_user/create_superuser to set email correctly.
"""

from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Custom manager for the email-based User model.
    All users must have an email address; username is not used.
    """

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields,
    ) -> "User":  # type: ignore[name-defined]  # noqa: F821
        """
        Create and return a regular user with an email and password.

        Args:
            email: User's email address (serves as login identifier).
            password: Plain-text password (will be hashed via set_password).
            **extra_fields: Additional fields to set on the user model
                            (e.g., first_name, role, phone).

        Returns:
            The created User instance.

        Raises:
            ValueError: If email is not provided.
        """
        if not email:
            raise ValueError(_("The Email field must be set."))

        # Normalise email: lowercase domain part (e.g., User@SCHOOL.com → User@school.com)
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str,
        **extra_fields,
    ) -> "User":  # type: ignore[name-defined]  # noqa: F821
        """
        Create and return a superuser (platform administrator).

        Superusers:
        - Have is_staff=True (can access Django admin)
        - Have is_superuser=True (bypass all permission checks)
        - Have role='platform_admin'

        Args:
            email: Superuser's email address.
            password: Plain-text password.
            **extra_fields: Additional fields.

        Returns:
            The created superuser instance.

        Raises:
            ValueError: If is_staff or is_superuser are explicitly set to False.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "platform_admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)
