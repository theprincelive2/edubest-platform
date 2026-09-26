# 🎓 Edubest School Management Platform

> **Commercial SaaS** platform for schools. Multi-tenant, role-based, audit-logged, and API-first.

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.0-green)](https://djangoproject.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://docker.com)
[![License](https://img.shields.io/badge/License-Commercial-red)](LICENSE)

---

## 🏗️ Architecture Overview

Edubest uses **PostgreSQL schema-based multi-tenancy** via `django-tenants`. Each school gets its own isolated database schema — no possibility of cross-school data access.

```
https://schoolname.edubest.com → nginx → Django (routes to school's schema) → PostgreSQL
```

## 📦 Project Structure

```
edubest/
├── backend/          # Django 5 + DRF API
│   ├── config/       # Settings, URLs, WSGI
│   ├── apps/
│   │   ├── tenants/      # School tenant management
│   │   ├── users/        # Auth, roles, permissions
│   │   ├── audit/        # Audit logging
│   │   ├── academics/    # Students, teachers, classes
│   │   ├── attendance/   # Attendance tracking
│   │   ├── exams/        # Exams, results, report cards
│   │   ├── finance/      # Fees, invoices, payments
│   │   ├── messaging/    # Internal messaging
│   │   ├── admissions/   # Online admissions portal
│   │   ├── timetable/    # Timetable management
│   │   └── announcements/# News & notices
│   └── api/v1/       # Versioned REST API
├── frontend/         # Next.js 14 (App Router)
│   ├── app/(public)/ # Public school website
│   ├── app/(auth)/   # Authentication pages
│   ├── app/(admin)/  # Admin portal
│   ├── app/(parent)/ # Parent portal
│   └── app/(student)/# Student portal
└── docker/           # Docker, nginx, postgres configs
```

## 🚀 Quick Start (Development)

### Prerequisites
- Docker Desktop (Windows/Mac/Linux)
- Git

### 1. Clone & Configure
```bash
git clone https://github.com/your-org/edubest.git
cd edubest
cp .env.example .env
# Edit .env with your values
```

### 2. Start All Services
```bash
docker-compose up -d
```

### 3. Create First Tenant (School)
```bash
# Create the public schema migrations
docker-compose exec web python manage.py migrate_schemas --shared

# Create a platform superuser
docker-compose exec web python manage.py create_platform_admin

# Create your first school tenant
docker-compose exec web python manage.py shell_plus
```

```python
from apps.tenants.models import Client, Domain

# Create first school
tenant = Client(
    schema_name='greenfield',
    name='Greenfield Academy',
    school_code='GFA001',
    subdomain='greenfield',
    plan='premium',
)
tenant.save()

# Assign domain
domain = Domain()
domain.domain = 'greenfield.localhost'
domain.tenant = tenant
domain.is_primary = True
domain.save()
```

### 4. Access the Platform
| URL | Service |
|-----|---------|
| `http://localhost` | Public website / Admin portal |
| `http://localhost:3000` | Next.js dev server |
| `http://localhost:8000/api/v1/` | Django REST API |
| `http://localhost:8000/api/docs/` | Swagger UI |
| `http://localhost:8000/admin/` | Django Admin |
| `http://greenfield.localhost:8080/` | School portal (dev) |

---

## 🔐 Security Features

| Feature | Implementation |
|---------|---------------|
| **Tenant Isolation** | PostgreSQL schema per school |
| **Authentication** | JWT (15min access / 7day refresh) |
| **Authorization** | Fine-grained RBAC |
| **Audit Trail** | Every CUD operation logged |
| **Rate Limiting** | Per-IP and per-user |
| **Data Encryption** | Sensitive fields encrypted at rest |
| **HTTPS** | Enforced in production |
| **SQL Injection** | ORM-only (no raw SQL) |
| **XSS** | CSP headers, output escaping |
| **CSRF** | Django CSRF + SameSite cookies |

---

## 👥 Role System

| Role | Permissions |
|------|-------------|
| `platform_admin` | Full platform access (all tenants) |
| `school_admin` | Full school access |
| `principal` | Academic management, reports |
| `teacher` | Own classes: grades, attendance |
| `accountant` | Finance module |
| `receptionist` | Admissions, visitor logs |
| `parent` | Own children's data |
| `student` | Own data only |

---

## 📡 API Reference

**Base URL:** `https://{school}.edubest.com/api/v1/`

**Authentication:** `Authorization: Bearer <access_token>`

Full API documentation available at `/api/docs/` (Swagger UI).

---

## 🏫 Modules

- **Admissions** — Online application forms, status tracking
- **Academic Management** — Students, teachers, classes, subjects
- **Timetable** — Automated timetable generation
- **Attendance** — Daily & period-wise tracking with reports
- **Examinations** — Multi-type exams, grading scales, report cards (PDF)
- **Finance** — Fee structures, invoices, payments, receipts
- **Messaging** — Internal school communication
- **Announcements** — School-wide and role-targeted notices
- **Audit Logs** — Complete audit trail for compliance

---

## 🛠️ Development

```bash
# Run tests
docker-compose exec web pytest

# Create migrations
docker-compose exec web python manage.py makemigrations --schema=greenfield

# Django shell
docker-compose exec web python manage.py shell_plus --schema=greenfield

# Format code
docker-compose exec web black apps/
docker-compose exec web isort apps/
```

---

## 📈 Production Deployment

See [docs/deployment.md](docs/deployment.md) for full production deployment guide including:
- AWS/GCP setup
- SSL certificate configuration  
- Environment variable management
- Database backup strategy
- Monitoring & alerting

---

## 📄 License

Commercial License. All rights reserved. Contact sales@edubest.com for licensing.
