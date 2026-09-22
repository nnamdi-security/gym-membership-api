## Day 5 — Payments, Membership Activation and Webhooks

### What we did

Today we implemented FitPro's payment flow for both staff-recorded payments and online payments.

For staff payments, front-desk or admin users can record payment for a membership that is still in `PENDING_PAYMENT`. The amount is not supplied by the staff user; FitPro gets the correct amount from the membership plan. When the payment succeeds, the payment becomes `SUCCEEDED` and the membership becomes `ACTIVE`.

We made payment recording and membership activation one database transaction so that we cannot end up with a successful payment while the membership remains pending.

We also implemented online payment initialization. FitPro creates a `PENDING` online payment, generates a unique reference, and returns checkout information without activating the membership.

We integrated the instructor's mock payment provider using the `/api/v1/webhooks/payment` endpoint. The webhook uses HMAC-SHA256 verification through the `X-Signature` header.

We added webhook idempotency using the `processed_events` table. Duplicate provider events return HTTP 200 without changing the payment or membership a second time.

We also implemented handling for orphan webhook events, invalid signatures, mismatched amounts and currencies, and invalid webhook payloads.

### What broke / challenges

The first time we ran the mock payment provider, every webhook returned HTTP 401. We discovered that the webhook secret used by the mock script did not match the `WEBHOOK_SECRET` inside the API container.

After fixing the secret, valid requests passed signature verification.

The first valid event was then returned as an `orphan`. We learned that this was expected because we had not yet created an actual pending online payment with the reference being sent by the mock provider.

We also had some payment service and router code pasted into the wrong files. We reorganized the code so provider initialization and business rules remained in the service layer while FastAPI response handling stayed in the router.

### What we learnt

We learnt that a signed webhook must be verified against the exact raw request body. Parsing and rebuilding the JSON before verifying the signature can change the bytes and invalidate the HMAC.

We also understood the difference between a payment reference and a webhook event ID. The payment reference identifies the payment transaction, while the event ID identifies one provider notification.

We learnt why webhook processing must be idempotent because payment providers may retry the exact same event.

We also learnt why payment success and membership activation must happen in one transaction: either both changes commit or both roll back.

### What is next

Next we will move into the classes and check-in domain.

We need to create scheduled class sessions, implement capacity rules, and solve the concurrency problem where two members may try to take the final available class spot at the same time.

### Who did what

Michael:
- [replace with the parts you actually handled]

Partner:
- [replace with the parts your partner actually handled]

Shared:
- Reviewed the payment flow and webhook behavior together.
- Tested the mock payment provider behavior and discussed the idempotency rules.