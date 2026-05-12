import asyncio
import logging
import shlex
import threading
import time
from dataclasses import dataclass
from io import StringIO
from uuid import UUID

import paramiko
from paramiko.ssh_exception import SSHException

from src.domain.ports.services.i_ssh_service import ISSHService
from src.infrastructure.services.shell_command_with_exit_marker import (
    build_sh_line,
    new_exit_marker,
    parse_marker_tail,
)

logger = logging.getLogger(__name__)


def _remote_exec_command(command: str, cwd: str | None) -> str:
    """Comando remoto único: bash -lc com cwd opcional (cada exec é sessão nova)."""
    inner = (command or "").strip() or "true"
    cwd_s = (cwd or "").strip()
    if cwd_s:
        inner = f"cd {shlex.quote(cwd_s)} && {inner}"
    return f"bash -lc {shlex.quote(inner)}"


def _normalize_private_key_pem(raw: str) -> str:
    """Remove BOM / zero-width, unifica fim de linha (PEM exige newlines correctos)."""
    t = (raw or "").replace("\ufeff", "").replace("\u200b", "")
    t = t.replace("\r\n", "\n").replace("\r", "\n").strip()
    return t


def _load_private_key(private_key: str, password: str | None = None) -> paramiko.PKey:
    """Carrega PEM / OpenSSH (RSA, Ed25519 ou ECDSA)."""
    data = _normalize_private_key_pem(private_key)
    if not data:
        raise SSHException("empty private key")
    file_obj = StringIO(data)
    key_classes: tuple[type[paramiko.PKey], ...] = (
        paramiko.RSAKey,
        paramiko.Ed25519Key,
        paramiko.ECDSAKey,
    )
    for key_cls in key_classes:
        file_obj.seek(0)
        try:
            return key_cls.from_private_key(file_obj, password=password)
        except (SSHException, ValueError):
            continue
    raise SSHException(
        "Chave privada não reconhecida. Use PEM ou OpenSSH: RSA, ECDSA ou Ed25519."
    )


def _configure_host_key_policy(
    client: paramiko.SSHClient, *, strict_host_key_checking: bool
) -> None:
    if strict_host_key_checking:
        try:
            client.load_system_host_keys()
        except OSError:
            pass
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
    else:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())


def _ssh_test_error_fields(exc: BaseException) -> tuple[str, str]:
    """Código estável para API + detalhe (truncado)."""
    cls = type(exc).__name__
    msg = str(exc).strip() or cls
    if len(msg) > 480:
        msg = msg[:477] + "..."
    if isinstance(exc, OSError) and getattr(exc, "errno", None) is not None:
        code = f"OS_ERRNO_{exc.errno}"
    else:
        code = cls
    return code, msg


def _sync_exec_one_shot(
    *,
    pkey: paramiko.PKey,
    host: str,
    port: int,
    username: str,
    full_command: str,
    strict_host_key_checking: bool,
    timeout_seconds: int,
) -> tuple[int, str]:
    client = paramiko.SSHClient()
    _configure_host_key_policy(client, strict_host_key_checking=strict_host_key_checking)
    try:
        client.connect(
            hostname=host,
            port=port,
            username=username,
            pkey=pkey,
            allow_agent=False,
            look_for_keys=False,
            timeout=15,
            banner_timeout=15,
            auth_timeout=15,
        )
        _stdin, stdout, stderr = client.exec_command(
            full_command, timeout=max(1, timeout_seconds)
        )
        out_bytes = stdout.read()
        err_bytes = stderr.read()
        exit_code = stdout.channel.recv_exit_status()
        output = out_bytes.decode("utf-8", errors="replace") + err_bytes.decode(
            "utf-8", errors="replace"
        )
        return exit_code, output.strip()
    finally:
        client.close()


@dataclass
class _PipelineShellSession:
    client: paramiko.SSHClient
    channel: paramiko.Channel
    lock: threading.Lock


def _drain_shell_welcome(channel: paramiko.Channel) -> None:
    channel.settimeout(0.35)
    deadline = time.monotonic() + 2.5
    drained = 0
    while time.monotonic() < deadline and drained < 65536:
        try:
            if channel.recv_ready():
                chunk = channel.recv(8192)
                drained += len(chunk)
                continue
        except (TimeoutError, OSError, EOFError):
            break
        time.sleep(0.04)


def _recv_until_marker(
    channel: paramiko.Channel, marker: str, timeout_seconds: int
) -> tuple[bytes, bool]:
    channel.settimeout(1.0)
    buf = b""
    marker_b = marker.encode("utf-8")
    end = time.monotonic() + max(1, timeout_seconds)
    max_buf = 10 * 1024 * 1024
    while time.monotonic() < end and len(buf) < max_buf:
        try:
            chunk = channel.recv(65536)
            if chunk:
                buf += chunk
                if marker_b in buf:
                    return buf, True
            else:
                time.sleep(0.02)
        except TimeoutError:
            if marker_b in buf:
                return buf, True
            continue
        except OSError:
            break
        except EOFError:
            break
    return buf, marker_b in buf


def _sync_shell_run_line(
    session: _PipelineShellSession,
    *,
    cwd: str | None,
    command: str,
    timeout_seconds: int,
) -> tuple[int, str]:
    marker = new_exit_marker()
    line = build_sh_line(command, cwd, marker)

    with session.lock:
        session.channel.send(line.encode("utf-8"))
        raw, ok = _recv_until_marker(session.channel, marker, timeout_seconds)
    text = raw.decode("utf-8", errors="replace")
    if not ok:
        return 124, (text.strip() + "\n(timeout: marcador de fim não recebido)").strip()
    code, visible = parse_marker_tail(text, marker)
    return code, visible


def _sync_connect_shell_session(
    *,
    pkey: paramiko.PKey,
    host: str,
    port: int,
    username: str,
    strict_host_key_checking: bool,
    initial_working_directory: str | None = None,
) -> _PipelineShellSession:
    client = paramiko.SSHClient()
    try:
        _configure_host_key_policy(client, strict_host_key_checking=strict_host_key_checking)
        client.connect(
            hostname=host,
            port=port,
            username=username,
            pkey=pkey,
            allow_agent=False,
            look_for_keys=False,
            timeout=15,
            banner_timeout=15,
            auth_timeout=15,
        )
        channel = client.invoke_shell(term="dumb", width=200, height=64)
        _drain_shell_welcome(channel)
        # Desliga eco do PTY para a saída guardada coincidir com o que um comando imprime no terminal
        # (sem repetir a linha enviada com cd/printf/marcador).
        try:
            channel.send(b"stty -echo 2>/dev/null || true\n")
        except OSError:
            pass
        _drain_shell_welcome(channel)
        iw = (initial_working_directory or "").strip()
        if iw:
            try:
                channel.send(f"cd {shlex.quote(iw)}\n".encode("utf-8"))
            except OSError:
                pass
            _drain_shell_welcome(channel)
        return _PipelineShellSession(client=client, channel=channel, lock=threading.Lock())
    except Exception:
        try:
            client.close()
        except Exception:
            pass
        raise


def _sync_release_shell_session(sess: _PipelineShellSession | None) -> None:
    if sess is None:
        return
    try:
        try:
            sess.channel.close()
        except Exception:
            pass
        sess.client.close()
    except Exception:
        pass


class ParamikoSshService(ISSHService):
    """SSH via Paramiko. Com `execution_id`, reutiliza um shell interactivo por execução de pipeline."""

    def __init__(self) -> None:
        self._shell_sessions: dict[UUID, _PipelineShellSession] = {}
        self._shell_sessions_lock = threading.Lock()

    async def test_connection(
        self,
        host: str,
        port: int,
        username: str,
        private_key: str,
        *,
        strict_host_key_checking: bool = False,
    ) -> tuple[bool, str | None, str | None]:
        try:
            pkey = _load_private_key(private_key)
        except SSHException as e:
            detail = (str(e).strip() or "invalid private key")[:480]
            logger.warning(
                "ssh_test_connection key_parse_failed host=%s port=%s user=%s strict_host_keys=%s "
                "error_code=PRIVATE_KEY_INVALID detail=%s",
                host,
                port,
                username,
                strict_host_key_checking,
                detail,
            )
            return False, "PRIVATE_KEY_INVALID", detail

        client = paramiko.SSHClient()
        _configure_host_key_policy(client, strict_host_key_checking=strict_host_key_checking)

        try:
            client.connect(
                hostname=host,
                port=port,
                username=username,
                pkey=pkey,
                allow_agent=False,
                look_for_keys=False,
                timeout=10,
                banner_timeout=10,
                auth_timeout=10,
            )
            return True, None, None
        except Exception as e:
            code, detail = _ssh_test_error_fields(e)
            logger.warning(
                "ssh_test_connection connect_failed host=%s port=%s user=%s strict_host_keys=%s "
                "error_code=%s detail=%s exc_type=%s",
                host,
                port,
                username,
                strict_host_key_checking,
                code,
                detail,
                type(e).__name__,
            )
            return False, code, detail
        finally:
            client.close()

    def _sync_execute_impl(
        self,
        *,
        host: str,
        port: int,
        username: str,
        private_key: str,
        command: str,
        cwd: str | None,
        strict_host_key_checking: bool,
        timeout_seconds: int,
        execution_id: UUID | None,
        pipeline_initial_directory: str | None,
    ) -> tuple[int, str]:
        try:
            pkey = _load_private_key(private_key)
        except SSHException:
            return (
                1,
                "Chave privada inválida ou tipo não suportado (RSA, ECDSA ou Ed25519 em PEM/OpenSSH).",
            )

        if execution_id is None:
            full_command = _remote_exec_command(command, cwd)
            return _sync_exec_one_shot(
                pkey=pkey,
                host=host,
                port=port,
                username=username,
                full_command=full_command,
                strict_host_key_checking=strict_host_key_checking,
                timeout_seconds=timeout_seconds,
            )

        try:
            with self._shell_sessions_lock:
                session = self._shell_sessions.get(execution_id)
                if session is None:
                    session = _sync_connect_shell_session(
                        pkey=pkey,
                        host=host,
                        port=port,
                        username=username,
                        strict_host_key_checking=strict_host_key_checking,
                        initial_working_directory=(
                            (pipeline_initial_directory or "").strip() or None
                        ),
                    )
                    self._shell_sessions[execution_id] = session
            return _sync_shell_run_line(
                session,
                cwd=cwd,
                command=command,
                timeout_seconds=timeout_seconds,
            )
        except TimeoutError:
            logger.warning(
                "ssh_pipeline_timeout execution_id=%s",
                execution_id,
            )
            with self._shell_sessions_lock:
                popped = self._shell_sessions.pop(execution_id, None)
            _sync_release_shell_session(popped)
            return (
                124,
                "Tempo esgotado à espera da resposta do servidor SSH (ligação, shell ou comando). "
                "Verifique rede, host, porto e credenciais.",
            )
        except Exception as e:
            logger.warning(
                "ssh_pipeline_shell_failed execution_id=%s error=%s",
                execution_id,
                type(e).__name__,
            )
            with self._shell_sessions_lock:
                popped = self._shell_sessions.pop(execution_id, None)
            _sync_release_shell_session(popped)
            return 1, f"Erro na sessão SSH da execução: {type(e).__name__}: {str(e)[:400]}"

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
        return await asyncio.to_thread(
            self._sync_execute_impl,
            host=host,
            port=port,
            username=username,
            private_key=private_key,
            command=command,
            cwd=cwd,
            strict_host_key_checking=strict_host_key_checking,
            timeout_seconds=timeout_seconds,
            execution_id=execution_id,
            pipeline_initial_directory=pipeline_initial_directory,
        )

    async def release_pipeline_session(self, execution_id: UUID) -> None:
        def _pop_and_close() -> None:
            with self._shell_sessions_lock:
                sess = self._shell_sessions.pop(execution_id, None)
            _sync_release_shell_session(sess)

        await asyncio.to_thread(_pop_and_close)


# Backward-compatible alias used in tests and dependency providers.
ParamikoSSHService = ParamikoSshService
