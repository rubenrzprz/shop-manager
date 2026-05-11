# Shop Manager 🛍️

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/ui-PySide6-41CD52?logo=qt&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/database-PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/orm-SQLAlchemy-D71F00)
![pytest](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)
![Ruff](https://img.shields.io/badge/lint-Ruff-D7FF64)

Shop Manager is a desktop application for store operations, built incrementally around a clean
Python architecture. It uses PySide6 for the Windows-friendly UI, PostgreSQL for persistence, and
application services to keep business logic out of the interface layer.

## What It Does Today ✅

- 📦 Products: create, list, edit, search/filter, manage variants and categories, activate/deactivate
- 🤝 Suppliers: create, list, edit
- 👥 Customers: create, list, edit
- 🧾 Orders: create, edit, calculate totals, apply discounts, validate deadlines
- 🔁 Order workflows: configurable statuses, advance/revert/cancel/recover actions
- ✅ Tasks: create one-off and order-linked reminders, generate recurring and active-order
  follow-up reminders, list daily tasks, complete and reopen tasks
- ⚙️ Settings: typed application settings backed by the database
- 🌐 Localization: English and Spanish UI labels/messages
- 🏠 Dashboard shell: entry tab with quick actions and daily task reminders

## What Is Coming 🧭

- 📅 Calendar-based task planning
- 🔁 Manual recurring reminder creation
- 🧭 Dashboard and reminder UI polish
- 🏷️ Product category grouping polish
- 📦 Stock movements
- 🚚 Shipment workflows

## Tech Stack 🧰

| Area | Tooling |
| --- | --- |
| Language | Python 3.12+ |
| Desktop UI | PySide6 |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Tests | pytest, Testcontainers |
| Quality | Ruff, Black, compile checks |
| CI | GitHub Actions |

## Quick Start 🚀

### 1. Create The Virtual Environment

Linux/macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test,dev]"
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test,dev]"
```

### 2. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Default values:

```env
APP_ENV=development

POSTGRES_DB=shop_manager
POSTGRES_USER=shop_user
POSTGRES_PASSWORD=shop_pass
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

DATABASE_URL=postgresql+psycopg://shop_user:shop_pass@localhost:5432/shop_manager
```

If you already have a PostgreSQL database with different credentials, update both the `POSTGRES_*`
values and `DATABASE_URL` so they match.

### 3. Start PostgreSQL

```bash
docker compose up -d
```

### 4. Run Migrations

Linux/macOS:

```bash
alembic upgrade head
```

Windows PowerShell:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

### 5. Run The Application

Linux/macOS:

```bash
python src/app/main.py
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe src\app\main.py
```

## Development Checks 🧪

Run these before pushing meaningful changes:

```bash
python -m ruff check src tests migrations
python -m compileall -q src tests
python -m pytest -q
```

Integration tests use PostgreSQL/Testcontainers when relevant, so Docker may be required.

## Architecture 🏗️

Shop Manager follows a layered structure:

```text
src/app/
  config/          settings and environment config
  domain/          framework-independent domain concepts and enums
  application/     DTOs, services, use cases, validation
  infrastructure/  database models, sessions, integrations
  ui/              PySide6 widgets, dialogs, windows
```

Core rule: UI code stays thin. Business behavior and validation belong in application services;
SQLAlchemy models stay behind service boundaries.

## Roadmap 🗺️

Near-term implementation path:

1. Calendar view
   - browse tasks by date
   - create reminders directly for selected days
2. Manual recurring reminders
   - create standalone recurring task series from the UI
   - generate occurrences after save
3. Dashboard and reminder UI polish
   - improve the dashboard task layout and reminder ergonomics
4. Product category browsing polish
   - consider grouping the product table by assigned categories if filtering is not enough
   - consider category filters in order product/variant selection
5. Stock and shipment workflows

See [docs/dashboard_tasks_roadmap.md](docs/dashboard_tasks_roadmap.md) for the dashboard and
reminder design.

## Author 👤

Built by [Rubén Ruiz Pérez](https://github.com/rubenrzprz).
