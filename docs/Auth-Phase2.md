# Auth Phase 2 — Rotacao e Revogacao de Tokens

Documento de referencia para evoluir a autenticacao JWT do TechPanel apos o MVP.

## Objetivo

Garantir seguranca operacional e controle de sessao com:

- revogacao de tokens antes do `exp`
- rotacao segura de chaves JWT
- refresh token com ciclo de vida separado
- logout com invalidacao server-side
- trilha de auditoria para eventos de seguranca

## Escopo da fase 2

Esta fase adiciona capacidades de seguranca sem alterar o contrato principal de autorizacao baseado em papeis (`admin` e `viewer`).

### Dentro do escopo

- modelo de refresh token persistido
- `jti` (JWT ID) em access token e refresh token
- denylist para revogacao de access tokens
- endpoint de logout com invalidacao de sessao
- rotacao de chaves (`kid`) para assinatura JWT
- monitoramento e alertas de eventos de auth

### Fora do escopo

- SSO/OIDC corporativo
- MFA
- politica de permissao granular por recurso

## Arquitetura proposta

### Tipos de token

1. **Access Token (curta duracao)**
  - uso: autorizacao em chamadas de API
  - duracao sugerida: 5 a 15 minutos
  - claims: `sub`, `role`, `exp`, `iat`, `jti`, `kid`
2. **Refresh Token (media/longa duracao)**
  - uso: renovar access token sem novo login
  - duracao sugerida: 7 a 30 dias
  - obrigatoriamente persistido com hash no banco
  - rotacionado a cada uso (refresh token rotation)

### Componentes

- **TokenService**: assina e valida JWT com suporte a `kid`
- **SessionService**: emite, rotaciona e revoga sessoes
- **RevocationStore**: consulta denylist por `jti`
- **KeyStore**: fornece chave ativa e chaves antigas para validacao

## Modelo de dados sugerido

### Tabela `auth_sessions`

- `id` UUID PK
- `user_id` UUID FK users
- `refresh_token_hash` text
- `refresh_token_jti` varchar(64) unico
- `user_agent` varchar(512) nullable
- `ip_address` varchar(64) nullable
- `created_at` timestamptz
- `expires_at` timestamptz
- `revoked_at` timestamptz nullable
- `replaced_by_session_id` UUID nullable

### Tabela `revoked_tokens`

- `id` UUID PK
- `token_jti` varchar(64) unico
- `token_type` varchar(16) (`access`/`refresh`)
- `reason` varchar(64)
- `expires_at` timestamptz
- `created_at` timestamptz

## Fluxos operacionais

### 1) Login

1. Validar credenciais.
2. Gerar access token (`jti` novo).
3. Gerar refresh token (`jti` novo).
4. Persistir sessao com hash do refresh token.
5. Retornar tokens ao cliente.

### 2) Refresh

1. Receber refresh token.
2. Validar assinatura, `exp`, `kid`, denylist e sessao ativa.
3. Revogar refresh token atual (ou marcar sessao anterior como substituida).
4. Emitir novo par access+refresh (rotacao).
5. Persistir nova sessao/token e retornar resposta.

### 3) Logout

1. Identificar sessao atual (por refresh token ou identificador de sessao).
2. Revogar sessao (`revoked_at`).
3. Inserir `jti` do access token em denylist ate o `exp`.
4. Responder `204 No Content`.

### 4) Revogacao forçada (admin/security)

1. Revogar todas as sessoes do usuario (incidente de seguranca).
2. Popular denylist para tokens ativos conhecidos.
3. Forcar reautenticacao.

## Rotacao de chaves JWT

### Estrategia

- assinar tokens com chave ativa identificada por `kid`
- manter chaves anteriores em modo validacao ate expirar o ultimo token emitido
- remover chave antiga apenas apos janela de seguranca

### Passos de rotacao

1. Publicar nova chave no `KeyStore` e marcar como ativa.
2. Novos tokens passam a ser assinados com novo `kid`.
3. Validacao aceita chave antiga e nova durante janela de transicao.
4. Encerrar chave antiga apos expirar toda base de tokens assinada por ela.

## Regras de seguranca

- nunca persistir token bruto em banco (somente hash para refresh)
- incluir `iat` e `jti` em todos os tokens
- validar `alg` explicitamente (nao aceitar algoritmo dinamico do token)
- usar segredo/chave via ambiente seguro (nao versionar em repo)
- limitar tentativas de login e refresh por IP/usuario (rate limit)

## Observabilidade e auditoria

Eventos que devem ser logados:

- `auth.login.success`
- `auth.login.failure`
- `auth.refresh.success`
- `auth.refresh.reused_token_detected`
- `auth.logout.success`
- `auth.token.revoked`
- `auth.key.rotated`

Campos minimos:

- `user_id` (quando houver)
- `session_id`
- `jti`
- `ip`
- `user_agent`
- `timestamp`

## Plano de implementacao incremental

### Fase 2.1 (base)

- adicionar `jti` e `iat` no JWT
- criar tabela `auth_sessions`
- implementar refresh token com persistencia

### Fase 2.2 (revogacao)

- criar tabela `revoked_tokens`
- consultar denylist em `get_current_user`
- endpoint de logout com invalidacao server-side

### Fase 2.3 (rotacao de chaves)

- suporte a `kid`
- `KeyStore` com chave ativa + historico
- procedimento operacional de rotacao documentado

## Testes recomendados

- unitarios:
  - emissao de tokens com claims esperadas
  - validacao de token expirado/invalido
  - fluxo de refresh com rotacao
- integracao (com mocks/fakes, sem DB real no ambiente de testes):
  - login -> refresh -> logout
  - token revogado retorna `401`
  - viewer continua recebendo `403` em rota de escrita

## Riscos e mitigacoes

- **Replay de refresh token**: usar rotacao e invalidacao atomica
- **Comprometimento de chave**: rotacao emergencial e revogacao em massa
- **Sessao zumbi**: expiracao curta de access token + denylist + logout server-side

## Definicoes de pronto (Phase 2)

- refresh token com rotacao implementado
- revogacao por `jti` funcional
- logout invalida sessao no servidor
- rotacao de chaves com `kid` validada em ambiente de homologacao
- dashboards/alertas de auth ativos