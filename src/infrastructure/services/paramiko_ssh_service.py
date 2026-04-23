import paramiko
from io import StringIO
from src.domain.ports.services.i_ssh_service import ISSHService


class ParamikoSshService(ISSHService):
    async def test_connection(
        self,
        host: str,
        port: int,
        username: str,
        private_key: str,
    ) -> bool:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        pkey = paramiko.RSAKey.from_private_key(StringIO(private_key))

        try:
            client.connect(
                hostname=host,
                port=port,
                username=username,
                pkey=pkey,
                timeout=10,
                banner_timeout=10,
                auth_timeout=10,
            )
            return True
        except Exception:
            return False
        finally:
            client.close()

    async def execute(
        self,
        host: str,
        port: int,
        username: str,
        private_key: str,
        command: str,
        cwd: str | None = None,
    ) -> tuple[int, str]:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        pkey = paramiko.RSAKey.from_private_key(StringIO(private_key))

        full_command = command if cwd is None else f"cd {cwd} && {command}"

        try:
            client.connect(
                hostname=host,
                port=port,
                username=username,
                pkey=pkey,
                timeout=15,
                banner_timeout=15,
                auth_timeout=15,
            )

            _stdin, stdout, stderr = client.exec_command(full_command, timeout=300)
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode("utf-8") + stderr.read().decode("utf-8")

            return exit_code, output.strip()
        finally:
            client.close()


# Backward-compatible alias used in tests and dependency providers.
ParamikoSSHService = ParamikoSshService
