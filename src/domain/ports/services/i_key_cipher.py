from abc import ABC, abstractmethod


class IKeyCipher(ABC):
    @abstractmethod
    def encrypt(self, plain_text: str) -> str: ...

    @abstractmethod
    def decrypt(self, cipher_text: str) -> str: ...
