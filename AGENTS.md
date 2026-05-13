# Shop Manager Agent Instructions

## Project Context

Shop Manager is a Python desktop application for store operations:

- products
- suppliers
- customers
- orders
- dashboard reminders and tasks planned next
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
- check whether `AGENTS.md` or `README.md` should be updated for the branch
- push the branch
- create a PR

When the user types `capup`, do this:

- commit atomically
- check whether `AGENTS.md` or `README.md` should be updated for the branch
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

## Keeping This File Current

Treat `AGENTS.md` as living project memory, not a one-time snapshot.

Update this file when a change affects future agent behavior or project understanding, especially when:

- a new vertical slice is completed
- the likely next step changes
- a workflow acronym is added or changed
- PR/body/commit conventions change
- architecture rules change
- important design decisions are made
- testing requirements change
- repeated review feedback reveals a new project rule

Do not update it for every small implementation detail. Keep it concise and focused on durable context that will help a future session.

When doing `capcp` or `capup`, consider whether `AGENTS.md` or `README.md` needs a small update before pushing. If it does, include that update in an appropriate atomic commit.

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

- Dashboard Shell v1
  - dashboard is the first application tab
  - dashboard quick action buttons can open create product/supplier/customer/order flows without
    leaving the dashboard; navigation shortcuts still switch to their tabs
  - dashboard order activity opens order editing modally without leaving the dashboard
  - polished dashboard layout uses shortcut chips, an orders overview column, and a daily tasks rail
  - management tabs use shared softer page chrome, table styling, and primary action treatment
  - completed tasks render with a completed visual treatment in dashboard and calendar
  - orders overview shows active order counts, due-soon orders, and recent orders
  - daily task sections show overdue, pending today, and completed today tasks
  - create standalone one-off tasks
  - create standalone recurring reminders from the task dialog
  - create order-linked recurring reminders from the selected order reminder flow
  - edit recurring task occurrences, future occurrences, or a whole recurring series
  - assign task colors that render in dashboard cards and calendar blocks
  - create custom order-linked reminder tasks
  - generate recurring task occurrences from active task series
  - generate automatic active-order follow-up reminders
  - browse dashboard tasks by selected date
  - calendar tab shows a month grid with task markers/snippets by due date
  - create standalone reminders directly for the selected dashboard date
  - edit task occurrences from the dashboard and calendar selected-day panels
  - mark tasks complete and reopen completed tasks
- Product Management v1
  - create products
  - list products
  - search products by product/category/supplier/SKU/variant fields
  - edit product core fields/default variant
  - add/edit variants after product creation
  - activate/deactivate individual variants
  - activate/deactivate products
  - manage product categories
  - assign products to multiple categories
  - filter products by assigned category or uncategorized products
  - product list shows assigned categories
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
  - edit active orders
  - order status transitions
  - customer picker
  - product variant picker
  - multi-line order creation UI
  - order total preview in create dialog
  - service-calculated totals
  - discount validation
  - deadline validation
- Settings Management v1
  - application settings table
  - typed settings service
  - settings tab
  - strict order workflow toggle
  - configurable enabled order statuses
  - configurable recurring task generation horizon
  - explicit recalculation action for open automatic order follow-up reminders
- Spanish Localization v1
  - `app_language` setting
  - lightweight UI translation helper
  - English/Spanish labels for current navigation, pages, dialogs, and common UI messages

## Current Design Decisions

- Product SKU format is `<PREFIX>-<PRODUCT_ID>-<VARIANT_INDEX>`.
- Variant SKUs are currently immutable after creation. Consider a guarded "Change SKU" action near
  final development if real-world correction workflows need it, with uniqueness checks and warnings
  for variants used in historical orders/stock movements.
- Products must have at least one variant.
- Active products must have at least one active variant; deactivating the last active variant
  automatically makes the product inactive.
- Inactive products may have zero active variants, and adding/activating a variant does not
  automatically reactivate the product.
- Product categories are product-level only for now; a product can belong to multiple categories,
  and variants inherit their parent product categories.
- Inactive categories can remain assigned to existing products, but inactive categories should not
  be newly assigned to products.
- Supplier/customer picker dialogs use one practical search box, not many field-specific filters.
- Multi-line order creation uses a compact line composer plus an added-lines table.
- Order create/edit uses a tabbed dialog for details, lines, and totals.
- Create order dialog previews subtotal, discount, and total before save; persisted totals remain
  service-calculated.
- Active order editing supports updating customer/date/deadline/notes/discount/lines and
  recalculates totals in the application layer.
- Order line editing in the dialog is currently remove-and-readd; inline line editing is deferred.
- `strict_order_workflow_enabled` defaults to `False`; while disabled, active statuses (`DRAFT`,
  `CONFIRMED`, `IN_PROGRESS`, `READY`) are editable with the same rules.
- Strict order workflow uses status-specific editing rules instead of draft-like behavior.
- Application settings should be stored as typed application-level settings backed by a flexible
  key/value table, not as ad hoc UI constants or a generic user-editable key/value grid.
- The settings UI should expose known typed controls, not a generic user-editable key/value grid.
- `app_language` is a typed setting. The UI currently supports English (`en`) and Spanish (`es`).
- UI translation uses a lightweight dictionary helper keyed by source English text. Keep new UI text
  routed through the helper instead of hardcoding final labels directly in widgets.
- User-visible dates should use locale-aware display helpers: ISO-like `yyyy-MM-dd` in English and
  `dd/MM/yyyy` in Spanish.
- Service validation messages mostly remain final English strings for now. If deeper localization is
  needed, introduce message codes before translating application-layer errors broadly.
- Status-aware editing rules should be practical rather than forcing unnecessary status churn:
  `DRAFT`, `CONFIRMED`, and `IN_PROGRESS` allow full edits; `READY` allows deadline, discount,
  and notes only; `COMPLETED` and `CANCELLED` allow notes only.
- `enabled_order_statuses` is a typed setting. `DRAFT`, `COMPLETED`, and `CANCELLED` are required;
  `CONFIRMED`, `IN_PROGRESS`, and `READY` can be disabled for simpler client workflows.
- Advance/revert order actions use the configured enabled status path and skip disabled statuses.
- Disabling optional order statuses converts existing orders currently in those statuses to `DRAFT`
  after user confirmation so they do not remain stranded outside the configured workflow.
  `CANCELLED` remains outside the normal forward path; cancellation and recovery are explicit
  actions.
- Likely future settings include currency code, default order deadline days, requiring order
  deadlines, default discount type, manual unit price override, cancelled order reopen behavior,
  stock deduction status, allowing negative stock, and default customer type.
- By default, order status transitions follow
  `DRAFT -> CONFIRMED -> IN_PROGRESS -> READY -> COMPLETED`.
- Forward-path statuses can be reverted one step for accidental advances, including
  `COMPLETED -> READY`.
- Active non-completed statuses can transition to `CANCELLED`.
- `CANCELLED` can be recovered to `DRAFT` as an explicit accidental-cancellation recovery action.
- A fuller order workspace redesign is a future UI step: group customer/date fields, line table,
  line composer, totals/discount summary, and notes around order review/editing workflows.
- The desktop app opens maximized by default, and larger workflow dialogs should size themselves
  against the available screen rather than using small fixed dimensions.
- Keep broad UI polish centralized through shared stylesheet/page chrome helpers before doing
  page-specific redesigns.
- Stock movements from orders are deferred.
- Shipment workflows are deferred.

## Dashboard And Task Reminder Plan

- The app should eventually open on a dashboard, not directly on a management table.
- Dashboard v1 should include shortcuts to core areas and a daily task/reminder section.
- Persist tasks/reminders as application concepts; "daily events" are the dashboard/calendar view
  of tasks due on a selected day.
- Tasks support standalone reminders, custom order-linked reminders, recurring reminders, and
  automatic active-order follow-up reminders.
- Daily task sections should show overdue tasks, pending tasks for the selected day, and completed
  tasks for that same day.
- Dashboard task browsing by selected date is implemented with a date picker; standalone reminders
  created from the dashboard default to the selected date.
- Calendar tab browsing is implemented as a month grid with task snippets per day plus a selected
  day task panel; standalone reminders created from the calendar default to the selected day.
  Month cells use capped colored task blocks and a "+ N more" marker to avoid overcrowding.
- Standalone one-off `Task` rows are implemented with title, notes, due date, and completed
  timestamp.
- Custom order-linked `Task` rows use optional `order_id`; the order page can create a reminder
  for the selected order, and dashboard task labels show the order number when present.
- Recurring tasks use `TaskSeries` plus generated `Task` occurrences:
  - `TaskSeries`: optional order, title, notes, color, recurrence type/interval, monthly rule,
    optional monthly day, starts on, optional ends on, active flag
  - `Task`: optional series, title/notes/color snapshot, due date, completed timestamp
- Recurring occurrences are generated only through a configurable horizon, not forever.
- `task_generation_horizon_days` is implemented as a typed setting, default `90`, allowed range
  `30` to `365`, and exposed in the settings UI.
- On app startup, an idempotent generation service creates missing recurring task occurrences from
  today through `today + task_generation_horizon_days`.
- Generated recurring tasks should be unique per `task_series_id` and `due_date`.
- Recurring series currently support daily, weekly, and monthly intervals. Monthly recurrence can
  use first-day, same-day-as-start, specific-day, or last-day behavior.
- Creating standalone recurring series from the task dialog is implemented.
- Creating order-linked recurring series from the selected order reminder flow is implemented.
- Editing existing recurring series from a task occurrence is implemented for one occurrence, future
  occurrences, or the whole series. Future/series edits regenerate incomplete generated tasks;
  completed task history keeps its due dates.
- `default_order_follow_up_days` is implemented as a typed setting, default `7`, allowed range
  `1` to `365`, and exposed in the settings UI.
- Automatic order follow-up reminders are generated for active orders without an open automatic
  follow-up on startup, when draft orders are created, and when orders transition back into an
  active status. Completing one schedules the next follow-up when the order remains active;
  future-due follow-ups schedule the next reminder from the original due date rather than an early
  completion date.
  completed and cancelled orders stop producing automatic follow-ups and clear open automatic
  follow-ups while preserving custom order-linked reminders. Completed automatic follow-ups cannot
  be reopened once their order is completed or cancelled.
- Settings include an explicit recalculation action for open automatic follow-ups. It deletes only
  current open automatic follow-ups for active orders and recreates them from the current
  `default_order_follow_up_days`; completed follow-ups and custom reminders are preserved.
- See `docs/dashboard_tasks_roadmap.md` for the detailed implementation roadmap.

## Likely Next Steps

When asked to propose the next logical step, consider this order:

1. Dashboard-centered UX and tab UI refresh
   - open the app maximized by default
   - size large workflow dialogs relative to the available screen
   - keep dashboard quick actions and dashboard order edits in modal dialogs without switching tabs
   - refresh all tabs with shared softer UI patterns, spacing, action bars, and table polish
2. Recurring reminder polish
   - refine recurrence editing UX after real-world use
   - consider more advanced recurrence rules only when needed
3. Product category grouping polish
   - consider grouping the products page by category if filtering is not enough
   - consider category filters in product/variant pickers when order creation needs it
4. Localization polish
   - translate any newly added UI strings through the existing helper
   - consider service-layer message codes if application validation errors need full localization
   - consider broader formatting localization for currency/date display
5. Stock movements
   - reduce stock when an order reaches the appropriate status
   - do not mix stock behavior into basic order create/list
6. Shipment workflows
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
