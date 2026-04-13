# Shop Manager

Desktop application for store operations focused on product management, order handling, and stock control.

## Local Setup

After cloning the repository, create a virtual environment, install dependencies, configure the database environment, and run the Alembic migrations.

### 1. Create the virtual environment and install dependencies

This project requires Python 3.12 or newer.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

If you also want development tools:

```bash
python -m pip install -r requirements-dev.txt
```

### 2. Configure `.env`

Copy the example file:

```bash
cp .env.example .env
```

Default example:

```env
APP_ENV=development

POSTGRES_DB=shop_manager
POSTGRES_USER=shop_user
POSTGRES_PASSWORD=shop_pass
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

DATABASE_URL=postgresql+psycopg://shop_user:shop_pass@localhost:5432/shop_manager
```

If you already have an existing PostgreSQL database with different credentials, update both the `POSTGRES_*` values and `DATABASE_URL` so they match the real database.

### 3. Start PostgreSQL with Docker Compose

```bash
docker compose up -d
```

### 4. Upgrade Alembic

Run the database migrations before starting the application:

```bash
alembic upgrade head
```

If you are not activating the virtual environment, you can run:

```bash
./.venv/bin/alembic upgrade head
```

### 5. Run the application

```bash
python src/app/main.py
```

## Goal

Build a Windows desktop application with a clear separation between UI, business logic, and data persistence, designed to scale from an initial local setup to a multi-workstation environment.

## Initial Scope

- Product management
- Order management
- Basic stock tracking

## Planned Stack

- Python
- PySide6
- PostgreSQL
- SQLAlchemy
- Alembic
- pytest

## Project Structure

src/app/
  config/          # settings and environment config
  domain/          # business entities and core rules
  application/     # use cases and application services
  infrastructure/  # database, repositories, external integrations
  ui/              # desktop interface

## Current Status

Initial repository setup in progress.
