import bcrypt

from src.domain.ports.services import IPasswordHasher


class BcryptPasswordHasher(IPasswordHasher):
    def hash(self, raw_password: str) -> str:
        return bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )

    def verify(self, raw_password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(
            raw_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
