from datetime import UTC, date, datetime, timedelta, timezone
import pytest

from app.services.noop_activity_feed_projection import (
    NoOpActivityFeedProjector,
)
from app.services.noop_class_board_events import (
    NoOpClassBoardEventPublisher,
)
from app.services.noop_class_board_projection import (
    NoOpClassBoardProjector,
)

from app.models.checkin import Checkin
from app.models.gym_class import GymClass
from app.models.membership import Membership, MembershipStatus
from app.models.user import User, UserRole
from app.services.checkin_service import (
    ActiveMembershipRequiredError,
    AlreadyCheckedInError,
    CheckinService,
    GymClassAlreadyStartedError,
    GymClassNotFoundError,
    InvalidMemberRoleError,
    MemberNotFoundError,
)


class FakeGymClassRepository:
    def __init__(self, checkin_repository):
        self.classes: dict[int, GymClass] = {}
        self.checkin_repository = checkin_repository

    def get_by_id_for_update(
        self,
        class_id: int,
    ) -> GymClass | None:
        return self.classes.get(class_id)

    def count_checkins(
        self,
        class_id: int,
    ) -> int:
        return sum(
            1
            for checkin in self.checkin_repository.checkins
            if checkin.class_id == class_id
        )


class FakeCheckinRepository:
    def __init__(self):
        self.checkins: list[Checkin] = []

    def get_by_class_and_member(
        self,
        class_id: int,
        member_id: int,
    ) -> Checkin | None:
        for checkin in self.checkins:
            if checkin.class_id == class_id and checkin.member_id == member_id:
                return checkin

        return None

    def add(
        self,
        checkin: Checkin,
    ) -> Checkin:
        checkin.id = len(self.checkins) + 1
        self.checkins.append(checkin)

        return checkin


class FakeMembershipRepository:
    def __init__(self):
        self.memberships: dict[int, Membership] = {}

    def get_active_for_member(
        self,
        member_id: int,
    ) -> Membership | None:
        membership = self.memberships.get(member_id)

        if membership is not None and membership.status == MembershipStatus.ACTIVE:
            return membership

        return None


class FakeUserRepository:
    def __init__(self):
        self.users: dict[int, User] = {}

    def get_by_id(
        self,
        user_id: int,
    ) -> User | None:
        return self.users.get(user_id)


class FakeSession:
    def commit(self):
        pass

    def rollback(self):
        pass

    def refresh(self, obj):
        pass


class FakeClassBoardProjector:
    def __init__(self):
        self.payloads = []

    def publish(
        self,
        **kwargs,
    ):
        self.payloads.append(kwargs)

def build_service():
    session = FakeSession
    checkin_repository = FakeCheckinRepository()
    gym_class_repository = FakeGymClassRepository(checkin_repository)
    
    membership_repository = FakeMembershipRepository()
    user_repository = FakeUserRepository()

    class_board_projector = FakeClassBoardProjector()

    service = CheckinService(
    session=session,
    checkin_repository=checkin_repository,
    gym_class_repository=gym_class_repository,
    membership_repository=membership_repository,
    user_repository=user_repository,
    class_board_projector=class_board_projector,
    activity_feed_projector=NoOpActivityFeedProjector(),
    class_board_event_publisher=NoOpClassBoardEventPublisher(),
)

    member = User(
        id=1,
        email="member@example.com",
        password_hash="hash",
        role=UserRole.MEMBER,
    )

    user_repository.users[1] = member

    membership_repository.memberships[1] = Membership(
        id=1,
        member_id=1,
        plan_id=1,
        status=MembershipStatus.ACTIVE,
        start_date=date.today() - timedelta(days=5),  # noqa: DTZ011
        end_date=date.today() + timedelta(days=25),  # noqa: DTZ011
    )

    gym_class_repository.classes[1] = GymClass(
        id=1,
        name="Spin",
        capacity=12,
        starts_at=(datetime.now(UTC) + timedelta(hours=2)),
    )

    service = CheckinService(
        session=FakeSession(),
        checkin_repository=checkin_repository,
        gym_class_repository=gym_class_repository,
        membership_repository=membership_repository,
        user_repository=user_repository,
        class_board_projector=class_board_projector,
        activity_feed_projector=NoOpActivityFeedProjector(),
        class_board_event_publisher=NoOpClassBoardEventPublisher(),
    )

    return (
        service,
        gym_class_repository,
        checkin_repository,
        membership_repository,
        user_repository,
        class_board_projector
        
    )


def test_member_can_check_in():
    (
        service,
        _,
        checkin_repository,
        _,
        _,
        _,
    ) = build_service()

    checkin = service.check_in(
        class_id=1,
        member_id=1,
    )

    assert checkin.id == 1
    assert checkin.class_id == 1
    assert checkin.member_id == 1

    assert len(checkin_repository.checkins) == 1


def test_checkin_rejects_missing_class():
    service, class_repository, _, _, _, _ = build_service()

    class_repository.classes.clear()

    with pytest.raises(GymClassNotFoundError):
        service.check_in(
            class_id=1,
            member_id=1,
        )


def test_checkin_rejects_missing_member():
    service, _, _, _, user_repository, _ = build_service()

    user_repository.users.clear()

    with pytest.raises(MemberNotFoundError):
        service.check_in(
            class_id=1,
            member_id=1,
        )


def test_checkin_rejects_staff_user():
    service, _, _, _, user_repository, _ = build_service()

    user_repository.users[1].role = UserRole.FRONT_DESK

    with pytest.raises(InvalidMemberRoleError):
        service.check_in(
            class_id=1,
            member_id=1,
        )


def test_checkin_requires_active_membership():
    (
        service,
        _,
        _,
        membership_repository,
        _,
        _
    ) = build_service()

    membership_repository.memberships.clear()

    with pytest.raises(ActiveMembershipRequiredError):
        service.check_in(
            class_id=1,
            member_id=1,
        )


def test_checkin_rejects_expired_active_membership():
    (
        service,
        _,
        _,
        membership_repository,
        _,
        _
    ) = build_service()

    membership = membership_repository.memberships[1]

    membership.end_date = date.today()  # noqa: DTZ011

    with pytest.raises(ActiveMembershipRequiredError):
        service.check_in(
            class_id=1,
            member_id=1,
        )


def test_member_cannot_check_in_twice():
    (
        service,
        _,
        _,
        _,
        _,
        _
    ) = build_service()

    service.check_in(
        class_id=1,
        member_id=1,
    )

    with pytest.raises(AlreadyCheckedInError):
        service.check_in(
            class_id=1,
            member_id=1,
        )


def test_checkin_rejects_started_class():
    (
        service,
        class_repository,
        _,
        _,
        _,
        _
    ) = build_service()

    class_repository.classes[1].starts_at = datetime.now(UTC) - timedelta(
        minutes=1
    )

    with pytest.raises(GymClassAlreadyStartedError):
        service.check_in(
            class_id=1,
            member_id=1,
        )





def test_successful_checkin_publishes_class_board():
    (
        service,
        _,
        checkin_repository,
        _,
        _,
        projector,
    ) = build_service()

    checkin_repository.checkins = []

    service.check_in(
        class_id=1,
        member_id=1,
    )

    assert len(projector.payloads) == 1

    payload = projector.payloads[0]

    assert payload["class_id"] == 1
    assert payload["capacity"] == 12
    assert payload["checked_in"] == 1
    assert payload["remaining"] == 11
    assert payload["full"] is False


class FailingClassBoardProjector:
    def publish(
        self,
        **kwargs,
    ):
        raise RuntimeError("Firestore unavailable")


def test_firestore_failure_does_not_undo_checkin():
    (
        service,
        _,
        _,
        _,
        _,
        _,
    ) = build_service()

    service.class_board_projector = FailingClassBoardProjector()

    checkin = service.check_in(
        class_id=1,
        member_id=1,
    )

    assert checkin.id is not None
