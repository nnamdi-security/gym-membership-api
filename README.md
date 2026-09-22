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

_To be written in our own words after implementing the daily job._

## Why This Design

_To be expanded throughout the project._

## Flowcharts

### Daily Job

_To be added._

### Class Check-in / Capacity

_To be added._