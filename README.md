# Shop Manager

Desktop application for store operations focused on product management, order handling, and stock control.

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