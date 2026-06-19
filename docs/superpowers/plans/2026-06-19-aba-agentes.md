# Aba Agentes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar aba "Agentes" ao sidebar com status ao vivo, tabela de desempenho histórico ordenável com gráfico de evolução por agente, e seção de CSAT com detecção automática.

**Architecture:** Todas as mudanças em `index.html` (single-file). Nova página `#agentes-page` com 3 seções renderizadas via JS. Dados de 3 fontes: `/v2/reports/overview` (ao vivo), `/v2/reports/summary?type=agent` (histórico), `/v1/reports/agents/satisfaction` (CSAT). Funções seguem o padrão existente: `fetchX()` busca dados, `renderX()` atualiza o DOM.

**Tech Stack:** HTML/CSS/JS inline, Chart.js 4 (já carregado via CDN), função `api()` existente, utilitários existentes: `fmtSec()`, `esc()`, `showToast()`, `chartColors()`, `destroyChart()`.

## Global Constraints

- Single file: todas as mudanças em `c:\Users\Samuel Wallace\Documents\vscode\grv-chatwoot-dashboard\index.html`
- Seguir CSS vars existentes: `--bg`, `--bg2`, `--bg3`, `--border`, `--accent`, `--text`, `--text2`, `--text3`, `--green`, `--yellow`, `--red`
- Reutilizar classes existentes: `.chart-card`, `.metric-card`, `.section-divider`, `.section-divider-label`, `.badge-live`, `.inbox-trigger`, `.inbox-chips`, `.inbox-clear`, `.chart-na`
- API calls via `api(path)` existente (linha ~1018)
- `_agentTabPeriod` default: `'3'` (3 meses)
- Ordenação padrão da tabela de desempenho: Volume (`conversations_count`) decrescente
- Agentes com `conversations_count === 0` sempre ao final da tabela

---

## File Structure

Apenas `index.html` é modificado. As mudanças se dividem em 4 blocos dentro do arquivo:

1. **CSS** (dentro de `<style>`) — estilos da aba Agentes
2. **HTML** (antes de `<!-- TOAST -->`) — `#agentes-page` + popup `#agp`
3. **Sidebar** — item "Agentes" entre Painel e Análise
4. **JS** (dentro de `<script>`) — variáveis de estado + 10 funções novas + atualizações de `showPage()`, `fetchAll()` e `MutationObserver`

---

## Task 1: CSS + Variáveis de Estado + Sidebar + HTML Skeleton

**Files:**
- Modify: `index.html` — CSS, sidebar HTML, agentes-page HTML, estado JS

**Interfaces:**
- Produces: `#agentes-page`, `#agp` (popup), `#agent-live-section`, `#agent-perf-section`, `#agent-csat-section`, `#agent-period-pills`, `_agentTabPeriod`, `_agentTabFilter`, `_agentList`, `_agentPerfData`, `_agentOverview`, `_agentCsat`, `_agentExpanded`, `_agentTabDirty`, `_agentPerfSort`

- [ ] **Step 1: Adicionar CSS da aba Agentes**

Localizar a linha `.chart-auth-overlay { ... }` no CSS (bloco `<style>`) e adicionar logo após:

```css
/* AGENTES TAB */
.agent-stat-cards { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:16px; }
.agent-stat-card { background:var(--bg2); border:1px solid var(--border); border-radius:8px; padding:14px 18px; flex:1; min-width:140px; }
.agent-stat-card .asv { font-size:26px; font-weight:800; line-height:1.1; }
.agent-stat-card .asl { font-size:11px; color:var(--text2); margin-top:3px; }
.agent-period-pills { display:flex; gap:4px; }
.agent-pill { padding:4px 14px; border-radius:20px; border:1px solid var(--border); background:transparent; color:var(--text2); font-size:12px; cursor:pointer; transition:background .15s,color .15s,border-color .15s; }
.agent-pill:hover { border-color:var(--accent); color:var(--accent); }
.agent-pill.active { background:var(--accent); color:#fff; border-color:var(--accent); }
.agent-table { width:100%; border-collapse:collapse; font-size:13px; }
.agent-table th { background:var(--bg2); color:var(--text2); font-size:11px; font-weight:600; text-align:left; padding:8px 10px; border-bottom:2px solid var(--border); cursor:pointer; user-select:none; white-space:nowrap; }
.agent-table th:hover { color:var(--text); }
.agent-table th.sort-asc::after  { content:' ▲'; color:var(--accent); }
.agent-table th.sort-desc::after { content:' ▼'; color:var(--accent); }
.agent-table td { padding:8px 10px; border-bottom:1px solid var(--border); vertical-align:middle; }
.agent-table tr:last-child td { border:none; }
.agent-table tr.agent-row:hover { background:var(--bg3); cursor:pointer; }
.agent-table tr.agent-row.expanded { background:rgba(59,130,246,.06); }
.agent-table tr.agent-expand-row td { padding:0; }
.agent-expand-inner { padding:16px 12px; background:var(--bg2); border-bottom:1px solid var(--border); }
.agent-status-dot { width:8px; height:8px; border-radius:50%; display:inline-block; flex-shrink:0; margin-right:6px; }
.dot-online { background:var(--green); }
.dot-busy   { background:var(--yellow); }
.dot-offline{ background:var(--text3); }
.agent-no-data { color:var(--text3); font-size:12px; font-style:italic; padding:24px; text-align:center; }
/* Agent filter popup */
#agp { position:fixed; z-index:300; background:var(--bg2); border:1px solid var(--border); border-radius:8px; box-shadow:0 8px 24px rgba(0,0,0,.4); width:260px; display:none; flex-direction:column; max-height:360px; }
#agp.open { display:flex; }
.agp-head { display:flex; align-items:center; gap:6px; padding:10px 12px; border-bottom:1px solid var(--border); }
.agp-head-title { flex:1; font-size:13px; font-weight:600; }
.agp-xs { padding:2px 8px; border-radius:4px; border:1px solid var(--border); background:transparent; color:var(--text2); font-size:11px; cursor:pointer; }
.agp-xs:hover { border-color:var(--accent); color:var(--accent); }
.agp-body { overflow-y:auto; flex:1; padding:6px 0; }
.agp-item { display:flex; align-items:center; gap:8px; padding:7px 12px; cursor:pointer; font-size:13px; }
.agp-item:hover { background:var(--bg3); }
.agp-item input[type=checkbox] { accent-color:var(--accent); width:14px; height:14px; flex-shrink:0; cursor:pointer; }
.agp-foot { display:flex; justify-content:flex-end; gap:8px; padding:10px 12px; border-top:1px solid var(--border); }
.agp-ok { padding:5px 16px; background:var(--accent); border:none; border-radius:5px; color:#fff; font-size:12px; font-weight:600; cursor:pointer; }
.agp-ok:hover { opacity:.85; }
.csat-placeholder { background:var(--bg2); border:1px solid var(--border); border-radius:8px; padding:24px; text-align:center; color:var(--text2); font-size:13px; line-height:1.7; }
.csat-placeholder strong { color:var(--text); display:block; margin-bottom:6px; }
```

- [ ] **Step 2: Adicionar item "Agentes" no sidebar**

Localizar:
```html
  <div class="sidebar-item" id="nav-graficos" onclick="showPage('graficos')" title="Análise">
```

Adicionar logo ANTES dessa linha:
```html
  <div class="sidebar-item" id="nav-agentes" onclick="showPage('agentes')" title="Agentes">
    <span class="sidebar-icon">👥</span>
    <span class="sidebar-label">Agentes</span>
  </div>
```

- [ ] **Step 3: Adicionar HTML da agentes-page e popup de filtro**

Localizar `<!-- TOAST -->` e adicionar logo ANTES:

```html
<!-- AGENTES PAGE -->
<div id="agentes-page" style="display:none;padding:12px 24px 32px;background:var(--bg);min-height:calc(100vh - 56px);margin-left:52px">
  <div class="chart-hdr">
    <h2>Agentes</h2>
    <div class="agent-period-pills" id="agent-period-pills">
      <button class="agent-pill" onclick="setAgentTabPeriod('1')">Mês atual</button>
      <button class="agent-pill active" onclick="setAgentTabPeriod('3')">3 meses</button>
      <button class="agent-pill" onclick="setAgentTabPeriod('6')">6 meses</button>
      <button class="agent-pill" onclick="setAgentTabPeriod('12')">12 meses</button>
    </div>
    <button class="inbox-trigger" id="agent-filter-trigger" onclick="openAgentFilter(event)">
      <span id="agent-filter-trigger-txt">Todos os agentes</span> ▾
    </button>
    <div class="inbox-chips" id="agent-filter-chips"></div>
    <button class="inbox-clear" id="agent-filter-clear" onclick="clearAgentFilter()" style="display:none">✕ Limpar</button>
    <span id="agent-tab-updated" style="font-size:11px;color:var(--text3);margin-left:auto"></span>
  </div>

  <div class="section-divider"><span class="section-divider-label">Status ao vivo</span></div>
  <div id="agent-live-section"><div class="agent-no-data">Carregando…</div></div>

  <div class="section-divider" style="margin-top:16px"><span class="section-divider-label">Desempenho no período</span></div>
  <div id="agent-perf-section"><div class="agent-no-data">Carregando…</div></div>

  <div class="section-divider" style="margin-top:16px"><span class="section-divider-label">Satisfação do Cliente (CSAT)</span></div>
  <div id="agent-csat-section"><div class="agent-no-data">Carregando…</div></div>
</div>

<!-- AGENT FILTER POPUP -->
<div id="agp" role="dialog" aria-modal="true" aria-label="Filtrar agentes">
  <div class="agp-head">
    <span class="agp-head-title">Agentes</span>
    <button class="agp-xs" onclick="agpAll()">Todos</button>
    <button class="agp-xs" onclick="agpNone()">Limpar</button>
  </div>
  <div class="agp-body" id="agp-body"></div>
  <div class="agp-foot">
    <button class="agp-xs" onclick="agpClose()">Fechar</button>
    <button class="agp-ok" onclick="agpApply()">Aplicar</button>
  </div>
</div>
```

- [ ] **Step 4: Adicionar variáveis de estado**

Localizar `let _authLimited     = false;` e adicionar logo após:

```javascript
/* ── AGENTES TAB STATE ── */
let _agentTabPeriod  = '3';    /* '1'|'3'|'6'|'12' */
let _agentTabFilter  = null;   /* Set<number>|null — ids de agentes */
let _agentList       = [];     /* [{id, name, availability_status, ...}] */
let _agentPerfData   = null;   /* {id: {summary, months[]}} */
let _agentOverview   = null;   /* dados brutos do overview */
let _agentCsat       = null;   /* [{agent_id, agent_name, total, positive}] | null */
let _agentExpanded   = null;   /* id do agente expandido */
let _agentTabDirty   = false;  /* true → re-fetch ao entrar na aba */
let _agentPerfSort   = { col: 'conversations_count', dir: 'desc' };
let _agp             = { sel: new Set() }; /* estado interno do popup */
```

- [ ] **Step 5: Verificar visualmente**

Abrir http://localhost:8765 no browser. O sidebar deve mostrar 3 itens: 📊 Painel, 👥 Agentes, 📈 Análise. Clicar em "Agentes" deve mostrar a página com 3 seções de "Carregando…". Nenhum erro no console JS.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat(agentes): HTML skeleton, CSS, sidebar item e variáveis de estado"
```

---

## Task 2: Helpers de Período + fetchAgentTab() + Integração com fetchAll()

**Files:**
- Modify: `index.html` (seção JS)

**Interfaces:**
- Consumes: `api()`, `cfg.account`, `_agentTabPeriod`, `_agentList`, `_agentTabFilter`, `isAuthError()`
- Produces: `getAgentTabRange()`, `getAgentMonths()`, `fetchAgentTab()` — popula `_agentList`, `_agentPerfData`, `_agentOverview`, `_agentCsat`, `_agentTabDirty`

- [ ] **Step 1: Adicionar getAgentTabRange() e getAgentMonths()**

Localizar `async function fetchAgentTab` (não existe ainda — adicionar antes de `function renderCharts()`):

```javascript
/* Retorna {since, until} para o período selecionado */
function getAgentTabRange() {
  const now   = new Date();
  const until = Math.floor(now.getTime() / 1000);
  let start;
  if (_agentTabPeriod === '1') {
    start = new Date(now.getFullYear(), now.getMonth(), 1);
  } else {
    const m = parseInt(_agentTabPeriod);
    start = new Date(now.getFullYear(), now.getMonth() - m, 1);
  }
  return { since: Math.floor(start.getTime() / 1000), until };
}

/* Retorna array de {since, until, label} — um por mês — para o gráfico de detalhe */
function getAgentMonths() {
  const now    = new Date();
  const months = _agentTabPeriod === '1' ? 1 : parseInt(_agentTabPeriod);
  const result = [];
  for (let i = months - 1; i >= 0; i--) {
    const y  = now.getFullYear();
    const m  = now.getMonth() - i;
    const s  = new Date(y, m, 1);
    const e  = new Date(y, m + 1, 0, 23, 59, 59);
    const lbl = s.toLocaleDateString('pt-BR', { month: 'short', year: '2-digit' });
    result.push({
      since: Math.floor(s.getTime() / 1000),
      until: Math.floor(Math.min(e.getTime(), now.getTime()) / 1000),
      label: lbl.charAt(0).toUpperCase() + lbl.slice(1)
    });
  }
  return result;
}
```

- [ ] **Step 2: Adicionar fetchAgentTab()**

Adicionar logo após as funções acima:

```javascript
async function fetchAgentTab() {
  const liveEl = document.getElementById('agent-live-section');
  const perfEl = document.getElementById('agent-perf-section');
  const csatEl = document.getElementById('agent-csat-section');
  if (liveEl) liveEl.innerHTML = '<div class="agent-no-data">Carregando…</div>';
  if (perfEl) perfEl.innerHTML = '<div class="agent-no-data">Carregando…</div>';
  if (csatEl) csatEl.innerHTML = '<div class="agent-no-data">Carregando…</div>';

  const { since, until } = getAgentTabRange();
  const months           = getAgentMonths();

  /* 1. Lista de agentes (já buscada em fetchAll — reusar _agentList) */
  const agents = _agentList.length ? _agentList
    : await api(`/v1/accounts/${cfg.account}/agents`).catch(() => []);
  if (!_agentList.length && Array.isArray(agents)) _agentList = agents;

  const visibleAgents = (_agentTabFilter && _agentTabFilter.size > 0)
    ? _agentList.filter(a => _agentTabFilter.has(a.id))
    : _agentList;

  /* 2. Overview ao vivo */
  _agentOverview = await api(`/v2/accounts/${cfg.account}/reports/overview`)
    .catch(() => null);

  /* 3. Summary por agente (período agregado) + detalhe mensal */
  try {
    const summaries = await Promise.all(visibleAgents.map(a =>
      api(`/v2/accounts/${cfg.account}/reports/summary?type=agent&id=${a.id}&since=${since}&until=${until}`)
        .catch(() => null)
    ));

    const monthDetails = await Promise.all(visibleAgents.map(a =>
      Promise.all(months.map(mo =>
        api(`/v2/accounts/${cfg.account}/reports/summary?type=agent&id=${a.id}&since=${mo.since}&until=${mo.until}`)
          .catch(() => null)
      ))
    ));

    _agentPerfData = {};
    visibleAgents.forEach((a, i) => {
      _agentPerfData[a.id] = {
        agent:   a,
        summary: summaries[i],
        months:  monthDetails[i].map((r, j) => ({ ...months[j], data: r }))
      };
    });
  } catch (e) {
    if (isAuthError(e)) {
      _agentPerfData = { _authError: true };
    } else {
      _agentPerfData = {};
    }
  }

  /* 4. CSAT */
  _agentCsat = await api(`/v1/accounts/${cfg.account}/reports/agents/satisfaction?since=${since}&until=${until}`)
    .then(data => {
      if (!Array.isArray(data) || !data.length) return null;
      const byAgent = {};
      data.forEach(r => {
        const id   = r.assigned_agent?.id;
        const name = r.assigned_agent?.name || 'Desconhecido';
        if (!id) return;
        if (!byAgent[id]) byAgent[id] = { id, name, total: 0, positive: 0 };
        byAgent[id].total++;
        if (r.rating === 'Satisfied') byAgent[id].positive++;
      });
      return Object.values(byAgent);
    })
    .catch(() => null);

  const updEl = document.getElementById('agent-tab-updated');
  if (updEl) updEl.textContent = `Atualizado às ${new Date().toLocaleTimeString('pt-BR')}`;

  renderAgentTab();
}
```

- [ ] **Step 3: Atualizar fetchAll() para salvar _agentList e marcar _agentTabDirty**

Localizar dentro de `async function fetchAll()`:
```javascript
    _inboxMap  = {};
    (inboxes.payload || []).forEach(i => { _inboxMap[i.id] = i; });
```

Adicionar logo após:
```javascript
    if (Array.isArray(agents)) _agentList = agents;
    _agentTabDirty = true;
```

- [ ] **Step 4: Verificar no browser**

Abrir http://localhost:8765, clicar em "Agentes". O console deve mostrar as chamadas de API sem erros. As seções devem mudar de "Carregando…" para algum conteúdo (mesmo que vazio por enquanto — as funções render ainda não existem). Verificar `_agentPerfData` no console com `window._agentPerfData`.

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "feat(agentes): fetchAgentTab(), getAgentTabRange(), getAgentMonths(), integração com fetchAll()"
```

---

## Task 3: renderAgentLive() — Seção 1 (Status ao vivo)

**Files:**
- Modify: `index.html` (seção JS)

**Interfaces:**
- Consumes: `_agentOverview`, `_agentList`, `_agentTabFilter`, `esc()`
- Produces: `renderAgentLive()` — preenche `#agent-live-section`

- [ ] **Step 1: Adicionar renderAgentLive()**

Adicionar após `fetchAgentTab()`:

```javascript
function renderAgentLive() {
  const el = document.getElementById('agent-live-section');
  if (!el) return;

  const ov = _agentOverview;
  if (!ov) {
    el.innerHTML = '<div class="agent-no-data">Status ao vivo não disponível com este token</div>';
    return;
  }

  /* Normaliza estrutura — Chatwoot pode retornar {data:{...}} ou diretamente {...} */
  const raw    = ov.data || ov;
  const ovAgents = Array.isArray(raw.agents) ? raw.agents : (raw.data?.agents || []);
  const openTotal = raw.open_conversations_count ?? raw.open ?? 0;

  const online  = ovAgents.filter(a => a.availability_status === 'online').length;
  const busy    = ovAgents.filter(a => a.availability_status === 'busy').length;
  const offline = ovAgents.filter(a => a.availability_status === 'offline').length;

  const visibleIds = (_agentTabFilter && _agentTabFilter.size > 0) ? _agentTabFilter : null;

  /* Ordenar: online → busy → offline; depois por open_conversations desc */
  const statusOrder = { online: 0, busy: 1, offline: 2 };
  const sorted = [...ovAgents]
    .filter(a => !visibleIds || visibleIds.has(a.id))
    .sort((a, b) => {
      const sd = (statusOrder[a.availability_status] ?? 3) - (statusOrder[b.availability_status] ?? 3);
      if (sd !== 0) return sd;
      return (b.open_conversations_count || 0) - (a.open_conversations_count || 0);
    });

  const dotCls = s => s === 'online' ? 'dot-online' : s === 'busy' ? 'dot-busy' : 'dot-offline';
  const statusLabel = s => s === 'online' ? 'Online' : s === 'busy' ? 'Ocupado' : 'Offline';

  const now = Date.now();
  function oldestConvAge(agentOvData) {
    const oldest = agentOvData.open_conversations?.sort((a,b) => (a.created_at||0)-(b.created_at||0))[0];
    if (!oldest?.created_at) return '—';
    const secs = Math.floor((now/1000) - oldest.created_at);
    return fmtSec(secs);
  }

  el.innerHTML = `
    <div class="agent-stat-cards">
      <div class="agent-stat-card"><div class="asv" style="color:var(--green)">${online}</div><div class="asl">Online</div></div>
      <div class="agent-stat-card"><div class="asv" style="color:var(--yellow)">${busy}</div><div class="asl">Ocupado</div></div>
      <div class="agent-stat-card"><div class="asv" style="color:var(--text3)">${offline}</div><div class="asl">Offline</div></div>
      <div class="agent-stat-card"><div class="asv" style="color:var(--accent)">${openTotal}</div><div class="asl">Conversas abertas agora</div></div>
    </div>
    ${sorted.length === 0
      ? '<div class="agent-no-data">Nenhum agente encontrado</div>'
      : `<div class="chart-card" style="overflow-x:auto">
          <table class="agent-table">
            <thead><tr>
              <th style="min-width:180px">Agente</th>
              <th>Status</th>
              <th>Conversas abertas</th>
              <th>Mensagem mais antiga</th>
            </tr></thead>
            <tbody>
              ${sorted.map(a => `<tr>
                <td>${esc(a.name)}</td>
                <td><span class="agent-status-dot ${dotCls(a.availability_status)}"></span>${statusLabel(a.availability_status)}</td>
                <td>${a.open_conversations_count ?? 0}</td>
                <td>${oldestConvAge(a)}</td>
              </tr>`).join('')}
            </tbody>
          </table>
        </div>`
    }`;
}
```

- [ ] **Step 2: Verificar**

Clicar em "Agentes" no browser. A seção "Status ao vivo" deve mostrar os 4 cards de resumo e a tabela de agentes com status coloridos. Se o token não tiver acesso ao overview, deve mostrar "Status ao vivo não disponível com este token".

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat(agentes): renderAgentLive() — status ao vivo com cards e tabela"
```

---

## Task 4: renderAgentPerf() + toggleAgentExpand() — Seção 2

**Files:**
- Modify: `index.html` (seção JS)

**Interfaces:**
- Consumes: `_agentPerfData`, `_agentPerfSort`, `_agentExpanded`, `_agentTabFilter`, `_agentList`, `fmtSec()`, `esc()`, `chartColors()`, `destroyChart()`
- Produces: `renderAgentPerf()`, `sortAgentPerf(col)`, `toggleAgentExpand(id)`

- [ ] **Step 1: Adicionar renderAgentPerf() e sortAgentPerf()**

Adicionar após `renderAgentLive()`:

```javascript
function renderAgentPerf() {
  const el = document.getElementById('agent-perf-section');
  if (!el) return;

  if (!_agentPerfData) { el.innerHTML = '<div class="agent-no-data">Carregando…</div>'; return; }
  if (_agentPerfData._authError) {
    el.innerHTML = '<div class="agent-no-data">🔒 Dados por agente requerem permissão de Administrador no Chatwoot</div>';
    return;
  }

  const entries = Object.values(_agentPerfData).filter(e => e.agent);
  if (!entries.length) { el.innerHTML = '<div class="agent-no-data">Nenhum dado de agente disponível</div>'; return; }

  /* Ordenar: agentes com dados primeiro, depois por coluna selecionada */
  const { col, dir } = _agentPerfSort;
  const val = e => {
    const s = e.summary;
    if (!s) return null;
    if (col === 'conversations_count')    return s.conversations_count || 0;
    if (col === 'avg_resolution_time')    return s.avg_resolution_time ?? Infinity;
    if (col === 'avg_first_response_time')return s.avg_first_response_time ?? Infinity;
    if (col === 'fcr')                    return s.conversations_count > 0 ? s.resolutions_count / s.conversations_count : null;
    if (col === 'msgs_conv')              return s.conversations_count > 0 ? (s.incoming_messages_count + s.outgoing_messages_count) / s.conversations_count : null;
    if (col === 'total_msgs')             return (s.incoming_messages_count || 0) + (s.outgoing_messages_count || 0);
    return null;
  };

  const sorted = [...entries].sort((a, b) => {
    const noDataA = !a.summary || (a.summary.conversations_count || 0) === 0;
    const noDataB = !b.summary || (b.summary.conversations_count || 0) === 0;
    if (noDataA && noDataB) return 0;
    if (noDataA) return 1;
    if (noDataB) return -1;
    const va = val(a) ?? (dir === 'asc' ? Infinity : -Infinity);
    const vb = val(b) ?? (dir === 'asc' ? Infinity : -Infinity);
    return dir === 'asc' ? va - vb : vb - va;
  });

  const th = (label, colId) => {
    const cls = _agentPerfSort.col === colId
      ? (_agentPerfSort.dir === 'asc' ? 'sort-asc' : 'sort-desc') : '';
    return `<th class="${cls}" onclick="sortAgentPerf('${colId}')">${label}</th>`;
  };

  const fmtPct = (num, denom) => (denom > 0) ? `${Math.round(num / denom * 100)}%` : '—';
  const fmtMsgs = (s) => {
    if (!s || s.conversations_count === 0) return '—';
    const total = (s.incoming_messages_count || 0) + (s.outgoing_messages_count || 0);
    const perConv = s.conversations_count > 0 ? (total / s.conversations_count).toFixed(1) : '—';
    return perConv;
  };

  el.innerHTML = `
    <div class="chart-card" style="overflow-x:auto">
      <table class="agent-table" id="agent-perf-table">
        <thead><tr>
          ${th('Agente', 'name')}
          ${th('Volume', 'conversations_count')}
          ${th('TMA', 'avg_resolution_time')}
          ${th('TMR', 'avg_first_response_time')}
          ${th('% Resolução', 'fcr')}
          ${th('Msgs/Conv', 'msgs_conv')}
          ${th('Total Msgs', 'total_msgs')}
        </tr></thead>
        <tbody>
          ${sorted.map(e => {
            const s   = e.summary;
            const nd  = !s || (s.conversations_count || 0) === 0;
            const exp = _agentExpanded === e.agent.id;
            return `
              <tr class="agent-row${exp ? ' expanded' : ''}" onclick="toggleAgentExpand(${e.agent.id})">
                <td>${esc(e.agent.name)}</td>
                <td>${nd ? '—' : (s.conversations_count || 0).toLocaleString('pt-BR')}</td>
                <td>${nd ? '—' : fmtSec(s.avg_resolution_time)}</td>
                <td>${nd ? '—' : fmtSec(s.avg_first_response_time)}</td>
                <td>${nd ? '—' : fmtPct(s.resolutions_count || 0, s.conversations_count || 0)}</td>
                <td>${nd ? '—' : fmtMsgs(s)}</td>
                <td>${nd ? '—' : ((s.incoming_messages_count || 0) + (s.outgoing_messages_count || 0)).toLocaleString('pt-BR')}</td>
              </tr>
              <tr class="agent-expand-row" id="exp-row-${e.agent.id}" style="${exp ? '' : 'display:none'}">
                <td colspan="7">
                  <div class="agent-expand-inner">
                    <div style="font-size:12px;color:var(--text2);margin-bottom:8px">Evolução de <strong>${esc(e.agent.name)}</strong></div>
                    <div style="height:180px;position:relative"><canvas id="agent-chart-${e.agent.id}"></canvas></div>
                  </div>
                </td>
              </tr>`;
          }).join('')}
        </tbody>
      </table>
    </div>`;

  /* Re-renderizar gráfico expandido se houver */
  if (_agentExpanded !== null) renderAgentExpandChart(_agentExpanded);
}

function sortAgentPerf(col) {
  if (_agentPerfSort.col === col) {
    _agentPerfSort.dir = _agentPerfSort.dir === 'asc' ? 'desc' : 'asc';
  } else {
    _agentPerfSort = { col, dir: col === 'avg_resolution_time' || col === 'avg_first_response_time' ? 'asc' : 'desc' };
  }
  renderAgentPerf();
}
```

- [ ] **Step 2: Adicionar toggleAgentExpand() e renderAgentExpandChart()**

Adicionar logo após `sortAgentPerf()`:

```javascript
function toggleAgentExpand(id) {
  if (_agentExpanded === id) {
    _agentExpanded = null;
    destroyChart(`agent-${id}`);
  } else {
    if (_agentExpanded !== null) destroyChart(`agent-${_agentExpanded}`);
    _agentExpanded = id;
  }
  renderAgentPerf();
}

function renderAgentExpandChart(id) {
  const entry = _agentPerfData?.[id];
  if (!entry || !entry.months) return;
  const canvas = document.getElementById(`agent-chart-${id}`);
  if (!canvas) return;

  destroyChart(`agent-${id}`);
  const c      = chartColors();
  const labels = entry.months.map(m => m.label);
  const vol    = entry.months.map(m => m.data?.conversations_count || 0);
  const tma    = entry.months.map(m => m.data?.avg_resolution_time != null ? +(m.data.avg_resolution_time / 3600).toFixed(2) : null);
  const tmr    = entry.months.map(m => m.data?.avg_first_response_time != null ? +(m.data.avg_first_response_time / 60).toFixed(1) : null);

  _charts[`agent-${id}`] = new Chart(canvas, {
    type: 'line',
    data: { labels, datasets: [
      { label: 'Volume', data: vol, borderColor: 'rgba(59,130,246,0.8)', backgroundColor: 'rgba(59,130,246,0.08)', fill: true, tension: 0.3, yAxisID: 'y2', pointRadius: 3 },
      { label: 'TMA (hr)', data: tma, borderColor: 'rgba(139,92,246,0.8)', backgroundColor: 'transparent', tension: 0.3, yAxisID: 'y1', pointRadius: 3, spanGaps: true },
      { label: 'TMR (min)', data: tmr, borderColor: 'rgba(20,184,166,0.8)', backgroundColor: 'transparent', tension: 0.3, yAxisID: 'y1', pointRadius: 3, spanGaps: true }
    ]},
    options: {
      responsive: true, maintainAspectRatio: false, animation: false,
      plugins: {
        legend: { display: true, position: 'top', labels: { color: c.labels, font: { size: 11 }, boxWidth: 12 } },
        tooltip: { backgroundColor: c.tooltipBg, titleColor: c.labels, bodyColor: c.labels, borderColor: c.grid, borderWidth: 1 }
      },
      scales: {
        x:  { grid: { color: c.grid }, ticks: { color: c.labels, font: { size: 11 } } },
        y1: { position: 'left',  grid: { color: c.grid }, ticks: { color: c.labels, font: { size: 11 } } },
        y2: { position: 'right', grid: { display: false }, ticks: { color: c.labels, font: { size: 11 } } }
      }
    }
  });
}
```

- [ ] **Step 3: Verificar**

Clicar em "Agentes". A seção "Desempenho no período" deve mostrar a tabela com todos os agentes ordenados por Volume decrescente. Clicar no cabeçalho de uma coluna deve reordenar. Clicar em um agente deve expandir a linha com o gráfico de linha. Clicar novamente deve fechar.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat(agentes): renderAgentPerf(), sortAgentPerf(), toggleAgentExpand(), gráfico de evolução"
```

---

## Task 5: renderAgentCsat() — Seção 3

**Files:**
- Modify: `index.html` (seção JS)

**Interfaces:**
- Consumes: `_agentCsat`, `_agentTabFilter`, `_agentList`, `esc()`
- Produces: `renderAgentCsat()` — preenche `#agent-csat-section`

- [ ] **Step 1: Adicionar renderAgentCsat()**

Adicionar após `renderAgentExpandChart()`:

```javascript
function renderAgentCsat() {
  const el = document.getElementById('agent-csat-section');
  if (!el) return;

  if (_agentCsat === null) {
    el.innerHTML = `
      <div class="csat-placeholder">
        <strong>Aguardando ativação do CSAT</strong>
        Para ativar o CSAT no Chatwoot: <br>
        Configurações → Caixa de entrada → editar → Configurações de colaboração → ativar pesquisa de satisfação.
      </div>`;
    return;
  }

  const visibleIds = (_agentTabFilter && _agentTabFilter.size > 0) ? _agentTabFilter : null;
  const rows = _agentCsat
    .filter(r => !visibleIds || visibleIds.has(r.id))
    .sort((a, b) => b.total - a.total);

  if (!rows.length) {
    el.innerHTML = '<div class="agent-no-data">Nenhuma avaliação no período para os agentes selecionados</div>';
    return;
  }

  const starRating = (pct) => {
    const filled = Math.round(pct / 100 * 5);
    return '★'.repeat(filled) + '☆'.repeat(5 - filled);
  };

  el.innerHTML = `
    <div class="chart-card" style="overflow-x:auto">
      <table class="agent-table">
        <thead><tr>
          <th style="min-width:180px">Agente</th>
          <th>Total de Avaliações</th>
          <th>% Positivas</th>
          <th>Nota</th>
        </tr></thead>
        <tbody>
          ${rows.map(r => {
            const pct = r.total > 0 ? Math.round(r.positive / r.total * 100) : 0;
            const color = pct >= 80 ? 'var(--green)' : pct >= 60 ? 'var(--yellow)' : 'var(--red)';
            return `<tr>
              <td>${esc(r.name)}</td>
              <td>${r.total}</td>
              <td style="color:${color};font-weight:600">${pct}%</td>
              <td style="color:var(--yellow)">${starRating(pct)}</td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>
    </div>`;
}
```

- [ ] **Step 2: Verificar**

Com CSAT desativado no Chatwoot (situação atual), a seção deve mostrar o card placeholder com a instrução de ativação. Não deve haver erro no console.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat(agentes): renderAgentCsat() — tabela CSAT ou placeholder de ativação"
```

---

## Task 6: renderAgentTab() + showPage() + Seletor de Período + Filtro de Agentes + MutationObserver

**Files:**
- Modify: `index.html` (seção JS)

**Interfaces:**
- Consumes: `renderAgentLive()`, `renderAgentPerf()`, `renderAgentCsat()`, `_agentList`, `_agentTabFilter`, `_agentTabPeriod`, `_agp`
- Produces: `renderAgentTab()`, `setAgentTabPeriod()`, `openAgentFilter()`, `agpAll()`, `agpNone()`, `agpClose()`, `agpApply()`, `clearAgentFilter()` — atualiza `showPage()` e `MutationObserver`

- [ ] **Step 1: Adicionar renderAgentTab()**

Adicionar após `renderAgentCsat()`:

```javascript
function renderAgentTab() {
  renderAgentLive();
  renderAgentPerf();
  renderAgentCsat();
}
```

- [ ] **Step 2: Adicionar setAgentTabPeriod()**

```javascript
function setAgentTabPeriod(p) {
  _agentTabPeriod = p;
  _agentPerfData  = null;
  _agentExpanded  = null;
  document.querySelectorAll('.agent-pill').forEach(btn => {
    btn.classList.toggle('active', btn.textContent.trim() === ({ '1': 'Mês atual', '3': '3 meses', '6': '6 meses', '12': '12 meses' }[p]));
  });
  fetchAgentTab();
}
```

- [ ] **Step 3: Adicionar funções do popup de filtro de agentes**

```javascript
function openAgentFilter(event) {
  event.stopPropagation();
  const popup = document.getElementById('agp');
  if (!popup) return;
  const rect = event.currentTarget.getBoundingClientRect();
  popup.style.top  = (rect.bottom + 6) + 'px';
  popup.style.left = rect.left + 'px';
  _agp.sel = _agentTabFilter ? new Set(_agentTabFilter) : new Set(_agentList.map(a => a.id));
  agpRender();
  popup.classList.add('open');
  setTimeout(() => document.addEventListener('click', agpOutside, { once: true }), 0);
}

function agpRender() {
  const body = document.getElementById('agp-body');
  if (!body) return;
  body.innerHTML = _agentList.map(a => `
    <label class="agp-item">
      <input type="checkbox" value="${a.id}" ${_agp.sel.has(a.id) ? 'checked' : ''} onchange="agpToggle(${a.id}, this.checked)">
      ${esc(a.name)}
    </label>`).join('');
}

function agpToggle(id, checked) {
  if (checked) _agp.sel.add(id); else _agp.sel.delete(id);
}

function agpAll()  { _agp.sel = new Set(_agentList.map(a => a.id)); agpRender(); }
function agpNone() { _agp.sel = new Set(); agpRender(); }

function agpClose() {
  document.getElementById('agp')?.classList.remove('open');
  document.removeEventListener('click', agpOutside);
}

function agpOutside(e) {
  if (!document.getElementById('agp')?.contains(e.target)) agpClose();
}

function agpApply() {
  const allSelected = _agp.sel.size === _agentList.length;
  _agentTabFilter = allSelected ? null : (_agp.sel.size > 0 ? new Set(_agp.sel) : null);
  agpClose();
  updateAgentFilterUI();
  _agentPerfData  = null;
  _agentExpanded  = null;
  fetchAgentTab();
}

function clearAgentFilter() {
  _agentTabFilter = null;
  updateAgentFilterUI();
  _agentPerfData  = null;
  _agentExpanded  = null;
  fetchAgentTab();
}

function updateAgentFilterUI() {
  const trig  = document.getElementById('agent-filter-trigger');
  const txt   = document.getElementById('agent-filter-trigger-txt');
  const chips = document.getElementById('agent-filter-chips');
  const clear = document.getElementById('agent-filter-clear');
  if (!_agentTabFilter) {
    if (txt)   txt.textContent = 'Todos os agentes';
    if (trig)  trig.classList.remove('active');
    if (chips) chips.innerHTML = '';
    if (clear) clear.style.display = 'none';
    return;
  }
  if (txt)  txt.textContent = `${_agentTabFilter.size} selecionado${_agentTabFilter.size > 1 ? 's' : ''}`;
  if (trig) trig.classList.add('active');
  if (clear) clear.style.display = '';
  if (chips) chips.innerHTML = [..._agentTabFilter].map(id => {
    const a = _agentList.find(a => a.id === id);
    const name = a?.name || `#${id}`;
    return `<span class="inbox-chip">${esc(name)}<button class="inbox-chip-rm" onclick="removeAgentChip(${id})" aria-label="Remover ${esc(name)}">×</button></span>`;
  }).join('');
}

function removeAgentChip(id) {
  if (!_agentTabFilter) return;
  _agentTabFilter.delete(id);
  if (_agentTabFilter.size === 0) _agentTabFilter = null;
  updateAgentFilterUI();
  _agentPerfData  = null;
  _agentExpanded  = null;
  fetchAgentTab();
}
```

- [ ] **Step 4: Atualizar showPage()**

Localizar a função `showPage` completa e substituí-la:

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

- [ ] **Step 5: Atualizar MutationObserver**

Localizar:
```javascript
new MutationObserver(() => {
  if (document.getElementById('graficos-page').style.display !== 'none' && _chartData.length) {
    renderCharts();
  }
}).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
```

Substituir por:
```javascript
new MutationObserver(() => {
  if (document.getElementById('graficos-page').style.display !== 'none' && _chartData.length) renderCharts();
  if (document.getElementById('agentes-page').style.display !== 'none' && _agentPerfData) renderAgentTab();
}).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
```

- [ ] **Step 6: Verificar fluxo completo**

1. Abrir http://localhost:8765
2. Clicar em "Agentes" — todas as 3 seções devem carregar com dados reais
3. Clicar nos pills de período (Mês atual / 3 meses / 6 meses / 12 meses) — tabela deve recarregar com dados do período
4. Clicar em "Todos os agentes" — popup deve abrir com checkboxes para cada agente
5. Selecionar alguns agentes e clicar "Aplicar" — chips devem aparecer, tabela deve filtrar
6. Clicar "✕ Limpar" — filtro deve ser removido
7. Trocar tema (claro/escuro) — tabela deve re-renderizar com cores corretas
8. Voltar para "Painel", esperar refresh automático (60s), voltar para "Agentes" — dados devem ser atualizados

- [ ] **Step 7: Commit final**

```bash
git add index.html
git commit -m "feat: aba Agentes completa — status ao vivo, desempenho histórico, CSAT, filtros e seletor de período"
```

---

## Self-Review

**Spec coverage:**
- ✅ Sidebar item "Agentes" entre Painel e Análise
- ✅ Seletor de período com 4 opções, default 3 meses
- ✅ Filtro de agentes com popup, chips, e limpar
- ✅ Seção 1: cards online/busy/offline + tabela ao vivo com status, conversas e mensagem mais antiga
- ✅ Seção 2: tabela ordenável por todas as colunas, Volume desc padrão, zeros ao final
- ✅ Seção 2: gráfico de evolução ao clicar em agente (toggle), um expandido por vez
- ✅ Seção 3: CSAT com detecção automática ou placeholder com instrução
- ✅ Colunas: Volume, TMA, TMR, Taxa de Resolução, Msgs/Conversa, Total de Mensagens
- ✅ Token sem acesso a `type=agent` → mensagem graceful
- ✅ Token sem acesso a overview → seção 1 com mensagem, seções 2 e 3 funcionam
- ✅ fetchAll() integração: salva _agentList, marca _agentTabDirty
- ✅ MutationObserver atualizado para tema
- ✅ showPage() atualizado para 3 abas

**Gaps identificados:** Nenhum.
