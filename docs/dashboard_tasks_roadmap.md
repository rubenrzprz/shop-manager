# Dashboard And Task Reminders Roadmap

This document captures the planned dashboard and reminder system before implementation starts.

## Product Goal

The application should open on a dashboard that helps the store operator decide what needs
attention today. It should combine fast navigation shortcuts with a daily task/reminder area.

The task area should support:

- order follow-up reminders
- custom reminders linked to a specific order
- standalone reminders not linked to any order
- recurring reminders
- pending tasks for a selected day
- completed tasks for that same day
- calendar exploration for future and past days

## Dashboard Sections

Initial dashboard sections:

- Shortcuts
  - products
  - suppliers
  - customers
  - orders
  - settings
- Daily tasks
  - overdue tasks
  - pending tasks due today
  - completed tasks for today

Future dashboard sections may include stock alerts, recent orders, or shipment alerts.

## Task Model Direction

Use tasks as the persisted concept. "Daily events" should be the dashboard/calendar view of tasks
due on a selected date.

Implemented model split:

- `TaskSeries`
  - title
  - notes
  - recurrence type
  - recurrence interval
  - starts on
  - optional ends on
  - active flag
- `Task`
  - optional `task_series_id`
  - title snapshot
  - notes snapshot
  - due date
  - completed at

Standalone one-off reminders are plain `Task` rows without a `task_series_id`.

Generated recurring occurrences should keep title/notes snapshots so completed history remains
stable even if the series is edited later.

## Recurring Task Generation

Recurring tasks are generated within a bounded planning window instead of infinitely.

Implemented setting:

- `task_generation_horizon_days`
- default: `90`
- allowed range: `30` to `365`

Startup behavior:

1. Load application settings.
2. Compute `generation_until = today + task_generation_horizon_days`.
3. Find active task series.
4. Generate missing occurrences from today through `generation_until`.
5. Commit before loading the dashboard task list.

The generation service must be idempotent. Running it repeatedly must not create duplicate tasks.

Use a uniqueness rule equivalent to one generated task per `task_series_id` and `due_date`.

Daily, weekly, and monthly recurrence intervals are implemented. Creating and editing recurring
series from the UI remains a later workflow.

## Order Follow-Up Reminders

Order reminders should support two modes:

- custom one-off reminders linked to an order
- automatic follow-up reminders for active orders

Planned setting:

- `default_order_follow_up_days`
- likely default: `7`

Expected behavior:

- Active orders can receive periodic "check order status" reminders.
- Completing an automatic order follow-up schedules the next one if the order remains active.
- Completed and cancelled orders should stop producing automatic follow-up reminders.
- Custom order reminders should remain independent from default follow-up reminders.

## Calendar View

The calendar view should be built after task persistence exists.

Expected behavior:

- browse tasks by selected date
- see pending and completed tasks for that date
- create standalone reminders directly on a selected date
- create order-linked reminders when launched from an order context

Later options:

- reschedule tasks
- edit one occurrence
- edit future occurrences
- edit the whole recurrence series

## Suggested Slice Order

1. Dashboard shell
   - completed as the entry tab with quick actions and empty daily task sections
2. Product variant management
   - completed before deepening task work
   - variants can be added/edited/activated/deactivated after product creation
   - active products require at least one active variant
3. Product category grouping/filtering
   - category persistence and assignment are implemented
   - group/filter the product table by assigned categories later
   - consider category filters in order product/variant selection later
4. Basic tasks
   - completed with task table, DTOs, services, tests
   - completed create/list/complete/reopen one-off tasks
   - completed dashboard lists overdue, pending, and completed tasks
5. Task series generation
   - completed with task series table, recurrence fields, `task_generation_horizon_days`, and
     startup generation service
6. Order-bound tasks
   - optional `order_id`
   - create custom reminders from orders
7. Default order follow-up reminders
   - `default_order_follow_up_days`
   - automatic active-order reminders
8. Calendar task view
   - browse days
   - create reminders from selected date
