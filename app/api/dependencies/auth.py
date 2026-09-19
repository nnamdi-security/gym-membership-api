from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlmodel import Session

from app.core.security import decode_access_token
from app.db.session import get_session
from app.models.user import User
from app.repositories.user import UserRepository


from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.models.user import User, UserRole


bearer_scheme = HTTPBearer(
    auto_error=False,
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    session: Session = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        user_id = int(subject)

    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    repository = UserRepository(session)

    user = repository.get_user_by_id(user_id)

    if user is None:
        raise credentials_exception

    return user



#Role-based authorization
def require_roles(
    *allowed_roles: UserRole,
) -> Callable:
    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return current_user

    return role_checker



#Authorization: Bearer <token>
#         ↓
# extract token
#         ↓
# decode JWT
#         ↓
# read sub claim
#         ↓
# load user from PostgreSQL
#         ↓
# return current User


# get_current_user extracts the bearer token, validates and decodes the JWT, reads the subject claim, loads the corresponding user from PostgreSQL, and returns that user to protected routes.