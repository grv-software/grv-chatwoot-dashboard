# Página de Configurações — Design Spec

**Data:** 2026-06-20
**Status:** Aprovado

---

## Objetivo

Criar uma página de configurações protegida por senha, acessível via ícone ⚙ no rodapé do sidebar, que permita ao administrador definir SLAs, alerta de fila, intervalo de atualização e pesos da pontuação de agentes — sem mexer no código-fonte.

---

## Contexto

Hoje todos os parâmetros operacionais estão hardcoded em `index.html`:

```js
let _SLA_TMA = 8;      // horas
let _SLA_TMR = 30;     // minutos
let _SLA_FCR = 85;     // %
let _SLA_MSG = 10;     // mensagens/conversa
const REFRESH_SEC = 60;
// pesos: cada métrica vale 25pts fixos
```

O alerta de fila (`cfg.threshold`) existe mas está enterrado no modal de configurações de acesso, inacessível para quem não sabe que existe.

---

## Usuários

- **Administradores** — têm a senha, configuram os parâmetros
- **Demais usuários** — veem o dashboard normalmente, sem acesso às configurações

---

## Arquitetura

### Autenticação

A senha fica em `server.js` como constante `SETTINGS_PASSWORD`. O browser nunca vê a senha em texto — só envia via `POST /api/auth-settings` e recebe `{ok: true/false}`.

```
SETTINGS_PASSWORD = 'xxxx'   ← definido pelo dev que faz o deploy
```

Uma vez autenticado, o browser salva `localStorage.setItem('grv_settings_auth', '1')`. Nas visitas seguintes, `grv_settings_auth === '1'` pula a tela de senha e abre direto.

Não há expiração — acesso permanente naquele browser.

### Fluxo de acesso

```
Clica ⚙ no sidebar
    ↓
grv_settings_auth === '1'?
    ├── Sim → showPage('configuracoes')
    └── Não → modal de senha
              ↓
         POST /api/auth-settings {password}
              ├── {ok: true}  → salva grv_settings_auth, showPage('configuracoes')
              └── {ok: false} → exibe erro "Senha incorreta"
```

### Novo endpoint no server.js

```
POST /api/auth-settings
Body: { "password": "..." }
Response 200: { "ok": true }  ou  { "ok": false }
```

Não exige `api_access_token` — é uma rota separada, antes do proxy.

---

## Interface

### Ícone no sidebar

- Posição: rodapé do sidebar, separado dos itens de navegação com `margin-top: auto`
- Ícone: ⚙ (engrenagem)
- Label: "Config."
- Comportamento: mesmo padrão dos outros itens — `onclick="openSettings()"`
- **Não** recebe a classe `active` quando a página de configurações está aberta (não é uma aba de conteúdo do dashboard)

### Modal de senha

- Aparece sobre o conteúdo atual (não muda de página)
- Campo `type="password"` com placeholder "Senha de administrador"
- Botão "Entrar"
- Mensagem de erro inline se senha errada: "Senha incorreta"
- Pressionar Enter submete o formulário

### Página de configurações

Abre via `showPage('configuracoes')` — mesma mecânica de Painel / Agentes / Análise.

Layout: coluna única com 4 cards/grupos de campos.

---

## Campos

### Grupo 1 — SLAs de Desempenho

| Campo | Tipo | Padrão | Unidade | localStorage key |
|---|---|---|---|---|
| TMA | number | 8 | horas | `grv_sla_tma` |
| TMR | number | 30 | minutos | `grv_sla_tmr` |
| Taxa de Resolução | number | 85 | % | `grv_sla_fcr` |
| Msgs/Conversa | number | 10 | mensagens | `grv_sla_msg` |

### Grupo 2 — Fila

| Campo | Tipo | Padrão | localStorage key |
|---|---|---|---|
| Alerta de fila (≥ N conversas aguardando) | number | 0 | `grv_threshold` |

`0` = desativado.

### Grupo 3 — Atualização

| Campo | Tipo | Padrão | Mínimo | localStorage key |
|---|---|---|---|---|
| Intervalo de atualização (segundos) | number | 60 | 15 | `grv_refresh_sec` |

### Grupo 4 — Pesos da Pontuação de Agentes

| Campo | Tipo | Padrão | localStorage key |
|---|---|---|---|
| Peso TMA | number | 25 | `grv_weight_tma` |
| Peso TMR | number | 25 | `grv_weight_tmr` |
| Peso Resolução | number | 25 | `grv_weight_fcr` |
| Peso Msgs | number | 25 | `grv_weight_msg` |

**Validação:** soma dos 4 pesos deve ser exatamente 100. Enquanto a soma ≠ 100, o botão Salvar fica desabilitado e exibe "Soma atual: X/100 pts".

---

## Ações

**Salvar** — persiste todos os campos no localStorage, atualiza as variáveis em memória (`_SLA_TMA`, `_SLA_TMR`, `_SLA_FCR`, `_SLA_MSG`, `cfg.threshold`, `REFRESH_SEC` → via variável `let`), reinicia o timer de atualização com o novo intervalo, exibe toast "Configurações salvas".

**Restaurar padrões** — preenche os campos com os valores padrão (não salva ainda — usuário precisa clicar Salvar para confirmar).

---

## Persistência e aplicação em memória

As variáveis SLA e de peso hoje são `let` — podem ser reatribuídas diretamente:

```js
_SLA_TMA = parseInt(localStorage.getItem('grv_sla_tma') || '8');
_SLA_TMR = parseInt(localStorage.getItem('grv_sla_tmr') || '30');
_SLA_FCR = parseInt(localStorage.getItem('grv_sla_fcr') || '85');
_SLA_MSG = parseInt(localStorage.getItem('grv_sla_msg') || '10');
```

`REFRESH_SEC` hoje é `const` — precisa ser convertida para `let` para ser reatribuída.

Os pesos da pontuação precisam de variáveis análogas:

```js
let _WEIGHT_TMA = parseInt(localStorage.getItem('grv_weight_tma') || '25');
let _WEIGHT_TMR = parseInt(localStorage.getItem('grv_weight_tmr') || '25');
let _WEIGHT_FCR = parseInt(localStorage.getItem('grv_weight_fcr') || '25');
let _WEIGHT_MSG = parseInt(localStorage.getItem('grv_weight_msg') || '25');
```

`calcAgentScore()` passa a usar `_WEIGHT_TMA`, `_WEIGHT_TMR`, `_WEIGHT_FCR`, `_WEIGHT_MSG` em vez dos 25pts fixos.

---

## O que não muda

- Não há logout / revogar acesso por browser (fora do escopo)
- Não há histórico de alterações
- Não há sincronização entre browsers (cada browser tem seu próprio estado em localStorage)
- A senha não é configurável pelo dashboard — muda apenas via `server.js`
