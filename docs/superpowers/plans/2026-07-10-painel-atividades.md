# Painel de Atividades — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the "Vencimentos" screen into "Painel de Atividades" with a KPI strip, fila toggle, and three sub-tabs (A resolver / A planejar / Por cliente).

**Architecture:** All changes are in the single-file SPA `grv-cs-jornada.html`. CSS goes in the existing `<style>` block (look for the `/* ── VENCIMENTOS */` comment at ~line 690). JavaScript goes in the existing `<script>` block near the existing `_venc_filter_*` globals (~line 3266). Nav HTML changes at lines 841–845. No new files.

**Tech Stack:** Vanilla JS, inline HTML/CSS SPA. No build step. Open the file in browser to test.

## Global Constraints

- Single file: `grv-cs-jornada.html` — all CSS, HTML, and JS are inline
- Never change the hash route `"vencimentos"` — external links and history depend on it
- Never rename `concluirVenc()`, `getTodasVencidas()`, `updateVencBadge()` — called from other parts of the codebase
- Use `var` / `function` declarations and ES5-compatible patterns — the file uses `const`/`let` but mixing is fine; avoid arrow functions in inline `onclick` attributes
- Every `onclick` attribute uses escaped single quotes inside double-quoted attributes: `onclick="fn('arg')"`
- `avatarGradiente(nome)` is already defined at line ~3549 — use it for client avatar colors
- `resolverResponsavel(at, pb, cliente)` at line 2263 — returns the responsible consultor id
- `calcHealthScore(cliente)` at line 2174 — returns a number or null
- `getConsultores()`, `getConsultorAtivo()`, `getCliente()`, `getClientes()` — existing data access functions
- `saveCliente(c)` — persists client to localStorage
- `showToast(msg, ms)` — shows a temporary notification
- `checkImplantacaoConcluida(clienteId)` — called after marking activity done (line 3486)

---

### Task 1: CSS for new components

**Files:**
- Modify: `grv-cs-jornada.html` (~line 707, after `.venc-btn-ir:hover` rule)

**Interfaces:**
- Produces: all `.painel-*` and `.venc-empty` CSS classes used by Tasks 3–6

- [ ] **Step 1: Locate the insertion point**

  Open `grv-cs-jornada.html`. Find line 707 (the `.venc-btn-ir:hover` rule). The new CSS block goes immediately after it, before the next comment section.

- [ ] **Step 2: Insert the new CSS block**

  After line 707 (`.venc-btn-ir:hover{...}`), insert:

  ```css
  /* ── PAINEL DE ATIVIDADES – new components ──────────── */
  .venc-empty{text-align:center;padding:48px 24px;color:var(--text2)}
  .venc-empty div:first-child{font-size:32px}
  .painel-kpi-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:18px}
  .painel-kpi-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:12px 14px}
  .painel-kpi-label{font-size:10px;color:var(--text3);font-weight:600;text-transform:uppercase;letter-spacing:.5px}
  .painel-kpi-value{font-size:26px;font-weight:700;line-height:1.1;margin-top:4px;font-variant-numeric:tabular-nums}
  .painel-kpi-sub{font-size:11px;color:var(--text3);margin-top:3px}
  .painel-toolbar{display:flex;align-items:center;gap:10px;margin-bottom:16px;flex-wrap:wrap}
  .painel-toggle-group{display:flex;background:var(--bg);border:1px solid var(--border);border-radius:8px;overflow:hidden}
  .painel-toggle-btn{background:none;border:none;padding:6px 14px;font-size:13px;cursor:pointer;color:var(--text2);transition:background .15s,color .15s;font-family:inherit}
  .painel-toggle-btn.active{background:var(--primary);color:#fff;font-weight:600}
  .painel-tabs{display:flex;gap:2px;background:var(--bg);border:1px solid var(--border);border-radius:8px;overflow:hidden}
  .painel-tab{background:none;border:none;padding:6px 14px;font-size:13px;cursor:pointer;color:var(--text2);font-family:inherit;transition:background .15s,color .15s;white-space:nowrap}
  .painel-tab.active{background:var(--surface);color:var(--primary);font-weight:600;border-radius:6px}
  .painel-due{font-size:11px;font-weight:600;padding:2px 8px;border-radius:12px;white-space:nowrap;flex-shrink:0}
  .painel-due-critico{background:#fee2e2;color:#b91c1c}
  .painel-due-atrasado{background:#fef9c3;color:#92400e}
  .painel-due-hoje{background:#dcfce7;color:#166534}
  .painel-resolver-row{flex-wrap:wrap}
  .painel-note-area{display:none;gap:8px;align-items:flex-start;padding:0 16px 10px 56px;flex-wrap:wrap}
  .painel-note-area.open{display:flex}
  .painel-note-input{flex:1;min-width:200px;border:1px solid var(--border);border-radius:6px;padding:6px 10px;font-size:12px;font-family:inherit;background:var(--bg);color:var(--text);resize:none;height:50px}
  .painel-note-input:focus{outline:none;border-color:var(--primary)}
  .painel-note-save{background:var(--primary);color:#fff;border:none;padding:6px 12px;border-radius:6px;font-size:12px;cursor:pointer;font-family:inherit;white-space:nowrap}
  .painel-note-cancel{background:none;color:var(--text3);border:1px solid var(--border);padding:6px 10px;border-radius:6px;font-size:12px;cursor:pointer;font-family:inherit;white-space:nowrap}
  .painel-week-header{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;color:var(--text3);padding:12px 0 4px;border-bottom:2px solid var(--border);margin-bottom:8px}
  .painel-filter-chips{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap}
  .painel-chip{border:1px solid var(--border);border-radius:20px;padding:4px 12px;font-size:12px;cursor:pointer;background:var(--bg);color:var(--text2);transition:background .15s,border-color .15s,color .15s;user-select:none}
  .painel-chip.active{background:var(--primary);border-color:var(--primary);color:#fff;font-weight:600}
  .painel-client-group{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:10px;overflow:hidden}
  .painel-client-header{display:flex;align-items:center;gap:10px;padding:10px 14px;cursor:pointer;border-bottom:1px solid var(--border);transition:background .1s}
  .painel-client-header:hover{background:var(--bg)}
  .painel-client-header.collapsed{border-bottom:none}
  .painel-chevron{font-size:11px;color:var(--text3);transition:transform .2s;flex-shrink:0;margin-left:auto}
  .painel-client-rows{padding:4px 0}
  .painel-client-row{display:flex;align-items:center;gap:10px;padding:8px 14px;border-bottom:1px solid var(--border)}
  .painel-client-row:last-child{border-bottom:none}
  .painel-client-row:hover{background:var(--bg)}
  @media(max-width:640px){.painel-kpi-strip{grid-template-columns:repeat(2,1fr)}}
  ```

- [ ] **Step 3: Verify no syntax errors**

  Open `grv-cs-jornada.html` in browser. Open DevTools → Console. Check for any CSS parse errors. The existing Vencimentos screen should still work.

- [ ] **Step 4: Commit**

  ```bash
  git add grv-cs-jornada.html
  git commit -m "style(painel): CSS para componentes do Painel de Atividades"
  ```

---

### Task 2: Nav rename + dropdown

**Files:**
- Modify: `grv-cs-jornada.html` (lines 841–845)

**Interfaces:**
- Consumes: existing `.nav-group`, `.nav-dropdown`, `.nav-drop-header`, `.nav-drop-divider`, `.nav-drop-item`, `.nav-drop-badge` CSS classes (already defined at lines 53–62)
- Produces: `#nav-vencimentos-group` (nav group), `#drop-venc-resolver`, `#drop-venc-planejar`, `#drop-venc-cliente` (dropdown items), `#drop-venc-resolver-badge`, `#drop-venc-planejar-badge` (badges)

- [ ] **Step 1: Locate the nav item**

  Find lines 841–845 in `grv-cs-jornada.html`. They look like:

  ```html
  <div class="nav-item" id="nav-vencimentos" data-route="vencimentos" onclick="navigate('vencimentos')">
    <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
    Vencimentos
    <span class="nav-badge hidden" id="nav-venc-badge">0</span>
  </div>
  ```

- [ ] **Step 2: Replace with wrapped group + dropdown**

  Replace those 5 lines with:

  ```html
  <div class="nav-group" id="nav-vencimentos-group">
    <div class="nav-item" id="nav-vencimentos" data-route="vencimentos" onclick="navigate('vencimentos')">
      <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
      Painel de Atividades
      <span class="nav-badge hidden" id="nav-venc-badge">0</span>
    </div>
    <div class="nav-dropdown" id="venc-dropdown">
      <div class="nav-drop-header">PAINEL DE ATIVIDADES</div>
      <div class="nav-drop-divider"></div>
      <div class="nav-drop-item" id="drop-venc-resolver" onclick="setVencTab('resolver')">
        A resolver <span class="nav-drop-badge" id="drop-venc-resolver-badge"></span>
      </div>
      <div class="nav-drop-item" id="drop-venc-planejar" onclick="setVencTab('planejar')">
        A planejar <span class="nav-drop-badge" id="drop-venc-planejar-badge"></span>
      </div>
      <div class="nav-drop-item" id="drop-venc-cliente" onclick="setVencTab('cliente')">
        Por cliente
      </div>
    </div>
  </div>
  ```

- [ ] **Step 3: Verify in browser**

  Reload page. The nav label should now read "Painel de Atividades". Hovering it should show the dropdown with three items. Clicking the nav item should still navigate to the Vencimentos screen. Badge still works.

- [ ] **Step 4: Commit**

  ```bash
  git add grv-cs-jornada.html
  git commit -m "feat(painel): renomeia nav 'Vencimentos' → 'Painel de Atividades' + dropdown"
  ```

---

### Task 3: New state globals + helper functions

**Files:**
- Modify: `grv-cs-jornada.html` (after the existing `_venc_filter_*` block at ~line 3271)

**Interfaces:**
- Consumes: `getTodasVencidas()`, `getClientes()`, `getConsultorAtivo()`, `resolverResponsavel()`
- Produces:
  - `_venc_tab: string` — read by `renderVencimentos()`
  - `_venc_fila: string` — read by all sub-renders
  - `_venc_chips: string[]` — read by `renderVencPorCliente()`
  - `setVencTab(tab: string): void` — called from dropdown items and tab buttons
  - `getKpiVencimentos(): {criticas: number, hoje: number, semana: number, sla: number}` — called by `renderVencimentos()`
  - `updateVencDropdownBadges(): void` — called by `renderVencimentos()`

- [ ] **Step 1: Find insertion point**

  Locate `let _venc_filter_horizonte = 'vencidas';` (around line 3271). The new globals and helpers go immediately after that line (before `function renderVencimentos()`).

- [ ] **Step 2: Insert new globals**

  After `let _venc_filter_horizonte = 'vencidas';`, insert:

  ```javascript
  let _venc_tab   = 'resolver'; // 'resolver' | 'planejar' | 'cliente'
  let _venc_fila  = 'minha';   // 'minha' | 'time'
  let _venc_chips = ['vencidas']; // active chips for 'Por cliente' view
  ```

- [ ] **Step 3: Insert setVencTab()**

  After the globals, insert:

  ```javascript
  function setVencTab(tab) {
    _venc_tab = tab;
    var hash = location.hash.replace('#','');
    if (hash === 'vencimentos') {
      renderVencimentos();
    } else {
      navigate('vencimentos');
    }
    ['resolver','planejar','cliente'].forEach(function(t) {
      var el = document.getElementById('drop-venc-' + t);
      if (el) el.classList.toggle('active', t === tab);
    });
  }
  ```

- [ ] **Step 4: Insert getKpiVencimentos()**

  ```javascript
  function getKpiVencimentos() {
    var ativo = getConsultorAtivo();
    var todos30 = getTodasVencidas(30);
    var minha = todos30.filter(function(v) {
      return resolverResponsavel(v.at, v.pb, v.cliente) === ativo;
    });
    var criticas = minha.filter(function(v) { return v.diff < -3; }).length;
    var hoje     = minha.filter(function(v) { return v.diff === 0; }).length;
    var semana   = todos30.filter(function(v) { return v.diff > 0 && v.diff <= 7; }).length;
    // SLA: % of all active activities whose deadline is not yet passed
    var totalAtivas = 0;
    var emDia = 0;
    var agora = new Date(); agora.setHours(0,0,0,0);
    getClientes().forEach(function(c) {
      (c.ativPlaybooks || []).forEach(function(pb) {
        if ((pb.status || 'ativo') === 'cancelado') return;
        (pb.atividades || []).forEach(function(at) {
          if (at.status === 'concluida') return;
          if (!at.dataLimite) return;
          totalAtivas++;
          var dl = new Date(at.dataLimite + 'T00:00:00');
          if (dl >= agora) emDia++;
        });
      });
    });
    var sla = totalAtivas > 0 ? Math.round(emDia / totalAtivas * 100) : 100;
    return { criticas: criticas, hoje: hoje, semana: semana, sla: sla };
  }
  ```

- [ ] **Step 5: Insert updateVencDropdownBadges()**

  ```javascript
  function updateVencDropdownBadges() {
    var ativo = getConsultorAtivo();
    var vencidas = getTodasVencidas(0).filter(function(v) {
      return resolverResponsavel(v.at, v.pb, v.cliente) === ativo;
    }).length;
    var proximos7 = getTodasVencidas(7).filter(function(v) {
      return v.diff > 0 && resolverResponsavel(v.at, v.pb, v.cliente) === ativo;
    }).length;
    var bR = document.getElementById('drop-venc-resolver-badge');
    var bP = document.getElementById('drop-venc-planejar-badge');
    if (bR) { bR.textContent = vencidas || ''; bR.style.display = vencidas ? '' : 'none'; }
    if (bP) { bP.textContent = proximos7 || ''; bP.style.display = proximos7 ? '' : 'none'; }
  }
  ```

- [ ] **Step 6: Verify no JS errors**

  Reload page in browser. Open DevTools → Console. Should be no errors. `setVencTab('planejar')` in the console should not throw.

- [ ] **Step 7: Commit**

  ```bash
  git add grv-cs-jornada.html
  git commit -m "feat(painel): globais _venc_tab/_venc_fila/_venc_chips + helpers KPI/badges"
  ```

---

### Task 4: renderVencimentos() shell rewrite

**Files:**
- Modify: `grv-cs-jornada.html` — replace the existing `renderVencimentos()` function (~lines 3273–3403)

**Interfaces:**
- Consumes: `_venc_tab`, `_venc_fila`, `getKpiVencimentos()`, `updateVencDropdownBadges()`, `renderVencAResolver()` (Task 5), `renderVencPlanejar()` (Task 6), `renderVencPorCliente()` (Task 7)
- Produces: updated `#sec-vencimentos` innerHTML; `mkKpiCard(label, value, color, sub): string`

**Important:** The existing function spans lines ~3273–3403. Replace the entire block. The new function is shorter because complex rendering moves to sub-functions.

- [ ] **Step 1: Replace renderVencimentos() entirely**

  Find the line `function renderVencimentos() {` (~line 3273) and replace everything from that line to the matching closing `}` (~line 3403) with:

  ```javascript
  function renderVencimentos() {
    var sec = document.getElementById('sec-vencimentos');
    if (!sec) return;

    var kpi = getKpiVencimentos();
    updateVencDropdownBadges();

    var kpiHtml = '<div class="painel-kpi-strip">' +
      mkKpiCard('Críticas', kpi.criticas, '#dc2626', 'Risco de churn') +
      mkKpiCard('Vencem hoje', kpi.hoje, '#eab308', 'Fila do dia') +
      mkKpiCard('Esta semana', kpi.semana, 'var(--primary)', 'Próximos 7 dias') +
      mkKpiCard('SLA em dia', kpi.sla + '%', '#22c55e', 'Atividades no prazo') +
    '</div>';

    var toolHtml = '<div class="painel-toolbar">' +
      '<div class="painel-toggle-group">' +
        '<button class="painel-toggle-btn' + (_venc_fila === 'minha' ? ' active' : '') + '" ' +
          'onclick="_venc_fila=\'minha\';renderVencimentos()">Minha fila</button>' +
        '<button class="painel-toggle-btn' + (_venc_fila === 'time' ? ' active' : '') + '" ' +
          'onclick="_venc_fila=\'time\';renderVencimentos()">Time todo</button>' +
      '</div>' +
      '<div class="painel-tabs">' +
        '<button class="painel-tab' + (_venc_tab === 'resolver' ? ' active' : '') + '" ' +
          'onclick="setVencTab(\'resolver\')">A resolver</button>' +
        '<button class="painel-tab' + (_venc_tab === 'planejar' ? ' active' : '') + '" ' +
          'onclick="setVencTab(\'planejar\')">A planejar</button>' +
        '<button class="painel-tab' + (_venc_tab === 'cliente' ? ' active' : '') + '" ' +
          'onclick="setVencTab(\'cliente\')">Por cliente</button>' +
      '</div>' +
    '</div>';

    var contentHtml;
    if (_venc_tab === 'resolver')       contentHtml = renderVencAResolver();
    else if (_venc_tab === 'planejar')  contentHtml = renderVencPlanejar();
    else                                contentHtml = renderVencPorCliente();

    sec.innerHTML = '<div class="venc-wrap">' + kpiHtml + toolHtml + contentHtml + '</div>';

    // restore active tab in dropdown
    ['resolver','planejar','cliente'].forEach(function(t) {
      var el = document.getElementById('drop-venc-' + t);
      if (el) el.classList.toggle('active', t === _venc_tab);
    });
  }

  function mkKpiCard(label, value, color, sub) {
    return '<div class="painel-kpi-card">' +
      '<div class="painel-kpi-label">' + label + '</div>' +
      '<div class="painel-kpi-value" style="color:' + color + '">' + value + '</div>' +
      '<div class="painel-kpi-sub">' + sub + '</div>' +
    '</div>';
  }
  ```

- [ ] **Step 2: Verify shell renders**

  Reload browser. Navigate to "Painel de Atividades". You should see:
  - KPI strip with 4 cards
  - Toggle group "Minha fila / Time todo"
  - Three tabs (A resolver / A planejar / Por cliente)
  - A blank content area (sub-render functions not yet defined — console will show "renderVencAResolver is not defined")

  That error is expected at this stage — Task 5 will fix it.

- [ ] **Step 3: Commit**

  ```bash
  git add grv-cs-jornada.html
  git commit -m "feat(painel): shell de renderVencimentos com KPI strip e tabs"
  ```

---

### Task 5: renderVencAResolver() + concluirVencComNota()

**Files:**
- Modify: `grv-cs-jornada.html` — insert after `mkKpiCard()` function (after Task 4 code)

**Interfaces:**
- Consumes: `_venc_fila`, `getTodasVencidas(0)`, `getConsultorAtivo()`, `resolverResponsavel()`, `getConsultores()`, `getCliente()`, `saveCliente()`, `updateVencBadge()`, `showToast()`, `checkImplantacaoConcluida()`
- Produces:
  - `renderVencAResolver(): string` — HTML for the A resolver tab
  - `abrirNotaVenc(rowId, clienteId, pbId, atId): void` — toggles note area
  - `fecharNotaVenc(notaId): void` — closes note area
  - `concluirVencComNota(evt, clienteId, pbId, atId, notaId): void` — marks done + saves note

- [ ] **Step 1: Insert renderVencAResolver()**

  After the closing `}` of `mkKpiCard()`, insert:

  ```javascript
  function renderVencAResolver() {
    var consultor = _venc_fila === 'minha' ? getConsultorAtivo() : 'todos';
    var todos = getTodasVencidas(0);
    if (consultor !== 'todos') {
      todos = todos.filter(function(v) {
        return resolverResponsavel(v.at, v.pb, v.cliente) === consultor;
      });
    }

    if (!todos.length) {
      return '<div class="venc-empty"><div>✅</div>' +
        '<div style="font-weight:700;margin-top:8px">Tudo em dia!</div>' +
        '<div style="font-size:13px;color:var(--text3)">Nenhuma atividade vencida na sua fila.</div></div>';
    }

    var criticos  = todos.filter(function(v) { return v.diff < -3; });
    var atrasados = todos.filter(function(v) { return v.diff < 0 && v.diff >= -3; });
    var hojeList  = todos.filter(function(v) { return v.diff === 0; });

    function mkResolverRow(v) {
      var absDiff = Math.abs(v.diff);
      var diasTxt = v.diff < 0
        ? 'Venceu há ' + absDiff + (absDiff === 1 ? ' dia' : ' dias')
        : 'Hoje';
      var stripeClr = v.diff < -3 ? '#dc2626' : v.diff < 0 ? '#eab308' : 'var(--primary)';
      var dueCls = v.diff < -3 ? 'painel-due-critico' : v.diff < 0 ? 'painel-due-atrasado' : 'painel-due-hoje';
      var tipoIcons = { reuniao:'📞', treinamento:'🎓', relatorio:'📊', qbr:'📋', pesquisa:'⭐', followup:'📩' };
      var icon = tipoIcons[v.at.tipo || ''] || '📋';
      var resp = resolverResponsavel(v.at, v.pb, v.cliente);
      var respNome = (getConsultores().find(function(x) { return x.id === resp; }) || {}).nome || resp;
      var nomeAt = v.at.nome || v.at.titulo || 'Atividade';
      var clienteLink = '<a href="#cliente/' + encodeURIComponent(v.clienteId) + '" ' +
        'onclick="event.stopPropagation()" ' +
        'style="color:var(--primary);font-weight:600;text-decoration:none">' + v.clienteId + '</a>';
      var rowId = 'vr_' + v.clienteId + '_' + v.atId;
      return '' +
        '<div class="venc-row painel-resolver-row" id="' + rowId + '">' +
          '<div class="venc-stripe" style="background:' + stripeClr + '"></div>' +
          '<span style="font-size:15px;flex-shrink:0">' + icon + '</span>' +
          '<div class="venc-info">' +
            '<div class="venc-nome">' + nomeAt + ' — ' + clienteLink + '</div>' +
            '<div class="venc-meta">' + respNome + ' · ' + (v.cliente.segmento || '') + '</div>' +
          '</div>' +
          '<span class="painel-due ' + dueCls + '">' + diasTxt + '</span>' +
          '<button class="venc-btn-ok" ' +
            'onclick="abrirNotaVenc(\'' + rowId + '\',\'' + v.clienteId + '\',\'' + v.pbId + '\',\'' + v.atId + '\')">✓ Concluir</button>' +
        '</div>' +
        '<div class="painel-note-area" id="nota_' + rowId + '">' +
          '<textarea class="painel-note-input" placeholder="Nota rápida (opcional) — salva no registro do cliente..."></textarea>' +
          '<button class="painel-note-save" ' +
            'onclick="concluirVencComNota(event,\'' + v.clienteId + '\',\'' + v.pbId + '\',\'' + v.atId + '\',\'nota_' + rowId + '\')">Salvar</button>' +
          '<button class="painel-note-cancel" ' +
            'onclick="fecharNotaVenc(\'nota_' + rowId + '\')">Cancelar</button>' +
        '</div>';
    }

    function mkResolverGroup(items, label, dotClr) {
      if (!items.length) return '';
      return '<div class="venc-group">' +
        '<div class="venc-group-label">' +
          '<span class="venc-dot" style="background:' + dotClr + '"></span>' +
          label + ' (' + items.length + ')' +
        '</div>' +
        items.map(mkResolverRow).join('') +
      '</div>';
    }

    return mkResolverGroup(criticos, 'Crítico — vencido há 4+ dias', '#dc2626') +
           mkResolverGroup(atrasados, 'Atrasado — vencido há 1–3 dias', '#eab308') +
           mkResolverGroup(hojeList, 'Vence hoje', 'var(--primary)');
  }
  ```

- [ ] **Step 2: Insert note helper functions**

  ```javascript
  function abrirNotaVenc(rowId, clienteId, pbId, atId) {
    var nota = document.getElementById('nota_' + rowId);
    if (!nota) return;
    nota.classList.toggle('open');
    if (nota.classList.contains('open')) {
      var inp = nota.querySelector('.painel-note-input');
      if (inp) { inp.focus(); }
    }
  }

  function fecharNotaVenc(notaId) {
    var nota = document.getElementById(notaId);
    if (nota) nota.classList.remove('open');
  }
  ```

- [ ] **Step 3: Insert concluirVencComNota()**

  ```javascript
  function concluirVencComNota(evt, clienteId, pbId, atId, notaId) {
    evt.stopPropagation();
    var notaEl = document.getElementById(notaId);
    var notaTxt = '';
    if (notaEl) {
      var inp = notaEl.querySelector('.painel-note-input');
      if (inp) notaTxt = inp.value.trim();
    }
    var c  = getCliente(clienteId);
    var pb = (c && c.ativPlaybooks || []).find(function(p) { return p.id === pbId; });
    var at = (pb && pb.atividades || []).find(function(a) { return a.id === atId; });
    if (!at || at.status === 'concluida') return;
    at.status = 'concluida';
    at.dataConclusao = new Date().toISOString();
    if (!at.registros) at.registros = [];
    var ativo = getConsultorAtivo();
    var autor = (getConsultores().find(function(x) { return x.id === ativo; }) || {}).nome || ativo;
    var textoReg = autor + ' marcou como Concluída (via Painel de Atividades)';
    if (notaTxt) textoReg += ': ' + notaTxt;
    at.registros.unshift({ id: 'reg_' + Date.now(), tipo: 'evento', texto: textoReg, data: new Date().toISOString() });
    saveCliente(c);
    updateVencBadge();
    renderVencimentos();
    showToast('Atividade concluída!', 3000);
    checkImplantacaoConcluida(clienteId);
  }
  ```

- [ ] **Step 4: Verify A resolver tab**

  Reload browser. Navigate to Painel de Atividades. The "A resolver" tab (default) should:
  - Show grouped rows (Crítico / Atrasado / Vence hoje) depending on your seed data
  - Clicking "✓ Concluir" expands a textarea + Salvar/Cancelar buttons
  - "Cancelar" closes the textarea without saving
  - "Salvar" marks the activity done, re-renders, shows toast

- [ ] **Step 5: Commit**

  ```bash
  git add grv-cs-jornada.html
  git commit -m "feat(painel): aba 'A resolver' com concluir inline + nota"
  ```

---

### Task 6: renderVencPlanejar()

**Files:**
- Modify: `grv-cs-jornada.html` — insert after `concluirVencComNota()` function

**Interfaces:**
- Consumes: `_venc_fila`, `getTodasVencidas(30)`, `getConsultorAtivo()`, `resolverResponsavel()`, `getConsultores()`
- Produces: `renderVencPlanejar(): string`

- [ ] **Step 1: Insert renderVencPlanejar()**

  ```javascript
  function renderVencPlanejar() {
    var consultor = _venc_fila === 'minha' ? getConsultorAtivo() : 'todos';
    var todos = getTodasVencidas(30).filter(function(v) { return v.diff > 0; });
    if (consultor !== 'todos') {
      todos = todos.filter(function(v) {
        return resolverResponsavel(v.at, v.pb, v.cliente) === consultor;
      });
    }
    todos.sort(function(a, b) { return a.diff - b.diff; });

    if (!todos.length) {
      return '<div class="venc-empty"><div>📅</div>' +
        '<div style="font-weight:700;margin-top:8px">Nada planejado</div>' +
        '<div style="font-size:13px;color:var(--text3)">Nenhuma atividade nos próximos 30 dias.</div></div>';
    }

    var buckets = { S1: [], S2: [], S3: [], S4: [] };
    var bucketLabels = {
      S1: 'Esta semana (1–7 dias)',
      S2: 'Próxima semana (8–14 dias)',
      S3: 'Em 2–3 semanas (15–21 dias)',
      S4: 'Em 3–4 semanas (22–30 dias)'
    };
    todos.forEach(function(v) {
      var b = v.diff <= 7 ? 'S1' : v.diff <= 14 ? 'S2' : v.diff <= 21 ? 'S3' : 'S4';
      buckets[b].push(v);
    });

    var html = '';
    ['S1','S2','S3','S4'].forEach(function(b) {
      if (!buckets[b].length) return;
      html += '<div class="painel-week-header">' + bucketLabels[b] + '</div>';
      buckets[b].forEach(function(v) {
        var dl = new Date(v.at.dataLimite + 'T00:00:00');
        var diaSemArr = ['Dom','Seg','Ter','Qua','Qui','Sex','Sáb'];
        var diaSem = diaSemArr[dl.getDay()];
        var dd = String(dl.getDate()).padStart(2,'0');
        var mm = String(dl.getMonth() + 1).padStart(2,'0');
        var resp = resolverResponsavel(v.at, v.pb, v.cliente);
        var respNome = (getConsultores().find(function(x) { return x.id === resp; }) || {}).nome || resp;
        var clienteLink = '<a href="#cliente/' + encodeURIComponent(v.clienteId) + '" ' +
          'style="color:var(--primary);font-weight:600;text-decoration:none">' + v.clienteId + '</a>';
        html += '<div class="venc-row" style="margin-bottom:6px">' +
          '<div style="font-size:11px;font-weight:700;color:var(--text2);min-width:52px;flex-shrink:0;font-variant-numeric:tabular-nums">' +
            diaSem + ' ' + dd + '/' + mm +
          '</div>' +
          '<div class="venc-info">' +
            '<div class="venc-nome">' + (v.at.nome || v.at.titulo || 'Atividade') + ' — ' + clienteLink + '</div>' +
            '<div class="venc-meta">' + respNome + ' · ' + (v.cliente.segmento || '') + '</div>' +
          '</div>' +
          '<span class="painel-due painel-due-hoje">Em ' + v.diff + ' dia' + (v.diff === 1 ? '' : 's') + '</span>' +
        '</div>';
      });
    });
    return html;
  }
  ```

- [ ] **Step 2: Verify A planejar tab**

  Reload browser. Click "A planejar" tab. Should show:
  - Activities grouped by week bucket (only non-empty buckets appear)
  - Each row has day/date, activity name, client link, consultor, "Em X dias" badge
  - No "Concluir" button (planning view only)
  - Toggle "Minha fila / Time todo" filters the list

- [ ] **Step 3: Commit**

  ```bash
  git add grv-cs-jornada.html
  git commit -m "feat(painel): aba 'A planejar' com agrupamento por semana"
  ```

---

### Task 7: renderVencPorCliente()

**Files:**
- Modify: `grv-cs-jornada.html` — insert after `renderVencPlanejar()` function

**Interfaces:**
- Consumes: `_venc_fila`, `_venc_chips`, `getTodasVencidas(30)`, `getConsultorAtivo()`, `resolverResponsavel()`, `getConsultores()`, `calcHealthScore()`, `avatarGradiente()`
- Produces:
  - `renderVencPorCliente(): string`
  - `toggleVencChip(chipId: string): void`
  - `togglePainelCliente(groupId: string): void`

- [ ] **Step 1: Insert renderVencPorCliente()**

  ```javascript
  function renderVencPorCliente() {
    var consultor = _venc_fila === 'minha' ? getConsultorAtivo() : 'todos';
    var todos = getTodasVencidas(30);
    if (consultor !== 'todos') {
      todos = todos.filter(function(v) {
        return resolverResponsavel(v.at, v.pb, v.cliente) === consultor;
      });
    }

    function classify(v) {
      if (v.diff <= 0) return 'vencidas';
      return 'avencer';
    }

    var filtered = todos.filter(function(v) {
      return _venc_chips.indexOf(classify(v)) >= 0;
    });

    // Group by client
    var byCliente = {};
    filtered.forEach(function(v) {
      if (!byCliente[v.clienteId]) {
        byCliente[v.clienteId] = { cliente: v.cliente, items: [], vencidasCount: 0 };
      }
      byCliente[v.clienteId].items.push(v);
      if (classify(v) === 'vencidas') byCliente[v.clienteId].vencidasCount++;
    });

    // Sort: most overdue first, then by health score ascending
    var grupos = Object.keys(byCliente).map(function(k) { return byCliente[k]; });
    grupos.sort(function(a, b) {
      if (b.vencidasCount !== a.vencidasCount) return b.vencidasCount - a.vencidasCount;
      var hsA = calcHealthScore(a.cliente);
      var hsB = calcHealthScore(b.cliente);
      if (hsA === null) hsA = 100;
      if (hsB === null) hsB = 100;
      return hsA - hsB;
    });

    var chipDefs = [
      { id: 'vencidas', label: '🔴 Vencidas' },
      { id: 'avencer',  label: '🟡 A vencer (30 dias)' }
    ];
    var chipsHtml = '<div class="painel-filter-chips">' +
      chipDefs.map(function(ch) {
        var active = _venc_chips.indexOf(ch.id) >= 0;
        return '<span class="painel-chip' + (active ? ' active' : '') + '" ' +
          'onclick="toggleVencChip(\'' + ch.id + '\')">' + ch.label + '</span>';
      }).join('') +
    '</div>';

    if (!grupos.length) {
      return chipsHtml + '<div class="venc-empty"><div>🔍</div>' +
        '<div style="font-weight:700;margin-top:8px">Nenhuma atividade</div>' +
        '<div style="font-size:13px;color:var(--text3)">Ajuste os filtros acima.</div></div>';
    }

    var groupsHtml = grupos.map(function(g) {
      var hs = calcHealthScore(g.cliente);
      var hsDot = hs === null ? '#888' : hs >= 70 ? '#22c55e' : hs >= 40 ? '#eab308' : '#dc2626';
      var initials = g.clienteId.substring(0, 2).toUpperCase();
      var resp = resolverResponsavel(g.items[0].at, g.items[0].pb, g.cliente);
      var respNome = (getConsultores().find(function(x) { return x.id === resp; }) || {}).nome || resp;
      var statsArr = [];
      if (g.vencidasCount) statsArr.push(g.vencidasCount + ' vencida' + (g.vencidasCount > 1 ? 's' : ''));
      var avencer = g.items.length - g.vencidasCount;
      if (avencer) statsArr.push(avencer + ' a vencer');
      var badgeHtml = g.vencidasCount > 0
        ? '<span style="font-size:10px;font-weight:700;background:#fee2e2;color:#b91c1c;padding:2px 8px;border-radius:10px;flex-shrink:0">' +
            g.vencidasCount + ' vencida' + (g.vencidasCount > 1 ? 's' : '') +
          '</span>'
        : '';
      var groupId = 'cg_' + g.clienteId.replace(/[^a-zA-Z0-9]/g, '_');
      var rowsHtml = g.items.map(function(v) {
        var cls = classify(v);
        var absDiff = Math.abs(v.diff);
        var diasTxt = v.diff < 0
          ? 'Venceu há ' + absDiff + (absDiff === 1 ? ' dia' : ' dias')
          : v.diff === 0 ? 'Hoje'
          : 'Em ' + v.diff + ' dia' + (v.diff === 1 ? '' : 's');
        var dueCls = cls === 'vencidas' ? 'painel-due-critico' : 'painel-due-hoje';
        return '<div class="painel-client-row">' +
          '<span style="font-size:13px;flex-shrink:0">📋</span>' +
          '<div class="venc-info">' +
            '<div style="font-size:13px;font-weight:600">' + (v.at.nome || v.at.titulo || 'Atividade') + '</div>' +
            '<div class="venc-meta">' + diasTxt + '</div>' +
          '</div>' +
          '<span class="painel-due ' + dueCls + '">' + diasTxt + '</span>' +
        '</div>';
      }).join('');

      return '<div class="painel-client-group">' +
        '<div class="painel-client-header' + (false ? ' collapsed' : '') + '" ' +
          'onclick="togglePainelCliente(\'' + groupId + '\')">' +
          '<div class="venc-avatar" style="background:' + avatarGradiente(g.clienteId) + '">' + initials + '</div>' +
          '<div class="venc-info">' +
            '<div class="venc-nome">' + g.clienteId + '</div>' +
            '<div class="venc-meta">' +
              '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;' +
                'background:' + hsDot + ';margin-right:4px;vertical-align:middle"></span>' +
              (hs !== null ? 'Health ' + hs : 'S/ health') + ' · ' + respNome +
              (statsArr.length ? ' · ' + statsArr.join(' · ') : '') +
            '</div>' +
          '</div>' +
          badgeHtml +
          '<span class="painel-chevron" id="chev_' + groupId + '" style="transform:rotate(90deg)">▶</span>' +
        '</div>' +
        '<div class="painel-client-rows" id="' + groupId + '">' + rowsHtml + '</div>' +
      '</div>';
    }).join('');

    return chipsHtml + groupsHtml;
  }
  ```

- [ ] **Step 2: Insert toggleVencChip() and togglePainelCliente()**

  ```javascript
  function toggleVencChip(chipId) {
    var idx = _venc_chips.indexOf(chipId);
    if (idx >= 0) {
      if (_venc_chips.length === 1) return; // always keep at least one active
      _venc_chips.splice(idx, 1);
    } else {
      _venc_chips.push(chipId);
    }
    renderVencimentos();
  }

  function togglePainelCliente(groupId) {
    var rows = document.getElementById(groupId);
    var chev = document.getElementById('chev_' + groupId);
    if (!rows || !chev) return;
    var isOpen = rows.style.display !== 'none';
    rows.style.display = isOpen ? 'none' : '';
    chev.style.transform = isOpen ? '' : 'rotate(90deg)';
  }
  ```

- [ ] **Step 3: Verify Por cliente tab**

  Reload browser. Click "Por cliente" tab. Should show:
  - Two chips at top (🔴 Vencidas active by default, 🟡 A vencer inactive)
  - Client accordion groups, ordered by most overdue first
  - Each client has health dot, stats, and badge if has overdue items
  - Clicking client header collapses/expands the activity rows
  - Clicking a chip toggles it; last active chip cannot be deselected
  - Toggle "Minha fila / Time todo" filters by consultor

- [ ] **Step 4: Verify full integration**

  Final checklist:
  - [ ] Nav shows "Painel de Atividades" with hover dropdown
  - [ ] Dropdown badge on "A resolver" shows count of overdue activities
  - [ ] KPI strip shows correct values
  - [ ] All three tabs switch correctly
  - [ ] "Minha fila / Time todo" toggle works in all three tabs
  - [ ] Marking an activity done in "A resolver" updates the KPI strip
  - [ ] No console errors

- [ ] **Step 5: Commit**

  ```bash
  git add grv-cs-jornada.html
  git commit -m "feat(painel): aba 'Por cliente' com chips multi-select e acordeão"
  ```
