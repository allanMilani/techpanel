# TechPanel — Documentação técnica

> **Projeto (repositório):** TechPanel.  
> Gestor de ambientes para execução de deploys com pipeline de passos sequenciais, controle de acesso, histórico de auditoria e execução remota segura via SSH. Suporte inicial a PHP (backend) e Vue (frontend), extensível para novas tecnologias.

**Versão:** 2.0 — última atualização: 2025

---

## Sumário

1. [Visão geral](#1-visão-geral)
2. [Stack tecnológica](#2-stack-tecnológica)
3. [Arquitetura hexagonal](#3-arquitetura-hexagonal)
4. [Estrutura de pastas](#4-estrutura-de-pastas)
5. [Modelo de dados](#5-modelo-de-dados)
6. [Pipeline de deploy — conceito central](#6-pipeline-de-deploy--conceito-central)
7. [Tipos de passo disponíveis](#7-tipos-de-passo-disponíveis)
8. [Ambientes de deploy](#8-ambientes-de-deploy)
9. [Telas e fluxos de usuário](#9-telas-e-fluxos-de-usuário)
10. [Fluxos de execução](#10-fluxos-de-execução)
11. [Regras de negócio](#11-regras-de-negócio)
12. [Endpoints da API](#12-endpoints-da-api)
13. [Execução remota segura](#13-execução-remota-segura)
14. [Controle de concorrência (lock)](#14-controle-de-concorrência-lock)
15. [Status em tempo real](#15-status-em-tempo-real)
16. [Frontend — TechPanel](#16-frontend--techpanel)
17. [Critérios de aceite](#17-critérios-de-aceite)
18. [Dependências Python](#18-dependências-python)
19. [Decisões pendentes](#19-decisões-pendentes)

---

## 1. Visão geral

O TechPanel é um painel interno para equipes técnicas que permite a usuários autorizados:

- Cadastrar pipelines com passos sequenciais e configuráveis de deploy
- Executar pipelines com avanço automático apenas após conclusão bem-sucedida de cada passo
- Gerenciar múltiplos ambientes (produção, staging, etc.) com configurações independentes
- Acompanhar status por passo e logs em tempo real
- Consultar histórico completo de execuções com auditoria

O sistema conecta repositórios do GitHub a servidores via SSH. Suporte inicial a PHP e Vue, extensível para qualquer tecnologia via cadastro de passos customizados.

---

## 2. Stack tecnológica

| Camada | Tecnologia |
|---|---|
| Backend | Python + FastAPI |
| Frontend | HTMX + Jinja2 + Bootstrap 5 |
| Banco de dados | PostgreSQL 16 (dev e prod) |
| ORM | SQLAlchemy 2.x + Alembic |
| Execução remota | Paramiko (SSH) |
| Integração GitHub | PyGithub + OAuth |
| Autenticação | JWT via `python-jose` |
| Hash de senhas | `passlib[bcrypt]` |
| HTTP client | `httpx` |
| Criptografia em repouso | `cryptography` (Fernet) |

> PostgreSQL é utilizado tanto em desenvolvimento quanto em produção para garantir paridade de ambiente e evitar diferenças de comportamento entre SQLite e Postgres (tipos, constraints, transações).

---

## 3. Arquitetura hexagonal

O sistema segue a arquitetura hexagonal (Ports & Adapters), dividida em três camadas:

```
┌─────────────────────────────────────────────────────────┐
│                    INTERFACES (driving)                  │
│         FastAPI Routers · Templates HTMX/Jinja2          │
└────────────────────────┬────────────────────────────────┘
                         │ chama
┌────────────────────────▼────────────────────────────────┐
│                    APPLICATION                           │
│              Use Cases · DTOs · Orquestração             │
└───────┬──────────────────────────────────┬──────────────┘
        │ depende de (ports)               │ depende de (ports)
┌───────▼──────────┐              ┌────────▼──────────────┐
│     DOMAIN       │              │   INFRASTRUCTURE       │
│ Entities ·       │◄─────────────│ Repositories (PG) ·   │
│ Value Objects ·  │  implementa  │ SSH (Paramiko) ·       │
│ Ports (abstratos)│              │ GitHub (PyGithub)      │
└──────────────────┘              └───────────────────────┘
```

**Domain** — regras de negócio puras, sem dependências externas. Contém entidades (`Pipeline`, `PipelineStep`, `Execution`, etc.), value objects e as interfaces (ports) que definem contratos.

**Application** — orquestra os casos de uso. Chama os ports sem saber quem os implementa. É aqui que vive a lógica de "executar o próximo passo somente após o anterior concluir com sucesso".

**Infrastructure** — implementações concretas dos ports: repositórios PostgreSQL via SQLAlchemy, serviço SSH via Paramiko, integração GitHub via PyGithub.

**Interfaces** — adaptadores de entrada: routers FastAPI, templates Jinja2/HTMX. Convertem HTTP em chamadas aos use cases.

---

## 4. Estrutura de pastas

```
techpanel/
│
├── src/
│   │
│   ├── domain/                            # Núcleo — sem dependências externas
│   │   ├── entities/
│   │   │   ├── user.py
│   │   │   ├── server.py
│   │   │   ├── project.py
│   │   │   ├── environment.py             # Ambiente (prod, staging, etc.)
│   │   │   ├── pipeline.py                # Definição do pipeline
│   │   │   ├── pipeline_step.py           # Passo individual do pipeline
│   │   │   ├── execution.py               # Execução de um pipeline
│   │   │   └── step_execution.py          # Execução de um passo específico
│   │   │
│   │   ├── value_objects/
│   │   │   ├── execution_status.py        # pending/running/success/failed/skipped
│   │   │   ├── step_type.py               # ssh_command/http_check/notify
│   │   │   ├── on_failure_policy.py       # stop/continue/notify_and_stop
│   │   │   └── environment_type.py        # production/staging/custom
│   │   │
│   │   └── ports/                         # Interfaces (contratos abstratos)
│   │       ├── repositories/
│   │       │   ├── i_user_repository.py
│   │       │   ├── i_server_repository.py
│   │       │   ├── i_project_repository.py
│   │       │   ├── i_pipeline_repository.py
│   │       │   ├── i_execution_repository.py
│   │       │   └── i_step_execution_repository.py
│   │       └── services/
│   │           ├── i_ssh_service.py
│   │           ├── i_github_service.py
│   │           ├── i_step_runner.py       # Interface para runners de passo
│   │           └── i_notification_service.py
│   │
│   ├── application/                       # Casos de uso
│   │   ├── use_cases/
│   │   │   ├── auth/
│   │   │   │   ├── login.py
│   │   │   │   └── logout.py
│   │   │   ├── servers/
│   │   │   │   ├── create_server.py
│   │   │   │   ├── update_server.py
│   │   │   │   └── test_connection.py
│   │   │   ├── projects/
│   │   │   │   ├── create_project.py
│   │   │   │   └── link_environment.py
│   │   │   ├── pipelines/
│   │   │   │   ├── create_pipeline.py
│   │   │   │   ├── add_step.py
│   │   │   │   ├── reorder_steps.py
│   │   │   │   └── delete_pipeline.py
│   │   │   └── executions/
│   │   │       ├── start_execution.py     # Orquestra o pipeline inteiro
│   │   │       ├── run_next_step.py       # Avança ao próximo passo
│   │   │       ├── get_execution_logs.py
│   │   │       └── get_history.py
│   │   │
│   │   └── dtos/
│   │       ├── pipeline_dto.py
│   │       ├── pipeline_step_dto.py
│   │       ├── execution_dto.py
│   │       └── step_execution_dto.py
│   │
│   ├── infrastructure/                    # Adapters — lado dirigido
│   │   ├── persistence/
│   │   │   ├── database.py                # Engine PostgreSQL + sessão
│   │   │   ├── models/                    # SQLAlchemy ORM models
│   │   │   │   ├── user_model.py
│   │   │   │   ├── server_model.py
│   │   │   │   ├── project_model.py
│   │   │   │   ├── environment_model.py
│   │   │   │   ├── pipeline_model.py
│   │   │   │   ├── pipeline_step_model.py
│   │   │   │   ├── execution_model.py
│   │   │   │   └── step_execution_model.py
│   │   │   ├── repositories/              # Implementações dos ports
│   │   │   │   ├── pg_user_repository.py
│   │   │   │   ├── pg_server_repository.py
│   │   │   │   ├── pg_pipeline_repository.py
│   │   │   │   ├── pg_execution_repository.py
│   │   │   │   └── pg_step_execution_repository.py
│   │   │   └── migrations/                # Alembic
│   │   │       ├── env.py
│   │   │       └── versions/
│   │   │
│   │   ├── ssh/
│   │   │   └── paramiko_ssh_service.py    # Implementa i_ssh_service
│   │   │
│   │   ├── step_runners/                  # Implementações de IStepRunner
│   │   │   ├── ssh_command_runner.py      # Tipo: ssh_command
│   │   │   ├── http_healthcheck_runner.py # Tipo: http_healthcheck
│   │   │   ├── notify_webhook_runner.py   # Tipo: notify_webhook
│   │   │   └── runner_registry.py         # Mapa tipo → runner
│   │   │
│   │   ├── github/
│   │   │   └── pygithub_service.py        # Implementa i_github_service
│   │   │
│   │   └── notifications/
│   │       └── webhook_notification_service.py
│   │
│   └── interfaces/                        # Adapters — lado condutor
│       ├── api/
│       │   ├── routers/
│       │   │   ├── auth_router.py
│       │   │   ├── servers_router.py
│       │   │   ├── projects_router.py
│       │   │   ├── pipelines_router.py
│       │   │   └── executions_router.py
│       │   ├── middleware/
│       │   │   ├── auth_middleware.py
│       │   │   └── error_handler.py
│       │   └── dependencies.py            # Injeção de dependências FastAPI
│       │
│       └── web/
│           └── templates/
│               ├── base.html
│               ├── login.html
│               ├── servers/
│               ├── projects/
│               ├── pipelines/             # Cadastro e edição de pipelines
│               └── panel/                 # TechPanel — execução e histórico
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   └── application/
│   └── integration/
│       └── infrastructure/
│
├── main.py                                # Entrypoint FastAPI
├── requirements.txt
├── alembic.ini
├── docker-compose.yml                     # PostgreSQL local
└── .env.example
```

---

## 5. Modelo de dados

### `users`

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID PK | — |
| `email` | varchar | Login único |
| `password_hash` | varchar | Hash bcrypt |
| `role` | enum | `admin` / `viewer` |
| `is_active` | boolean | Permite desativar sem excluir |
| `created_at` | timestamptz | — |

### `servers`

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID PK | — |
| `name` | varchar | Nome amigável |
| `host` | varchar | IP ou hostname |
| `port` | int | Porta SSH (padrão 22) |
| `ssh_user` | varchar | Usuário SSH |
| `private_key_enc` | text | Chave privada criptografada (Fernet) |
| `created_by` | FK → users | — |
| `created_at` | timestamptz | — |

### `projects`

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID PK | — |
| `name` | varchar | Nome do projeto |
| `repo_github` | varchar | `owner/repo` |
| `tech_stack` | varchar | `php` / `vue` / `laravel` / extensível (texto livre) |
| `created_by` | FK → users | — |
| `created_at` | timestamptz | — |

### `environments`

Cada projeto pode ter múltiplos ambientes com servidores e diretórios independentes.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID PK | — |
| `project_id` | FK → projects | — |
| `name` | varchar | Ex: `production`, `staging`, `homologação` |
| `type` | enum | `production` / `staging` / `custom` |
| `server_id` | FK → servers | Servidor alvo deste ambiente |
| `working_directory` | varchar | Diretório base no servidor |
| `is_active` | boolean | — |

### `pipelines`

Um pipeline é uma sequência de passos associada a um ambiente específico.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID PK | — |
| `environment_id` | FK → environments | — |
| `name` | varchar | Ex: `Deploy Completo PHP + Vue` |
| `description` | text | — |
| `created_by` | FK → users | — |
| `created_at` | timestamptz | — |

### `pipeline_steps`

Cada passo é executado sequencialmente. O próximo só inicia após o anterior concluir com sucesso (ou com `on_failure=continue`).

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID PK | — |
| `pipeline_id` | FK → pipelines | — |
| `order` | int | Posição na sequência (1, 2, 3…) |
| `name` | varchar | Ex: `Rodar migrations`, `Build Vue` |
| `type` | varchar | `ssh_command` / `http_healthcheck` / `notify_webhook` |
| `command` | text | Comando ou URL dependendo do tipo |
| `working_directory` | varchar | Sobrescreve o diretório do ambiente se preenchido |
| `timeout_seconds` | int | Timeout (padrão 300s) |
| `on_failure` | enum | `stop` / `continue` / `notify_and_stop` |
| `is_active` | boolean | Passos inativos são ignorados na execução |

### `executions`

Registro de uma execução completa de um pipeline.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID PK | — |
| `pipeline_id` | FK → pipelines | — |
| `triggered_by` | FK → users | — |
| `branch_or_tag` | varchar | Ref selecionada no GitHub |
| `status` | enum | `pending` / `running` / `success` / `failed` / `blocked` |
| `started_at` | timestamptz | — |
| `finished_at` | timestamptz | — |
| `triggered_by_ip` | varchar | Auditoria |

### `step_executions`

Registro de cada passo dentro de uma execução. Permite visualizar progresso passo a passo.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID PK | — |
| `execution_id` | FK → executions | — |
| `pipeline_step_id` | FK → pipeline_steps | — |
| `order` | int | Cópia da ordem no momento da execução |
| `status` | enum | `pending` / `running` / `success` / `failed` / `skipped` |
| `log_output` | text | Log completo deste passo |
| `exit_code` | int | Código de saída |
| `started_at` | timestamptz | — |
| `finished_at` | timestamptz | — |

---

## 6. Pipeline de deploy — conceito central

O pipeline substitui os fluxos fixos (migration / deploy / deploy completo) por uma sequência de passos totalmente configurável pelo usuário.

### Princípio de execução sequencial

```
Passo 1 → [OK?] → Passo 2 → [OK?] → Passo 3 → ... → Concluído
              ↓                  ↓
           FALHA              FALHA
       on_failure=stop    on_failure=continue
       Interrompe         Avança ao próximo
       Passos restantes   Execução continua
       = skipped
```

O use case `run_next_step` é invocado ao final de cada passo:

```python
# application/use_cases/executions/run_next_step.py
class RunNextStep:
    def execute(self, execution_id: str):
        execution = self.execution_repo.get(execution_id)
        last = self.step_exec_repo.get_last(execution_id)

        if last and last.status == StepStatus.FAILED:
            policy = last.pipeline_step.on_failure
            if policy == OnFailurePolicy.STOP:
                self.execution_repo.mark_failed(execution_id)
                self.step_exec_repo.skip_remaining(execution_id)
                return
            if policy == OnFailurePolicy.NOTIFY_AND_STOP:
                self.notification_service.send(execution)
                self.execution_repo.mark_failed(execution_id)
                self.step_exec_repo.skip_remaining(execution_id)
                return
            # on_failure=continue: avança normalmente

        next_step = self.pipeline_repo.get_next_step(
            pipeline_id=execution.pipeline_id,
            after_order=last.order if last else 0
        )

        if next_step is None:
            self.execution_repo.mark_success(execution_id)
            return

        self._start_step(execution_id, next_step)

    def _start_step(self, execution_id, step):
        step_exec = self.step_exec_repo.mark_running(execution_id, step.id)
        runner = self.runner_registry.get(step.type)
        result = runner.run(step, ExecutionContext(execution_id, step_exec.id))
        self.step_exec_repo.complete(step_exec.id, result)
        self.execute(execution_id)  # recursão para o próximo passo
```

### Exemplo de pipeline — Deploy Completo (PHP + Vue)

| Ordem | Nome | Tipo | Comando | Em caso de falha |
|---|---|---|---|---|
| 1 | Git pull | `ssh_command` | `git -C /var/www/app pull origin main` | stop |
| 2 | Instalar deps PHP | `ssh_command` | `composer install --no-dev --optimize-autoloader` | stop |
| 3 | Rodar migrations | `ssh_command` | `php artisan migrate --force` | stop |
| 4 | Limpar cache | `ssh_command` | `php artisan config:cache && php artisan route:cache` | continue |
| 5 | Instalar deps Node | `ssh_command` | `npm ci --prefix /var/www/app/frontend` | stop |
| 6 | Build Vue | `ssh_command` | `npm run build --prefix /var/www/app/frontend` | stop |
| 7 | Reload PHP-FPM | `ssh_command` | `sudo systemctl reload php8.2-fpm` | notify_and_stop |

Se o passo 3 (migrations) falhar com `on_failure=stop`, os passos 4–7 ficam com `status=skipped` e a execução encerra como `failed`.

---

## 7. Tipos de passo disponíveis

O campo `type` define qual runner será utilizado. Novos tipos são adicionados implementando a interface `IStepRunner` e registrando no `RunnerRegistry` — sem alterar nenhuma outra parte do código.

```python
# domain/ports/services/i_step_runner.py
from abc import ABC, abstractmethod

class IStepRunner(ABC):
    @abstractmethod
    def run(self, step: PipelineStep, context: ExecutionContext) -> StepResult:
        ...
```

### Tipos implementados inicialmente

| Tipo | Descrição | Campo `command` |
|---|---|---|
| `ssh_command` | Executa comando no servidor via SSH | Comando shell |
| `http_healthcheck` | GET em URL e valida status HTTP 2xx | URL |
| `notify_webhook` | POST para webhook (Slack, Teams, etc.) | URL do webhook |

### Como adicionar novo tipo

```python
# infrastructure/step_runners/docker_compose_runner.py
class DockerComposeRunner(IStepRunner):
    def run(self, step, context) -> StepResult:
        conn = self.ssh_service.connect(context.server)
        result = conn.exec(f"docker compose up -d", cwd=step.working_directory)
        return StepResult(success=(result.exit_code == 0), log=result.log)

# infrastructure/step_runners/runner_registry.py
RUNNERS = {
    "ssh_command":        SshCommandRunner,
    "http_healthcheck":   HttpHealthcheckRunner,
    "notify_webhook":     NotifyWebhookRunner,
    "docker_compose":     DockerComposeRunner,  # novo tipo registrado aqui
}
```

---

## 8. Ambientes de deploy

Cada projeto pode ter múltiplos ambientes. O ambiente define qual servidor e diretório serão usados. O pipeline é sempre vinculado a um ambiente específico.

```
Projeto: e-commerce
├── Ambiente: production  (type=production)
│   ├── Servidor: srv-prod-01 (192.168.1.10)
│   ├── Diretório: /var/www/ecommerce
│   └── Pipeline: Deploy Completo Prod
│
└── Ambiente: staging  (type=staging)
    ├── Servidor: srv-stg-01 (192.168.1.20)
    ├── Diretório: /var/www/ecommerce-staging
    └── Pipeline: Deploy Completo Staging
```

### Regras por tipo de ambiente

| Regra | `staging` / `custom` | `production` |
|---|---|---|
| Confirmação modal | Padrão | Reforçada (digitar `CONFIRMAR`) |
| Badge visual | Azul/neutro | Vermelho persistente |
| Lock por projeto | Sim | Sim |
| Execução paralela | Não | Não |

---

## 9. Telas e fluxos de usuário

### Tela de login
Autenticação com email e senha. Gera token JWT armazenado em cookie HttpOnly seguro.

### Cadastro de servidores
Formulário com: nome, host, porta SSH, usuário e chave privada (upload de arquivo `.pem` ou textarea). Botão **Testar conexão** valida o acesso via Paramiko antes de salvar.

### Conexão com GitHub
Fluxo OAuth padrão. Após autorizar, sistema armazena token e lista repositórios disponíveis.

### Cadastro de projetos e ambientes
Formulário em duas etapas: primeiro cria o projeto (nome, repositório, tech stack), depois cadastra ambientes vinculando servidor e diretório. Múltiplos ambientes por projeto.

### Cadastro e edição de pipelines

Tela com lista de passos arrastável (drag-and-drop para reordenar). Para cada passo: nome, tipo, comando, diretório (opcional), timeout e política de falha.

```
Pipeline: Deploy Completo Prod
┌─────────────────────────────────────────────────────────────┐
│  ≡  1. Git pull              ssh_command   stop    [✎] [✕]  │
│  ≡  2. Composer install      ssh_command   stop    [✎] [✕]  │
│  ≡  3. Rodar migrations      ssh_command   stop    [✎] [✕]  │
│  ≡  4. Limpar cache          ssh_command   continue[✎] [✕]  │
│  ≡  5. npm install           ssh_command   stop    [✎] [✕]  │
│  ≡  6. npm run build         ssh_command   stop    [✎] [✕]  │
│  ≡  7. Reload php-fpm        ssh_command   notify  [✎] [✕]  │
└─────────────────────────────────────────────────────────────┘
[ + Adicionar passo ]                       [ Salvar pipeline ]
```

### TechPanel — painel de execução
Tela principal de execução, detalhada na seção 16.

---

## 10. Fluxos de execução

### Fluxo de execução de pipeline

1. Usuário seleciona: projeto → ambiente → pipeline → branch/tag
2. Clica em **Executar Pipeline**
3. Sistema exibe modal de confirmação (reforçada se ambiente for `production`)
4. Sistema verifica lock → `HTTP 409` se há execução ativa no projeto
5. Cria registro em `executions` com `status=running`
6. Cria registros em `step_executions` para todos os passos ativos com `status=pending`
7. Inicia Passo 1:
   - Atualiza `step_executions[1].status = running`
   - Executa via runner correspondente ao tipo do passo
   - Acumula log em tempo real no banco
   - Ao concluir: atualiza `status`, `exit_code`, `log_output`, `finished_at`
8. Invoca `run_next_step`:
   - Se passo falhou e `on_failure=stop` → encerra execução, marca restantes como `skipped`
   - Se passo falhou e `on_failure=continue` → avança para o próximo passo
   - Se passo falhou e `on_failure=notify_and_stop` → envia notificação, encerra
   - Se passo bem-sucedido → inicia passo seguinte
9. Ao esgotar todos os passos → `executions.status = success`
10. Registra `finished_at` na execução

### Fluxo de adição de passo ao pipeline

1. Usuário abre edição do pipeline
2. Clica em **+ Adicionar passo**
3. Preenche: nome, tipo, comando, diretório, timeout, política de falha
4. Novo passo é criado ao final da lista (maior `order` + 1)
5. Usuário pode reordenar arrastando; sistema atualiza `order` de todos os passos

---

## 11. Regras de negócio

- Apenas usuários `admin` podem disparar execuções, criar/editar pipelines, servidores e projetos
- Usuários `viewer` podem consultar histórico, status e logs, mas não executar ações nem editar configurações
- Toda execução gera registros em `executions` e `step_executions` com log completo e IP de origem
- O próximo passo só executa após conclusão do anterior — nunca em paralelo dentro de um mesmo pipeline
- Lock por projeto: não é possível iniciar nova execução enquanto houver `execution.status=running` para o mesmo `project_id`
- Ambientes `production` exigem confirmação textual (`CONFIRMAR`) antes da execução
- Chaves privadas SSH são armazenadas criptografadas com Fernet; a chave de criptografia fica exclusivamente no `.env`
- O painel nunca aceita comandos arbitrários de entrada — apenas executa os comandos previamente cadastrados nos `pipeline_steps`
- Passos com `is_active=false` são ignorados na execução mas mantidos no histórico
- Ao falhar com `stop` ou `notify_and_stop`, os passos restantes recebem `status=skipped`

---

## 12. Endpoints da API

### Autenticação

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/auth/login` | Retorna JWT |
| `POST` | `/auth/logout` | Invalida sessão |
| `GET` | `/auth/github` | Inicia OAuth GitHub |
| `GET` | `/auth/github/callback` | Callback OAuth |

### Servidores

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/servers` | Lista servidores |
| `POST` | `/api/servers` | Cadastra servidor |
| `POST` | `/api/servers/{id}/test` | Testa conexão SSH |
| `PUT` | `/api/servers/{id}` | Atualiza servidor |
| `DELETE` | `/api/servers/{id}` | Remove servidor |

### Projetos e ambientes

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/projects` | Lista projetos |
| `POST` | `/api/projects` | Cria projeto |
| `GET` | `/api/projects/{id}/environments` | Lista ambientes do projeto |
| `POST` | `/api/projects/{id}/environments` | Cadastra ambiente |
| `PUT` | `/api/projects/{id}/environments/{env_id}` | Atualiza ambiente |

### Pipelines

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/environments/{env_id}/pipelines` | Lista pipelines do ambiente |
| `POST` | `/api/environments/{env_id}/pipelines` | Cria pipeline |
| `GET` | `/api/pipelines/{id}` | Detalha pipeline com passos |
| `PUT` | `/api/pipelines/{id}` | Atualiza pipeline |
| `DELETE` | `/api/pipelines/{id}` | Remove pipeline |
| `POST` | `/api/pipelines/{id}/steps` | Adiciona passo |
| `PUT` | `/api/pipelines/{id}/steps/{step_id}` | Atualiza passo |
| `DELETE` | `/api/pipelines/{id}/steps/{step_id}` | Remove passo |
| `POST` | `/api/pipelines/{id}/steps/reorder` | Reordena passos |

### GitHub

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/github/repos` | Lista repositórios |
| `GET` | `/api/github/repos/{repo}/refs` | Lista branches e tags |

### Execuções (TechPanel)

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| `POST` | `/api/pipelines/{id}/execute` | admin | Dispara execução |
| `GET` | `/api/projects/{id}/active-execution` | admin/viewer | Execução ativa ou `null` |
| `GET` | `/api/executions/{id}` | admin/viewer | Detalha execução com status por passo |
| `GET` | `/api/executions/{id}/logs` | admin/viewer | Log consolidado |
| `GET` | `/api/executions/{id}/steps/{step_id}/logs` | admin/viewer | Log de um passo |
| `GET` | `/api/projects/{id}/history` | admin/viewer | Histórico paginado |

---

## 13. Execução remota segura

O painel executa exclusivamente os comandos cadastrados em `pipeline_steps.command`. Nenhuma string de shell é construída dinamicamente a partir de input do usuário.

### Interface do serviço SSH

```python
# domain/ports/services/i_ssh_service.py
from abc import ABC, abstractmethod

class ISshService(ABC):
    @abstractmethod
    def connect(self, server) -> "ISshConnection":
        ...

class ISshConnection(ABC):
    @abstractmethod
    def exec(self, command: str, cwd: str, timeout: int) -> "SshStream":
        ...
```

### Implementação com Paramiko

```python
# infrastructure/ssh/paramiko_ssh_service.py
import io, paramiko
from domain.ports.services.i_ssh_service import ISshService

class ParamikoSshService(ISshService):
    def connect(self, server) -> "ParamikoConnection":
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        pkey = paramiko.RSAKey.from_private_key(
            io.StringIO(decrypt_fernet(server.private_key_enc))
        )
        client.connect(
            hostname=server.host,
            port=server.port,
            username=server.ssh_user,
            pkey=pkey,
            timeout=10
        )
        return ParamikoConnection(client)

class ParamikoConnection:
    def exec(self, command: str, cwd: str, timeout: int):
        full_cmd = f"cd {cwd} && {command}" if cwd else command
        _, stdout, stderr = self._client.exec_command(full_cmd, timeout=timeout)
        for line in iter(stdout.readline, ""):
            yield ("stdout", line.rstrip())
        for line in iter(stderr.readline, ""):
            yield ("stderr", line.rstrip())
        self._exit_code = stdout.channel.recv_exit_status()
```

### Runner de passo SSH

```python
# infrastructure/step_runners/ssh_command_runner.py
class SshCommandRunner(IStepRunner):
    def run(self, step: PipelineStep, context: ExecutionContext) -> StepResult:
        server = self.server_repo.get(context.server_id)
        conn = self.ssh_service.connect(server)
        log_lines = []

        for stream, line in conn.exec(
            command=step.command,
            cwd=step.working_directory or context.working_directory,
            timeout=step.timeout_seconds
        ):
            log_lines.append(f"[{stream}] {line}")
            self.step_exec_repo.append_log(context.step_execution_id, line)

        return StepResult(
            success=(conn.exit_code == 0),
            exit_code=conn.exit_code,
            log="\n".join(log_lines)
        )
```

---

## 14. Controle de concorrência (lock)

Lock implementado no banco PostgreSQL — resistente a restart e a múltiplas instâncias do serviço:

```python
# application/use_cases/executions/start_execution.py
class StartExecution:
    def execute(self, pipeline_id: str, ref: str, user_id: str, ip: str):
        pipeline = self.pipeline_repo.get(pipeline_id)
        project_id = pipeline.environment.project_id

        active = self.execution_repo.find_running(project_id)
        if active:
            raise ExecutionAlreadyRunningError(active.id, active.started_at)

        execution = self.execution_repo.create(
            pipeline_id=pipeline_id,
            branch_or_tag=ref,
            triggered_by=user_id,
            triggered_by_ip=ip,
            status=ExecutionStatus.RUNNING
        )
        for step in pipeline.active_steps_ordered:
            self.step_exec_repo.create_pending(execution.id, step)

        return execution
```

Resposta HTTP em caso de conflito (`HTTP 409`):

```json
{
  "error": "execution_blocked",
  "message": "Já existe uma execução em andamento para este projeto.",
  "active_execution_id": "uuid-da-execucao-ativa",
  "started_at": "2025-01-15T14:32:00Z"
}
```

---

## 15. Status em tempo real

### Opção A — Polling HTMX (recomendada para início)

O painel atualiza o status de cada passo a cada 2 segundos. O polling é interrompido automaticamente quando a execução encerra.

```html
<div id="execution-panel"
     hx-get="/api/executions/{{ exec_id }}"
     hx-trigger="every 2s [window.__execRunning]"
     hx-swap="outerHTML">
  ...
</div>

<script>
  window.__execRunning = {{ "true" if execution.status == "running" else "false" }};
</script>
```

### Opção B — Server-Sent Events (SSE)

Para deploys com builds longos onde feedback linha a linha é crítico:

```python
# interfaces/api/routers/executions_router.py
from fastapi.responses import StreamingResponse

@router.get("/api/executions/{id}/stream")
async def stream_execution(id: str):
    async def generator():
        async for event in execution_stream_service.stream(id):
            yield f"data: {json.dumps(event)}\n\n"
        yield 'data: {"done": true}\n\n'
    return StreamingResponse(generator(), media_type="text/event-stream")
```

```html
<div hx-ext="sse"
     sse-connect="/api/executions/{{ exec_id }}/stream"
     sse-swap="message"
     id="log-output">
</div>
```

---

## 16. Frontend — TechPanel

### Seletor de contexto

Antes de qualquer ação, o usuário seleciona: **Projeto → Ambiente → Pipeline → Branch/Tag**. O ambiente `production` exibe badge vermelho persistente enquanto selecionado.

```
Projeto: [e-commerce ▼]   Ambiente: [⚠ production ▼]   Branch: [main ▼]
```

### Zona 1 — Pipeline e ações

```
Pipeline: Deploy Completo Prod  (7 passos)
┌──────────────────────────────────────────────────┐
│  1. Git pull                 pending             │
│  2. Composer install         pending             │
│  3. Rodar migrations         pending             │
│  4. Limpar cache             pending             │
│  5. npm install              pending             │
│  6. npm run build            pending             │
│  7. Reload php-fpm           pending             │
└──────────────────────────────────────────────────┘
              [ ⚠ Executar Pipeline ]
```

### Zona 2 — Execução em andamento

Status passo a passo atualiza em tempo real. Passo ativo exibe spinner; concluídos exibem ✅ ou ❌; não iniciados exibem ⬜; ignorados exibem ⏭.

```
● Executando: Deploy Completo Prod  ·  main  ·  14:32:01

  ✅  1. Git pull              2s          [ver log]
  ✅  2. Composer install      48s         [ver log]
  ⏳  3. Rodar migrations      running…    [ver log]
  ⬜  4. Limpar cache          pending
  ⬜  5. npm install           pending
  ⬜  6. npm run build         pending
  ⬜  7. Reload php-fpm        pending

┌──────────────────────────────────────────────────────────┐
│ [14:32:51] Migrating: 2025_01_14_create_orders_table     │
│ [14:32:52] Migrated:  2025_01_14_create_orders_table     │
└──────────────────────────────────────────────────────────┘
```

Em caso de falha com `stop`, os passos restantes ficam com ⏭ `skipped`.

### Zona 3 — Histórico

| Data/hora | Pipeline | Branch | Ambiente | Usuário | Status |
|---|---|---|---|---|---|
| 2025-01-15 14:32 | Deploy Completo Prod | main | production | admin | ✅ Sucesso |
| 2025-01-15 11:20 | Deploy Completo Prod | main | production | admin | ❌ Falhou (passo 3) |
| 2025-01-14 09:05 | Deploy Vue Staging | v1.2.3 | staging | admin | ✅ Sucesso |

Clicando em qualquer linha abre o detalhe da execução com status passo a passo e logs individuais.

### Modal de confirmação padrão

```
┌──────────────────────────────────────────────┐
│  Confirmar execução                          │
│                                              │
│  Pipeline: Deploy Completo Prod              │
│  Ambiente: staging                           │
│  Branch:   main · 7 passos                   │
│  Servidor: srv-stg-01 (192.168.1.20)         │
│                                              │
│              [Cancelar]  [Confirmar]         │
└──────────────────────────────────────────────┘
```

### Modal de confirmação reforçada (ambiente `production`)

```
┌──────────────────────────────────────────────┐
│  ⚠ Você está prestes a executar em           │
│    PRODUÇÃO                                  │
│                                              │
│  Pipeline: Deploy Completo Prod              │
│  Branch:   main  ·  7 passos                 │
│  Servidor: srv-prod-01 (192.168.1.10)        │
│                                              │
│  Digite CONFIRMAR para prosseguir:           │
│  [ _________________________ ]               │
│                                              │
│              [Cancelar]  [Confirmar ▶]       │
│                          (desabilitado)      │
└──────────────────────────────────────────────┘
```

---

## 17. Critérios de aceite

- [ ] Tela de login com autenticação JWT
- [ ] Cadastro de servidores com teste de conexão SSH
- [ ] Fluxo OAuth com GitHub
- [ ] Cadastro de projetos com tech stack livre (PHP, Vue, etc.)
- [ ] Suporte a múltiplos ambientes por projeto
- [ ] Cadastro e edição de pipelines com passos configuráveis
- [ ] Passos podem ser adicionados, removidos e reordenados
- [ ] Cada passo permite configurar: nome, tipo, comando, diretório, timeout e política de falha
- [ ] O TechPanel permite selecionar projeto, ambiente, pipeline e branch/tag
- [ ] Modal de confirmação antes de qualquer execução
- [ ] Confirmação reforçada (texto `CONFIRMAR`) para ambiente `production`
- [ ] Sistema bloqueia nova execução quando há processo ativo no projeto (`HTTP 409`)
- [ ] Execução avança ao próximo passo somente após conclusão bem-sucedida do anterior
- [ ] Passos restantes recebem `status=skipped` quando execução interrompe por falha
- [ ] Status de cada passo atualiza em tempo real durante execução
- [ ] Log de cada passo é visível individualmente
- [ ] Histórico exibe qual passo falhou em execuções com status `failed`
- [ ] Sistema funciona com PostgreSQL em dev e prod
- [ ] Usuários `viewer` podem consultar mas não executar

---

## 18. Dependências Python

```
# requirements.txt

# Framework
fastapi
uvicorn[standard]
jinja2
python-multipart

# Banco de dados (PostgreSQL)
sqlalchemy[asyncio]
alembic
psycopg2-binary

# SSH
paramiko

# GitHub
PyGithub

# Autenticação
python-jose[cryptography]
passlib[bcrypt]

# Criptografia de chaves SSH em repouso
cryptography

# HTTP
httpx

# Configuração
python-dotenv
pydantic-settings
```

### `docker-compose.yml` (desenvolvimento local)

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: deploy_manager
      POSTGRES_USER: deploy
      POSTGRES_PASSWORD: deploy
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

---

## 19. Decisões pendentes

**Notificações de falha:** definir canal — apenas interface, email, ou Slack/Teams via passo do tipo `notify_webhook`. O tipo `notify_webhook` já está previsto na infraestrutura.

**Modelo de permissões:** confirmar se o controle de acesso será por papel global (`admin`/`viewer`) ou granular por projeto (usuário A pode deployar projeto X mas não Y).

**Rollback assistido:** o comportamento atual em caso de falha é exibir log e interromper. Rollback (ex: `php artisan migrate:rollback`) pode ser implementado como passo opcional no pipeline após os passos de execução, ativado somente por trigger manual.

**Aprovação manual entre passos:** para fluxos críticos, avaliar adicionar um tipo de passo `manual_approval` que pause a execução até um `admin` aprovar via painel antes de continuar.

**Agendamento:** avaliar necessidade de execuções agendadas (cron). Se sim, a entidade `Pipeline` receberá campo `cron_expression` e um scheduler separado invocará `StartExecution`.