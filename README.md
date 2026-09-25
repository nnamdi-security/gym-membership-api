# FitPro — Gym Membership & Classes API |  [![wakatime](https://wakatime.com/badge/user/55f2e7d8-e681-415e-ba87-93dc727f5023/project/9f3b2bb3-b709-4faf-b0f0-5967bf8e3a23.svg)](https://wakatime.com/badge/user/55f2e7d8-e681-415e-ba87-93dc727f5023/project/9f3b2bb3-b709-4faf-b0f0-5967bf8e3a23)

FitPro is a backend API for managing gym members, membership plans, payments, scheduled classes, check-ins, renewal reminders, and operational jobs.

The project was built as a backend-development capstone by **Emerald Wave** using FastAPI, SQLModel, PostgreSQL, Redis, Alembic, Docker, and pytest.

The design focuses on three things:

1. clear separation of responsibilities;
2. transactional correctness for business-critical operations;
3. safe handling of concurrency, retries, and duplicate requests.

---

## Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. Core Features](#2-core-features)
- [3. Technology Stack](#3-technology-stack)
- [4. Architecture](#4-architecture)
- [5. Project Structure](#5-project-structure)
- [6. Environment Setup](#6-environment-setup)
- [7. Database Setup and Migrations](#7-database-setup-and-migrations)
- [8. Demo Seed Data](#8-demo-seed-data)
- [9. Demo Accounts](#9-demo-accounts)
- [10. API Documentation](#10-api-documentation)
- [11. Core Business Flows](#11-core-business-flows)
- [12. Database Design / ERD](#12-database-design--erd)
- [13. Authentication and Authorization](#13-authentication-and-authorization)
- [14. Membership Lifecycle](#14-membership-lifecycle)
- [15. Payments](#15-payments)
- [16. Payment Webhooks](#16-payment-webhooks)
- [17. Class Capacity and Concurrency](#17-class-capacity-and-concurrency)
- [18. Daily Job and Idempotency](#18-daily-job-and-idempotency)
- [19. Redis and Firestore](#19-redis-and-firestore)
- [20. Testing Strategy](#20-testing-strategy)
- [21. Running the Test Suite](#21-running-the-test-suite)
- [22. Postman Acceptance Checklist](#22-postman-acceptance-checklist)
- [23. Hard Problem](#23-hard-problem)
- [24. Why This Design](#24-why-this-design)
- [25. Known Limitations and Future Improvements](#25-known-limitations-and-future-improvements)
- [26. Defense Guide](#26-defense-guide)
- [27. Quick Viva Questions and Answers](#27-quick-viva-questions-and-answers)

---

# 1. Project Overview

FitPro manages the main backend operations of a gym.

A user can create an account, but having the `MEMBER` role does not automatically mean the user currently has access to the gym. Access is controlled separately through membership records.

A typical flow is:

```text
User registers
    ↓
User selects a plan
    ↓
Membership becomes PENDING_PAYMENT
    ↓
Payment succeeds
    ↓
Membership becomes ACTIVE
    ↓
Member can check into scheduled classes
```

Administrative and front-desk users have separate permissions for plan management, class management, staff-recorded payments, member check-in assistance, and operational views.

FitPro also includes:

- idempotent payment-webhook processing;
- class-capacity protection under concurrent requests;
- daily membership-expiry and reminder processing;
- optional Redis and Firestore integration for live/read projections.

---

# 2. Core Features

FitPro currently supports:

- user registration and login;
- JWT authentication;
- role-based authorization;
- membership-plan CRUD;
- pending, active, frozen, expired, and cancelled membership states;
- staff-recorded payments;
- online-payment initialization;
- signed payment webhooks;
- duplicate-webhook protection;
- scheduled gym classes;
- member self check-in;
- front-desk/admin check-in support;
- duplicate check-in protection;
- class-capacity enforcement;
- class-board counts;
- daily membership-expiry processing;
- seven-day expiry reminders;
- idempotent daily jobs;
- Redis connectivity and event infrastructure;
- Firestore read projections;
- Swagger/OpenAPI documentation;
- automated tests using a dedicated PostgreSQL test database.

---

# 3. Technology Stack

| Technology | Purpose |
| --- | --- |
| Python 3.12 | Application language |
| FastAPI | HTTP API framework |
| SQLModel | Models and ORM integration |
| PostgreSQL 16 | Authoritative relational database |
| Alembic | Database migrations |
| Redis 7 | Transient/live event infrastructure |
| Firestore | Optional read projection |
| Pydantic | Request/response validation |
| python-jose | JWT handling |
| pwdlib / Argon2 | Password hashing |
| pytest | Automated testing |
| Docker Compose | Local development environment |
| Ruff | Formatting and linting |
| GitHub Actions | Continuous integration |

---

# 4. Architecture

FitPro uses a layered architecture:

```text
Client / Postman / Swagger
          |
          v
     FastAPI Router
          |
          v
      Service Layer
          |
          v
    Repository Layer
          |
          v
       PostgreSQL
```

Additional infrastructure is connected around the core flow:

```text
                         ┌─────────────┐
                         │  Firestore  │
                         │ projection  │
                         └──────▲──────┘
                                |
Client → Router → Service → PostgreSQL
                                |
                         ┌──────▼──────┐
                         │    Redis    │
                         │ live events │
                         └─────────────┘
```


## System Architecture

The following diagram illustrates the architecture of the FitPro API, including the application layers, external services, and data stores.

![FitPro System Architecture](docs/images/FitPro-full-system-AD.png)

### Router layer

Routers are responsible for HTTP concerns:

- routes;
- request validation;
- dependency injection;
- status codes;
- response models;
- authentication/authorization dependencies.

### Service layer

Services contain business rules.

Examples:

- `PaymentService`
- `MembershipService`
- `CheckinService`
- `GymClassService`
- `DailyJobService`
- `WebhookService`

### Repository layer

Repositories isolate database access.

Examples:

- `UserRepository`
- `PlanRepository`
- `MembershipRepository`
- `PaymentRepository`
- `GymClassRepository`
- `CheckinRepository`
- `ReminderRepository`
- `JobRunRepository`
- `ProcessedEventRepository`

This keeps SQLModel queries out of the router and reduces coupling between HTTP handling and persistence.

---

# 5. Project Structure

A simplified structure is:

```text
fitpro/
├── alembic/
├── app/
│   ├── api/
│   │   ├── dependencies/
│   │   └── v1/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── scripts/
│   └── seed_demo.py
├── tests/
├── alembic.ini
├── docker-compose.yml
├── requirements.txt
├── README.md
└── LOG.md
```

---

# 6. Environment Setup

## 6.1 Clone the repository

```bash
git clone https://github.com/nnamdi-security/gym-membership-api.git
cd fitpro
```

## 6.2 Create environment file

Copy the example file:

```bash
cp .env.example .env
```

Typical development variables include:

```env
APP_ENV=development

DATABASE_URL=postgresql+psycopg://fitpro:fitpro@postgres:5432/fitpro
REDIS_URL=redis://redis:6379/0

JWT_SECRET=change-me
JWT_ALGORITHM=HS256

DAILY_JOB_API_KEY=change-me
DEMO_SEED_PASSWORD=FitProDemo123!

FIRESTORE_ENABLED=false
FIRESTORE_PROJECT_ID=
```

Do not commit the real `.env` file.

## 6.3 Start the application

```bash
docker compose up -d --build
```

Check services:

```bash
docker compose ps
```

View API logs:

```bash
docker compose logs api -f
```

The API runs at:

```text
http://localhost:8000
```

---

# 7. Database Setup and Migrations

Apply migrations:

```bash
docker compose exec api alembic upgrade head
```

Check the current migration:

```bash
docker compose exec api alembic current
```

Migration history:

```bash
docker compose exec api alembic history
```

PostgreSQL is the source of truth for users, plans, memberships, payments, classes, check-ins, reminders, job-run claims, and processed webhook events.

---

# 8. Demo Seed Data

FitPro includes a repeatable development seed script.

Run:

```bash
docker compose exec api python scripts/seed_demo.py
```

The script creates admin, front-desk, active-member, pending-payment-member, frozen-member, demo plans, and future gym classes.

The seed script is designed to be safe to run again without creating duplicate demo users and resets demo passwords so the environment remains predictable.

---

# 9. Demo Accounts

Default local-development password:

```text
FitProDemo123!
```

| Purpose | Email | Role / State |
| --- | --- | --- |
| Admin | `admin@fitpro.demo` | ADMIN |
| Front Desk | `frontdesk@fitpro.demo` | FRONT_DESK |
| Active Member | `member@fitpro.demo` | MEMBER + ACTIVE membership |
| Pending Member | `pending@fitpro.demo` | MEMBER + PENDING_PAYMENT membership |
| Frozen Member | `frozen@fitpro.demo` | MEMBER + FROZEN membership |

These accounts are for local demonstration only.

---

# 10. API Documentation

Swagger UI:

```text
http://localhost:8000/docs
```

OpenAPI JSON:

```text
http://localhost:8000/openapi.json
```

API prefix:

```text
/api/v1
```

Examples:

```text
POST /api/v1/auth/login
GET  /api/v1/plans
POST /api/v1/payments/staff
GET  /api/v1/classes
POST /api/v1/checkins
POST /api/v1/jobs/daily
```

---

# 11. Core Business Flows

## 11.1 Registration and membership

```text
Register account
      |
      v
User role = MEMBER
      |
      v
Select plan
      |
      v
PENDING_PAYMENT
      |
      v
Payment succeeds
      |
      v
ACTIVE membership
```

## 11.2 Staff-recorded payment

```text
Front Desk / Admin
        |
        v
POST /payments/staff
        |
        v
Load pending membership
        |
        v
Load selected plan
        |
        v
Derive amount from plan
        |
        v
Create SUCCEEDED payment
        |
        v
Activate membership
        |
        v
Single transaction commit
```

## 11.3 Online payment

```text
Member
  |
  v
Initialize payment
  |
  v
Create PENDING ONLINE payment
  |
  v
Provider checkout
  |
  v
Signed webhook
  |
  v
Verify payment details
  |
  v
Payment SUCCEEDED
  |
  v
Membership ACTIVE
```

## 11.4 Check-in

```text
Member requests check-in
        |
        v
Lock class row
        |
        v
Verify future class
        |
        v
Verify member
        |
        v
Verify ACTIVE membership
        |
        v
Verify entitlement dates
        |
        v
Reject duplicate
        |
        v
Count check-ins
        |
        v
Compare to capacity
        |
        v
Insert check-in
```

---

# 12. Database Design / ERD

Main entities:

```mermaid
erDiagram
    USERS ||--o{ MEMBERSHIPS : has
    PLANS ||--o{ MEMBERSHIPS : selected_by
    MEMBERSHIPS ||--o{ PAYMENTS : receives
    USERS ||--o{ CHECKINS : performs
    CLASSES ||--o{ CHECKINS : contains
    MEMBERSHIPS ||--o{ REMINDERS : generates

    USERS {
        int id PK
        string email UK
        string password_hash
        string role
    }

    PLANS {
        int id PK
        string name
        decimal price
        int period_days
    }

    MEMBERSHIPS {
        int id PK
        int member_id FK
        int plan_id FK
        string status
        date start_date
        date end_date
        date frozen_on
    }

    PAYMENTS {
        int id PK
        int membership_id FK
        decimal amount
        string status
        string method
        string reference UK
        string provider
        int recorded_by
        datetime recorded_at
        datetime paid_at
    }

    CLASSES {
        int id PK
        string name
        int capacity
        datetime starts_at
    }

    CHECKINS {
        int id PK
        int class_id FK
        int member_id FK
        datetime checked_in_at
    }

    REMINDERS {
        int id PK
        int membership_id FK
        string kind
    }

    JOB_RUNS {
        int id PK
        string job_name
        date run_date
    }

    PROCESSED_EVENTS {
        int id PK
        string event_id UK
    }
```

Important constraints:

```text
users.email UNIQUE
checkins(class_id, member_id) UNIQUE
job_runs(job_name, run_date) UNIQUE
processed_events.event_id UNIQUE
reminders(membership_id, kind) UNIQUE
```

---

# 13. Authentication and Authorization

FitPro uses JWT bearer authentication.

Passwords are hashed with Argon2 through `pwdlib`; plain-text passwords are never stored.

The token stores the user ID in the `sub` claim. The API then loads the current user from PostgreSQL so the database remains authoritative for user existence and role changes.

Public registration always creates `UserRole.MEMBER`; the client cannot self-register as an admin or front-desk user.

`401 Unauthorized` means authentication failed. `403 Forbidden` means authentication succeeded but the user lacks permission.

---

# 14. Membership Lifecycle

Membership statuses:

```text
PENDING_PAYMENT
ACTIVE
FROZEN
EXPIRED
CANCELLED
```

`PENDING_PAYMENT` has no active entitlement dates yet. `ACTIVE` means payment succeeded and access is valid. `FROZEN` pauses access and stores `frozen_on`. On unfreeze, the end date is extended by the frozen duration. The daily job marks active memberships expired when `end_date <= today`. `CANCELLED` is no longer active.

The end date is treated as exclusive.

---

# 15. Payments

Payment statuses:

```text
PENDING
SUCCEEDED
FAILED
```

Payment methods:

```text
CASH
TRANSFER
CARD
ONLINE
```

The API derives payment amount from the selected plan rather than accepting an arbitrary amount from the client.

A staff-recorded payment verifies the membership is awaiting payment, rejects `ONLINE` as a manual method, derives the price from the plan, creates a successful payment, activates the membership, and commits both operations atomically.

---

# 16. Payment Webhooks

Endpoint:

```text
POST /api/v1/webhooks/payment
```

The webhook uses an HMAC SHA-256 signature over the exact raw request body via `X-Signature`.

Flow:

```text
Receive request
      |
      v
Read raw body
      |
      v
Verify HMAC
      |
      v
Parse JSON
      |
      v
Check event_id
      |
      v
Find/lock payment
      |
      v
Validate amount/currency/reference
      |
      v
Update payment
      |
      v
Activate membership
      |
      v
Record processed event
      |
      v
Commit
```

Provider retries are made safe using `processed_events.event_id UNIQUE`.

---

# 17. Class Capacity and Concurrency

A class can have one slot left while two check-in requests arrive at the same time. A naïve count-then-insert flow can overbook.

FitPro locks the class row first using:

```text
SELECT ... FOR UPDATE
```

Then it counts current check-ins and decides whether a slot remains. Competing requests serialize around the locked class row.

The authoritative attendance count is `COUNT(checkins)` rather than a separate mutable counter on the class row.

---

# 18. Daily Job and Idempotency

The daily job expires overdue memberships and creates seven-day reminders.

Endpoint:

```text
POST /api/v1/jobs/daily
```

It uses `X-API-Key` rather than user JWT authentication.

The job first inserts `(job_name, run_date)` into `job_runs`, which has a unique constraint, then calls `flush()` before business work. PostgreSQL therefore decides which concurrent execution owns that day's run. The claim and maintenance work remain in one transaction, so failure rolls everything back and allows retry.

---

# 19. Redis and Firestore

```text
PostgreSQL = business truth
Redis      = transient/live infrastructure
Firestore  = read projection
```

Redis is used for transient/live concerns such as pub/sub and event fanout. Firestore is a read-oriented projection and is not authoritative.

Projection happens after PostgreSQL commit so a Firestore or Redis outage does not invalidate a valid business transaction.

Firestore is optional locally; no-op implementations allow the core API to run without cloud credentials.

---

# 20. Testing Strategy

FitPro uses unit, repository, API, integration, and concurrency tests.

Concurrency tests use real PostgreSQL because fakes cannot reproduce row locks, unique-constraint blocking, or transaction isolation correctly.

The class-capacity test uses threads, separate sessions, and a synchronization barrier to prove that only one contender gets the final slot.

The daily-job concurrency test proves one execution completes, one returns `already_run`, and only one job-run claim/reminder persists.

---

# 21. Running the Test Suite

Create/reset the test database:

```bash
docker compose exec postgres dropdb -U fitpro --if-exists fitpro_test
docker compose exec postgres createdb -U fitpro fitpro_test
```

Apply migrations:

```bash
docker compose exec -e APP_ENV=test -e DATABASE_URL=postgresql+psycopg://fitpro:fitpro@postgres:5432/fitpro_test api alembic upgrade head
```

Run all tests:

```bash
docker compose exec -e APP_ENV=test -e DATABASE_URL=postgresql+psycopg://fitpro:fitpro@postgres:5432/fitpro_test api pytest -v
```

At final stabilization, the full suite passes:

```text
223 passed
```

Run Ruff:

```bash
docker compose exec api ruff format .
docker compose exec api ruff check .
```

---

# 22. Postman Acceptance Checklist

| Area | Test | Expected |
| --- | --- | --- |
| Auth | Login | 200 |
| Auth | Invalid token | 401 |
| Auth | Member calls admin route | 403 |
| Plans | Admin creates plan | Success |
| Plans | Member creates plan | 403 |
| Membership | Pending membership | PENDING_PAYMENT |
| Payment | Staff records payment | 201 |
| Payment | Membership activates | ACTIVE |
| Payment | Pay same membership twice | 409 |
| Payment | Member uses staff route | 403 |
| Online payment | Initialize | 201 + PENDING payment |
| Classes | Admin creates class | Success |
| Check-in | Active member | 201 |
| Check-in | Duplicate | 409 |
| Check-in | Full class | 409 |
| Check-in | Inactive membership | 403 |
| Daily job | Correct API key | 200 |
| Daily job | Same-day rerun | already_run |
| Daily job | Wrong API key | 401 |

---

# 23. Hard Problem

## Hard Problem 1: Class Capacity

Checking `COUNT(checkins) < capacity` without locking is vulnerable to a race condition. FitPro solves this with `SELECT ... FOR UPDATE` on the class row before the count-and-insert sequence.

## Hard Problem 2: Daily Job Idempotency

A read-before-write check is also vulnerable to concurrent execution. FitPro instead inserts `(job_name, run_date)` into a table with a unique constraint and immediately calls `flush()`. Only one transaction can claim the day's execution. The claim and maintenance work remain in one transaction so failures roll back safely.

---

# 24. Why This Design

FastAPI was chosen for typed request validation, dependency injection, OpenAPI/Swagger documentation, and clean Python integration.

PostgreSQL was chosen because the project depends on transactions, foreign keys, unique constraints, and row-level locking.

SQLModel combines ORM behavior with typed models and integrates naturally with FastAPI.

Repositories isolate persistence behavior. Services hold business rules. Classes are used where multiple related operations share the same dependencies. Dependency injection makes infrastructure replaceable in tests.

Classes are not always better; small stateless logic may be simpler as plain functions.

---

# 25. Known Limitations and Future Improvements

Possible future improvements include:

- real payment-provider integration;
- production-grade Firestore retry/reconciliation;
- scheduler integration;
- richer SSE/live-client support;
- refresh tokens;
- rate limiting;
- recurring class templates;
- class cancellation/rescheduling;
- attendance analytics;
- audit logging;
- observability and metrics;
- cloud IAM/service-to-service authentication.

These were intentionally deprioritized in favor of core transactional correctness for the capstone.

---

# 26. Defense Guide

## 26.1 Architecture

FitPro uses:

```text
Router → Service → Repository → PostgreSQL
```

The router handles HTTP concerns, the service handles business rules, and the repository handles persistence.

## 26.2 Why did we use classes?

We used classes where related methods share dependencies. For example, `PaymentService` needs a session, repositories, a payment provider, and an activity projector. A service object receives these once and reuses them across methods.

Alternative approaches include plain functions, module-level functions, functional programming, static methods, or direct route logic. Classes are not automatically better; they are useful here because of shared dependencies and grouped responsibilities.

## 26.3 Authentication

Passwords are hashed with Argon2. JWT `sub` stores the user ID. After decoding, the API loads the user from PostgreSQL so role changes and deletions take effect.

`401` means authentication failed. `403` means the user is authenticated but not allowed to perform the action.

## 26.4 Why MEMBER does not mean active membership

`UserRole.MEMBER` describes the account's authorization role. Actual gym access depends on the membership state, which can be pending, active, frozen, expired, or cancelled.

## 26.5 Why payment amount comes from the plan

The server derives the amount from the plan to prevent client-side tampering.

## 26.6 Why payment and membership activation are atomic

A successful payment and membership activation belong to one business operation. Committing one without the other would create inconsistent state.

## 26.7 Why HMAC for webhooks

HMAC verifies that the sender knows the shared secret. The raw request body is used because signatures must be calculated over the exact signed bytes.

## 26.8 Why processed events?

Payment providers retry webhooks. Storing a unique event ID makes repeated delivery safe and prevents repeated side effects.

## 26.9 Why `SELECT ... FOR UPDATE`?

It serializes competing check-ins around the same class so two users cannot take the same final slot.

## 26.10 Why the daily job uses a unique claim

The database uniquely identifies a run by `(job_name, run_date)`, so concurrent executions cannot both own the same day's job.

## 26.11 Why `flush()`?

`flush()` sends pending SQL to PostgreSQL and triggers constraint checks while the transaction remains open and can still roll back.

## 26.12 Why Redis?

Redis is useful for transient pub/sub and live event delivery, not business truth.

## 26.13 Why Firestore?

Firestore is useful for denormalized read projections. It can be rebuilt from PostgreSQL and should not control whether a business transaction succeeds.

## 26.14 Why a separate test database?

Tests create and delete data. A dedicated `fitpro_test` database protects development/demo data and allows destructive cleanup safely.

## 26.15 Why real PostgreSQL in concurrency tests?

Fakes cannot reproduce row locks, transaction isolation, or unique-constraint blocking accurately.

## 26.16 Unit vs integration vs API tests

A unit test checks a small component in isolation. An integration test checks components against real infrastructure. An API test verifies externally visible HTTP behavior.

## 26.17 What would we improve with more time?

We would improve operational infrastructure rather than replace the core design: real provider integration, projection retries, observability, richer live updates, recurring classes, and audit/reporting capabilities.

---

# 27. Quick Viva Questions and Answers

### Why FastAPI?
Because it provides typed validation, dependency injection, OpenAPI documentation, and works cleanly with Python type hints.

### Why PostgreSQL?
Because FitPro depends on transactions, relational constraints, unique constraints, and row-level locking.

### Why SQLModel?
Because it combines ORM behavior with typed models and integrates naturally with FastAPI.

### Why use a repository?
To keep database access separate from business logic.

### Why use a service layer?
To keep business rules separate from HTTP and persistence concerns.

### Why use classes?
Because some components have several related methods that share the same dependencies.

### Are classes always better?
No. Stateless logic can often be simpler as plain functions.

### Why dependency injection?
It makes components easier to replace and test.

### Why is MEMBER different from ACTIVE membership?
MEMBER is an account role. ACTIVE is a business entitlement state.

### Why not accept payment amount from the client?
Because the client could tamper with it. The server derives the amount from the plan.

### Why HMAC?
To verify that the webhook came from a party that knows the shared secret.

### Why use the raw webhook body?
Because HMAC must be calculated over exactly the bytes that were signed.

### Why store processed webhook IDs?
To make provider retries idempotent.

### Why lock the class row?
To prevent two concurrent requests from taking the same final class slot.

### Why not store `current_attendees` on the class row?
Because `COUNT(checkins)` is the authoritative attendance count and avoids a second mutable source of truth.

### Why use a unique job-run constraint?
To guarantee that only one execution can claim the same daily job and date.

### Why `flush()`?
To force PostgreSQL to check the unique constraint before work begins while still allowing rollback.

### Why return `already_run` instead of an error?
Because retrying an idempotent operation after it already succeeded is not a business failure.

### Why Redis?
For transient live/event infrastructure, not authoritative business state.

### Why Firestore?
For denormalized read projections that can be rebuilt from PostgreSQL.

### Why can Firestore fail without failing the check-in?
Because PostgreSQL is authoritative and the projection is secondary.

### Why a separate test database?
To protect development data and allow destructive test cleanup safely.

### How did we test the hardest concurrency issue?
With real PostgreSQL, separate sessions, threads, and synchronization so two requests competed for the final class slot.

### What is the main source of truth?
PostgreSQL.

### What is the main design principle of FitPro?
Keep business-critical state transactional and authoritative in PostgreSQL while external/live infrastructure remains replaceable and secondary.

---

# Team Development Log

Development history, challenges, lessons, and contribution notes are maintained separately in `LOG.md`.

The README explains how the system works. The LOG records how the team built it.

---

# Final Notes

Before submission or defense:

```bash
docker compose up -d
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed_demo.py
```

Run quality checks:

```bash
docker compose exec api ruff format .
docker compose exec api ruff check .
```

Run the full test suite against `fitpro_test`, then verify the main flows externally through Swagger or Postman.

The most important areas both team members should be able to explain are:

```text
JWT + RBAC
membership lifecycle
server-derived payment amount
webhook HMAC + idempotency
class-capacity row locking
daily-job unique claim + flush
PostgreSQL as source of truth
```
