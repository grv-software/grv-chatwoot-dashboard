# Supabase Config Sync — Design Spec

## Objetivo

Sincronizar todas as configurações do GRV SAC Dashboard (incluindo token da API do Chatwoot) em uma tabela Supabase compartilhada, eliminando a necessidade de configuração individual por máquina. Qualquer pessoa que abrir o link já visualiza o dashboard com as credenciais do administrador.

## Contexto

Hoje as configurações ficam em `localStorage` — cada máquina precisa inserir o token manualmente. Com esta mudança, o administrador configura uma vez e todos enxergam os dados automaticamente. O botão "Conectar" e o modal de token são removidos.

---

## Arquitetura

### Supabase

- Projeto gratuito no [supabase.com](https://supabase.com)
- Tabela `dashboard_config` com **uma única linha** (id = 1)
- Acesso via service key (nunca exposta no frontend) — apenas as Netlify Functions tocam o Supabase diretamente

### Netlify Functions

| Endpoint | Método | Proteção | Ação |
|---|---|---|---|
| `/api/config` | GET | nenhuma | Lê linha id=1 do Supabase e retorna JSON |
| `/api/config` | POST | senha no body | Verifica `SETTINGS_PASSWORD`, faz upsert no Supabase |

### Variáveis de ambiente no Netlify

| Variável | Descrição |
|---|---|
| `SUPABASE_URL` | URL do projeto Supabase (ex: `https://xyz.supabase.co`) |
| `SUPABASE_SERVICE_KEY` | Service role key do Supabase (nunca exposta no frontend) |
| `SETTINGS_PASSWORD` | Já existe — reutilizado para proteger o POST |

---

## Modelo de dados

```sql
create table dashboard_config (
  id           int primary key default 1,
  token        text,
  account      int,
  sla_tma      int default 8,
  sla_tmr      int default 30,
  sla_fcr      int default 85,
  sla_msg      int default 10,
  threshold    int default 0,
  refresh_sec  int default 60,
  weight_tma   int default 25,
  weight_tmr   int default 25,
  weight_fcr   int default 25,
  weight_msg   int default 25,
  weight_csat  int default 0,
  updated_at   timestamptz default now()
);

-- Garante apenas uma linha
create unique index on dashboard_config ((id));
```

RLS desabilitado — acesso controlado exclusivamente via service key nas Netlify Functions.

---

## Fluxo de startup

```
Abre o dashboard
  → GET /api/config
      → Sucesso: aplica config em memória (cfg.token, cfg.account, _SLA_*, _WEIGHT_*, etc.)
                 salva em localStorage como cache
                 inicia startDashboard()
      → Config vazia (token ausente): exibe tela de primeira configuração
                 "Configure o token para começar" → abre settings com aviso
      → Falha de rede: usa localStorage como fallback
                 exibe aviso sutil: "⚠ Usando config local — Supabase indisponível"
```

A função `loadRemoteConfig()` executa **antes** de `startDashboard()` no `DOMContentLoaded`.

---

## Fluxo de save

```
Admin abre Configurações (senha validada)
  → Edita campos (token, SLAs, pesos, etc.)
  → Clica Salvar
      → POST /api/config { password, token, account, sla_tma, ... }
          → Netlify Function verifica senha
          → Upsert no Supabase (id=1)
          → Retorna { ok: true }
      → Frontend: aplica em memória + salva localStorage como cache
      → showToast('Configurações salvas e sincronizadas')
      → startDashboard()
```

---

## Mudanças na interface

### Removidos
- Botão "Conectar" no sidebar (`#nav-connect`)
- Modal de token (`#token-modal`, `showTokenModal()`)
- CSS e JS relacionados ao modal de token

### Adicionados na página de Configurações
- Card "Conexão Chatwoot" (antes do card de SLA) com campos:
  - **Token API** — `<input type="password">` com botão olho para mostrar/ocultar
  - **Conta (Account ID)** — `<input type="number">`
- Indicador de status de sync: última atualização + "Sincronizado com Supabase ✓" ou "Config local (offline)"

### Mantidos
- Senha de administrador para acessar configurações
- Todos os campos existentes de SLA, pesos, refresh, threshold

---

## Primeira configuração (onboarding)

Quando `GET /api/config` retorna sem token, o frontend verifica o localStorage:

**Caso A — localStorage tem token** (usuário já configurou antes do Supabase):
- Exibe banner: *"Config local encontrada. Deseja sincronizar com o Supabase?"* com botão "Sincronizar agora"
- Ao confirmar: abre Configurações (solicita senha), pré-preenche campos com valores do localStorage
- Salva → upsert no Supabase → banner desaparece, dashboard inicia

**Caso B — localStorage vazio** (primeiro acesso puro):
- Dashboard exibe overlay: *"Bem-vindo! Configure o token do Chatwoot para começar."*
- Botão "Configurar agora" abre a página de Configurações (solicita senha)
- Admin preenche token + account → Salva → linha criada no Supabase → dashboard inicia

---

## Segurança: token na resposta pública

O `GET /api/config` não exige senha e retorna o token no response — qualquer pessoa com o link consegue ler o token via DevTools. Isso é intencional: o caso de uso aprovado é "todos enxergam o dashboard pelas credenciais do admin". Se a segurança do token precisar ser reforçada no futuro, o GET pode ser protegido por senha (mudança pontual na Netlify Function).

---

## Escopo fora deste spec

- Múltiplos perfis de configuração (apenas um config global)
- Histórico de alterações no Supabase
- Notificações em tempo real quando config muda (Supabase Realtime)
- Autenticação de usuários no Supabase (usa apenas a senha de admin do dashboard)
