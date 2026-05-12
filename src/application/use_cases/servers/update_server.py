from uuid import UUID

from src.application import NotFoundAppError, ValidationAppError
from src.application.constants import LOCAL_DOCKER_SSH_KEY_PLACEHOLDER
from src.application.dtos import ServerOutputDTO, UpdateServerInputDTO
from src.domain.entities.server import Server, normalize_docker_container_ref
from src.domain.errors import ValidationError
from src.domain.ports.repositories import IServerRepository
from src.domain.ports.services.i_key_cipher import IKeyCipher
from src.domain.value_objects.server_connection_kind import ServerConnectionKind


class UpdateServer:
    def __init__(self, server_repo: IServerRepository, key_cipher: IKeyCipher) -> None:
        self.server_repo = server_repo
        self.key_cipher = key_cipher

    async def execute(
        self, server_id: UUID, dto: UpdateServerInputDTO
    ) -> ServerOutputDTO:
        existing = await self.server_repo.get_by_id(server_id)
        if existing is None:
            raise NotFoundAppError("Server not found")

        try:
            kind = ServerConnectionKind(dto.connection_kind)
        except ValueError as e:
            raise ValidationAppError("Tipo de conexão inválido.") from e

        if kind == ServerConnectionKind.SSH:
            docker_name = None
        else:
            docker_name = normalize_docker_container_ref(dto.docker_container_name) or None

        plain = (dto.private_key_plain or "").strip()
        if (
            kind == ServerConnectionKind.SSH
            and existing.connection_kind == ServerConnectionKind.LOCAL_DOCKER
            and not plain
        ):
            raise ValidationAppError(
                "Informe a chave privada SSH ao sair do modo Docker local."
            )

        if kind == ServerConnectionKind.SSH:
            if plain:
                try:
                    encrypted_key = self.key_cipher.encrypt(plain)
                except UnicodeEncodeError as e:
                    raise ValidationAppError(
                        "A chave privada contém caracteres inválidos para UTF-8. "
                        "Cole o PEM em texto puro (ASCII), sem BOM nem caracteres especiais."
                    ) from e
            else:
                encrypted_key = existing.private_key_enc
        elif existing.connection_kind == ServerConnectionKind.LOCAL_DOCKER:
            encrypted_key = existing.private_key_enc
        else:
            encrypted_key = self.key_cipher.encrypt(LOCAL_DOCKER_SSH_KEY_PLACEHOLDER)

        try:
            Server._validate(
                name=dto.name,
                host=dto.host,
                port=dto.port,
                ssh_user=dto.ssh_user,
                private_key_enc=encrypted_key,
                connection_kind=kind,
                docker_container_name=docker_name,
            )
        except ValidationError as e:
            raise ValidationAppError(str(e)) from e

        updated = Server(
            id=existing.id,
            name=dto.name.strip(),
            host=dto.host.strip(),
            port=dto.port,
            ssh_user=dto.ssh_user.strip(),
            private_key_enc=encrypted_key,
            created_by=existing.created_by,
            connection_kind=kind,
            docker_container_name=docker_name,
            ssh_strict_host_key_checking=(
                dto.ssh_strict_host_key_checking
                if kind == ServerConnectionKind.SSH
                else False
            ),
            project_directory=(dto.project_directory or "").strip() or None,
        )

        persisted = await self.server_repo.update(updated)

        return ServerOutputDTO(
            id=persisted.id,
            name=persisted.name,
            host=persisted.host,
            port=persisted.port,
            ssh_user=persisted.ssh_user,
            created_by=persisted.created_by,
            connection_kind=persisted.connection_kind.value,
            docker_container_name=persisted.docker_container_name,
            ssh_strict_host_key_checking=persisted.ssh_strict_host_key_checking,
            project_directory=persisted.project_directory,
        )
