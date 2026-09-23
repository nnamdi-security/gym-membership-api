from datetime import date, datetime, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session

from app.models.checkin import Checkin
from app.models.membership import MembershipStatus
from app.models.user import UserRole
from app.repositories.checkins_repository import CheckinRepository
from app.repositories.gym_class_repository import GymClassRepository
from app.repositories.membership_repository import MembershipRepository
from app.repositories.user import UserRepository


import logging

from app.services.class_board_projection import (
    ClassBoardProjector,
)

from app.services.activity_feed_projection import (
    ActivityFeedProjector,
)

from app.services.class_board_event_publisher import (
    ClassBoardEventPublisher,
)

class GymClassNotFoundError(Exception):
    pass


class MemberNotFoundError(Exception):
    pass


class InvalidMemberRoleError(Exception):
    pass


class ActiveMembershipRequiredError(Exception):
    pass


class AlreadyCheckedInError(Exception):
    pass


class GymClassFullError(Exception):
    pass


class GymClassAlreadyStartedError(Exception):
    pass


class CheckinService:
    def __init__(
        self,
        session: Session,
        checkin_repository: CheckinRepository,
        gym_class_repository: GymClassRepository,
        membership_repository: MembershipRepository,
        user_repository: UserRepository,
        class_board_projector: ClassBoardProjector,
        activity_feed_projector: ActivityFeedProjector,
        class_board_event_publisher: ClassBoardEventPublisher,
    ):
        self.session = session
        self.checkin_repository = checkin_repository
        self.gym_class_repository = gym_class_repository
        self.membership_repository = membership_repository
        self.user_repository = user_repository
        self.class_board_projector = class_board_projector
        self.activity_feed_projector = activity_feed_projector
        self.class_board_event_publisher = (class_board_event_publisher)

    def check_in(
        self,
        *,
        class_id: int,
        member_id: int,
    ) -> Checkin:
        gym_class = (
            self.gym_class_repository.get_by_id_for_update(
                class_id
            )
        )

        if gym_class is None:
            raise GymClassNotFoundError

        self._validate_class_time(
            gym_class.starts_at
        )

        member = self.user_repository.get_by_id(
            member_id
        )

        if member is None:
            raise MemberNotFoundError

        if member.role != UserRole.MEMBER:
            raise InvalidMemberRoleError

        membership = (
            self.membership_repository.get_active_for_member(
                member_id
            )
        )

        if membership is None:
            raise ActiveMembershipRequiredError

        self._validate_membership_entitlement(
            membership
        )

        existing_checkin = (
            self.checkin_repository.get_by_class_and_member(
                class_id,
                member_id,
            )
        )

        if existing_checkin is not None:
            raise AlreadyCheckedInError

        current_count = (
            self.gym_class_repository.count_checkins(
                class_id
            )
        )

        if current_count >= gym_class.capacity:
            raise GymClassFullError

        checkin = Checkin(
            class_id=class_id,
            member_id=member_id,
        )

        try:
            self.checkin_repository.add(
                checkin
            )

            self.session.commit()

        except IntegrityError:
            self.session.rollback()
            raise AlreadyCheckedInError from None

        except SQLAlchemyError:
            self.session.rollback()
            raise

        self.session.refresh(checkin)

        self._publish_class_board(gym_class)

        self._publish_activity(checkin=checkin, gym_class=gym_class)

        board_payload = self._build_class_board_payload(gym_class)

        self._publish_class_board(board_payload)

        self._publish_class_board_event(board_payload)

        self._publish_activity(checkin=checkin, gym_class=gym_class)

        return checkin

    def _validate_class_time(
        self,
        starts_at: datetime,
    ) -> None:
        if starts_at.tzinfo is None:
            raise GymClassAlreadyStartedError

        if starts_at <= datetime.now(timezone.utc):
            raise GymClassAlreadyStartedError

    def _validate_membership_entitlement(
        self,
        membership,
    ) -> None:
        if membership.status != MembershipStatus.ACTIVE:
            raise ActiveMembershipRequiredError

        if (
            membership.start_date is None
            or membership.end_date is None
        ):
            raise ActiveMembershipRequiredError

        today = date.today()

        if not (
            membership.start_date
            <= today
            < membership.end_date
        ):
            raise ActiveMembershipRequiredError



    def get_member_checkins(
        self,
        member_id: int,
    ) -> list[Checkin]:
        return self.checkin_repository.get_for_member(
            member_id
        )


    def get_class_checkins(
        self,
        class_id: int,
    ) -> list[Checkin]:
        gym_class = self.gym_class_repository.get_by_id(
            class_id
        )

        if gym_class is None:
            raise GymClassNotFoundError

        return self.checkin_repository.get_for_class(
            class_id
        )




    def _publish_class_board(
        self,
        payload: dict,
    ) -> None:
        try:
            self.class_board_projector.publish(
                **payload
            )

        except Exception:
            logger.exception(
                "Failed to publish Firestore class board",
                extra={
                    "class_id": payload["class_id"],
                },
            )

    def _build_class_board_payload(
        self,
        gym_class,
    ) -> dict:
        checked_in = (
            self.gym_class_repository.count_checkins(
                gym_class.id
            )
        )

        remaining = max(
            gym_class.capacity - checked_in,
            0,
        )

        return {
            "class_id": gym_class.id,
            "name": gym_class.name,
            "starts_at": gym_class.starts_at,
            "capacity": gym_class.capacity,
            "checked_in": checked_in,
            "remaining": remaining,
            "full": checked_in >= gym_class.capacity,
        }    


    def _publish_activity(
        self,
        *,
        checkin: Checkin,
        gym_class,
    ) -> None:
        try:
            self.activity_feed_projector.publish(
                event_type="class.checked_in",
                occurred_at=checkin.checked_in_at,
                message=(
                    f"Member {checkin.member_id} "
                    f"checked into {gym_class.name}"
                ),
                data={
                    "member_id": checkin.member_id,
                    "class_id": gym_class.id,
                },
            )

        except Exception:
            logger.exception(
                "Failed to publish activity feed event",
                extra={
                    "class_id": gym_class.id,
                    "member_id": checkin.member_id,
                },
            )





    def _publish_class_board_event(
        self,
        payload: dict,
    ) -> None:
        try:
            self.class_board_event_publisher.publish(
                payload
            )

        except Exception:
            logger.exception(
                "Failed to publish Redis class-board event",
                extra={
                    "class_id": payload["class_id"],
                },
            )

logger = logging.getLogger(__name__)









# BEGIN
# ↓
# lock the class session row
# ↓
# confirm class exists
# ↓
# confirm target user is a MEMBER
# ↓
# confirm member has a valid ACTIVE membership
# ↓
# confirm member has not already checked in
# ↓
# count current check-ins
# ↓
# if count >= capacity → reject
# ↓
# insert check-in
# ↓
# COMMIT