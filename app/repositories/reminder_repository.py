from sqlmodel import Session, select

from app.models.reminder import Reminder, ReminderKind


class ReminderRepository:
    def __init__(
        self,
        session: Session,
    ):
        self.session = session

    def get_for_membership_and_kind(
        self,
        membership_id: int,
        kind: ReminderKind,
    ) -> Reminder | None:
        statement = select(Reminder).where(
            Reminder.membership_id == membership_id,
            Reminder.kind == kind,
        )

        return self.session.exec(statement).first()

    def get_for_membership(
        self,
        membership_id: int,
    ) -> list[Reminder]:
        statement = (
            select(Reminder)
            .where(Reminder.membership_id == membership_id)
            .order_by(Reminder.id)
        )

        return list(self.session.exec(statement).all())

    def add(
        self,
        reminder: Reminder,
    ) -> Reminder:
        self.session.add(reminder)

        return reminder

    def create(
        self,
        reminder: Reminder,
    ) -> Reminder:
        self.session.add(reminder)
        self.session.commit()
        self.session.refresh(reminder)

        return reminder
