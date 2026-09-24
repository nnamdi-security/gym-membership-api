from datetime import UTC, datetime, timedelta, timezone
from threading import Barrier

from sqlmodel import Session

from app.db.session import engine
from app.models.checkin import Checkin
from app.models.gym_class import GymClass
from app.models.membership import (
    Membership,
    MembershipStatus,
)
from app.models.plan import Plan
from app.models.user import User, UserRole
from app.repositories.checkins_repository import CheckinRepository
from app.repositories.gym_class_repository import GymClassRepository
from app.repositories.membership_repository import MembershipRepository
from app.repositories.user_repository import UserRepository
from app.services.checkin_service import (
    CheckinService,
    GymClassFullError,
)


def prepare_nearly_full_class() -> tuple[int, int, int]:
    with Session(engine) as session:
        plan = Plan(
            name="Concurrency Test Plan",
            price=1000,
            period_days=30,
        )

        gym_class = GymClass(
            name="Concurrency Spin",
            capacity=12,
            starts_at=(datetime.now(UTC) + timedelta(hours=2)),
        )

        session.add(plan)
        session.add(gym_class)
        session.commit()

        session.refresh(plan)
        session.refresh(gym_class)

        filler_members: list[User] = []

        for index in range(11):
            member = User(
                email=f"filler-{index}@example.com",
                password_hash="hash",
                role=UserRole.MEMBER,
            )

            filler_members.append(member)
            session.add(member)

        first_contender = User(
            email="contender-one@example.com",
            password_hash="hash",
            role=UserRole.MEMBER,
        )

        second_contender = User(
            email="contender-two@example.com",
            password_hash="hash",
            role=UserRole.MEMBER,
        )

        session.add(first_contender)
        session.add(second_contender)
        session.commit()

        for member in filler_members:
            session.refresh(member)

        session.refresh(first_contender)
        session.refresh(second_contender)

        today = datetime.now(timezone.utc)
        first_membership = Membership(
            member_id=first_contender.id,
            plan_id=plan.id,
            status=MembershipStatus.ACTIVE,
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=29),
        )

        second_membership = Membership(
            member_id=second_contender.id,
            plan_id=plan.id,
            status=MembershipStatus.ACTIVE,
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=29),
        )

        session.add(first_membership)
        session.add(second_membership)

        for member in filler_members:
            session.add(
                Checkin(
                    class_id=gym_class.id,
                    member_id=member.id,
                )
            )

        session.commit()

        return (
            gym_class.id,
            first_contender.id,
            second_contender.id,
        )




def attempt_checkin(
    *,
    class_id: int,
    member_id: int,
    barrier: Barrier,
) -> str:
    with Session(engine) as session:
        service = CheckinService(
            session=session,
            checkin_repository=CheckinRepository(session),
            gym_class_repository=GymClassRepository(session),
            membership_repository=MembershipRepository(session),
            user_repository=UserRepository(session),
            
        )

        barrier.wait()

        try:
            service.check_in(
                class_id=class_id,
                member_id=member_id,
            )

            return "success"

        except GymClassFullError:
            return "full"
