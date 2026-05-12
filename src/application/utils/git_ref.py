"""Validação de refs Git usadas em shell remoto (evitar injeção)."""

import re

_SAFE_GIT_REF = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._/@^-]*$")


def is_safe_git_ref(value: str) -> bool:
    s = (value or "").strip()
    if not s or len(s) > 512:
        return False
    return bool(_SAFE_GIT_REF.fullmatch(s))
