"""refine membership lifecycle

Revision ID: 0b2fe3043043
Revises: 046226a2fcb4
Create Date: 2026-09-21 14:57:45.020804
"""

from _collections_abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0b2fe3043043"
down_revision: str | Sequence[str] | None = "046226a2fcb4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.drop_index(
        op.f("ix_memberships_end_date_status"),
        table_name="memberships",
    )

    op.add_column(
        "memberships",
        sa.Column(
            "frozen_on",
            sa.Date(),
            nullable=True,
        ),
    )

    op.alter_column(
        "memberships",
        "start_date",
        existing_type=sa.Date(),
        nullable=True,
    )

    op.alter_column(
        "memberships",
        "end_date",
        existing_type=sa.Date(),
        nullable=True,
    )

    op.execute(
        """
        CREATE TYPE membershipstatus_new AS ENUM (
            'PENDING_PAYMENT',
            'ACTIVE',
            'FROZEN',
            'EXPIRED',
            'CANCELLED'
        )
        """
    )

    op.execute(
        """
        ALTER TABLE memberships
        ALTER COLUMN status
        TYPE membershipstatus_new
        USING (
            CASE
                WHEN status::text = 'PENDING'
                    THEN 'PENDING_PAYMENT'::membershipstatus_new
                ELSE status::text::membershipstatus_new
            END
        )
        """
    )

    op.execute(
        "DROP TYPE membershipstatus"
    )

    op.execute(
        "ALTER TYPE membershipstatus_new RENAME TO membershipstatus"
    )

    op.create_index(
        op.f("ix_memberships_end_date_status"),
        "memberships",
        ["end_date", "status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_memberships_end_date_status"),
        table_name="memberships",
    )

    op.execute(
        """
        UPDATE memberships
        SET
            start_date = COALESCE(start_date, created_at::date),
            end_date = COALESCE(end_date, created_at::date)
        """
    )

    op.alter_column(
        "memberships",
        "end_date",
        existing_type=sa.Date(),
        nullable=False,
    )

    op.alter_column(
        "memberships",
        "start_date",
        existing_type=sa.Date(),
        nullable=False,
    )

    op.drop_column(
        "memberships",
        "frozen_on",
    )

    op.execute(
        """
        CREATE TYPE membershipstatus_old AS ENUM (
            'PENDING',
            'ACTIVE',
            'FROZEN',
            'EXPIRED'
        )
        """
    )

    op.execute(
        """
        ALTER TABLE memberships
        ALTER COLUMN status
        TYPE membershipstatus_old
        USING (
            CASE
                WHEN status::text = 'PENDING_PAYMENT'
                    THEN 'PENDING'::membershipstatus_old
                WHEN status::text = 'CANCELLED'
                    THEN 'PENDING'::membershipstatus_old
                ELSE status::text::membershipstatus_old
            END
        )
        """
    )

    op.execute(
        "DROP TYPE membershipstatus"
    )

    op.execute(
        "ALTER TYPE membershipstatus_old RENAME TO membershipstatus"
    )

    op.create_index(
        op.f("ix_memberships_end_date_status"),
        "memberships",
        ["end_date", "status"],
        unique=False,
    )