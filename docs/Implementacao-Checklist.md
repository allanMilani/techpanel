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

- [x] Aplicação OAuth GitHub configurada; callbacks em `.env`  
- [x] Fluxo de login/callback (state, CSRF)  
- [x] Integração PyGithub atrás do port (listar branches/tags por `owner/repo`)  
- [x] Não armazenar tokens em log  

**Critério de pronto:** usuário autenticado escolhe branch/tag exibida pela API antes de confirmar execução.

---

## Etapa 12 — Interface web (Vue 3 + Vite + Tailwind)

**Objetivo:** interface web do TechPanel usável (seção 16 de [TechPanel.md](./TechPanel.md)).

- [x] SPA em `frontend/` (Vue Router, `components/inputs/`, Font Awesome, Tailwind); build → `src/interfaces/web/static/dist/`  
- [x] Login/registo (`/login`, `/register`), sessão via `POST /api/auth/session` + cookie; `GET /api/auth/me` para guards; `POST /api/auth/logout`  
- [x] Layout com navegação e logout  
- [x] Fluxos: CRUD servidores (incl. teste SSH), projetos, ambientes, pipelines e passos (reordenação por UUIDs), execução e monitor (`GetExecutionLogs` + polling ~2s no cliente)  
- [x] Modal de confirmação na execução (`/app/pipelines/.../run`)  
- [x] Modal reforçado para `production` (checkbox de reconhecimento)  
- [x] Histórico por pipeline (`GET /api/pipelines/{id}/history`) na UI  

**Critério de pronto:** fluxo feliz e fluxo de falha visíveis sem usar apenas API bruta.

---

## Etapa 13 — Encerramento MVP vs backlog

**Objetivo:** alinhar implementação, [TechPanel.md](./TechPanel.md) (seções 17 e 19) e expectativa de produto; transformar lacunas em passos executáveis.

**Legenda da revisão (seção 17):** `[x]` atende ao critério de forma utilizável; `[~]` parcial (API ou esqueleto de UI sem fluxo ponta a ponta); `[ ]` não atende ou diverge do documento.

### 13.1 — Revisão dos critérios de aceite ([TechPanel.md §17](./TechPanel.md#17-critérios-de-aceite))

| Critério (resumo) | Status | Observação |
|---|---|---|
| Tela de login com JWT | [x] | Login web (`/`, `/login`) + cookie; API `POST /api/auth/login`. |
| Cadastro de servidores + teste SSH | [x] | **API** + **UI** (`/app/servers`, formulários, `POST .../test`). |
| Fluxo OAuth GitHub | [~] | Endpoints `/api/auth/github` e callback existem; token retornado em JSON — **persistência por usuário** (doc §9) e uso contínuo sem reautenticar **não** espelhados na UI. |
| Cadastro de projetos (tech stack livre) | [x] | **API** + **UI** (`/app/projects`). |
| Múltiplos ambientes por projeto | [x] | **API** (projetos + ambientes). |
| Cadastro/edição de pipelines e passos | [x] | **API** + **UI** (`/app/pipelines/...`, reordenação via textarea de UUIDs; sem drag-and-drop). |
| Passos: adicionar, remover, reordenar | [x] | Via **API**. |
| Campos por passo (nome, tipo, comando, dir, timeout, `on_failure`) | [x] | Domínio + **API**. |
| Seletor: projeto → ambiente → pipeline → branch/tag | [~] | Navegação por páginas encadeadas; branch/tag manual na execução; **refs GitHub** ainda não na UI. |
| Modal antes de executar | [x] | Tela `/app/pipelines/{id}/run` + `StartExecution` após confirmação. |
| Modal reforçado `CONFIRMAR` em `production` | [x] | Condicionado a `environment_type == production`. |
| Bloqueio 409 com execução ativa no projeto | [x] | `StartExecution` + repositório. |
| Avanço sequencial só após sucesso do passo anterior | [x] | `RunNextStep` + runners. |
| Passos restantes `skipped` ao interromper por falha | [x] | Conforme política `on_failure`. |
| Status em “tempo real” durante execução | [x] | Painel via `GET /api/executions/{id}/panel` + polling ~2s no Vue. |
| Log por passo visível | [~] | **UI** usa `GetExecutionLogs`; rotas REST extras do doc §12 (logs consolidados, etc.) ainda não no `api_router`. |
| Histórico indica passo que falhou | [~] | `GetHistory` na UI; coluna de falha ainda genérica (sem nome do passo que falhou na execução). |
| PostgreSQL dev e prod | [x] | Stack e migrações alinhadas ao doc. |
| `viewer` consulta sem executar | [x] | `require_admin` em disparo de execução e testes de API. |

**Itens do produto fora do §17 original (implementados no repositório):**

- [x] Cadastro de usuário via web (`/register`) com validação de e-mail já cadastrado (papéis novos como `viewer` por padrão — alinhar com política de admin se necessário).

### 13.2 — Passos para concluir o MVP conforme [TechPanel.md](./TechPanel.md)

Estes itens fecham a lacuna entre “API pronta” e “critérios de aceite §17 utilizáveis na interface” + alinhamento de contratos HTTP.

**Interface web (painel §16)**

- [ ] Seletor **Projeto → Ambiente → Pipeline → Branch/Tag** no dashboard + refs GitHub (`/api/github/...`) após OAuth/token.  
- [x] Modais de confirmação acoplados ao disparo (`/app/pipelines/.../run`; produção com `CONFIRMAR`).  
- [x] Painel de execução com `GetExecutionLogs` (JSON) e polling no cliente ~2s.  
- [~] Histórico: `GetHistory` na UI; coluna “falha” ainda genérica (nome/ordem do passo que falhou em backlog).  
- [x] Telas CRUD web: servidores (incl. teste SSH), projetos, ambientes, pipelines e passos (reordenação por lista de UUIDs).  
- [ ] `POST /api/auth/logout` com invalidação server-side (hoje só remove o cookie `access_token`).

**API REST (alinhamento [TechPanel.md §12](./TechPanel.md#12-endpoints-da-api))**

- [ ] Expor rotas de execução/consulta conforme doc: detalhe de execução, logs consolidado, log por passo, histórico (e/ou `active-execution` por projeto), ou atualizar o **TechPanel.md** para refletir os paths reais (`/api/executions/start`, etc.).  
- [ ] `POST /api/auth/logout` (e comportamento de cookie/sessão na web, se aplicável).  
- [ ] Opcional MVP: endpoint SSE `/api/executions/{id}/stream` (doc §15-B) se o polling for insuficiente para logs longos.

**GitHub e segurança de cadastro**

- [ ] Definir e implementar **armazenamento do token GitHub** por usuário (ou fluxo alternativo documentado) para listar repos/refs sem exigir callback a cada uso.  
- [ ] Revisar política de **cadastro público de usuários** (`/register`) vs doc §11 (“apenas admin cria/edita…”) — restringir rota a admin, desativar self-signup ou atualizar o documento.

**Decisões pendentes ([TechPanel.md §19](./TechPanel.md#19-decisões-pendentes)) — registrar como issues/backlog**

- [ ] Canal de notificações de falha (UI apenas / e-mail / webhook já previsto).  
- [ ] Permissões: manter papéis globais ou granularidade por projeto.  
- [ ] Rollback assistido (passo opcional no pipeline vs feature dedicada).  
- [ ] Tipo de passo `manual_approval`.  
- [ ] Agendamento (`cron`) para `StartExecution`.

### 13.3 — Encerramento da etapa 13 (checklist operacional)

- [ ] Todos os itens da tabela **13.1** estão `[x]` **ou** explicitamente aceitos como fora de escopo com ajuste no [TechPanel.md](./TechPanel.md).  
- [ ] Itens da subseção **13.2** priorizados (MVP vs pós-MVP) e rastreados (issues).  
- [ ] Decisões **§19** (bloco em **13.2**) convertidas em issues com prioridade.

**Critério de pronto (etapa 13):** revisão **13.1** concluída; itens de **13.2** e follow-up de **§19** definidos e rastreados; documentação e código sem contradição não explicada.

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
