from abc import ABC, abstractmethod


class ISSHService(ABC):
    @abstractmethod
    async def test_connection(
        self, host: str, port: int, username: str, private_key: str
    ) -> bool: ...

    @abstractmethod
    async def execute(
        self,
        host: str,
        port: int,
        username: str,
        private_key: str,
        command: str,
        cwd: str | None = None,
    ) -> tuple[int, str]: ...
