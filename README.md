# TechPanel

Painel interno para orquestrar deploys com pipelines sequenciais, auditoria e execucao remota segura.

## Pre-requisitos

- Python 3.12+
- `uv` instalado
- Docker + Docker Compose

## Configuracao inicial

1. Copie as variaveis de ambiente:
   - `cp .env.example .env`
2. Sincronize dependencias:
   - `make sync`
3. Suba o banco local:
   - `make db-up`
4. Aplique migracoes:
   - `make migrate`

## Executar a API

- `make run`

Endpoints de verificacao:

- `GET /health`
- `GET /health/db`

## Comandos principais

- `make sync` - sincroniza dependencias com `pyproject.toml` e `uv.lock`
- `make db-up` - sobe PostgreSQL local
- `make migrate` - aplica migracoes Alembic ate `head`
- `make run` - sobe API com autoreload
- `make lint` - executa Ruff
- `make test` - executa testes com Pytest
