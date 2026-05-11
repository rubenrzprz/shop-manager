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
- Orders overview
  - active order counts
  - due-soon orders
  - recent orders
- Daily tasks
  - overdue tasks
  - pending tasks due today
  - completed tasks for today

Future dashboard sections may include stock alerts or shipment alerts.

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
  - optional `order_id`
  - automatic order follow-up flag
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

Daily, weekly, and monthly recurrence intervals are implemented. Creating standalone recurring
series from the task dialog is implemented. Editing existing recurring series remains a later
workflow beyond that first manual recurring-reminder slice.

## Order Follow-Up Reminders

Order reminders support two modes:

- custom one-off reminders linked to an order
- automatic follow-up reminders for active orders

Implemented setting:

- `default_order_follow_up_days`
- default: `7`
- allowed range: `1` to `365`

Implemented behavior:

- Active orders can receive periodic "check order status" reminders.
- New draft orders receive an initial automatic follow-up during order creation.
- Orders recovered or transitioned back into active statuses receive an open follow-up when one is
  missing.
- Completing an automatic order follow-up schedules the next one if the order remains active.
- Completed and cancelled orders stop producing automatic follow-up reminders and clear open
  automatic follow-ups.
- Completed automatic follow-ups cannot be reopened after their order becomes completed or
  cancelled.
- Custom order reminders should remain independent from default follow-up reminders.

## Calendar View

The calendar task view is implemented with selected-date task browsing in the dashboard task area
and a dedicated Calendar tab with a month grid.

Implemented behavior:

- browse tasks by selected date
- see which month-grid days have tasks
- month-grid days show capped colored task blocks plus a "+ N more" marker instead of full
  unbounded task text
- see pending and completed tasks for that date
- create standalone reminders directly on a selected date
- create order-linked reminders when launched from an order context

Later options:

- customizable task colors or task categories for calendar/dashboard blocks
- reschedule tasks
- edit future recurring occurrences
- edit the whole recurrence series

## Manual Recurring Reminders

Manual recurring reminders let the operator create standalone `TaskSeries` rows from the task
dialog.

Implemented v1 behavior:

- create a recurring reminder with title, notes, recurrence type, interval, start date, and
  optional end date
- generate missing occurrences immediately after saving through the configured
  `task_generation_horizon_days`
- keep generated occurrence title/notes as snapshots
- defer editing existing series until after creation is useful in day-to-day use

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
   - completed with optional `order_id` and custom reminders from orders
7. Default order follow-up reminders
   - completed with `default_order_follow_up_days` and automatic active-order reminders
8. Calendar task view
   - completed with dashboard selected-date browsing
   - completed with a Calendar tab month grid showing days with tasks
   - completed with standalone reminders defaulting to the selected date
9. Manual recurring reminders
   - completed with standalone recurring reminders from the task dialog
   - completed occurrence generation after save
10. Dashboard/UI polish
   - completed with shortcut chips, an orders overview column, and a daily tasks rail
   - continue task/reminder ergonomics after real-world use
