from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.checkin import Checkin
from app.models.gym_class import GymClass
from app.models.user import User, UserRole
from app.repositories.checkin_repository import (
    CheckinRepository,
)



def create_class_and_members(
    db_session,
) -> tuple[GymClass, User, User]:
    gym_class = GymClass(
        name="Spin",
        capacity=12,
        starts_at=(
            datetime.now(timezone.utc)
            + timedelta(days=1)
        ),
    )

    first_member = User(
        email="one@example.com",
        password_hash="hash",
        role=UserRole.MEMBER,
    )

    second_member = User(
        email="two@example.com",
        password_hash="hash",
        role=UserRole.MEMBER,
    )

    db_session.add(gym_class)
    db_session.add(first_member)
    db_session.add(second_member)
    db_session.commit()

    db_session.refresh(gym_class)
    db_session.refresh(first_member)
    db_session.refresh(second_member)

    return (
        gym_class,
        first_member,
        second_member,
    )


def test_create_checkin(
    db_session,
):
    gym_class, member, _ = (
        create_class_and_members(
            db_session
        )
    )

    repository = CheckinRepository(
        db_session
    )

    checkin = repository.create(
        Checkin(
            class_id=gym_class.id,
            member_id=member.id,
        )
    )

    assert checkin.id is not None
    assert checkin.class_id == gym_class.id
    assert checkin.member_id == member.id



def test_get_by_class_and_member(
    db_session,
):
    gym_class, member, _ = (
        create_class_and_members(
            db_session
        )
    )

    repository = CheckinRepository(
        db_session
    )

    created = repository.create(
        Checkin(
            class_id=gym_class.id,
            member_id=member.id,
        )
    )

    found = (
        repository.get_by_class_and_member(
            gym_class.id,
            member.id,
        )
    )

    assert found is not None
    assert found.id == created.id



def test_get_by_class_and_member(
    db_session,
):
    gym_class, member, _ = (
        create_class_and_members(
            db_session
        )
    )

    repository = CheckinRepository(
        db_session
    )

    created = repository.create(
        Checkin(
            class_id=gym_class.id,
            member_id=member.id,
        )
    )

    found = (
        repository.get_by_class_and_member(
            gym_class.id,
            member.id,
        )
    )

    assert found is not None
    assert found.id == created.id



def test_get_by_class_and_member_returns_none_when_missing(
    db_session,
):
    gym_class, member, _ = (
        create_class_and_members(
            db_session
        )
    )

    repository = CheckinRepository(
        db_session
    )

    found = (
        repository.get_by_class_and_member(
            gym_class.id,
            member.id,
        )
    )

    assert found is None




def test_get_for_member_returns_member_history(
    db_session,
):
    gym_class, member, _ = (
        create_class_and_members(
            db_session
        )
    )

    repository = CheckinRepository(
        db_session
    )

    created = repository.create(
        Checkin(
            class_id=gym_class.id,
            member_id=member.id,
        )
    )

    checkins = repository.get_for_member(
        member.id
    )

    assert len(checkins) == 1
    assert checkins[0].id == created.id


def test_duplicate_member_class_checkin_is_rejected(
    db_session,
):
    gym_class, member, _ = (
        create_class_and_members(
            db_session
        )
    )

    repository = CheckinRepository(
        db_session
    )

    repository.create(
        Checkin(
            class_id=gym_class.id,
            member_id=member.id,
        )
    )

    duplicate = Checkin(
        class_id=gym_class.id,
        member_id=member.id,
    )

    with pytest.raises(IntegrityError):
        repository.create(
            duplicate
        )

    db_session.rollback()