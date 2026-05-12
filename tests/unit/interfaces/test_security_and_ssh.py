from types import SimpleNamespace

import paramiko
import pytest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.infrastructure.security.fernet_key_cipher import FernetKeyCipher
from src.infrastructure.services.paramiko_ssh_service import (
    ParamikoSSHService,
    _load_private_key,
    _remote_exec_command,
)
from src.infrastructure.services.shell_command_with_exit_marker import parse_marker_tail


def test_fernet_key_cipher_encrypt_decrypt_roundtrip() -> None:
    # Chave Fernet de teste (gerada previamente para fixture estável)
    key = "n6o_Ef9ZJq2f4hW-cWcLG3I8g4QxW2M_8SY2VvDdzfE="
    cipher = FernetKeyCipher(key)

    encrypted = cipher.encrypt("PRIVATE_KEY_CONTENT")
    decrypted = cipher.decrypt(encrypted)

    assert encrypted != "PRIVATE_KEY_CONTENT"
    assert decrypted == "PRIVATE_KEY_CONTENT"


def test_load_private_key_accepts_ed25519_openssh() -> None:
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pkey = _load_private_key(pem.decode())
    assert isinstance(pkey, paramiko.Ed25519Key)


def test_load_private_key_accepts_windows_line_endings() -> None:
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pem_crlf = pem.decode().replace("\n", "\r\n")
    pkey = _load_private_key(pem_crlf)
    assert isinstance(pkey, paramiko.Ed25519Key)


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
        "src.infrastructure.services.paramiko_ssh_service._load_private_key",
        lambda _k, password=None: object(),
    )

    svc = ParamikoSSHService()
    ok, err_code, err_detail = await svc.test_connection(
        host="127.0.0.1",
        port=22,
        username="ubuntu",
        private_key="-----BEGIN PRIVATE KEY-----\n...",
    )

    assert ok is True
    assert err_code is None
    assert err_detail is None


def test_remote_exec_command_quotes_cwd_and_wraps_bash() -> None:
    cmd = _remote_exec_command("echo ok", "/var/www")
    assert cmd.startswith("bash -lc ")
    assert "cd /var/www && echo ok" in cmd
    spaced = _remote_exec_command("ls", "/var/my app")
    assert "my app" in spaced


def test_parse_marker_tail_strips_exit_line_and_normalizes_crlf() -> None:
    m = "__TP_EXIT_abc__"
    code, visible = parse_marker_tail(f"line1\r\nline2\r\n{m} 0\r\n", m)
    assert code == 0
    assert visible == "line1\nline2"


def test_parse_marker_tail_preserves_leading_and_trailing_blank_lines() -> None:
    m = "__TP_EXIT_xyz__"
    raw = f"\n\nout\n\n\n{m} 1\n"
    code, visible = parse_marker_tail(raw, m)
    assert code == 1
    assert visible == "\n\nout\n\n"


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
        "src.infrastructure.services.paramiko_ssh_service._load_private_key",
        lambda _k, password=None: object(),
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
