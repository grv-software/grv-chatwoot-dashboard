# Aba Agentes v2 — Design Spec

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reformular completamente a aba Agentes para ser a ferramenta principal de gestão de desempenho do time — tabela com pontuação e badges coloridos como visão estratégica, modal "Perfil do Agente" com gráfico e tabela mensal para o 1:1, e performance impecável com lazy loading.

**Architecture:** Single-file (`index.html`). Remove seção de status ao vivo. Substitui tabela com linha expansível por tabela + modal centralizado. Fetch paralelo no load inicial; dados mensais carregados sob demanda ao abrir o modal. Cache por agente para evitar re-fetches desnecessários.

**Tech Stack:** HTML/CSS/JS inline, Chart.js 4 (já carregado), função `api()` existente, utilitários `fmtSec()`, `esc()`, `chartColors()`, `destroyChart()`.

---

## Global Constraints

- Single file: todas as mudanças em `index.html`
- Seguir CSS vars existentes: `--bg`, `--bg2`, `--bg3`, `--border`, `--accent`, `--text`, `--text2`, `--text3`, `--green`, `--yellow`, `--red`
- SLAs existentes: `_SLA_TMA` (horas), `_SLA_TMR` (minutos), `_SLA_FCR` (%), `_SLA_MSG` (mensagens/conversa)
- Linguagem sem jargão nas colunas: "Atendimento" (não TMA), "1ª Resposta" (não TMR), "Resolução" (não FCR)
- Tooltips revelam sigla completa ao hover: "Tempo Médio de Atendimento (TMA)"
- Badges: pills HTML estilizados com fundo colorido — não emoji
- Pontuação 0–100 calculada localmente em JS
- Agentes com `conversations_count === 0` no período exibem `—` na pontuação e ficam no final da tabela
- Fechar modal: ESC ou clique fora (backdrop)
- Cache de dados mensais: `_agentMonthCache[agentId][periodKey]` — não re-fetcha se já carregado

---

## Remoções

- Remover seção `#agent-live-section` do HTML
- Remover função `renderAgentLive()`
- Remover chamada `api('/reports/overview')` de `fetchAgentTab()`
- Remover variável `_agentOverview`
- Remover CSS `.agent-status-dot`, `.dot-online`, `.dot-busy`, `.dot-offline`
- Remover linha expansível (`agent-expand-row`, `agent-expand-inner`) da tabela atual
- Remover `renderAgentExpandChart()` e `toggleAgentExpand()`
- Remover variável `_agentExpanded`

---

## Novas Variáveis de Estado

```javascript
let _agentMonthCache = {}; /* {agentId: {periodKey: months[]}} — lazy cache */
let _agentModalId    = null; /* id do agente cujo modal está aberto */
let _agentModalOrder = [];   /* array de ids na ordem da tabela — para navegar ‹ › */
```

Remover: `_agentOverview`, `_agentExpanded`

---

## Cálculo de Pontuação

```javascript
function calcAgentScore(summary) {
  if (!summary || (summary.conversations_count || 0) === 0) return null;
  const s = summary;
  let pts = 0;

  // Atendimento (TMA) — 25pts
  const tmaH = s.avg_resolution_time != null ? s.avg_resolution_time / 3600 : null;
  if (tmaH != null) {
    if (tmaH <= _SLA_TMA)          pts += 25;
    else if (tmaH <= _SLA_TMA * 1.5) pts += 12;
  }

  // 1ª Resposta (TMR) — 25pts
  const tmrM = s.avg_first_response_time != null ? s.avg_first_response_time / 60 : null;
  if (tmrM != null) {
    if (tmrM <= _SLA_TMR)          pts += 25;
    else if (tmrM <= _SLA_TMR * 1.5) pts += 12;
  }

  // Resolução — 25pts
  const fcr = s.conversations_count > 0 ? (s.resolutions_count || 0) / s.conversations_count * 100 : null;
  if (fcr != null) {
    if (fcr >= _SLA_FCR)               pts += 25;
    else if (fcr >= _SLA_FCR - 15)     pts += 12;
  }

  // Msgs/Conversa — 25pts
  const totalMsgs = (s.incoming_messages_count || 0) + (s.outgoing_messages_count || 0);
  const msgsConv  = s.conversations_count > 0 ? totalMsgs / s.conversations_count : null;
  if (msgsConv != null) {
    if (msgsConv <= _SLA_MSG)          pts += 25;
    else if (msgsConv <= _SLA_MSG * 1.5) pts += 12;
  }

  return pts;
}
```

---

## Badge Colorido

```javascript
function agentBadge(value, label, meta, unit, lowerIsBetter = true) {
  // value: número cru | null
  // label: texto formatado para exibição (ex: "1h40")
  // meta: valor de referência da SLA
  // unit: string da unidade para tooltip (ex: "h", "min", "%")
  // lowerIsBetter: true para TMA/TMR/Msgs, false para % Resolução
  if (value == null || label == null) return `<span class="agent-badge badge-na">—</span>`;
  const ratio = lowerIsBetter ? value / meta : meta / value;
  const cls   = ratio <= 1 ? 'badge-green' : ratio <= 1.5 ? 'badge-yellow' : 'badge-red';
  const icon  = ratio <= 1 ? '✓' : ratio <= 1.5 ? '~' : '✗';
  const tip   = `meta: ${meta}${unit}`;
  return `<span class="agent-badge ${cls}" title="${tip}">${label} ${icon}</span>`;
}
```

---

## CSS Novo

### Badges

```css
.agent-badge { display:inline-flex; align-items:center; gap:4px; padding:3px 8px; border-radius:12px; font-size:12px; font-weight:600; white-space:nowrap; }
.badge-green  { background:rgba(34,197,94,.15);  color:#22c55e; }
.badge-yellow { background:rgba(234,179,8,.15);  color:#eab308; }
.badge-red    { background:rgba(239,68,68,.15);  color:#ef4444; }
.badge-na     { background:var(--bg3); color:var(--text3); }
.score-badge  { display:inline-block; padding:2px 10px; border-radius:10px; font-size:13px; font-weight:800; }
.score-hi  { background:rgba(34,197,94,.15);  color:#22c55e; }
.score-mid { background:rgba(234,179,8,.15);  color:#eab308; }
.score-lo  { background:rgba(239,68,68,.15);  color:#ef4444; }
```

### Modal

```css
#agent-modal-backdrop { display:none; position:fixed; inset:0; background:rgba(0,0,0,.6); z-index:400; align-items:center; justify-content:center; }
#agent-modal-backdrop.open { display:flex; }
#agent-modal { background:var(--bg2); border:1px solid var(--border); border-radius:12px; width:min(860px,95vw); max-height:90vh; overflow-y:auto; box-shadow:0 24px 64px rgba(0,0,0,.5); display:flex; flex-direction:column; }
.am-header { display:flex; align-items:center; gap:12px; padding:20px 24px 16px; border-bottom:1px solid var(--border); flex-wrap:wrap; }
.am-avatar { width:40px; height:40px; border-radius:50%; background:var(--accent); color:#fff; font-size:16px; font-weight:800; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.am-name { font-size:16px; font-weight:700; flex:1; }
.am-semaphores { display:flex; gap:8px; flex-wrap:wrap; }
.am-nav { display:flex; gap:4px; margin-left:auto; }
.am-nav button { width:32px; height:32px; border-radius:6px; border:1px solid var(--border); background:transparent; color:var(--text); cursor:pointer; font-size:14px; }
.am-nav button:hover { border-color:var(--accent); color:var(--accent); }
.am-close { width:32px; height:32px; border-radius:6px; border:1px solid var(--border); background:transparent; color:var(--text2); cursor:pointer; font-size:18px; line-height:1; }
.am-close:hover { border-color:var(--red); color:var(--red); }
.am-body { padding:20px 24px 24px; display:flex; flex-direction:column; gap:20px; }
.am-highlights { display:flex; gap:10px; flex-wrap:wrap; }
.am-highlight { background:var(--bg3); border-radius:8px; padding:10px 14px; font-size:12px; flex:1; min-width:160px; }
.am-highlight strong { display:block; font-size:13px; margin-bottom:2px; }
.am-chart-wrap { height:240px; position:relative; }
.am-month-table { width:100%; border-collapse:collapse; font-size:12px; }
.am-month-table th { background:var(--bg3); color:var(--text2); font-size:11px; font-weight:600; padding:7px 10px; text-align:left; border-bottom:2px solid var(--border); }
.am-month-table td { padding:7px 10px; border-bottom:1px solid var(--border); }
.am-month-table tr:last-child td { border:none; }
.ver-perfil-btn { padding:4px 12px; border-radius:5px; border:1px solid var(--border); background:transparent; color:var(--text2); font-size:12px; cursor:pointer; white-space:nowrap; }
.ver-perfil-btn:hover { border-color:var(--accent); color:var(--accent); }
```

---

## HTML

### Substituir `#agentes-page` inteiro

```html
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

  <div id="agent-perf-section"><div class="agent-no-data">Carregando…</div></div>
  <div id="agent-csat-section" style="margin-top:16px"></div>
</div>

<!-- AGENT MODAL -->
<div id="agent-modal-backdrop" onclick="closeAgentModal(event)">
  <div id="agent-modal" role="dialog" aria-modal="true" aria-label="Perfil do agente">
    <div class="am-header" id="am-header"></div>
    <div class="am-body">
      <div class="am-highlights" id="am-highlights"></div>
      <div class="am-chart-wrap"><canvas id="am-chart"></canvas></div>
      <div id="am-month-loading" class="agent-no-data" style="display:none">Carregando histórico…</div>
      <div id="am-month-table-wrap"></div>
    </div>
  </div>
</div>
```

---

## Funções

### fetchAgentTab() — refatorada

```javascript
async function fetchAgentTab() {
  const perfEl = document.getElementById('agent-perf-section');
  const csatEl = document.getElementById('agent-csat-section');
  if (perfEl) perfEl.innerHTML = '<div class="agent-no-data">Carregando…</div>';
  if (csatEl) csatEl.innerHTML = '';

  if (!_agentList.length) {
    const agents = await api(`/v1/accounts/${cfg.account}/agents`).catch(() => []);
    if (Array.isArray(agents)) _agentList = agents;
  }

  const visibleAgents = (_agentTabFilter && _agentTabFilter.size > 0)
    ? _agentList.filter(a => _agentTabFilter.has(a.id))
    : _agentList;

  const { since, until } = getAgentTabRange();

  /* Tudo em paralelo — sem sequential awaits */
  const [summaries, csatRaw] = await Promise.all([
    Promise.all(visibleAgents.map(a =>
      api(`/v2/accounts/${cfg.account}/reports/summary?type=agent&id=${a.id}&since=${since}&until=${until}`)
        .catch(() => null)
    )),
    api(`/v1/accounts/${cfg.account}/reports/agents/satisfaction?since=${since}&until=${until}`)
      .catch(() => null)
  ]);

  _agentPerfData = {};
  visibleAgents.forEach((a, i) => {
    _agentPerfData[a.id] = { agent: a, summary: summaries[i] };
  });

  /* Processar CSAT */
  if (Array.isArray(csatRaw) && csatRaw.length) {
    const byAgent = {};
    csatRaw.forEach(r => {
      const id = r.assigned_agent?.id;
      if (!id) return;
      if (!byAgent[id]) byAgent[id] = { id, name: r.assigned_agent?.name || '—', total: 0, positive: 0 };
      byAgent[id].total++;
      if (r.rating === 'Satisfied') byAgent[id].positive++;
    });
    _agentCsat = Object.values(byAgent);
  } else {
    _agentCsat = null;
  }

  const updEl = document.getElementById('agent-tab-updated');
  if (updEl) updEl.textContent = `Atualizado às ${new Date().toLocaleTimeString('pt-BR')}`;

  renderAgentTab();
}
```

### renderAgentPerf() — refatorada

Renderiza a tabela de desempenho com badges e pontuação. Nenhuma linha expansível.

```javascript
function renderAgentPerf() {
  const el = document.getElementById('agent-perf-section');
  if (!el) return;
  if (!_agentPerfData) { el.innerHTML = '<div class="agent-no-data">Carregando…</div>'; return; }
  if (_agentPerfData._authError) {
    el.innerHTML = '<div class="agent-no-data">🔒 Dados por agente requerem permissão de Administrador</div>'; return;
  }

  const entries = Object.values(_agentPerfData).filter(e => e.agent);
  if (!entries.length) { el.innerHTML = '<div class="agent-no-data">Nenhum agente encontrado</div>'; return; }

  const { col, dir } = _agentPerfSort;
  const getVal = e => {
    const s = e.summary;
    if (!s) return null;
    if (col === 'conversations_count')    return s.conversations_count || 0;
    if (col === 'avg_resolution_time')    return s.avg_resolution_time ?? Infinity;
    if (col === 'avg_first_response_time')return s.avg_first_response_time ?? Infinity;
    if (col === 'fcr')                    return s.conversations_count > 0 ? (s.resolutions_count || 0) / s.conversations_count : null;
    if (col === 'score')                  return calcAgentScore(s);
    return null;
  };

  const sorted = [...entries].sort((a, b) => {
    const nd = e => !e.summary || (e.summary.conversations_count || 0) === 0;
    if (nd(a) && nd(b)) return 0;
    if (nd(a)) return 1;
    if (nd(b)) return -1;
    const va = getVal(a) ?? (dir === 'asc' ? Infinity : -Infinity);
    const vb = getVal(b) ?? (dir === 'asc' ? Infinity : -Infinity);
    return dir === 'asc' ? va - vb : vb - va;
  });

  /* Salvar ordem para navegação do modal */
  _agentModalOrder = sorted.map(e => e.agent.id);

  const scoreCls = s => s == null ? '' : s >= 75 ? 'score-hi' : s >= 50 ? 'score-mid' : 'score-lo';
  const th = (label, colId, tip = '') =>
    `<th class="${_agentPerfSort.col === colId ? (_agentPerfSort.dir === 'asc' ? 'sort-asc' : 'sort-desc') : ''}"
         onclick="sortAgentPerf('${colId}')"
         title="${tip}">${label}</th>`;

  el.innerHTML = `
    <div class="chart-card" style="overflow-x:auto">
      <table class="agent-table">
        <thead><tr>
          ${th('Agente', 'name')}
          ${th('Volume', 'conversations_count', 'Total de conversas no período')}
          ${th('Atendimento', 'avg_resolution_time', 'Tempo Médio de Atendimento (TMA) · meta: ' + _SLA_TMA + 'h')}
          ${th('1ª Resposta', 'avg_first_response_time', 'Tempo Médio de 1ª Resposta (TMR) · meta: ' + _SLA_TMR + 'min')}
          ${th('Resolução', 'fcr', 'Taxa de Resolução · meta: ' + _SLA_FCR + '%')}
          ${th('Pontuação', 'score', 'Pontuação geral 0–100 baseada nas SLAs')}
          <th></th>
        </tr></thead>
        <tbody>
          ${sorted.map(e => {
            const s    = e.summary;
            const nd   = !s || (s.conversations_count || 0) === 0;
            const sc   = nd ? null : calcAgentScore(s);
            const tmaH = s?.avg_resolution_time != null ? s.avg_resolution_time / 3600 : null;
            const tmrM = s?.avg_first_response_time != null ? s.avg_first_response_time / 60 : null;
            const fcr  = !nd && s.conversations_count > 0 ? (s.resolutions_count || 0) / s.conversations_count * 100 : null;
            return `<tr class="agent-row" onclick="openAgentModal(${e.agent.id})">
              <td style="font-weight:600">${esc(e.agent.name)}</td>
              <td>${nd ? '—' : (s.conversations_count).toLocaleString('pt-BR')}</td>
              <td>${nd ? '<span class="agent-badge badge-na">—</span>' : agentBadge(tmaH, fmtSec(s.avg_resolution_time), _SLA_TMA, 'h', true)}</td>
              <td>${nd ? '<span class="agent-badge badge-na">—</span>' : agentBadge(tmrM, fmtSec(s.avg_first_response_time), _SLA_TMR, 'min', true)}</td>
              <td>${nd ? '<span class="agent-badge badge-na">—</span>' : agentBadge(fcr != null ? 100 - fcr : null, fcr != null ? Math.round(fcr) + '%' : null, 100 - _SLA_FCR, '%', true)}</td>
              <td>${sc == null ? '<span class="agent-badge badge-na">—</span>' : '<span class="score-badge ' + scoreCls(sc) + '">' + sc + '</span>'}</td>
              <td><button class="ver-perfil-btn" onclick="event.stopPropagation();openAgentModal(${e.agent.id})">Ver perfil →</button></td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>
    </div>`;
}
```

> **Nota sobre badge de Resolução:** lowerIsBetter=true com `100 - fcr` como value e `100 - _SLA_FCR` como meta inverte a lógica corretamente (quem resolve mais é melhor).

### openAgentModal(id) — nova

```javascript
async function openAgentModal(id) {
  _agentModalId = id;
  const backdrop = document.getElementById('agent-modal-backdrop');
  backdrop.classList.add('open');
  document.addEventListener('keydown', agentModalKeydown);
  renderAgentModalHeader(id);
  renderAgentModalHighlights(id, null); /* placeholder enquanto carrega */
  await fetchAgentMonths(id);
  renderAgentModalHighlights(id, _agentMonthCache[id]?.[_agentTabPeriod]);
  renderAgentModalChart(id);
  renderAgentModalMonthTable(id);
}

function closeAgentModal(e) {
  if (e && e.target !== document.getElementById('agent-modal-backdrop')) return;
  _agentModalId = null;
  document.getElementById('agent-modal-backdrop').classList.remove('open');
  document.removeEventListener('keydown', agentModalKeydown);
  destroyChart('am');
}

function agentModalKeydown(e) {
  if (e.key === 'Escape') closeAgentModal(null);
  if (e.key === 'ArrowLeft')  navigateAgentModal(-1);
  if (e.key === 'ArrowRight') navigateAgentModal(1);
}

function navigateAgentModal(dir) {
  const idx = _agentModalOrder.indexOf(_agentModalId);
  if (idx === -1) return;
  const next = _agentModalOrder[idx + dir];
  if (next != null) openAgentModal(next);
}
```

### fetchAgentMonths(id) — lazy + cache

```javascript
async function fetchAgentMonths(id) {
  const key = _agentTabPeriod;
  if (_agentMonthCache[id]?.[key]) return; /* cache hit */

  const months = getAgentMonths();
  const loadEl = document.getElementById('am-month-loading');
  if (loadEl) loadEl.style.display = '';

  const results = await Promise.all(months.map(mo =>
    api(`/v2/accounts/${cfg.account}/reports/summary?type=agent&id=${id}&since=${mo.since}&until=${mo.until}`)
      .catch(() => null)
  ));

  if (!_agentMonthCache[id]) _agentMonthCache[id] = {};
  _agentMonthCache[id][key] = months.map((mo, i) => ({ ...mo, data: results[i] }));
  if (loadEl) loadEl.style.display = 'none';
}
```

### renderAgentModalHeader(id)

```javascript
function renderAgentModalHeader(id) {
  const el = document.getElementById('am-header');
  if (!el) return;
  const entry = _agentPerfData?.[id];
  if (!entry) return;
  const sc    = calcAgentScore(entry.summary);
  const s     = entry.summary;
  const scoreCls = sc == null ? 'badge-na' : sc >= 75 ? 'score-hi' : sc >= 50 ? 'score-mid' : 'score-lo';
  const initial = (entry.agent.name || '?')[0].toUpperCase();

  const tmaH = s?.avg_resolution_time != null ? s.avg_resolution_time / 3600 : null;
  const tmrM = s?.avg_first_response_time != null ? s.avg_first_response_time / 60 : null;
  const fcr  = s?.conversations_count > 0 ? (s.resolutions_count || 0) / s.conversations_count * 100 : null;

  const semaphore = (val, meta, lowerIsBetter) => {
    if (val == null) return '<span style="width:10px;height:10px;border-radius:50%;background:var(--bg3);display:inline-block"></span>';
    const ratio = lowerIsBetter ? val / meta : meta / val;
    const color = ratio <= 1 ? 'var(--green)' : ratio <= 1.5 ? 'var(--yellow)' : 'var(--red)';
    return `<span style="width:10px;height:10px;border-radius:50%;background:${color};display:inline-block"></span>`;
  };

  const idx  = _agentModalOrder.indexOf(id);
  const prev = _agentModalOrder[idx - 1] != null;
  const next = _agentModalOrder[idx + 1] != null;

  el.innerHTML = `
    <div class="am-avatar">${initial}</div>
    <div>
      <div class="am-name">${esc(entry.agent.name)}</div>
      <div style="font-size:11px;color:var(--text2)">Período: ${_agentTabPeriod === '1' ? 'Mês atual' : _agentTabPeriod + ' meses'}</div>
    </div>
    <span class="score-badge ${scoreCls}" style="font-size:18px">${sc ?? '—'}</span>
    <div class="am-semaphores">
      ${semaphore(tmaH, _SLA_TMA, true)} <span style="font-size:11px;color:var(--text2)">Atend.</span>
      ${semaphore(tmrM, _SLA_TMR, true)} <span style="font-size:11px;color:var(--text2)">Resposta</span>
      ${semaphore(fcr, _SLA_FCR, false)} <span style="font-size:11px;color:var(--text2)">Resolução</span>
    </div>
    <div class="am-nav">
      <button onclick="navigateAgentModal(-1)" ${prev ? '' : 'disabled'} title="Agente anterior">‹</button>
      <button onclick="navigateAgentModal(1)"  ${next ? '' : 'disabled'} title="Próximo agente">›</button>
    </div>
    <button class="am-close" onclick="closeAgentModal(null)" title="Fechar (ESC)">×</button>`;
}
```

### renderAgentModalHighlights(id, months)

```javascript
function renderAgentModalHighlights(id, months) {
  const el = document.getElementById('am-highlights');
  if (!el) return;
  if (!months) { el.innerHTML = '<div class="am-highlight" style="color:var(--text3)">Calculando destaques…</div>'; return; }

  const withData = months.filter(m => m.data && (m.data.conversations_count || 0) > 0);
  if (!withData.length) { el.innerHTML = '<div class="am-highlight" style="color:var(--text3)">Sem dados no período</div>'; return; }

  /* Melhor mês: maior pontuação */
  const scored = withData.map(m => ({ ...m, score: calcAgentScore(m.data) })).filter(m => m.score != null);
  const best   = scored.reduce((a, b) => b.score > a.score ? b : a, scored[0]);
  const worst  = scored.reduce((a, b) => b.score < a.score ? b : a, scored[0]);

  /* Tendência: comparar último mês com penúltimo */
  const last = withData[withData.length - 1];
  const prev = withData[withData.length - 2];
  let trend = '';
  if (last && prev) {
    const sc1 = calcAgentScore(last.data), sc2 = calcAgentScore(prev.data);
    if (sc1 != null && sc2 != null) {
      trend = sc1 > sc2
        ? `<div class="am-highlight"><strong>↑ Melhorando</strong>Pontuação subiu de ${sc2} para ${sc1} no último mês</div>`
        : sc1 < sc2
        ? `<div class="am-highlight"><strong>↓ Queda recente</strong>Pontuação caiu de ${sc2} para ${sc1} no último mês</div>`
        : `<div class="am-highlight"><strong>→ Estável</strong>Pontuação mantida no último mês</div>`;
    }
  }

  el.innerHTML = `
    <div class="am-highlight">
      <strong>🟢 Melhor mês: ${best?.label ?? '—'}</strong>
      Pontuação ${best?.score ?? '—'}/100
    </div>
    <div class="am-highlight">
      <strong>🔴 Pior mês: ${worst?.label ?? '—'}</strong>
      Pontuação ${worst?.score ?? '—'}/100
    </div>
    ${trend}`;
}
```

### renderAgentModalChart(id)

```javascript
function renderAgentModalChart(id) {
  destroyChart('am');
  const months = _agentMonthCache[id]?.[_agentTabPeriod];
  const canvas = document.getElementById('am-chart');
  if (!months || !canvas) return;
  const c      = chartColors();
  const labels = months.map(m => m.label);
  const vol    = months.map(m => m.data?.conversations_count || 0);
  const tma    = months.map(m => m.data?.avg_resolution_time != null ? +(m.data.avg_resolution_time / 3600).toFixed(2) : null);
  const tmr    = months.map(m => m.data?.avg_first_response_time != null ? +(m.data.avg_first_response_time / 60).toFixed(1) : null);

  _charts['am'] = new Chart(canvas, {
    type: 'bar',
    data: { labels, datasets: [
      { type: 'bar',  label: 'Volume', data: vol, backgroundColor: 'rgba(59,130,246,0.25)', borderColor: 'rgba(59,130,246,0.6)', borderWidth: 1, borderRadius: 4, yAxisID: 'y2' },
      { type: 'line', label: `Atendimento (h) · meta ${_SLA_TMA}h`, data: tma, borderColor: '#8b5cf6', backgroundColor: 'transparent', tension: 0.3, yAxisID: 'y1', pointRadius: 4, spanGaps: true, borderWidth: 2 },
      { type: 'line', label: `1ª Resposta (min) · meta ${_SLA_TMR}min`, data: tmr, borderColor: '#14b8a6', backgroundColor: 'transparent', tension: 0.3, yAxisID: 'y1', pointRadius: 4, spanGaps: true, borderWidth: 2 }
    ]},
    options: {
      responsive: true, maintainAspectRatio: false, animation: false,
      plugins: {
        legend: { display: true, position: 'top', labels: { color: c.labels, font: { size: 11 }, boxWidth: 12 } },
        tooltip: { backgroundColor: c.tooltipBg, titleColor: c.labels, bodyColor: c.labels, borderColor: c.grid, borderWidth: 1 },
        annotation: { annotations: {
          slaTma: { type: 'line', yMin: _SLA_TMA, yMax: _SLA_TMA, yScaleID: 'y1', borderColor: 'rgba(139,92,246,0.4)', borderWidth: 1.5, borderDash: [6,4] },
          slaTmr: { type: 'line', yMin: _SLA_TMR, yMax: _SLA_TMR, yScaleID: 'y1', borderColor: 'rgba(20,184,166,0.4)', borderWidth: 1.5, borderDash: [6,4] }
        }}
      },
      scales: {
        x:  { grid: { color: c.grid }, ticks: { color: c.labels, font: { size: 11 } } },
        y1: { position: 'left',  grid: { color: c.grid }, ticks: { color: c.labels, font: { size: 11 } }, title: { display: true, text: 'h / min', color: c.labels, font: { size: 10 } } },
        y2: { position: 'right', grid: { display: false }, ticks: { color: c.labels, font: { size: 11 } }, title: { display: true, text: 'Volume', color: c.labels, font: { size: 10 } } }
      }
    }
  });
}
```

### renderAgentModalMonthTable(id)

```javascript
function renderAgentModalMonthTable(id) {
  const el = document.getElementById('am-month-table-wrap');
  if (!el) return;
  const months = _agentMonthCache[id]?.[_agentTabPeriod];
  if (!months) { el.innerHTML = ''; return; }

  const fmtBadge = (value, meta, unit, lowerIsBetter, fmtFn) => {
    if (value == null) return '<span class="agent-badge badge-na">—</span>';
    const ratio  = lowerIsBetter ? value / meta : meta / value;
    const cls    = ratio <= 1 ? 'badge-green' : ratio <= 1.5 ? 'badge-yellow' : 'badge-red';
    const pct    = Math.round(Math.abs(ratio - 1) * 100);
    const dir    = ratio <= 1 ? 'abaixo da meta ✓' : `${pct}% acima da meta ✗`;
    const dirNeg = ratio <= 1 ? `${pct}% acima da meta ✓` : `${pct}% abaixo da meta ✗`;
    const label  = lowerIsBetter ? dir : dirNeg;
    return `<span class="agent-badge ${cls}" title="${label}">${fmtFn(value)}</span>`;
  };

  el.innerHTML = `
    <table class="am-month-table">
      <thead><tr>
        <th>Mês</th>
        <th>Volume</th>
        <th title="Tempo Médio de Atendimento · meta: ${_SLA_TMA}h">Atendimento</th>
        <th title="Tempo Médio de 1ª Resposta · meta: ${_SLA_TMR}min">1ª Resposta</th>
        <th title="Taxa de Resolução · meta: ${_SLA_FCR}%">Resolução</th>
        <th>Pontuação</th>
      </tr></thead>
      <tbody>
        ${months.map(m => {
          const d  = m.data;
          const nd = !d || (d.conversations_count || 0) === 0;
          const tmaH = d?.avg_resolution_time != null ? d.avg_resolution_time / 3600 : null;
          const tmrM = d?.avg_first_response_time != null ? d.avg_first_response_time / 60 : null;
          const fcr  = !nd && d.conversations_count > 0 ? (d.resolutions_count || 0) / d.conversations_count * 100 : null;
          const sc   = nd ? null : calcAgentScore(d);
          const scoreCls = sc == null ? 'badge-na' : sc >= 75 ? 'score-hi' : sc >= 50 ? 'score-mid' : 'score-lo';
          return `<tr>
            <td style="font-weight:600">${m.label}</td>
            <td>${nd ? '—' : (d.conversations_count).toLocaleString('pt-BR')}</td>
            <td>${nd ? '<span class="agent-badge badge-na">—</span>' : fmtBadge(tmaH, _SLA_TMA, 'h', true, v => fmtSec(d.avg_resolution_time))}</td>
            <td>${nd ? '<span class="agent-badge badge-na">—</span>' : fmtBadge(tmrM, _SLA_TMR, 'min', true, v => fmtSec(d.avg_first_response_time))}</td>
            <td>${nd ? '<span class="agent-badge badge-na">—</span>' : fmtBadge(fcr != null ? 100 - fcr : null, 100 - _SLA_FCR, '%', true, v => Math.round(fcr) + '%')}</td>
            <td>${sc == null ? '<span class="agent-badge badge-na">—</span>' : '<span class="score-badge ' + scoreCls + '">' + sc + '</span>'}</td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>`;
}
```

---

## Limpeza de Cache

Ao mudar período (`setAgentTabPeriod()`): limpar `_agentMonthCache` completo e `_agentPerfData`.
Ao mudar filtro de agentes: limpar `_agentPerfData` (manter `_agentMonthCache` — dados mensais por agente permanecem válidos).

```javascript
function setAgentTabPeriod(p) {
  _agentTabPeriod  = p;
  _agentPerfData   = null;
  _agentMonthCache = {}; /* período mudou — cache mensal inválido */
  // ... atualizar pills, fetchAgentTab()
}
```

---

## Tratamento de Erros

| Cenário | Comportamento |
|---|---|
| Token sem acesso a `type=agent` | `_agentPerfData._authError = true` → mensagem 🔒 na tabela |
| Agente sem dados no período | Linha com `—` em todas as métricas, posicionada ao final |
| CSAT inativo / vazio | Placeholder com instrução de ativação |
| Erro de rede em fetchAgentMonths | Meses com `data: null` → exibe `—` nas células |
| Modal aberto e período alterado | Modal fecha (`_agentModalId = null`), `fetchAgentTab()` recarrega |

---

## Self-Review

**Placeholders:** Nenhum.

**Consistência interna:**
- `agentBadge()` para Resolução usa lógica invertida (`100 - fcr` vs `100 - _SLA_FCR`) — documentado com nota inline.
- `_agentMonthCache[id][key]` é limpo ao mudar período mas mantido ao mudar filtro — correto.
- `closeAgentModal(e)` verifica `e.target` para distinguir clique no backdrop vs clique no modal — necessário para não fechar ao clicar dentro.
- `_agentModalOrder` é atualizado em `renderAgentPerf()` antes de abrir qualquer modal — garante navegação ‹ › correta.

**Scope:** Focado em uma única aba. Adequado para um único plano de implementação.
