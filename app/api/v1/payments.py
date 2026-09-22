from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.dependencies.auth import require_roles
from app.db.session import get_session
from app.models.user import User, UserRole
from app.repositories.membership_repository import MembershipRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.user import UserRepository
from app.schemas.payment import (
    OnlinePaymentInitializeRequest,
    OnlinePaymentInitializeResponse,
    PaymentResponse,
    StaffPaymentRequest,
)
from app.services.fake_payment_provider import FakePaymentProvider
from app.services.payment_service import (
    InvalidStaffPaymentMethodError,
    MembershipAlreadyPaidError,
    MembershipNotAwaitingPaymentError,
    MembershipNotFoundError,
    PaymentNotFoundError,
    PaymentService,
    PendingOnlinePaymentExistsError,
    PlanNotFoundError,
)


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


SESSION_DEPENDENCY = Depends(get_session)

STAFF_USER_DEPENDENCY = Depends(
    require_roles(
        UserRole.FRONT_DESK,
        UserRole.ADMIN,
    )
)

MEMBER_USER_DEPENDENCY = Depends(
    require_roles(UserRole.MEMBER)
)


def get_payment_service(
    session: Session = SESSION_DEPENDENCY,
) -> PaymentService:
    payment_repository = PaymentRepository(session)
    membership_repository = MembershipRepository(session)
    plan_repository = PlanRepository(session)
    user_repository = UserRepository(session)
    payment_provider = FakePaymentProvider()

    return PaymentService(
        session=session,
        payment_repository=payment_repository,
        membership_repository=membership_repository,
        plan_repository=plan_repository,
        user_repository=user_repository,
        payment_provider=payment_provider,
    )


PAYMENT_SERVICE_DEPENDENCY = Depends(
    get_payment_service
)


@router.post(
    "/staff",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a staff payment",
    description=(
        "Record a successful offline payment for a pending "
        "membership and activate the membership."
    ),
)
def record_staff_payment(
    data: StaffPaymentRequest,
    current_user: User = STAFF_USER_DEPENDENCY,
    service: PaymentService = PAYMENT_SERVICE_DEPENDENCY,
):
    try:
        return service.record_staff_payment(
            data=data,
            recorded_by=current_user.id,
        )

    except MembershipNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found",
        ) from None

    except PlanNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership plan not found",
        ) from None

    except MembershipNotAwaitingPaymentError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Membership is not awaiting payment",
        ) from None

    except MembershipAlreadyPaidError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Membership has already been paid",
        ) from None

    except InvalidStaffPaymentMethodError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "ONLINE is not a valid staff-recorded "
                "payment method"
            ),
        ) from None


@router.get(
    "/membership/{membership_id}",
    response_model=list[PaymentResponse],
    status_code=status.HTTP_200_OK,
    summary="List payments for a membership",
    dependencies=[STAFF_USER_DEPENDENCY],
)
def get_membership_payments(
    membership_id: int,
    service: PaymentService = PAYMENT_SERVICE_DEPENDENCY,
):
    try:
        return service.get_membership_payments(
            membership_id
        )

    except MembershipNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found",
        ) from None


@router.post(
    "/online/initialize",
    response_model=OnlinePaymentInitializeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize an online membership payment",
    description=(
        "Create a pending online payment for one of the "
        "authenticated member's pending memberships."
    ),
)
def initialize_online_payment(
    data: OnlinePaymentInitializeRequest,
    current_user: User = MEMBER_USER_DEPENDENCY,
    service: PaymentService = PAYMENT_SERVICE_DEPENDENCY,
):
    try:
        result = service.initialize_online_payment(
            membership_id=data.membership_id,
            member_id=current_user.id,
        )

        return OnlinePaymentInitializeResponse(
            payment=PaymentResponse.model_validate(
                result.payment
            ),
            checkout_url=result.checkout_url,
        )

    except MembershipNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found",
        ) from None

    except MembershipNotAwaitingPaymentError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Membership is not awaiting payment",
        ) from None

    except PendingOnlinePaymentExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A pending online payment already exists "
                "for this membership"
            ),
        ) from None

    except PlanNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership plan not found",
        ) from None


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a payment",
    dependencies=[STAFF_USER_DEPENDENCY],
)
def get_payment(
    payment_id: int,
    service: PaymentService = PAYMENT_SERVICE_DEPENDENCY,
):
    try:
        return service.get_payment(payment_id)

    except PaymentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        ) from None