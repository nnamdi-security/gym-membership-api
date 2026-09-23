# FitPro Development Log

Team: Emerald Wave  
Project: FitPro — Gym Membership & Classes

---

## Day 1 — Project Design and ERD

### What we did

We studied the FitPro project brief and broke the system into its main business entities.

We designed the initial ERD with the following PostgreSQL tables:

- users
- plans
- memberships
- classes
- checkins
- payments
- reminders
- job_runs
- processed_events

We identified the main relationships between users, plans, memberships, classes and check-ins.

We also identified the important database constraints required by the brief:

- `users.email` must be unique.
- `checkins(class_id, member_id)` must be unique so one member cannot check into the same class twice.
- `job_runs(job_name, run_date)` must be unique so the daily job can safely run more than once.
- `processed_events.event_id` must be unique so the same webhook event cannot be processed twice.
- memberships need an index on `(end_date, status)`.
- classes need an index on `starts_at`.

We discussed the difference between a user account and a membership, and why check-ins need their own table because members and classes have a many-to-many relationship.

We prepared the ERD and the required handwritten design for instructor review.

The instructor approved the handwritten design before we started coding.

### What broke / challenges

There was no coding failure on Day 1, but the main challenge was understanding the difference between the business entities.

At first, concepts such as a member, membership, plan and class could easily have been combined into fewer tables, but doing that would have made the system harder to manage.

We also had to think carefully about the hard problems before implementation:

- making the scheduled daily job idempotent;
- preventing class capacity from being exceeded when multiple members check in at the same time.

### What we learnt

We learnt that an ERD is not just a diagram of tables. It should also reflect the rules the application must guarantee.

We learnt why important rules should be backed by database constraints instead of relying only on Python checks.

We also learnt the difference between:

- one-to-many relationships;
- many-to-many relationships;
- join tables;
- operational/idempotency tables such as `job_runs` and `processed_events`.

We understood that PostgreSQL will be the source of truth, while Firestore will later hold read-oriented/live information such as class board counts.

### What is next

Day 2 will set up the actual backend project:

- FastAPI application structure;
- configuration;
- Docker;
- PostgreSQL;
- Redis;
- Alembic;
- first migration;
- pytest;
- GitHub Actions CI.

### Who did what

Nnamdi:
- Led the walkthrough of the brief and proposed the first draft of the nine-table ERD.
- Identified the unique constraints and indexes needed to back the daily-job and webhook idempotency rules.

Stephanie:
- Reviewed the ERD table by table and worked through the relationships (foreign keys, one-to-many vs many-to-many) to confirm the design made sense.
- Helped reason through why check-ins needed their own join table instead of being folded into memberships or classes.

Shared:
- Reviewed the ERD and project requirements together.
- Discussed the system entities and relationships.
- Prepared the handwritten design and presented it for instructor sign-off.

---

## Day 2 — Backend Foundation, Docker, Database and CI

### What we did

We created the FastAPI project structure using separate folders for:

- API routers;
- core configuration;
- database setup;
- models;
- schemas;
- repositories;
- services;
- tests.

We configured environment-based settings using `pydantic-settings`.

We added a FastAPI health endpoint and an initial pytest smoke test.

We containerized the application with Docker and Docker Compose.

The local development environment now includes three services:

- FastAPI API;
- PostgreSQL;
- Redis.

We configured Docker health checks so the API waits until PostgreSQL and Redis are actually ready.

We added SQLModel database session handling and verified that the Python application could connect to PostgreSQL by executing `SELECT 1`.

We configured Alembic for database migrations.

We converted the approved ERD into SQLModel models for:

- users;
- plans;
- memberships;
- classes;
- checkins;
- payments;
- reminders;
- job_runs;
- processed_events.

We generated and applied the first Alembic migration.

We added GitHub Actions CI so every push and pull request:

- checks out the project;
- installs Python;
- installs dependencies;
- starts PostgreSQL and Redis;
- runs Alembic migrations;
- runs pytest.

### What broke / challenges

The first Alembic setup had several issues.

`alembic.ini` was empty, so Alembic returned:

`No 'script location' key found in configuration`.

After fixing that, Alembic still tried to use the placeholder SQLAlchemy URL:

`driver://user:pass@localhost/dbname`

which caused:

`Can't load plugin: sqlalchemy.dialects:driver`.

We fixed `alembic/env.py` so it reads the real database URL from the application settings.

We also found an enum downgrade problem.

After downgrading the first migration, PostgreSQL removed the tables but left enum types such as:

- `userrole`;
- `membershipstatus`;
- `reminderkind`.

The next upgrade failed with:

`type "userrole" already exists`.

We corrected the migration downgrade so it explicitly removes PostgreSQL enum types.

### What we learnt

We learnt the difference between:

- Docker image;
- Docker container;
- Docker Compose service;
- Docker volume;
- Docker health check.

We learnt why Docker services communicate using service names such as `postgres` and `redis` instead of `localhost`.

We learnt that the API application and Alembic should use the same environment-based database configuration.

We learnt that Alembic autogenerate must always be reviewed before execution.

We also learnt that PostgreSQL enum types are independent schema objects and may need to be explicitly removed during downgrade.

We learnt why tests need a dedicated `fitpro_test` database rather than using the development database.

### What is next

Day 3 will implement authentication and authorization:

- password hashing;
- JWT access tokens;
- request/response schemas;
- user repository;
- authentication service;
- register/login endpoints;
- current-user dependency;
- role-based authorization.

### Who did what

Nnamdi:
- Bootstrapped the FastAPI project structure, `Dockerfile`, `docker-compose.yml`, and `pyproject.toml`/dependency setup.
- Set up `alembic.ini`, `alembic/env.py`, and generated and fixed the first migration, including the enum downgrade issue.
- Wired up GitHub Actions CI to run migrations and pytest on every push.

Stephanie:
- Built `app/db/session.py` (the SQLAlchemy engine and session dependency) and verified the app could connect to PostgreSQL with a real `SELECT 1` check.
- Debugged and fixed local Docker/Postgres connection issues (stale volumes, `localhost` vs container hostnames) while getting the environment running end to end.

Shared:
- Reviewed Docker and database setup.
- Reviewed migration behavior and the CI workflow.

---

## Day 3 — Authentication and Role-Based Authorization

### What we did

We implemented password hashing using Argon2 through `pwdlib`.

Plain-text passwords are never stored in PostgreSQL.

We added JWT access token creation and validation.

JWT tokens contain:

- `sub` for the user ID;
- `exp` for token expiry.

We created authentication request and response schemas for:

- registration;
- login;
- token responses;
- safe user responses.

The public registration schema deliberately does not accept a role, so a user cannot register themselves as an administrator.

We implemented the `UserRepository` with:

- `get_by_email`;
- `get_by_id`;
- `create`.

We added an `AuthService` that handles:

- duplicate email checks;
- password hashing;
- login authentication;
- JWT generation.

We created API endpoints:

- `POST /api/v1/auth/register`;
- `POST /api/v1/auth/login`;
- `GET /api/v1/auth/me`.

We implemented `get_current_user`, which:

- reads the Bearer token;
- validates the JWT;
- extracts the user ID;
- loads the current user from PostgreSQL.

We implemented reusable role-based authorization with:

`require_roles(...)`.

Roles currently are:

- MEMBER;
- FRONT_DESK;
- ADMIN.

We tested 401 and 403 behavior.

We also hardened authentication against:

- duplicate registrations;
- wrong passwords;
- invalid emails;
- expired JWTs;
- malformed JWTs;
- JWTs for deleted users;
- members trying staff-only operations.

### What broke / challenges

One issue was deciding where each responsibility should live.

It would have been easy to put password hashing, database queries and HTTP errors directly inside FastAPI routes.

Instead, we separated:

- router responsibilities;
- service responsibilities;
- repository responsibilities.

We also discussed the difference between service errors and HTTP errors.

The service raises application errors such as `InvalidCredentialsError`, while the router converts them into HTTP responses.

Another challenge was making sure role-based authorization did not depend only on information stored inside the JWT.

We decided to load the current user from PostgreSQL so role changes take effect immediately.

### What we learnt

We learnt the difference between authentication and authorization.

Authentication answers:

`Who are you?`

Authorization answers:

`Are you allowed to do this?`

We learnt the HTTP distinction:

- 401 means authentication failed;
- 403 means authentication succeeded but permission is denied.

We learnt that JWT payloads are signed, not encrypted, so sensitive information should not be stored in them.

We also learnt why response schemas are separate from SQLModel database models: database fields such as `password_hash` must never be accidentally exposed through the API.

### What is next

Day 4 will implement the gym membership business domain:

- membership plans;
- memberships;
- membership lifecycle;
- staff/member access rules;
- freezing and unfreezing;
- preparation for membership expiry and reminder jobs.

### Who did what

Nnamdi:
- Implemented Argon2 password hashing and JWT creation/validation in `core/security.py`.
- Built the `AuthService` (duplicate-email checks, authentication, JWT generation) and the `get_current_user` / `require_roles` dependencies for role-based authorization.

Stephanie:
- Built the authentication request/response schemas (register, login, token, safe user response) and the `UserRepository` (`get_by_email`, `get_by_id`, `create`), including repository-level tests.
- Implemented the `POST /auth/register` and `POST /auth/login` endpoints, and tested 401/403 behavior across the protected routes.

Shared:
- Reviewed authentication flow and role behavior.
- Tested login and protected routes.

---

## Day 4 — Membership Plans and Membership Lifecycle

### What we did

We implemented membership-plan schemas, repository, service and API endpoints.

Plan endpoints include:

- list plans;
- view a plan;
- create a plan;
- update a plan;
- delete a plan.

Only ADMIN users can modify plans.

Members, front-desk staff and admins can view plans.

We added a business rule preventing a plan from being deleted after a membership references it.

We then discussed the real-world gym membership flow in more detail and refined the project design.

We clarified that:

`UserRole.MEMBER`

means the user is a gym customer account, while:

`MembershipStatus.ACTIVE`

means the customer currently has paid gym entitlement.

We changed the membership lifecycle from the original simple `PENDING` state to:

- `PENDING_PAYMENT`;
- `ACTIVE`;
- `FROZEN`;
- `EXPIRED`;
- `CANCELLED`.

A membership awaiting payment has:

- `start_date = NULL`;
- `end_date = NULL`.

Payment confirmation later sets those dates and activates the membership.

We added `frozen_on` so FitPro can calculate how long a membership was paused.

We created a second Alembic migration for the refined membership lifecycle.

We implemented:

- membership schemas;
- membership repository;
- membership service;
- member membership API;
- staff membership API;
- freeze/unfreeze behavior.

Members can create a pending subscription for themselves.

Front-desk/admin users can create a pending subscription for another member.

Members can only view their own membership history.

Staff/admin users can inspect membership records.

We defined a membership end date as an exclusive expiry date.

For example:

- start date: 21 September;
- duration: 30 days;
- end date: 21 October;
- membership is valid through 20 October.

We implemented freezing so only ACTIVE memberships can be frozen.

Unfreezing extends the end date by the number of frozen days.

We also added repository queries needed for the future daily job:

- `get_active_expiring_on(target_date)`;
- `get_active_expired_by(as_of_date)`.

### What broke / challenges

The first attempt at generating the membership-lifecycle migration was dangerous.

Alembic generated a migration that tried to drop almost every FitPro table.

We discovered that the cause was replacing `SQLModel.metadata` in `app/db/base.py`.

Alembic was comparing PostgreSQL's nine tables against an empty metadata object and concluded that all tables should be deleted.

We fixed the metadata setup and regenerated the migration.

The corrected migration only changed the memberships table.

Alembic did not automatically handle the PostgreSQL enum change, so we manually wrote the enum migration from:

`PENDING`

to:

`PENDING_PAYMENT`

and added:

`CANCELLED`.

We tested upgrade, downgrade and re-upgrade successfully.

Another challenge was deciding exactly what a gym class represents.

We clarified that each row in `classes` should represent one scheduled class session, such as:

`Spin — 21 Sep — 6 PM`

rather than a permanent generic class that resets every day.

### What we learnt

We learnt that a user account and an active membership are separate concepts.

Registering gives a user an account, while successful payment grants active gym entitlement.

We learnt that generic status-update APIs can be dangerous.

Instead of allowing clients to arbitrarily change membership status, important transitions such as:

- activation;
- freeze;
- unfreeze;
- expiry

should happen through explicit business operations.

We learnt that Alembic autogenerate is only a comparison assistant and generated migrations must always be reviewed.

We also learnt why an expiry query should use:

`end_date <= today`

instead of only:

`end_date == today`.

If the daily job misses a day, overdue memberships must still be found on the next run.

### What is next

Day 5 will implement payments and membership activation:

- staff-recorded payments;
- online-payment initialization;
- payment references;
- payment status lifecycle;
- payment-provider webhooks;
- webhook signatures;
- idempotent event processing.

### Who did what

Nnamdi:
- Implemented membership-plan schemas, repository, service and the full Plan CRUD API with ADMIN-only write access, plus the rule blocking deletion of a plan already referenced by a membership.
- Diagnosed and fixed the dangerous Alembic autogenerate issue caused by the `SQLModel.metadata` mismatch, and hand-wrote the enum migration for the refined membership-status lifecycle.

Stephanie:
- Implemented the membership schemas, repository and service, including the subscribe date-math (`end_date = start_date + plan.period_days`) and the freeze/unfreeze logic that extends `end_date` by the frozen duration.
- Built the member-facing and staff-facing membership endpoints with the correct role and ownership rules (members see only their own membership; staff can freeze/unfreeze any membership), and wrote the membership service-level tests.

Shared:
- Reviewed the gym membership business flow.
- Discussed class-session behavior and membership lifecycle rules.

---

## Day 5 — Payments, Membership Activation and Webhooks

### What we did

We refined the original payment model so it can support both offline and online payments.

Payments now contain:

- membership ID;
- amount;
- status;
- method;
- unique reference;
- provider;
- recorded-by user when applicable;
- recorded timestamp;
- paid timestamp.

Payment statuses are:

- PENDING;
- SUCCEEDED;
- FAILED.

Payment methods include:

- CASH;
- TRANSFER;
- CARD;
- ONLINE.

We made `recorded_by` nullable because an online payment confirmed by a payment provider is not recorded manually by a FitPro employee.

We added a third Alembic migration for the refined payment lifecycle.

We implemented the PaymentRepository with:

- lookup by ID;
- lookup by reference;
- membership payment history;
- create;
- update;
- pending/successful payment lookups.

We implemented transactional staff payment processing.

For an offline payment:

- the membership must be `PENDING_PAYMENT`;
- FitPro derives the amount from the selected membership plan;
- staff cannot manually submit the amount;
- staff cannot manually use the ONLINE payment method;
- FitPro generates the payment reference;
- payment becomes `SUCCEEDED`;
- membership becomes `ACTIVE`;
- payment creation and membership activation commit in one PostgreSQL transaction.

We then implemented online-payment initialization.

Online initialization:

- creates a `PENDING` payment;
- uses the plan price;
- generates a unique FitPro reference;
- stores the provider;
- leaves `recorded_by` empty;
- does not activate the membership.

We introduced a payment-provider abstraction and a fake provider for development.

The instructor then provided a mock payment-provider script.

The script sends signed webhook requests to:

`POST /api/v1/webhooks/payment`.

We implemented:

- webhook payload schema;
- raw-body HMAC-SHA256 signature validation;
- processed-event repository;
- webhook service;
- webhook API endpoint;
- payment lookup by reference;
- payment-row locking using `FOR UPDATE`;
- webhook event idempotency;
- orphan webhook handling;
- amount verification;
- currency verification.

The webhook success operation updates:

- Payment → SUCCEEDED;
- Membership → ACTIVE;
- ProcessedEvent → inserted;

inside one transaction.

Duplicate webhook events return HTTP 200 without changing the payment or membership a second time.

Unknown references return HTTP 200 and are recorded as orphan events.

Bad signatures return HTTP 401.

### What broke / challenges

The first time we ran the instructor's mock payment provider, every request returned:

`401 Invalid webhook signature`.

We discovered that the `WEBHOOK_SECRET` being used by the API container did not match the secret passed to the mock provider script.

After making the secrets match, signature verification worked.

The next mock-provider run returned:

- valid event → 200 orphan;
- duplicate → 200 duplicate;
- wrong signature → 401;
- unknown reference → 200 orphan.

The first event was still an orphan because no real pending online payment with that reference existed yet.

We decided to create the real business records later for the final end-to-end provider test.

We also accidentally pasted some payment-router code into `payment_service.py`.

We corrected the file responsibilities so:

- provider/business logic remains in services;
- HTTP response construction remains in routers.

We also cleaned duplicated imports and incorrect repository imports in `payments.py`.

### What we learnt

We learnt that webhook signatures must be calculated from the exact raw request bytes.

Parsing JSON and reconstructing it before checking the HMAC may alter the byte sequence and invalidate the signature.

We learnt the difference between:

`Payment.reference`

and:

`ProcessedEvent.event_id`.

The payment reference identifies the payment transaction.

The event ID identifies one provider notification.

A provider may retry the same event, which is why `processed_events.event_id` is unique.

We learnt why webhook endpoints do not use JWT authentication.

Members and staff authenticate with JWTs, while an external payment provider authenticates using its HMAC signature.

We also learnt why financial state transitions must be atomic.

A successful payment and membership activation must either both commit or both roll back.

We learnt that the provider sends amounts in the smallest currency unit, so FitPro must compare:

`payment.amount × 100`

against the provider's kobo value without converting money through Python floats.

### What is next

Day 6 will implement scheduled gym classes and class check-ins.

The main rules will include:

- each class row represents one scheduled session;
- only members with ACTIVE membership can check in;
- duplicate check-in must return 409;
- a full class must return 409;
- capacity must never be exceeded even if two members attempt the final place at the same time;
- the class-count query will later feed the live board/SSE feature.

After classes/check-ins, we still need to implement the daily membership job and its idempotency requirement.

### Who did what

Nnamdi:
- Refined the Payment model and schemas, wrote the third Alembic migration, and implemented the `PaymentRepository`, `PaymentService`, and the staff/offline payment endpoint with atomic payment-and-membership-activation in one transaction.
- Implemented online-payment initialization, the payment-provider abstraction and fake provider, and the full webhook flow (signature validation, `WebhookService`, row locking, amount/currency verification, orphan handling).
- Diagnosed and fixed the `WEBHOOK_SECRET` mismatch that was causing every mock-provider request to fail signature validation, and cleaned up the duplicated/misplaced code between `payments.py` and `payment_service.py`.

Stephanie:
- Built and tested a first version of the payment webhook (HMAC signature verification and `processed_events` idempotency) independently, then reconciled it against Nnamdi's completed `WebhookService` implementation once both were compared, keeping the more complete version.
- Added `scripts/mock_payment_provider.py` to the repo for repeatable local testing, worked through the local Postgres/environment issues blocking end-to-end webhook testing, and prepared the Postman collection and test flow used to demonstrate the full payment journey (subscribe → staff payment → online payment → webhook) for review.

Shared:
- Reviewed payment and webhook design.
- Tested provider signature and duplicate behavior.
- Discussed payment-provider retry and idempotency rules.

---




## Day 6 — Scheduled Classes, Check-ins and Capacity Concurrency

### What we did

Today we implemented FitPro's scheduled class and check-in domain.

We clarified that one row in the `classes` table represents one specific scheduled class session, for example:

`Spin — 22 Sep 2026 — 6:00 PM`

rather than a reusable class definition that resets every day.

We implemented class schemas, repository, service and CRUD API.

Administrators can create, update and delete scheduled class sessions.

Authenticated members, front-desk staff and administrators can list and view scheduled sessions.

The class service prevents normal class creation in the past.

It also prevents reducing class capacity below the number of members already checked in.

A class session with attendance history cannot be deleted.

We implemented the CheckinRepository and CheckinService.

Members can check themselves into a class, while front-desk staff and administrators can perform assisted check-in for a member.

Check-in requires:

- the class to exist;
- the target user to be a MEMBER;
- the member to have an ACTIVE membership;
- the membership dates to still grant entitlement;
- the class not to have already started;
- the member not to already be checked in;
- the class not to be full.

We implemented the class-capacity concurrency solution using a PostgreSQL row lock.

Before checking capacity, the service loads the class with:

`SELECT ... FOR UPDATE`

inside the same transaction.

The service then counts check-ins and inserts the new check-in before committing.

This prevents two simultaneous requests from both taking the final class space.

We added a real PostgreSQL concurrency test using separate database sessions and threads.

The test prepares a class with capacity 12 and 11 existing check-ins, then sends two competing check-in operations at the same time.

The expected result is:

- one request succeeds;
- one request receives the class-full error;
- final attendance remains exactly 12.

We also added class-board responses that derive:

- capacity;
- checked-in count;
- remaining spaces;
- whether the class is full.

These values currently come from PostgreSQL and will later be projected into Firestore for the wall display.

### What broke / challenges

The main challenge was understanding why a normal:

`count → compare → insert`

sequence is not safe when requests happen concurrently.

Without locking, two requests could both read the same attendance count and both insert, which could push a class beyond capacity.

We also had to keep transaction boundaries correct.

The class row lock must remain active from the moment the class is selected through the attendance count and check-in insert until the transaction commits.

Another challenge was separating normal business tests from actual concurrency tests.

Fake repositories can test the capacity rule itself, but they cannot prove PostgreSQL locking behavior.

We therefore added a separate integration test using the real `fitpro_test` PostgreSQL database.

### What we learnt

We learnt that concurrency correctness cannot be proven only with application-level `if` statements.

The database transaction and row lock are what serialize competing capacity decisions.

We learnt that the authoritative class attendance count should come from the `checkins` table instead of a manually maintained counter on the class row.

We also learnt why a frozen or date-expired membership should not grant class access even if a stale status value exists.

The service checks both membership status and entitlement dates.

We learnt that a new class session should be a new database row rather than resetting yesterday's attendance count.

This preserves historical attendance automatically.

### What is next

Next we will implement the scheduled daily membership job.

The daily job must:

- expire memberships whose end date has passed;
- create renewal reminders seven days before expiry;
- be safe to run more than once on the same day;
- avoid duplicate reminders;
- record its execution in `job_runs`.

This is the main hard problem described in the original project brief.

After that, we will continue with the remaining live-board, Firestore, Redis and activity-feed requirements.

### Who did what

Michael:
- [Fill in your actual work.]

Partner:
- [Fill in your partner's actual work.]

Shared:
- Reviewed the class-capacity race condition.
- Discussed the transaction and locking strategy.
- Tested class and check-in behavior.






## Day 7 — Daily Job and Idempotency

### What we did

Today we implemented FitPro's daily membership-maintenance job.

The job performs two main business operations:

- expire ACTIVE memberships whose `end_date` is today or earlier;
- create one renewal reminder for ACTIVE memberships expiring exactly seven days later.

We implemented repositories for `job_runs` and `reminders`.

The daily job uses the existing unique constraint on:

`job_runs(job_name, run_date)`

to make the job idempotent.

Instead of first checking whether today's job has already run, the
service tries to insert today's job-run row and immediately calls
`flush()`.

PostgreSQL therefore decides which concurrent execution owns that day's
job before any membership maintenance work begins.

The winning execution expires memberships, creates missing reminders
and commits everything together.

The losing execution receives the uniqueness conflict and returns
`already_run` without repeating the work.

We also added a secure scheduler endpoint:

`POST /api/v1/jobs/daily`

The endpoint uses the `X-API-Key` header rather than user JWT
authentication.

We created real PostgreSQL tests for:

- running the job twice sequentially;
- two concurrent executions;
- exactly one `job_runs` row;
- exactly one expiry reminder;
- membership expiry;
- full rollback when the job fails;
- frozen-membership behavior;
- missed-job recovery;
- the exact seven-day reminder boundary.

### What broke / challenges

The main challenge was understanding why a normal existence check is
not sufficient for idempotency.

Two requests can both check for a job-run row before either one inserts
it.

We solved this by using an insert-first strategy with the database
unique constraint and `flush()`.

We also had to make sure the job-run marker was not committed before
the actual maintenance work.

If the marker were committed first and the job later failed, future
retries would incorrectly believe the job had already completed.

### What we learnt

We learnt the difference between `flush()` and `commit()`.

`flush()` sends pending SQL to PostgreSQL so constraints can be checked,
but the transaction is still open.

`commit()` permanently completes the transaction.

This allowed us to claim the day's unique job execution before doing the
work while still rolling back the claim if anything failed.

We also learnt that idempotency should be enforced at more than one
level.

`job_runs` protects the whole daily execution, while the unique reminder
constraint separately protects reminder records.

### What is next

Next we will continue with the remaining infrastructure requirements:

- Redis;
- Firestore class-board projection;
- activity feed;
- SSE/live updates;
- final documentation;
- presentation preparation.

### Who did what

Michael:
- [Fill in your actual work.]

Partner:
- [Fill in your partner's actual work.]

Shared:
- Reviewed the daily-job race condition.
- Discussed the insert-first idempotency strategy.
- Reviewed the transaction and rollback behavior.