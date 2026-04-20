# Use bash for better script behavior
SHELL := /bin/bash

# Default goal
.DEFAULT_GOAL := help

# Variables
PYTHON_VERSION ?= 3.12
APP_MODULE ?= main:app
HOST ?= 0.0.0.0
PORT ?= 8000
ALEMBIC_MSG ?= "update schema"

.PHONY: help install-uv python-install init-env sync add run health health-db db-up db-down db-logs migrate downgrade revision history current test format lint check bootstrap

help: ## Lista os comandos disponíveis
	@echo "Comandos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# ----------------------------
# Environment / Dependencies
# ----------------------------

install-uv: ## Instala uv (uma vez na máquina)
	curl -LsSf https://astral.sh/uv/install.sh | sh

python-install: ## Instala Python gerenciado pelo uv
	uv python install $(PYTHON_VERSION)

init-env: ## Cria .venv e sincroniza dependências
	uv venv --python $(PYTHON_VERSION)
	uv sync

sync: ## Sincroniza dependências com pyproject.toml/uv.lock
	uv sync

add: ## Adiciona pacote. Uso: make add PKG="httpx"
	@test -n "$(PKG)" || (echo "Uso: make add PKG=<pacote>" && exit 1)
	uv add $(PKG)

# ----------------------------
# App
# ----------------------------

run: ## Sobe API em modo dev (reload)
	uv run uvicorn $(APP_MODULE) --reload --host $(HOST) --port $(PORT)

health: ## Testa health endpoint
	curl -fsS http://localhost:$(PORT)/health || true

health-db: ## Testa health endpoint de banco
	curl -fsS http://localhost:$(PORT)/health/db || true

# ----------------------------
# Database / Migrations
# ----------------------------

db-up: ## Sobe Postgres via docker compose
	docker compose up -d

db-down: ## Derruba containers do docker compose
	docker compose down

db-logs: ## Mostra logs do banco
	docker compose logs -f db

migrate: ## Aplica migrations até head
	uv run alembic upgrade head

downgrade: ## Reverte 1 migration
	uv run alembic downgrade -1

revision: ## Gera migration automaticamente. Uso: make revision ALEMBIC_MSG="init"
	uv run alembic revision --autogenerate -m $(ALEMBIC_MSG)

history: ## Mostra histórico de migrations
	uv run alembic history

current: ## Mostra revisão atual no banco
	uv run alembic current

# ----------------------------
# Quality / Tests
# ----------------------------

test: ## Executa testes
	uv run pytest -q

format: ## Formata código (se ruff/black estiverem adicionados)
	uv run ruff format .

lint: ## Executa lint (se ruff estiver adicionado)
	uv run ruff check .

check: lint test ## Executa validações principais

# ----------------------------
# Bootstrap completo
# ----------------------------

bootstrap: python-install init-env db-up migrate ## Setup inicial do projeto
	@echo "Bootstrap concluído."