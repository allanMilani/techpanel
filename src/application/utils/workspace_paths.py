"""Caminho raiz do projeto no servidor (Git / .env)."""

from src.domain.entities.environment import Environment
from src.domain.entities.server import Server


def effective_project_root(server: Server, environment: Environment) -> str | None:
    pd = (getattr(server, "project_directory", None) or "").strip()
    if pd:
        return pd
    wd = (environment.working_directory or "").strip()
    return wd or None


def remote_dotenv_path(server: Server, environment: Environment) -> str | None:
    root = effective_project_root(server, environment)
    if not root:
        return None
    return f"{root.rstrip('/')}/.env"
