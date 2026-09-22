from datetime import date, datetime, timezone

from app.models.gym_class import GymClass
from app.repositories.gym_class_repository import (
    GymClassRepository,
)

from app.models.checkin import Checkin
from app.models.user import User, UserRole


def test_create_class(
    db_session,
):
    repository = GymClassRepository(
        db_session
    )

    gym_class = GymClass(
        name="Spin",
        capacity=12,
        starts_at=datetime(
            2026,
            9,
            22,
            18,
            0,
            tzinfo=timezone.utc,
        ),
    )

    created = repository.create(
        gym_class
    )

    assert created.id is not None
    assert created.name == "Spin"
    assert created.capacity == 12




def test_get_class_by_id(
    db_session,
):
    repository = GymClassRepository(
        db_session
    )

    created = repository.create(
        GymClass(
            name="Yoga",
            capacity=20,
            starts_at=datetime(
                2026,
                9,
                22,
                9,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    found = repository.get_by_id(
        created.id
    )

    assert found is not None
    assert found.id == created.id




def test_get_by_id_returns_none_when_missing(
    db_session,
):
    repository = GymClassRepository(
        db_session
    )

    assert repository.get_by_id(
        999999
    ) is None



def test_get_all_orders_by_start_time(
    db_session,
):
    repository = GymClassRepository(
        db_session
    )

    repository.create(
        GymClass(
            name="Evening Spin",
            capacity=12,
            starts_at=datetime(
                2026,
                9,
                22,
                18,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    repository.create(
        GymClass(
            name="Morning Yoga",
            capacity=20,
            starts_at=datetime(
                2026,
                9,
                22,
                8,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    classes = repository.get_all()

    assert len(classes) == 2
    assert classes[0].name == "Morning Yoga"
    assert classes[1].name == "Evening Spin"



def test_get_by_date_returns_only_requested_day(
    db_session,
):
    repository = GymClassRepository(
        db_session
    )

    repository.create(
        GymClass(
            name="Day One",
            capacity=10,
            starts_at=datetime(
                2026,
                9,
                22,
                10,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    repository.create(
        GymClass(
            name="Day Two",
            capacity=10,
            starts_at=datetime(
                2026,
                9,
                23,
                10,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    classes = repository.get_by_date(
        date(2026, 9, 22)
    )

    assert len(classes) == 1
    assert classes[0].name == "Day One"





def test_count_checkins_returns_zero_when_empty(
    db_session,
):
    repository = GymClassRepository(
        db_session
    )

    gym_class = repository.create(
        GymClass(
            name="Spin",
            capacity=12,
            starts_at=datetime(
                2026,
                9,
                22,
                18,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    count = repository.count_checkins(
        gym_class.id
    )

    assert count == 0



def test_count_checkins_returns_actual_count(
    db_session,
):
    repository = GymClassRepository(
        db_session
    )

    gym_class = repository.create(
        GymClass(
            name="Spin",
            capacity=12,
            starts_at=datetime(
                2026,
                9,
                22,
                18,
                0,
                tzinfo=timezone.utc,
            ),
        )
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

    db_session.add(first_member)
    db_session.add(second_member)
    db_session.commit()

    db_session.refresh(first_member)
    db_session.refresh(second_member)

    db_session.add(
        Checkin(
            class_id=gym_class.id,
            member_id=first_member.id,
        )
    )

    db_session.add(
        Checkin(
            class_id=gym_class.id,
            member_id=second_member.id,
        )
    )

    db_session.commit()

    count = repository.count_checkins(
        gym_class.id
    )

    assert count == 2



def test_update_class(
    db_session,
):
    repository = GymClassRepository(
        db_session
    )

    gym_class = repository.create(
        GymClass(
            name="Spin",
            capacity=12,
            starts_at=datetime(
                2026,
                9,
                22,
                18,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    gym_class.capacity = 15

    updated = repository.update(
        gym_class
    )

    assert updated.capacity == 15



def test_delete_class(
    db_session,
):
    repository = GymClassRepository(
        db_session
    )

    gym_class = repository.create(
        GymClass(
            name="Temporary",
            capacity=10,
            starts_at=datetime(
                2026,
                9,
                22,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    class_id = gym_class.id

    repository.delete(
        gym_class
    )

    assert repository.get_by_id(
        class_id
    ) is None