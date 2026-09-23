from sqlmodel import Session, select

from app.models.processed_event import ProcessedEvent


class ProcessedEventRepository:
    def __init__(
        self,
        session: Session,
    ):
        self.session = session

    def get_by_event_id(
        self,
        event_id: str,
    ) -> ProcessedEvent | None:
        statement = select(ProcessedEvent).where(ProcessedEvent.event_id == event_id)

        return self.session.exec(statement).first()

    def add(
        self,
        processed_event: ProcessedEvent,
    ) -> ProcessedEvent:
        self.session.add(processed_event)

        return processed_event

    def create(
        self,
        processed_event: ProcessedEvent,
    ) -> ProcessedEvent:
        self.session.add(processed_event)
        self.session.commit()
        self.session.refresh(processed_event)

        return processed_event


# reference identifies the payment while event_id identifies the provider notification.
