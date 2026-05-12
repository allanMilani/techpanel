from __future__ import annotations

import asyncio
import shlex
import time
from dataclasses import dataclass
from uuid import UUID

from src.domain.entities.server import (
    is_valid_docker_container_ref,
    normalize_docker_container_ref,
)
from src.domain.ports.services.i_docker_exec_service import IDockerExecService
from src.infrastructure.services.shell_command_with_exit_marker import (
    build_sh_line,
    new_exit_marker,
    parse_marker_tail,
)


def assert_safe_container_name(container: str) -> None:
    if not is_valid_docker_container_ref(normalize_docker_container_ref(container)):
        raise ValueError("Identificador do container Docker inválido.")


@dataclass
class _DockerPipelineShell:
    container: str
    username: str | None
    proc: asyncio.subprocess.Process
    lock: asyncio.Lock


async def _drain_startup_output(
    proc: asyncio.subprocess.Process, *, max_wall: float = 2.5, max_bytes: int = 65536
) -> None:
    if proc.stdout is None:
        return
    drained = 0
    end = time.monotonic() + max_wall
    while time.monotonic() < end and drained < max_bytes:
        try:
            chunk = await asyncio.wait_for(proc.stdout.read(8192), timeout=0.35)
        except TimeoutError:
            chunk = b""
        if not chunk:
            await asyncio.sleep(0.04)
            continue
        drained += len(chunk)


async def _async_recv_until_marker(
    stdout: asyncio.StreamReader, marker: str, timeout_seconds: int
) -> tuple[bytes, bool]:
    buf = b""
    marker_b = marker.encode("utf-8")
    end = time.monotonic() + max(1, timeout_seconds)
    max_buf = 10 * 1024 * 1024
    while time.monotonic() < end and len(buf) < max_buf:
        try:
            chunk = await asyncio.wait_for(stdout.read(65536), timeout=1.0)
        except TimeoutError:
            if marker_b in buf:
                return buf, True
            continue
        if chunk:
            buf += chunk
            if marker_b in buf:
                return buf, True
        else:
            await asyncio.sleep(0.02)
    return buf, marker_b in buf


async def _async_shell_run_line(
    sess: _DockerPipelineShell,
    *,
    cwd: str | None,
    command: str,
    timeout_seconds: int,
) -> tuple[int, str]:
    marker = new_exit_marker()
    line = build_sh_line(command, cwd, marker)
    proc = sess.proc
    if proc.stdin is None or proc.stdout is None:
        return 1, "Sessão Docker sem stdin/stdout."
    async with sess.lock:
        if proc.returncode is not None:
            return 1, "Processo shell do container terminou inesperadamente."
        proc.stdin.write(line.encode("utf-8"))
        await proc.stdin.drain()
        raw, ok = await _async_recv_until_marker(proc.stdout, marker, timeout_seconds)
    text = raw.decode("utf-8", errors="replace")
    if not ok:
        return 124, (text.strip() + "\n(timeout: marcador de fim não recebido)").strip()
    code, visible = parse_marker_tail(text, marker)
    return code, visible


class DockerCliExecService(IDockerExecService):
    """Implementação usando o binário `docker` do PATH (CLI)."""

    def __init__(self) -> None:
        self._shell_sessions: dict[UUID, _DockerPipelineShell] = {}
        self._shell_sessions_lock = asyncio.Lock()

    async def test_container(self, container: str) -> bool:
        """Confere se o container aceita `docker exec` como nas execuções de pipeline."""
        name = normalize_docker_container_ref(container)
        if not name or not is_valid_docker_container_ref(name):
            return False
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker",
                "exec",
                name,
                "sh",
                "-c",
                "true",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except FileNotFoundError:
            return False
        try:
            await asyncio.wait_for(proc.wait(), timeout=15)
        except TimeoutError:
            proc.kill()
            return False
        return proc.returncode == 0

    async def _async_connect_shell(
        self,
        *,
        container: str,
        username: str | None,
        initial_working_directory: str | None,
    ) -> _DockerPipelineShell:
        name = normalize_docker_container_ref(container)
        assert_safe_container_name(name)
        args: list[str] = ["docker", "exec", "-i"]
        if username and username.strip():
            args.extend(["-u", username.strip()])
        args.extend([name, "sh"])
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        if proc.stdin is None or proc.stdout is None:
            raise RuntimeError("docker exec não abriu stdin/stdout.")
        await _drain_startup_output(proc)
        init_lines = b"exec 2>&1\nstty -echo 2>/dev/null || true\n"
        proc.stdin.write(init_lines)
        await proc.stdin.drain()
        await _drain_startup_output(proc)
        iw = (initial_working_directory or "").strip()
        if iw:
            proc.stdin.write(f"cd {shlex.quote(iw)}\n".encode("utf-8"))
            await proc.stdin.drain()
            await _drain_startup_output(proc)
        return _DockerPipelineShell(
            container=name,
            username=username.strip() if username and username.strip() else None,
            proc=proc,
            lock=asyncio.Lock(),
        )

    async def _async_release_one(self, sess: _DockerPipelineShell | None) -> None:
        if sess is None:
            return
        async with sess.lock:
            proc = sess.proc
            if proc.stdin is not None and not proc.stdin.is_closing():
                try:
                    proc.stdin.write(b"exit 0\n")
                    await proc.stdin.drain()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    pass
                try:
                    proc.stdin.close()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    pass
            try:
                await asyncio.wait_for(proc.wait(), timeout=8)
            except TimeoutError:
                proc.kill()
                await proc.wait()

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
        name = normalize_docker_container_ref(container)
        try:
            assert_safe_container_name(name)
        except ValueError as e:
            return 1, str(e)

        if execution_id is None:
            return await self._execute_one_shot(
                name=name,
                username=username,
                command=command,
                cwd=cwd,
                timeout_seconds=timeout_seconds,
            )

        try:
            async with self._shell_sessions_lock:
                sess = self._shell_sessions.get(execution_id)
                if sess is None or sess.container != name:
                    if sess is not None:
                        old = self._shell_sessions.pop(execution_id, None)
                        await self._async_release_one(old)
                    sess = await self._async_connect_shell(
                        container=name,
                        username=username,
                        initial_working_directory=(
                            (pipeline_initial_directory or "").strip() or None
                        ),
                    )
                    self._shell_sessions[execution_id] = sess
            return await _async_shell_run_line(
                sess,
                cwd=cwd,
                command=command,
                timeout_seconds=timeout_seconds,
            )
        except TimeoutError:
            async with self._shell_sessions_lock:
                popped = self._shell_sessions.pop(execution_id, None)
            await self._async_release_one(popped)
            return (
                124,
                "Tempo esgotado à espera da resposta do container Docker (shell ou comando).",
            )
        except Exception as e:
            async with self._shell_sessions_lock:
                popped = self._shell_sessions.pop(execution_id, None)
            await self._async_release_one(popped)
            return 1, f"Erro na sessão Docker da execução: {type(e).__name__}: {str(e)[:400]}"

    async def _execute_one_shot(
        self,
        *,
        name: str,
        username: str | None,
        command: str,
        cwd: str | None,
        timeout_seconds: int,
    ) -> tuple[int, str]:
        args: list[str] = ["docker", "exec", "-i"]
        if cwd and cwd.strip():
            args.extend(["-w", cwd.strip()])
        if username and username.strip():
            args.extend(["-u", username.strip()])
        args.extend([name, "sh", "-c", command])
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            out, _ = await asyncio.wait_for(
                proc.communicate(),
                timeout=max(1, timeout_seconds),
            )
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return 124, "Timeout ao executar docker exec."
        raw = (out or b"").decode("utf-8", errors="replace").strip()
        code = proc.returncode if proc.returncode is not None else 1
        return code, raw

    async def release_pipeline_session(self, execution_id: UUID) -> None:
        async with self._shell_sessions_lock:
            sess = self._shell_sessions.pop(execution_id, None)
        await self._async_release_one(sess)
