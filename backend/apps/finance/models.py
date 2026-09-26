"""
Edubest - Finance Models
==========================
Handles all financial operations:
  - Fee structure configuration per class/term
  - Automatic invoice generation
  - Payment recording with receipts
  - Outstanding fee tracking

Design notes:
  - Fee structures are templates; invoices are per-student instances
  - Payments are linked to invoices and auto-update invoice status
  - Receipt numbers are auto-generated and unique per tenant
  - All monetary amounts stored as Decimal for precision
"""

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.audit.mixins import AuditableMixin


class FeeStructure(AuditableMixin, models.Model):
    """
    Defines a fee type and amount for a specific class/term combination.

    Examples:
      - School Fees (JSS1, First Term): ₦45,000
      - Development Levy (All classes, Annual): ₦5,000
      - Exam Fee (SS3, Second Term): ₦3,500
    """

    class FeeCategory(models.TextChoices):
        TUITION = "tuition", "Tuition/School Fees"
        EXAM = "exam", "Examination Fee"
        DEVELOPMENT = "development", "Development Levy"
        SPORTS = "sports", "Sports/Activity Fee"
        LIBRARY = "library", "Library Fee"
        TRANSPORT = "transport", "Transport Fee"
        UNIFORM = "uniform", "Uniform Fee"
        BOOKS = "books", "Books/Materials"
        BOARDING = "boarding", "Boarding Fee"
        OTHER = "other", "Other"

    name = models.CharField(max_length=200, help_text="e.g., 'First Term School Fees 2024'")
    category = models.CharField(
        max_length=20,
        choices=FeeCategory.choices,
        default=FeeCategory.TUITION,
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.PROTECT,
        related_name="fee_structures",
    )
    term = models.ForeignKey(
        "academics.Term",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="fee_structures",
        help_text="Leave blank for annual fees that apply to all terms.",
    )
    # Null class = applies to ALL classes
    class_obj = models.ForeignKey(
        "academics.Class",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="fee_structures",
        help_text="Leave blank to apply this fee to all classes.",
        verbose_name="Class",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    due_date = models.DateField(null=True, blank=True)
    is_mandatory = models.BooleanField(
        default=True,
        help_text="Mandatory fees are automatically invoiced to all eligible students.",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_fee_structures",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-academic_year__start_date", "name"]
        verbose_name = "Fee Structure"
        verbose_name_plural = "Fee Structures"

    def __str__(self) -> str:
        class_str = self.class_obj.name if self.class_obj else "All Classes"
        term_str = self.term.name if self.term else "Annual"
        return f"{self.name} | {class_str} | {term_str}"


class Invoice(AuditableMixin, models.Model):
    """
    A fee invoice for a specific student.

    Invoices are created when fee structures are assigned to students.
    They track payment status and outstanding balance.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PARTIAL = "partial", "Partially Paid"
        PAID = "paid", "Fully Paid"
        OVERDUE = "overdue", "Overdue"
        WAIVED = "waived", "Waived"

    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Auto-generated unique invoice number.",
    )
    student = models.ForeignKey(
        "academics.Student",
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    amount_due = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total amount owed for this invoice.",
    )
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Total amount paid so far.",
    )
    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Scholarship or discount applied.",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"

    def __str__(self) -> str:
        return f"INV-{self.invoice_number} | {self.student} | {self.get_status_display()}"

    @property
    def balance(self) -> Decimal:
        """Outstanding balance (amount due minus discount minus paid)."""
        return self.amount_due - self.discount - self.amount_paid

    @property
    def is_overdue(self) -> bool:
        """True if unpaid and past due date."""
        return (
            self.due_date
            and self.status not in (self.Status.PAID, self.Status.WAIVED)
            and self.due_date < timezone.now().date()
        )

    def update_status(self) -> None:
        """Recompute and save invoice status based on payments received."""
        if self.amount_paid >= (self.amount_due - self.discount):
            self.status = self.Status.PAID
        elif self.amount_paid > 0:
            self.status = self.Status.PARTIAL
        elif self.is_overdue:
            self.status = self.Status.OVERDUE
        else:
            self.status = self.Status.PENDING
        self.save(update_fields=["status", "updated_at"])

    def save(self, *args, **kwargs):
        """Auto-generate invoice number on creation."""
        if not self.invoice_number:
            from utils.helpers import generate_unique_code
            self.invoice_number = generate_unique_code("INV", 8)
        super().save(*args, **kwargs)


class Payment(AuditableMixin, models.Model):
    """
    A payment record against an invoice.

    Each payment generates a unique receipt number and updates
    the parent invoice's status automatically.
    """

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        CARD = "card", "Debit/Credit Card"
        MOBILE_MONEY = "mobile_money", "Mobile Money"
        CHEQUE = "cheque", "Cheque"
        ONLINE = "online", "Online Payment"

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
    )
    reference_number = models.CharField(
        max_length=200,
        blank=True,
        help_text="Bank transaction ID, cheque number, POS reference, etc.",
    )
    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Auto-generated receipt number.",
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="recorded_payments",
        help_text="Staff member who recorded this payment.",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date", "-created_at"]
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self) -> str:
        return f"RCP-{self.receipt_number} | ₦{self.amount:,.2f} | {self.invoice}"

    def save(self, *args, **kwargs):
        """Auto-generate receipt, update invoice payment totals."""
        if not self.receipt_number:
            from utils.helpers import generate_receipt_number
            self.receipt_number = generate_receipt_number()

        super().save(*args, **kwargs)

        # Update the parent invoice's paid amount and status
        self._update_invoice()

    def _update_invoice(self) -> None:
        """Recalculate invoice amount_paid and status after this payment."""
        from django.db.models import Sum
        total_paid = self.invoice.payments.aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")

        self.invoice.amount_paid = total_paid
        self.invoice.update_status()
