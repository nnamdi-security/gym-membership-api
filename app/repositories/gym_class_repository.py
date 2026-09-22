# This layer answer database questions about scheduled class sessions without making business decisions.

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.checkin import Checkin
from app.models.gym_class import GymClass


class GymClassRepository:
    def __init__(
        self,
        session: Session,
    ):
        self.session = session

    def get_by_id(
        self,
        class_id: int,
    ) -> GymClass | None:
        return self.session.get(
            GymClass,
            class_id,
        )

    def get_all(
        self,
    ) -> list[GymClass]:
        statement = select(
            GymClass
        ).order_by(
            GymClass.starts_at
        )

        return list(
            self.session.exec(
                statement
            ).all()
        )

    def get_by_date(
        self,
        target_date: date,
    ) -> list[GymClass]:
        start_of_day = datetime.combine(
        target_date,
        time.min,
        tzinfo=timezone.utc,
)
        

        end_of_day = start_of_day + timedelta(days=1)

        statement = (
            select(GymClass)
            .where(
                GymClass.starts_at >= start_of_day,
                GymClass.starts_at < end_of_day,
            )
            .order_by(
                GymClass.starts_at
            )
        )

        return list(
            self.session.exec(
                statement
            ).all()
        )

    def count_checkins(
        # This should be the authoritative attendance count. We do not store current_count inside classes. Why? Because a stored counter can drift out of sync. The actual truth is: how many Checkin rows exist for this class session Later Firestore can hold a denormalized live count for the wall board, but PostgreSQL remains the source of truth.
        self,
        class_id: int,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(Checkin)
            .where(
                Checkin.class_id == class_id
            )
        )

        return int(
            self.session.exec(
                statement
            ).one()
        )

    def create(
        self,
        gym_class: GymClass,
    ) -> GymClass:
        self.session.add(
            gym_class
        )
        self.session.commit()
        self.session.refresh(
            gym_class
        )

        return gym_class

    def update(
        self,
        gym_class: GymClass,
    ) -> GymClass:
        self.session.add(
            gym_class
        )
        self.session.commit()
        self.session.refresh(
            gym_class
        )

        return gym_class

    def delete(
        self,
        gym_class: GymClass,
    ) -> None:
        self.session.delete(
            gym_class
        )
        self.session.commit()