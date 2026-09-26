"""
Edubest - Celery Application Configuration
==========================================
Celery is used for async tasks:
  - PDF report card generation
  - Email notifications
  - Bulk attendance imports
  - Fee reminder emails
  - Data export (Excel/CSV)

Multi-tenant note: Tasks that operate on tenant data must
explicitly set the schema context before accessing the DB.
"""

import os

from celery import Celery
from django.conf import settings

# Set default Django settings module for 'celery' program
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("edubest")

# Use Django's settings for Celery config (CELERY_* prefix)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all INSTALLED_APPS
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f"Request: {self.request!r}")
