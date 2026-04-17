# Shop Manager Agent Instructions

## Project Context

Shop Manager is a Python desktop application for store operations:

- products
- suppliers
- customers
- orders
- stock workflows later

The stack is:

- Python 3.12+
- PySide6
- PostgreSQL
- SQLAlchemy ORM
- Alembic migrations
- pytest
- Testcontainers for integration tests
- GitHub Actions CI

The application follows a layered architecture:

- `src/app/ui/`: PySide6 widgets and dialogs
- `src/app/application/`: services, use cases, DTOs
- `src/app/domain/`: framework-independent domain concepts/enums
- `src/app/infrastructure/`: database models, sessions, integrations

Strict rules:

- UI must not query SQLAlchemy models directly.
- UI may open sessions only to call application services.
- Business logic and validation belong in the application layer.
- DB persistence goes through SQLAlchemy models behind services.
- Keep changes vertical, small, and testable.
- Avoid premature abstractions.

## Workflow Acronyms

When the user types `git-clean`, do this:

- switch to `main`
- pull latest changes with fast-forward only
- fetch and prune remotes
- remove the merged local feature branch

When the user types `capcp`, do this:

- commit atomically
- push the branch
- create a PR

When the user types `capup`, do this:

- commit atomically
- push the branch
- update the existing PR body

For `capup`, update the PR body when relevant, especially when:

- behavior changed
- tests changed
- test counts changed
- scope changed
- Codex/GitHub review fixes added validation or user-visible behavior

## Branching

Use branch names with conventional prefixes:

- `feat/name`
- `fix/name`
- `docs/name`
- `ci/name`
- `refactor/name`

Before editing for a new task, switch to a new branch unless the user says otherwise.

## Commit Style

Use conventional commits:

- `feat(scope): summary`
- `fix(scope): summary`
- `docs(scope): summary`
- `ci(scope): summary`
- `refactor(scope): summary`

Prefer atomic commits grouped by logical boundary:

- application layer
- UI layer
- tests
- review fixes
- docs

Do not commit unrelated changes together.

## PR Body Style

Use the established PR body structure:

```md
## Goal

## Scope
This PR includes:

### 1. Area

### 2. Area

### 3. Tests

## Out of Scope

## Definition of Done

## Testing

## Notes / Design Decisions
```

If unsure, inspect the latest merged PR and match its style.

Keep PR bodies accurate after follow-up commits. Update test counts after local verification.

## Implemented Slices

The project currently has these completed vertical slices:

- Product Management v1
  - create products
  - list products
  - edit product core fields/default variant
  - activate/deactivate products
  - searchable supplier picker in product dialog
- Supplier Management v1
  - create suppliers
  - list suppliers
  - edit suppliers
- Customer Management v1
  - create customers
  - list customers
  - edit customers
- Order Management v1
  - create draft orders
  - list orders
  - customer picker
  - product variant picker
  - one order line in the v1 dialog
  - service-calculated totals
  - discount validation
  - deadline validation

## Current Design Decisions

- Product SKU format is `<PREFIX>-<PRODUCT_ID>-<VARIANT_INDEX>`.
- Products must have at least one variant.
- Product editing is limited to core fields and the first/default variant.
- Supplier/customer picker dialogs use one practical search box, not many field-specific filters.
- Order Management v1 intentionally supports one line in the UI to keep the slice small.
- Order editing is deferred.
- Multi-line order UI is deferred.
- Stock movements from orders are deferred.
- Shipment workflows are deferred.

## Likely Next Steps

When asked to propose the next logical step, consider this order:

1. Multi-line order creation UI
   - add/remove multiple order lines in `OrderDialog`
   - keep totals service-calculated
   - preserve validation in `CreateOrderService`
2. Draft order editing
   - edit only `DRAFT` orders
   - update customer/date/deadline/notes/lines
   - recalculate totals in service
3. Order status transitions
   - draft to confirmed
   - confirmed to in-progress/ready/completed/cancelled
   - enforce valid transitions in application layer
4. Stock movements
   - reduce stock when an order reaches the appropriate status
   - do not mix stock behavior into basic order create/list
5. Shipment workflows
   - create/update shipment info for orders

Prefer one small vertical slice per branch.

## Testing

Use these checks when relevant:

```bash
./.venv/bin/python -m compileall -q src tests
./.venv/bin/pytest tests/unit -q
./.venv/bin/pytest tests/integration -q
```

Integration tests require Docker/Testcontainers access. Ask for elevated permission when needed.

For focused work, run the specific integration test file first, then the full suite before pushing.

## GitHub CLI

Use `gh` for PR operations when requested:

- `gh pr create`
- `gh pr view`
- `gh api repos/<owner>/<repo>/issues/<number> --method PATCH -f body=...`

If `gh pr edit` fails due to GitHub GraphQL/project-card deprecation, update PR bodies through the REST issue endpoint with `gh api`.

## Current Repository Goal

Build Shop Manager incrementally as a clean layered desktop application for store operations.

The development style should favor:

- clean service boundaries
- deterministic validation errors before DB flush/commit
- UI that remains thin and service-driven
- integration tests for real DB behavior
- small, reviewable vertical slices

