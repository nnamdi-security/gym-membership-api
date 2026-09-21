"""refine payment lifecycle

Revision ID: 7309b31e7344
Revises: 0b2fe3043043
Create Date: 2026-09-21 22:34:11.626192

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7309b31e7344'
down_revision: Union[str, Sequence[str], None] = '0b2fe3043043'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PAYMENT_STATUS_ENUM = postgresql.ENUM(
    "PENDING",
    "SUCCEEDED",
    "FAILED",
    name="paymentstatus",
    create_type=False,
)

PAYMENT_METHOD_ENUM = postgresql.ENUM(
    "CASH",
    "TRANSFER",
    "CARD",
    "ONLINE",
    name="paymentmethod",
    create_type=False,
)

def upgrade() -> None:
    """Refine the payment lifecycle."""

    op.execute(
        """
        CREATE TYPE paymentstatus AS ENUM (
            'PENDING',
            'SUCCEEDED',
            'FAILED'
        )
        """
    )

    op.execute(
        """
        CREATE TYPE paymentmethod AS ENUM (
            'CASH',
            'TRANSFER',
            'CARD',
            'ONLINE'
        )
        """
    )

    # Add temporarily nullable so existing rows can be migrated safely.
    op.add_column(
        "payments",
        sa.Column(
            "status",
            PAYMENT_STATUS_ENUM,
            nullable=True,
        ),
    )

    op.add_column(
        "payments",
        sa.Column(
            "method",
            PAYMENT_METHOD_ENUM,
            nullable=True,
        ),
    )

    op.add_column(
        "payments",
        sa.Column(
            "reference",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "payments",
        sa.Column(
            "provider",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "payments",
        sa.Column(
            "paid_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Existing payment rows came from the old model where every record
    # represented an already-recorded payment.
    op.execute(
        """
        UPDATE payments
        SET
            status = 'SUCCEEDED'::paymentstatus,
            method = 'CASH'::paymentmethod,
            reference = 'LEGACY-' || id::text,
            paid_at = recorded_at
        WHERE status IS NULL
        """
    )

    op.alter_column(
        "payments",
        "status",
        existing_type=PAYMENT_STATUS_ENUM,
        nullable=False,
    )

    op.alter_column(
        "payments",
        "method",
        existing_type=PAYMENT_METHOD_ENUM,
        nullable=False,
    )

    op.alter_column(
        "payments",
        "reference",
        existing_type=sa.String(length=255),
        nullable=False,
    )

    op.alter_column(
        "payments",
        "recorded_by",
        existing_type=sa.Integer(),
        nullable=True,
    )

    op.create_index(
        op.f("ix_payments_reference"),
        "payments",
        ["reference"],
        unique=True,
    )


def downgrade() -> None:
    """Restore the original payment schema."""

    # Old schema requires recorded_by.
    # Online payments may have NULL here, so remove rows that cannot
    # meaningfully exist in the old representation.
    op.execute(
        """
        DELETE FROM payments
        WHERE recorded_by IS NULL
        """
    )

    op.alter_column(
        "payments",
        "recorded_by",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.drop_index(
        op.f("ix_payments_reference"),
        table_name="payments",
    )

    op.drop_column(
        "payments",
        "paid_at",
    )

    op.drop_column(
        "payments",
        "provider",
    )

    op.drop_column(
        "payments",
        "reference",
    )

    op.drop_column(
        "payments",
        "method",
    )

    op.drop_column(
        "payments",
        "status",
    )

    op.execute(
        "DROP TYPE paymentmethod"
    )

    op.execute(
        "DROP TYPE paymentstatus"
    )
