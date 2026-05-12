from src.application import ValidationAppError
from src.application.constants import LOCAL_DOCKER_SSH_KEY_PLACEHOLDER
from src.application.dtos import CreateServerInputDTO, ServerOutputDTO
from src.domain.entities.server import Server
from src.domain.errors import ValidationError
from src.domain.ports.repositories import IServerRepository
from src.domain.value_objects.server_connection_kind import ServerConnectionKind


class CreateServer:
    def __init__(self, server_repo: IServerRepository, key_cipher) -> None:
        self.server_repo = server_repo
        self.key_cipher = key_cipher

    async def execute(self, dto: CreateServerInputDTO) -> ServerOutputDTO:
        try:
            kind = ServerConnectionKind(dto.connection_kind)
        except ValueError as e:
            raise ValidationAppError("Tipo de conexão inválido.") from e

        if kind == ServerConnectionKind.SSH:
            plain = (dto.private_key_plain or "").strip()
            if not plain:
                raise ValidationAppError(
                    "Chave privada é obrigatória para conexão SSH."
                )
            try:
                encrypted_key = self.key_cipher.encrypt(plain)
            except UnicodeEncodeError as e:
                raise ValidationAppError(
                    "A chave privada contém caracteres inválidos para UTF-8. "
                    "Cole o PEM em texto puro (ASCII), sem BOM nem caracteres especiais."
                ) from e
        else:
            if not (dto.docker_container_name or "").strip():
                raise ValidationAppError(
                    "Informe o identificador do container (nome ou ID) no modo Docker local."
                )
            encrypted_key = self.key_cipher.encrypt(LOCAL_DOCKER_SSH_KEY_PLACEHOLDER)

        try:
            server = Server.create(
                name=dto.name,
                host=dto.host,
                port=dto.port,
                ssh_user=dto.ssh_user,
                private_key_enc=encrypted_key,
                created_by=dto.created_by,
                connection_kind=kind,
                docker_container_name=dto.docker_container_name,
                ssh_strict_host_key_checking=dto.ssh_strict_host_key_checking,
                project_directory=dto.project_directory,
            )
        except ValidationError as e:
            raise ValidationAppError(str(e)) from e

        server = await self.server_repo.create(server)

        return ServerOutputDTO(
            id=server.id,
            name=server.name,
            host=server.host,
            port=server.port,
            ssh_user=server.ssh_user,
            created_by=server.created_by,
            connection_kind=server.connection_kind.value,
            docker_container_name=server.docker_container_name,
            ssh_strict_host_key_checking=server.ssh_strict_host_key_checking,
            project_directory=server.project_directory,
        )
