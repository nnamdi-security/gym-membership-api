from sqlmodel import Session, select

from app.models.checkin import Checkin


class CheckinRepository:
    def __init__(
        self,
        session: Session,
    ):
        self.session = session

    def get_by_class_and_member(
        self,
        class_id: int,
        member_id: int,
    ) -> Checkin | None:
        statement = select(Checkin).where(
            Checkin.class_id == class_id,
            Checkin.member_id == member_id,
        )

        return self.session.exec(statement).first()

    def get_for_class(
        self,
        class_id: int,
    ) -> list[Checkin]:
        statement = (
            select(Checkin)
            .where(Checkin.class_id == class_id)
            .order_by(Checkin.checked_in_at)
        )

        return list(self.session.exec(statement).all())

    def get_for_member(
        self,
        member_id: int,
    ) -> list[Checkin]:
        statement = (
            select(Checkin)
            .where(Checkin.member_id == member_id)
            .order_by(Checkin.checked_in_at.desc())
        )

        return list(self.session.exec(statement).all())

    def add(
        self,
        checkin: Checkin,
    ) -> Checkin:
        self.session.add(checkin)

        return checkin

    def create(
        self,
        checkin: Checkin,
    ) -> Checkin:
        self.session.add(checkin)
        self.session.commit()
        self.session.refresh(checkin)

        return checkin
