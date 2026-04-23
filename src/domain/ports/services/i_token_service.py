from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TokenPayload:
    sub: str
    role: str


class ITokenService(ABC):
    @abstractmethod
    def create_access_token(self, sub: str, role: str) -> str: ...

    @abstractmethod
    def decode_access_token(self, token: str) -> TokenPayload: ...
