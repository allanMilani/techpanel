from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True, frozen=True)
class LoginInputDTO:
    email: str
    password: str


@dataclass(slots=True, frozen=True)
class LoginOutputDTO:
    access_token: str
    token_type: str
    user_id: UUID
    role: str
