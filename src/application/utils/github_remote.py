"""Extrai `owner/repo` do GitHub a partir da URL do remoto `origin`."""

from __future__ import annotations

import re
from urllib.parse import urlparse


def parse_github_owner_repo_from_remote_url(raw: str) -> str | None:
    """Aceita saída típica de `git remote get-url origin` apontando para GitHub.com."""
    lines = (raw or "").strip().splitlines()
    s = lines[0].strip() if lines else ""
    if not s:
        return None

    ssh_short = re.match(
        r"^git@github\.com:(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?$",
        s,
        re.IGNORECASE,
    )
    if ssh_short:
        return f"{ssh_short.group('owner')}/{ssh_short.group('repo')}"

    ssh_url = re.match(
        r"^ssh://git@github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$",
        s,
        re.IGNORECASE,
    )
    if ssh_url:
        return f"{ssh_url.group('owner')}/{ssh_url.group('repo')}"

    if "github.com" not in s.lower():
        return None

    url = s if s.startswith(("http://", "https://")) else f"https://{s.lstrip('/')}"
    try:
        parsed = urlparse(url)
    except ValueError:
        return None

    host = (parsed.hostname or "").lower()
    if host not in ("github.com", "www.github.com"):
        return None

    path = (parsed.path or "").strip("/")
    if not path:
        return None
    parts = path.split("/")
    if len(parts) < 2:
        return None
    owner, repo = parts[0], parts[1]
    repo = repo.removesuffix(".git")
    if owner and repo:
        return f"{owner}/{repo}"
    return None
