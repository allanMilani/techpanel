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

.PHONY: help install-uv python-install init-env sync add run dev health health-db db-up db-down db-logs migrate downgrade revision history current test format lint check bootstrap frontend-install frontend-build frontend-dev

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

init-env: ## Cria .venv, sincroniza Python e instala/compila o frontend (se npm existir)
	uv venv --python $(PYTHON_VERSION)
	uv sync
	@command -v npm >/dev/null 2>&1 && $(MAKE) frontend-install && $(MAKE) frontend-build || (echo "Aviso: npm não encontrado. Instale Node.js e execute: make frontend-install && make frontend-build" >&2; true)

frontend-install: ## npm ci no diretório frontend/
	cd frontend && npm ci

frontend-build: ## Build de produção do Vue (saída em src/interfaces/static/dist)
	cd frontend && npm run build

frontend-dev: ## Vite dev server (proxy /api → porta $(PORT) do backend)
	cd frontend && VITE_API_PORT=$(PORT) npm run dev

sync: ## Sincroniza dependências com pyproject.toml/uv.lock
	uv sync

add: ## Adiciona pacote. Uso: make add PKG="httpx"
	@test -n "$(PKG)" || (echo "Uso: make add PKG=<pacote>" && exit 1)
	uv add $(PKG)

# ----------------------------
# App
# ----------------------------

run: ## Sobe API em modo dev (reload)
	uv run uvicorn $(APP_MODULE) --reload --reload-dir src --reload-dir tests --host $(HOST) --port $(PORT)

dev: ## Reinicia e sobe API + Vite (mata instâncias antigas do projeto antes)
	@echo "Reiniciando ambiente dev (backend :$(PORT), frontend :5173)..."
	@set -e; \
	BACKEND_OLD_PIDS=$$(ss -tlnp 2>/dev/null | awk -v p=":$(PORT)" '$$4 ~ p {print $$NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | sort -u); \
	FRONTEND_OLD_PIDS=$$(ss -tlnp 2>/dev/null | awk '$$4 ~ /:5173/ {print $$NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | sort -u); \
	if [ -n "$$BACKEND_OLD_PIDS$$FRONTEND_OLD_PIDS" ]; then \
		echo "Encerrando processos antigos..."; \
		kill $$BACKEND_OLD_PIDS $$FRONTEND_OLD_PIDS 2>/dev/null || true; \
		sleep 0.5; \
	fi; \
	echo "API http://$(HOST):$(PORT)  |  Vite http://localhost:5173 (proxy /api → $(PORT))"; \
	trap 'kill $$BACKEND_PID $$FRONTEND_PID 2>/dev/null; wait 2>/dev/null; exit 0' INT TERM; \
	uv run uvicorn $(APP_MODULE) --reload --reload-dir src --reload-dir tests --host $(HOST) --port $(PORT) & \
	BACKEND_PID=$$!; \
	cd frontend && VITE_API_PORT=$(PORT) npm run dev & \
	FRONTEND_PID=$$!; \
	wait

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

test:
	uv run pytest -q

format: ## Formata código (se ruff/black estiverem adicionados)
	uv run ruff format .

lint: ## Executa lint (se ruff estiver adicionado)
	make format && uv run ruff check .

check: lint test ## Executa validações principais

# ----------------------------
# Bootstrap completo
# ----------------------------

bootstrap: python-install init-env db-up migrate ## Setup inicial do projeto (inclui frontend se npm existir)
	@echo "Bootstrap concluído."