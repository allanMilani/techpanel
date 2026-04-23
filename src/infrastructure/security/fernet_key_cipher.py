from cryptography.fernet import Fernet, InvalidToken
from src.domain.ports.services.i_key_cipher import IKeyCipher


class FernetKeyCipher(IKeyCipher):
    def __init__(self, key: str) -> None:
        self._fernet = Fernet(key.encode("utf-8"))

    def encrypt(self, plain_text: str) -> str:
        token = self._fernet.encrypt(plain_text.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, cipher_text: str) -> str:
        try:
            raw = self._fernet.decrypt(cipher_text.encode("utf-8"))
            return raw.decode("utf-8")
        except InvalidToken as e:
            raise InvalidToken("Invalid encrypted private key") from e
