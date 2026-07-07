# Projetos GRV: Sub-páginas Portfólio / Implantação / Customer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separar "Projetos GRV" em três sub-páginas (Portfólio, Implantação, Customer) acessíveis por dropdown no topnav, dividindo clientes por `c.status`.

**Architecture:** SPA single-file `grv-cs-jornada.html`, hash routing, localStorage como banco. A nova variável global `_proj_tab` controla qual sub-página está ativa. `renderProjetosGRV()` passa a despachar para `renderPortfolio()`, `renderImplantacao()` ou `renderCustomer()` conforme `_proj_tab`. O dropdown no topnav usa hover CSS puro (`.nav-group:hover .nav-dropdown { display:flex }`). As três novas funções são declarações `function` (hoisted), então podem ser referenciadas antes de serem declaradas.

**Tech Stack:** HTML/CSS/JS inline, sem build step, localStorage.

## Global Constraints

- Arquivo único: `grv-cs-jornada.html` — todas as alterações vão nele
- Usar `function` declarations (não arrow functions ou `const fn =`) para garantir hoisting
- `saveCliente(c)` + re-render após qualquer mutação de dados
- Sem dependências externas novas
- Branch: `alteracoes`

---

## Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `grv-cs-jornada.html` | Todas as alterações — 6 blocos independentes descritos abaixo |

Seções do arquivo a tocar (usar como âncora de busca):

| Seção | Âncora para localizar |
|---|---|
| Topnav CSS (~linha 52) | `.nav-item:hover .nav-icon{opacity:.75}` |
| Topnav HTML (~linha 587) | `<div class="nav-item" id="nav-projetos"` |
| Globals Projetos (~linha 3328) | `const PROJETOS_VIEW_KEY =` |
| `renderProjetosGRV()` (linhas 3400–3524) | `function renderProjetosGRV() {` |
| Formulário Criar Playbook (~linha 4958) | `<label>Consultor responsável</label>` |
| `salvarPlaybook()` (~linha 5106) | `const novo = {` |

---

## Task 1 — CSS do dropdown + HTML do nav-group com dropdown

**Files:** Modify `grv-cs-jornada.html`

**Interfaces:**
- Produces: classes CSS `.nav-group`, `.nav-dropdown`, `.nav-drop-item`, `.nav-drop-badge`; elementos HTML com IDs `nav-projetos-group`, `proj-dropdown`, `drop-portfolio`, `drop-implantacao`, `drop-customer`, `drop-portfolio-badge`, `drop-implantacao-badge`, `drop-customer-badge`, `nav-proj-subbadge`

- [ ] **Step 1: Adicionar CSS do dropdown**

Localizar a linha:
```css
.nav-item:hover .nav-icon{opacity:.75}
```

Inserir logo após essa linha:
```css
.nav-group{position:relative;height:100%;display:flex;align-items:center}
.nav-group:hover .nav-dropdown{display:flex}
.nav-dropdown{display:none;position:absolute;top:100%;left:0;background:var(--sidebar-bg);border:1px solid var(--border);border-radius:var(--radius);box-shadow:0 4px 16px rgba(0,0,0,.12);padding:6px 0;flex-direction:column;min-width:200px;z-index:300}
.nav-drop-header{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text4);padding:6px 16px 4px}
.nav-drop-divider{height:1px;background:var(--border);margin:4px 0}
.nav-drop-item{display:flex;align-items:center;justify-content:space-between;padding:8px 16px;cursor:pointer;font-size:12.5px;color:var(--text2);transition:background .1s;border-left:2px solid transparent;white-space:nowrap}
.nav-drop-item:hover{background:var(--bg-hover,rgba(0,0,0,.04))}
.nav-drop-item.active{color:var(--primary);border-left-color:var(--primary);padding-left:14px;font-weight:600;background:rgba(255,107,53,.05)}
.nav-drop-badge{font-size:10px;color:var(--text3);font-weight:600;background:var(--bg);padding:1px 7px;border-radius:8px;border:1px solid var(--border);margin-left:12px}
.nav-drop-item.active .nav-drop-badge{background:rgba(255,107,53,.08);color:var(--primary);border-color:rgba(255,107,53,.3)}
.nav-proj-subbadge{font-size:10px;color:var(--text3);font-weight:500;margin-left:4px}
```

- [ ] **Step 2: Substituir o nav-item Projetos GRV por um nav-group com dropdown**

Localizar:
```html
      <div class="nav-item" id="nav-projetos" data-route="projetos" onclick="navigate('projetos')">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 010 20M12 2a15.3 15.3 0 000 20"/></svg>
        Projetos GRV
      </div>
```

Substituir por:
```html
      <div class="nav-group" id="nav-projetos-group">
        <div class="nav-item" id="nav-projetos" data-route="projetos" onclick="navigate('projetos')">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 010 20M12 2a15.3 15.3 0 000 20"/></svg>
          Projetos GRV
          <span id="nav-proj-subbadge" class="nav-proj-subbadge"></span>
          <svg style="width:10px;height:10px;margin-left:3px;opacity:.4;flex-shrink:0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 9l6 6 6-6"/></svg>
        </div>
        <div class="nav-dropdown" id="proj-dropdown">
          <div class="nav-drop-header">PROJETOS GRV</div>
          <div class="nav-drop-divider"></div>
          <div class="nav-drop-item" id="drop-portfolio" onclick="setProjetosTab('portfolio')">
            Portfólio <span class="nav-drop-badge" id="drop-portfolio-badge"></span>
          </div>
          <div class="nav-drop-item" id="drop-implantacao" onclick="setProjetosTab('implantacao')">
            Implantação <span class="nav-drop-badge" id="drop-implantacao-badge"></span>
          </div>
          <div class="nav-drop-item" id="drop-customer" onclick="setProjetosTab('customer')">
            Customer <span class="nav-drop-badge" id="drop-customer-badge"></span>
          </div>
        </div>
      </div>
```

- [ ] **Step 3: Verificar no browser**

Abrir `http://localhost:7799/grv-cs-jornada.html`.  
Passar o mouse sobre "Projetos GRV" no topnav — o dropdown deve aparecer com as três opções.  
O dropdown fecha ao mover o mouse para fora.  
Os badges ainda estão vazios (serão preenchidos na Task 2). ✅

- [ ] **Step 4: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(projetos): dropdown nav-group com Portfólio / Implantação / Customer"
```

---

## Task 2 — Global `_proj_tab` + `setProjetosTab()` + refatorar `renderProjetosGRV()`

**Files:** Modify `grv-cs-jornada.html`

**Interfaces:**
- Consumes: `renderPortfolio()`, `renderImplantacao()`, `renderCustomer()` (Tasks 3–5 — declaradas com `function`, portanto hoisted; podem ser referenciadas aqui antes de serem definidas no arquivo)
- Produces: `_proj_tab: string` global, `setProjetosTab(tab: string): void`, `renderProjetosGRV()` refatorado

- [ ] **Step 1: Adicionar globals `_proj_tab` e `setProjetosTab`**

Localizar:
```javascript
const PROJETOS_VIEW_KEY = 'grv_cs_projetos_view';
```

Inserir logo antes dessa linha:
```javascript
const PROJ_TAB_KEY = 'grv_cs_proj_tab';
let _proj_tab = localStorage.getItem(PROJ_TAB_KEY) || 'implantacao';
// 'portfolio' | 'implantacao' | 'customer'

function setProjetosTab(tab) {
  _proj_tab = tab;
  localStorage.setItem(PROJ_TAB_KEY, tab);
  navigate('projetos');
}
```

- [ ] **Step 2: Substituir o corpo completo de `renderProjetosGRV()`**

Localizar o bloco inteiro de `renderProjetosGRV()`, da linha `function renderProjetosGRV() {` até o `}` de fechamento da função (que termina com `sec.innerHTML = ...`).

Substituir por:
```javascript
function renderProjetosGRV() {
  const todos = getClientes();
  const nImpl = todos.filter(function(c){ return c.status !== 'cs_ativo'; }).length;
  const nCs   = todos.filter(function(c){ return c.status === 'cs_ativo'; }).length;

  // Atualiza badges e estado ativo do dropdown
  var counts = {portfolio: todos.length, implantacao: nImpl, customer: nCs};
  ['portfolio','implantacao','customer'].forEach(function(tab) {
    var badgeEl = document.getElementById('drop-'+tab+'-badge');
    var itemEl  = document.getElementById('drop-'+tab);
    if (badgeEl) badgeEl.textContent = counts[tab];
    if (itemEl)  itemEl.classList.toggle('active', _proj_tab === tab);
  });
  var subEl = document.getElementById('nav-proj-subbadge');
  if (subEl) {
    var labels = {portfolio:'· Portfólio', implantacao:'· Implantação', customer:'· Customer'};
    subEl.textContent = labels[_proj_tab] || '';
  }

  if (_proj_tab === 'customer')    { renderCustomer();    return; }
  if (_proj_tab === 'implantacao') { renderImplantacao(); return; }
  renderPortfolio();
}
```

- [ ] **Step 3: Verificar no browser**

Abrir `http://localhost:7799/grv-cs-jornada.html` → navegar para Projetos GRV.  
O texto "· Implantação" deve aparecer ao lado de "Projetos GRV" no topnav (default).  
Ao passar o mouse sobre o topnav, os badges do dropdown devem mostrar as contagens corretas.  
O item "Implantação" deve ter borda esquerda laranja. ✅  
(A tela pode dar erro de função não definida — `renderImplantacao` ainda não existe — se Tasks 3–5 ainda não foram feitas. Isso é esperado.)

- [ ] **Step 4: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(projetos): _proj_tab global + renderProjetosGRV despacha por tab"
```

---

## Task 3 — `renderPortfolio()` (todos os clientes, dashboard/lista/kanban existente)

**Files:** Modify `grv-cs-jornada.html`

**Interfaces:**
- Consumes: `getClientes()`, `getConsultores()`, `ETAPAS`, `ETAPA_META`, `STATUS_COLOR`, `getProgresso(c)`, `getStatus(c)`, `getStatusDash(c)`, `getEtapaBadge(etapa)`, `getStatusBadge(st)`, `fmtDate(date)`, `calcProgresso(ativPlaybooks)`, `renderDashboardProjetos(clientes, consultores)`, `renderKanbanBoard(filtered, consultores, false)`, `computeDashboardKPIs(clientes)`, `initCharts(kpis, clientes, consultores)`, `drillKpi(v)`, variáveis globais `_proj_consultor`, `_proj_view`, `_proj_etapa`, `_proj_status`, `_proj_kpi_filter`
- Produces: `renderPortfolio(): void` — função declarada (hoisted)

Esta função é o dashboard atual de `renderProjetosGRV()` extraído para função própria, adicionando no subtitle a divisão `X em implantação · Y em CS`.

- [ ] **Step 1: Adicionar `renderPortfolio()` logo antes de `renderProjetosGRV()`**

Localizar:
```javascript
function renderProjetosGRV() {
```

Inserir o seguinte bloco ANTES dessa linha (não dentro dela):
```javascript
function renderPortfolio() {
  const todos       = getClientes();
  const consultores = getConsultores();
  const sec         = document.getElementById('sec-projetos');

  const nImpl = todos.filter(function(c){ return c.status !== 'cs_ativo'; }).length;
  const nCs   = todos.filter(function(c){ return c.status === 'cs_ativo'; }).length;

  let filtered = todos;
  if (_proj_consultor) filtered = filtered.filter(function(c){ return c.consultorId === _proj_consultor; });
  if (_proj_view !== 'dashboard') {
    if (_proj_kpi_filter) filtered = filtered.filter(function(c){ return getStatusDash(c) === _proj_kpi_filter; });
    else {
      if (_proj_etapa)  filtered = filtered.filter(function(c){ return c.etapa === _proj_etapa; });
      if (_proj_status) filtered = filtered.filter(function(c){ return getStatus(c) === _proj_status; });
    }
  }

  const toggle = `
    <div class="view-toggle">
      <button class="vt-btn${_proj_view==='dashboard'?' active':''}" onclick="setProjetosView('dashboard')">📊 Dashboard</button>
      <button class="vt-btn${_proj_view==='lista'?' active':''}" onclick="setProjetosView('lista')">☰ Lista</button>
      <button class="vt-btn${_proj_view==='kanban'?' active':''}" onclick="setProjetosView('kanban')">⊞ Kanban</button>
    </div>`;

  if (_proj_view === 'dashboard') {
    const dashClientes = _proj_consultor ? todos.filter(function(c){ return c.consultorId === _proj_consultor; }) : todos;
    const dashKpis     = computeDashboardKPIs(dashClientes);
    sec.innerHTML = `
      <div class="page-header" style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px">
        <div>
          <div class="page-title">Projetos GRV — Portfólio</div>
          <div class="page-subtitle">Visão estratégica do portfólio · ${todos.length} total · ${nImpl} em implantação · ${nCs} em CS</div>
        </div>
        ${toggle}
      </div>
      ${renderDashboardProjetos(dashClientes, consultores)}`;
    initCharts(dashKpis, dashClientes, consultores);
    return;
  }

  const kpiPill = _proj_kpi_filter
    ? `<span style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;background:#E05A1E22;border:1px solid #E05A1E66;border-radius:20px;font-size:12px;color:#E05A1E;font-weight:600">
        Filtro: ${_proj_kpi_filter}
        <span onclick="drillKpi('')" style="cursor:pointer;font-size:14px;line-height:1" title="Limpar filtro">×</span>
       </span>` : '';

  const filterBar = `
    <div class="filter-bar">
      <select onchange="setProjConsultor(this.value)">
        <option value="">Todos consultores</option>
        ${consultores.map(function(c){ return '<option value="'+c.id+'"'+(c.id===_proj_consultor?' selected':'')+'>'+c.nome+'</option>'; }).join('')}
      </select>
      ${_proj_kpi_filter ? kpiPill : `
      <select onchange="setProjEtapa(this.value)">
        <option value="">Todas etapas</option>
        ${ETAPAS.map(function(e){ return '<option value="'+e+'"'+(e===_proj_etapa?' selected':'')+'>'+ETAPA_META[e].emoji+' '+e+'</option>'; }).join('')}
      </select>
      <select onchange="setProjStatus(this.value)">
        <option value="">Todos status</option>
        ${Object.keys(STATUS_COLOR).map(function(s){ return '<option value="'+s+'"'+(s===_proj_status?' selected':'')+'>'+s+'</option>'; }).join('')}
      </select>`}
    </div>`;

  let content;
  if (_proj_view === 'lista') {
    content = filtered.length === 0
      ? `<div class="empty-state"><div class="es-icon">🔍</div><div class="es-text">Nenhum projeto encontrado com este filtro.</div></div>`
      : `<div class="table-wrap">
           <table class="data-table">
             <thead><tr>
               <th>Cliente</th><th>Consultor</th><th>Etapa</th><th>Status</th>
               <th style="width:130px">Progresso</th><th>Prazo</th>
             </tr></thead>
             <tbody>
               ${filtered.map(function(c) {
                 var prog   = getProgresso(c);
                 var st     = getStatus(c);
                 var consul = (consultores.find(function(x){ return x.id === c.consultorId; }) || {}).nome || c.consultorId;
                 return '<tr onclick="navigate(\'cliente/'+encodeURIComponent(c.id)+'\')">'
                   + '<td><div style="font-weight:600">'+c.id+'</div><div class="proj-id">'+c.projeto+'</div></td>'
                   + '<td style="font-size:12px;color:var(--text2)">'+consul+'</td>'
                   + '<td>'+getEtapaBadge(c.etapa)+'</td>'
                   + '<td>'+getStatusBadge(st)+'</td>'
                   + '<td><div style="display:flex;align-items:center;gap:8px"><div class="prog-wrap" style="flex:1"><div class="prog-fill" style="width:'+prog+'%"></div></div><span style="font-size:11px;color:var(--text3);white-space:nowrap">'+prog+'%</span></div></td>'
                   + '<td style="font-size:12px;color:'+(st==='Atrasado'?'var(--red)':'var(--text2)')+'">'+fmtDate(c.prazo)+'</td>'
                   + '</tr>';
               }).join('')}
             </tbody>
           </table>
         </div>`;
  } else {
    content = renderKanbanBoard(filtered, consultores, false);
  }

  const csats     = todos.filter(function(c){ return c.csat; }).map(function(c){ return c.csat; });
  const csatMedio = csats.length ? (csats.reduce(function(s,v){return s+v;},0)/csats.length).toFixed(1) : '—';
  const atrNovo   = todos.filter(function(c){ return c.status !== 'cs_ativo' && getStatus(c) === 'Atrasado'; }).length;
  const progressos = todos.map(function(c){ return calcProgresso(c.ativPlaybooks || []); });
  const progMedio  = progressos.length ? Math.round(progressos.reduce(function(s,v){return s+v;},0)/progressos.length) : 0;

  sec.innerHTML = `
    <div class="page-header" style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px">
      <div>
        <div class="page-title">Projetos GRV — Portfólio</div>
        <div class="page-subtitle">Todos os projetos · ${todos.length} total · ${nImpl} em implantação · ${nCs} em CS</div>
      </div>
      ${toggle}
    </div>
    <div class="metric-grid">
      <div class="metric-card mc-accent"><div class="mc-label">Total de projetos</div><div class="mc-value">${todos.length}</div></div>
      <div class="metric-card mc-green"><div class="mc-label">CSAT médio ★</div><div class="mc-value">${csatMedio}</div></div>
      <div class="metric-card mc-red"><div class="mc-label">Em atraso</div><div class="mc-value">${atrNovo}</div></div>
      <div class="metric-card mc-gray"><div class="mc-label">Progresso médio</div><div class="mc-value">${progMedio}%</div></div>
    </div>
    ${filterBar}
    ${content}`;
}

```

- [ ] **Step 2: Verificar no browser**

Abrir Projetos GRV → no dropdown, clicar em "Portfólio".  
Título deve ser "Projetos GRV — Portfólio" com subtitle mostrando `X total · Y em implantação · Z em CS`.  
Toggle Dashboard/Lista/Kanban funciona normalmente.  
Filtros de consultor/etapa/status funcionam. ✅

- [ ] **Step 3: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(projetos): renderPortfolio() — visão de todos os clientes com divisão impl/CS"
```

---

## Task 4 — `renderImplantacao()` (KPIs + Lista/Kanban, filtrado por `status !== 'cs_ativo'`)

**Files:** Modify `grv-cs-jornada.html`

**Interfaces:**
- Consumes: `getClientes()`, `getConsultores()`, `ETAPAS`, `ETAPA_META`, `STATUS_COLOR`, `getProgresso(c)`, `getStatus(c)`, `getEtapaBadge(etapa)`, `getStatusBadge(st)`, `fmtDate(date)`, `renderKanbanBoard(filtered, consultores, false)`, `_proj_consultor`, `_proj_view`, `_proj_etapa`, `_proj_status`
- Produces: `renderImplantacao(): void` — função declarada (hoisted)

- [ ] **Step 1: Adicionar `renderImplantacao()` logo antes de `renderPortfolio()`**

Localizar:
```javascript
function renderPortfolio() {
```

Inserir o seguinte bloco ANTES dessa linha:
```javascript
function renderImplantacao() {
  const todos       = getClientes().filter(function(c){ return c.status !== 'cs_ativo'; });
  const consultores = getConsultores();
  const sec         = document.getElementById('sec-projetos');

  let filtered = todos;
  if (_proj_consultor) filtered = filtered.filter(function(c){ return c.consultorId === _proj_consultor; });
  if (_proj_etapa)     filtered = filtered.filter(function(c){ return c.etapa === _proj_etapa; });
  if (_proj_status)    filtered = filtered.filter(function(c){ return getStatus(c) === _proj_status; });

  const nTotal     = todos.length;
  const nNoPrazo   = todos.filter(function(c){ return getStatus(c) !== 'Atrasado'; }).length;
  const nAtrasados = nTotal - nNoPrazo;
  const progressos = todos.map(function(c){ return getProgresso(c); });
  const progMedio  = progressos.length ? Math.round(progressos.reduce(function(s,v){return s+v;},0)/progressos.length) : 0;

  const toggle = `
    <div class="view-toggle">
      <button class="vt-btn${_proj_view==='lista'||_proj_view==='dashboard'?' active':''}" onclick="setProjetosView('lista')">☰ Lista</button>
      <button class="vt-btn${_proj_view==='kanban'?' active':''}" onclick="setProjetosView('kanban')">⊞ Kanban</button>
    </div>`;

  const filterBar = `
    <div class="filter-bar">
      <select onchange="setProjConsultor(this.value)">
        <option value="">Todos consultores</option>
        ${consultores.map(function(c){ return '<option value="'+c.id+'"'+(c.id===_proj_consultor?' selected':'')+'>'+c.nome+'</option>'; }).join('')}
      </select>
      <select onchange="setProjEtapa(this.value)">
        <option value="">Todas etapas</option>
        ${ETAPAS.map(function(e){ return '<option value="'+e+'"'+(e===_proj_etapa?' selected':'')+'>'+ETAPA_META[e].emoji+' '+e+'</option>'; }).join('')}
      </select>
      <select onchange="setProjStatus(this.value)">
        <option value="">Todos status</option>
        ${Object.keys(STATUS_COLOR).map(function(s){ return '<option value="'+s+'"'+(s===_proj_status?' selected':'')+'>'+s+'</option>'; }).join('')}
      </select>
    </div>`;

  let content;
  if (_proj_view === 'kanban') {
    content = renderKanbanBoard(filtered, consultores, false);
  } else {
    content = filtered.length === 0
      ? `<div class="empty-state"><div class="es-icon">🔍</div><div class="es-text">Nenhum projeto em implantação encontrado.</div></div>`
      : `<div class="table-wrap">
           <table class="data-table">
             <thead><tr>
               <th>Cliente</th><th>Consultor Digital</th><th>Etapa</th>
               <th style="width:130px">Progresso</th><th>Prazo</th><th>Status</th>
             </tr></thead>
             <tbody>
               ${filtered.map(function(c) {
                 var prog   = getProgresso(c);
                 var st     = getStatus(c);
                 var consul = (consultores.find(function(x){ return x.id === c.consultorId; }) || {}).nome || c.consultorId;
                 return '<tr onclick="navigate(\'cliente/'+encodeURIComponent(c.id)+'\')">'
                   + '<td><div style="font-weight:600">'+c.id+'</div><div class="proj-id">'+c.projeto+'</div></td>'
                   + '<td style="font-size:12px;color:var(--text2)">'+consul+'</td>'
                   + '<td>'+getEtapaBadge(c.etapa)+'</td>'
                   + '<td><div style="display:flex;align-items:center;gap:8px"><div class="prog-wrap" style="flex:1"><div class="prog-fill" style="width:'+prog+'%"></div></div><span style="font-size:11px;color:var(--text3);white-space:nowrap">'+prog+'%</span></div></td>'
                   + '<td style="font-size:12px;color:'+(st==='Atrasado'?'var(--red)':'var(--text2)')+'">'+fmtDate(c.prazo)+'</td>'
                   + '<td>'+getStatusBadge(st)+'</td>'
                   + '</tr>';
               }).join('')}
             </tbody>
           </table>
         </div>`;
  }

  sec.innerHTML = `
    <div class="page-header" style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px">
      <div>
        <div class="page-title">Projetos GRV — Implantação</div>
        <div class="page-subtitle">Clientes em processo de implantação · ${nTotal} total</div>
      </div>
      ${toggle}
    </div>
    <div class="metric-grid">
      <div class="metric-card mc-accent"><div class="mc-label">Em Implantação</div><div class="mc-value">${nTotal}</div></div>
      <div class="metric-card mc-green"><div class="mc-label">No Prazo</div><div class="mc-value">${nNoPrazo}</div></div>
      <div class="metric-card mc-red"><div class="mc-label">Atrasados</div><div class="mc-value">${nAtrasados}</div></div>
      <div class="metric-card mc-gray"><div class="mc-label">Progresso Médio</div><div class="mc-value">${progMedio}%</div></div>
    </div>
    ${filterBar}
    ${content}`;
}

```

- [ ] **Step 2: Verificar no browser**

Abrir Projetos GRV → no dropdown, clicar em "Implantação".  
Título: "Projetos GRV — Implantação".  
KPIs: Em Implantação / No Prazo / Atrasados / Progresso Médio — com valores corretos.  
Lista mostra apenas clientes com `status !== 'cs_ativo'`. Coluna "Consultor Digital" presente.  
Toggle Lista/Kanban funciona. Filtros funcionam. ✅

- [ ] **Step 3: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(projetos): renderImplantacao() — KPIs + lista/kanban filtrados por em_implantacao"
```

---

## Task 5 — `renderCustomer()` (KPIs + Lista, filtrado por `status === 'cs_ativo'`, ordenado por health score)

**Files:** Modify `grv-cs-jornada.html`

**Interfaces:**
- Consumes: `getClientes()`, `getConsultores()`, `calcHealthScore(c): number`, `calcCsatAtual(c): number|null`, `getDiasUltimoContato(c): number`, `fmtDate(date)`, `_proj_consultor`
- Produces: `renderCustomer(): void` — função declarada (hoisted)

- [ ] **Step 1: Adicionar `renderCustomer()` logo antes de `renderImplantacao()`**

Localizar:
```javascript
function renderImplantacao() {
```

Inserir o seguinte bloco ANTES dessa linha:
```javascript
function renderCustomer() {
  const todos       = getClientes().filter(function(c){ return c.status === 'cs_ativo'; });
  const consultores = getConsultores();
  const sec         = document.getElementById('sec-projetos');

  let filtered = todos;
  if (_proj_consultor) filtered = filtered.filter(function(c){
    return (c.csId || c.consultorId) === _proj_consultor;
  });

  // Ordenar por health score crescente — menor health = maior risco = topo
  filtered = filtered.slice().sort(function(a, b){
    return calcHealthScore(a) - calcHealthScore(b);
  });

  const nTotal      = todos.length;
  const healthAll   = todos.map(function(c){ return calcHealthScore(c); });
  const healthMedio = healthAll.length
    ? Math.round(healthAll.reduce(function(s,v){return s+v;},0)/healthAll.length) : 0;
  const csatAll     = todos.map(function(c){ return calcCsatAtual(c); }).filter(function(v){ return v !== null; });
  const csatMedio   = csatAll.length ? (csatAll.reduce(function(s,v){return s+v;},0)/csatAll.length).toFixed(1) : '—';
  const semContato  = todos.filter(function(c){ return getDiasUltimoContato(c) > 30; }).length;

  const filterBar = `
    <div class="filter-bar">
      <select onchange="setProjConsultor(this.value)">
        <option value="">Todos CS</option>
        ${consultores.map(function(con){
          return '<option value="'+con.id+'"'+(con.id===_proj_consultor?' selected':'')+'>'+con.nome+'</option>';
        }).join('')}
      </select>
    </div>`;

  function healthPill(score) {
    var color = score >= 70 ? 'var(--green)' : score >= 40 ? '#f59e0b' : 'var(--red)';
    return '<span style="font-size:13px;font-weight:700;color:'+color+'">'+score+'</span>';
  }

  var rows = filtered.map(function(c) {
    var health = calcHealthScore(c);
    var csat   = calcCsatAtual(c);
    var dias   = getDiasUltimoContato(c);
    var csNome = (consultores.find(function(x){ return x.id === (c.csId||''); }) || {}).nome || (c.csId ? c.csId : '—');
    var diasCell = dias > 30
      ? '<span style="color:var(--red);font-weight:600">'+dias+'d</span>'
      : '<span style="color:var(--text2)">'+dias+'d</span>';
    return '<tr onclick="navigate(\'cliente/'+encodeURIComponent(c.id)+'\')">'
      + '<td><div style="font-weight:600">'+c.id+'</div><div class="proj-id">'+(c.segmento||c.produto||c.projeto||'')+'</div></td>'
      + '<td style="font-size:12px;color:var(--text2)">'+csNome+'</td>'
      + '<td>'+healthPill(health)+'</td>'
      + '<td style="font-size:12px">'+(csat !== null ? '★ '+csat : '—')+'</td>'
      + '<td>'+diasCell+'</td>'
      + '<td style="font-size:12px;color:var(--text2)">'+(c.proximaAcao||'—')+'</td>'
      + '</tr>';
  }).join('');

  var tableHtml = filtered.length === 0
    ? `<div class="empty-state"><div class="es-icon">⭐</div><div class="es-text">Nenhum cliente em Customer Success encontrado.</div></div>`
    : `<div class="table-wrap">
         <table class="data-table">
           <thead><tr>
             <th>Cliente</th><th>CS Responsável</th><th>Health Score</th>
             <th>CSAT</th><th>Último Contato</th><th>Próxima Ação</th>
           </tr></thead>
           <tbody>${rows}</tbody>
         </table>
       </div>`;

  sec.innerHTML = `
    <div class="page-header">
      <div>
        <div class="page-title">Projetos GRV — Customer</div>
        <div class="page-subtitle">Clientes em Customer Success · ${nTotal} total · ordenados por risco (menor health primeiro)</div>
      </div>
    </div>
    <div class="metric-grid">
      <div class="metric-card mc-accent"><div class="mc-label">Em Customer</div><div class="mc-value">${nTotal}</div></div>
      <div class="metric-card mc-green"><div class="mc-label">Health Médio</div><div class="mc-value">${healthMedio}</div></div>
      <div class="metric-card mc-green"><div class="mc-label">CSAT Médio ★</div><div class="mc-value">${csatMedio}</div></div>
      <div class="metric-card mc-red"><div class="mc-label">Sem Contato +30d</div><div class="mc-value">${semContato}</div></div>
    </div>
    ${filterBar}
    ${tableHtml}`;
}

```

- [ ] **Step 2: Verificar no browser**

Abrir Projetos GRV → no dropdown, clicar em "Customer".  
Título: "Projetos GRV — Customer".  
KPIs: Em Customer / Health Médio / CSAT Médio / Sem Contato +30d.  
Lista mostra apenas `status === 'cs_ativo'`. Ordenada por health crescente (menor = topo = maior risco).  
Health Score aparece colorido: verde ≥ 70, amarelo 40–69, vermelho < 40.  
Clientes com último contato > 30d em vermelho. ✅  
Filtro por CS Responsável funciona. ✅

- [ ] **Step 3: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(projetos): renderCustomer() — lista cs_ativo ordenada por health score"
```

---

## Task 6 — Campo CS Responsável no formulário "Criar Playbook"

**Files:** Modify `grv-cs-jornada.html`

**Interfaces:**
- Consumes: `getConsultores()`, campo `f-cs` do DOM
- Produces: `c.csId: string | undefined` salvo no objeto do cliente via `salvarPlaybook()`

- [ ] **Step 1: Adicionar campo `f-cs` no formulário manual**

Localizar dentro da branch de entrada manual do formulário (~linha 4958):
```html
          <div class="form-group">
            <label>Consultor responsável</label>
            <select id="f-consultor">
              ${consultores.map(c => `<option value="${c.id}"${c.id===ativo?' selected':''}>${c.nome}</option>`).join('')}
            </select>
          </div>
```

Inserir logo após esse bloco `</div>`:
```html
          <div class="form-group">
            <label>CS Responsável <span style="font-size:10px;color:var(--text3);font-weight:400">(opcional)</span></label>
            <select id="f-cs">
              <option value="">— Definir depois —</option>
              ${consultores.map(c => `<option value="${c.id}">${c.nome}</option>`).join('')}
            </select>
          </div>
```

- [ ] **Step 2: Salvar `csId` em `salvarPlaybook()`**

Localizar dentro de `salvarPlaybook()` (~linha 5106):
```javascript
    const novo = {
      id, projeto, produto, consultorId: consul, etapa,
      dataInicio, prazo,
      proximaAcao: acao || '',
```

Substituir por:
```javascript
    const csIdVal = document.getElementById('f-cs')?.value || '';
    const novo = {
      id, projeto, produto, consultorId: consul, csId: csIdVal || undefined, etapa,
      dataInicio, prazo,
      proximaAcao: acao || '',
```

> `csId: csIdVal || undefined` evita persistir string vazia no localStorage — clientes sem CS mantêm `c.csId === undefined`, o que é verdadeiro para todos os checks de truthiness existentes.

- [ ] **Step 3: Verificar no browser**

Abrir "Criar Playbook" → modo de entrada manual.  
Campo "CS Responsável (opcional)" deve aparecer abaixo de "Consultor responsável".  
Criar um cliente com CS selecionado → abrir localStorage (DevTools) → confirmar que `csId` está salvo no objeto.  
Criar cliente sem CS → confirmar que `csId` está ausente (undefined, não string vazia). ✅

- [ ] **Step 4: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(criar-playbook): campo CS Responsável opcional no formulário de criação"
```

---

## Self-Review do Plano

**Cobertura do spec:**

| Requisito do spec | Task |
|---|---|
| Dropdown no topnav com hover | Task 1 (CSS + HTML) |
| Item ativo com borda esquerda laranja + fundo sutil | Task 1 (CSS `.nav-drop-item.active`) |
| Badge de contagem em cada item do dropdown | Task 2 (atualiza `drop-*-badge`) |
| Nome da sub-página ativa ao lado de "Projetos GRV" | Task 2 (`nav-proj-subbadge`) |
| `_proj_tab` global + `setProjetosTab()` | Task 2 |
| `renderProjetosGRV()` despacha por tab | Task 2 |
| Portfólio: todos os clientes, dashboard/lista/kanban | Task 3 |
| Portfólio: subtitle com X em implantação · Y em CS | Task 3 |
| Implantação: filtrado por `status !== 'cs_ativo'` | Task 4 |
| Implantação: KPIs (Em Implantação / No Prazo / Atrasados / Progresso Médio) | Task 4 |
| Implantação: lista com coluna Consultor Digital | Task 4 |
| Implantação: toggle Lista/Kanban (sem Dashboard) | Task 4 |
| Customer: filtrado por `status === 'cs_ativo'` | Task 5 |
| Customer: KPIs (Em Customer / Health Médio / CSAT Médio / Sem Contato +30d) | Task 5 |
| Customer: lista com Health Score pill colorida (verde/amarelo/vermelho) | Task 5 |
| Customer: lista com CS Responsável (`c.csId`) | Task 5 |
| Customer: lista com Último Contato — vermelho se > 30d | Task 5 |
| Customer: ordenado por health score crescente | Task 5 |
| Customer: apenas Lista (sem Kanban) | Task 5 (sem toggle) |
| Campo CS Responsável no formulário Criar Playbook | Task 6 |
| `c.csId` salvo — undefined se vazio | Task 6 |

Cobertura: 100%.

**Placeholder scan:** Nenhum "TBD", "TODO" ou seção incompleta.

**Type consistency:**
- `calcHealthScore(c)` → `number` — usado em Task 5 para `healthPill(score)` e `sort`
- `calcCsatAtual(c)` → `number | null` — Task 5 filtra `!== null` antes de calcular média
- `getDiasUltimoContato(c)` → `number` — Task 5 compara com `> 30`
- `getProgresso(c)` → `number` (0–100) — Task 4 usa para `progMedio` e barra de progresso
- `getStatus(c)` → `'Pausado'|'Interrompido'|'Cancelado'|'Atrasado'|'Em ordem'` — Task 4 compara com `=== 'Atrasado'`

**Nota sobre `_proj_view` em Implantação:** O default de `_proj_view` é `'dashboard'` (salvo no localStorage). Ao trocar de Portfólio para Implantação pela primeira vez, `_proj_view` pode ser `'dashboard'`. O toggle de Implantação trata `lista` e `dashboard` como equivalentes (o botão "Lista" fica ativo quando `_proj_view === 'lista' || _proj_view === 'dashboard'`), e o `if (_proj_view === 'kanban')` só ativa kanban explicitamente. Resultado correto: usuários vindos do dashboard de Portfólio verão automaticamente a lista de Implantação.
