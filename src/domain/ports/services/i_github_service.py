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

    @abstractmethod
    async def search_repositories(
        self, access_token: str, query: str, page: int, per_page: int
    ) -> tuple[list[str], int]: ...

    @abstractmethod
    async def search_refs(
        self, access_token: str, repository: str, query: str, limit: int
    ) -> tuple[list[str], list[str]]: ...
