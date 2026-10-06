# Multi-Tenant SaaS Platform — Complete Architecture & Implementation Guide

This document is a comprehensive, production-ready guide detailing the architecture, configuration, data models, template layer, migration workflows, and operational procedures implemented for this multi-tenant Django SaaS project.

---

## 1. Project Overview & Multi-Tenant Architecture

This platform implements an **isolated-schema multi-tenancy** pattern using PostgreSQL schemas via `django-tenants`. Each client (tenant) has their own database schema, ensuring strict logical data isolation, security, and independent migration capabilities, while sharing the same underlying PostgreSQL database and Django codebase.

```
                           +---------------------------+
                           |   Incoming HTTP Request   |
                           +-------------+-------------+
                                         |
                                         v
                     +---------------------------------------+
                     | TenantMainMiddleware (Domain Lookup)  |
                     +-------------------+-------------------+
                                         |
                        +----------------+---------------+
                        |                                |
                        v                                v
             [ Schema: public ]                 [ Schema: tenant_* ]
             - Shared Core                      - Tenant-Specific
             - Tenant Registry                  - User Profiles
             - Domain Routing                   - CRM (Leads)
             - Django Admin / Sessions          - HRM (Employees/Depts)
```

### Key Architectural Separation

| Layer | Responsibility | Schemas | Apps Included |
| :--- | :--- | :--- | :--- |
| **Shared (Control Plane)** | System administration, tenant lifecycle management, public domains. | `public` | `django_tenants`, `tenant_manament`, `django.contrib.*` |
| **Tenant (Data Plane)** | Tenant-specific business operations, customer data, and modular features. | Dynamic (e.g., `acme`, `client_b`) | `user_management`, `crm`, `hrm`, `django.contrib.auth` |

---

## 2. Environment Setup & Project Initialization

### 2.1 Virtual Environment & Package Installation

The project runs on Python 3.14+ in an isolated virtual environment (`.venv`).

```bash
# 1. Create and activate virtual environment
python -m venv .venv

# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows Command Prompt:
.venv\Scripts\activate.bat

# 2. Core Dependencies
pip install django django-tenants psycopg2-binary python-dotenv
```

### 2.2 Environment Configuration (`.env`)

Database credentials and environment variables are externalized in `.env` at the root directory:

```env
DB_NAME=saas_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432
```

---

## 3. Database & Django Multi-Tenant Settings

File: `config/settings.py`

### 3.1 PostgreSQL Engine & Router

`django_tenants` replaces the standard PostgreSQL backend and uses a specialized database router to dispatch migrations and queries to either `public` or tenant-specific schemas.

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

TENANT_MODEL = "tenant_manament.Tenant"
TENANT_DOMAIN_MODEL = "tenant_manament.Domain"
```

### 3.2 Two-Tier Application Configuration

Apps are cleanly partitioned into `SHARED_APPS` and `TENANT_APPS`. `INSTALLED_APPS` is dynamically generated to avoid duplicate registration:

```python
SHARED_APPS = [
    'django_tenants',
    'tenant_manament',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

TENANT_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'user_management',
    'crm',
    'hrm',
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]
```

### 3.3 Middleware Configuration

To resolve the active tenant from the request hostname and switch PostgreSQL `search_path`, `TenantMainMiddleware` must be at the very top of `MIDDLEWARE`:

```python
MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

### 3.4 Template Directory Configuration

Global template overrides and base layouts are located in the root `templates/` folder:

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

---

## 4. Application Models & Modular Schema Design

### 4.1 Tenant Management (`tenant_manament/models.py`)

Defines the Tenant entity with dynamic feature gating capabilities (`active_modules`) and the Domain routing model:

```python
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Tenant(TenantMixin):
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)
    # Feature Gating: Stores active module keys, e.g. ["crm", "user_management"]
    active_modules = models.JSONField(default=list, blank=True)

    # Set to True so tenant schemas are automatically created in PostgreSQL on save
    auto_create_schema = True

    def __str__(self):
        return self.name

class Domain(DomainMixin):
    pass
```

### 4.2 User Management (`user_management/models.py`)

Extends Django's `User` model with per-tenant roles:

```python
from django.db import models
from django.contrib.auth.models import User

class TenantUserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Tenant Admin'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tenant_profile')
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
```

### 4.3 CRM Module (`crm/models.py`)

Lead management model for customer acquisition and pipeline tracking:

```python
from django.db import models

class Lead(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('lost', 'Lost'),
    ]
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company_name = models.CharField(max_length=150, blank=True)
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.company_name}"
```

### 4.4 HRM Module (`hrm/models.py`)

Human Resource Management model handling organizational structure and employees:

```python
from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Employee(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    designation = models.CharField(max_length=100)
    joining_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.designation})"
```

---

## 5. Front-End Architecture: Tailwind CSS, HTMX & Feature Gating

File: `templates/base/base.html`

The presentation layer combines:
1. **Tailwind CSS (CDN)** for modern, utility-first styling.
2. **HTMX (CDN)** for seamless, single-page-app-like asynchronous interactions without a heavy JavaScript frontend framework.
3. **Global CSRF Injection** automatically attaching `X-CSRFToken` to all HTMX requests.
4. **Dynamic Module Gating** inspecting `request.tenant.active_modules` to render navigation items strictly for subscriptions active on the current tenant.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ request.tenant.name }} | Multi-Tenant Portal</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- HTMX CDN -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
</head>
<body class="bg-slate-50 min-h-screen text-slate-800" hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>

    <!-- Top Navigation Bar -->
    <nav class="bg-indigo-900 text-white shadow-md">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between h-16 items-center">
            <div class="flex items-center space-x-3">
                <span class="font-bold text-xl tracking-tight">{{ request.tenant.name }}</span>
                <span class="text-xs bg-indigo-700 px-2.5 py-1 rounded-full text-indigo-200">
                    Schema: {{ request.tenant.schema_name }}
                </span>
            </div>

            <!-- Dynamic Module Navigation Links based on active_modules -->
            <div class="flex items-center space-x-4">
                <a href="/" class="hover:bg-indigo-800 px-3 py-2 rounded-md text-sm font-medium">Dashboard</a>

                {% if "user_management" in request.tenant.active_modules %}
                    <a href="/users/" class="hover:bg-indigo-800 px-3 py-2 rounded-md text-sm font-medium">Team</a>
                {% endif %}

                {% if "crm" in request.tenant.active_modules %}
                    <a href="/crm/" class="hover:bg-indigo-800 px-3 py-2 rounded-md text-sm font-medium">CRM Leads</a>
                {% endif %}

                {% if "hrm" in request.tenant.active_modules %}
                    <a href="/hrm/" class="hover:bg-indigo-800 px-3 py-2 rounded-md text-sm font-medium">HRM Employees</a>
                {% endif %}

                <a href="/admin/" class="text-slate-300 hover:text-white text-xs border border-slate-500 px-2 py-1 rounded">Admin Panel</a>
            </div>
        </div>
    </nav>

    <!-- Main Content Canvas -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {% block content %}
        {% endblock %}
    </main>

</body>
</html>
```

---

## 6. Migration Procedures & Operational Execution

Because schemas are divided into shared and tenant-specific tables, migrations must be created and applied following a strict two-step protocol.

### 6.1 Creating Migrations

```bash
# Generate migrations for all installed applications
python manage.py makemigrations
```

This creates initial migration files in:
- `tenant_manament/migrations/0001_initial.py`
- `user_management/migrations/0001_initial.py`
- `crm/migrations/0001_initial.py`
- `hrm/migrations/0001_initial.py`

### 6.2 Executing Migrations

`django-tenants` provides the `migrate_schemas` management command to replace standard `migrate`:

```bash
# 1. Migrate public (shared) schema first
python manage.py migrate_schemas --shared

# 2. Migrate all existing tenant schemas
python manage.py migrate_schemas --tenant
```

---

## 7. Creating Tenants & Domains (Django Shell)

To interactively bootstrap the public schema and provision new tenants:

```bash
python manage.py shell
```

### 7.1 Bootstrapping the Public (Control Plane) Tenant

```python
from tenant_manament.models import Tenant, Domain

# Step 1: Create and save the public tenant
public_tenant = Tenant(schema_name='public', name='Control Plane')
public_tenant.auto_create_schema = False # Schema already created by migrate_schemas
public_tenant.save()

# Step 2: Bind the primary localhost domain to the public tenant
public_domain = Domain()
public_domain.domain = 'localhost'
public_domain.tenant = public_tenant
public_domain.is_primary = True
public_domain.save()
```

### 7.2 Provisioning a New Customer Tenant

```python
from tenant_manament.models import Tenant, Domain

# Step 1: Instantiate tenant with enabled module keys
client = Tenant(
    schema_name='acme',
    name='Acme Corporation',
    active_modules=['crm', 'user_management']  # HRM is deactivated for Acme
)
# auto_create_schema is True: automatically provisions PostgreSQL schema and runs tenant migrations
client.save()

# Step 2: Bind tenant subdomain
domain = Domain()
domain.domain = 'acme.localhost'
domain.tenant = client
domain.is_primary = True
domain.save()
```

---

## 8. Troubleshooting & Common Pitfalls Encountered

### 8.1 Gotcha 1: `ImportError: cannot import name 'Tenant' from 'tenant_manament'`
- **Symptom:** Running `from tenant_manament import Tenant` in the shell raises an import error pointing to `__init__.py`.
- **Cause:** Python looks directly in `tenant_manament/__init__.py`.
- **Resolution:** Explicitly import from the models module:
  ```python
  from tenant_manament.models import Tenant, Domain
  ```

### 8.2 Gotcha 2: `ValueError: Model instances passed to related filters must be saved.`
- **Symptom:** Calling `domain.save()` crashes with a `ValueError`.
- **Cause:** `domain.tenant = public_tenant` assigned an unsaved model instance without a primary key. When `Domain.save()` executes, `django-tenants` queries `Domain.objects.filter(tenant=self.tenant, is_primary=True)`, which fails if `tenant.pk` is null.
- **Resolution:** Always invoke `tenant.save()` **before** calling `domain.save()`.

### 8.3 Gotcha 3: `SyntaxError: invalid non-printable character U+00A0`
- **Symptom:** Pasting code into the interactive terminal fails with `U+00A0`.
- **Cause:** Non-breaking space character (often introduced by copying formatted code from web pages or rich text editors).
- **Resolution:** Strip trailing spaces or retype the line cleanly in the terminal.

### 8.4 Gotcha 4: `ImproperlyConfigured: Application labels aren't unique, duplicates: crm`
- **Symptom:** `python manage.py makemigrations` fails with duplicate application label `crm`.
- **Cause:** Running `python manage.py startapp crm hrm` parsed `hrm` as the target directory for an app named `crm`, generating `class CrmConfig` with `name = 'crm'` in `hrm/apps.py`.
- **Resolution:** Edit `hrm/apps.py` to correctly define `HrmConfig` with `name = 'hrm'`:
  ```python
  from django.apps import AppConfig

  class HrmConfig(AppConfig):
      name = 'hrm'
  ```

---

## 9. Current Project Structure

```
saas_project/
├── .env                          # Database credentials & local env vars
├── .venv/                        # Python virtual environment
├── manage.py                     # Django project entrypoint
├── PROJECT_DOCUMENTATION.md      # Complete architectural documentation
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py               # Shared/Tenant apps, DB routing, Templates
│   ├── urls.py                   # Root URL routing
│   └── wsgi.py
├── tenant_manament/              # Control Plane app (Shared)
│   ├── migrations/
│   │   └── 0001_initial.py
│   ├── models.py                 # Tenant (TenantMixin), Domain (DomainMixin)
│   └── apps.py
├── user_management/              # Tenant User profiles & roles (Tenant App)
│   ├── migrations/
│   │   └── 0001_initial.py
│   ├── models.py                 # TenantUserProfile
│   └── apps.py
├── crm/                          # Customer Relationship Management (Tenant App)
│   ├── migrations/
│   │   └── 0001_initial.py
│   ├── models.py                 # Lead model
│   └── apps.py
├── hrm/                          # Human Resource Management (Tenant App)
│   ├── migrations/
│   │   └── 0001_initial.py
│   ├── models.py                 # Department, Employee models
│   └── apps.py                   # HrmConfig (name='hrm')
└── templates/
    └── base/
        └── base.html             # Base layout with Tailwind, HTMX & module gating
```

---

## 10. Next Steps & Recommended Implementation Roadmap

1. **Enable Middleware:** Ensure `'django_tenants.middleware.main.TenantMainMiddleware'` is at the very top of `MIDDLEWARE` in `config/settings.py`.
2. **Local Hosts / DNS Setup:** Add local domain aliases in Windows `C:\Windows\System32\drivers\etc\hosts`:
   ```
   127.0.0.1  localhost
   127.0.0.1  acme.localhost
   127.0.0.1  beta.localhost
   ```
3. **Tenant & Public URL Routing Separation:** Configure `PUBLIC_SCHEMA_URLCONF` and standard `ROOT_URLCONF` to serve distinct landing pages for the public domain vs tenant workspaces.
4. **HTMX Interactive Views:** Build partial views and modals for CRM Leads and HRM Employees extending `base.html` using HTMX swaps (`hx-get`, `hx-post`, `hx-target`).
