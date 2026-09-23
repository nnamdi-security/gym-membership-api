from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

from pwdlib import PasswordHash
from sqlmodel import Session, select

from app.core.config import settings
from app.db.session import engine
from app.models.gym_class import GymClass
from app.models.membership import Membership, MembershipStatus
from app.models.plan import Plan
from app.models.user import User, UserRole

password_hasher = PasswordHash.recommended()


# User helper function
def get_or_create_user(
    session: Session,
    *,
    email: str,
    role: UserRole,
) -> User:
    existing = session.exec(select(User).where(User.email == email)).first()

    if existing is not None:
        return existing

    user = User(
        email=email,
        password_hash=password_hasher.hash(settings.demo_seed_password),
        role=role,
    )

    session.add(user)
    session.flush()

    return user


# Plan helper function
def get_or_create_plan(
    session: Session,
    *,
    name: str,
    price: Decimal,
    period_days: int,
) -> Plan:
    existing = session.exec(select(Plan).where(Plan.name == name)).first()

    if existing is not None:
        return existing

    plan = Plan(
        name=name,
        price=price,
        period_days=period_days,
    )

    session.add(plan)
    session.flush()

    return plan


# Membership helper function
def membership_exists(
    session: Session,
    member_id: int,
) -> bool:
    membership = session.exec(
        select(Membership).where(Membership.member_id == member_id)
    ).first()

    return membership is not None


def seed_memberships(
    session: Session,
    *,
    monthly_plan: Plan,
    active_member: User,
    pending_member: User,
    frozen_member: User,
) -> None:
    today = datetime.now(timezone.utc)  # noqa: UP017

    if not membership_exists(
        session,
        active_member.id,
    ):
        session.add(
            Membership(
                member_id=active_member.id,
                plan_id=monthly_plan.id,
                status=MembershipStatus.ACTIVE,
                start_date=today - timedelta(days=5),
                end_date=today + timedelta(days=25),
            )
        )

    if not membership_exists(
        session,
        pending_member.id,
    ):
        session.add(
            Membership(
                member_id=pending_member.id,
                plan_id=monthly_plan.id,
                status=(MembershipStatus.PENDING_PAYMENT),
                start_date=None,
                end_date=None,
            )
        )

    if not membership_exists(
        session,
        frozen_member.id,
    ):
        session.add(
            Membership(
                member_id=frozen_member.id,
                plan_id=monthly_plan.id,
                status=MembershipStatus.FROZEN,
                start_date=today - timedelta(days=10),
                end_date=today + timedelta(days=20),
                frozen_on=today - timedelta(days=2),
            )
        )


def get_or_create_class(
    session: Session,
    *,
    name: str,
    starts_at: datetime,
    capacity: int,
) -> GymClass:
    existing = session.exec(
        select(GymClass).where(
            GymClass.name == name,
            GymClass.starts_at == starts_at,
        )
    ).first()

    if existing is not None:
        return existing

    gym_class = GymClass(
        name=name,
        starts_at=starts_at,
        capacity=capacity,
    )

    session.add(gym_class)
    session.flush()

    return gym_class


def future_demo_time(
    *,
    days_from_now: int,
    hour: int,
) -> datetime:
    today = datetime.now(UTC).date()

    target_date = today + timedelta(days=days_from_now)

    return datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        hour,
        0,
        tzinfo=UTC,
    )


def seed_classes(
    session: Session,
) -> None:
    get_or_create_class(
        session,
        name="Morning Strength",
        starts_at=future_demo_time(
            days_from_now=1,
            hour=8,
        ),
        capacity=10,
    )

    get_or_create_class(
        session,
        name="Spin Session",
        starts_at=future_demo_time(
            days_from_now=1,
            hour=17,
        ),
        capacity=3,
    )

    get_or_create_class(
        session,
        name="Evening Yoga",
        starts_at=future_demo_time(
            days_from_now=2,
            hour=18,
        ),
        capacity=12,
    )


def seed_demo_data() -> None:
    with Session(engine) as session:
        try:
            get_or_create_user(
                session,
                email="admin@fitpro.demo",
                role=UserRole.ADMIN,
            )

            get_or_create_user(
                session,
                email="frontdesk@fitpro.demo",
                role=UserRole.FRONT_DESK,
            )

            active_member = get_or_create_user(
                session,
                email="member@fitpro.demo",
                role=UserRole.MEMBER,
            )

            pending_member = get_or_create_user(
                session,
                email="pending@fitpro.demo",
                role=UserRole.MEMBER,
            )

            frozen_member = get_or_create_user(
                session,
                email="frozen@fitpro.demo",
                role=UserRole.MEMBER,
            )

            monthly_plan = get_or_create_plan(
                session,
                name="Monthly",
                price=Decimal("15000.00"),
                period_days=30,
            )

            get_or_create_plan(
                session,
                name="Quarterly",
                price=Decimal("40000.00"),
                period_days=90,
            )

            seed_memberships(
                session,
                monthly_plan=monthly_plan,
                active_member=active_member,
                pending_member=pending_member,
                frozen_member=frozen_member,
            )

            seed_classes(session)

            session.commit()

        except Exception:
            session.rollback()
            raise

    print("FitPro demo data seeded successfully.")


if __name__ == "__main__":
    seed_demo_data()
