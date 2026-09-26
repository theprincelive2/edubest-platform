#!/usr/bin/env bash
set -e

echo "==> Running database schema migrations..."
python manage.py migrate_schemas --noinput

echo "==> Bootstrapping public tenant and live superadmin..."
python manage.py setup_initial_tenant

echo "==> Starting Gunicorn server on port ${PORT:-8000}..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120
