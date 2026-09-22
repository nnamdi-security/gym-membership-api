from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.dependencies.auth import require_roles
from app.db.session import get_session
from app.models.payment import PaymentMethod
from app.models.user import User, UserRole
from app.repositories.membership_repository import MembershipRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.plan_repository import PlanRepository
from app.schemas.payment import PaymentResponse, StaffPaymentRequest
from app.services.payment_service import (
    InvalidStaffPaymentMethodError,
    MembershipAlreadyPaidError,
    MembershipNotAwaitingPaymentError,
    MembershipNotFoundError,
    PaymentNotFoundError,
    PaymentService,
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


# Service dependency
def get_payment_service(
    session: Session = SESSION_DEPENDENCY,
) -> PaymentService:
    payment_repository = PaymentRepository(session)
    membership_repository = MembershipRepository(session)
    plan_repository = PlanRepository(session)

    return PaymentService(
        session=session,
        payment_repository=payment_repository,
        membership_repository=membership_repository,
        plan_repository=plan_repository,
    )


PAYMENT_SERVICE_DEPENDENCY = Depends(
    get_payment_service
)




# Staff payment endpoint
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
        )

    except PlanNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership plan not found",
        )

    except MembershipNotAwaitingPaymentError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Membership is not awaiting payment",
        )

    except MembershipAlreadyPaidError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Membership has already been paid",
        )

    except InvalidStaffPaymentMethodError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "ONLINE is not a valid staff-recorded "
                "payment method"
            ),
        )


# Membership payment history
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
        )

# Staff/admin payment lookup/inspect
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
        )




