from datetime import date

from sqlmodel import Session, select

from app.models.membership import Membership, MembershipStatus


class MembershipRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, membership_id: int) -> Membership | None:
        return self.session.get(Membership, membership_id)

    def get_for_member(
        self,
        member_id: int,
    ) -> list[Membership]:
        statement = (
            select(Membership)
            .where(Membership.member_id == member_id)
            .order_by(Membership.id.desc())
        )

        return list(self.session.exec(statement).all())

    def get_active_for_member(
        #  Is this member currently entitled to use the gym?
        self,
        member_id: int,
    ) -> Membership | None:
        statement = (
            select(Membership)
            .where(
                Membership.member_id == member_id,
                Membership.status == MembershipStatus.ACTIVE,
            )
            .order_by(Membership.id.desc())
        )

        return self.session.exec(statement).first()

    def create(
        self,
        membership: Membership,
    ) -> Membership:
        self.session.add(membership)
        self.session.commit()
        self.session.refresh(membership)

        return membership

    def update(
        self,
        membership: Membership,
    ) -> Membership:
        self.session.add(membership)
        self.session.commit()
        self.session.refresh(membership)

        return membership

    def get_pending_for_member(
        self,
        member_id: int,
    ) -> Membership | None:
        statement = (
            select(Membership)
            .where(
                Membership.member_id == member_id,
                Membership.status == MembershipStatus.PENDING_PAYMENT,
            )
            .order_by(Membership.id.desc())
        )

        return self.session.exec(statement).first()

    def get_current_for_member(
        # Does this member already have an existing live membership, including one temporarily frozen?
        self,
        member_id: int,
    ) -> Membership | None:
        statement = (
            select(Membership)
            .where(
                Membership.member_id == member_id,
                Membership.status.in_(
                    [
                        MembershipStatus.ACTIVE,
                        MembershipStatus.FROZEN,
                    ]
                ),
            )
            .order_by(Membership.id.desc())
        )

        return self.session.exec(statement).first()

    def get_active_expiring_on(
        self,
        target_date: date,
    ) -> list[Membership]:
        statement = (
            select(Membership)
            .where(
                Membership.status == MembershipStatus.ACTIVE,
                Membership.end_date == target_date,
            )
            .order_by(Membership.id)
        )

        return list(self.session.exec(statement).all())

    def get_active_expired_by(
        self,
        as_of_date: date,
    ) -> list[Membership]:
        statement = (
            select(Membership)
            .where(
                Membership.status == MembershipStatus.ACTIVE,
                Membership.end_date.is_not(None),
                Membership.end_date <= as_of_date,
            )
            .order_by(Membership.id)
        )

        return list(self.session.exec(statement).all())

    def add(
        self,
        membership: Membership,
    ) -> Membership:
        self.session.add(membership)

        return membership
