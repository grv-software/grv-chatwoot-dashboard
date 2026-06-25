# Redesign Visual e Funcional — GRV CS Jornada

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign completo de navegação, visual e modelo de dados do `grv-cs-jornada.html` — sidebar branca estilo SAG, Minha Carteira Feed+Kanban, overlay de atividade com 3 abas, lifecycle permanente do cliente.

**Architecture:** Single-file SPA (`grv-cs-jornada.html`) — todo CSS + JS inline. Tasks sequenciais; cada uma estende o modelo de dados da anterior. **Executar após merge da v3 (abas 360°/Atividades/Notas).**

**Tech Stack:** HTML/CSS/JS vanilla, localStorage como DB, Chart.js v4 via CDN.

## Global Constraints

- Arquivo único: `grv-cs-jornada.html` — não criar arquivos externos
- Array canônico: `ativPlaybooks[]` (não `Playbooks[]` nem `playbooks[]`)
- Sub-arrays de atividade: `atividades[]`, `registros[]`, `checklist[]`, `anotacoes[]` (todos lowercase)
- Consultor ativo: sempre via `getConsultorAtivo()` — nunca hardcodado
- Buscar funções por nome antes de editar — line numbers mudam com o merge de v3
- Não remover: `historicoEtapas`, `checkTask()`, `showToast()`, `fases[]`
- Novo CSS: usar `var(--token)` — nunca hex hardcoded

---

### Task 1: Seed + helpers de dados

**Files:**
- Modify: `grv-cs-jornada.html` — SEED_CLIENTES e bloco de helpers JS

**Interfaces:**
- Produz: `calcProgresso(pbOrArray)`, `getMinhaCarteira(consultorId)`, `getStatusCliente(c, consultorId)`, `getKanbanColuna(c, consultorId)`

- [ ] **Step 1: Verificar que v3 já inseriu `ativPlaybooks[]`**

Abrir `grv-cs-jornada.html`. Buscar `ativPlaybooks`. Se não existir, parar — v3 precisa ser mergeada primeiro.

- [ ] **Step 2: Adicionar `status`, `dataInicioImplantacao`, `dataInicioCS` a cada cliente do SEED**

Localizar `const SEED_CLIENTES`. Para cada objeto de cliente, adicionar (se não existir):
```javascript
status: 'em_implantacao',
dataInicioImplantacao: '2025-01-15',   // usar valor de c.dataInicio se disponível
dataInicioCS: null,
```

- [ ] **Step 3: Adicionar `donoId` e `fase` a cada playbook do SEED**

Para cada entrada em `ativPlaybooks[]` de cada cliente:
```javascript
// Dentro de cada playbook objeto:
donoId: cliente.csId,   // ex: 'severiano'
fase:   'implantacao',
```

- [ ] **Step 4: Adicionar `responsavelId`, `checklist`, `anotacoes` a cada atividade**

Para cada objeto em `atividades[]` de cada playbook:
```javascript
responsavelId: pb.donoId,
checklist:  [],
anotacoes:  [],
// registros já deve existir de v3; se não existir: registros: []
```

- [ ] **Step 5: Adicionar `calcProgresso()`**

Buscar `function getProgresso`. Logo abaixo, adicionar:
```javascript
function calcProgresso(pbOrArray) {
  const pbs = Array.isArray(pbOrArray) ? pbOrArray : (pbOrArray ? [pbOrArray] : []);
  const ats = pbs.flatMap(pb => pb.atividades || []);
  if (!ats.length) return 0;
  return Math.round(ats.filter(a => a.status === 'concluida').length / ats.length * 100);
}
```

- [ ] **Step 6: Adicionar `getMinhaCarteira()`**

```javascript
function getMinhaCarteira(consultorId) {
  return getClientes().filter(c =>
    (c.ativPlaybooks || []).some(pb => pb.donoId === consultorId)
  );
}
```

- [ ] **Step 7: Adicionar `getStatusCliente()`**

```javascript
function getStatusCliente(cliente, consultorId) {
  const meusPbs   = (cliente.ativPlaybooks || []).filter(pb => pb.donoId === consultorId);
  const atividades = meusPbs.flatMap(pb => pb.atividades || []);
  const hoje  = new Date(); hoje.setHours(0,0,0,0);
  const em7   = new Date(hoje); em7.setDate(em7.getDate() + 7);
  const pend  = atividades.filter(a => a.status !== 'concluida');
  if (pend.some(a => a.dataLimite && new Date(a.dataLimite) < hoje))  return 'atrasado';
  if (pend.some(a => a.dataLimite && new Date(a.dataLimite) <= em7))  return 'atencao';
  if (calcProgresso(meusPbs) < 15) return 'inicio';
  return 'em_ordem';
}
```

- [ ] **Step 8: Adicionar `getKanbanColuna()`**

```javascript
function getKanbanColuna(cliente, consultorId) {
  if (cliente.status === 'cs_ativo') return 'CS Ativo';
  const pb = (cliente.ativPlaybooks || []).find(
    p => p.fase === 'implantacao' && p.donoId === consultorId
  ) || (cliente.ativPlaybooks || [])[0];
  const prog = calcProgresso(pb);
  if (prog < 15) return '1ª Reunião';
  if (prog < 50) return 'Implantação';
  if (prog < 85) return 'Evolução';
  return 'Conclusão';
}
```

- [ ] **Step 9: Testar no console do browser**

```javascript
const c = getClientes()[0];
const cid = getConsultorAtivo();
console.assert(typeof calcProgresso(c.ativPlaybooks) === 'number', 'calcProgresso falhou');
console.assert(typeof getStatusCliente(c, cid) === 'string', 'getStatusCliente falhou');
console.assert(typeof getKanbanColuna(c, cid) === 'string', 'getKanbanColuna falhou');
console.log('Carteira:', getMinhaCarteira(cid).map(x => x.projeto));
```
Esperado: nenhum erro no console.

- [ ] **Step 10: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(cs): seed migration + helpers calcProgresso/getStatusCliente/getKanbanColuna/getMinhaCarteira"
```

---

### Task 2: CSS tokens + sidebar estilo SAG

**Files:**
- Modify: `grv-cs-jornada.html` — bloco `:root {}` e sidebar HTML

**Interfaces:**
- Produz: variáveis `--border-2`, `--b-*-bg`, sidebar branca com nav items SAG

- [ ] **Step 1: Atualizar `:root` com tokens faltantes**

Localizar `:root {`. Verificar e adicionar/corrigir:
```css
:root {
  --primary:      #E05A1E;
  --bg:           #f8f9fb;
  --surface:      #ffffff;
  --border:       #e8ecf0;
  --border-2:     #f0f2f5;   /* NOVO */
  --text:         #1a202c;
  --text2:        #4a5568;
  --text3:        #718096;
  --text4:        #a0aec0;
  --radius:       12px;
  --radius-sm:    9px;
  --green:        #38a169;
  --red:          #e53e3e;
  --yellow:       #d69e2e;
  --blue:         #3182ce;
  --b-green-bg:   #F0FFF4;   /* NOVO */
  --b-red-bg:     #FFF5F5;   /* NOVO */
  --b-orange-bg:  #FFF3EE;   /* NOVO */
  --b-blue-bg:    #EBF8FF;   /* NOVO */
  --sidebar-bg:   #ffffff;
  --sidebar-border: #e8ecf0;
}
```

- [ ] **Step 2: Atualizar CSS da sidebar**

Buscar `.sidebar {` no CSS. Substituir/completar:
```css
.sidebar {
  width: 210px; background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  display: flex; flex-direction: column;
  height: 100%; overflow: hidden; flex-shrink: 0;
}
.sidebar .nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 10px; border-radius: var(--radius-sm);
  font-size: 12px; font-weight: 500; color: var(--text2);
  cursor: pointer; transition: all .12s; margin-bottom: 1px;
}
.sidebar .nav-item:hover   { background: #f7f8fa; color: var(--text); }
.sidebar .nav-item.active  { background: var(--b-orange-bg); color: var(--primary); font-weight: 700; }
.sidebar .nav-icon         { width: 16px; height: 16px; flex-shrink: 0; opacity: 0.45; }
.sidebar .nav-item.active .nav-icon { opacity: 1; }
```

- [ ] **Step 3: Substituir HTML interno da sidebar**

Localizar `<aside class="sidebar"` (ou `id="main-sidebar"`). Substituir o conteúdo interno:
```html
<aside class="sidebar" id="main-sidebar">
  <div style="padding:18px 16px 14px;display:flex;align-items:center;gap:10px;border-bottom:1px solid var(--border-2)">
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
      <rect width="32" height="32" rx="8" fill="#E05A1E"/>
      <text x="16" y="22" text-anchor="middle" font-size="17" font-weight="900" fill="white" font-family="system-ui">G</text>
    </svg>
    <div>
      <div style="font-size:12px;font-weight:700;color:var(--text)">GRV Software</div>
      <div style="font-size:9px;color:var(--text4)">CS · Jornada do Cliente</div>
    </div>
  </div>
  <nav style="padding:10px;flex:1;display:flex;flex-direction:column;gap:1px">
    <div class="nav-item" id="nav-projetos" onclick="navigate('projetos')">
      <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 010 20M12 2a15.3 15.3 0 000 20"/>
      </svg>
      Projetos GRV
    </div>
    <div class="nav-item" id="nav-carteira" onclick="navigate('carteira')">
      <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>
      </svg>
      Minha Carteira
    </div>
    <div class="nav-item" id="nav-criar" onclick="navigate('criar')">
      <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 5v14M5 12h14"/>
      </svg>
      Criar Playbook
    </div>
  </nav>
  <div style="padding:12px 14px;border-top:1px solid var(--border-2)">
    <div style="font-size:9px;text-transform:uppercase;letter-spacing:.08em;color:var(--text4);margin-bottom:5px;font-weight:700">Consultor ativo</div>
    <div style="display:flex;align-items:center;gap:8px;background:#f7f8fa;border-radius:9px;padding:7px 10px">
      <div id="sb-avatar" style="width:26px;height:26px;border-radius:7px;background:linear-gradient(135deg,var(--primary),#ff8c5a);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;color:#fff;flex-shrink:0">?</div>
      <div id="sb-nome" style="font-size:11px;color:var(--text);font-weight:600">—</div>
    </div>
  </div>
</aside>
```

- [ ] **Step 4: Adicionar `setActiveNav()` e `updateSidebarConsultor()`**

Buscar a função que controla o nav ativo (pode ser `setActivePage` ou similar). Adicionar/substituir:
```javascript
function setActiveNav(page) {
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  const el = document.getElementById('nav-' + page);
  if (el) el.classList.add('active');
}

function updateSidebarConsultor() {
  const id = getConsultorAtivo();
  const lista = getConsultores ? getConsultores() : [];
  const c = lista.find(x => x.id === id) || { nome: id };
  const av = document.getElementById('sb-avatar');
  const nm = document.getElementById('sb-nome');
  if (av) av.textContent = (c.nome || id)[0].toUpperCase();
  if (nm) nm.textContent = c.nome || id;
}
```

Garantir que `navigate(page)` chama `setActiveNav(page)` e que `updateSidebarConsultor()` é chamada ao iniciar e ao trocar consultor.

- [ ] **Step 5: Verificar visualmente**

Abrir no browser. Confirmar:
- Sidebar branca com borda direita sutil
- Item ativo em `#FFF3EE` com texto laranja
- Avatar do consultor visível no rodapé

- [ ] **Step 6: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(cs): sidebar estilo SAG + CSS tokens border-2 e b-*-bg"
```

---

### Task 3: Minha Carteira — view Feed

**Files:**
- Modify: `grv-cs-jornada.html` — `renderCarteira()` e CSS

**Interfaces:**
- Consome: `getMinhaCarteira()`, `getStatusCliente()`, `calcProgresso()`
- Produz: `renderFeedCard()`, `renderCarteiraFeed()`, `setCarteiraView()`, `filtrarCarteira()`

- [ ] **Step 1: Adicionar CSS de Feed**

No bloco `<style>`, adicionar:
```css
.feed-wrap { padding: 16px 24px; display: flex; flex-direction: column; gap: 7px; }
.feed-card {
  display: flex; align-items: center; background: var(--surface);
  border-radius: var(--radius); padding: 12px 16px; border: 1px solid var(--border);
  cursor: pointer; transition: border-color .12s, box-shadow .12s;
  position: relative; overflow: hidden;
}
.feed-card:hover { border-color: var(--primary); box-shadow: 0 2px 12px rgba(224,90,30,.08); }
.fc-stripe { position: absolute; left: 0; top: 0; bottom: 0; width: 4px; }
.fc-body   { display: flex; align-items: center; gap: 12px; flex: 1; margin-left: 4px; }
.fc-avatar { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 800; color: #fff; flex-shrink: 0; }
.fc-info   { flex: 1; }
.fc-nome   { font-size: 13px; font-weight: 700; color: var(--text); margin-bottom: 2px; }
.fc-meta   { font-size: 11px; color: var(--text3); }
.fc-right  { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.fc-csat   { font-size: 10px; color: var(--text3); }
.fc-prog   { width: 64px; height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; }
.fc-progbar { height: 4px; border-radius: 2px; }
.status-badge { padding: 3px 10px; border-radius: 20px; font-size: 10px; font-weight: 700; }
.s-atrasado { background: var(--red); }
.s-atencao  { background: var(--yellow); }
.s-em_ordem { background: var(--green); }
.s-inicio   { background: var(--blue); }
.s-cs_ativo { background: var(--primary); }
.b-atrasado { background: var(--b-red-bg);    color: var(--red); }
.b-atencao  { background: #FFFBEB;            color: var(--yellow); }
.b-em_ordem { background: var(--b-green-bg);  color: var(--green); }
.b-inicio   { background: var(--b-blue-bg);   color: var(--blue); }
.b-cs_ativo { background: var(--b-orange-bg); color: var(--primary); }
.view-toggle { display: flex; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); overflow: hidden; }
.vt-btn     { padding: 6px 12px; font-size: 11px; font-weight: 600; border: none; cursor: pointer; display: flex; align-items: center; gap: 5px; background: transparent; color: var(--text3); }
.vt-btn.active { background: var(--b-orange-bg); color: var(--primary); }
```

- [ ] **Step 2: Adicionar helpers `avatarGradiente()` e `statusLabel()`**

```javascript
function avatarGradiente(nome) {
  const paletas = [
    ['#E05A1E','#ff8c5a'],['#2c7a7b','#4fd1c5'],['#553c9a','#9f7aea'],
    ['#1a365d','#4a90d9'],['#276749','#68d391'],['#d69e2e','#f6e05e'],
  ];
  const [a, b] = paletas[(nome||'').charCodeAt(0) % paletas.length];
  return `linear-gradient(135deg,${a},${b})`;
}

const STATUS_LABEL = {
  atrasado:'Atrasado', atencao:'Atenção', em_ordem:'Em ordem',
  inicio:'Início', cs_ativo:'CS Ativo'
};
function statusLabel(s) { return STATUS_LABEL[s] || s; }
```

- [ ] **Step 3: Adicionar `renderFeedCard()`**

```javascript
function renderFeedCard(c, consultorId) {
  const st     = c.status === 'cs_ativo' ? 'cs_ativo' : getStatusCliente(c, consultorId);
  const meusPbs = (c.ativPlaybooks || []).filter(pb => pb.donoId === consultorId);
  const prog   = calcProgresso(meusPbs);
  const pb     = meusPbs[0];
  const fase   = pb ? (pb.titulo || 'Playbook') : '—';
  const csat   = c.csat ? `CSAT ★ ${c.csat}` : 'CSAT —';
  const pColor = st === 'atrasado' ? 'var(--red)' : st === 'atencao' ? 'var(--yellow)' : 'var(--green)';
  return `
    <div class="feed-card" onclick="navigate('cliente/${c.id}')">
      <div class="fc-stripe s-${st}"></div>
      <div class="fc-body">
        <div class="fc-avatar" style="background:${avatarGradiente(c.projeto)}">${(c.projeto||'?')[0].toUpperCase()}</div>
        <div class="fc-info">
          <div class="fc-nome">${c.projeto}</div>
          <div class="fc-meta">${fase} · ${prog}%</div>
        </div>
        <div class="fc-right">
          <span class="status-badge b-${st}">${statusLabel(st)}</span>
          <div class="fc-csat">${csat}</div>
          <div class="fc-prog"><div class="fc-progbar" style="width:${prog}%;background:${pColor}"></div></div>
        </div>
      </div>
    </div>`;
}
```

- [ ] **Step 4: Reescrever `renderCarteira()`**

Localizar `function renderCarteira()`. Substituir por:
```javascript
function renderCarteira() {
  const cid      = getConsultorAtivo();
  const clientes = getMinhaCarteira(cid);
  const view     = localStorage.getItem('grv_cs_carteira_view') || 'feed';
  const atr      = clientes.filter(c => c.status !== 'cs_ativo' && getStatusCliente(c, cid) === 'atrasado').length;
  const sec      = document.getElementById('sec-carteira');
  if (!sec) return;

  sec.innerHTML = `
    <div style="padding:20px 24px 0">
      <div style="font-size:20px;font-weight:800;color:var(--text);margin-bottom:2px">Minha Carteira</div>
      <div style="font-size:12px;color:var(--text3)">${cid} · ${clientes.length} clientes${atr ? ` · <span style="color:var(--red);font-weight:700">${atr} atrasados</span>` : ''}</div>
    </div>
    <div style="padding:12px 24px;display:flex;align-items:center;gap:10px;border-bottom:1px solid var(--border)">
      <div style="flex:1;max-width:260px;display:flex;align-items:center;gap:8px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:7px 12px">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--text4)" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input type="text" placeholder="Buscar cliente..." id="carteira-busca"
          oninput="filtrarCarteira()"
          style="border:none;outline:none;font-size:12px;color:var(--text);width:100%;background:transparent"/>
      </div>
      <select id="carteira-status" onchange="filtrarCarteira()"
        style="border:1px solid var(--border);border-radius:var(--radius-sm);padding:7px 10px;font-size:12px;color:var(--text2);background:var(--surface)">
        <option value="">Todos os status</option>
        <option value="atrasado">Atrasados</option>
        <option value="atencao">Atenção</option>
        <option value="em_ordem">Em ordem</option>
        <option value="inicio">Início</option>
        <option value="cs_ativo">CS Ativo</option>
      </select>
      <div class="view-toggle" style="margin-left:auto">
        <button class="vt-btn ${view==='feed'?'active':''}" onclick="setCarteiraView('feed')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/></svg>
          Feed
        </button>
        <button class="vt-btn ${view==='kanban'?'active':''}" onclick="setCarteiraView('kanban')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="5" height="18" rx="1"/><rect x="10" y="3" width="5" height="13" rx="1"/><rect x="17" y="3" width="5" height="9" rx="1"/></svg>
          Kanban
        </button>
      </div>
    </div>
    <div id="carteira-body">
      ${view === 'feed' ? renderCarteiraFeed(clientes, cid) : renderCarteiraKanban(clientes, cid)}
    </div>`;
}

function setCarteiraView(view) {
  localStorage.setItem('grv_cs_carteira_view', view);
  renderCarteira();
}

function filtrarCarteira() {
  const cid    = getConsultorAtivo();
  let cls      = getMinhaCarteira(cid);
  const busca  = (document.getElementById('carteira-busca')?.value || '').toLowerCase();
  const filtro = document.getElementById('carteira-status')?.value || '';
  if (busca)  cls = cls.filter(c => (c.projeto||'').toLowerCase().includes(busca));
  if (filtro) cls = cls.filter(c => {
    const st = c.status === 'cs_ativo' ? 'cs_ativo' : getStatusCliente(c, cid);
    return st === filtro;
  });
  const view = localStorage.getItem('grv_cs_carteira_view') || 'feed';
  const body = document.getElementById('carteira-body');
  if (body) body.innerHTML = view === 'feed'
    ? renderCarteiraFeed(cls, cid)
    : renderCarteiraKanban(cls, cid);
}

function renderCarteiraFeed(clientes, cid) {
  if (!clientes.length) return '<div style="padding:40px;text-align:center;color:var(--text3)">Nenhum cliente na carteira.</div>';
  return `<div class="feed-wrap">${clientes.map(c => renderFeedCard(c, cid)).join('')}</div>`;
}
```

- [ ] **Step 5: Verificar visualmente**

Abrir no browser → Minha Carteira. Confirmar:
- Cards com stripe colorida por status
- Badge correto (Atrasado / Em ordem / Atenção / Início / CS Ativo)
- Busca filtra em tempo real
- Dropdown de status filtra
- Toggle Feed/Kanban funciona

- [ ] **Step 6: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(carteira): view Feed com stripe, badge status, CSAT, filtros e toggle"
```

---

### Task 4: Minha Carteira — view Kanban

**Files:**
- Modify: `grv-cs-jornada.html` — nova função `renderCarteiraKanban()` e CSS

**Interfaces:**
- Consome: `getKanbanColuna()`, `getStatusCliente()`, `calcProgresso()`
- Produz: 5 colunas com cards rounded + stripe no topo

- [ ] **Step 1: Adicionar CSS de Kanban**

```css
.kanban-wrap { padding: 16px 24px; display: flex; gap: 14px; overflow-x: auto; flex: 1; align-items: flex-start; }
.k-col       { flex-shrink: 0; width: 220px; }
.k-col-head  { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.k-col-lbl   { font-size: 11px; font-weight: 700; color: var(--text2); text-transform: uppercase; letter-spacing: .06em; }
.k-col-cnt   { width: 20px; height: 20px; border-radius: 6px; background: var(--border); display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 800; color: var(--text3); }
.k-card      { background: var(--surface); border-radius: var(--radius); padding: 11px 13px; border: 1px solid var(--border); margin-bottom: 8px; cursor: pointer; transition: border-color .12s; position: relative; overflow: hidden; }
.k-card:hover { border-color: var(--primary); }
.k-stripe    { position: absolute; top: 0; left: 0; right: 0; height: 3px; border-radius: var(--radius) var(--radius) 0 0; }
.k-nome      { font-size: 12px; font-weight: 700; color: var(--text); margin: 7px 0 3px; }
.k-fase      { font-size: 10px; color: var(--text3); margin-bottom: 6px; }
.k-foot      { display: flex; align-items: center; justify-content: space-between; }
.k-pct       { font-size: 10px; font-weight: 700; }
```

- [ ] **Step 2: Adicionar `renderCarteiraKanban()`**

```javascript
const KANBAN_COLUNAS = ['1ª Reunião','Implantação','Evolução','Conclusão','CS Ativo'];

function renderCarteiraKanban(clientes, consultorId) {
  const stripeCol = {
    atrasado:'var(--red)', atencao:'var(--yellow)',
    em_ordem:'var(--green)', inicio:'var(--blue)', cs_ativo:'var(--primary)'
  };

  const cols = KANBAN_COLUNAS.map(col => {
    const items = clientes.filter(c => getKanbanColuna(c, consultorId) === col);
    const cards = items.map(c => {
      const meusPbs = (c.ativPlaybooks || []).filter(pb => pb.donoId === consultorId);
      const prog    = calcProgresso(meusPbs);
      const pb      = meusPbs[0];
      const st      = c.status === 'cs_ativo' ? 'cs_ativo' : getStatusCliente(c, consultorId);
      const pColor  = st === 'atrasado' ? 'var(--red)' : st === 'atencao' ? 'var(--yellow)' : 'var(--green)';
      return `
        <div class="k-card" onclick="navigate('cliente/${c.id}')">
          <div class="k-stripe s-${st}"></div>
          <div class="k-nome">${c.projeto}</div>
          <div class="k-fase">${pb ? pb.titulo : '—'}</div>
          <div class="k-foot">
            <span class="k-pct" style="color:${pColor}">${prog}%</span>
            <span class="status-badge b-${st}">${statusLabel(st)}</span>
          </div>
        </div>`;
    }).join('');
    return `
      <div class="k-col">
        <div class="k-col-head">
          <span class="k-col-lbl">${col}</span>
          <span class="k-col-cnt">${items.length}</span>
        </div>
        ${cards || '<div style="font-size:11px;color:var(--text4);padding:8px 0">Vazio</div>'}
      </div>`;
  }).join('');

  return `<div class="kanban-wrap">${cols}</div>`;
}
```

- [ ] **Step 3: Verificar visualmente**

Clicar em "Kanban" na toolbar. Confirmar:
- 5 colunas na ordem correta
- Clientes nas colunas certas baseado em `calcProgresso()`
- Stripe colorida no topo de cada card
- Click navega para detalhe do cliente

- [ ] **Step 4: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(carteira): view Kanban com 5 colunas por progresso e stripe no topo"
```

---

### Task 5: Overlay de atividade — 3 abas

**Files:**
- Modify: `grv-cs-jornada.html` — CSS, HTML do overlay, JS, `renderAbaAtividades()`

**Interfaces:**
- Consome: `atividade.registros[]`, `atividade.checklist[]`, `atividade.anotacoes[]`
- Produz: `openAtividade(cId, pbId, atId)`, `closeAtividade()`, `setOverlayTab(tab, el)`

- [ ] **Step 1: Adicionar CSS do overlay**

```css
.ov-backdrop { position:fixed;inset:0;background:rgba(15,20,30,.35);z-index:200;opacity:0;pointer-events:none;transition:opacity .2s; }
.ov-backdrop.open { opacity:1;pointer-events:all; }
.ov-panel    { position:fixed;top:0;right:0;bottom:0;width:420px;background:var(--surface);border-left:1px solid var(--border);z-index:201;display:flex;flex-direction:column;transform:translateX(100%);transition:transform .22s cubic-bezier(.4,0,.2,1);box-shadow:-4px 0 24px rgba(0,0,0,.08); }
.ov-panel.open { transform:translateX(0); }
.ov-hd       { padding:14px 16px 0;border-bottom:1px solid var(--border-2);flex-shrink:0; }
.ov-hd-top   { display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:10px; }
.ov-title    { font-size:14px;font-weight:800;color:var(--text);flex:1;margin-right:12px;line-height:1.3; }
.ov-close    { width:28px;height:28px;border-radius:7px;border:1px solid var(--border);background:var(--surface);display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:14px;color:var(--text3);flex-shrink:0; }
.ov-close:hover { background:var(--border-2); }
.ov-meta     { display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap; }
.ov-tabs     { display:flex; }
.ov-tab      { padding:8px 14px;font-size:12px;font-weight:600;color:var(--text3);cursor:pointer;border-bottom:2px solid transparent;transition:all .12s; }
.ov-tab.active { color:var(--primary);border-bottom-color:var(--primary); }
.ov-body     { flex:1;overflow-y:auto;padding:16px; }

/* registro */
.reg-form    { display:flex;gap:8px;margin-bottom:16px; }
.reg-av      { width:28px;height:28px;border-radius:7px;background:linear-gradient(135deg,var(--primary),#ff8c5a);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;color:#fff;flex-shrink:0;margin-top:2px; }
.reg-wrap    { flex:1;background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-sm);padding:8px 12px; }
.reg-ta      { border:none;outline:none;font-size:12px;color:var(--text);background:transparent;width:100%;resize:none;font-family:inherit;min-height:40px; }
.reg-send    { float:right;margin-top:6px;padding:5px 12px;background:var(--primary);color:#fff;border:none;border-radius:7px;font-size:11px;font-weight:700;cursor:pointer; }
.reg-item    { display:flex;gap:10px;margin-bottom:14px; }
.reg-iav     { width:28px;height:28px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:800;color:#fff;flex-shrink:0; }
.reg-ibody   { flex:1; }
.reg-iwho    { font-size:11px;font-weight:700;color:var(--text); }
.reg-iwhen   { font-size:10px;color:var(--text4); }
.reg-itext   { font-size:12px;color:var(--text2);line-height:1.6;margin-top:4px;background:var(--bg);border-radius:8px;padding:8px 10px; }
.reg-event   { display:flex;align-items:center;gap:6px;font-size:11px;color:var(--text3);margin-bottom:12px; }
.reg-dot     { width:6px;height:6px;border-radius:50%;flex-shrink:0; }

/* checklist */
.cl-item  { display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--border-2); }
.cl-check { width:17px;height:17px;border-radius:4px;border:1.5px solid var(--border);display:flex;align-items:center;justify-content:center;flex-shrink:0;cursor:pointer; }
.cl-check.done { background:var(--green);border-color:var(--green);color:#fff;font-size:9px; }
.cl-lbl   { font-size:12px;color:var(--text2);flex:1; }
.cl-lbl.done { text-decoration:line-through;color:var(--text4); }

/* anotação */
.ano-form { background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-sm);padding:10px 12px;margin-bottom:14px; }
.ano-ta   { border:none;outline:none;font-size:12px;color:var(--text);background:transparent;width:100%;resize:none;font-family:inherit;height:70px; }
.ano-card { background:#FFFBEB;border:1px solid #fde68a;border-radius:var(--radius-sm);padding:10px 12px;margin-bottom:8px; }
.ano-date { font-size:10px;color:var(--text4);margin-bottom:4px; }
.ano-text { font-size:12px;color:var(--text2);line-height:1.6; }
```

- [ ] **Step 2: Adicionar HTML do overlay antes de `</body>`**

```html
<div class="ov-backdrop" id="ov-backdrop" onclick="closeAtividade()"></div>
<div class="ov-panel" id="ov-panel">
  <div class="ov-hd">
    <div class="ov-hd-top">
      <div class="ov-title" id="ov-titulo">Atividade</div>
      <div class="ov-close" onclick="closeAtividade()">✕</div>
    </div>
    <div class="ov-meta" id="ov-meta"></div>
    <div class="ov-tabs">
      <div class="ov-tab active" onclick="setOverlayTab('registro',this)">Registro</div>
      <div class="ov-tab" onclick="setOverlayTab('checklist',this)">Checklist</div>
      <div class="ov-tab" onclick="setOverlayTab('anotacao',this)">Anotação</div>
    </div>
  </div>
  <div class="ov-body" id="ov-body"></div>
</div>
```

- [ ] **Step 3: Adicionar globals e funções de abertura/fechamento**

Junto aos outros `let _*` globals:
```javascript
let _ov_cId = null, _ov_pbId = null, _ov_atId = null;
```

```javascript
function openAtividade(cId, pbId, atId) {
  _ov_cId = cId; _ov_pbId = pbId; _ov_atId = atId;
  const c  = getCliente(cId);
  const pb = (c?.ativPlaybooks || []).find(p => p.id === pbId);
  const at = (pb?.atividades || []).find(a => a.id === atId);
  if (!at) return;

  document.getElementById('ov-titulo').textContent = at.titulo || at.nome || '—';

  const stBg  = {concluida:'var(--b-green-bg)',atrasada:'var(--b-red-bg)',pendente:'var(--border-2)',em_andamento:'var(--b-blue-bg)'};
  const stClr = {concluida:'var(--green)',atrasada:'var(--red)',pendente:'var(--text3)',em_andamento:'var(--blue)'};
  const stLbl = {concluida:'Concluída',atrasada:'Atrasada',pendente:'Pendente',em_andamento:'Em andamento'};
  const resp  = at.responsavelId || pb.donoId || '?';

  document.getElementById('ov-meta').innerHTML = `
    <span style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--text2)">
      <span style="width:20px;height:20px;border-radius:5px;background:linear-gradient(135deg,var(--primary),#ff8c5a);display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:800;color:#fff">${resp[0].toUpperCase()}</span>
      ${resp}
    </span>
    <span class="status-badge" style="background:${stBg[at.status]||'var(--border-2)'};color:${stClr[at.status]||'var(--text3)'}">${stLbl[at.status]||at.status}</span>`;

  document.querySelectorAll('.ov-tab').forEach((t,i) => t.classList.toggle('active', i===0));
  renderOverlayTab('registro');
  document.getElementById('ov-backdrop').classList.add('open');
  document.getElementById('ov-panel').classList.add('open');
}

function closeAtividade() {
  document.getElementById('ov-backdrop').classList.remove('open');
  document.getElementById('ov-panel').classList.remove('open');
  _ov_cId = _ov_pbId = _ov_atId = null;
}

function setOverlayTab(tab, el) {
  document.querySelectorAll('.ov-tab').forEach(t => t.classList.remove('active'));
  if (el) el.classList.add('active');
  renderOverlayTab(tab);
}

function renderOverlayTab(tab) {
  const body = document.getElementById('ov-body');
  if (!body) return;
  if (tab === 'registro')  body.innerHTML = renderOvRegistro();
  if (tab === 'checklist') body.innerHTML = renderOvChecklist();
  if (tab === 'anotacao')  body.innerHTML = renderOvAnotacao();
}
```

- [ ] **Step 4: Adicionar `renderOvRegistro()` e `addRegistroAtividade()`**

```javascript
function renderOvRegistro() {
  const c  = getCliente(_ov_cId);
  const pb = (c?.ativPlaybooks||[]).find(p=>p.id===_ov_pbId);
  const at = (pb?.atividades||[]).find(a=>a.id===_ov_atId);
  if (!at) return '';
  const cid = getConsultorAtivo();
  const itens = (at.registros||[]).map(r => r.tipo === 'evento'
    ? `<div class="reg-event"><span class="reg-dot" style="background:var(--green)"></span>${r.texto}<span style="margin-left:auto;font-size:10px;color:var(--text4)">${r.data}</span></div>`
    : `<div class="reg-item">
        <div class="reg-iav" style="background:linear-gradient(135deg,var(--primary),#ff8c5a)">${(r.autor||'?')[0].toUpperCase()}</div>
        <div class="reg-ibody">
          <div style="display:flex;justify-content:space-between"><div class="reg-iwho">${r.autor}</div><div class="reg-iwhen">${r.data}</div></div>
          <div class="reg-itext">${r.texto}</div>
        </div>
      </div>`
  ).join('');
  return `
    <div class="reg-form">
      <div class="reg-av">${cid[0].toUpperCase()}</div>
      <div class="reg-wrap">
        <textarea class="reg-ta" id="ov-reg-input" placeholder="Adicionar registro..."></textarea>
        <button class="reg-send" onclick="addRegistroAtividade()">Registrar</button>
      </div>
    </div>
    ${itens||'<p style="font-size:12px;color:var(--text4);text-align:center;padding:20px">Nenhum registro ainda.</p>'}`;
}

function addRegistroAtividade() {
  const texto = document.getElementById('ov-reg-input')?.value?.trim();
  if (!texto) return;
  const c  = getCliente(_ov_cId);
  const pb = (c?.ativPlaybooks||[]).find(p=>p.id===_ov_pbId);
  const at = (pb?.atividades||[]).find(a=>a.id===_ov_atId);
  if (!at) return;
  if (!at.registros) at.registros = [];
  const agora = new Date();
  at.registros.unshift({
    id:'r-'+Date.now(), autor:getConsultorAtivo(), tipo:'manual',
    data: agora.toLocaleDateString('pt-BR')+' · '+agora.getHours()+'h'+String(agora.getMinutes()).padStart(2,'0'),
    texto
  });
  saveCliente(c);
  renderOverlayTab('registro');
}
```

- [ ] **Step 5: Adicionar `renderOvChecklist()`, `toggleChecklistItem()`, `addChecklistItem()`**

```javascript
function renderOvChecklist() {
  const c  = getCliente(_ov_cId);
  const pb = (c?.ativPlaybooks||[]).find(p=>p.id===_ov_pbId);
  const at = (pb?.atividades||[]).find(a=>a.id===_ov_atId);
  if (!at) return '';
  const items = at.checklist||[];
  const feitos = items.filter(i=>i.done).length;
  const pct    = items.length ? Math.round(feitos/items.length*100) : 0;
  const lista  = items.map((item,idx)=>`
    <div class="cl-item">
      <div class="cl-check ${item.done?'done':''}" onclick="toggleChecklistItem(${idx})">${item.done?'✓':''}</div>
      <span class="cl-lbl ${item.done?'done':''}">${item.texto}</span>
    </div>`).join('');
  return `
    <div style="font-size:11px;color:var(--text4);margin-bottom:8px">${feitos} de ${items.length} itens concluídos</div>
    <div style="width:100%;height:4px;background:var(--border);border-radius:2px;margin-bottom:16px;overflow:hidden">
      <div style="width:${pct}%;height:100%;background:var(--green);border-radius:2px"></div>
    </div>
    ${lista}
    <div style="margin-top:10px;display:flex;gap:8px">
      <input id="cl-novo" type="text" placeholder="Novo item..."
        style="flex:1;border:1px solid var(--border);border-radius:7px;padding:7px 10px;font-size:12px;outline:none"
        onkeydown="if(event.key==='Enter')addChecklistItem()"/>
      <button onclick="addChecklistItem()" style="padding:7px 12px;background:var(--primary);color:#fff;border:none;border-radius:7px;font-size:11px;font-weight:700;cursor:pointer">+</button>
    </div>`;
}

function toggleChecklistItem(idx) {
  const c  = getCliente(_ov_cId);
  const pb = (c?.ativPlaybooks||[]).find(p=>p.id===_ov_pbId);
  const at = (pb?.atividades||[]).find(a=>a.id===_ov_atId);
  if (!at?.checklist?.[idx]) return;
  at.checklist[idx].done = !at.checklist[idx].done;
  saveCliente(c);
  renderOverlayTab('checklist');
}

function addChecklistItem() {
  const input = document.getElementById('cl-novo');
  const texto = input?.value?.trim();
  if (!texto) return;
  const c  = getCliente(_ov_cId);
  const pb = (c?.ativPlaybooks||[]).find(p=>p.id===_ov_pbId);
  const at = (pb?.atividades||[]).find(a=>a.id===_ov_atId);
  if (!at) return;
  if (!at.checklist) at.checklist = [];
  at.checklist.push({id:'cl-'+Date.now(), texto, done:false});
  saveCliente(c);
  renderOverlayTab('checklist');
}
```

- [ ] **Step 6: Adicionar `renderOvAnotacao()` e `addAnotacaoAtividade()`**

```javascript
function renderOvAnotacao() {
  const c  = getCliente(_ov_cId);
  const pb = (c?.ativPlaybooks||[]).find(p=>p.id===_ov_pbId);
  const at = (pb?.atividades||[]).find(a=>a.id===_ov_atId);
  if (!at) return '';
  const notas = (at.anotacoes||[]).map(n=>`
    <div class="ano-card">
      <div class="ano-date">${n.data} · ${n.autor}</div>
      <div class="ano-text">${n.texto}</div>
    </div>`).join('');
  return `
    <div class="ano-form">
      <textarea class="ano-ta" id="ov-ano-input" placeholder="Escreva uma anotação privada..."></textarea>
      <div style="text-align:right;margin-top:6px">
        <button onclick="addAnotacaoAtividade()" style="padding:6px 14px;background:var(--primary);color:#fff;border:none;border-radius:8px;font-size:11px;font-weight:700;cursor:pointer">Salvar</button>
      </div>
    </div>
    ${notas||'<p style="font-size:12px;color:var(--text4);text-align:center;padding:20px">Nenhuma anotação ainda.</p>'}`;
}

function addAnotacaoAtividade() {
  const texto = document.getElementById('ov-ano-input')?.value?.trim();
  if (!texto) return;
  const c  = getCliente(_ov_cId);
  const pb = (c?.ativPlaybooks||[]).find(p=>p.id===_ov_pbId);
  const at = (pb?.atividades||[]).find(a=>a.id===_ov_atId);
  if (!at) return;
  if (!at.anotacoes) at.anotacoes = [];
  at.anotacoes.unshift({
    id:'ano-'+Date.now(), autor:getConsultorAtivo(),
    data: new Date().toLocaleDateString('pt-BR'), texto
  });
  saveCliente(c);
  renderOverlayTab('anotacao');
}
```

- [ ] **Step 7: Atualizar `renderAbaAtividades()` para usar `openAtividade()`**

Localizar `function renderAbaAtividades(c)`. Nas linhas que geram cada linha de atividade (buscar `at-row` ou similar), substituir o `onclick` de cada atividade:

```javascript
// Antes (exemplo):
onclick="selecionarAtividade('${at.id}')"

// Depois:
onclick="openAtividade('${c.id}','${pb.id}','${at.id}')"
```

Também adicionar o responsável na linha da atividade:
```javascript
// Adicionar após o nome da atividade na linha:
`<span style="font-size:10px;color:var(--text4);margin-left:auto">${at.responsavelId||pb.donoId||'—'}</span>`
```

- [ ] **Step 8: Verificar overlay completo**

Cliente → Atividades → clicar em qualquer linha. Confirmar:
- Painel desliza da direita com animação suave
- Backdrop escurece o fundo; click no backdrop fecha
- Header: título correto + responsável + badge de status
- Aba Registro: campo de texto + botão + lista de registros
- Aba Checklist: progress bar + itens toggle + campo novo item
- Aba Anotação: textarea + cards amarelos
- Fechar com ✕ funciona

- [ ] **Step 9: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(atividade): overlay slide-over com abas Registro/Checklist/Anotação"
```

---

### Task 6: Auto-advance Implantação → CS Ativo

**Files:**
- Modify: `grv-cs-jornada.html` — `checkTask()` e novas funções

**Interfaces:**
- Consome: `cliente.status`, `ativPlaybook.fase`, `atividade.status`
- Produz: `checkImplantacaoConcluida(clienteId)`, `confirmarCSAtivo(clienteId)`

- [ ] **Step 1: Adicionar `checkImplantacaoConcluida()`**

Localizar `function checkTask(`. Logo acima, adicionar:
```javascript
function checkImplantacaoConcluida(clienteId) {
  const c = getCliente(clienteId);
  if (c.status === 'cs_ativo') return;
  const cid    = getConsultorAtivo();
  const pbsImpl = (c.ativPlaybooks||[]).filter(pb => pb.fase==='implantacao' && pb.donoId===cid);
  if (!pbsImpl.length) return;
  const todas = pbsImpl.flatMap(pb => pb.atividades||[]);
  if (!todas.length || !todas.every(a => a.status==='concluida')) return;

  showToast(
    '🎉 Implantação concluída! ' +
    `<button onclick="confirmarCSAtivo('${clienteId}')" ` +
    `style="margin-left:8px;padding:3px 10px;background:#fff;color:var(--green);border:none;border-radius:6px;font-weight:700;cursor:pointer;font-size:11px">Mover para CS Ativo</button>`,
    6000
  );
}
```

- [ ] **Step 2: Adicionar `confirmarCSAtivo()`**

```javascript
function confirmarCSAtivo(clienteId) {
  const c = getCliente(clienteId);
  c.status       = 'cs_ativo';
  c.dataInicioCS = new Date().toISOString();
  if (!c.historicoEtapas) c.historicoEtapas = [];
  c.historicoEtapas.push({
    etapa: 'cs_ativo', autor: getConsultorAtivo(),
    data:  new Date().toISOString(), tipo: 'evento',
    texto: 'Implantação encerrada — cliente movido para CS Ativo',
  });
  (c.ativPlaybooks||[]).filter(pb=>pb.fase==='implantacao').forEach(pb=>pb.encerrado=true);
  saveCliente(c);
  showToast('✅ ' + c.projeto + ' agora está em CS Ativo!', 3000);
  if (_cliente_id_atual === clienteId) renderCliente(clienteId);
  else renderCarteira();
}
```

- [ ] **Step 3: Chamar `checkImplantacaoConcluida()` em `checkTask()`**

Localizar `function checkTask(`. Identificar onde `saveCliente(c)` é chamado após marcar a atividade. Logo após esse save, adicionar:
```javascript
checkImplantacaoConcluida(clienteId);   // ou o nome do parâmetro que a função recebe
```

- [ ] **Step 4: Marcar playbook encerrado como read-only**

Em `renderAbaAtividades(c)`, ao montar o header do painel direito, verificar `pb.encerrado`:
```javascript
const btnAdd = pb.encerrado
  ? `<span style="font-size:10px;padding:3px 8px;background:var(--border-2);color:var(--text3);border-radius:6px">Encerrado</span>`
  : `<button class="btn-sm btn-primary" onclick="abrirFormAtividade('${c.id}','${pb.id}')">+ Atividade</button>`;
```

- [ ] **Step 5: Verificar auto-advance**

Marcar todas as atividades de um cliente como `concluida`. Confirmar:
- Toast aparece com botão "Mover para CS Ativo"
- Clicar move o cliente: `status === 'cs_ativo'`
- Cliente aparece na coluna "CS Ativo" no Kanban
- Playbook mostra badge "Encerrado" (sem botão "+ Atividade")

- [ ] **Step 6: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(lifecycle): implantacao concluida → toast → cs_ativo com historicoEtapas"
```

---

### Task 7: Visão 360° histórico + Projetos GRV KPIs

**Files:**
- Modify: `grv-cs-jornada.html` — `renderAba360()` e `renderProjetosGRV()`

**Interfaces:**
- Consome: `cliente.status`, `cliente.dataInicioImplantacao`, `cliente.dataInicioCS`
- Produz: `tempoComoCliente(dataInicio)`, bloco histórico na 360°, KPIs atualizados

- [ ] **Step 1: Adicionar `tempoComoCliente()`**

```javascript
function tempoComoCliente(dataInicio) {
  if (!dataInicio) return '—';
  const meses = (d => {
    const n = new Date(), i = new Date(d);
    return (n.getFullYear()-i.getFullYear())*12 + n.getMonth()-i.getMonth();
  })(dataInicio);
  if (meses < 1)  return 'Menos de 1 mês';
  if (meses < 12) return meses + (meses===1?' mês':' meses');
  const a = Math.floor(meses/12), m = meses%12;
  return a+(a===1?' ano':' anos')+(m?' e '+m+(m===1?' mês':' meses'):'');
}
```

- [ ] **Step 2: Atualizar `renderAba360(c)` com bloco histórico**

Localizar `function renderAba360(c)`. No final do HTML gerado (antes do `return`), adicionar bloco condicional:
```javascript
const historicoHTML = c.status === 'cs_ativo' ? `
  <div style="background:var(--b-orange-bg);border:1px solid #fed7aa;border-radius:var(--radius);padding:14px 16px;margin-top:14px">
    <div style="font-size:10px;font-weight:700;color:var(--text4);text-transform:uppercase;letter-spacing:.07em;margin-bottom:10px">Histórico</div>
    <div style="display:flex;gap:24px;flex-wrap:wrap">
      <div>
        <div style="font-size:10px;color:var(--text3)">Início da implantação</div>
        <div style="font-size:13px;font-weight:700;color:var(--text)">${c.dataInicioImplantacao ? new Date(c.dataInicioImplantacao).toLocaleDateString('pt-BR') : '—'}</div>
      </div>
      <div>
        <div style="font-size:10px;color:var(--text3)">Entrada no CS</div>
        <div style="font-size:13px;font-weight:700;color:var(--primary)">${c.dataInicioCS ? new Date(c.dataInicioCS).toLocaleDateString('pt-BR') : '—'}</div>
      </div>
      <div>
        <div style="font-size:10px;color:var(--text3)">Tempo como cliente</div>
        <div style="font-size:13px;font-weight:700;color:var(--text)">${tempoComoCliente(c.dataInicioImplantacao)}</div>
      </div>
    </div>
  </div>` : '';
```
Incluir `${historicoHTML}` no HTML retornado pela função.

- [ ] **Step 3: Atualizar KPIs do Projetos GRV**

Localizar `function renderProjetosGRV()`. Atualizar os cálculos dos KPIs:
```javascript
const todosClientes = getClientes();
const totalAtivos   = todosClientes.length;
const csats         = todosClientes.filter(c=>c.csat).map(c=>c.csat);
const csatMedio     = csats.length ? (csats.reduce((s,v)=>s+v,0)/csats.length).toFixed(1) : '—';
const atrasados     = todosClientes.filter(c =>
  c.status !== 'cs_ativo' && getStatusCliente(c, c.csId) === 'atrasado'
).length;
const progressos    = todosClientes.map(c => calcProgresso(c.ativPlaybooks||[]));
const progMedio     = progressos.length ? Math.round(progressos.reduce((s,v)=>s+v,0)/progressos.length) : 0;
```
Substituir os valores hardcoded dos 4 KPI cards por `totalAtivos`, `csatMedio`, `atrasados`, `progMedio`.

- [ ] **Step 4: Verificar**

- Cliente com `status='cs_ativo'` → aba 360° mostra bloco laranja com datas e tempo como cliente
- Cliente em implantação → bloco histórico não aparece
- Projetos GRV → KPIs refletem dados reais do seed

- [ ] **Step 5: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(360+projetos): histórico cs_ativo na 360° e KPIs com novo modelo de dados"
```

---

## Self-Review

**Spec coverage:**
- [x] Sidebar SAG → Task 2
- [x] CSS tokens `--border-2`, `--b-*-bg` → Task 2
- [x] `getMinhaCarteira()` filtra por `donoId` → Task 1
- [x] `getStatusCliente()` com regras Atenção/Início → Task 1
- [x] `getKanbanColuna()` com faixas de progresso → Task 1
- [x] Feed view com stripe + badge + CSAT → Task 3
- [x] View Jornada removida (só feed/kanban) → Task 3
- [x] Kanban 5 colunas → Task 4
- [x] Overlay Registro/Checklist/Anotação → Task 5
- [x] Responsável na linha de atividade → Task 5
- [x] Auto-advance implantação → cs_ativo → Task 6
- [x] `historicoEtapas` preservado → Task 6
- [x] Playbook encerrado read-only → Task 6
- [x] 360° histórico para cs_ativo → Task 7
- [x] Projetos GRV KPIs atualizados → Task 7
- [x] Migração seed: donoId, fase, responsavelId, checklist, anotacoes → Task 1

**Placeholders:** Nenhum TBD, nenhum "similar ao Task N".

**Consistência de tipos:**
- `calcProgresso(pbOrArray)` — Task 1 define, Tasks 3/4/5/7 consomem ✓
- `getStatusCliente(c, consultorId)` — Task 1 define, Tasks 3/4/7 consomem ✓
- `getKanbanColuna(c, consultorId)` — Task 1 define, Task 4 consome ✓
- `openAtividade(cId, pbId, atId)` — Task 5 define e Task 5 chama ✓
- `confirmarCSAtivo(clienteId)` — Task 6 define, chamada do toast em Task 6 ✓
- `tempoComoCliente(dataInicio)` — Task 7 define e usa ✓
