from abc import ABC, abstractmethod
from uuid import UUID


class ISSHService(ABC):
    @abstractmethod
    async def test_connection(
        self,
        host: str,
        port: int,
        username: str,
        private_key: str,
        *,
        strict_host_key_checking: bool = False,
    ) -> tuple[bool, str | None, str | None]:
        """Retorna (sucesso, código_erro_curto, mensagem_segura)."""

    @abstractmethod
    async def execute(
        self,
        host: str,
        port: int,
        username: str,
        private_key: str,
        command: str,
        cwd: str | None = None,
        *,
        strict_host_key_checking: bool = False,
        timeout_seconds: int = 300,
        execution_id: UUID | None = None,
        pipeline_initial_directory: str | None = None,
    ) -> tuple[int, str]:
        """Se ``execution_id`` for definido, reutiliza sessão shell persistente (pipelines).

        Com ``pipeline_initial_directory``, faz ``cd`` uma vez ao criar a sessão (base do ambiente),
        para ``cd`` nos comandos persistir entre passos sem repetir ``cd`` do ambiente em cada linha.
        """

    async def release_pipeline_session(self, execution_id: UUID) -> None:
        """Liberta sessão SSH persistente associada a uma execução de pipeline, se existir."""
        del execution_id
