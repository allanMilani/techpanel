from types import SimpleNamespace

import pytest

from src.infrastructure.security.fernet_key_cipher import FernetKeyCipher
from src.infrastructure.services.paramiko_ssh_service import ParamikoSSHService


def test_fernet_key_cipher_encrypt_decrypt_roundtrip() -> None:
    # Chave Fernet de teste (gerada previamente para fixture estável)
    key = "n6o_Ef9ZJq2f4hW-cWcLG3I8g4QxW2M_8SY2VvDdzfE="
    cipher = FernetKeyCipher(key)

    encrypted = cipher.encrypt("PRIVATE_KEY_CONTENT")
    decrypted = cipher.decrypt(encrypted)

    assert encrypted != "PRIVATE_KEY_CONTENT"
    assert decrypted == "PRIVATE_KEY_CONTENT"


@pytest.mark.asyncio
async def test_paramiko_ssh_service_test_connection(monkeypatch) -> None:
    class FakeClient:
        def set_missing_host_key_policy(self, _policy):
            return None

        def connect(self, **_kwargs):
            return None

        def close(self):
            return None

    monkeypatch.setattr(
        "src.infrastructure.services.paramiko_ssh_service.paramiko.SSHClient",
        lambda: FakeClient(),
    )
    monkeypatch.setattr(
        "src.infrastructure.services.paramiko_ssh_service.paramiko.RejectPolicy",
        lambda: object(),
    )
    monkeypatch.setattr(
        "src.infrastructure.services.paramiko_ssh_service.paramiko.RSAKey.from_private_key",
        lambda _stream: object(),
    )

    svc = ParamikoSSHService()
    ok = await svc.test_connection(
        host="127.0.0.1",
        port=22,
        username="ubuntu",
        private_key="-----BEGIN PRIVATE KEY-----\n...",
    )

    assert ok is True


@pytest.mark.asyncio
async def test_paramiko_ssh_service_execute(monkeypatch) -> None:
    class FakeStdout:
        def __init__(self):
            self.channel = SimpleNamespace(recv_exit_status=lambda: 0)

        def read(self):
            return b"ok"

    class FakeStderr:
        def read(self):
            return b""

    class FakeClient:
        def set_missing_host_key_policy(self, _policy):
            return None

        def connect(self, **_kwargs):
            return None

        def exec_command(self, _command, timeout):
            _ = timeout
            return None, FakeStdout(), FakeStderr()

        def close(self):
            return None

    monkeypatch.setattr(
        "src.infrastructure.services.paramiko_ssh_service.paramiko.SSHClient",
        lambda: FakeClient(),
    )
    monkeypatch.setattr(
        "src.infrastructure.services.paramiko_ssh_service.paramiko.RejectPolicy",
        lambda: object(),
    )
    monkeypatch.setattr(
        "src.infrastructure.services.paramiko_ssh_service.paramiko.RSAKey.from_private_key",
        lambda _stream: object(),
    )

    svc = ParamikoSSHService()
    code, output = await svc.execute(
        host="127.0.0.1",
        port=22,
        username="ubuntu",
        private_key="-----BEGIN PRIVATE KEY-----\n...",
        command="echo ok",
        cwd="/var/www",
    )

    assert code == 0
    assert output == "ok"
