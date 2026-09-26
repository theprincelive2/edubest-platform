"""
apps/audit/mixins.py
====================
AuditableMixin — a model mixin that captures before/after state snapshots
whenever a model instance is saved or deleted.

Why a mixin instead of signals?
- Mixins make the "this model is audited" contract explicit in the class definition.
- Signals work globally but can be missed when using QuerySet.update() (bypasses save()).
- The mixin approach is more testable and readable for business logic.

Usage:
    class Student(AuditableMixin, models.Model):
        ...

Note: QuerySet.update() still bypasses this mixin. For bulk operations,
use apps.audit.signals which hooks into post_save/post_delete.
"""

import copy
from typing import Any


class AuditableMixin:
    """
    Mixin that captures model state before and after save/delete operations.
    The captured snapshots are stored as instance attributes so that
    audit signals (apps.audit.signals) can read them without an extra DB query.

    Attributes set on instance:
        _pre_save_state (dict | None): Field values before save() was called.
            None on the first save (creation).
        _post_save_state (dict | None): Field values after save() completes.
        _is_new (bool): True if this save() created a new DB row.
    """

    def _capture_state(self) -> dict[str, Any]:
        """
        Capture a snapshot of the current field values.

        Returns:
            Dictionary of {field_name: value} for all concrete fields.
            Excludes many-to-many and reverse relations (too expensive).
        """
        state: dict[str, Any] = {}
        # _meta.concrete_fields excludes M2M and virtual fields
        for field in self._meta.concrete_fields:  # type: ignore[union-attr]
            try:
                state[field.name] = copy.deepcopy(getattr(self, field.name))
            except Exception:
                # Skip fields that cannot be deepcopied (e.g., file fields)
                state[field.name] = str(getattr(self, field.name, ""))
        return state

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override save to capture before/after snapshots.
        The _pre_save_state is fetched from the DB before the write
        so we have accurate "old" values for the audit diff.
        """
        # Determine if this is a creation (no PK yet) or update
        self._is_new: bool = self.pk is None  # type: ignore[attr-defined]

        if not self._is_new:
            # Fetch the current DB state BEFORE our changes are written
            try:
                old_instance = self.__class__.objects.get(pk=self.pk)  # type: ignore[attr-defined]
                self._pre_save_state: dict[str, Any] | None = old_instance._capture_state()
            except self.__class__.DoesNotExist:
                self._pre_save_state = None
        else:
            self._pre_save_state = None

        # Perform the actual database write
        super().save(*args, **kwargs)  # type: ignore[misc]

        # Capture state AFTER the write (PK is now available for new records)
        self._post_save_state: dict[str, Any] | None = self._capture_state()

    def delete(self, *args: Any, **kwargs: Any) -> tuple:
        """
        Override delete to capture the final state before deletion.
        Signal receivers can use _pre_delete_state for audit records.
        """
        # Capture state before deletion so the audit log can record what was removed
        self._pre_delete_state: dict[str, Any] = self._capture_state()
        return super().delete(*args, **kwargs)  # type: ignore[misc]
