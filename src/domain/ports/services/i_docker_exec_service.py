from abc import ABC, abstractmethod


class IDockerExecService(ABC):
    """Executa comandos em container Docker local (mesmo host do processo da API)."""

    @abstractmethod
    async def test_container(self, container: str) -> bool:
        """Verifica se o container existe e está em execução."""

    @abstractmethod
    async def execute(
        self,
        container: str,
        username: str | None,
        command: str,
        cwd: str | None,
        timeout_seconds: int,
    ) -> tuple[int, str]:
        """Executa `command` via shell no container; retorna (exit_code, log)."""
