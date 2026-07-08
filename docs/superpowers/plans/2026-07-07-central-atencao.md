# Central de Atenção — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar badge de urgências no nav, botão ⚡ Urgentes por aba e menu `···` nas linhas urgentes das 3 abas de Projetos GRV.

**Architecture:** Tudo num único arquivo HTML (`grv-cs-jornada.html`). Uma função pura `isUrgente(c)` centraliza o critério. O badge do nav, o botão de filtro e o botão `···` nas linhas todos a consomem. Estado de filtro (`_urg_filter`) é uma variável global simples, resetada ao trocar de aba.

**Tech Stack:** Vanilla JS, HTML/CSS inline, `localStorage` para dados, sem build step, sem framework.

## Global Constraints

- Arquivo único: `grv-cs-jornada.html` — todas as edições vão nele
- Sem TypeScript, sem build — JS puro, compatível com ES2017+
- Tokens de design: accent `#E05A1E` (var --primary), urgência `#dc2626` (semântico, não accent)
- Dev server: `npx http-server -p 7799 -c-1` na raiz do projeto → `http://localhost:7799`
- Verificação é visual no browser — não há test runner
- Seguir estilo do código existente: `var` para variáveis de estado globais, `const`/`let` dentro de funções

---

## File Structure

Apenas um arquivo é modificado:

- **Modify:** `grv-cs-jornada.html`
  - CSS: adicionar bloco `/* ── CENTRAL DE ATENÇÃO */` após a seção `/* ── MODAL */` (~linha 432)
  - JS — funções novas puras: `isUrgente`, `countUrgentes` após `calcHealthScore` (~linha 1900)
  - JS — estado global: `_urg_filter` após `_proj_tab` (~linha 3497)
  - JS — helpers de popover: `closeProjPops`, `toggleProjPop`, `toggleUrgFilter` após `setProjetosTab` (~linha 3506)
  - JS — funções de ação: `registrarContato`, stubs `openProxAcaoModal` / `closeProxAcaoModal` / `saveProxAcao` (Task 3, substituídas em Task 6)
  - HTML nav: `<span id="nav-urg-badge">` após `nav-proj-subbadge` (~linha 737)
  - HTML modal: `#modal-prox-acao` após `#confirm-overlay` (~linha 854)
  - JS — `updateNavUrgBadge` chamada no final de `renderProjetosGRV` (~linha 4132)
  - Modificações em `renderCustomer` (linhas 3722–3784), `renderImplantacao` (linhas 3885–3916), `renderPortfolio` (linhas 4060–4112)

---

## Task 1: Função `isUrgente`, `countUrgentes` e CSS

**Files:**
- Modify: `grv-cs-jornada.html` — CSS bloco Central de Atenção (~linha 432) + funções JS (~linha 1900)

**Interfaces:**
- Produces:
  - `isUrgente(c: objeto cliente) → boolean` — pura, sem side effects
  - `countUrgentes() → number` — soma todos os clientes urgentes

---

- [ ] **Step 1: Abrir o arquivo e confirmar as linhas de referência**

  Verificar que a linha 432 termina com o bloco CSS `/* ── MODAL */` e que a linha 1872 é `function calcHealthScore`. Isso confirma os pontos de inserção.

  ```
  # No browser: abrir grv-cs-jornada.html e verificar que o app carrega normalmente
  http://localhost:7799
  ```

- [ ] **Step 2: Adicionar CSS do bloco Central de Atenção**

  Inserir após a linha que contém `.modal-footer{` (ao redor da linha 432, dentro do bloco modal CSS — inserir DEPOIS do bloco modal, não dentro):

  ```css
  /* ── CENTRAL DE ATENÇÃO ──────────────────────────────────── */
  .nav-urg-badge{display:inline-flex;align-items:center;justify-content:center;min-width:17px;height:17px;padding:0 4px;border-radius:9px;background:#dc2626;color:#fff;font-size:9.5px;font-weight:900;margin-left:5px;animation:urg-pulse 2.5s ease-in-out infinite;vertical-align:middle}
  @keyframes urg-pulse{0%,100%{box-shadow:0 0 0 0 rgba(220,38,38,.45)}55%{box-shadow:0 0 0 5px rgba(220,38,38,0)}}
  .urg-filter-btn{margin-left:auto;display:inline-flex;align-items:center;gap:7px;padding:6px 14px 6px 11px;border-radius:20px;font-size:12px;font-weight:700;border:1.5px solid;cursor:pointer;background:none;transition:all .15s;line-height:1}
  .urg-filter-btn.off{border-color:var(--border);color:var(--text2)}
  .urg-filter-btn.on{background:rgba(220,38,38,.08);border-color:#dc2626;color:#dc2626}
  .urg-filter-btn .urg-ct{font-size:10px;font-weight:900;min-width:17px;height:17px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;padding:0 4px;background:#dc2626;color:#fff}
  .urg-filter-btn.off .urg-ct{background:var(--text3)}
  .urg-filter-hint{font-size:11.5px;color:var(--text3);margin-bottom:12px;display:flex;align-items:center;gap:4px}
  .urg-filter-hint strong{color:#dc2626;font-weight:700}
  .urg-clear{color:var(--primary);cursor:pointer;font-weight:600;margin-left:6px}
  .urg-clear:hover{text-decoration:underline}
  .proj-ac{position:relative;width:42px;text-align:right;padding:8px 10px !important}
  .proj-dot{width:30px;height:30px;border-radius:8px;border:1px solid var(--border);background:#fff;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:var(--text3);font-size:16px;letter-spacing:.5px;transition:border-color .12s,color .12s,background .12s}
  .proj-dot:hover,.proj-dot.open{border-color:var(--primary);color:var(--primary);background:rgba(224,90,30,.07)}
  .proj-pop{position:absolute;right:0;top:calc(100% + 4px);width:200px;background:#fff;border-radius:10px;box-shadow:0 8px 32px rgba(0,0,0,.13),0 2px 8px rgba(0,0,0,.07);border:1px solid var(--border);z-index:400;overflow:hidden;display:none}
  .proj-pop.vis{display:block}
  .proj-pop-head{padding:8px 14px 7px;border-bottom:1px solid var(--border);font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .proj-pop-item{display:flex;align-items:center;gap:10px;padding:10px 14px;font-size:12.5px;color:var(--text1);cursor:pointer;border-bottom:1px solid var(--border);transition:background .1s}
  .proj-pop-item:last-child{border-bottom:none}
  .proj-pop-item:hover{background:var(--bg)}
  .proj-pop-item.prim{color:var(--primary);font-weight:600}
  .kcard.urgent{border-left:3px solid #dc2626}
  .kcard-urg-row{position:relative;margin-top:8px}
  .kcard-urg-btn{width:100%;display:flex;align-items:center;justify-content:center;gap:5px;padding:5px 0;border-radius:6px;border:1px solid var(--border);background:none;font-size:11.5px;font-weight:700;color:var(--text2);cursor:pointer;transition:background .1s,color .1s}
  .kcard-urg-btn:hover{background:rgba(224,90,30,.07);color:var(--primary);border-color:var(--primary)}
  ```

- [ ] **Step 3: Adicionar `isUrgente` e `countUrgentes` após `calcHealthScore`**

  Localizar a linha que começa com `function calcHealthScore(cliente)` (~linha 1872). Inserir o bloco abaixo APÓS o fechamento desta função (após a chave `}` que encerra `calcHealthScore`, antes de qualquer função seguinte):

  ```javascript
  function isUrgente(c) {
    if (c.status !== 'cs_ativo') {
      // Implantação: urgente se atrasado OU sem contato há mais de 14 dias
      return getStatus(c) === 'Atrasado' || getDiasUltimoContato(c) > 14;
    }
    // Customer / Portfólio: urgente se health crítico OU sem contato há mais de 30 dias
    var h = calcHealthScore(c);
    return (h !== null && h < 40) || getDiasUltimoContato(c) > 30;
  }

  function countUrgentes() {
    return getClientes().filter(isUrgente).length;
  }
  ```

- [ ] **Step 4: Verificar no console do browser**

  Abrir `http://localhost:7799`, abrir DevTools → Console, colar:
  ```javascript
  console.log('isUrgente test:', typeof isUrgente === 'function');
  console.log('countUrgentes:', countUrgentes());
  var clientes = getClientes();
  clientes.slice(0,3).forEach(function(c){ console.log(c.id, isUrgente(c)); });
  ```
  Esperado: `isUrgente test: true`, `countUrgentes` retorna número ≥ 0, e cada cliente mostra `true` ou `false`.

- [ ] **Step 5: Commit**

  ```bash
  git add grv-cs-jornada.html
  git commit -m "feat(central-atencao): isUrgente, countUrgentes e CSS dos componentes"
  ```

---

## Task 2: Badge de Urgências no Nav

**Files:**
- Modify: `grv-cs-jornada.html` — HTML nav (~linha 737) + JS `updateNavUrgBadge` + chamada em `renderProjetosGRV` (~linha 4132)

**Interfaces:**
- Consumes: `countUrgentes() → number` (Task 1)
- Produces:
  - `updateNavUrgBadge() → void` — atualiza `#nav-urg-badge` visualmente

---

- [ ] **Step 1: Inserir o span `#nav-urg-badge` no HTML do nav**

  Localizar a linha 737 (o span `nav-proj-subbadge`):
  ```html
  <span id="nav-proj-subbadge" class="nav-proj-subbadge"></span>
  ```

  Inserir APÓS esse span (antes do SVG do chevron que vem depois):
  ```html
  <span id="nav-urg-badge" class="nav-urg-badge" style="display:none">0</span>
  ```

- [ ] **Step 2: Adicionar a função `updateNavUrgBadge`**

  Localizar `function setProjetosTab(tab)` (~linha 3498). Inserir o bloco abaixo ANTES desta função:

  ```javascript
  function updateNavUrgBadge() {
    var el = document.getElementById('nav-urg-badge');
    if (!el) return;
    var n = countUrgentes();
    el.textContent = n;
    el.style.display = n > 0 ? '' : 'none';
  }
  ```

- [ ] **Step 3: Chamar `updateNavUrgBadge` no final de `renderProjetosGRV`**

  Localizar `renderProjetosGRV` (~linha 4115). A função termina com:
  ```javascript
  if (_proj_tab === 'customer')    { renderCustomer();    return; }
  if (_proj_tab === 'implantacao') { renderImplantacao(); return; }
  renderPortfolio();
  ```

  Modificar para chamar `updateNavUrgBadge()` antes de cada `return` e no final:
  ```javascript
  if (_proj_tab === 'customer')    { renderCustomer();    updateNavUrgBadge(); return; }
  if (_proj_tab === 'implantacao') { renderImplantacao(); updateNavUrgBadge(); return; }
  renderPortfolio();
  updateNavUrgBadge();
  ```

- [ ] **Step 4: Verificar visualmente**

  Abrir `http://localhost:7799`, navegar para Projetos GRV. O badge vermelho pulsante `[N]` deve aparecer ao lado de "· Customer" no nav (se houver clientes urgentes). Se `countUrgentes()` retornar 0, o badge não aparece.

  No console, testar manualmente:
  ```javascript
  updateNavUrgBadge();
  document.getElementById('nav-urg-badge').style.display; // deve ser '' ou 'none'
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add grv-cs-jornada.html
  git commit -m "feat(central-atencao): badge de urgencias no nav"
  ```

---

## Task 3: Customer — Urgentes Filter + `···` Popover

**Files:**
- Modify: `grv-cs-jornada.html` — estado `_urg_filter`, helpers de popover, `setProjetosTab`, `renderCustomer` (linhas 3577–3784)

**Interfaces:**
- Consumes: `isUrgente(c)` (Task 1), `updateNavUrgBadge()` (Task 2)
- Produces:
  - `_urg_filter: boolean` — estado do filtro (global)
  - `toggleUrgFilter(event) → void`
  - `closeProjPops() → void`
  - `toggleProjPop(event, popId, btnId) → void`
  - `registrarContato(clienteId) → void` (stub, completo em Task 6)
  - `openProxAcaoModal(clienteId) → void` (stub, completo em Task 6)

---

- [ ] **Step 1: Adicionar `_urg_filter` e helpers de popover após `_proj_tab`**

  Localizar `let _proj_tab = localStorage.getItem(PROJ_TAB_KEY) || 'implantacao';` (~linha 3495). Inserir após essa linha:

  ```javascript
  var _urg_filter = false;
  ```

  Localizar `function setProjetosTab(tab)` (~linha 3498). Adicionar `_urg_filter = false;` como PRIMEIRA linha do corpo:

  ```javascript
  function setProjetosTab(tab) {
    _urg_filter = false;  // ← linha adicionada
    _proj_tab = tab;
    localStorage.setItem(PROJ_TAB_KEY, tab);
    if (location.hash === '#projetos') {
      renderProjetosGRV();
    } else {
      navigate('projetos');
    }
  }
  ```

  Após o fechamento de `setProjetosTab`, adicionar os helpers:

  ```javascript
  function toggleUrgFilter(event) {
    if (event) event.stopPropagation();
    _urg_filter = !_urg_filter;
    closeProjPops();
    renderProjetosGRV();
  }

  function closeProjPops() {
    document.querySelectorAll('.proj-pop').forEach(function(p){ p.classList.remove('vis'); });
    document.querySelectorAll('.proj-dot').forEach(function(b){ b.classList.remove('open'); });
  }

  function toggleProjPop(event, popId, btnId) {
    event.stopPropagation();
    var pop = document.getElementById(popId);
    var btn = document.getElementById(btnId);
    if (!pop || !btn) return;
    var was = pop.classList.contains('vis');
    closeProjPops();
    if (!was) { pop.classList.add('vis'); btn.classList.add('open'); }
  }

  // Stubs — implementados completamente na Task 6
  function registrarContato(clienteId) {
    closeProjPops();
    _cliente_id_atual = clienteId;
    _cliente_aba = 'atividades';
    navigate('cliente/' + encodeURIComponent(clienteId));
  }

  function openProxAcaoModal(clienteId) {
    // Implementado na Task 6
    console.log('openProxAcaoModal stub:', clienteId);
  }
  ```

  Localizar o final do script (antes de `</script>`). Adicionar:

  ```javascript
  document.addEventListener('click', function(){ closeProjPops(); });
  ```

- [ ] **Step 2: Modificar `renderCustomer` — contagem, filtro e urgentes button**

  Dentro de `renderCustomer` (~linha 3582), após `let filtered = todos;` e os filtros por consultor/ordenação, adicionar:

  ```javascript
  var nUrgCust = todos.filter(isUrgente).length;
  var listClientes = _urg_filter ? filtered.filter(isUrgente) : filtered;
  ```

  Onde `listClientes` será usado no lugar de `filtered` ao construir as linhas da tabela.

- [ ] **Step 3: Adicionar o urgentes button e o hint na seção HTML**

  Localizar a parte final de `renderCustomer` (~linha 3782) onde o `sec.innerHTML` é montado:
  ```javascript
  <div class="proj-sect">Lista de Risco · ordenada por health crescente</div>
  ${filterBar}
  ${tableHtml}`;
  ```

  Substituir por:
  ```javascript
  <div class="proj-sect" style="display:flex;align-items:center">
    Lista de Risco · ordenada por health crescente
    ${nUrgCust > 0
      ? '<button class="urg-filter-btn ' + (_urg_filter ? 'on' : 'off') + '" onclick="toggleUrgFilter(event)">'
        + '<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>'
        + ' Urgentes<span class="urg-ct">' + nUrgCust + '</span>'
        + '</button>'
      : ''}
  </div>
  ${_urg_filter && nUrgCust > 0
    ? '<div class="urg-filter-hint">Mostrando <strong>' + nUrgCust + ' urgentes</strong> de ' + nTotal + ' clientes<span class="urg-clear" onclick="toggleUrgFilter(event)">× Limpar</span></div>'
    : ''}
  ${filterBar}
  ${tableHtml}`;
  ```

- [ ] **Step 4: Adicionar a coluna de ação na tabela de Customer**

  Localizar o cabeçalho da tabela em `renderCustomer` (~linha 3742):
  ```javascript
  '<div class="proj-tw"><table class="proj-rt data-table"><thead><tr><th>Cliente</th><th>CS Responsável</th><th>Health</th><th>CSAT</th><th>Último Contato</th><th>Próxima Ação</th></tr></thead>'
  ```

  Substituir `</tr></thead>` por `<th style="width:48px"></th></tr></thead>`.

  Localizar o row builder dentro de `renderCustomer` (~linha 3722). A variável `rows` é construída com `.map(function(c) { ... })`. Precisa ser mudada para usar `listClientes` e adicionar a célula de ação:

  ```javascript
  var rows = listClientes.map(function(c, i) {
    var health = calcHealthScore(c);
    var csat   = calcCsatAtual(c);
    var dias   = getDiasUltimoContato(c);
    var csNome = (consultores.find(function(x){ return x.id === (c.csId||''); }) || {}).nome || (c.csId||'—');
    var rowCls = health < 40 ? ' class="crit-row"' : health < 70 ? ' class="warn-row"' : '';
    var hpCls  = health >= 70 ? 'ok' : health >= 40 ? 'warn' : 'crit';
    var urgTag = health < 40 ? '<span class="tag-urg">urgente</span> ' : '';
    var pid    = 'pcust' + i;
    var urgAc  = isUrgente(c)
      ? '<td class="proj-ac">'
        + '<button class="proj-dot" id="dot-' + pid + '" onclick="toggleProjPop(event,\'' + pid + '\',\'dot-' + pid + '\')" title="Ações rápidas">···</button>'
        + '<div class="proj-pop" id="' + pid + '">'
        + '<div class="proj-pop-head">' + c.id + '</div>'
        + '<div class="proj-pop-item prim" onclick="registrarContato(\'' + c.id + '\')">💬 Registrar contato</div>'
        + '<div class="proj-pop-item" onclick="openProxAcaoModal(\'' + c.id + '\')">✏️ Atualizar próxima ação</div>'
        + '<div class="proj-pop-item" onclick="navigate(\'cliente/' + encodeURIComponent(c.id) + '\')">↗ Abrir cliente</div>'
        + '</div>'
        + '</td>'
      : '<td class="proj-ac"></td>';
    return '<tr onclick="navigate(\'cliente/'+encodeURIComponent(c.id)+'\')"' + rowCls + '>'
      + '<td><div class="prt-name">'+urgTag+c.id+'</div><div class="prt-sub">'+(c.segmento||c.produto||c.projeto||'')+'</div></td>'
      + '<td style="font-size:12px;color:var(--text2)">'+csNome+'</td>'
      + '<td><span class="proj-hp '+hpCls+'">'+health+'</span></td>'
      + '<td class="csat-star" style="font-size:12px">'+(csat !== null ? '★ '+csat.toFixed(1) : '—')+'</td>'
      + '<td class="'+(dias>30?'prt-dc':'')+'" style="font-size:12px">'+dias+'d</td>'
      + '<td style="font-size:12px;color:var(--text2)">'+(c.proximaAcao||'—')+'</td>'
      + urgAc
      + '</tr>';
  }).join('');
  ```

  Também atualizar `tableHtml` para usar `listClientes` na checagem de lista vazia:
  ```javascript
  var tableHtml = listClientes.length === 0
    ? '<div class="empty-state"><div class="es-icon">⭐</div><div class="es-text">'
      + (_urg_filter ? 'Nenhum cliente urgente no momento.' : 'Nenhum cliente em Customer Success encontrado.')
      + '</div></div>'
    : '<div class="proj-tw"><table class="proj-rt data-table"><thead><tr>'
      + '<th>Cliente</th><th>CS Responsável</th><th>Health</th><th>CSAT</th><th>Último Contato</th><th>Próxima Ação</th><th style="width:48px"></th>'
      + '</tr></thead><tbody>'+rows+'</tbody></table></div>';
  ```

- [ ] **Step 5: Adicionar close-on-scroll na table-wrap**

  Após o `sec.innerHTML = ...` no final de `renderCustomer`, adicionar:
  ```javascript
  var tw = sec.querySelector('.proj-tw');
  if (tw) tw.addEventListener('scroll', closeProjPops, {passive: true});
  ```

- [ ] **Step 6: Verificar visualmente**

  Abrir `http://localhost:7799` → Projetos GRV → Customer (view Lista):
  - O botão ⚡ Urgentes aparece ao lado do título "Lista de Risco" se houver urgentes.
  - Clicar em ⚡ Urgentes filtra a tabela — só aparecem linhas urgentes; hint "Mostrando N urgentes de X clientes" aparece.
  - Clicar em `×` limpa o filtro.
  - As linhas urgentes têm `···` na última coluna; linhas normais não.
  - Clicar em `···` abre o popover com 3 ações.
  - Clicar em "Abrir cliente" navega para o cliente.
  - Clicar em "Registrar contato" navega para o cliente na aba Atividades.
  - Clicar em "Atualizar próxima ação" loga no console (stub).
  - Clicar fora do popover fecha-o.
  - Trocar de aba (ex: Implantação) e voltar para Customer: o filtro reseta.

- [ ] **Step 7: Commit**

  ```bash
  git add grv-cs-jornada.html
  git commit -m "feat(central-atencao): urgentes filter e popover na aba Customer"
  ```

---

## Task 4: Implantação — Urgentes Filter + `···` Popover

**Files:**
- Modify: `grv-cs-jornada.html` — `renderImplantacao` (linhas 3787–3917)

**Interfaces:**
- Consumes: `isUrgente(c)`, `_urg_filter`, `toggleUrgFilter`, `toggleProjPop`, `closeProjPops`, `registrarContato`, `openProxAcaoModal` (Tasks 1–3)

---

- [ ] **Step 1: Adicionar contagem e filtro urgente em `renderImplantacao`**

  Dentro de `renderImplantacao` (~linha 3792), após `let filtered = todos;` e os filtros existentes (consultor, etapa, status), adicionar:

  ```javascript
  var nUrgImpl = todos.filter(isUrgente).length;
  ```

  Na view Lista (bloco `else` em ~linha 3888), onde `filtered` é mapeado para linhas, substituir `filtered` pelo array filtrado:

  ```javascript
  var implClientes = _urg_filter ? filtered.filter(isUrgente) : filtered;
  ```

- [ ] **Step 2: Adicionar urgentes button + hint na view Lista**

  No bloco de `content` da view Lista (~linha 3889), substituir:

  ```javascript
  content = filtered.length === 0
    ? `<div class="empty-state">...</div>`
    : `<div class="table-wrap"><table ...>
         <thead><tr>
           <th>Cliente</th><th>Consultor Digital</th><th>Etapa</th>
           <th style="width:130px">Progresso</th><th>Prazo</th><th>Status</th>
         </tr></thead>
         <tbody>
           ${filtered.map(function(c) {
  ```

  Por:

  ```javascript
  var urgBtnImpl = nUrgImpl > 0
    ? '<button class="urg-filter-btn ' + (_urg_filter ? 'on' : 'off') + '" onclick="toggleUrgFilter(event)">'
      + '<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>'
      + ' Urgentes<span class="urg-ct">' + nUrgImpl + '</span></button>'
    : '';
  var hintImpl = _urg_filter && nUrgImpl > 0
    ? '<div class="urg-filter-hint">Mostrando <strong>' + nUrgImpl + ' urgentes</strong> de ' + todos.length + ' clientes<span class="urg-clear" onclick="toggleUrgFilter(event)">× Limpar</span></div>'
    : '';

  content = implClientes.length === 0
    ? `<div class="empty-state"><div class="es-icon">🔍</div><div class="es-text">${_urg_filter ? 'Nenhum urgente nesta aba.' : 'Nenhum projeto em implantação encontrado.'}</div></div>`
    : `<div style="display:flex;align-items:center;margin-bottom:4px">${urgBtnImpl}</div>
       ${hintImpl}
       <div class="table-wrap">
         <table class="data-table">
           <thead><tr>
             <th>Cliente</th><th>Consultor Digital</th><th>Etapa</th>
             <th style="width:130px">Progresso</th><th>Prazo</th><th>Status</th><th style="width:48px"></th>
           </tr></thead>
           <tbody>
             ${implClientes.map(function(c, i) {
               var prog   = getProgresso(c);
               var st     = getStatus(c);
               var consul = (consultores.find(function(x){ return x.id === c.consultorId; }) || {}).nome || c.consultorId;
               var pid    = 'pimpl' + i;
               var urgAc  = isUrgente(c)
                 ? '<td class="proj-ac">'
                   + '<button class="proj-dot" id="dot-' + pid + '" onclick="toggleProjPop(event,\'' + pid + '\',\'dot-' + pid + '\')" title="Ações rápidas">···</button>'
                   + '<div class="proj-pop" id="' + pid + '">'
                   + '<div class="proj-pop-head">' + c.id + '</div>'
                   + '<div class="proj-pop-item prim" onclick="registrarContato(\'' + c.id + '\')">💬 Registrar contato</div>'
                   + '<div class="proj-pop-item" onclick="openProxAcaoModal(\'' + c.id + '\')">✏️ Atualizar próxima ação</div>'
                   + '<div class="proj-pop-item" onclick="navigate(\'cliente/' + encodeURIComponent(c.id) + '\')">↗ Abrir cliente</div>'
                   + '</div>'
                   + '</td>'
                 : '<td class="proj-ac"></td>';
               var rowUrgCls = isUrgente(c) ? ' class="' + (getStatus(c)==='Atrasado' ? 'crit-row' : 'warn-row') + '"' : '';
               return '<tr onclick="navigate(\'cliente/'+encodeURIComponent(c.id)+'\')"' + rowUrgCls + '>'
                 + '<td><div style="font-weight:600">'+c.id+'</div><div class="proj-id">'+c.projeto+'</div></td>'
                 + '<td style="font-size:12px;color:var(--text2)">'+consul+'</td>'
                 + '<td>'+getEtapaBadge(c.etapa)+'</td>'
                 + '<td><div style="display:flex;align-items:center;gap:8px"><div class="prog-wrap" style="flex:1"><div class="prog-fill" style="width:'+prog+'%"></div></div><span style="font-size:11px;color:var(--text3);white-space:nowrap">'+prog+'%</span></div></td>'
                 + '<td style="font-size:12px;color:'+(st==='Atrasado'?'var(--red)':'var(--text2)')+'">'+fmtDate(c.prazo)+'</td>'
                 + '<td>'+getStatusBadge(st)+'</td>'
                 + urgAc
                 + '</tr>';
             }).join('')}
           </tbody>
         </table>
       </div>`;
  ```

- [ ] **Step 3: Aplicar filtro urgente no Kanban de Implantação**

  Localizar a chamada do Kanban em `renderImplantacao` (~linha 3887):
  ```javascript
  content = renderKanbanBoard(filtered, consultores, false);
  ```

  Substituir por:
  ```javascript
  var kImplClientes = _urg_filter ? filtered.filter(isUrgente) : filtered;
  content = renderKanbanBoard(kImplClientes, consultores, false);
  ```

- [ ] **Step 4: Adicionar `···` nos cards Kanban urgentes**

  Localizar `renderKanbanBoard` (~linha 3412). Dentro do `.map(c => { ... })` dos cards (~linha 3423), APÓS `return \``, adicionar ao template do card:

  Antes do fechamento do `div.kcard`, inserir:
  ```javascript
  ${isUrgente(c) ? `<div class="kcard-urg-row">
    <button class="kcard-urg-btn" onclick="event.stopPropagation();toggleProjPop(event,'pkb${c.id.replace(/\W/g,'')}','dkb${c.id.replace(/\W/g,'')}')">··· Ações rápidas</button>
    <div class="proj-pop" id="pkb${c.id.replace(/\W/g,'')}" style="top:auto;bottom:calc(100% + 4px)">
      <div class="proj-pop-head">${c.id}</div>
      <div class="proj-pop-item prim" onclick="registrarContato('${c.id}')">💬 Registrar contato</div>
      <div class="proj-pop-item" onclick="openProxAcaoModal('${c.id}')">✏️ Atualizar próxima ação</div>
      <div class="proj-pop-item" onclick="navigate('cliente/${encodeURIComponent(c.id)}')">↗ Abrir cliente</div>
    </div>
  </div>` : ''}
  ```

  E adicionar `${isUrgente(c) ? ' urgent' : ''}` à classe do `.kcard`:
  ```javascript
  <div class="kcard${isUrgente(c) ? ' urgent' : ''}" ...>
  ```

- [ ] **Step 5: Adicionar close-on-scroll na table-wrap de Implantação**

  Após o `sec.innerHTML = ...` no final de `renderImplantacao`:
  ```javascript
  var twImpl = sec.querySelector('.table-wrap');
  if (twImpl) twImpl.addEventListener('scroll', closeProjPops, {passive: true});
  ```

- [ ] **Step 6: Verificar visualmente**

  Abrir `http://localhost:7799` → Projetos GRV → Implantação (view Lista):
  - Botão ⚡ Urgentes aparece (se houver urgentes).
  - Filtro funciona, hint aparece.
  - `···` só em linhas urgentes; popover com 3 ações.
  - Mudar para Kanban: cards urgentes têm borda vermelha e botão "··· Ações rápidas"; cards normais, não.

- [ ] **Step 7: Commit**

  ```bash
  git add grv-cs-jornada.html
  git commit -m "feat(central-atencao): urgentes filter e popover na aba Implantacao"
  ```

---

## Task 5: Portfólio — Urgentes Filter + `···` Popover

**Files:**
- Modify: `grv-cs-jornada.html` — `renderPortfolio` (linhas 3919–4113)

**Interfaces:**
- Consumes: `isUrgente(c)`, `_urg_filter`, `toggleUrgFilter`, `toggleProjPop`, `closeProjPops`, `registrarContato`, `openProxAcaoModal` (Tasks 1–3)

---

- [ ] **Step 1: Adicionar contagem urgente em `renderPortfolio`**

  Dentro de `renderPortfolio` (~linha 3919), após `const todos = getClientes();`, adicionar:
  ```javascript
  var nUrgPort = todos.filter(isUrgente).length;
  ```

- [ ] **Step 2: Modificar a view Lista de Portfólio**

  Localizar o bloco `if (_proj_view === 'lista')` (~linha 4061). A lista usa `filtered` no `.map()`. Adicionar `var portClientes` e o urgentes button:

  ```javascript
  if (_proj_view === 'lista') {
    var portClientes = _urg_filter ? filtered.filter(isUrgente) : filtered;
    var urgBtnPort = nUrgPort > 0
      ? '<button class="urg-filter-btn ' + (_urg_filter ? 'on' : 'off') + '" onclick="toggleUrgFilter(event)">'
        + '<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>'
        + ' Urgentes<span class="urg-ct">' + nUrgPort + '</span></button>'
      : '';
    var hintPort = _urg_filter && nUrgPort > 0
      ? '<div class="urg-filter-hint">Mostrando <strong>' + nUrgPort + ' urgentes</strong> de ' + todos.length + ' clientes<span class="urg-clear" onclick="toggleUrgFilter(event)">× Limpar</span></div>'
      : '';

    content = portClientes.length === 0
      ? `<div class="empty-state"><div class="es-icon">🔍</div><div class="es-text">${_urg_filter ? 'Nenhum urgente nesta aba.' : 'Nenhum projeto encontrado com este filtro.'}</div></div>`
      : `<div style="display:flex;align-items:center;margin-bottom:4px">${urgBtnPort}</div>
         ${hintPort}
         <div class="table-wrap">
           <table class="data-table">
             <thead><tr>
               <th>Cliente</th><th>Consultor</th><th>Etapa</th><th>Status</th>
               <th style="width:130px">Progresso</th><th>Prazo</th><th style="width:48px"></th>
             </tr></thead>
             <tbody>
               ${portClientes.map(function(c, i) {
                 var prog   = getProgresso(c);
                 var st     = getStatus(c);
                 var consul = (consultores.find(function(x){ return x.id === c.consultorId; }) || {}).nome || c.consultorId;
                 var pid    = 'pport' + i;
                 var urgAc  = isUrgente(c)
                   ? '<td class="proj-ac">'
                     + '<button class="proj-dot" id="dot-' + pid + '" onclick="toggleProjPop(event,\'' + pid + '\',\'dot-' + pid + '\')" title="Ações rápidas">···</button>'
                     + '<div class="proj-pop" id="' + pid + '">'
                     + '<div class="proj-pop-head">' + c.id + '</div>'
                     + '<div class="proj-pop-item prim" onclick="registrarContato(\'' + c.id + '\')">💬 Registrar contato</div>'
                     + '<div class="proj-pop-item" onclick="openProxAcaoModal(\'' + c.id + '\')">✏️ Atualizar próxima ação</div>'
                     + '<div class="proj-pop-item" onclick="navigate(\'cliente/' + encodeURIComponent(c.id) + '\')">↗ Abrir cliente</div>'
                     + '</div>'
                     + '</td>'
                   : '<td class="proj-ac"></td>';
                 return '<tr onclick="navigate(\'cliente/'+encodeURIComponent(c.id)+'\')">'
                   + '<td><div style="font-weight:600">'+c.id+'</div><div class="proj-id">'+c.projeto+'</div></td>'
                   + '<td style="font-size:12px;color:var(--text2)">'+consul+'</td>'
                   + '<td>'+getEtapaBadge(c.etapa)+'</td>'
                   + '<td>'+getStatusBadge(st)+'</td>'
                   + '<td><div style="display:flex;align-items:center;gap:8px"><div class="prog-wrap" style="flex:1"><div class="prog-fill" style="width:'+prog+'%"></div></div><span style="font-size:11px;color:var(--text3);white-space:nowrap">'+prog+'%</span></div></td>'
                   + '<td style="font-size:12px;color:'+(st==='Atrasado'?'var(--red)':'var(--text2)')+'">'+fmtDate(c.prazo)+'</td>'
                   + urgAc
                   + '</tr>';
               }).join('')}
             </tbody>
           </table>
         </div>`;
  ```

- [ ] **Step 3: Aplicar filtro urgente no Kanban de Portfólio**

  Localizar a chamada do Kanban em `renderPortfolio` (~linha 4088):
  ```javascript
  content = renderKanbanBoard(filtered, consultores, false);
  ```
  Substituir por:
  ```javascript
  var kPortClientes = _urg_filter ? filtered.filter(isUrgente) : filtered;
  content = renderKanbanBoard(kPortClientes, consultores, false);
  ```
  (O `···` nos cards Kanban já foi adicionado em `renderKanbanBoard` na Task 4 — funciona aqui também.)

- [ ] **Step 4: Adicionar close-on-scroll na table-wrap de Portfólio**

  Após o `sec.innerHTML = ...` no final de `renderPortfolio`:
  ```javascript
  var twPort = sec.querySelector('.table-wrap');
  if (twPort) twPort.addEventListener('scroll', closeProjPops, {passive: true});
  ```

- [ ] **Step 5: Verificar visualmente**

  Abrir `http://localhost:7799` → Projetos GRV → Portfólio (view Lista):
  - Botão ⚡ Urgentes aparece, filtra, hint aparece.
  - `···` só em linhas urgentes.
  - Mudar para Kanban: cards urgentes com "··· Ações rápidas".
  - Mudar para Dashboard: nenhum botão Urgentes aparece (view Dashboard não tem o botão).

- [ ] **Step 6: Commit**

  ```bash
  git add grv-cs-jornada.html
  git commit -m "feat(central-atencao): urgentes filter e popover na aba Portfolio"
  ```

---

## Task 6: Modal "Atualizar Próxima Ação"

**Files:**
- Modify: `grv-cs-jornada.html` — HTML modal (~linha 854) + funções JS `openProxAcaoModal`, `closeProxAcaoModal`, `saveProxAcao`

**Interfaces:**
- Consumes: `getCliente(id)`, `saveCliente(updated)`, `renderProjetosGRV()`, `closeProjPops()`
- Produces:
  - `openProxAcaoModal(clienteId) → void` — sobrescreve o stub da Task 3
  - `closeProxAcaoModal() → void`
  - `saveProxAcao() → void`

---

- [ ] **Step 1: Adicionar HTML do modal**

  Localizar o `#confirm-overlay` (~linha 853). Inserir ANTES dele:

  ```html
  <!-- ── MODAL ATUALIZAR PRÓXIMA AÇÃO ──────────────────────── -->
  <div class="modal-overlay hidden" id="modal-prox-acao">
    <div class="modal-box" onclick="event.stopPropagation()">
      <h3 id="modal-prox-acao-titulo">Próxima Ação</h3>
      <label class="modal-label">Próxima ação para este cliente</label>
      <textarea id="modal-prox-acao-txt"
        style="width:100%;min-height:80px;resize:vertical;border:1px solid var(--border);border-radius:6px;padding:8px 10px;font-size:13px;font-family:inherit;line-height:1.5"
        placeholder="Descreva a próxima ação..."></textarea>
      <div class="modal-footer" style="margin-top:16px;display:flex;gap:8px;justify-content:flex-end">
        <button class="btn btn-ghost" onclick="closeProxAcaoModal()">Cancelar</button>
        <button class="btn btn-primary" onclick="saveProxAcao()">Salvar</button>
      </div>
    </div>
  </div>
  ```

- [ ] **Step 2: Adicionar as funções do modal**

  Localizar a seção JS próxima de `openModal` / `closeModal` (~linha 5387). Adicionar o bloco abaixo no mesmo agrupamento:

  ```javascript
  // ─── Modal Atualizar Próxima Ação ──────────────────────────
  var _prox_acao_cliente_id = null;

  function openProxAcaoModal(clienteId) {
    closeProjPops();
    var c = getCliente(clienteId);
    if (!c) return;
    _prox_acao_cliente_id = clienteId;
    document.getElementById('modal-prox-acao-titulo').textContent = c.id + ' — Próxima Ação';
    document.getElementById('modal-prox-acao-txt').value = c.proximaAcao || '';
    document.getElementById('modal-prox-acao').classList.remove('hidden');
    setTimeout(function(){ document.getElementById('modal-prox-acao-txt').focus(); }, 50);
  }

  function closeProxAcaoModal() {
    document.getElementById('modal-prox-acao').classList.add('hidden');
    _prox_acao_cliente_id = null;
  }

  function saveProxAcao() {
    if (!_prox_acao_cliente_id) return;
    var c = getCliente(_prox_acao_cliente_id);
    if (!c) return;
    c.proximaAcao = document.getElementById('modal-prox-acao-txt').value.trim();
    saveCliente(c);
    closeProxAcaoModal();
    renderProjetosGRV();
  }

  document.getElementById('modal-prox-acao').addEventListener('click', function(e){
    if (e.target === this) closeProxAcaoModal();
  });
  ```

- [ ] **Step 3: Verificar visualmente**

  Abrir `http://localhost:7799` → Projetos GRV → Customer → ⚡ Urgentes → clicar `···` em linha urgente → "✏️ Atualizar próxima ação":
  - Modal abre com o nome do cliente no título.
  - Textarea pré-preenchida com o valor atual de `proximaAcao`.
  - Editar o texto → Salvar: modal fecha, lista re-renderiza com o novo valor na coluna "Próxima Ação".
  - Clicar em Cancelar ou fora do modal fecha sem salvar.
  - Verificar o mesmo fluxo nas abas Implantação e Portfólio.

- [ ] **Step 4: Verificar `registrarContato` na aba Atividades**

  Clicar `···` em linha urgente → "💬 Registrar contato":
  - Deve navegar para `#cliente/ID` e abrir a aba Atividades (não a aba 360).
  - Verificar que `_cliente_aba` está correto inspecionando o DOM: a aba ativa no detail deve ser "Atividades".

- [ ] **Step 5: Commit final**

  ```bash
  git add grv-cs-jornada.html
  git commit -m "feat(central-atencao): modal atualizar proxima acao + registrar contato"
  ```

---

## Self-Review

**Spec coverage check:**
- ✅ Badge `#nav-urg-badge` no nav — Task 2
- ✅ `isUrgente` centralizado — Task 1
- ✅ Botão ⚡ Urgentes por aba (Customer/Implantação/Portfólio) — Tasks 3-5
- ✅ Não aparece na view Dashboard — Tasks 3-5 (button está dentro do bloco de lista, não do dashboard)
- ✅ `···` só em linhas urgentes — Tasks 3-5
- ✅ Popover com 3 ações — Tasks 3-5
- ✅ "Registrar contato" → aba Atividades — Task 3 (`registrarContato`)
- ✅ "Atualizar próxima ação" → modal inline — Tasks 3 (stub) + Task 6 (implementação)
- ✅ "Abrir cliente" → `navigate('cliente/' + id)` — Tasks 3-5
- ✅ Fechar popover ao clicar fora — Task 3 (`document.addEventListener('click', closeProjPops)`)
- ✅ Fechar popover ao scroll — Tasks 3-5 (listener na table-wrap)
- ✅ `···` em card Kanban urgente — Task 4 (em `renderKanbanBoard`, reutilizado em Task 5)
- ✅ Estado não persiste entre trocas de aba — `_urg_filter = false` em `setProjetosTab`
- ✅ Badge oculto quando count = 0 — Task 2 (`style.display = n > 0 ? '' : 'none'`)
- ✅ `updateNavUrgBadge` chamada após cada render de aba — Task 2
