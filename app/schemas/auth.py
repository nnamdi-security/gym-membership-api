from pydantic import BaseModel, Emailstr, Field, ConfigDict


class UserRegisterRequest(BaseModel):
    email: Emailstr
    password: str = Field(min_length=8, max_length=128)


class UserLoginRequest(BaseModel):
    email: Emailstr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: Emailstr
    role: str

    class config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
