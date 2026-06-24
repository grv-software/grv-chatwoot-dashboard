# Supabase Config Sync — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sincronizar todas as configurações do GRV SAC Dashboard (incluindo token do Chatwoot) em uma tabela Supabase, eliminando configuração por máquina — qualquer pessoa que abrir o link vê o dashboard com as credenciais do administrador.

**Architecture:** Duas Netlify Functions (`GET /api/config` e `POST /api/config`) fazem ponte entre o frontend e o Supabase usando a service key. O frontend chama `loadRemoteConfig()` no startup antes de qualquer outra coisa, aplica a config em memória e armazena em localStorage como cache offline. O botão "Conectar" e o modal de token são removidos; o token vai para a página de Configurações protegida por senha.

**Tech Stack:** Netlify Functions (Node.js 18), Supabase REST API (sem SDK — fetch nativo), HTML/CSS/JS vanilla no `index.html`.

## Global Constraints

- `index.html` é arquivo único — todo CSS, HTML e JS inline; não criar arquivos externos
- Netlify Functions em `netlify/functions/` — Node.js 18 (fetch nativo disponível, não instalar node-fetch)
- Variáveis de ambiente no Netlify: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SETTINGS_PASSWORD` (já existe)
- Nenhuma dependência npm nova — o projeto não tem package.json para as functions
- Token API Chatwoot do administrador: usar o token salvo nas configurações do Netlify / obtido com o administrador do Chatwoot
- Account ID: verificar valor atual em `cfg.account` no localStorage ou usar `1` como padrão

---

### Task 1: Supabase — criar tabela e Netlify Function GET+POST /api/config

**Files:**
- Create: `netlify/functions/config.js`
- Modify: `netlify.toml`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `GET /api/config` → `{ token, account, sla_tma, sla_tmr, sla_fcr, sla_msg, threshold, refresh_sec, weight_tma, weight_tmr, weight_fcr, weight_msg, weight_csat }` ou `{}` se sem linha
- Produces: `POST /api/config { password, token, account, sla_tma, ... }` → `{ ok: true }` ou `{ ok: false }` para senha errada

- [ ] **Step 1: Criar tabela no Supabase**

Acesse https://supabase.com → seu projeto → SQL Editor e execute:

```sql
create table if not exists dashboard_config (
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

-- Desabilitar RLS (acesso controlado pela service key nas Netlify Functions)
alter table dashboard_config disable row level security;
```

Verificar: a tabela aparece em Table Editor com 0 rows.

- [ ] **Step 2: Criar `netlify/functions/config.js`**

```javascript
const ALLOWED = ['token','account','sla_tma','sla_tmr','sla_fcr','sla_msg',
                 'threshold','refresh_sec','weight_tma','weight_tmr','weight_fcr',
                 'weight_msg','weight_csat'];

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Content-Type': 'application/json',
};

exports.handler = async (event) => {
  const SUPABASE_URL = process.env.SUPABASE_URL;
  const SERVICE_KEY  = process.env.SUPABASE_SERVICE_KEY;

  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 204,
      headers: {
        ...CORS,
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
      body: '',
    };
  }

  if (!SUPABASE_URL || !SERVICE_KEY) {
    return { statusCode: 503, headers: CORS, body: JSON.stringify({ error: 'Supabase not configured' }) };
  }

  /* GET — leitura pública */
  if (event.httpMethod === 'GET') {
    try {
      const res = await fetch(
        `${SUPABASE_URL}/rest/v1/dashboard_config?id=eq.1&select=*`,
        { headers: { apikey: SERVICE_KEY, Authorization: `Bearer ${SERVICE_KEY}` } }
      );
      const rows = await res.json();
      return { statusCode: 200, headers: CORS, body: JSON.stringify(rows[0] || {}) };
    } catch (e) {
      return { statusCode: 500, headers: CORS, body: JSON.stringify({ error: e.message }) };
    }
  }

  /* POST — upsert com senha */
  if (event.httpMethod === 'POST') {
    try {
      const body     = JSON.parse(event.body || '{}');
      const { password, ...fields } = body;
      const expected = process.env.SETTINGS_PASSWORD;

      if (!expected) {
        return { statusCode: 503, headers: CORS, body: JSON.stringify({ error: 'SETTINGS_PASSWORD not configured' }) };
      }
      if (password !== expected) {
        return { statusCode: 200, headers: CORS, body: JSON.stringify({ ok: false }) };
      }

      const payload = { id: 1, updated_at: new Date().toISOString() };
      for (const key of ALLOWED) {
        if (fields[key] !== undefined) payload[key] = fields[key];
      }

      const res = await fetch(`${SUPABASE_URL}/rest/v1/dashboard_config`, {
        method: 'POST',
        headers: {
          apikey: SERVICE_KEY,
          Authorization: `Bearer ${SERVICE_KEY}`,
          'Content-Type': 'application/json',
          Prefer: 'resolution=merge-duplicates',
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.text();
        return { statusCode: 500, headers: CORS, body: JSON.stringify({ error: err }) };
      }

      return { statusCode: 200, headers: CORS, body: JSON.stringify({ ok: true }) };
    } catch (e) {
      return { statusCode: 500, headers: CORS, body: JSON.stringify({ error: e.message }) };
    }
  }

  return { statusCode: 405, headers: CORS, body: JSON.stringify({ error: 'Method not allowed' }) };
};
```

- [ ] **Step 3: Atualizar `netlify.toml` — adicionar redirect ANTES do wildcard**

O arquivo atual tem dois redirects. Inserir o `/api/config` como segundo redirect (depois do auth-settings, antes do wildcard):

```toml
[functions]
  directory = "netlify/functions"

[[redirects]]
  from = "/api/auth-settings"
  to = "/.netlify/functions/auth-settings"
  status = 200
  force = true

[[redirects]]
  from = "/api/config"
  to = "/.netlify/functions/config"
  status = 200
  force = true

[[redirects]]
  from = "/api/*"
  to = "https://nxticket.com.br/api/:splat"
  status = 200
  force = true
```

- [ ] **Step 4: Atualizar `.gitignore`**

Adicionar `.env` ao `.gitignore` para não commitar credenciais locais:

Arquivo `.gitignore` atual:
```
nul
check-api.html
```

Novo conteúdo:
```
nul
check-api.html
.env
```

- [ ] **Step 5: Criar `.env` local para testar com `netlify dev`**

Criar `.env` na raiz do projeto (NÃO commitar — já está no .gitignore):

```
SUPABASE_URL=https://SEU-PROJETO.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGci...  (service_role key do Supabase)
SETTINGS_PASSWORD=<sua_senha_de_admin>
```

Obter os valores em:
- `SUPABASE_URL`: Supabase → seu projeto → Settings → API → Project URL
- `SUPABASE_SERVICE_KEY`: Supabase → seu projeto → Settings → API → service_role key (não a anon key!)
- `SETTINGS_PASSWORD`: mesmo valor que está configurado nas env vars do Netlify

- [ ] **Step 6: Testar GET com `netlify dev`**

```bash
netlify dev
# Aguardar inicialização (porta 8888 por padrão)
```

Em outro terminal:

```bash
curl http://localhost:8888/api/config
```

Resultado esperado: `{}` (tabela vazia ainda)

- [ ] **Step 7: Testar POST para inserir primeira linha**

```bash
curl -X POST http://localhost:8888/api/config \
  -H "Content-Type: application/json" \
  -d '{"password":"<SETTINGS_PASSWORD>","token":"<SEU_TOKEN_CHATWOOT>","account":1,"sla_tma":8,"sla_tmr":30,"sla_fcr":85,"sla_msg":10,"threshold":0,"refresh_sec":60,"weight_tma":25,"weight_tmr":25,"weight_fcr":25,"weight_msg":25,"weight_csat":0}'
```

Resultado esperado: `{"ok":true}`

Verificar no Supabase Table Editor: linha aparece com todos os valores.

- [ ] **Step 8: Testar GET após inserção**

```bash
curl http://localhost:8888/api/config
```

Resultado esperado: JSON com `token`, `account`, `sla_tma`, etc.

- [ ] **Step 9: Commitar**

```bash
git add netlify/functions/config.js netlify.toml .gitignore
git commit -m "feat: netlify function GET+POST /api/config via supabase"
```

---

### Task 2: Settings page — card "Conexão Chatwoot" + saveConfig() async

**Files:**
- Modify: `index.html` — seção config-page (~linha 968), loadConfigPage() (~linha 3458), saveConfig() (~linha 3483), checkSettingsPassword() (~linha 1150), globals (~linha 1088)

**Interfaces:**
- Consumes: `POST /api/config` produzido na Task 1
- Produces: `_settingsPassword` (string, em memória) — senha capturada no modal e usada no POST
- Produces: `cfg.token`, `cfg.account` atualizados em memória após saveConfig()

- [ ] **Step 1: Adicionar variável global `_settingsPassword`**

Localizar na linha ~1088 (logo após o bloco `let cfg = {...}`):

```javascript
let cfg = {
  account:   localStorage.getItem('grv_account')   || '1',
  threshold: parseInt(localStorage.getItem('grv_threshold') || '0', 10) || 0,
  token:     localStorage.getItem('grv_token')      || ''
};
```

Adicionar a linha abaixo após o `};`:

```javascript
let _settingsPassword = '';
```

Resultado esperado: variável declarada globalmente, valor inicial string vazia.

- [ ] **Step 2: Capturar senha em `checkSettingsPassword()`**

Localizar a função `checkSettingsPassword()` (~linha 1150). Encontrar o bloco `if (data.ok)` e adicionar `_settingsPassword = password;` como primeira linha dentro dele:

**Antes:**
```javascript
    if (data.ok) {
      localStorage.setItem('grv_settings_auth', '1');
      document.getElementById('settings-auth-modal').classList.add('hidden');
      showPage('configuracoes');
```

**Depois:**
```javascript
    if (data.ok) {
      _settingsPassword = password;
      localStorage.setItem('grv_settings_auth', '1');
      document.getElementById('settings-auth-modal').classList.add('hidden');
      showPage('configuracoes');
```

- [ ] **Step 3: Adicionar card "Conexão Chatwoot" no config-page HTML**

Localizar a linha ~968 (início da `config-page`):

```html
<!-- CONFIG PAGE -->
<div id="config-page" style="display:none;background:var(--bg);min-height:calc(100vh - 56px);margin-left:52px">
  <div class="config-page">
    <h2 style="margin:0;font-size:18px;font-weight:700;color:var(--text)">Configurações</h2>

    <!-- SLAs -->
    <div class="config-card">
```

Inserir o novo card entre o `<h2>` e o `<!-- SLAs -->`:

```html
<!-- CONFIG PAGE -->
<div id="config-page" style="display:none;background:var(--bg);min-height:calc(100vh - 56px);margin-left:52px">
  <div class="config-page">
    <h2 style="margin:0;font-size:18px;font-weight:700;color:var(--text)">Configurações</h2>

    <!-- Conexão Chatwoot -->
    <div class="config-card">
      <h3>Conexão Chatwoot</h3>
      <div class="config-row">
        <div>
          <div class="config-label">Token API</div>
          <div class="config-unit">Chatwoot → Perfil → Token de acesso à API</div>
        </div>
        <div style="display:flex;gap:6px;align-items:center">
          <input type="password" class="config-input" id="cfg-token" autocomplete="off" placeholder="api_access_token" style="width:200px" />
          <button onclick="toggleCfgTokenVisibility()" title="Mostrar/ocultar token" style="background:none;border:1px solid var(--border);border-radius:5px;padding:4px 8px;cursor:pointer;color:var(--text2);font-size:13px;height:34px">👁</button>
        </div>
      </div>
      <div class="config-row">
        <div>
          <div class="config-label">Conta (Account ID)</div>
          <div class="config-unit">Número da conta no Chatwoot</div>
        </div>
        <input type="number" class="config-input" id="cfg-account-field" min="1" step="1" />
      </div>
      <div id="cfg-sync-status" style="font-size:12px;color:var(--text3);margin-top:4px;padding:0 4px"></div>
    </div>

    <!-- SLAs -->
    <div class="config-card">
```

Nota: o campo de account usa `id="cfg-account-field"` (não `cfg-account`, que seria ambíguo com o hidden input do modal original).

- [ ] **Step 4: Adicionar `toggleCfgTokenVisibility()` ao JS**

Localizar a função `updateWeightSum()` (~linha 3473) e inserir ANTES dela:

```javascript
function toggleCfgTokenVisibility() {
  const inp = document.getElementById('cfg-token');
  inp.type = inp.type === 'password' ? 'text' : 'password';
}
```

- [ ] **Step 5: Atualizar `loadConfigPage()` para popular os novos campos**

Localizar `loadConfigPage()` (~linha 3458):

```javascript
function loadConfigPage() {
  document.getElementById('cfg-sla-tma').value    = _SLA_TMA;
  document.getElementById('cfg-sla-tmr').value    = _SLA_TMR;
  document.getElementById('cfg-sla-fcr').value    = _SLA_FCR;
  document.getElementById('cfg-sla-msg').value    = _SLA_MSG;
  document.getElementById('cfg-threshold').value  = cfg.threshold;
  document.getElementById('cfg-refresh').value    = REFRESH_SEC;
  document.getElementById('cfg-weight-tma').value  = _WEIGHT_TMA;
  document.getElementById('cfg-weight-tmr').value  = _WEIGHT_TMR;
  document.getElementById('cfg-weight-fcr').value  = _WEIGHT_FCR;
  document.getElementById('cfg-weight-msg').value  = _WEIGHT_MSG;
  document.getElementById('cfg-weight-csat').value = _WEIGHT_CSAT;
  updateWeightSum();
}
```

Substituir por:

```javascript
function loadConfigPage() {
  document.getElementById('cfg-token').value        = cfg.token || '';
  document.getElementById('cfg-account-field').value = cfg.account || '1';
  document.getElementById('cfg-sla-tma').value      = _SLA_TMA;
  document.getElementById('cfg-sla-tmr').value      = _SLA_TMR;
  document.getElementById('cfg-sla-fcr').value      = _SLA_FCR;
  document.getElementById('cfg-sla-msg').value      = _SLA_MSG;
  document.getElementById('cfg-threshold').value    = cfg.threshold;
  document.getElementById('cfg-refresh').value      = REFRESH_SEC;
  document.getElementById('cfg-weight-tma').value   = _WEIGHT_TMA;
  document.getElementById('cfg-weight-tmr').value   = _WEIGHT_TMR;
  document.getElementById('cfg-weight-fcr').value   = _WEIGHT_FCR;
  document.getElementById('cfg-weight-msg').value   = _WEIGHT_MSG;
  document.getElementById('cfg-weight-csat').value  = _WEIGHT_CSAT;
  document.getElementById('cfg-sync-status').textContent = '';
  updateWeightSum();
}
```

- [ ] **Step 6: Substituir `saveConfig()` por versão async com POST /api/config**

Localizar `saveConfig()` (~linha 3483) e substituir a função inteira por:

```javascript
async function saveConfig() {
  const slaTma  = Math.max(1,  parseInt(document.getElementById('cfg-sla-tma').value,    10) || 8);
  const slaTmr  = Math.max(1,  parseInt(document.getElementById('cfg-sla-tmr').value,    10) || 30);
  const slaFcr  = Math.max(1,  parseInt(document.getElementById('cfg-sla-fcr').value,    10) || 85);
  const slaMsg  = Math.max(1,  parseInt(document.getElementById('cfg-sla-msg').value,    10) || 10);
  const thr     = Math.max(0,  parseInt(document.getElementById('cfg-threshold').value,  10) || 0);
  const refresh = Math.max(15, parseInt(document.getElementById('cfg-refresh').value,    10) || 60);
  const wTma    = parseInt(document.getElementById('cfg-weight-tma').value,  10) || 0;
  const wTmr    = parseInt(document.getElementById('cfg-weight-tmr').value,  10) || 0;
  const wFcr    = parseInt(document.getElementById('cfg-weight-fcr').value,  10) || 0;
  const wMsg    = parseInt(document.getElementById('cfg-weight-msg').value,  10) || 0;
  const wCsat   = parseInt(document.getElementById('cfg-weight-csat').value, 10) || 0;
  const token   = (document.getElementById('cfg-token').value         || '').trim();
  const account = (document.getElementById('cfg-account-field').value || '1').trim();

  if (wTma + wTmr + wFcr + wMsg + wCsat !== 100) return;

  const saveBtn = document.getElementById('cfg-save-btn');
  saveBtn.disabled = true;
  saveBtn.textContent = 'Salvando...';

  let syncOk = false;
  try {
    const res = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        password:    _settingsPassword,
        token,
        account:     parseInt(account, 10) || 1,
        sla_tma:     slaTma,
        sla_tmr:     slaTmr,
        sla_fcr:     slaFcr,
        sla_msg:     slaMsg,
        threshold:   thr,
        refresh_sec: refresh,
        weight_tma:  wTma,
        weight_tmr:  wTmr,
        weight_fcr:  wFcr,
        weight_msg:  wMsg,
        weight_csat: wCsat,
      }),
    });
    const data = await res.json();
    if (!data.ok) {
      showToast('Senha inválida — não foi possível sincronizar com o Supabase');
      saveBtn.disabled = false;
      saveBtn.textContent = 'Salvar configurações';
      return;
    }
    syncOk = true;
  } catch {
    showToast('Supabase indisponível — configurações salvas apenas localmente');
  }

  cfg.token     = token;
  cfg.account   = account;
  cfg.threshold = thr;
  _SLA_TMA      = slaTma;
  _SLA_TMR      = slaTmr;
  _SLA_FCR      = slaFcr;
  _SLA_MSG      = slaMsg;
  REFRESH_SEC   = refresh;
  _WEIGHT_TMA   = wTma;
  _WEIGHT_TMR   = wTmr;
  _WEIGHT_FCR   = wFcr;
  _WEIGHT_MSG   = wMsg;
  _WEIGHT_CSAT  = wCsat;

  localStorage.setItem('grv_token',       token);
  localStorage.setItem('grv_account',     account);
  localStorage.setItem('grv_threshold',   thr);
  localStorage.setItem('grv_sla_tma',     slaTma);
  localStorage.setItem('grv_sla_tmr',     slaTmr);
  localStorage.setItem('grv_sla_fcr',     slaFcr);
  localStorage.setItem('grv_sla_msg',     slaMsg);
  localStorage.setItem('grv_refresh_sec', refresh);
  localStorage.setItem('grv_weight_tma',  wTma);
  localStorage.setItem('grv_weight_tmr',  wTmr);
  localStorage.setItem('grv_weight_fcr',  wFcr);
  localStorage.setItem('grv_weight_msg',  wMsg);
  localStorage.setItem('grv_weight_csat', wCsat);

  _agentPerfData   = null;
  _agentMonthCache = {};

  const overlay = document.getElementById('onboarding-overlay');
  if (overlay) overlay.classList.add('hidden');

  saveBtn.disabled = false;
  saveBtn.textContent = 'Salvar configurações';

  showToast(syncOk ? 'Configurações salvas e sincronizadas' : 'Configurações salvas localmente');
  startDashboard();
  showPage('painel');
}
```

- [ ] **Step 7: Testar na UI com `netlify dev`**

Abrir http://localhost:8888 → clicar Config. → digitar senha → na página de Configurações:
- O campo Token deve mostrar o token atual (vindo do localStorage/cfg)
- O campo Account deve mostrar o account atual
- Alterar alguma SLA → Salvar → toast "Configurações salvas e sincronizadas" deve aparecer
- Verificar no Supabase Table Editor que os valores foram atualizados

- [ ] **Step 8: Commitar**

```bash
git add index.html
git commit -m "feat: settings page com conexao chatwoot e saveConfig async via supabase"
```

---

### Task 3: Startup flow com loadRemoteConfig() + remoção do token modal

**Files:**
- Modify: `index.html` — múltiplas seções

**Interfaces:**
- Consumes: `GET /api/config` produzido na Task 1
- Consumes: `applyRemoteConfig(data)` — definida nesta task
- Produces: startup flow sem modal de token; onboarding overlay para primeiro acesso

- [ ] **Step 1: Adicionar HTML — onboarding overlay, migrate banner e offline banner**

Localizar a linha após o `#config-page` div de fechamento (~linha 1062):

```html
</div>
</div>

<script>
```

Inserir ANTES do `<script>`:

```html
<!-- ONBOARDING OVERLAY (Caso B: sem token em lugar nenhum) -->
<div id="onboarding-overlay" class="hidden" style="position:fixed;inset:0;background:var(--bg);display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:8000;gap:16px;padding:24px">
  <div style="font-size:48px;line-height:1">⚙</div>
  <h2 style="margin:0;font-size:22px;color:var(--text)">Bem-vindo ao GRV SAC</h2>
  <p style="margin:0;color:var(--text2);text-align:center;max-width:380px;line-height:1.6">Configure o token do Chatwoot para começar a usar o dashboard.</p>
  <button class="btn-primary" onclick="openSettingsFromOnboarding()">Configurar agora</button>
</div>

<!-- MIGRATE BANNER (Caso A: tem token local, Supabase vazio) -->
<div id="migrate-banner" class="hidden" style="position:fixed;top:0;left:0;right:0;background:var(--accent);color:#fff;padding:10px 16px;z-index:7999;display:flex;align-items:center;gap:12px;font-size:13px">
  <span>Config local encontrada. Deseja sincronizar com o Supabase?</span>
  <button onclick="syncLocalToSupabase()" style="background:#fff;color:var(--accent);border:none;border-radius:5px;padding:4px 12px;cursor:pointer;font-weight:600;font-size:13px">Sincronizar agora</button>
  <button onclick="dismissMigrate()" style="background:none;border:none;color:#fff;cursor:pointer;margin-left:auto;font-size:20px;line-height:1;padding:0 4px">×</button>
</div>

<!-- OFFLINE BANNER (Supabase indisponível, usando localStorage) -->
<div id="offline-banner" class="hidden" style="position:fixed;top:0;left:0;right:0;background:var(--bg2);border-bottom:1px solid var(--border);color:var(--text3);padding:6px 16px;z-index:7999;font-size:12px">
  ⚠ Usando config local — Supabase indisponível
</div>
```

- [ ] **Step 2: Adicionar funções `applyRemoteConfig()`, `loadRemoteConfig()` e helpers**

Localizar a linha logo após `let _settingsPassword = '';` (adicionada na Task 2, linha ~1090) e inserir as novas funções:

```javascript
function applyRemoteConfig(data) {
  const ri = (v, d) => { const n = parseInt(v, 10); return Number.isFinite(n) ? n : d; };
  cfg.token     = data.token     || '';
  cfg.account   = String(data.account || '1');
  cfg.threshold = ri(data.threshold,  0);
  _SLA_TMA      = ri(data.sla_tma,   8);
  _SLA_TMR      = ri(data.sla_tmr,   30);
  _SLA_FCR      = ri(data.sla_fcr,   85);
  _SLA_MSG      = ri(data.sla_msg,   10);
  REFRESH_SEC   = ri(data.refresh_sec, 60);
  const wTma  = ri(data.weight_tma,  25);
  const wTmr  = ri(data.weight_tmr,  25);
  const wFcr  = ri(data.weight_fcr,  25);
  const wMsg  = ri(data.weight_msg,  25);
  const wCsat = ri(data.weight_csat, 0);
  if (wTma + wTmr + wFcr + wMsg + wCsat === 100) {
    _WEIGHT_TMA = wTma; _WEIGHT_TMR = wTmr; _WEIGHT_FCR = wFcr;
    _WEIGHT_MSG = wMsg; _WEIGHT_CSAT = wCsat;
  }
  localStorage.setItem('grv_token',       cfg.token);
  localStorage.setItem('grv_account',     cfg.account);
  localStorage.setItem('grv_threshold',   cfg.threshold);
  localStorage.setItem('grv_sla_tma',     _SLA_TMA);
  localStorage.setItem('grv_sla_tmr',     _SLA_TMR);
  localStorage.setItem('grv_sla_fcr',     _SLA_FCR);
  localStorage.setItem('grv_sla_msg',     _SLA_MSG);
  localStorage.setItem('grv_refresh_sec', REFRESH_SEC);
  localStorage.setItem('grv_weight_tma',  _WEIGHT_TMA);
  localStorage.setItem('grv_weight_tmr',  _WEIGHT_TMR);
  localStorage.setItem('grv_weight_fcr',  _WEIGHT_FCR);
  localStorage.setItem('grv_weight_msg',  _WEIGHT_MSG);
  localStorage.setItem('grv_weight_csat', _WEIGHT_CSAT);
}

async function loadRemoteConfig() {
  try {
    const res = await fetch('/api/config');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    if (data.token) {
      applyRemoteConfig(data);
      return 'ok';
    }
    return localStorage.getItem('grv_token') ? 'migrate' : 'setup';
  } catch(e) {
    if (localStorage.getItem('grv_token')) {
      document.getElementById('offline-banner').classList.remove('hidden');
      return 'offline';
    }
    return 'setup';
  }
}

function openSettingsFromOnboarding() {
  document.getElementById('onboarding-overlay').classList.add('hidden');
  openSettings();
}

function dismissMigrate() {
  document.getElementById('migrate-banner').classList.add('hidden');
}

function syncLocalToSupabase() {
  document.getElementById('migrate-banner').classList.add('hidden');
  openSettings();
}
```

- [ ] **Step 3: Substituir bloco de startup — trocar `if (cfg.token)` por `loadRemoteConfig()`**

Localizar (~linha 1216):

```javascript
if (cfg.token) {
  document.getElementById('token-modal').classList.add('hidden');
  updateConnStatus();
  startDashboard();
} else {
  showTokenModal();
}
```

Substituir por:

```javascript
loadRemoteConfig().then(function(result) {
  if (result === 'ok' || result === 'offline') {
    startDashboard();
  } else if (result === 'migrate') {
    document.getElementById('migrate-banner').classList.remove('hidden');
    startDashboard();
  } else {
    document.getElementById('onboarding-overlay').classList.remove('hidden');
  }
});
```

- [ ] **Step 4: Corrigir fallback de 401 em `startDashboard()`**

Localizar (~linha 1507):

```javascript
    if (e.status === 401) {
      clearInterval(timer);
      cfg.token = '';
      localStorage.removeItem('grv_token');
      updateConnStatus();
      showTokenModal();
      document.getElementById('modal-error').textContent = 'Token inválido ou expirado. Insira novamente.';
      document.getElementById('modal-error').style.display = '';
      return;
    }
```

Substituir por:

```javascript
    if (e.status === 401) {
      clearInterval(timer);
      cfg.token = '';
      localStorage.removeItem('grv_token');
      showToast('Token inválido ou expirado. Atualize o token nas Configurações.');
      document.getElementById('onboarding-overlay').classList.remove('hidden');
      return;
    }
```

- [ ] **Step 5: Remover `#token-modal` do HTML**

Localizar e remover o bloco completo (~linhas 489-506):

```html
<div id="token-modal">
  <div class="modal-box">
    <h2>Conectar ao Chatwoot</h2>
    <div class="modal-error" id="modal-error"></div>
    <label for="inp-token">Token de acesso</label>
    <input type="password" id="inp-token" placeholder="Cole aqui seu api_access_token"
      autocomplete="off" onkeydown="if(event.key==='Enter') saveToken()" />
    <p class="hint">Chatwoot → Perfil → Token de acesso à API</p>
    <hr class="modal-divider">
    <label for="inp-account">ID da Conta Chatwoot</label>
    <input type="number" id="inp-account" value="1" />
    <hr class="modal-divider">
    <label for="inp-threshold">Alerta de fila — avisar quando aguardando ≥</label>
    <input type="number" id="inp-threshold" placeholder="Ex: 5  (0 = desativado)" min="0" />
    <p class="hint">Badge fica pulsante quando a fila de espera atingir esse número</p>
    <button class="btn-primary" onclick="saveToken()">Salvar e conectar</button>
  </div>
</div>
```

Remover todo o bloco — não substituir por nada.

- [ ] **Step 6: Remover `#nav-connect` do sidebar**

Localizar e remover (~linhas 522-526):

```html
    <div class="sidebar-item" id="nav-connect" onclick="showTokenModal()" title="Clique para conectar ao Chatwoot">
      <span class="sidebar-icon" id="conn-icon">●</span>
      <span class="sidebar-label" id="conn-label">Conectar</span>
    </div>
```

Remover todo o bloco. O botão `openSettings()` logo abaixo permanece.

- [ ] **Step 7: Remover CSS do token modal e nav-connect**

Localizar e remover as linhas de CSS (~linhas 27-28):

```css
#token-modal { position:fixed; inset:0; background:rgba(0,0,0,.82); backdrop-filter:blur(4px); display:flex; align-items:center; justify-content:center; z-index:9999; }
#token-modal.hidden { display:none; }
```

Remover ambas.

Localizar e remover (~linhas 153-157):

```css
#nav-connect { opacity:.8; }
#nav-connect:hover { opacity:1; }
#conn-icon { font-size:9px; transition:color .3s; }
#conn-icon.connected    { color:#4ade80; }
#conn-icon.disconnected { color:#f59e0b; animation:pulse-badge 2s ease-in-out infinite; }
```

Remover todas as 5 linhas.

- [ ] **Step 8: Remover funções `updateConnStatus()`, `showTokenModal()` e `saveToken()`**

Localizar e remover o bloco completo (~linhas 1176-1214):

```javascript
function updateConnStatus() {
  const icon  = document.getElementById('conn-icon');
  const label = document.getElementById('conn-label');
  if (!icon || !label) return;
  const ok = !!cfg.token;
  icon.className    = ok ? 'connected' : 'disconnected';
  label.textContent = ok ? 'Conectado' : 'Conectar';
  const nav = document.getElementById('nav-connect');
  if (nav) nav.title = ok ? `Conta ${cfg.account} · clique para alterar conexão` : 'Clique para conectar ao Chatwoot';
}
function showTokenModal() {
  document.getElementById('inp-token').value     = cfg.token || '';
  document.getElementById('inp-account').value   = cfg.account;
  document.getElementById('inp-threshold').value = cfg.threshold || '';
  const errEl = document.getElementById('modal-error');
  errEl.style.display = 'none';
  errEl.textContent   = '';
  document.getElementById('token-modal').classList.remove('hidden');
  setTimeout(() => document.getElementById('inp-token').focus(), 50);
}
function saveToken() {
  const token     = document.getElementById('inp-token').value.trim();
  const account   = document.getElementById('inp-account').value.trim() || '1';
  const threshold = parseInt(document.getElementById('inp-threshold').value, 10) || 0;
  if (!token) {
    const errEl = document.getElementById('modal-error');
    errEl.textContent   = 'Token obrigatório.';
    errEl.style.display = '';
    document.getElementById('inp-token').focus();
    return;
  }
  localStorage.setItem('grv_token',     token);
  localStorage.setItem('grv_account',   account);
  localStorage.setItem('grv_threshold', threshold);
  cfg = { token, account, threshold };
  document.getElementById('token-modal').classList.add('hidden');
  updateConnStatus();
  startDashboard();
}
```

Remover todo o bloco.

- [ ] **Step 9: Verificar na UI — fluxo completo**

Com `netlify dev` rodando:

1. Limpar localStorage: DevTools → Application → Local Storage → Clear all
2. Recarregar http://localhost:8888 — deve aparecer o onboarding overlay "Bem-vindo"
3. Clicar "Configurar agora" → modal de senha → inserir senha → página de Configurações
4. Preencher o token do Chatwoot e account `1` → Salvar → toast "Configurações salvas e sincronizadas"
5. Dashboard deve iniciar automaticamente
6. Recarregar a página — dashboard deve iniciar direto (sem overlay) com config do Supabase
7. Verificar que NÃO aparece botão "Conectar" no sidebar

- [ ] **Step 10: Commitar**

```bash
git add index.html
git commit -m "feat: startup via supabase, remove token modal, onboarding overlay"
```

---

### Task 4: Configurar variáveis de ambiente no Netlify + deploy

**Files:**
- Nenhum arquivo — configuração externa

**Interfaces:**
- Consumes: valores do Supabase (URL, service key)
- Produces: dashboard em produção sincronizando config via Supabase

- [ ] **Step 1: Adicionar env vars no Netlify**

Netlify Dashboard → seu projeto → Site configuration → Environment variables → Add variable:

| Key | Value | Scope |
|---|---|---|
| `SUPABASE_URL` | `https://SEU-PROJETO.supabase.co` | Production |
| `SUPABASE_SERVICE_KEY` | `eyJhbGci...` (service_role key do Supabase) | Production |

`SETTINGS_PASSWORD` já existe — não alterar.

- [ ] **Step 2: Push e deploy**

```bash
git push origin alteracoes
```

Fazer merge no GitHub (PR para `main`) → Netlify faz deploy automático.

- [ ] **Step 3: Verificar em produção**

Acessar a URL do Netlify:
1. GET https://SEU-SITE.netlify.app/api/config → deve retornar JSON com o token
2. Abrir o dashboard → deve iniciar direto (sem overlay) pois o Supabase já tem a linha populada da Task 1

Se aparecer o onboarding overlay: o Supabase está vazio ou as env vars não estão configuradas → verificar Netlify → Site configuration → Environment variables.

- [ ] **Step 4: Testar em uma segunda máquina / aba anônima**

Abrir o dashboard em aba anônima ou outra máquina — deve iniciar direto, sem pedir token, mostrando os dados da conta configurada pelo admin.
