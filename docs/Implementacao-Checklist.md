# Checklist de implementação — TechPanel

Documento operacional para acompanhar o desenvolvimento do projeto **TechPanel** em **etapas ordenadas**. Marque os itens conforme concluídos. Especificação técnica de referência: [TechPanel.md](./TechPanel.md).

**Legenda**

- `[ ]` pendente  
- `[x]` concluído  
- Itens marcados **(opcional)** podem ser adiados sem bloquear o MVP.

---

## Estado assumido (já feito)

- [x] Estrutura de pastas (hexagonal) definida  
- [x] `pyproject.toml` / `uv` / ambiente virtual  
- [x] PostgreSQL local (ex.: Docker) e variáveis de ambiente  
- [x] SQLAlchemy async + modelos ORM + Alembic configurado  
- [x] FastAPI com `/health` e `/health/db` funcionando  

---

## Etapa 0 — Baseline do repositório

**Objetivo:** qualquer desenvolvedor clona, sobe o banco e roda a API com comandos documentados.

- [x] `README.md` ou trecho em doc interna com: pré-requisitos, `make`/`uv` targets, variáveis `.env` mínimas  
- [x] `docker-compose.yml` (ou equivalente) versionado e testado  
- [x] `.env.example` alinhado ao `Settings` (sem segredos reais)  
- [x] `Makefile` (ou task runner) cobrindo: `sync`, `db-up`, `migrate`, `run`  
- [x] CI mínimo **(opcional):** lint + testes em PR  

**Critério de pronto:** nova máquina executa `db-up` + `migrate` + `run` e obtém `200` em `/health/db`.

---

## Etapa 1 — Schema e migrações

**Objetivo:** banco reflete fielmente o modelo de dados (seção 5 de [TechPanel.md](./TechPanel.md)).

- [x] Revisar migration inicial (`autogenerate` + ajustes manuais se necessário) — revisão `a71640253481`, template `alembic/script.py.mako`  
- [x] Constraints: `users.email` único; FKs com `ON DELETE` coerentes — ver [Schema-migrations.md](./Schema-migrations.md)  
- [x] Tipos Postgres: UUID, `timestamptz`; enums como `VARCHAR` + validação na aplicação — documentado em [Schema-migrations.md](./Schema-migrations.md)  
- [x] Índices: `ix_executions_pipeline_id_started_at` + unicidade `(pipeline_id, order)` e `(execution_id, order)`  
- [x] Política de dados sensíveis: `servers.private_key_enc` — ver [Schema-migrations.md](./Schema-migrations.md)  

**Critério de pronto:** `alembic upgrade head` em banco limpo cria todas as tabelas; downgrade **(se usado)** documentado.

---

## Etapa 2 — Domínio (núcleo)

**Objetivo:** regras e contratos sem dependência de framework ou ORM.

- [x] Entidades em `src/domain/entities/` (`User`, `Server`, `Project`, `Environment`, `Pipeline`, `PipelineStep`, `Execution`, `StepExecution`)  
- [x] Value objects / enums de domínio em `src/domain/value_objects/` (status, tipos de passo, `on_failure`, tipo de ambiente)  
- [x] Ports: repositórios em `src/domain/ports/repositories/`  
- [x] Ports: serviços em `src/domain/ports/services/` (`ISSHService`, `IGitHubService`, `IStepRunner`, `INotificationService`)  
- [x] Validações puras no domínio onde couber (ex.: email, ordem de passos > 0)  

**Critério de pronto:** módulo `domain` importável sem `fastapi`, `sqlalchemy`, `paramiko`.

---

## Etapa 3 — DTOs e casos de uso (application)

**Objetivo:** orquestração testável sobre os ports.

- [x] DTOs de entrada/saída em `src/application/dtos/`  
- [x] Casos de uso por agregado, pastas espelhando o doc (`auth`, `servers`, `projects`, `pipelines`, `executions`)  
- [x] Tratamento de erro de aplicação (exceções de domínio vs infra) sem vazar detalhes internos na API  

**Critério de pronto:** pelo menos um use case (ex.: “obter usuário por email”) coberto por teste unitário com **fakes** dos repositórios.

---

## Etapa 4 — Repositórios PostgreSQL (infrastructure)

**Objetivo:** implementar ports com SQLAlchemy async.

- [x] Implementações `Pg*Repository` em `src/infrastructure/persistence/repositories/`  
- [x] Mapeamento explícito ORM ↔ entidade (funções dedicadas; sem expor modelos ORM para fora da infra)  

**Critério de pronto:** fluxos de aplicação cobrindo leitura/criação de `User` e integração entre use cases com **mocks/fakes**, sem uso de banco de dados nos testes de integração.

---

## Etapa 5 — Injeção de dependências e API base

**Objetivo:** FastAPI enxuto, composição na borda.

- [x] `src/interfaces/api/dependencies.py` (ou equivalente): providers de sessão, repositórios, use cases  
- [x] `error_handler` padronizando JSON de erro  
- [x] Prefixo `/api` nas rotas REST conforme doc  
- [x] CORS e trust proxy **(opcional)** se houver front separado  

**Critério de pronto:** composição via `Depends` em rotas base (`/health`, `/health/db`, `/auth/login`) sem lógica de negócio no router.  
**Nota:** rota autenticada de exemplo (ex.: `/me`) foi adiada para a Etapa 6 por decisão de escopo.

---

## Etapa 6 — Autenticação e autorização

**Objetivo:** JWT + papéis `admin` / `viewer` (seção 11 e 17).

- [x] Hash de senha (bcrypt) na criação/atualização de usuário  
- [x] `POST` login emitindo JWT; payload mínimo (`sub`, `role`, exp)  
- [x] Dependency `get_current_user` + `require_admin` onde necessário  
- [x] `viewer` bloqueado de executar pipelines **(critério de aceite)**  
- [x] Rotação / revogação **(opcional MVP):** documentar como “fase 2” — ver [Auth-Phase2.md](./Auth-Phase2.md)  

**Critério de pronto:** token válido acessa rotas protegidas; token `viewer` recebe `403` em operação de escrita/execução.

---

## Etapa 7 — Servidores e SSH

**Objetivo:** cadastro seguro e teste de conexão.

- [x] CRUD API de servidores (conforme endpoints do doc)  
- [x] Criptografia Fernet para `private_key_enc` (chave só no `.env`)  
- [x] Use case `CheckSSHConnection` (`check_ssh_connection.py`) usando `Paramiko` atrás do port `ISSHService`  
- [x] Auditoria mínima: `created_by` preenchido  

**Critério de pronto:** admin cadastra servidor, testa SSH com sucesso; chave nunca retornada em claro na API.

---

## Etapa 8 — Projetos e ambientes

**Objetivo:** múltiplos ambientes por projeto.

- [x] CRUD projeto (`repo_github`, `tech_stack` livre)  
- [x] Vincular N ambientes: servidor + `working_directory` + tipo (`production` / `staging` / `custom`)  
- [x] Validações: ambiente ativo/inativo; servidor existente  

**Critério de pronto:** fluxo “projeto → dois ambientes (stg/prod)” persistido e consultável via API.

---

## Etapa 9 — Pipelines e passos

**Objetivo:** pipeline configurável por ambiente.

- [x] CRUD pipeline por `environment_id`  
- [x] CRUD passos; tipos iniciais: `ssh_command`, `http_healthcheck`, `notify_webhook`  
- [x] Reordenação de passos (`order` consistente)  
- [x] Campos: nome, tipo, comando, `working_directory` opcional, `timeout_seconds`, `on_failure`, `is_active`  

**Critério de pronto:** pipeline com ≥ 3 passos salvo, reordenado e relido corretamente.

---

## Etapa 10 — Execução do pipeline (core)

**Objetivo:** sequência estrita; falhas e `skipped` conforme política.

- [x] `StartExecution`: cria `execution` + `step_executions` em `pending`  
- [x] Lock por projeto: nova execução retorna **409** se houver processo ativo (doc)  
- [x] `RunNextStep` / motor: só avança após sucesso; `stop` / `continue` / `notify_and_stop`  
- [x] `RunnerRegistry` + implementações infra dos runners  
- [x] Persistir `log_output`, `exit_code`, timestamps por passo  
- [x] Atualização de status da execução global (`success` / `failed` / …)  

**Critério de pronto:** pipeline de teste com `http_healthcheck` + `ssh_command` simulado **ou** ambiente de staging real executa ponta a ponta sem passos paralelos indevidos.

---

## Etapa 11 — GitHub

**Objetivo:** OAuth + seleção de branch/tag.

- [ ] Aplicação OAuth GitHub configurada; callbacks em `.env`  
- [ ] Fluxo de login/callback (state, CSRF)  
- [ ] Integração PyGithub atrás do port (listar branches/tags por `owner/repo`)  
- [ ] Não armazenar tokens em log  

**Critério de pronto:** usuário autenticado escolhe branch/tag exibida pela API antes de confirmar execução.

---

## Etapa 12 — Interface web (HTMX + Jinja2 + Bootstrap)

**Objetivo:** interface web do TechPanel usável (seção 16 de [TechPanel.md](./TechPanel.md)).

- [ ] `base.html`, layout, flash/alertas  
- [ ] Login  
- [ ] Telas: servidores, projetos/ambientes, pipelines, painel de execução  
- [ ] Modal de confirmação padrão  
- [ ] Modal reforçado para `production` (digitar `CONFIRMAR`)  
- [ ] Polling ~2s no painel até execução terminal  
- [ ] Histórico com indicação do passo que falhou  

**Critério de pronto:** fluxo feliz e fluxo de falha visíveis sem usar apenas API bruta.

---

## Etapa 13 — Encerramento MVP vs backlog

**Objetivo:** alinhar com critérios de aceite (seção 17) e decisões pendentes (seção 19).

- [ ] Revisar checklist da seção 17 de [TechPanel.md](./TechPanel.md) (todos os itens)  
- [ ] Decisões pendentes registradas: notificações, permissões granulares, rollback assistido, `manual_approval`, agendamento cron  

**Critério de pronto:** lista de aceite do produto marcada; gaps viram issues priorizadas.

---

## Dependências entre etapas (resumo)

```text
0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13
                              ↑_______________|
                        (11 pode paralelizar após 6 se API estável)
```

---

## Manutenção deste documento

- Atualize **Estado assumido** quando novos baselines forem concluídos.  
- Itens **(opcional)** podem ser movidos para um arquivo de backlog se poluírem o MVP.  
- Data da última revisão: preencher abaixo.

**Última revisão:** 2026-04-26
