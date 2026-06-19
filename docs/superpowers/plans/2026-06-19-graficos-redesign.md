# Redesign da Aba Análise — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reestruturar a aba "Gráficos" → "Análise" em duas seções temáticas (Operacional / Desempenho) com 5 gráficos novos, removendo FCR e TMR, adicionando Pico de Horário e Status donut, com indicadores de tendência e diferenciação de cores.

**Architecture:** Single-file dashboard (`index.html`). As mudanças tocam três zonas independentes do arquivo: bloco CSS (~linha 140), bloco HTML da sidebar + página de gráficos (~linhas 348–536) e função JS `renderCharts()` (~linhas 1527–1591). Nenhuma nova dependência é necessária — Chart.js já está carregado e `_rawConvs` / `_chartData` já existem.

**Tech Stack:** HTML/CSS/JS vanilla; Chart.js 4 (CDN já incluído); API Chatwoot via proxy local.

## Global Constraints

- Arquivo único: `index.html` — nunca criar arquivos JS/CSS separados
- CSS variables existentes (`--bg`, `--accent`, `--text3`, etc.) devem ser reutilizadas — não use cores hardcoded onde já existe variável
- `_rawConvs` é o array de conversas abertas já carregado — não fazer nova chamada de API
- `_chartData` é o array de dados mensais já retornado por `fetchChartData()` — não alterar essa função
- `destroyChart(id)` deve ser chamado antes de recriar qualquer Chart.js — IDs novos: `'peak'` e `'status'`
- Manter suporte a tema claro/escuro via `chartColors()`
- Canvas IDs alterados: removidos `chart-tmr` e `chart-fcr`; adicionados `chart-peak` e `chart-status`

---

### Task 1: CSS — novos estilos para cards, seções e badge

**Files:**
- Modify: `index.html:140-150` (bloco `/* CHARTS PAGE */`)

**Interfaces:**
- Produz: `.section-divider`, `.section-divider-label`, `.badge-live`, `.chart-card-hdr`, `.chart-card-sub`, `.chart-trend-pos`, `.chart-trend-neg`, `.chart-grid-op`, `.chart-grid-perf`, `.chart-legend`, `.chart-legend-item`, `.chart-legend-dot`
- Consome: variáveis CSS existentes (`--border`, `--text3`, `--text2`, `--bg2`, `--bg3`, `--text`, `--green`)

- [ ] **Step 1: Localizar o bloco CSS de charts**

  Abrir `index.html`. Localizar a linha que contém `/* CHARTS PAGE */` (próximo da linha 140). O bloco atual é:

  ```css
  /* CHARTS PAGE */
  .chart-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
  @media (max-width:800px) { .chart-grid { grid-template-columns:1fr; } }
  .chart-card { background:var(--bg2); border:1px solid var(--border); border-radius:6px; padding:16px; }
  .chart-card-title { font-size:13px; font-weight:700; margin-bottom:12px; color:var(--text); }
  .chart-wrap { position:relative; height:220px; }
  .chart-na { display:flex; align-items:center; justify-content:center; height:220px; color:var(--text3); font-size:12px; font-style:italic; text-align:center; }
  .chart-hdr { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:16px; padding:4px 0; }
  .chart-hdr h2 { font-size:15px; font-weight:700; flex:1; }
  .chart-sel { padding:5px 10px; background:var(--bg3); border:1px solid var(--border); border-radius:4px; color:var(--text); font-size:12px; cursor:pointer; outline:none; }
  ```

- [ ] **Step 2: Substituir o bloco CSS de charts pelo novo**

  Substituir todo o bloco acima por:

  ```css
  /* CHARTS PAGE */
  .chart-grid-op   { display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; }
  .chart-grid-perf { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
  @media (max-width:900px) {
    .chart-grid-op, .chart-grid-perf { grid-template-columns:1fr; }
  }
  .chart-card { background:var(--bg2); border:1px solid var(--border); border-radius:6px; padding:16px; }
  .chart-card-hdr { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:4px; }
  .chart-card-title { font-size:13px; font-weight:700; color:var(--text); }
  .chart-card-sub { font-size:11px; color:var(--text3); margin-top:3px; line-height:1.4; max-width:260px; }
  .chart-trend-pos { font-size:12px; font-weight:600; color:var(--green); white-space:nowrap; padding-top:2px; }
  .chart-trend-neg { font-size:12px; font-weight:600; color:var(--red); white-space:nowrap; padding-top:2px; }
  .chart-wrap { position:relative; height:220px; margin-top:10px; }
  .chart-na { display:flex; align-items:center; justify-content:center; height:220px; color:var(--text3); font-size:12px; font-style:italic; text-align:center; }
  .chart-hdr { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:12px; padding:4px 0; }
  .chart-hdr h2 { font-size:15px; font-weight:700; flex:1; }
  .chart-sel { padding:5px 10px; background:var(--bg3); border:1px solid var(--border); border-radius:4px; color:var(--text); font-size:12px; cursor:pointer; outline:none; }
  .section-divider { display:flex; align-items:center; gap:10px; margin:8px 0 10px; }
  .section-divider::before,.section-divider::after { content:''; flex:1; height:1px; background:var(--border); }
  .section-divider-label { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.6px; color:var(--text3); white-space:nowrap; }
  @keyframes live-pulse { 0%,100% { opacity:1; } 50% { opacity:.35; } }
  .badge-live { display:inline-flex; align-items:center; gap:4px; font-size:10px; font-weight:700; color:var(--green); animation:live-pulse 2s ease-in-out infinite; padding-top:2px; }
  .badge-live::before { content:'●'; }
  .chart-legend { display:flex; justify-content:center; gap:16px; margin-top:10px; }
  .chart-legend-item { display:flex; align-items:center; gap:5px; font-size:11px; color:var(--text2); }
  .chart-legend-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
  ```

- [ ] **Step 3: Verificar no browser**

  Abrir http://localhost:8765, navegar para a aba Gráficos/Análise. Nenhum erro de CSS no console. O layout dos charts existentes não deve ter quebrado.

- [ ] **Step 4: Commit**

  ```bash
  git add index.html
  git commit -m "style: adicionar CSS para redesign da aba Análise (seções, badge-live, tendências)"
  ```

---

### Task 2: HTML — sidebar + página Análise reestruturada

**Files:**
- Modify: `index.html:348-351` (sidebar item Gráficos)
- Modify: `index.html:503-536` (bloco `#graficos-page`)

**Interfaces:**
- Consome: classes CSS produzidas na Task 1
- Produz: canvas IDs `chart-vol`, `chart-peak`, `chart-status`, `chart-tma`, `chart-agents`; elementos `id="trend-vol"` e `id="trend-tma"` para o JS escrever tendência; remove canvas `chart-tmr` e `chart-fcr`
- `showPage('graficos')` e `fetchChartData()` continuam funcionando — nenhuma mudança em JS nessa task

- [ ] **Step 1: Renomear sidebar item Gráficos → Análise**

  Localizar (linha ~348):
  ```html
    <div class="sidebar-item" id="nav-graficos" onclick="showPage('graficos')" title="Gráficos">
      <span class="sidebar-icon">📈</span>
      <span class="sidebar-label">Gráficos</span>
    </div>
  ```

  Substituir por:
  ```html
    <div class="sidebar-item" id="nav-graficos" onclick="showPage('graficos')" title="Análise">
      <span class="sidebar-icon">📈</span>
      <span class="sidebar-label">Análise</span>
    </div>
  ```

- [ ] **Step 2: Substituir o bloco `#graficos-page` inteiro**

  Localizar (linha ~503):
  ```html
  <!-- GRAFICOS PAGE -->
  <div id="graficos-page" style="display:none;padding:12px 24px;background:var(--bg);min-height:calc(100vh - 56px);margin-left:52px">
    <div class="chart-hdr">
      <h2>Dashboard de Gráficos</h2>
      ...
    </div>
    <div class="chart-grid">
      ...5 chart cards antigos...
    </div>
  </div>
  ```

  Substituir **tudo** entre `<!-- GRAFICOS PAGE -->` e `<!-- TOAST -->` (exclusive) por:

  ```html
  <!-- GRAFICOS PAGE (Análise) -->
  <div id="graficos-page" style="display:none;padding:12px 24px;background:var(--bg);min-height:calc(100vh - 56px);margin-left:52px">
    <div class="chart-hdr">
      <h2>Análise</h2>
      <select id="chart-period-sel" class="chart-sel" onchange="fetchChartData()">
        <option value="3">Últimos 3 meses</option>
        <option value="6" selected>Últimos 6 meses</option>
        <option value="12">Últimos 12 meses</option>
      </select>
      <button id="chart-update-btn" class="btn-hdr blue" onclick="fetchChartData()">↺ Atualizar</button>
    </div>

    <!-- OPERACIONAL -->
    <div class="section-divider"><span class="section-divider-label">Operacional</span></div>
    <div class="chart-grid-op">

      <div class="chart-card">
        <div class="chart-card-hdr">
          <div>
            <div class="chart-card-title">Volume de Atendimentos</div>
            <div class="chart-card-sub">Total de atendimentos iniciados no período</div>
          </div>
          <span id="trend-vol"></span>
        </div>
        <div class="chart-wrap"><canvas id="chart-vol"></canvas></div>
      </div>

      <div class="chart-card">
        <div class="chart-card-hdr">
          <div>
            <div class="chart-card-title">Pico de Horário</div>
            <div class="chart-card-sub">Horários com mais atendimentos em aberto agora</div>
          </div>
          <span class="badge-live">Ao vivo</span>
        </div>
        <div class="chart-wrap"><canvas id="chart-peak"></canvas></div>
      </div>

      <div class="chart-card">
        <div class="chart-card-hdr">
          <div>
            <div class="chart-card-title">Status das Conversas</div>
            <div class="chart-card-sub">Distribuição atual das conversas</div>
          </div>
          <span class="badge-live">Ao vivo</span>
        </div>
        <div class="chart-wrap"><canvas id="chart-status"></canvas></div>
        <div class="chart-legend">
          <span class="chart-legend-item"><span class="chart-legend-dot" style="background:#ef4444"></span>Abertas</span>
          <span class="chart-legend-item"><span class="chart-legend-dot" style="background:#22c55e"></span>Resolvidas</span>
          <span class="chart-legend-item"><span class="chart-legend-dot" style="background:#eab308"></span>Pendentes</span>
        </div>
      </div>

    </div>

    <!-- DESEMPENHO -->
    <div class="section-divider" style="margin-top:16px"><span class="section-divider-label">Desempenho</span></div>
    <div class="chart-grid-perf">

      <div class="chart-card">
        <div class="chart-card-hdr">
          <div>
            <div class="chart-card-title">Tempo Médio de Atendimento</div>
            <div class="chart-card-sub">Quanto tempo em média para resolver um atendimento. Quanto menor, melhor.</div>
          </div>
          <span id="trend-tma"></span>
        </div>
        <div class="chart-wrap"><canvas id="chart-tma"></canvas></div>
      </div>

      <div class="chart-card" style="grid-column:1/-1">
        <div class="chart-card-hdr">
          <div>
            <div class="chart-card-title">Atendimentos por Agente</div>
            <div class="chart-card-sub">Conversas abertas por atendente agora</div>
          </div>
          <span class="badge-live">Ao vivo</span>
        </div>
        <div class="chart-wrap" style="height:280px"><canvas id="chart-agents"></canvas></div>
      </div>

    </div>
  </div>

  ```

- [ ] **Step 3: Verificar sem erro de console**

  Abrir http://localhost:8765. Abrir DevTools → Console. Clicar em "Análise" na sidebar. Verificar:
  - Layout mostra dois separadores ("OPERACIONAL" e "DESEMPENHO")
  - 3 cards na seção Operacional, 2 cards na seção Desempenho
  - Badge "● Ao vivo" pisca nos cards de tempo real
  - Nenhum erro de console

  **Esperado no console:** nenhum erro. Pode haver "cannot read chart-tmr" se o JS ainda tentar — isso será corrigido na Task 3.

- [ ] **Step 4: Commit**

  ```bash
  git add index.html
  git commit -m "feat: reestruturar HTML da aba Análise em seções Operacional/Desempenho"
  ```

---

### Task 3: JS — reescrever `renderCharts()` com os 5 novos gráficos

**Files:**
- Modify: `index.html:1527-1591` (função `renderCharts`)

**Interfaces:**
- Consome: `_chartData[]` (array de objetos `{ label, conversations_count, avg_resolution_time, ... }`), `_rawConvs[]` (array de conversas com `created_at` (Unix timestamp), `status`, `meta.assignee.name`), `chartColors()`, `makeChartOpts(isHoriz, yFmt)`, `destroyChart(id)`, canvas IDs da Task 2 (`chart-vol`, `chart-peak`, `chart-status`, `chart-tma`, `chart-agents`), elements `#trend-vol` e `#trend-tma`
- Produz: `_charts.vol`, `_charts.peak`, `_charts.status`, `_charts.tma`, `_charts.agents`; escreve HTML nos elementos `#trend-vol` e `#trend-tma`

- [ ] **Step 1: Localizar a função `renderCharts` atual**

  Localizar (linha ~1527):
  ```javascript
  function renderCharts() {
    if (!window.Chart || !_chartData.length) return;
    ...
  }
  ```

  A função termina no fechamento de chave antes de `/* ── PAGE NAVIGATION ── */`.

- [ ] **Step 2: Substituir `renderCharts()` inteira pela nova versão**

  Substituir desde `function renderCharts() {` até o `}` de fechamento (antes de `/* ── PAGE NAVIGATION ── */`) por:

  ```javascript
  function renderCharts() {
    if (!window.Chart || !_chartData.length) return;
    const c      = chartColors();
    const labels = _chartData.map(d => d.label);
    const n      = _chartData.length;

    function trendEl(elId, current, previous, invertSign) {
      const el = document.getElementById(elId);
      if (!el) return;
      if (!previous || previous === 0 || current == null) { el.innerHTML = ''; return; }
      const pct      = Math.round(((current - previous) / previous) * 100);
      if (pct === 0) { el.innerHTML = ''; return; }
      const up       = pct > 0;
      const positive = invertSign ? !up : up;
      const cls      = positive ? 'chart-trend-pos' : 'chart-trend-neg';
      el.className   = cls;
      el.textContent = `${up ? '↑' : '↓'} ${Math.abs(pct)}% vs ant.`;
    }

    /* ── Volume de Atendimentos ── */
    destroyChart('vol');
    trendEl('trend-vol',
      _chartData[n - 1]?.conversations_count,
      _chartData[n - 2]?.conversations_count,
      false
    );
    const volOpts = makeChartOpts(false);
    volOpts.animation = false;
    _charts.vol = new Chart(document.getElementById('chart-vol'), {
      type: 'bar',
      data: {
        labels,
        datasets: [{ data: _chartData.map(d => d.conversations_count || 0), backgroundColor: '#3b82f6', borderRadius: 3 }]
      },
      options: volOpts
    });

    /* ── Pico de Horário ── */
    destroyChart('peak');
    const hourBuckets = new Array(24).fill(0);
    _rawConvs.forEach(cv => {
      if (!cv.created_at) return;
      const h = new Date(cv.created_at * 1000).getHours();
      hourBuckets[h]++;
    });
    const peakIdx  = hourBuckets.indexOf(Math.max(...hourBuckets));
    const peakOpts = makeChartOpts(false);
    peakOpts.animation = false;
    peakOpts.plugins.tooltip.callbacks = {
      title: items => `${items[0].label}`,
      label: item  => `${item.raw} atendimento${item.raw !== 1 ? 's' : ''}`
    };
    _charts.peak = new Chart(document.getElementById('chart-peak'), {
      type: 'bar',
      data: {
        labels: Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}h`),
        datasets: [{
          data: hourBuckets,
          backgroundColor: hourBuckets.map((_, i) => i === peakIdx ? '#f97316' : 'rgba(249,115,22,0.4)'),
          borderRadius: 3
        }]
      },
      options: peakOpts
    });

    /* ── Status das Conversas ── */
    destroyChart('status');
    const sc = { open: 0, resolved: 0, pending: 0 };
    _rawConvs.forEach(cv => { if (cv.status in sc) sc[cv.status]++; });
    _charts.status = new Chart(document.getElementById('chart-status'), {
      type: 'doughnut',
      data: {
        labels: ['Abertas', 'Resolvidas', 'Pendentes'],
        datasets: [{
          data: [sc.open, sc.resolved, sc.pending],
          backgroundColor: ['#ef4444', '#22c55e', '#eab308'],
          borderWidth: 2,
          borderColor: c.tooltipBg
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: '65%',
        plugins: {
          legend: { display: false },
          tooltip: { backgroundColor: c.tooltipBg, titleColor: c.labels, bodyColor: c.labels, borderColor: c.grid, borderWidth: 1 }
        }
      }
    });

    /* ── Tempo Médio de Atendimento ── */
    destroyChart('tma');
    trendEl('trend-tma',
      _chartData[n - 1]?.avg_resolution_time,
      _chartData[n - 2]?.avg_resolution_time,
      true
    );
    const tmaOpts = makeChartOpts(false, v => {
      const h = Math.floor(v), m = Math.round((v - h) * 60);
      return `${h}hr ${String(m).padStart(2, '0')}min`;
    });
    tmaOpts.animation = false;
    _charts.tma = new Chart(document.getElementById('chart-tma'), {
      type: 'line',
      data: {
        labels,
        datasets: [{
          data: _chartData.map(d => d.avg_resolution_time != null ? +(d.avg_resolution_time / 3600).toFixed(2) : null),
          borderColor: '#8b5cf6', backgroundColor: 'rgba(139,92,246,0.08)',
          pointBackgroundColor: '#8b5cf6', tension: 0.3, fill: true, spanGaps: true
        }]
      },
      options: tmaOpts
    });

    /* ── Atendimentos por Agente ── */
    destroyChart('agents');
    const agCounts = {};
    _rawConvs.forEach(cv => { const nm = cv.meta?.assignee?.name; if (nm) agCounts[nm] = (agCounts[nm] || 0) + 1; });
    const agSorted = Object.entries(agCounts).sort((a, b) => b[1] - a[1]).slice(0, 15);
    const agOpts   = makeChartOpts(true);
    agOpts.animation = false;
    agOpts.scales.y.ticks.font = { size: 11 };
    _charts.agents = new Chart(document.getElementById('chart-agents'), {
      type: 'bar',
      data: {
        labels: agSorted.map(([nm]) => nm.length > 22 ? nm.slice(0, 20) + '…' : nm),
        datasets: [{ data: agSorted.map(([, v]) => v), backgroundColor: '#14b8a6', borderRadius: 3 }]
      },
      options: agOpts
    });
  }
  ```

- [ ] **Step 3: Verificar no browser — caminho feliz**

  1. Abrir http://localhost:8765
  2. Configurar token (se necessário)
  3. Clicar em "Análise" na sidebar
  4. Verificar cada gráfico:
     - **Volume:** barras azuis com labels de mês no eixo X; `#trend-vol` mostra `↑ N%` ou `↓ N%` (ou vazio se só 1 mês)
     - **Pico de Horário:** barras laranjas por hora; a barra do pico é mais escura
     - **Status:** donut com 3 cores; legenda embaixo visível
     - **Tempo Médio:** linha roxa; subtítulo "Quanto menor, melhor" visível
     - **Agentes:** barras horizontais teal
  5. Clicar em "↺ Atualizar" — gráficos recarregam sem duplicar
  6. Alternar tema claro/escuro — gráficos atualizam cores

- [ ] **Step 4: Verificar no console — sem erros**

  DevTools → Console. Nenhum erro de `Cannot read properties of null` ou `chart-tmr` / `chart-fcr`. Se aparecer algum, procurar referências residuais a esses IDs no arquivo e remover.

- [ ] **Step 5: Commit final**

  ```bash
  git add index.html
  git commit -m "feat: reescrever renderCharts() com Volume, Pico, Status, TMA e Agente + tendências"
  ```

---

## Self-Review

**Cobertura da spec:**

| Requisito | Task |
|-----------|------|
| Renomear sidebar "Gráficos" → "Análise" | Task 2, Step 1 |
| Separadores Operacional / Desempenho | Task 1 (CSS) + Task 2 (HTML) |
| Volume com tendência ↑↓ | Task 2 (HTML: `#trend-vol`) + Task 3 (JS) |
| Pico de Horário (novo, `_rawConvs`) | Task 2 (canvas) + Task 3 (JS) |
| Status donut (novo, `_rawConvs`) | Task 2 (canvas + legenda) + Task 3 (JS) |
| TMA roxo com tendência invertida | Task 2 (HTML: `#trend-tma`) + Task 3 (JS) |
| Agente teal, full-width | Task 2 (HTML: `grid-column:1/-1`) + Task 3 (JS) |
| Remover TMR e FCR | Task 2 (HTML) + Task 3 (JS não referencia mais) |
| Badge "Ao vivo" verde pulsante (`.badge-live`) | Task 1 (CSS) + Task 2 (HTML) |
| Grid 3 colunas Operacional / 2 colunas Desempenho | Task 1 (CSS: `.chart-grid-op`, `.chart-grid-perf`) |
| Responsivo 1 coluna < 900px | Task 1 (CSS: `@media`) |
| Cores por gráfico diferentes | Task 3 (azul/laranja/verde-vermelho-amarelo/roxo/teal) |
| Subtítulo explicativo em cada card | Task 2 (HTML: `.chart-card-sub`) |
| Suporte tema claro/escuro | Task 3 (`chartColors()` já existente, reutilizado) |

**Placeholder scan:** Nenhum TBD, TODO ou "implementar depois" encontrado.

**Consistência de nomes:**
- `destroyChart('peak')` → `_charts.peak` ✓
- `destroyChart('status')` → `_charts.status` ✓
- `destroyChart('vol')` → `_charts.vol` ✓
- `destroyChart('tma')` → `_charts.tma` ✓
- `destroyChart('agents')` → `_charts.agents` ✓
- Canvas IDs no HTML batem com `document.getElementById(...)` no JS ✓
- `#trend-vol` e `#trend-tma` presentes no HTML e referenciados em `trendEl()` ✓
