# Design Uplift GRV CS — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir os tokens visuais do GRV CS Jornada por uma paleta warm stone coerente, unificar 7 padrões de KPI card em 1, adicionar sistema de elevação com 3 níveis de sombra, implementar micro-interações de hover, substituir emoji por SVG em toda a UI.

**Architecture:** Tudo vive em `grv-cs-jornada.html` (single-file SPA). Mudanças de CSS são localizadas no bloco `<style>` no topo. Mudanças de HTML acontecem dentro das funções JS de render (que constroem strings HTML). Nenhuma estrutura de rota, dado ou lógica de negócio é alterada.

**Tech Stack:** HTML/CSS/JS puro. Sem build system, sem dependências (exceto Chart.js já carregado). Teste = abrir no navegador e verificar visualmente.

## Global Constraints

- Arquivo único: `grv-cs-jornada.html` na raiz do projeto — todas as edições vão aqui.
- Branch de trabalho: `alteracoes` — nunca commitar em `main`.
- Não alterar: estrutura de rotas, funções de dados, lógica de playbooks, o `.vg-card` (dark gradient card já bem executado).
- `--primary: #E05A1E` — manter sem alteração.
- Commits frequentes por task concluída.
- Verificação = abrir o arquivo no Chrome (File → Open, ou arrastar) e navegar até a tela indicada.

---

### Task 1: Warm stone palette + sistema de sombras (`:root`)

**Files:**
- Modify: `grv-cs-jornada.html` — bloco `:root` (linhas 9–35), sombras em seletores de modal/dropdown (~linhas 425, 449, 508, 55)

**Interfaces:**
- Produces: tokens `--bg`, `--border`, `--border-2`, `--text`, `--text2`, `--text3`, `--text4`, `--shadow` (alias), `--shadow-1`, `--shadow-2`, `--shadow-3`, `--radius: 10px`, `--radius-sm: 6px` — usados por todas as tasks seguintes.

- [ ] **Step 1: Substituir tokens de cor no `:root`**

Localizar o bloco `:root {` no topo do `<style>`. Substituir as seguintes linhas (manter as demais intactas):

```css
/* ANTES */
  --bg: #f8f9fb;
  --surface: #ffffff;
  --border: #e8ecf0;
  --border-2: #f0f2f5;
  --text: #1a202c;
  --text2: #4a5568;
  --text3: #718096;
  --text4: #a0aec0;
  --radius: 9px;
  --radius-sm: 7px;
  --shadow: 0 1px 3px rgba(0,0,0,.07), 0 1px 2px rgba(0,0,0,.05);

/* DEPOIS */
  --bg: #F5F3F0;
  --surface: #ffffff;
  --border: #E2DDD7;
  --border-2: #EDE9E4;
  --text: #1A1917;
  --text2: #534E4A;
  --text3: #8A847F;
  --text4: #B5AFA9;
  --radius: 10px;
  --radius-sm: 6px;
  --shadow:   0 1px 3px rgba(0,0,0,.05), 0 1px 2px rgba(0,0,0,.04);
  --shadow-1: 0 1px 3px rgba(0,0,0,.05), 0 1px 2px rgba(0,0,0,.04);
  --shadow-2: 0 4px 14px rgba(0,0,0,.08), 0 2px 4px rgba(0,0,0,.04);
  --shadow-3: 0 12px 32px rgba(0,0,0,.12), 0 4px 8px rgba(0,0,0,.06);
```

- [ ] **Step 2: Atualizar sombra do modal (`.modal-box`)**

Localizar `.modal-box` (~linha 425). Substituir `box-shadow:0 8px 30px rgba(0,0,0,.2)` por `box-shadow:var(--shadow-3)`.

- [ ] **Step 3: Atualizar sombra de popovers (`.proj-pop`, `.nav-dropdown`)**

Localizar `.nav-dropdown` (~linha 55):
```css
/* ANTES */
box-shadow:0 4px 16px rgba(0,0,0,.12)
/* DEPOIS */
box-shadow:var(--shadow-2)
```

Localizar `.proj-pop` (~linha 449):
```css
/* ANTES */
box-shadow:0 8px 32px rgba(0,0,0,.13),0 2px 8px rgba(0,0,0,.07)
/* DEPOIS */
box-shadow:var(--shadow-2)
```

- [ ] **Step 4: Atualizar sombra do activity overlay (`.ov-panel`)**

Localizar `.ov-panel` (~linha 508). Substituir `box-shadow:-4px 0 24px rgba(0,0,0,.08)` por `box-shadow:var(--shadow-2)`.

- [ ] **Step 5: Corrigir hover hardcoded na `.lista-section-hdr`**

Localizar `.lista-section-hdr:hover{background:#f9fafb}` (~linha 632). Substituir por:
```css
.lista-section-hdr:hover{background:var(--surface-2,#FAF9F8)}
```

- [ ] **Step 6: Verificar visualmente**

Abrir `grv-cs-jornada.html` no Chrome. Verificar:
- Background da página: tom warm/bege em vez de azulado frio
- Bordas dos cards: tom warm (levemente acastanhado) em vez de azul-cinza
- Abrir modal de alteração de etapa: sombra mais profunda e definida
- Abrir dropdown do nav (hover em "Projetos GRV"): sombra mais suave que antes

- [ ] **Step 7: Commit**

```
git add grv-cs-jornada.html
git commit -m "style(tokens): warm stone palette, 3-level shadow system, radius 10px"
```

---

### Task 2: KPI card canônico — CSS + Painel de Atividades

**Files:**
- Modify: `grv-cs-jornada.html` — CSS block (~linha 712), função `mkKpiCard()` (~linha 3440), media query (~linha 748)

**Interfaces:**
- Consumes: tokens `--surface`, `--border`, `--shadow-1`, `--text4`, `--text3`, `--red`, `--yellow`, `--primary`, `--green` da Task 1.
- Produces: classe CSS `.kpi-card` + variantes `.kpi-card.v-red/v-amber/v-orange/v-green`; função `mkKpiCard()` gera HTML com essas classes.

- [ ] **Step 1: Adicionar CSS do `.kpi-card` canônico**

Logo após `.painel-kpi-strip{...}` (~linha 712), adicionar o bloco:

```css
/* ── KPI CARD — padrão unificado ── */
.kpi-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:18px}
.kpi-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px 16px;box-shadow:var(--shadow-1)}
.kpi-card .kpi-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text4);margin-bottom:8px}
.kpi-card .kpi-value{font-size:32px;font-weight:800;line-height:1;letter-spacing:-1.2px;font-variant-numeric:tabular-nums}
.kpi-card .kpi-sublabel{font-size:11px;color:var(--text3);margin-top:3px}
.kpi-card.v-red    .kpi-value{color:var(--red)}
.kpi-card.v-amber  .kpi-value{color:var(--yellow)}
.kpi-card.v-orange .kpi-value{color:var(--primary)}
.kpi-card.v-green  .kpi-value{color:var(--green)}
@media(max-width:640px){.kpi-strip{grid-template-columns:repeat(2,1fr)}}
```

- [ ] **Step 2: Atualizar `mkKpiCard()` para gerar o novo HTML**

Localizar a função `mkKpiCard` (~linha 3440):

```javascript
// ANTES
function mkKpiCard(label, value, color, sub) {
  return '<div class="painel-kpi-card">' +
    '<div class="painel-kpi-label">' + label + '</div>' +
    '<div class="painel-kpi-value" style="color:' + color + '">' + value + '</div>' +
    '<div class="painel-kpi-sub">' + sub + '</div>' +
  '</div>';
}
```

Substituir por:

```javascript
function mkKpiCard(label, value, colorVar, sub) {
  var variantMap = {
    '#dc2626':'v-red','var(--red)':'v-red',
    '#eab308':'v-amber','var(--yellow)':'v-amber',
    'var(--primary)':'v-orange',
    '#22c55e':'v-green','var(--green)':'v-green'
  };
  var cls = variantMap[colorVar] || 'v-orange';
  return '<div class="kpi-card ' + cls + '">' +
    '<div class="kpi-label">' + label + '</div>' +
    '<div class="kpi-value">' + value + '</div>' +
    '<div class="kpi-sublabel">' + sub + '</div>' +
  '</div>';
}
```

- [ ] **Step 3: Trocar classe wrapper no `renderVencimentos()`**

Localizar (~linha 3396):
```javascript
// ANTES
var kpiHtml = '<div class="painel-kpi-strip">' +
// DEPOIS
var kpiHtml = '<div class="kpi-strip">' +
```

- [ ] **Step 4: Verificar visualmente**

Navegar para "Painel de Atividades" no app. Verificar:
- 4 KPI cards aparecem alinhados em grid
- Labels em caps 10px, valores grandes, sublabels menores
- Cores semânticas corretas (vermelho para Críticas, amarelo para Hoje, etc.)

- [ ] **Step 5: Commit**

```
git add grv-cs-jornada.html
git commit -m "style(kpi-card): padrão unificado substitui painel-kpi-card"
```

---

### Task 3: KPI card canônico — Dashboard (Projetos GRV)

**Files:**
- Modify: `grv-cs-jornada.html` — função `renderDashboardKpisHtml()` (~linha 2421), CSS `.dash-kpi-*` (~linhas 263–269)

**Interfaces:**
- Consumes: `.kpi-card` e variantes definidos na Task 2.
- Produces: Dashboard com KPI cards no padrão unificado.

- [ ] **Step 1: Entender a estrutura atual do dashboard KPI**

A função gera 7 cards com `dash-kpi-card`, `dash-kpi-label`, `dash-kpi-value`. O array `cards` (~linha 2395) define `label`, `color`, `cls` (ex: `kpi-atrasado`) e `drill`.

- [ ] **Step 2: Substituir HTML do `renderDashboardKpisHtml()`**

Localizar (~linha 2421):
```javascript
// ANTES
return `<div class="dash-kpi-row">
    ${cards.map((c,i) => `
      <div class="dash-kpi-card ${c.cls}" onclick="drillKpi('${c.drill}')" title="Ver lista: ${c.label}" style="cursor:pointer">
        <div class="dash-kpi-label">${c.label}</div>
        <div class="dash-kpi-value" id="kpi-v-${i}" style="color:${c.color}">0</div>
      </div>`).join('')}
  </div>`;

// DEPOIS
```

Primeiro, adicionar a propriedade `variant` a cada objeto no array `cards` (~linha 2395). Localizar onde `cards` é definido — o array de objetos com `{label, color, cls, drill}` — e adicionar `variant`:

```javascript
// No array cards, mapear color → variant:
// '#718096' → 'v-gray' (sem variante de cor — usar text3)
// '#e53e3e' → 'v-red'
// '#d69e2e' → 'v-amber'
// '#38a169' → 'v-green'
// '#3182ce' → 'v-blue'
// var(--primary) → 'v-orange'
```

Substitua o template do return por:

```javascript
return `<div class="kpi-strip" style="grid-template-columns:repeat(7,1fr);gap:12px;margin-bottom:24px">
    ${cards.map((c,i) => {
      const vMap = {'#e53e3e':'v-red','#d69e2e':'v-amber','#38a169':'v-green','#3182ce':'v-blue','var(--primary)':'v-orange'};
      const v = vMap[c.color] || '';
      return `<div class="kpi-card ${v}" onclick="drillKpi('${c.drill}')" title="Ver lista: ${c.label}" style="cursor:pointer">
        <div class="kpi-label">${c.label}</div>
        <div class="kpi-value" id="kpi-v-${i}">0</div>
      </div>`;
    }).join('')}
  </div>`;
```

Nota: não existe `.kpi-card.v-blue` no CSS ainda — adicionar ao bloco de Task 2:
```css
.kpi-card.v-blue   .kpi-value{color:var(--blue)}
```

- [ ] **Step 3: Verificar visualmente**

Navegar para "Projetos GRV" → Dashboard. Verificar:
- 7 KPI cards em linha horizontal com novo padrão visual
- Animação de countUp ainda funciona (os IDs `kpi-v-0` a `kpi-v-6` continuam presentes)
- Cores semânticas corretas

- [ ] **Step 4: Commit**

```
git add grv-cs-jornada.html
git commit -m "style(dashboard): KPI cards migrados para padrão unificado .kpi-card"
```

---

### Task 4: Micro-interações — nav hover, feed cards, kanban cards

**Files:**
- Modify: `grv-cs-jornada.html` — CSS `.nav-item:hover` (~linha 47), `.feed-card:hover` (~linha 469), `.kcard:hover` (~linha 613)

**Interfaces:**
- Consumes: `--shadow-2` da Task 1.
- Produces: interface que "responde" ao cursor em 3 pontos críticos.

- [ ] **Step 1: Nav item hover com tint sutil**

Localizar `.nav-item:hover{background:none;color:var(--text)}` (~linha 47). Substituir por:

```css
.nav-item:hover{background:rgba(0,0,0,.03);color:var(--text)}
```

- [ ] **Step 2: Feed card hover com lift**

Localizar `.feed-card:hover{border-color:var(--primary);box-shadow:0 2px 12px rgba(224,90,30,.08)}` (~linha 469). Substituir por:

```css
.feed-card:hover{border-color:var(--primary);box-shadow:var(--shadow-2);transform:translateY(-1px)}
```

Adicionar `transition` no `.feed-card` base (~linha 468):
```css
/* ANTES */
.feed-card{display:flex;align-items:center;background:var(--surface);border-radius:var(--radius);padding:12px 16px;border:1px solid var(--border);cursor:pointer;transition:border-color .12s,box-shadow .12s;position:relative;overflow:hidden}
/* DEPOIS — adicionar transform na transition */
.feed-card{display:flex;align-items:center;background:var(--surface);border-radius:var(--radius);padding:12px 16px;border:1px solid var(--border);cursor:pointer;transition:border-color .12s,box-shadow .12s,transform .1s;position:relative;overflow:hidden}
```

- [ ] **Step 3: Kanban card hover com shadow-2**

Localizar `.kcard:hover{border-color:var(--primary);box-shadow:0 2px 8px rgba(224,90,30,.12)}` (~linha 613). Substituir por:

```css
.kcard:hover{border-color:var(--primary);box-shadow:var(--shadow-2);transform:translateY(-1px)}
```

Adicionar `transform` na transition base do `.kcard`:
```css
/* ANTES */
.kcard{...;transition:border-color .15s,box-shadow .15s,opacity .15s}
/* DEPOIS */
.kcard{...;transition:border-color .15s,box-shadow .15s,opacity .15s,transform .1s}
```

- [ ] **Step 4: Botão Concluir — glow verde em vez de dim**

Localizar `.venc-btn-ok:hover{opacity:.88}` (~linha 705). Substituir por:

```css
.venc-btn-ok:hover{opacity:1;box-shadow:0 2px 8px rgba(22,163,74,.35)}
```

- [ ] **Step 5: Verificar visualmente**

Verificar em 3 pontos:
1. Passar mouse nos itens do nav (Projetos, Minha Carteira, etc.) — fundo levemente escurece
2. Hover em um feed card (Minha Carteira): sobe 1px visivelmente
3. Hover em um kanban card: sobe 1px
4. Hover no botão "✓ Concluir" (Painel de Atividades): brilho verde em vez de escurecer

- [ ] **Step 6: Commit**

```
git add grv-cs-jornada.html
git commit -m "style(interactions): nav hover tint, feed/kanban card lift, Concluir glow"
```

---

### Task 5: SVG icons nas activity rows (Painel de Atividades)

**Files:**
- Modify: `grv-cs-jornada.html` — função `mkResolverRow()` (~linha 3474), CSS `.painel-due-*` (~linha 725)

**Interfaces:**
- Consumes: `--red`, `--yellow`, `--primary`, cores semânticas.
- Produces: rows de atividade com ícone SVG por tipo, stripe lateral de criticidade como CSS class (sem inline style), badges de prazo com cores corretas.

- [ ] **Step 1: Substituir mapa de emoji por SVG em `mkResolverRow()`**

Localizar (~linha 3474):
```javascript
var tipoIcons = { reuniao:'📞', treinamento:'🎓', relatorio:'📊', qbr:'📋', pesquisa:'⭐', followup:'📩' };
var icon = tipoIcons[v.at.tipo || ''] || '📋';
```

Substituir por:

```javascript
var tipoIcons = {
  reuniao:    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>',
  treinamento:'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>',
  relatorio:  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
  qbr:        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1"/></svg>',
  pesquisa:   '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
  followup:   '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>'
};
var defaultIcon = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1"/></svg>';
var icon = tipoIcons[v.at.tipo || ''] || defaultIcon;
```

- [ ] **Step 2: Substituir o span de emoji pelo ícone SVG com contêiner estilizado**

Localizar (~linha 3487) a linha que usa `icon` na row:
```javascript
// ANTES
'<span style="font-size:15px;flex-shrink:0">' + icon + '</span>'

// DEPOIS
'<div class="venc-row-icon" style="width:30px;height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;background:var(--bg);color:var(--text3)">' + icon + '</div>'
```

- [ ] **Step 3: Corrigir cores dos badges `.painel-due-*` para usar tokens**

Localizar (~linha 725):
```css
/* ANTES */
.painel-due-critico{background:#fee2e2;color:#b91c1c}
.painel-due-atrasado{background:#fef9c3;color:#92400e}
.painel-due-hoje{background:#dcfce7;color:#166534}

/* DEPOIS */
.painel-due-critico{background:var(--red-bg,rgba(220,38,38,.1));color:var(--red)}
.painel-due-atrasado{background:var(--yellow-bg,rgba(214,158,46,.1));color:var(--yellow)}
.painel-due-hoje{background:var(--primary-light);color:var(--primary)}
```

- [ ] **Step 4: Verificar visualmente**

Navegar para Painel de Atividades → A resolver. Verificar:
- Ícones SVG aparecem nas rows (calendar, send, clipboard, etc.) — sem emoji
- Stripe lateral colorida mantém as cores de criticidade
- Badges de prazo (Venceu há X dias / Hoje) com cores corretas

- [ ] **Step 5: Commit**

```
git add grv-cs-jornada.html
git commit -m "style(painel): SVG icons em activity rows, badge colors por token"
```

---

### Task 6: ETAPA_META SVG — Kanban + Lista de Clientes

**Files:**
- Modify: `grv-cs-jornada.html` — `ETAPA_META` (~linha 1023), função `getEtapaBadge()` (~linha 3062), CSS `.kc-emoji` (~linha 607) e `.lista-section-emoji` (~linha 634), HTML na lista (~linha 4433) e kanban (~linha 4499)

**Interfaces:**
- Consumes: nada novo — modifica constante e CSS existentes.
- Produces: Kanban e lista de clientes sem emoji visível; `getEtapaBadge()` continua funcionando sem emoji no badge.

- [ ] **Step 1: Substituir emoji no `ETAPA_META` por strings de SVG**

Localizar `ETAPA_META` (~linha 1023). Substituir completamente:

```javascript
const ETAPA_META = {
  '1ª Reunião':  {
    icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    color:'blue'
  },
  'Engajamento': {
    icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>',
    color:'purple'
  },
  'Evolução':    {
    icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
    color:'green'
  },
  'Conclusão':   {
    icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>',
    color:'yellow'
  },
  'Pausado':     {
    icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>',
    color:'gray'
  },
  'Interrompido':{
    icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
    color:'red'
  },
  'Cancelado':   {
    icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>',
    color:'black'
  },
};
```

- [ ] **Step 2: Atualizar `getEtapaBadge()` para usar `.icon` em vez de `.emoji`**

Localizar (~linha 3062):
```javascript
// ANTES
function getEtapaBadge(etapa) {
  const m = ETAPA_META[etapa] || {emoji:'', color:'gray'};
  return `<span class="badge badge-${m.color}">${m.emoji} ${etapa}</span>`;
}

// DEPOIS
function getEtapaBadge(etapa) {
  const m = ETAPA_META[etapa] || {icon:'', color:'gray'};
  return `<span class="badge badge-${m.color}" style="display:inline-flex;align-items:center;gap:4px">${m.icon}${etapa}</span>`;
}
```

- [ ] **Step 3: Atualizar CSS `.kc-emoji` e `.lista-section-emoji`**

Localizar `.kanban-col-name .kc-emoji{font-size:14px}` (~linha 607). Substituir por:
```css
.kanban-col-name .kc-icon{width:14px;height:14px;flex-shrink:0;opacity:.7}
```

Localizar `.lista-section-emoji{font-size:16px}` (~linha 634). Substituir por:
```css
.lista-section-icon{width:16px;height:16px;flex-shrink:0;color:var(--text3)}
```

- [ ] **Step 4: Atualizar HTML do kanban (~linha 4499)**

Localizar:
```javascript
// ANTES
<div class="kanban-col-name"><span class="kc-emoji">${m.emoji}</span><span>${etapa}</span></div>

// DEPOIS
<div class="kanban-col-name"><span class="kc-icon">${m.icon}</span><span>${etapa}</span></div>
```

- [ ] **Step 5: Atualizar HTML da lista (~linha 4433)**

Localizar:
```javascript
// ANTES
<span class="lista-section-emoji">${m.emoji}</span>

// DEPOIS
<span class="lista-section-icon">${m.icon}</span>
```

- [ ] **Step 6: Verificar visualmente**

Navegar para Minha Carteira:
- Lista accordion: ícones SVG no header de cada etapa (sem emoji)
- Kanban: ícones SVG no header de cada coluna (sem emoji)
- Badges de etapa em qualquer lugar do sistema: SVG + texto

- [ ] **Step 7: Commit**

```
git add grv-cs-jornada.html
git commit -m "style(icons): ETAPA_META emoji → SVG, atualiza kanban e lista de clientes"
```

---

### Task 7: Empty states SVG + `.venc-empty` cleanup

**Files:**
- Modify: `grv-cs-jornada.html` — CSS `.es-icon` (~linha 645), 6 ocorrências de empty state com emoji hardcoded

**Interfaces:**
- Consumes: nada novo.
- Produces: estados vazios com ícone SVG 40px, sem nenhum emoji visível no sistema.

- [ ] **Step 1: Atualizar CSS `.es-icon` para suportar SVG**

Localizar `.es-icon{font-size:40px;margin-bottom:12px}` (~linha 645). Substituir por:
```css
.es-icon{width:40px;height:40px;margin:0 auto 12px;color:var(--text4)}
.es-icon svg{width:40px;height:40px}
```

- [ ] **Step 2: Substituir empty states de emoji hardcoded**

Localizar e substituir cada ocorrência:

**Ocorrência 1** (~linha 3049, dashboard sem projetos):
```javascript
// ANTES
'<div class="es-icon">📊</div>'
// DEPOIS
'<div class="es-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></div>'
```

**Ocorrência 2** (~linha 3458, Painel sem atividades vencidas):
```javascript
// ANTES
'<div class="venc-empty"><div>✅</div>' +
// DEPOIS
'<div class="venc-empty"><div><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="1.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>' +
```

**Ocorrência 3** (~linha 4880, Customer sem clientes):
```javascript
// ANTES
'<div class="es-icon">⭐</div>'
// DEPOIS
'<div class="es-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg></div>'
```

**Ocorrências 4 e 5** (~linhas 5044, 5245, filtros sem resultado):
```javascript
// ANTES
'<div class="es-icon">🔍</div>'
// DEPOIS
'<div class="es-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></div>'
```

**Ocorrência 6** (~linha 5358, cliente não encontrado):
```javascript
// ANTES
'<div class="es-icon">❓</div>'
// DEPOIS
'<div class="es-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></div>'
```

- [ ] **Step 3: Verificar visualmente**

Testar cada tela de empty state:
1. Dashboard sem projetos: filtrar por um período sem dados
2. Painel de Atividades com fila vazia (trocar para consultor sem vencimentos)
3. Customer sem clientes: filtrar por consultor sem clientes
4. Portfólio/Implantação sem resultados: buscar por texto inexistente

Verificar: ícones SVG aparecem centralizados, na cor `--text4` (cinza warm), sem emoji.

- [ ] **Step 4: Commit**

```
git add grv-cs-jornada.html
git commit -m "style(empty-states): emoji → SVG icons em todos os estados vazios"
```

---

### Task 8: Feed card progress bars semânticas + CSS cleanup

**Files:**
- Modify: `grv-cs-jornada.html` — render do feed card (~linha 3945 — variável `pColor`), CSS `.kcard-prog-wrap` (~linha 621)

**Interfaces:**
- Consumes: `--green`, `--yellow`, `--red`, `calcHealthScore()` função existente.
- Produces: barras de progresso do feed de clientes com cor baseada no health score; laranja reservado para ações.

- [ ] **Step 1: Localizar onde `pColor` é calculado no feed card render**

Fazer busca no arquivo por `pColor` para encontrar o contexto completo. A variável é usada em ~linha 3945. Localizar onde é definida (tipicamente algumas linhas acima, baseada no status ou health score do cliente).

Buscar: `var pColor` ou `pColor =` no bloco da função de render do feed card (provavelmente `renderCarteiraFeed()` ou nome similar).

- [ ] **Step 2: Ajustar `pColor` para usar health score semântico**

Quando `pColor` for baseado apenas em `var(--primary)` ou uma cor fixa, substituir por lógica semântica:

```javascript
// Padrão: baseado no health score do cliente
var hs = calcHealthScore(c) || 0;
var pColor = hs >= 70 ? 'var(--green)' : hs >= 40 ? 'var(--yellow)' : 'var(--red)';
```

Se já existir lógica de cor baseada em status, verificar se laranja (`var(--primary)`) pode ser substituído pelo health score semântico para esse componente específico.

- [ ] **Step 3: Atualizar `.kcard-prog-wrap` background**

Localizar `.kcard-prog-wrap{flex:1;background:#edf2f7;...}` (~linha 621). Substituir o background hardcoded:
```css
/* ANTES */
.kcard-prog-wrap{flex:1;background:#edf2f7;border-radius:4px;height:5px;overflow:hidden}
/* DEPOIS */
.kcard-prog-wrap{flex:1;background:var(--border-2);border-radius:4px;height:5px;overflow:hidden}
```

- [ ] **Step 4: Verificar visualmente que laranja não aparece em progresso**

Navegar para Minha Carteira (feed e kanban). Verificar:
- Barras de progresso dos feed cards: verde/amarelo/vermelho baseado no health, não laranja
- Laranja ainda aparece em: botões primários, nav ativo, atividades do dia no Painel

- [ ] **Step 5: Verificação geral do sistema**

Percorrer todas as telas em sequência:
1. Projetos GRV → Dashboard: KPI cards unificados, fundo warm, sombras suaves
2. Minha Carteira → Carteira (lista): feed cards levantam no hover, stripe de criticidade, ícones SVG de etapa
3. Minha Carteira → Kanban: colunas com ícones SVG, cards levantam no hover
4. Painel de Atividades → A resolver: KPI strip, ícones SVG nas rows, badges com tokens
5. Detalhe do cliente: header com tokens novos, progress bars semânticas
6. Abrir modal de etapa: sombra mais profunda e definida
7. Abrir dropdown do nav: sombra shadow-2

- [ ] **Step 6: Commit final**

```
git add grv-cs-jornada.html
git commit -m "style(progress): barras de progresso semânticas, laranja reservado para ações"
```

---

## Pós-implementação

Após todas as tasks concluídas e verificadas, criar PR da branch `alteracoes` para `main`:

```
gh pr create --title "Design Uplift GRV CS — warm stone palette, SVG icons, unified KPI card" \
  --body "Uplift visual completo conforme spec docs/superpowers/specs/2026-07-10-design-uplift-design.md

## O que muda
- Paleta warm stone substitui fundo azulado genérico
- Sistema de elevação 3 níveis (shadow-1/2/3)
- 1 padrão canônico de KPI card substitui 7 variações
- Emoji → SVG em: activity rows, ETAPA_META (kanban/lista), empty states
- Hover com lift em feed cards e kanban cards
- Laranja reservado para ações primárias

## O que não muda
- Estrutura de rotas e hash navigation
- Lógica de negócio, dados, playbooks
- vg-card (dark gradient — já bem executado)"
```
