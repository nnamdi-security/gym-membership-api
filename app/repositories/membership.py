from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.membership import Membership, MembershipStatus


class MembershipRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, membership_id: int) -> Membership | None:
        return self.session.get(Membership, membership_id)

    def get_by_member_id(self, member_id: int) -> Membership | None:
        statement = select(Membership).where(Membership.member_id == member_id)
        return self.session.exec(statement).first()

    def get_active_by_member_id(self, member_id: int) -> Membership | None:
        statement = select(Membership).where(
            Membership.member_id == member_id,
            Membership.status == MembershipStatus.ACTIVE,
        )
        return self.session.exec(statement).first()

    def create(self, membership: Membership) -> Membership:
        self.session.add(membership)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise
        self.session.refresh(membership)
        return membership

    def update(self, membership: Membership) -> Membership:
        self.session.add(membership)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise
        self.session.refresh(membership)
        return membership
