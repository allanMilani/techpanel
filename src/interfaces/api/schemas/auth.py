from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    role: str


class MeResponse(BaseModel):
    user_id: str
    role: str
    display_name: str | None = None
    has_github_token: bool = False


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = Field(default=None, max_length=255)


class RegisterResponse(BaseModel):
    user_id: str
    email: str
    role: str
