from abc import ABC, abstractmethod


class IGitHubService(ABC):
    @abstractmethod
    def build_authorization_url(self, state: str) -> str: ...

    @abstractmethod
    async def exchange_code_for_token(self, code: str) -> tuple[str, str]: ...

    @abstractmethod
    async def list_repositories(self, access_token: str) -> list[str]: ...

    @abstractmethod
    async def list_branches(self, repository: str, access_token: str) -> list[str]: ...

    @abstractmethod
    async def list_tags(self, repository: str, access_token: str) -> list[str]: ...

    @abstractmethod
    async def ref_exists(
        self, repository: str, ref_name: str, access_token: str
    ) -> bool: ...
