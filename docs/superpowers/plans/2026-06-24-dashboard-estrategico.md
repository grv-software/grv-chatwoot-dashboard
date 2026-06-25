# Dashboard Estratégico v2 + Sidebar Colapsável — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesenhar o dashboard de Projetos GRV em 3 zonas de decisão estratégica (saúde, problemas, metas) com visual SAC-level e sidebar colapsável.

**Architecture:** Single-file SPA `grv-cs-jornada.html` — CSS + JS inline, sem build step. Chart.js v4 já presente via CDN. Todas as funções de cálculo base já existem (verificado). O `renderDashboardProjetos` é substituído por 3 funções `renderZona1/2/3`. `animateKpis` deixa de ser chamado (hero numbers são estáticos).

**Tech Stack:** HTML/CSS/JS vanilla, Chart.js v4 CDN (`https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js`), localStorage.

## Global Constraints

- Arquivo único: `grv-cs-jornada.html` — nunca criar arquivos separados
- Chart.js v4: plugins globais via `Chart.register(plugin)` antes de criar qualquer chart
- Gradiente em barras: `ctx.createLinearGradient` — NÃO usar em doughnut (não suportado v4)
- Linha de meta em doughnut/gauge: SOMENTE via plugin `afterDraw` — não usar dataset tipo `'line'`
- Linha de meta em bar chart: dataset extra tipo `'line'` com `borderDash: [4,4]`
- Trend "vs mês ant.": dado ilustrativo — badge deve ter `title="Estimativa ilustrativa — não é dado real"` e exibir ★
- Sidebar colapsada: 56px, expandida: 240px, transição `width 0.2s ease`
- `_dashCharts` global destruído no início de cada `renderDashboardProjetos` (já existe)
- Não alterar: Lista, Kanban, Minha Carteira, Detalhe do Cliente, Criar Playbook, seed data

---

## Arquivo modificado

`grv-cs-jornada.html` (~2185 linhas na branch `alteracoes`)

Seções que mudam:
- CSS (linhas ~32–140): adicionar `.sidebar--collapsed`, hero CSS, zone CSS, chart plugin CSS
- HTML sidebar (linhas ~305–325): adicionar botão `☰`
- JS funções (linhas ~940–1302): adicionar helpers, renderZona1/2/3, modificar chartConfigs e initCharts
- JS `renderProjetosGRV` (linhas ~1700+): remover `animateKpis`, atualizar chamada

---

## Task 1: Sidebar Colapsável

**Files:**
- Modify: `grv-cs-jornada.html` — CSS sidebar, HTML sidebar, JS toggle

**Interfaces:**
- Produces: `toggleSidebar()` global, class `.sidebar--collapsed` no `<aside>`

- [ ] **Step 1: Adicionar CSS da sidebar colapsável**

Localizar a regra `.nav-icon{...}` (linha ~46) e adicionar logo após:

```css
.sb-toggle{width:100%;background:none;border:none;text-align:left;padding:10px 16px;cursor:pointer;font-size:18px;color:var(--text3);display:block;border-bottom:1px solid var(--border);line-height:1}
.sb-toggle:hover{color:var(--primary)}
.sidebar{transition:width 0.2s ease}
.sidebar--collapsed{width:56px;overflow:hidden}
.sidebar--collapsed .sb-logo-text{display:none}
.sidebar--collapsed .sb-section{display:none}
.sidebar--collapsed .nav-item .nav-label{display:none}
.sidebar--collapsed .nav-item{justify-content:center;padding:10px 0}
.sidebar--collapsed .sb-toggle{text-align:center;padding:10px 0}
```

- [ ] **Step 2: Envolver texto das nav-items com `.nav-label`**

Localizar o HTML das nav-items (linha ~315) e adicionar classe `nav-label` ao texto:

```html
<nav class="sb-nav">
  <a class="nav-item" data-route="projetos" href="#projetos" title="Projetos GRV">
    <span class="nav-icon">🌐</span><span class="nav-label"> Projetos GRV</span>
  </a>
  <a class="nav-item" data-route="carteira" href="#carteira" title="Minha Carteira">
    <span class="nav-icon">📋</span><span class="nav-label"> Minha Carteira</span>
  </a>
  <a class="nav-item" data-route="criar" href="#criar" title="Criar Playbook">
    <span class="nav-icon">➕</span><span class="nav-label"> Criar Playbook</span>
  </a>
</nav>
```

- [ ] **Step 3: Adicionar botão toggle no topo da sidebar**

Localizar `<aside class="sidebar">` (linha ~305) e adicionar o botão como primeiro filho:

```html
<aside class="sidebar" id="main-sidebar">
  <button class="sb-toggle" onclick="toggleSidebar()" title="Recolher/Expandir menu">☰</button>
  <div class="sb-logo">
```

- [ ] **Step 4: Adicionar função `toggleSidebar` e init no load**

Localizar a função `initConsultorSel` (linha ~1261) e adicionar antes dela:

```javascript
function toggleSidebar() {
  const aside = document.getElementById('main-sidebar');
  const collapsed = aside.classList.toggle('sidebar--collapsed');
  localStorage.setItem('grv_cs_sidebar_collapsed', collapsed ? '1' : '');
}
```

Localizar o bloco de inicialização no fim do JS (próximo a `initConsultorSel()` ou `window.addEventListener`) e adicionar:

```javascript
if (localStorage.getItem('grv_cs_sidebar_collapsed')) {
  const aside = document.getElementById('main-sidebar');
  if (aside) aside.classList.add('sidebar--collapsed');
}
```

- [ ] **Step 5: Verificar no browser**

Abrir `grv-cs-jornada.html#projetos`. Verificar:
- Botão `☰` visível no topo da sidebar
- Clicar colapsa para 56px com só ícones visíveis
- Clicar novamente expande para 240px com labels
- Recarregar página — estado persiste (localStorage)
- Conteúdo principal se expande para ocupar espaço liberado

- [ ] **Step 6: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(sidebar): colapsar/expandir com ícones e persistência localStorage"
```

---

## Task 2: CSS Visual SAC-Level + Plugins Chart.js Globais

**Files:**
- Modify: `grv-cs-jornada.html` — CSS classes novas, plugins Chart.js registrados

**Interfaces:**
- Produces: classes `.health-banner`, `.hero-row`, `.hero-metrics`, `.hero-card`, `.hero-value`, `.hero-trend`, `.dash-zone`, `.dash-zone-title`, `.chart-headline`, `.chart-subline`, `.alerts-compact`, `.alert-compact`
- Produces: plugins `donutCenterPlugin`, `barGradientPlugin` registrados globalmente via `Chart.register()`

- [ ] **Step 1: Adicionar CSS de tipografia hero e zonas**

Localizar o bloco `/* ── DASHBOARD */` (linha ~102) e adicionar após as regras `.dash-card-title`:

```css
/* ── DASHBOARD ESTRATÉGICO v2 ───────────────────────── */
.health-banner{padding:16px 20px;border-radius:var(--radius);border-left:5px solid;margin-bottom:20px;display:flex;align-items:center;gap:12px;font-size:14px;font-weight:600;line-height:1.4}
.hero-row{display:grid;grid-template-columns:2fr 1fr;gap:16px;margin-bottom:0}
.hero-metrics{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}
.hero-card{background:var(--surface);border-radius:var(--radius);padding:24px 20px;box-shadow:var(--shadow);border:1px solid var(--border)}
.hero-label{font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;font-weight:700}
.hero-value{font-size:52px;font-weight:800;line-height:1;letter-spacing:-1px}
.hero-sub{font-size:13px;color:var(--text3);margin-top:6px}
.hero-trend{font-size:12px;font-weight:600;margin-top:8px}
.hero-trend-up{color:#e53e3e}
.hero-trend-down{color:#38a169}
.hero-trend-neutral{color:var(--text3)}
.dash-zone{margin-bottom:32px}
.dash-zone-title{font-size:11px;font-weight:700;color:var(--text3);text-transform:uppercase;letter-spacing:.1em;padding-bottom:12px;border-bottom:2px solid var(--border);margin-bottom:20px}
.chart-headline{font-size:14px;font-weight:700;color:var(--text);margin-bottom:4px;line-height:1.3}
.chart-subline{font-size:12px;color:var(--text3);margin-bottom:16px}
.alerts-compact{display:flex;flex-direction:column;gap:8px}
.alert-compact{padding:10px 12px;border-radius:var(--radius);border-left:3px solid;display:flex;align-items:flex-start;gap:8px;font-size:12px}
.alert-compact-title{font-weight:600;color:var(--text);line-height:1.3}
.alert-compact-acao{color:var(--text3);margin-top:2px;font-size:11px}
@media(max-width:1100px){.hero-metrics{grid-template-columns:1fr 1fr}.hero-row{grid-template-columns:1fr}}
@media(max-width:800px){.hero-metrics{grid-template-columns:1fr}}
```

- [ ] **Step 2: Registrar plugins Chart.js globais**

Localizar o bloco após `<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>` e antes de `<style>`, ou logo após o CDN, adicionar uma tag `<script>` inline com os plugins globais. **Deve vir depois do CDN e antes de qualquer uso de `Chart`.**

Localizar o comentário `// ═══ DADOS / SEED` ou o primeiro `const SEED_CONSULTORES` (linha ~370) e adicionar ANTES dele:

```javascript
// ── CHART.JS PLUGINS GLOBAIS ──────────────────────────
Chart.register({
  id: 'donutCenter',
  afterDraw(chart) {
    if (chart.config.type !== 'doughnut') return;
    if (!chart.config.options._showCenter) return;
    const {ctx, chartArea} = chart;
    if (!chartArea) return;
    const cx = (chartArea.left + chartArea.right) / 2;
    const cy = (chartArea.top  + chartArea.bottom) / 2;
    const total = chart.config.data.datasets[0].data.reduce((a,b)=>a+b,0);
    ctx.save();
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillStyle = '#1a202c'; ctx.font = '800 28px Segoe UI,sans-serif';
    ctx.fillText(total, cx, cy - 8);
    ctx.fillStyle = '#718096'; ctx.font = '400 11px Segoe UI,sans-serif';
    ctx.fillText('projetos', cx, cy + 14);
    ctx.restore();
  }
});

Chart.register({
  id: 'barGradient',
  beforeDatasetsDraw(chart) {
    if (chart.config.type !== 'bar') return;
    const {ctx, chartArea} = chart;
    if (!chartArea) return;
    chart.data.datasets.forEach(ds => {
      if (!ds._gradColor) return;
      const grad = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
      grad.addColorStop(0, ds._gradColor);
      grad.addColorStop(1, ds._gradColor + '55');
      ds.backgroundColor = grad;
    });
  }
});
```

- [ ] **Step 3: Verificar no browser (console)**

Abrir DevTools → Console. Digitar:
```javascript
Chart.registry.plugins.get('donutCenter')  // deve retornar o plugin
Chart.registry.plugins.get('barGradient')  // deve retornar o plugin
```
Ambos devem retornar objetos, não `undefined`.

- [ ] **Step 4: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(dash-v2): CSS hero/zones + plugins Chart.js donutCenter e barGradient"
```

---

## Task 3: Funções Auxiliares Puras

**Files:**
- Modify: `grv-cs-jornada.html` — adicionar funções após `computeAlertas` (linha ~1141)

**Interfaces:**
- Consumes: `computeDashboardKPIs`, `computeAlertas`, `computePerformance`, `getStatusDash` (todas existentes)
- Produces:
  - `simulateTrend(value: number, seed: number): {delta: number, dir: 'up'|'down'}`
  - `renderTrendBadge(delta: number, dir: string, invertido: boolean): string`
  - `computeSaudePortfolio(kpis: object): {nivel, cor, bg, icone, frase}`
  - `computeNarrativaDonut(kpis: object, clientes: array): string`
  - `computeNarrativaConsultor(data: array): string`
  - `computeNarrativaBarras(clientes: array): string`

- [ ] **Step 1: Adicionar as 6 funções auxiliares**

Localizar `function renderAlertas` (linha ~1145) e adicionar ANTES dela:

```javascript
// ── FUNÇÕES AUXILIARES DASHBOARD v2 ──────────────────
function simulateTrend(value, seed) {
  const delta = Math.round(Math.abs(Math.sin(seed * 7.3) * 0.12 * value));
  const dir   = Math.sin(seed * 3.7) > 0 ? 'up' : 'down';
  return {delta, dir};
}

function renderTrendBadge(delta, dir, invertido) {
  if (!delta) return '';
  // invertido=true: 'up' é ruim (ex: atrasados aumentaram)
  const melhorou = invertido ? dir === 'down' : dir === 'up';
  const seta = dir === 'up' ? '▲' : '▼';
  const cls  = melhorou ? 'hero-trend-down' : 'hero-trend-up';
  return `<div class="hero-trend ${cls}" title="Estimativa ilustrativa — não é dado real">${seta} ${delta} vs mês ant. ★</div>`;
}

function computeSaudePortfolio(kpis) {
  const pct   = kpis.total ? Math.round(kpis.atrasado / kpis.total * 100) : 0;
  const ativos = kpis.total - kpis.cancelado;
  if (pct < 10) return {nivel:'ok', cor:'#38a169', bg:'#F0FFF4', icone:'✅',
    frase: `Portfólio saudável — ${ativos} projetos ativos, tudo dentro do esperado`};
  if (pct <= 20) return {nivel:'atencao', cor:'#d69e2e', bg:'#FFFFF0', icone:'⚠️',
    frase: `Atenção — ${pct}% do portfólio precisa de acompanhamento (${kpis.atrasado} projetos atrasados)`};
  return {nivel:'risco', cor:'#e53e3e', bg:'#FFF5F5', icone:'🚨',
    frase: `Portfólio em risco — ${pct}% atrasados, acima do limite saudável de 20%`};
}

function computeNarrativaDonut(kpis, clientes) {
  if (!kpis.atrasado) return `Nenhum atraso no portfólio — ${kpis.emAndamento} projetos em andamento saudável`;
  const contagem = {};
  clientes.filter(c => getStatusDash(c) === 'Atrasado').forEach(c => {
    const p = c.produto.split('/')[0];
    contagem[p] = (contagem[p] || 0) + 1;
  });
  const top = Object.entries(contagem).sort((a,b) => b[1]-a[1])[0];
  if (top && top[1] / kpis.atrasado >= 0.5) {
    const pct = Math.round(top[1] / kpis.atrasado * 100);
    return `${top[0]} concentra ${pct}% dos atrasos — ${top[1]} dos ${kpis.atrasado} projetos atrasados são ${top[0]}`;
  }
  return `Atrasos distribuídos entre os produtos — ${kpis.atrasado} projetos precisam de atenção`;
}

function computeNarrativaConsultor(data) {
  if (!data.length) return 'Nenhum consultor com dados disponíveis';
  const pior = data[0]; // computePerformance já ordena por pctAtrasado desc
  if (pior.pctAtrasado > 25)
    return `${pior.nome.split(' ')[0]} concentra a maior carga de atrasos — ${pior.pctAtrasado}% da carteira está atrasada`;
  return 'Equipe dentro do esperado — nenhum consultor com concentração crítica de atrasos';
}

function computeNarrativaBarras(clientes) {
  const produtos = [...new Set(clientes.map(c => c.produto.split('/')[0]))].filter(Boolean);
  if (produtos.length < 2) return 'Distribuição de status por produto';
  const taxas = produtos.map(p => {
    const sub  = clientes.filter(c => c.produto.split('/')[0] === p);
    const conc = sub.filter(c => getStatusDash(c) === 'Concluído').length;
    return {p, taxa: sub.length ? Math.round(conc / sub.length * 100) : 0};
  }).sort((a,b) => b.taxa - a.taxa);
  const melhor = taxas[0], pior = taxas[taxas.length - 1];
  if (melhor.taxa > 0 && pior.taxa < melhor.taxa) {
    const mult = pior.taxa > 0 ? Math.round(melhor.taxa / pior.taxa) : '∞';
    return `${melhor.p} tem taxa de conclusão ${mult}× maior que ${pior.p} neste período`;
  }
  return 'Comparativo de status entre produtos';
}
```

- [ ] **Step 2: Verificar no console do browser**

```javascript
// Abrir o arquivo no browser, abrir DevTools → Console
const kpis = computeDashboardKPIs(getClientes())
const saude = computeSaudePortfolio(kpis)
console.log(saude.nivel)        // deve ser 'risco' (10 atrasados em 38 = 26%)
console.log(saude.frase)        // "Portfólio em risco — 26% atrasados..."

const t = simulateTrend(10, 2)
console.log(t.delta > 0)        // true
console.log(t.dir === 'up' || t.dir === 'down')  // true

const clientes = getClientes()
const narrativa = computeNarrativaDonut(kpis, clientes)
console.log(narrativa.includes('CPS'))  // deve ser true (CPS domina os atrasos)

const perf = computePerformance(clientes, getConsultores())
const nc = computeNarrativaConsultor(perf)
console.log(nc.length > 0)  // true
```

- [ ] **Step 3: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(dash-v2): funções auxiliares simulateTrend, computeSaudePortfolio, narrativas"
```

---

## Task 4: Zona 1 — "Está tudo bem?"

**Files:**
- Modify: `grv-cs-jornada.html` — adicionar `renderZona1`, atualizar `renderDashboardProjetos`

**Interfaces:**
- Consumes: `computeSaudePortfolio`, `simulateTrend`, `renderTrendBadge`, `computeAlertas` (Tasks 2–3)
- Produces: `renderZona1(kpis, clientes, consultores): string`

- [ ] **Step 1: Adicionar `renderZona1`**

Localizar `function renderDashboardProjetos` (linha ~1205) e adicionar ANTES dela:

```javascript
function renderZona1(kpis, clientes, consultores) {
  const saude  = computeSaudePortfolio(kpis);
  const ativos = kpis.total - kpis.cancelado;
  const pctAtr = kpis.total ? Math.round(kpis.atrasado / kpis.total * 100) : 0;
  const t1 = simulateTrend(ativos,        1);
  const t2 = simulateTrend(kpis.atrasado, 2);
  const t3 = simulateTrend(kpis.concluido,3);

  const alertas    = computeAlertas(kpis, clientes).slice(0, 3);
  const alertasHTML = alertas.length
    ? alertas.map(a => `
        <div class="alert-compact" style="background:${a.sev==='critico'?'#FFF5F5':'#FFFFF0'};border-color:${a.sev==='critico'?'#e53e3e':'#d69e2e'}">
          <span style="font-size:14px">${a.sev==='critico'?'🚨':'⚠️'}</span>
          <div>
            <div class="alert-compact-title">${a.titulo}</div>
            <div class="alert-compact-acao">${a.acao}</div>
          </div>
        </div>`).join('')
      + `<a href="#dash-zona2" style="font-size:12px;color:var(--primary);text-decoration:none;font-weight:600;margin-top:4px;display:block">Ver todos os alertas ↓</a>`
    : `<div class="alert-compact" style="background:#F0FFF4;border-color:#38a169">
        <span style="font-size:14px">✅</span>
        <div class="alert-compact-title">Sem alertas críticos no momento</div>
       </div>`;

  return `
    <div class="dash-zone">
      <div class="health-banner" style="background:${saude.bg};border-color:${saude.cor}">
        <span style="font-size:22px">${saude.icone}</span>
        <span style="color:${saude.cor}">${saude.frase}</span>
      </div>
      <div class="hero-row">
        <div class="hero-metrics">
          <div class="hero-card">
            <div class="hero-label">Projetos Ativos</div>
            <div class="hero-value" style="color:var(--text)">${ativos}</div>
            ${renderTrendBadge(t1.delta, t1.dir, false)}
          </div>
          <div class="hero-card">
            <div class="hero-label">Atrasados</div>
            <div class="hero-value" style="color:#e53e3e">${kpis.atrasado}</div>
            <div class="hero-sub">${pctAtr}% do portfólio</div>
            ${renderTrendBadge(t2.delta, t2.dir, true)}
          </div>
          <div class="hero-card">
            <div class="hero-label">Concluídos</div>
            <div class="hero-value" style="color:#38a169">${kpis.concluido}</div>
            ${renderTrendBadge(t3.delta, t3.dir, false)}
          </div>
        </div>
        <div class="dash-card">
          <div class="dash-card-title">Alertas Críticos</div>
          <div class="alerts-compact" style="margin-top:12px">${alertasHTML}</div>
        </div>
      </div>
    </div>`;
}
```

- [ ] **Step 2: Atualizar `renderDashboardProjetos` para chamar `renderZona1`**

Substituir o conteúdo de `renderDashboardProjetos` (da linha `const kpis = computeDashboardKPIs` até o fechamento da template string):

```javascript
function renderDashboardProjetos(clientes, consultores) {
  Object.values(_dashCharts).forEach(ch => { try{ ch.destroy(); }catch(e){} });
  _dashCharts = {};

  if (clientes.length === 0) {
    return `<div class="dash-filter-bar">
      <select onchange="setProjConsultor(this.value)">
        <option value="">Todos consultores</option>
        ${consultores.map(c => `<option value="${c.id}"${c.id===_proj_consultor?' selected':''}>${c.nome}</option>`).join('')}
      </select>
    </div>
    <div class="empty-state"><div class="es-icon">📊</div><div class="es-text">Nenhum projeto encontrado para este consultor.</div></div>`;
  }

  const kpis = computeDashboardKPIs(clientes);
  return `
    <div class="dash-filter-bar">
      <select onchange="setProjConsultor(this.value)">
        <option value="">Todos consultores</option>
        ${consultores.map(c => `<option value="${c.id}"${c.id===_proj_consultor?' selected':''}>${c.nome}</option>`).join('')}
      </select>
    </div>
    ${renderZona1(kpis, clientes, consultores)}
    <div id="dash-zona2-placeholder"></div>
    <div id="dash-zona3-placeholder"></div>`;
}
```

- [ ] **Step 3: Remover `animateKpis` da chamada em `renderProjetosGRV`**

Localizar no bloco do dashboard em `renderProjetosGRV`:
```javascript
animateKpis(dashKpis);
```
Remover essa linha. (Os hero numbers são agora estáticos — não há mais countUp.)

- [ ] **Step 4: Verificar no browser**

Abrir `grv-cs-jornada.html#projetos`. Verificar:
- Banner de saúde vermelho visível no topo (26% atrasados)
- 3 hero cards: "37 Ativos", "10 Atrasados" em vermelho, "3 Concluídos" em verde
- Trend badges com ★ e título "Estimativa ilustrativa"
- Card de alertas compactos ao lado direito com top 3 alertas
- Link "Ver todos os alertas ↓" presente

- [ ] **Step 5: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(dash-v2): Zona 1 — banner saúde, hero metrics com trend, alertas compactos"
```

---

## Task 5: Zona 2 — "Onde estão os problemas?" + Charts Donut e Consultor

**Files:**
- Modify: `grv-cs-jornada.html` — `renderZona2`, `chartDonutConfig`, `chartConsulConfig`, `initCharts`

**Interfaces:**
- Consumes: `computeNarrativaDonut`, `computeNarrativaConsultor`, `computePerformance`, `renderTabelaConsultores`, `renderAlertas`, `computeAlertas` (Tasks 2–3 + existentes)
- Produces: `renderZona2(kpis, clientes, consultores): string`; `_dashCharts.donut`, `_dashCharts.consul` inicializados

- [ ] **Step 1: Adicionar `renderZona2`**

Adicionar logo após `renderZona1`:

```javascript
function renderZona2(kpis, clientes, consultores) {
  const perf = computePerformance(clientes, consultores);
  return `
    <div class="dash-zone" id="dash-zona2">
      <div class="dash-zone-title">Onde estão os problemas?</div>
      <div class="dash-chart-row">
        <div class="dash-card">
          <div class="chart-headline">${computeNarrativaDonut(kpis, clientes)}</div>
          <div class="chart-subline">Distribuição de todos os ${kpis.total} projetos por status atual</div>
          <div style="height:280px;display:flex;align-items:center;justify-content:center">
            <canvas id="ch-donut" style="max-height:280px"></canvas>
          </div>
        </div>
        <div class="dash-card">
          <div class="chart-headline">${computeNarrativaConsultor(perf)}</div>
          <div class="chart-subline">Projetos por consultor — empilhado por status · vermelho = acima de 30% atrasados</div>
          <div style="height:${Math.max(180, perf.length * 36)}px;margin-top:12px">
            <canvas id="ch-consul"></canvas>
          </div>
          ${renderTabelaConsultores(perf)}
        </div>
      </div>
      <div class="dash-card" style="margin-top:16px">
        <div class="dash-card-title">Todos os Alertas Operacionais</div>
        <div style="margin-top:12px;display:flex;flex-direction:column;gap:8px">
          ${renderAlertas(computeAlertas(kpis, clientes))}
        </div>
      </div>
    </div>`;
}
```

- [ ] **Step 2: Atualizar `chartDonutConfig` — label central via plugin `afterDraw`**

Localizar `function chartDonutConfig` e substituir:

```javascript
function chartDonutConfig(kpis) {
  return {
    type: 'doughnut',
    data: {
      labels: ['Concluídos','Em Andamento','Atrasados','Pausados','Não Iniciado','Cancelados'],
      datasets: [{
        data: [kpis.concluido, kpis.emAndamento, kpis.atrasado, kpis.pausado, kpis.naoIniciado, kpis.cancelado],
        backgroundColor: ['#38a169','#3182ce','#e53e3e','#d69e2e','#718096','#4a5568'],
        borderWidth: 2, borderColor: '#fff', hoverOffset: 6,
      }]
    },
    options: {
      cutout: '65%',
      _showCenter: true,  // sinaliza ao plugin donutCenter para desenhar o label
      plugins: {
        legend: { position:'right', labels:{ boxWidth:12, padding:14, font:{size:12},
          generateLabels(chart) {
            const data = chart.data;
            const total = data.datasets[0].data.reduce((a,b)=>a+b,0);
            return data.labels.map((label, i) => ({
              text: `${label} (${total ? Math.round(data.datasets[0].data[i]/total*100) : 0}%)`,
              fillStyle: data.datasets[0].backgroundColor[i],
              index: i,
            }));
          }
        }},
        tooltip: { callbacks: { label: ctx => {
          const total = ctx.dataset.data.reduce((a,b)=>a+b,0);
          const pct   = total ? Math.round(ctx.parsed / total * 100) : 0;
          return ` ${ctx.label}: ${ctx.parsed} (${pct}%)`;
        }}}
      },
      animation: { duration:500 }
    }
  };
}
```

- [ ] **Step 3: Atualizar `chartConsulConfig` — label vermelho via `ticks.color` callback**

Localizar `function chartConsulConfig` e substituir:

```javascript
function chartConsulConfig(data) {
  return {
    type: 'bar',
    data: {
      labels: data.map(d => d.nome.split(' ')[0]),
      datasets: [
        {label:'Em Andamento', data:data.map(d=>d.andamento), backgroundColor:'#3182ce', stack:'s'},
        {label:'Atrasados',    data:data.map(d=>d.atrasado),  backgroundColor:'#e53e3e', stack:'s'},
        {label:'Pausados',     data:data.map(d=>d.pausado),   backgroundColor:'#d69e2e', stack:'s'},
        {label:'Concluídos',   data:data.map(d=>d.concluido), backgroundColor:'#38a169', stack:'s'},
      ]
    },
    options: {
      indexAxis: 'y',
      plugins:{ legend:{ position:'bottom', labels:{ boxWidth:12, font:{size:12} } } },
      scales:{
        x:{ stacked:true, grid:{color:'#edf2f7'}, ticks:{stepSize:1} },
        y:{ stacked:true, grid:{display:false},
          ticks:{
            color: ctx => data[ctx.index] && data[ctx.index].pctAtrasado > 30 ? '#e53e3e' : '#718096',
            font:  ctx => data[ctx.index] && data[ctx.index].pctAtrasado > 30 ? {weight:'bold',size:12} : {size:12}
          }
        }
      },
      animation:{ duration:500 }
    }
  };
}
```

- [ ] **Step 4: Atualizar `initCharts` — incluir donut e consul da Zona 2**

Localizar `function initCharts` e substituir:

```javascript
function initCharts(kpis, clientes, consultores) {
  const get  = id => document.getElementById(id);
  const perf = computePerformance(clientes, consultores);
  if (get('ch-donut'))     _dashCharts.donut    = new Chart(get('ch-donut'),    chartDonutConfig(kpis));
  if (get('ch-consul'))    _dashCharts.consul   = new Chart(get('ch-consul'),   chartConsulConfig(perf));
  if (get('ch-gauge-cps')) _dashCharts.gaugeCPS = new Chart(get('ch-gauge-cps'),chartGaugeConfig(computeAtivacao(clientes,'CPS').pct));
  if (get('ch-gauge-nx'))  _dashCharts.gaugeNX  = new Chart(get('ch-gauge-nx'), chartGaugeConfig(computeAtivacao(clientes,'NX').pct));
  if (get('ch-barras'))    _dashCharts.barras   = new Chart(get('ch-barras'),   chartBarrasConfig(clientes));
}
```

- [ ] **Step 5: Atualizar `renderDashboardProjetos` para incluir Zona 2**

Localizar o placeholder `<div id="dash-zona2-placeholder"></div>` (adicionado na Task 4) e substituir a linha do placeholder por `${renderZona2(kpis, clientes, consultores)}`:

```javascript
  return `
    <div class="dash-filter-bar">
      ...
    </div>
    ${renderZona1(kpis, clientes, consultores)}
    ${renderZona2(kpis, clientes, consultores)}
    <div id="dash-zona3-placeholder"></div>`;
```

- [ ] **Step 6: Verificar no browser**

Abrir `#projetos`. Verificar:
- Seção "ONDE ESTÃO OS PROBLEMAS?" com título ALL CAPS
- Manchete do donut: "CPS concentra X% dos atrasos..."
- Donut com label central "38 projetos" desenhado via plugin (não via div absoluto)
- Legenda do donut com percentuais
- Chart de consultor com barras empilhadas
- Consultores com > 30% atrasados têm label vermelho e bold no eixo Y
- Manchete do consultor com nome do pior
- Tabela ordenável abaixo do chart
- Todos os alertas visíveis abaixo

- [ ] **Step 7: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(dash-v2): Zona 2 — manchetes narrativas, donut label via plugin, consultor labels vermelhos"
```

---

## Task 6: Zona 3 + Integração Final + Cleanup

**Files:**
- Modify: `grv-cs-jornada.html` — `renderZona3`, `chartGaugeConfig`, `chartBarrasConfig`, `renderDashboardProjetos` final

**Interfaces:**
- Consumes: `computeNarrativaBarras`, `computeAtivacao`, `computeBacklog`, `simulateTrend`, `renderTrendBadge`, `fmtMilhares` (Tasks 2–3 + existentes)
- Produces: `renderZona3(kpis, clientes, consultores): string`; dashboard completo com 3 zonas; `renderDashboardProjetos` final sem placeholders

- [ ] **Step 1: Atualizar `chartGaugeConfig` — meta line via plugin afterDraw**

Localizar `function chartGaugeConfig` e substituir:

```javascript
function chartGaugeConfig(pct) {
  const cor = pct >= 85 ? '#38a169' : '#e53e3e';
  return {
    type: 'doughnut',
    data: { datasets: [{ data:[pct, 100-pct], backgroundColor:[cor,'#edf2f7'], borderWidth:0, circumference:180, rotation:-90 }] },
    options: { cutout:'72%', plugins:{ legend:{display:false}, tooltip:{enabled:false} }, animation:{duration:500} },
    plugins: [{
      id: 'gaugeMeta',
      afterDraw(chart) {
        const {ctx, chartArea} = chart;
        if (!chartArea) return;
        const cx = (chartArea.left + chartArea.right) / 2;
        const cy = chartArea.bottom;
        const r  = (chartArea.right - chartArea.left) * 0.38;
        // Semicircle: starts at -PI/2 (top=left edge), ends at +PI/2 (bottom=right edge)
        // 85% along the arc = -PI/2 + PI * 0.85
        const metaAngle = -Math.PI / 2 + Math.PI * 0.85;
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(cx + (r - 9) * Math.cos(metaAngle), cy + (r - 9) * Math.sin(metaAngle));
        ctx.lineTo(cx + (r + 9) * Math.cos(metaAngle), cy + (r + 9) * Math.sin(metaAngle));
        ctx.strokeStyle = '#E05A1E'; ctx.lineWidth = 2.5; ctx.stroke();
        ctx.fillStyle = '#E05A1E'; ctx.font = 'bold 9px Segoe UI,sans-serif';
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText('85%', cx + (r + 20) * Math.cos(metaAngle), cy + (r + 20) * Math.sin(metaAngle));
        ctx.restore();
      }
    }]
  };
}
```

- [ ] **Step 2: Atualizar `chartBarrasConfig` — gradiente + linha de meta**

Localizar `function chartBarrasConfig` e substituir:

```javascript
function chartBarrasConfig(clientes) {
  const produtos = [...new Set(clientes.map(c => c.produto.split('/')[0]))].filter(Boolean).sort();
  const series = [
    {label:'Em Andamento', key:'emAndamento', color:'#3182ce'},
    {label:'Atrasados',    key:'atrasado',    color:'#e53e3e'},
    {label:'Pausados',     key:'pausado',     color:'#d69e2e'},
    {label:'Concluídos',   key:'concluido',   color:'#38a169'},
  ];
  // Linha de meta: 85% do total de cada produto convertido para quantidade
  const metaData = produtos.map(p => {
    const total = clientes.filter(c => c.produto.split('/')[0] === p).length;
    return Math.round(total * 0.85);
  });

  const datasets = series.map(s => ({
    label: s.label,
    data: produtos.map(p => computeDashboardKPIs(clientes.filter(c => c.produto.split('/')[0] === p))[s.key]),
    backgroundColor: s.color,  // fallback para o primeiro frame (antes do plugin disparar)
    _gradColor: s.color,        // consumido pelo plugin barGradient (Task 2) para substituir por gradiente
    borderRadius: 4,
  }));

  // Dataset de meta: tipo 'line' — funciona em chart tipo 'bar' com datasets mistos
  datasets.push({
    label: 'Meta (85%)',
    type: 'line',
    data: metaData,
    borderColor: '#E05A1E',
    borderDash: [5, 4],
    borderWidth: 1.5,
    pointRadius: 0,
    fill: false,
    backgroundColor: 'transparent',
  });

  return {
    type: 'bar',
    data: { labels: produtos, datasets },
    options: {
      plugins: { legend:{ position:'bottom', labels:{ boxWidth:12, font:{size:12},
        filter: item => item.text !== 'Meta (85%)' ? true : true  // mostra a meta na legenda
      }}},
      scales: {
        y: { beginAtZero:true, grid:{ color:'#edf2f7' }, ticks:{ stepSize:1 } },
        x: { grid:{ display:false } }
      },
      animation: { duration:500 }
    }
  };
}
```

- [ ] **Step 3: Adicionar `renderZona3`**

Adicionar logo após `renderZona2`:

```javascript
function renderZona3(kpis, clientes, consultores) {
  const cps  = computeAtivacao(clientes, 'CPS');
  const nx   = computeAtivacao(clientes, 'NX');
  const back = computeBacklog(clientes);
  const corCPS   = cps.pct  >= 85 ? '#38a169' : '#e53e3e';
  const corNX    = nx.pct   >= 85 ? '#38a169' : '#e53e3e';
  const backTrend = simulateTrend(back.total, 4);

  return `
    <div class="dash-zone">
      <div class="dash-zone-title">Estamos batendo as metas?</div>
      <div class="dash-gauge-row">
        <div class="dash-card" style="text-align:center">
          <div class="chart-headline" style="text-align:left">Ativação CPS</div>
          <div class="chart-subline" style="text-align:left">Projetos concluídos dentro do prazo · meta 85%</div>
          <div style="height:130px;overflow:hidden"><canvas id="ch-gauge-cps"></canvas></div>
          <div style="margin-top:-20px;font-size:36px;font-weight:800;color:${corCPS};line-height:1">${cps.pct}%</div>
          <div style="font-size:12px;color:var(--text3);margin-top:6px">${cps.noPrazo}/${cps.concluidos} concluídos no prazo</div>
        </div>
        <div class="dash-card" style="text-align:center">
          <div class="chart-headline" style="text-align:left">Ativação NX</div>
          <div class="chart-subline" style="text-align:left">Projetos concluídos dentro do prazo · meta 85%</div>
          <div style="height:130px;overflow:hidden"><canvas id="ch-gauge-nx"></canvas></div>
          <div style="margin-top:-20px;font-size:36px;font-weight:800;color:${corNX};line-height:1">${nx.pct}%</div>
          <div style="font-size:12px;color:var(--text3);margin-top:6px">${nx.noPrazo}/${nx.concluidos} concluídos no prazo</div>
        </div>
        <div class="dash-card">
          <div class="chart-headline">Backlog de Atrasos</div>
          <div class="chart-subline">Dias acumulados fora do prazo</div>
          <div style="margin-top:12px">
            <div style="display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid #edf2f7">
              <span style="color:var(--text3);font-size:13px">Projetos atrasados</span>
              <span style="font-weight:700;color:#e53e3e;font-size:20px">${back.qtd}</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:flex-start;padding:12px 0;border-bottom:1px solid #edf2f7">
              <span style="color:var(--text3);font-size:13px">Total dias atrasados</span>
              <div style="text-align:right">
                <div style="font-weight:700;color:var(--text);font-size:20px">${fmtMilhares(back.total)}</div>
                ${renderTrendBadge(backTrend.delta, backTrend.dir, true)}
              </div>
            </div>
            <div style="display:flex;justify-content:space-between;padding:12px 0">
              <span style="color:var(--text3);font-size:13px">Média por projeto</span>
              <span style="font-weight:700;color:${back.media>90?'#e53e3e':back.media>45?'#d69e2e':'#38a169'};font-size:20px">${back.media} dias</span>
            </div>
          </div>
        </div>
      </div>
      <div class="dash-card" style="margin-top:16px">
        <div class="chart-headline">${computeNarrativaBarras(clientes)}</div>
        <div class="chart-subline">Status por produto · linha tracejada laranja = meta de ativação 85% convertida em quantidade</div>
        <div style="height:260px;margin-top:12px"><canvas id="ch-barras"></canvas></div>
      </div>
    </div>`;
}
```

- [ ] **Step 4: Finalizar `renderDashboardProjetos` com as 3 zonas**

Substituir o corpo completo de `renderDashboardProjetos` pela versão final (sem placeholders):

```javascript
function renderDashboardProjetos(clientes, consultores) {
  Object.values(_dashCharts).forEach(ch => { try{ ch.destroy(); }catch(e){} });
  _dashCharts = {};

  if (clientes.length === 0) {
    return `<div class="dash-filter-bar">
      <select onchange="setProjConsultor(this.value)">
        <option value="">Todos consultores</option>
        ${consultores.map(c => `<option value="${c.id}"${c.id===_proj_consultor?' selected':''}>${c.nome}</option>`).join('')}
      </select>
    </div>
    <div class="empty-state"><div class="es-icon">📊</div><div class="es-text">Nenhum projeto encontrado para este consultor.</div></div>`;
  }

  const kpis = computeDashboardKPIs(clientes);
  return `
    <div class="dash-filter-bar">
      <select onchange="setProjConsultor(this.value)">
        <option value="">Todos consultores</option>
        ${consultores.map(c => `<option value="${c.id}"${c.id===_proj_consultor?' selected':''}>${c.nome}</option>`).join('')}
      </select>
    </div>
    ${renderZona1(kpis, clientes, consultores)}
    ${renderZona2(kpis, clientes, consultores)}
    ${renderZona3(kpis, clientes, consultores)}`;
}
```

- [ ] **Step 5: Verificação completa no browser**

Sequência de testes:
1. **Dashboard padrão** — abrir `#projetos`, verificar:
   - Zona 1 visível above the fold: banner vermelho, 3 hero cards, alertas compactos
   - Zona 2: donut com label central via plugin, manchete narrativa, barras consultor com label vermelho para quem > 30% atrasado
   - Zona 3: gauges com % grande, linha de meta laranja desenhada no arco, barras agrupadas com gradiente e linha de meta tracejada
2. **Filtro por consultor** — selecionar "Ana Paula Souza", verificar que banner/hero/charts atualizam
3. **KPI cards clicáveis** — clicar "10 Atrasados" → navega para Lista filtrada → botão `×` na pill limpa filtro → volta para Dashboard
4. **Switch de views** — clicar Lista → Kanban → Dashboard, verificar que charts reinicializam sem erro no console
5. **Sidebar** — colapsar, recarregar, verificar que fica colapsada; expandir, confirma navegação funcional
6. **Console DevTools** — sem erros JS

- [ ] **Step 6: Commit final**

```bash
git add grv-cs-jornada.html
git commit -m "feat(dash-v2): Zona 3, integração das 3 zonas, gauge meta plugin, barras gradiente + linha meta"
```
