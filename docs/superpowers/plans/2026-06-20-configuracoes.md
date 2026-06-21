# Página de Configurações — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar uma página de configurações protegida por senha, acessível via ícone ⚙ no rodapé do sidebar, para editar SLAs, alerta de fila, intervalo de atualização e pesos da pontuação de agentes.

**Architecture:** A senha fica em `server.js` como `SETTINGS_PASSWORD`; o browser envia `POST /api/auth-settings` para verificar, e o servidor responde `{ok: true/false}` sem expor a senha ao cliente. Uma vez autenticado, o browser armazena `grv_settings_auth=1` em `localStorage`. A página de configurações segue o padrão existente de `showPage()` com uma `<div id="config-page">`.

**Tech Stack:** Node.js (server), HTML/CSS/JS vanilla (cliente), Chart.js 4 (não alterado), localStorage (persistência)

## Global Constraints

- Arquivo único: todas as mudanças de frontend vão em `index.html` (atualmente ~3065 linhas)
- Sem dependências novas — zero bibliotecas externas
- Português em todos os textos do usuário
- `server.js` deve continuar funcional sem reinicialização a não ser quando `SETTINGS_PASSWORD` for alterada
- Mínimo de intervalo de atualização: 15 segundos
- Pesos devem somar exatamente 100 para salvar

---

## Arquivos

| Arquivo | Ação | O que muda |
|---|---|---|
| `server.js` | Modificar | Adicionar `SETTINGS_PASSWORD`, rota `POST /api/auth-settings` |
| `index.html` | Modificar | CSS sidebar-footer, HTML sidebar ⚙ + modal senha + página config, JS variáveis + funções |

---

## Task 1: server.js — endpoint de autenticação

**Files:**
- Modify: `server.js:7-15`

**Interfaces:**
- Produces: `POST /api/auth-settings` — aceita `{password: string}`, retorna `{ok: boolean}`

- [ ] **Step 1: Adicionar SETTINGS_PASSWORD e rota de autenticação**

Substituir o bloco atual do servidor (linhas 7-30) pelo código abaixo. A rota `POST /api/auth-settings` deve ser checada **antes** do bloco `/api/` proxy para evitar que o proxy intercepte a requisição.

```javascript
const PORT = 8765;
const TARGET = 'nxticket.com.br';
const DIR = __dirname;
const TOKEN = 'rzpghGjyG4cDVYg4tNjSpJBD';
const SETTINGS_PASSWORD = 'grv2026';

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.ico': 'image/x-icon' };

http.createServer((req, res) => {
  // Autenticação de configurações
  if (req.method === 'POST' && req.url === '/api/auth-settings') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const { password } = JSON.parse(body);
        const ok = password === SETTINGS_PASSWORD;
        res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ ok }));
      } catch {
        res.writeHead(400);
        res.end('Bad request');
      }
    });
    return;
  }

  if (req.url.startsWith('/api/')) {
    // Proxy para nxticket.com.br
    const fwd = { 'api_access_token': TOKEN };
    const opts = {
      hostname: TARGET,
      path: req.url,
      method: req.method,
      headers: { 'Accept': 'application/json', ...fwd }
    };
    const proxy = https.request(opts, r => {
      res.writeHead(r.statusCode, { 'Content-Type': r.headers['content-type'] || 'application/json', 'Access-Control-Allow-Origin': '*' });
      r.pipe(res);
    });
    proxy.on('error', e => { res.writeHead(502); res.end(e.message); });
    proxy.end();
  } else {
    // Arquivos estáticos
    const filePath = path.join(DIR, req.url === '/' ? 'index.html' : req.url);
    if (!filePath.startsWith(DIR + path.sep) && filePath !== path.join(DIR, 'index.html')) {
      res.writeHead(403); res.end('Forbidden'); return;
    }
    fs.readFile(filePath, (err, data) => {
      if (err) { res.writeHead(404); res.end('Not found'); return; }
      const ext = path.extname(filePath);
      res.writeHead(200, { 'Content-Type': (MIME[ext] || 'text/plain') + '; charset=utf-8' });
      res.end(data);
    });
  }
}).listen(PORT, () => {
  console.log(`\n  GRV SAC Dashboard → http://localhost:${PORT}\n  Ctrl+C para parar.\n`);
});
```

> **Nota:** `SETTINGS_PASSWORD = 'grv2026'` é o valor padrão. O responsável pelo deploy deve alterar para a senha real antes de compartilhar o dashboard.

- [ ] **Step 2: Testar o endpoint manualmente**

Reiniciar o servidor (`Ctrl+C` + `node server.js`). Depois, num segundo terminal:

```bash
# Senha correta
curl -s -X POST http://localhost:8765/api/auth-settings -H "Content-Type: application/json" -d "{\"password\":\"grv2026\"}"
# Esperado: {"ok":true}

# Senha errada
curl -s -X POST http://localhost:8765/api/auth-settings -H "Content-Type: application/json" -d "{\"password\":\"errada\"}"
# Esperado: {"ok":false}
```

- [ ] **Step 3: Commit**

```bash
git add server.js
git commit -m "feat(config): endpoint POST /api/auth-settings para verificação de senha"
```

---

## Task 2: Variáveis de configuração dinâmicas

**Files:**
- Modify: `index.html:851` (REFRESH_SEC), `index.html:874` (countdown), `index.html:887-895` (SLA vars)

**Interfaces:**
- Produces: `let REFRESH_SEC`, `let _WEIGHT_TMA`, `let _WEIGHT_TMR`, `let _WEIGHT_FCR`, `let _WEIGHT_MSG` — todas legíveis e reatribuíveis a partir de qualquer função JS da página

- [ ] **Step 1: Converter REFRESH_SEC para let e carregar do localStorage**

Localizar linha 851. Substituir:

```javascript
const REFRESH_SEC = 60;
```

Por:

```javascript
let REFRESH_SEC = parseInt(localStorage.getItem('grv_refresh_sec') || '60', 10);
```

- [ ] **Step 2: Carregar SLAs do localStorage na inicialização**

Localizar linhas 887-895 (bloco de variáveis SLA). Substituir:

```javascript
let _SLA_TMA = 8;      /* horas — meta de TMA */
let _SLA_TMR = 30;     /* minutos — meta de TMR */
let _SLA_FCR = 85;     /* % — meta de taxa de resolução */
let _SLA_MSG = 10;     /* mensagens — meta de eficiência por conversa */
```

Por:

```javascript
let _SLA_TMA = parseInt(localStorage.getItem('grv_sla_tma') || '8',  10);
let _SLA_TMR = parseInt(localStorage.getItem('grv_sla_tmr') || '30', 10);
let _SLA_FCR = parseInt(localStorage.getItem('grv_sla_fcr') || '85', 10);
let _SLA_MSG = parseInt(localStorage.getItem('grv_sla_msg') || '10', 10);
let _WEIGHT_TMA = parseInt(localStorage.getItem('grv_weight_tma') || '25', 10);
let _WEIGHT_TMR = parseInt(localStorage.getItem('grv_weight_tmr') || '25', 10);
let _WEIGHT_FCR = parseInt(localStorage.getItem('grv_weight_fcr') || '25', 10);
let _WEIGHT_MSG = parseInt(localStorage.getItem('grv_weight_msg') || '25', 10);
```

- [ ] **Step 3: Verificar que não há erros de console**

Abrir `http://localhost:8765` no browser. Abrir DevTools → Console. Não deve haver erros. O dashboard deve carregar normalmente.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat(config): variáveis SLA, REFRESH_SEC e pesos carregados do localStorage"
```

---

## Task 3: Ícone ⚙ no sidebar + modal de senha

**Files:**
- Modify: `index.html` — CSS (após `.sidebar-item.active {...}`), HTML sidebar (após linha 454), HTML modais (junto ao settings modal existente), JS (junto às funções de modal)

**Interfaces:**
- Consumes: `localStorage.getItem('grv_settings_auth')`, `POST /api/auth-settings`
- Produces: `openSettings()` — verifica auth e chama `showPage('configuracoes')` ou exibe modal de senha

- [ ] **Step 1: Adicionar CSS para sidebar footer**

Localizar no CSS o bloco `.sidebar-item.active { ... }` (linha ~149). Adicionar logo após:

```css
.sidebar-footer { margin-top:auto; border-top:1px solid var(--border); padding-top:4px; }
```

- [ ] **Step 2: Adicionar ícone ⚙ ao sidebar**

Localizar o bloco HTML do sidebar (linhas 441-454):

```html
<nav class="sidebar" id="sidebar" aria-label="Navegação principal">
  <div class="sidebar-item active" id="nav-painel" onclick="showPage('painel')" title="Painel">
    <span class="sidebar-icon">📊</span>
    <span class="sidebar-label">Painel</span>
  </div>
  <div class="sidebar-item" id="nav-agentes" onclick="showPage('agentes')" title="Agentes">
    <span class="sidebar-icon">👥</span>
    <span class="sidebar-label">Agentes</span>
  </div>
  <div class="sidebar-item" id="nav-graficos" onclick="showPage('graficos')" title="Análise">
    <span class="sidebar-icon">📈</span>
    <span class="sidebar-label">Análise</span>
  </div>
</nav>
```

Substituir por:

```html
<nav class="sidebar" id="sidebar" aria-label="Navegação principal">
  <div class="sidebar-item active" id="nav-painel" onclick="showPage('painel')" title="Painel">
    <span class="sidebar-icon">📊</span>
    <span class="sidebar-label">Painel</span>
  </div>
  <div class="sidebar-item" id="nav-agentes" onclick="showPage('agentes')" title="Agentes">
    <span class="sidebar-icon">👥</span>
    <span class="sidebar-label">Agentes</span>
  </div>
  <div class="sidebar-item" id="nav-graficos" onclick="showPage('graficos')" title="Análise">
    <span class="sidebar-icon">📈</span>
    <span class="sidebar-label">Análise</span>
  </div>
  <div class="sidebar-footer">
    <div class="sidebar-item" onclick="openSettings()" title="Configurações">
      <span class="sidebar-icon">⚙</span>
      <span class="sidebar-label">Config.</span>
    </div>
  </div>
</nav>
```

- [ ] **Step 3: Adicionar modal de senha de configurações**

Localizar o bloco `<!-- SETTINGS MODAL -->` existente (linhas ~425-442). Adicionar um novo modal **antes** desse bloco:

```html
<!-- SETTINGS AUTH MODAL -->
<div id="settings-auth-modal" class="hidden" style="position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:9999;display:flex;align-items:center;justify-content:center">
  <div class="modal-box" style="width:340px">
    <h2>Acesso Restrito</h2>
    <p style="font-size:13px;color:var(--text3);margin:0 0 14px">Digite a senha de administrador para acessar as configurações.</p>
    <div class="modal-error" id="settings-auth-error" style="display:none"></div>
    <input type="password" id="inp-settings-password" placeholder="Senha de administrador"
      autocomplete="off" style="width:100%;box-sizing:border-box"
      onkeydown="if(event.key==='Enter') checkSettingsPassword()" />
    <button class="btn-primary" style="margin-top:12px;width:100%" onclick="checkSettingsPassword()">Entrar</button>
    <button onclick="document.getElementById('settings-auth-modal').classList.add('hidden')"
      style="margin-top:8px;width:100%;padding:7px;border:none;background:none;color:var(--text3);cursor:pointer;font-size:13px">Cancelar</button>
  </div>
</div>
```

- [ ] **Step 4: Adicionar funções JS openSettings() e checkSettingsPassword()**

Localizar a função `showTokenModal()` (linha ~914). Adicionar as duas funções **logo antes** dela:

```javascript
function openSettings() {
  if (localStorage.getItem('grv_settings_auth') === '1') {
    showPage('configuracoes');
  } else {
    const errEl = document.getElementById('settings-auth-error');
    errEl.style.display = 'none';
    document.getElementById('inp-settings-password').value = '';
    document.getElementById('settings-auth-modal').classList.remove('hidden');
    setTimeout(() => document.getElementById('inp-settings-password').focus(), 50);
  }
}

async function checkSettingsPassword() {
  const password = document.getElementById('inp-settings-password').value;
  const errEl    = document.getElementById('settings-auth-error');
  errEl.style.display = 'none';
  try {
    const res  = await fetch('/api/auth-settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    });
    const data = await res.json();
    if (data.ok) {
      localStorage.setItem('grv_settings_auth', '1');
      document.getElementById('settings-auth-modal').classList.add('hidden');
      showPage('configuracoes');
    } else {
      errEl.textContent   = 'Senha incorreta.';
      errEl.style.display = 'block';
      document.getElementById('inp-settings-password').select();
    }
  } catch {
    errEl.textContent   = 'Erro ao verificar senha. Tente novamente.';
    errEl.style.display = 'block';
  }
}
```

- [ ] **Step 5: Verificar no browser**

1. Recarregar `http://localhost:8765`
2. O ícone ⚙ deve aparecer no rodapé do sidebar
3. Clicar ⚙ → deve abrir o modal "Acesso Restrito"
4. Digitar senha errada → deve exibir "Senha incorreta."
5. Digitar `grv2026` → modal fecha (a página de configurações ainda não existe — é normal)
6. Recarregar a página e clicar ⚙ novamente → deve pular o modal (auth salva no localStorage)

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat(config): ícone ⚙ no sidebar e modal de autenticação por senha"
```

---

## Task 4: Página de configurações — HTML e CSS

**Files:**
- Modify: `index.html` — adicionar `<div id="config-page">` antes da tag `<script>` (linha ~849), adicionar CSS para os campos da página

**Interfaces:**
- Consumes: `_SLA_TMA`, `_SLA_TMR`, `_SLA_FCR`, `_SLA_MSG`, `REFRESH_SEC`, `_WEIGHT_TMA/TMR/FCR/MSG`, `cfg.threshold`
- Produces: elementos HTML com IDs: `cfg-sla-tma`, `cfg-sla-tmr`, `cfg-sla-fcr`, `cfg-sla-msg`, `cfg-threshold`, `cfg-refresh`, `cfg-weight-tma`, `cfg-weight-tmr`, `cfg-weight-fcr`, `cfg-weight-msg`, `cfg-weight-sum`, `cfg-save-btn`

- [ ] **Step 1: Adicionar CSS para a página de configurações**

Localizar o bloco `/* Mobile */` no CSS (linha ~411). Adicionar **antes** dele:

```css
/* CONFIG PAGE */
.config-page { padding:24px 32px; max-width:640px; display:flex; flex-direction:column; gap:20px; }
.config-card { background:var(--bg2); border:1px solid var(--border); border-radius:10px; padding:20px 24px; }
.config-card h3 { margin:0 0 16px; font-size:14px; font-weight:600; color:var(--text); }
.config-row { display:grid; grid-template-columns:1fr 180px; align-items:center; gap:8px; margin-bottom:12px; }
.config-row:last-child { margin-bottom:0; }
.config-label { font-size:13px; color:var(--text); }
.config-unit { font-size:11px; color:var(--text3); margin-top:2px; }
.config-input { width:100%; padding:7px 10px; border:1px solid var(--border); border-radius:6px;
  background:var(--bg3); color:var(--text); font-size:14px; box-sizing:border-box; text-align:right; }
.config-input:focus { outline:none; border-color:var(--accent); }
.config-actions { display:flex; gap:10px; }
.config-weight-sum { font-size:12px; margin-top:12px; padding:8px 12px; border-radius:6px;
  background:var(--bg3); text-align:center; }
.config-weight-sum.ok  { color:#22c55e; }
.config-weight-sum.err { color:#ef4444; }
```

- [ ] **Step 2: Adicionar HTML da página de configurações**

Localizar a linha em branco antes de `<script>` (linha ~849). Inserir antes dela:

```html
<!-- CONFIG PAGE -->
<div id="config-page" style="display:none;background:var(--bg);min-height:calc(100vh - 56px);margin-left:52px">
  <div class="config-page">
    <h2 style="margin:0;font-size:18px;font-weight:700;color:var(--text)">Configurações</h2>

    <!-- SLAs -->
    <div class="config-card">
      <h3>SLAs de Desempenho</h3>
      <div class="config-row">
        <div>
          <div class="config-label">Tempo Médio de Atendimento (TMA)</div>
          <div class="config-unit">horas — quanto menor, melhor</div>
        </div>
        <input type="number" class="config-input" id="cfg-sla-tma" min="1" max="72" step="1" />
      </div>
      <div class="config-row">
        <div>
          <div class="config-label">Tempo Médio de Resposta (TMR)</div>
          <div class="config-unit">minutos — quanto menor, melhor</div>
        </div>
        <input type="number" class="config-input" id="cfg-sla-tmr" min="1" max="480" step="1" />
      </div>
      <div class="config-row">
        <div>
          <div class="config-label">Taxa de Resolução</div>
          <div class="config-unit">% — quanto maior, melhor</div>
        </div>
        <input type="number" class="config-input" id="cfg-sla-fcr" min="1" max="100" step="1" />
      </div>
      <div class="config-row">
        <div>
          <div class="config-label">Mensagens por Conversa</div>
          <div class="config-unit">mensagens — quanto menor, melhor</div>
        </div>
        <input type="number" class="config-input" id="cfg-sla-msg" min="1" max="100" step="1" />
      </div>
    </div>

    <!-- Fila -->
    <div class="config-card">
      <h3>Alerta de Fila</h3>
      <div class="config-row">
        <div>
          <div class="config-label">Avisar quando aguardando ≥</div>
          <div class="config-unit">conversas · 0 = desativado</div>
        </div>
        <input type="number" class="config-input" id="cfg-threshold" min="0" max="999" step="1" />
      </div>
    </div>

    <!-- Atualização -->
    <div class="config-card">
      <h3>Atualização Automática</h3>
      <div class="config-row">
        <div>
          <div class="config-label">Intervalo de atualização</div>
          <div class="config-unit">segundos · mínimo 15</div>
        </div>
        <input type="number" class="config-input" id="cfg-refresh" min="15" max="3600" step="1" />
      </div>
    </div>

    <!-- Pesos -->
    <div class="config-card">
      <h3>Pesos da Pontuação de Agentes</h3>
      <div class="config-row">
        <div class="config-label">Peso TMA</div>
        <input type="number" class="config-input" id="cfg-weight-tma" min="0" max="100" step="1" oninput="updateWeightSum()" />
      </div>
      <div class="config-row">
        <div class="config-label">Peso TMR</div>
        <input type="number" class="config-input" id="cfg-weight-tmr" min="0" max="100" step="1" oninput="updateWeightSum()" />
      </div>
      <div class="config-row">
        <div class="config-label">Peso Resolução</div>
        <input type="number" class="config-input" id="cfg-weight-fcr" min="0" max="100" step="1" oninput="updateWeightSum()" />
      </div>
      <div class="config-row">
        <div class="config-label">Peso Msgs/Conversa</div>
        <input type="number" class="config-input" id="cfg-weight-msg" min="0" max="100" step="1" oninput="updateWeightSum()" />
      </div>
      <div class="config-weight-sum ok" id="cfg-weight-sum">Soma: 100 / 100 pts ✓</div>
    </div>

    <!-- Ações -->
    <div class="config-actions">
      <button class="btn-primary" id="cfg-save-btn" onclick="saveConfig()">Salvar configurações</button>
      <button onclick="resetConfigDefaults()" style="padding:8px 16px;border:1px solid var(--border);border-radius:6px;background:var(--bg2);color:var(--text3);cursor:pointer;font-size:13px">Restaurar padrões</button>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Verificar renderização**

Abrir o browser, autenticar com a senha. A página deve renderizar com os 4 cards. Os campos ainda podem estar vazios — serão preenchidos na Task 5.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat(config): HTML e CSS da página de configurações"
```

---

## Task 5: Lógica JS da página de configurações

**Files:**
- Modify: `index.html` — função `showPage()` (linha ~2923) e novas funções JS

**Interfaces:**
- Consumes: `_SLA_TMA`, `_SLA_TMR`, `_SLA_FCR`, `_SLA_MSG`, `REFRESH_SEC`, `_WEIGHT_TMA/TMR/FCR/MSG`, `cfg.threshold`, `startDashboard()`
- Produces: `loadConfigPage()`, `saveConfig()`, `resetConfigDefaults()`, `updateWeightSum()`

- [ ] **Step 1: Atualizar showPage() para incluir config-page**

Localizar a função `showPage()` (linha ~2923). Substituir:

```javascript
function showPage(page) {
  document.getElementById('content').style.display       = page === 'painel'   ? '' : 'none';
  document.getElementById('graficos-page').style.display = page === 'graficos' ? '' : 'none';
  document.getElementById('agentes-page').style.display  = page === 'agentes'  ? '' : 'none';
  const ib = document.getElementById('inbox-bar');
  if (ib) ib.style.display = page === 'painel' ? (_ibVisible ? 'flex' : 'none') : 'none';
  document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active'));
  document.getElementById(`nav-${page}`).classList.add('active');
  if (page === 'graficos') {
    if (!_chartData.length || _chartDataStale) { _chartDataStale = false; fetchChartData(); }
    else if (_chartsDirty) renderCharts();
  }
  if (page === 'agentes') {
    if (!_agentPerfData || _agentTabDirty) { _agentTabDirty = false; fetchAgentTab(); }
    else renderAgentTab();
  }
}
```

Por:

```javascript
function showPage(page) {
  document.getElementById('content').style.display       = page === 'painel'        ? '' : 'none';
  document.getElementById('graficos-page').style.display = page === 'graficos'      ? '' : 'none';
  document.getElementById('agentes-page').style.display  = page === 'agentes'       ? '' : 'none';
  document.getElementById('config-page').style.display   = page === 'configuracoes' ? '' : 'none';
  const ib = document.getElementById('inbox-bar');
  if (ib) ib.style.display = page === 'painel' ? (_ibVisible ? 'flex' : 'none') : 'none';
  document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active'));
  const navEl = document.getElementById(`nav-${page}`);
  if (navEl) navEl.classList.add('active');
  if (page === 'graficos') {
    if (!_chartData.length || _chartDataStale) { _chartDataStale = false; fetchChartData(); }
    else if (_chartsDirty) renderCharts();
  }
  if (page === 'agentes') {
    if (!_agentPerfData || _agentTabDirty) { _agentTabDirty = false; fetchAgentTab(); }
    else renderAgentTab();
  }
  if (page === 'configuracoes') loadConfigPage();
}
```

- [ ] **Step 2: Adicionar funções de configuração JS**

Localizar a função `setAgentTabPeriod()` (linha ~2941). Adicionar as seguintes funções **antes** dela:

```javascript
/* ── CONFIGURAÇÕES ── */
function loadConfigPage() {
  document.getElementById('cfg-sla-tma').value    = _SLA_TMA;
  document.getElementById('cfg-sla-tmr').value    = _SLA_TMR;
  document.getElementById('cfg-sla-fcr').value    = _SLA_FCR;
  document.getElementById('cfg-sla-msg').value    = _SLA_MSG;
  document.getElementById('cfg-threshold').value  = cfg.threshold;
  document.getElementById('cfg-refresh').value    = REFRESH_SEC;
  document.getElementById('cfg-weight-tma').value = _WEIGHT_TMA;
  document.getElementById('cfg-weight-tmr').value = _WEIGHT_TMR;
  document.getElementById('cfg-weight-fcr').value = _WEIGHT_FCR;
  document.getElementById('cfg-weight-msg').value = _WEIGHT_MSG;
  updateWeightSum();
}

function updateWeightSum() {
  const sum = ['tma','tmr','fcr','msg'].reduce((acc, k) =>
    acc + (parseInt(document.getElementById(`cfg-weight-${k}`).value, 10) || 0), 0);
  const el = document.getElementById('cfg-weight-sum');
  const ok = sum === 100;
  el.textContent = ok ? `Soma: ${sum} / 100 pts ✓` : `Soma: ${sum} / 100 pts — ajuste os pesos para somar exatamente 100`;
  el.className   = `config-weight-sum ${ok ? 'ok' : 'err'}`;
  document.getElementById('cfg-save-btn').disabled = !ok;
}

function saveConfig() {
  const slaTma  = Math.max(1,  parseInt(document.getElementById('cfg-sla-tma').value,    10) || 8);
  const slaTmr  = Math.max(1,  parseInt(document.getElementById('cfg-sla-tmr').value,    10) || 30);
  const slaFcr  = Math.max(1,  parseInt(document.getElementById('cfg-sla-fcr').value,    10) || 85);
  const slaMsg  = Math.max(1,  parseInt(document.getElementById('cfg-sla-msg').value,    10) || 10);
  const thr     = Math.max(0,  parseInt(document.getElementById('cfg-threshold').value,  10) || 0);
  const refresh = Math.max(15, parseInt(document.getElementById('cfg-refresh').value,    10) || 60);
  const wTma    = parseInt(document.getElementById('cfg-weight-tma').value, 10) || 0;
  const wTmr    = parseInt(document.getElementById('cfg-weight-tmr').value, 10) || 0;
  const wFcr    = parseInt(document.getElementById('cfg-weight-fcr').value, 10) || 0;
  const wMsg    = parseInt(document.getElementById('cfg-weight-msg').value, 10) || 0;

  if (wTma + wTmr + wFcr + wMsg !== 100) return;

  localStorage.setItem('grv_sla_tma',    slaTma);
  localStorage.setItem('grv_sla_tmr',    slaTmr);
  localStorage.setItem('grv_sla_fcr',    slaFcr);
  localStorage.setItem('grv_sla_msg',    slaMsg);
  localStorage.setItem('grv_threshold',  thr);
  localStorage.setItem('grv_refresh_sec', refresh);
  localStorage.setItem('grv_weight_tma', wTma);
  localStorage.setItem('grv_weight_tmr', wTmr);
  localStorage.setItem('grv_weight_fcr', wFcr);
  localStorage.setItem('grv_weight_msg', wMsg);

  _SLA_TMA    = slaTma;
  _SLA_TMR    = slaTmr;
  _SLA_FCR    = slaFcr;
  _SLA_MSG    = slaMsg;
  cfg.threshold = thr;
  REFRESH_SEC = refresh;
  _WEIGHT_TMA = wTma;
  _WEIGHT_TMR = wTmr;
  _WEIGHT_FCR = wFcr;
  _WEIGHT_MSG = wMsg;

  _agentPerfData = null;
  _agentMonthCache = {};

  startDashboard();
  showToast('Configurações salvas');
  showPage('painel');
}

function resetConfigDefaults() {
  document.getElementById('cfg-sla-tma').value    = 8;
  document.getElementById('cfg-sla-tmr').value    = 30;
  document.getElementById('cfg-sla-fcr').value    = 85;
  document.getElementById('cfg-sla-msg').value    = 10;
  document.getElementById('cfg-threshold').value  = 0;
  document.getElementById('cfg-refresh').value    = 60;
  document.getElementById('cfg-weight-tma').value = 25;
  document.getElementById('cfg-weight-tmr').value = 25;
  document.getElementById('cfg-weight-fcr').value = 25;
  document.getElementById('cfg-weight-msg').value = 25;
  updateWeightSum();
}
```

- [ ] **Step 3: Verificar fluxo completo no browser**

1. Recarregar. Clicar ⚙. Autenticar.
2. A página de configurações deve abrir com os valores atuais preenchidos.
3. Alterar os pesos para soma ≠ 100 (ex: TMA=30, TMR=25, FCR=25, MSG=25 = 105) → botão Salvar deve ficar desabilitado, mensagem de erro na soma.
4. Corrigir para soma = 100. Botão Salvar habilitado.
5. Alterar TMA para 5h. Clicar Salvar → toast "Configurações salvas" + volta ao Painel.
6. Ir para aba Agentes → a nova SLA de TMA=5h deve estar sendo usada (badge muda de cor se antes estava verde e agora deveria ser outra).
7. Clicar "Restaurar padrões" → campos voltam para os valores padrão (mas não salva ainda).

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat(config): lógica JS de loadConfigPage, saveConfig, resetConfigDefaults, updateWeightSum"
```

---

## Task 6: calcAgentScore() com pesos dinâmicos

**Files:**
- Modify: `index.html:2009-2035`

**Interfaces:**
- Consumes: `_WEIGHT_TMA`, `_WEIGHT_TMR`, `_WEIGHT_FCR`, `_WEIGHT_MSG` (definidas na Task 2)
- Produces: `calcAgentScore(summary) → number|null` — score 0-100 usando pesos configuráveis

- [ ] **Step 1: Substituir calcAgentScore() com pesos dinâmicos**

Localizar a função `calcAgentScore` (linha ~2009). Substituir todo o bloco:

```javascript
function calcAgentScore(summary) {
  if (!summary || (summary.conversations_count || 0) === 0) return null;
  const s = summary;
  let pts = 0;
  const tmaH = s.avg_resolution_time != null ? s.avg_resolution_time / 3600 : null;
  if (tmaH != null) {
    if (tmaH <= _SLA_TMA)            pts += 25;
    else if (tmaH <= _SLA_TMA * 1.5) pts += 12;
  }
  const tmrM = s.avg_first_response_time != null ? s.avg_first_response_time / 60 : null;
  if (tmrM != null) {
    if (tmrM <= _SLA_TMR)            pts += 25;
    else if (tmrM <= _SLA_TMR * 1.5) pts += 12;
  }
  const fcr = s.conversations_count > 0 ? (s.resolutions_count || 0) / s.conversations_count * 100 : null;
  if (fcr != null) {
    if (fcr >= _SLA_FCR)             pts += 25;
    else if (fcr >= _SLA_FCR - 15)   pts += 12;
  }
  const totalMsgs = (s.incoming_messages_count || 0) + (s.outgoing_messages_count || 0);
  const msgsConv  = s.conversations_count > 0 ? totalMsgs / s.conversations_count : null;
  if (msgsConv != null) {
    if (msgsConv <= _SLA_MSG)           pts += 25;
    else if (msgsConv <= _SLA_MSG * 1.5) pts += 12;
  }
  return pts;
}
```

Por:

```javascript
function calcAgentScore(summary) {
  if (!summary || (summary.conversations_count || 0) === 0) return null;
  const s = summary;
  let pts = 0;
  const tmaH = s.avg_resolution_time != null ? s.avg_resolution_time / 3600 : null;
  if (tmaH != null) {
    if (tmaH <= _SLA_TMA)            pts += _WEIGHT_TMA;
    else if (tmaH <= _SLA_TMA * 1.5) pts += Math.round(_WEIGHT_TMA / 2);
  }
  const tmrM = s.avg_first_response_time != null ? s.avg_first_response_time / 60 : null;
  if (tmrM != null) {
    if (tmrM <= _SLA_TMR)            pts += _WEIGHT_TMR;
    else if (tmrM <= _SLA_TMR * 1.5) pts += Math.round(_WEIGHT_TMR / 2);
  }
  const fcr = s.conversations_count > 0 ? (s.resolutions_count || 0) / s.conversations_count * 100 : null;
  if (fcr != null) {
    if (fcr >= _SLA_FCR)             pts += _WEIGHT_FCR;
    else if (fcr >= _SLA_FCR - 15)   pts += Math.round(_WEIGHT_FCR / 2);
  }
  const totalMsgs = (s.incoming_messages_count || 0) + (s.outgoing_messages_count || 0);
  const msgsConv  = s.conversations_count > 0 ? totalMsgs / s.conversations_count : null;
  if (msgsConv != null) {
    if (msgsConv <= _SLA_MSG)           pts += _WEIGHT_MSG;
    else if (msgsConv <= _SLA_MSG * 1.5) pts += Math.round(_WEIGHT_MSG / 2);
  }
  return pts;
}
```

- [ ] **Step 2: Verificar que pontuações ainda batem com pesos padrão**

Com pesos padrão (25/25/25/25), o score máximo continua sendo 100 (25+25+25+25). Ir para aba Agentes → os scores devem ser idênticos aos de antes.

- [ ] **Step 3: Testar com pesos alterados**

Na página de Configurações, alterar pesos para TMA=40, TMR=30, FCR=20, MSG=10. Salvar. Ir para Agentes → scores devem refletir a nova ponderação (agentes com TMA bom sobem, agentes com TMA ruim descem mais).

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat(config): calcAgentScore() usa pesos dinâmicos de _WEIGHT_*"
```

---

## Self-Review

### Cobertura da spec

| Requisito | Task |
|---|---|
| Senha em server.js | Task 1 |
| POST /api/auth-settings | Task 1 |
| Ícone ⚙ no rodapé do sidebar | Task 3 |
| Modal de senha com erro inline | Task 3 |
| Auth permanente via localStorage | Task 3 |
| Página config via showPage() | Task 4 + 5 |
| Ícone ⚙ não recebe active | Task 5 — null-check em showPage() |
| SLAs editáveis (TMA/TMR/FCR/MSG) | Task 4 + 5 |
| Threshold de fila editável | Task 4 + 5 |
| Intervalo de atualização editável | Task 2 + 5 |
| Pesos editáveis com soma=100 | Task 4 + 5 |
| Validação soma de pesos em tempo real | Task 5 — updateWeightSum() |
| Botão Salvar desabilitado se soma≠100 | Task 5 — updateWeightSum() |
| Aplicação imediata após Salvar | Task 5 — saveConfig() reatribui variáveis + startDashboard() |
| Restaurar padrões | Task 5 — resetConfigDefaults() |
| calcAgentScore() com pesos dinâmicos | Task 6 |
| Persistência no localStorage | Task 2 (leitura) + Task 5 (escrita) |
