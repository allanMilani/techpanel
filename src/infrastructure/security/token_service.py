from datetime import UTC, datetime, timedelta

import jwt

from src.domain.ports.services import ITokenService, TokenPayload


class JwtTokenService(ITokenService):
    def __init__(
        self,
        secret_key: str,
        algorithm: str,
        expires_minutes: int,
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._expires_minutes = expires_minutes

    def create_access_token(self, sub: str, role: str) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": sub,
            "role": role,
            "exp": now + timedelta(minutes=self._expires_minutes),
        }

        return jwt.encode(payload, self._secret_key, self._algorithm)

    def decode_access_token(self, token: str) -> TokenPayload:
        payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])

        return TokenPayload(
            sub=str(payload["sub"]),
            role=str(payload["role"]),
        )
