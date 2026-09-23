# FitPro — Gym Membership & Classes

FitPro is the backend capstone project for Team Emerald Wave.

The application manages gym membership plans, member subscriptions,
payments, scheduled classes, class check-ins, membership expiry,
renewal reminders and live class-count updates.

## Team

- Nnamdi
- Stephanie

## Technology

- Python
- FastAPI
- SQLModel
- PostgreSQL
- Redis
- Firestore
- Docker
- Alembic
- Pytest
- GitHub Actions

## Setup

_To be completed and verified before final submission._

## Demo Accounts

_To be added when seed/demo data is implemented._

## ERD

_To be added from the approved Day 1 design._

## API Documentation

When the application is running:

`http://localhost:8000/docs`

## Authentication

FitPro uses JWT bearer authentication for people using the API.

The roles are:

- `MEMBER`
- `FRONT_DESK`
- `ADMIN`

## Membership Lifecycle

A registered member account is not the same as an active gym membership.

The membership lifecycle currently follows:

`PENDING_PAYMENT → ACTIVE → EXPIRED`

An active membership may temporarily become `FROZEN` and return to
`ACTIVE` when unfrozen.

Payment confirmation is what activates a pending membership.

## Payment Flow

### Staff payment

A front-desk or admin user records a successful offline payment.
FitPro derives the amount from the selected membership plan and
activates the membership in the same database transaction.

### Online payment

FitPro first creates a pending online payment with a unique reference.

A trusted payment-provider webhook later confirms the payment. The
webhook signature is verified using HMAC-SHA256. Provider event IDs
are stored in `processed_events` so duplicate deliveries do not
process the same event twice.

## The Hard Problem


---

The main concurrency problem in FitPro is making the daily membership
maintenance job safe to run more than once.

The job expires memberships whose end date has passed and creates
renewal reminders seven days before expiry.

A simple implementation could first check whether today's job has
already run and then perform the work. That is not safe under
concurrency because two requests could both check at the same time,
both see that no job-run record exists, and both perform the work.

FitPro instead uses the database as the final concurrency authority.

At the beginning of the job, the service attempts to insert:

`(job_name, run_date)`

into the `job_runs` table.

A unique constraint exists on these two columns.

The service calls `flush()` immediately after adding the row. This
causes PostgreSQL to enforce the unique constraint before the job
performs any membership or reminder work.

If two executions start for the same day, only one transaction can
claim that unique key. The winning transaction continues with
membership expiry and reminder creation. The other execution receives
the uniqueness conflict and returns `already_run` without repeating
the work.

The job-run claim, membership expiry updates and reminder inserts all
remain inside the same database transaction.

If any part of the job fails, the entire transaction rolls back,
including the job-run claim. This means the job can be retried safely
instead of becoming permanently marked as completed after a partial
failure.

The reminders table also has a unique constraint on:

`(membership_id, kind)`

which provides an additional database-level guarantee that the same
expiry reminder cannot be inserted twice.

We verified this design with both sequential and concurrent tests
against the real PostgreSQL test database.

## Why This Design

### Class Capacity Safety

FitPro does not check the class count and insert a check-in as two independent operations.

The Check-in Service starts a transaction and locks the target class row using `SELECT ... FOR UPDATE`.

Only after acquiring that lock does FitPro count the existing check-ins.

If capacity is still available, the new check-in is inserted and the transaction commits.

If another request is waiting for the same class, it only continues after the first transaction releases the lock. It then recounts attendance and rejects the check-in if the class is now full.

This prevents a class with capacity 12 from ever ending up with 13 valid check-ins because of simultaneous requests.._

## Flowcharts

## Daily Job Flow

```text
Scheduler
   |
   v
POST /api/v1/jobs/daily
   |
   v
Validate X-API-Key
   |
   v
BEGIN TRANSACTION
   |
   v
INSERT job_runs(job_name, run_date)
   |
   v
FLUSH
   |
   +---- duplicate unique key? ---- yes ----> ROLLBACK
   |                                      return already_run
   |
   no
   |
   v
Find ACTIVE memberships
where end_date <= today
   |
   v
Mark them EXPIRED
   |
   v
Find ACTIVE memberships
where end_date = today + 7 days
   |
   v
Create missing expiry reminders
   |
   v
COMMIT
   |
   v
return completed

### Daily Job

_To be added._

### Class Check-in / Capacity

_To be added._