from abc import ABC, abstractmethod
from uuid import UUID


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
        *,
        execution_id: UUID | None = None,
        pipeline_initial_directory: str | None = None,
    ) -> tuple[int, str]:
        """Executa `command` via shell no container; retorna (exit_code, log).

        Com ``execution_id``, reutiliza um processo ``sh`` persistente no mesmo container
        (pipelines), alinhado ao SSH: directório e estado do shell mantêm-se entre passos.
        Com ``pipeline_initial_directory``, faz ``cd`` ao criar essa sessão.
        """

    async def release_pipeline_session(self, execution_id: UUID) -> None:
        """Liberta sessão Docker persistente associada a uma execução de pipeline, se existir."""
        del execution_id
