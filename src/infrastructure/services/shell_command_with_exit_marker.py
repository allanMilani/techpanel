"""Linha de comando em shell com marcador de exit code (pipelines com sessão persistente)."""

from __future__ import annotations

import re
import shlex
import uuid


def new_exit_marker() -> str:
    return f"__TP_EXIT_{uuid.uuid4().hex}__"


def build_sh_line(command: str, cwd: str | None, marker: str) -> str:
    """Comando + printf do marcador e de $? (POSIX sh)."""
    mq = shlex.quote(marker)
    inner = (command or "").strip() or "true"
    cwd_s = (cwd or "").strip()
    if cwd_s:
        return f"cd {shlex.quote(cwd_s)} && {inner}; printf '\\n%s %s\\n' {mq} \"$?\"\n"
    return f"{inner}; printf '\\n%s %s\\n' {mq} \"$?\"\n"


def parse_marker_tail(text: str, marker: str) -> tuple[int, str]:
    """Extrai exit code da última linha com marker; devolve texto sem essa linha final."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.splitlines()
    exit_code = 1
    cut = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        m = re.match(rf"^{re.escape(marker)}\s+(\d+)\s*$", lines[i].strip())
        if m:
            exit_code = int(m.group(1))
            cut = i
            break
    visible = "\n".join(lines[:cut])
    return exit_code, visible
