from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.job_run import JobRun
from app.repositories.job_run_repository import (
    JobRunRepository,
)


def test_create_job_run(
    db_session,
):
    repository = JobRunRepository(db_session)

    run = repository.create(
        JobRun(
            job_name="daily",
            run_date=date(2026, 9, 23),
        )
    )

    assert run.id is not None
    assert run.job_name == "daily"
    assert run.run_date == date(
        2026,
        9,
        23,
    )


def test_get_job_run_by_name_and_date(
    db_session,
):
    repository = JobRunRepository(db_session)

    created = repository.create(
        JobRun(
            job_name="daily",
            run_date=date(2026, 9, 23),
        )
    )

    found = repository.get_by_job_and_date(
        "daily",
        date(2026, 9, 23),
    )

    assert found is not None
    assert found.id == created.id


def test_duplicate_job_run_is_rejected(
    db_session,
):
    repository = JobRunRepository(db_session)

    repository.create(
        JobRun(
            job_name="daily",
            run_date=date(2026, 9, 23),
        )
    )

    duplicate = JobRun(
        job_name="daily",
        run_date=date(2026, 9, 23),
    )

    with pytest.raises(IntegrityError):
        repository.create(duplicate)

    db_session.rollback()
