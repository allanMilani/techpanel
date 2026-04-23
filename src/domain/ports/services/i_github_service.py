from abc import ABC, abstractmethod


class IGitHubService(ABC):
    @abstractmethod
    async def list_branches(self, repository: str) -> list[str]: ...

    @abstractmethod
    async def list_tags(self, repository: str) -> list[str]: ...

    @abstractmethod
    async def ref_exists(self, repository: str, ref_name: str) -> bool: ...
