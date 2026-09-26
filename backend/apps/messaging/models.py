"""
Edubest - Messaging Models
============================
Internal school communication system.

Features:
  - Direct messages between staff, parents, students
  - Broadcast messages to entire classes or role groups
  - Message threading (replies)
  - Read/unread tracking per recipient
  - Announcements (one-way, role-targeted)
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.audit.mixins import AuditableMixin


class Message(AuditableMixin, models.Model):
    """
    A message sent from one user to one or more recipients.

    Can be a direct message or a broadcast to a group.
    Replies are linked via parent_message to form threads.
    """

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_messages",
    )
    recipients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="MessageStatus",
        related_name="received_messages",
    )
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)
    is_broadcast = models.BooleanField(
        default=False,
        help_text="If True, this is a broadcast to a group (class, role, etc.)",
    )
    parent_message = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies",
        help_text="The original message this is a reply to.",
    )
    # Soft delete — messages are never hard-deleted
    is_deleted_by_sender = models.BooleanField(default=False)

    class Meta:
        ordering = ["-sent_at"]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self) -> str:
        return f"From {self.sender} | {self.subject[:50]} | {self.sent_at:%Y-%m-%d}"


class MessageStatus(models.Model):
    """
    Tracks per-recipient read status for a message.
    This is the through model for Message.recipients.
    """

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="statuses",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_statuses",
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft delete from recipient's inbox.",
    )

    class Meta:
        unique_together = [["message", "recipient"]]
        verbose_name = "Message Status"
        verbose_name_plural = "Message Statuses"

    def __str__(self) -> str:
        status = "Read" if self.is_read else "Unread"
        return f"{self.recipient} | {self.message.subject[:30]} | {status}"

    def mark_read(self) -> None:
        """Mark this message as read for this recipient."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])


class Announcement(AuditableMixin, models.Model):
    """
    School-wide or role-targeted announcements.

    Unlike messages, announcements are one-way (no replies)
    and are displayed in the portal dashboards.

    Examples:
      - "School reopens on Monday" (all roles)
      - "Staff meeting at 3pm" (staff only)
      - "Exam timetable released" (students and parents)
    """

    title = models.CharField(max_length=255)
    body = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="announcements",
    )
    # JSON list of role names this announcement is targeted at
    # Empty list = all roles
    target_roles = models.JSONField(
        default=list,
        blank=True,
        help_text='List of roles to target, e.g. ["parent", "student"]. Empty = all.',
    )
    target_classes = models.ManyToManyField(
        "academics.Class",
        blank=True,
        related_name="announcements",
        help_text="Specific classes to target. Empty = all classes.",
    )
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_pinned = models.BooleanField(
        default=False,
        help_text="Pinned announcements appear at the top of the dashboard.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-published_at"]
        verbose_name = "Announcement"
        verbose_name_plural = "Announcements"

    def __str__(self) -> str:
        return f"{self.title} | {self.published_at:%Y-%m-%d}" if self.published_at else self.title

    @property
    def is_published(self) -> bool:
        """True if the announcement is currently visible."""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.published_at and self.published_at > now:
            return False
        if self.expires_at and self.expires_at < now:
            return False
        return True
