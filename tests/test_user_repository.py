from app.repositories.user import create_user, get_user_by_id, get_user_by_email


def test_create_user_saves_to_database(db_session):
    user = create_user(db_session, email="steph@gmail.com", password_hash="hashed123")
    assert user.id is not None
    assert user.email == "steph@gmail.com"
    assert user.role == "member"


def test_get_user_by_id_returns_correct_user(db_session):
    created = create_user(
        db_session, email="nnamdi@gmail.com", password_hash="hashed123"
    )
    found = get_user_by_id(db_session, created.id)
    assert found is not None
    assert found.email == "nnamdi@gmail.com"


def test_get_user_by_id_returns_none_when_not_found(db_session):
    found = get_user_by_id(db_session, 999999)
    assert found is None


def test_get_user_by_email_returns_correct_user(db_session):
    create_user(db_session, email="neche@gmail.com", password_hash="hashed123")
    found = get_user_by_email(db_session, "find-neche@gmail.com")
    assert found is not None
    assert found.email == "find-neche@gmail.com"


def test_get_user_by_email_returns_none_when_not_found(db_session):
    found = get_user_by_email(db_session, "ada@gmail.com")
    assert found is None
