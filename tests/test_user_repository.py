from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository


def test_create_user_saves_to_database(db_session):
    repository = UserRepository(db_session)

    user = User(
        email="steph@gmail.com",
        password_hash="hashed123",
        role=UserRole.MEMBER,
    )

    created = repository.create(user)

    assert created.id is not None
    assert created.email == "steph@gmail.com"
    assert created.role == UserRole.MEMBER


def test_get_by_id_returns_correct_user(db_session):
    repository = UserRepository(db_session)

    user = User(
        email="nnamdi@gmail.com",
        password_hash="hashed123",
        role=UserRole.MEMBER,
    )

    created = repository.create(user)

    found = repository.get_by_id(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.email == "nnamdi@gmail.com"


def test_get_by_id_returns_none_when_not_found(db_session):
    repository = UserRepository(db_session)

    found = repository.get_by_id(999999)

    assert found is None


def test_get_by_email_returns_correct_user(db_session):
    repository = UserRepository(db_session)

    user = User(
        email="neche@gmail.com",
        password_hash="hashed123",
        role=UserRole.MEMBER,
    )

    created = repository.create(user)

    found = repository.get_by_email("neche@gmail.com")

    assert found is not None
    assert found.id == created.id
    assert found.email == "neche@gmail.com"


def test_get_by_email_returns_none_when_not_found(db_session):
    repository = UserRepository(db_session)

    found = repository.get_by_email(
        "ada@gmail.com"
    )

    assert found is None