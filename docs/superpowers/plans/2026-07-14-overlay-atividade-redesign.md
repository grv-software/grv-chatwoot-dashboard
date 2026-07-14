# Overlay de Atividade — Redesign Premium (6 Zonas)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesenhar o painel lateral de detalhe de atividade (`#ov-panel`) com 6 zonas visuais: stripe de status, header compacto 2-linhas, KPI strip, tabs, body e footer integrado.

**Architecture:** Todo o trabalho é no arquivo único `grv-cs-jornada.html`. CSS primeiro (Task 1), depois HTML estático (Task 2), depois JS (Task 3). Cada task é independente e commitável. Nenhuma lógica de negócio muda — só apresentação.

**Tech Stack:** HTML/CSS/JS puro, arquivo único `grv-cs-jornada.html`, branch `alteracoes`.

## Global Constraints

- Arquivo único: `grv-cs-jornada.html` — todas as edições aqui.
- Branch: `alteracoes`. Nunca commitar em `main`.
- Todos os `id="ov-*"` existentes devem ser preservados (JS depende deles).
- Não alterar lógica de `concluirAtividade()`, `reabrirAtividade()`, `addOvRegistro()`, `renderOvChecklist()`, `renderOvAnotacao()`.
- Verificação = abrir `grv-cs-jornada.html` no Chrome, clicar numa atividade e observar o painel.

---

### Task 1: CSS — substituir seletores do overlay

**Files:**
- Modify: `grv-cs-jornada.html` — linhas 513–527 (`.ov-hd` … `.ov-dates-row`), linhas 610–614 (`.ov-reg-form` … `.ov-reg-send`), linha 519–521 (`.ov-tabs`, `.ov-tab`, `.ov-tab.active`), linhas 522–526 (`.ov-body`, `.ov-footer`, `.ov-btn-concluir`)

**Interfaces:**
- Consumes: nada de outras tasks.
- Produces: classes CSS usadas pelo HTML da Task 2 e pelo JS da Task 3.

- [ ] **Step 1: Substituir seletores `.ov-hd` … `.ov-dates-row` (linhas 513–527)**

Localizar e substituir o bloco exato:
```css
.ov-hd{padding:14px 16px 0;border-bottom:1px solid var(--border-2);flex-shrink:0}
.ov-hd-top{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:10px}
.ov-title{font-size:14px;font-weight:800;color:var(--text);flex:1;margin-right:12px;line-height:1.3}
.ov-close{width:28px;height:28px;border-radius:7px;border:1px solid var(--border);background:var(--surface);display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:14px;color:var(--text3);flex-shrink:0}
.ov-close:hover{background:var(--border-2)}
.ov-meta{display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap}
.ov-tabs{display:flex}
.ov-tab{padding:8px 14px;font-size:12px;font-weight:600;color:var(--text3);cursor:pointer;border-bottom:2px solid transparent;transition:all .12s}
.ov-tab.active{color:var(--primary);border-bottom-color:var(--primary)}
.ov-body{flex:1;overflow-y:auto;padding:16px}
.ov-footer{padding:12px 16px;border-top:1px solid var(--border-2);flex-shrink:0;background:var(--surface)}
.ov-btn-concluir{width:100%;padding:10px;background:var(--green);color:#fff;border:none;border-radius:9px;font-size:13px;font-weight:700;cursor:pointer;transition:opacity .15s}
.ov-btn-concluir:hover{opacity:.88}
.ov-btn-concluir.done{background:var(--border-2);color:var(--text3);cursor:default}
.ov-dates-row{display:flex;gap:10px;padding:8px 0 4px}
```

Pelo bloco novo:
```css
/* ── OVERLAY PANEL — 6 zonas ───────────────────────────── */
.ov-stripe{height:4px;flex-shrink:0;transition:background .2s}
.ov-head{border-bottom:1px solid var(--border-2);flex-shrink:0}
.ov-head-row1{display:flex;align-items:center;justify-content:space-between;padding:16px 18px 8px;position:relative;gap:8px}
.ov-head-title{font-size:18px;font-weight:800;color:var(--text);flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;letter-spacing:-.5px;line-height:1.1}
.ov-tag{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.09em;padding:3px 9px;border-radius:12px;flex-shrink:0;white-space:nowrap;display:inline-flex;align-items:center;gap:4px}
.ov-tag-dot{width:5px;height:5px;border-radius:50%;flex-shrink:0}
.ov-head-row2{padding:0 18px 12px;font-size:11px;color:var(--text4);display:flex;align-items:center;gap:5px;flex-wrap:wrap;line-height:1.4}
.ov-head-row2 b{color:var(--text3);font-weight:600}
.ov-head-av{width:16px;height:16px;border-radius:4px;background:linear-gradient(135deg,var(--primary),#ff8c5a);display:inline-flex;align-items:center;justify-content:center;font-size:7px;font-weight:800;color:#fff;flex-shrink:0;vertical-align:middle}
.ov-kpi-strip{display:grid;grid-template-columns:1fr 1fr 1fr}
.ov-kpi-cell{padding:10px 14px;border-right:1px solid var(--border-2);border-top:1px solid var(--border-2)}
.ov-kpi-cell:last-child{border-right:none}
.ov-kpi-label{font-size:8px;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:var(--text4);margin-bottom:3px}
.ov-kpi-val{font-size:13px;font-weight:800;color:var(--text);letter-spacing:-.2px}
.ov-kpi-urgency{font-size:9px;font-weight:700;margin-top:2px}
.ov-kpi-input{display:none}
.ov-kpi-prog-track{height:3px;background:var(--border-2);border-radius:2px;overflow:hidden;margin-top:5px}
.ov-kpi-prog-fill{height:100%;border-radius:2px;transition:width .3s}
.ov-close{width:26px;height:26px;border-radius:7px;border:1px solid var(--border);background:var(--surface);display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:13px;color:var(--text3);flex-shrink:0}
.ov-close:hover{background:var(--border-2)}
.ov-tabs{display:flex;border-bottom:1px solid var(--border-2)}
.ov-tab{flex:1;text-align:center;padding:10px 0;font-size:11px;font-weight:600;color:var(--text3);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;transition:all .12s}
.ov-tab.active{color:var(--primary);border-bottom-color:var(--primary)}
.ov-body{flex:1;overflow-y:auto;padding:16px 20px}
.ov-footer{padding:11px 20px;border-top:1px solid var(--border-2);flex-shrink:0;background:var(--bg);display:flex;align-items:center;justify-content:space-between;gap:12px}
.ov-footer-prog{font-size:11px;color:var(--text3);white-space:nowrap}
.ov-footer-prog strong{font-weight:800;color:var(--green)}
.ov-btn-concluir{padding:9px 20px;background:var(--primary);color:#fff;border:1.5px solid transparent;border-radius:9px;font-size:12px;font-weight:700;cursor:pointer;transition:opacity .15s;white-space:nowrap;flex-shrink:0}
.ov-btn-concluir:hover{opacity:.88}
.ov-btn-concluir.done{background:transparent;color:var(--green);border-color:var(--green);cursor:default;opacity:1}
```

- [ ] **Step 2: Atualizar seletores `.ov-reg-form` … `.ov-reg-send` (linhas 610–614)**

Localizar e substituir:
```css
.ov-reg-form{display:flex;gap:8px;margin-bottom:16px}
.ov-reg-av{width:28px;height:28px;border-radius:7px;background:linear-gradient(135deg,var(--primary),#ff8c5a);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;color:#fff;flex-shrink:0;margin-top:2px}
.ov-reg-wrap{flex:1;background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-sm);padding:8px 12px}
.ov-reg-ta{border:none;outline:none;font-size:12px;color:var(--text);background:transparent;width:100%;resize:none;font-family:inherit;min-height:40px}
.ov-reg-send{float:right;margin-top:6px;padding:5px 12px;background:var(--primary);color:#fff;border:none;border-radius:7px;font-size:11px;font-weight:700;cursor:pointer}
```

Pelo bloco novo:
```css
.ov-reg-form{display:flex;gap:9px;margin-bottom:16px;align-items:flex-start}
.ov-reg-av{width:28px;height:28px;border-radius:8px;background:linear-gradient(135deg,var(--primary),#ff8c5a);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:800;color:#fff;flex-shrink:0;margin-top:1px}
.ov-reg-wrap{flex:1}
.ov-reg-ta{width:100%;background:var(--bg);border:1.5px solid var(--border);border-radius:9px;padding:9px 12px;font-size:12px;color:var(--text);resize:none;min-height:56px;box-sizing:border-box;font-family:inherit;line-height:1.5;outline:none;transition:border-color .12s}
.ov-reg-ta:focus{border-color:var(--primary)}
.ov-reg-actions{display:flex;justify-content:space-between;align-items:center;margin-top:7px}
.ov-reg-hint{font-size:10px;color:var(--text4)}
.ov-reg-send{padding:6px 16px;background:var(--primary);color:#fff;border:none;border-radius:7px;font-size:11px;font-weight:700;cursor:pointer}
```

- [ ] **Step 3: Verificar**

Abrir `grv-cs-jornada.html` no Chrome → F12 → verificar que as classes novas estão no DevTools e não há erros de CSS no console.

O painel de atividade ainda não estará correto visualmente (o HTML ainda é o antigo). Isso é esperado — Task 2 corrige.

- [ ] **Step 4: Commit**

```
git add grv-cs-jornada.html
git commit -m "style(overlay): novos seletores CSS — 6 zonas stripe/head/kpi/tabs/body/footer"
```

---

### Task 2: HTML — reescrever `<div class="ov-panel">` (linhas 998–1039)

**Files:**
- Modify: `grv-cs-jornada.html` — linhas 998–1039

**Interfaces:**
- Consumes: classes CSS definidas na Task 1.
- Produces: IDs `ov-stripe`, `ov-titulo`, `ov-tag`, `ov-meta`, `ov-kpi-inicio`, `ov-kpi-prazo`, `ov-kpi-urgency`, `ov-kpi-prog`, `ov-kpi-prog-fill`, `ov-data-inicio`, `ov-data-fim`, `ov-body`, `ov-footer-prog`, `ov-btn-concluir` — todos consumidos pelo JS da Task 3.

- [ ] **Step 1: Substituir o bloco HTML do painel (linhas 998–1039)**

Localizar:
```html
<div class="ov-panel" id="ov-panel">
  <div class="ov-hd">
    <div class="ov-hd-top" style="position:relative">
      <div class="ov-title" id="ov-titulo">Atividade</div>
      <div style="display:flex;align-items:center;gap:4px;flex-shrink:0">
        <div class="ov-menu-btn" onclick="toggleOvMenu(event)" title="Mais opções">···</div>
        <div class="ov-close" onclick="closeAtividade()">✕</div>
      </div>
      <div class="ov-dropdown" id="ov-dropdown" style="display:none">
        <button class="ov-dropdown-item" onclick="editarNomeAtiv()">✎ Editar nome</button>
        <button class="ov-dropdown-item" onclick="alterarRespAtiv()">👤 Alterar responsável</button>
        <button class="ov-dropdown-item" onclick="alterarPrazoAtiv()">📅 Alterar prazo</button>
        <button class="ov-dropdown-item" id="ov-btn-reabrir" style="display:none" onclick="reabrirAtividade()">↩ Reabrir</button>
        <div class="ov-dropdown-divider"></div>
        <button class="ov-dropdown-item danger" onclick="excluirAtividade()">🗑 Excluir atividade</button>
      </div>
    </div>
    <div class="ov-meta" id="ov-meta"></div>
    <div id="ov-deadline-wrap" style="display:none;padding:4px 0 0;font-size:11px;font-weight:600">
      <span id="ov-deadline"></span>
    </div>
    <div class="ov-dates-row">
      <div style="flex:1">
        <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--text4);margin-bottom:3px">Início</div>
        <input type="date" id="ov-data-inicio" onchange="saveOvDatas()" style="width:100%;border:1px solid var(--border);border-radius:6px;padding:5px 8px;font-size:11px;color:var(--text);background:var(--bg);outline:none;cursor:pointer">
      </div>
      <div style="flex:1">
        <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--text4);margin-bottom:3px">Meta (fim)</div>
        <input type="date" id="ov-data-fim" onchange="saveOvDatas()" style="width:100%;border:1px solid var(--border);border-radius:6px;padding:5px 8px;font-size:11px;color:var(--text);background:var(--bg);outline:none;cursor:pointer">
      </div>
    </div>
    <div class="ov-tabs">
      <div class="ov-tab active" onclick="setOverlayTab('registro',this)">Registro</div>
      <div class="ov-tab" onclick="setOverlayTab('checklist',this)">Checklist</div>
      <div class="ov-tab" onclick="setOverlayTab('anotacao',this)">Anotação</div>
    </div>
  </div>
  <div class="ov-body" id="ov-body"></div>
  <div class="ov-footer">
    <button class="ov-btn-concluir" id="ov-btn-concluir" onclick="concluirAtividade()">✓ Marcar como Concluída</button>
  </div>
</div>
```

Substituir por:
```html
<div class="ov-panel" id="ov-panel">
  <!-- Zona 1: Stripe de status -->
  <div class="ov-stripe" id="ov-stripe"></div>
  <!-- Zona 2: Header -->
  <div class="ov-head">
    <div class="ov-head-row1">
      <div class="ov-head-title" id="ov-titulo">Atividade</div>
      <div style="display:flex;align-items:center;gap:4px;flex-shrink:0">
        <span class="ov-tag" id="ov-tag"><span class="ov-tag-dot" id="ov-tag-dot"></span><span id="ov-tag-lbl">Pendente</span></span>
        <div class="ov-menu-btn" onclick="toggleOvMenu(event)" title="Mais opções">···</div>
        <div class="ov-close" onclick="closeAtividade()">✕</div>
      </div>
      <div class="ov-dropdown" id="ov-dropdown" style="display:none">
        <button class="ov-dropdown-item" onclick="editarNomeAtiv()">✎ Editar nome</button>
        <button class="ov-dropdown-item" onclick="alterarRespAtiv()">👤 Alterar responsável</button>
        <button class="ov-dropdown-item" onclick="alterarPrazoAtiv()">📅 Alterar prazo</button>
        <button class="ov-dropdown-item" id="ov-btn-reabrir" style="display:none" onclick="reabrirAtividade()">↩ Reabrir</button>
        <div class="ov-dropdown-divider"></div>
        <button class="ov-dropdown-item danger" onclick="excluirAtividade()">🗑 Excluir atividade</button>
      </div>
    </div>
    <div class="ov-head-row2" id="ov-meta"></div>
    <!-- Zona 3: KPI Strip -->
    <div class="ov-kpi-strip">
      <div class="ov-kpi-cell" onclick="document.getElementById('ov-data-inicio').showPicker&&document.getElementById('ov-data-inicio').showPicker()" style="cursor:pointer">
        <div class="ov-kpi-label">Início</div>
        <div class="ov-kpi-val" id="ov-kpi-inicio">—</div>
        <input type="date" id="ov-data-inicio" class="ov-kpi-input" onchange="saveOvDatas()">
      </div>
      <div class="ov-kpi-cell" onclick="document.getElementById('ov-data-fim').showPicker&&document.getElementById('ov-data-fim').showPicker()" style="cursor:pointer">
        <div class="ov-kpi-label">Prazo</div>
        <div class="ov-kpi-val" id="ov-kpi-prazo">—</div>
        <div class="ov-kpi-urgency" id="ov-kpi-urgency"></div>
        <input type="date" id="ov-data-fim" class="ov-kpi-input" onchange="saveOvDatas()">
      </div>
      <div class="ov-kpi-cell">
        <div class="ov-kpi-label">Progresso</div>
        <div class="ov-kpi-val" id="ov-kpi-prog">—</div>
        <div class="ov-kpi-prog-track"><div class="ov-kpi-prog-fill" id="ov-kpi-prog-fill" style="width:0%"></div></div>
      </div>
    </div>
    <!-- Zona 4: Tabs -->
    <div class="ov-tabs">
      <div class="ov-tab active" onclick="setOverlayTab('registro',this)">Registro</div>
      <div class="ov-tab" onclick="setOverlayTab('checklist',this)">Checklist</div>
      <div class="ov-tab" onclick="setOverlayTab('anotacao',this)">Anotação</div>
    </div>
  </div>
  <!-- Zona 5: Body -->
  <div class="ov-body" id="ov-body"></div>
  <!-- Zona 6: Footer -->
  <div class="ov-footer">
    <span class="ov-footer-prog" id="ov-footer-prog"></span>
    <button class="ov-btn-concluir" id="ov-btn-concluir" onclick="concluirAtividade()">✓ Marcar como Concluída</button>
  </div>
</div>
```

- [ ] **Step 2: Verificar**

Abrir `grv-cs-jornada.html` no Chrome → clicar numa atividade → o painel deve abrir com a nova estrutura. Esperado:
- Stripe vazia no topo (será preenchida pelo JS na Task 3)
- Título grande no header
- Tag "Pendente" visível
- KPI strip com 3 colunas "—"
- Tabs Registro / Checklist / Anotação
- Footer com botão à direita

- [ ] **Step 3: Commit**

```
git add grv-cs-jornada.html
git commit -m "feat(overlay): novo HTML do painel — 6 zonas stripe/head/kpi/body/footer"
```

---

### Task 3: JS — atualizar `openAtividade()`, `renderOvRegistro()` e `saveOvDatas()`

**Files:**
- Modify: `grv-cs-jornada.html` — função `openAtividade()` (linha ~6140), `renderOvRegistro()` (linha ~6251), `saveOvDatas()` (linha ~6301)

**Interfaces:**
- Consumes: IDs do HTML definidos na Task 2.
- Produces: overlay totalmente funcional com stripe colorida, meta inline, KPI preenchidos e footer com progresso.

- [ ] **Step 1: Substituir o corpo de `openAtividade()` (linhas 6140–6222)**

Localizar a função completa:
```javascript
function openAtividade(cId, pbId, atId) {
  _ov_cId = cId; _ov_pbId = pbId; _ov_atId = atId;
  const c  = getCliente(cId);
  const pb = (c?.ativPlaybooks || []).find(p => p.id === pbId);
  if ((pb?.status || 'ativo') === 'cancelado') return;
  const at = (pb?.atividades || []).find(a => a.id === atId);
  if (!at) return;

  document.getElementById('ov-titulo').textContent = at.nome || at.titulo || '—';

  const stBg  = {concluida:'var(--b-green-bg)',atrasada:'var(--b-red-bg)',pendente:'var(--border-2)',em_andamento:'var(--b-blue-bg)'};
  const stClr = {concluida:'var(--green)',atrasada:'var(--red)',pendente:'var(--text3)',em_andamento:'var(--blue)'};
  const stLbl = {concluida:'Concluída',atrasada:'Atrasada',pendente:'Pendente',em_andamento:'Em andamento'};
  const resp  = at.responsavelId || pb.donoId || '?';
  const st    = at.status || 'pendente';

  document.getElementById('ov-meta').innerHTML =
    '<span style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--text2)">' +
      '<span style="width:20px;height:20px;border-radius:5px;background:linear-gradient(135deg,var(--primary),#ff8c5a);display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:800;color:#fff">' +
        resp[0].toUpperCase() +
      '</span>' +
      resp +
    '</span>' +
    '<span class="status-badge" style="background:' + (stBg[st]||'var(--border-2)') + ';color:' + (stClr[st]||'var(--text3)') + '">' +
      (stLbl[st]||st) +
    '</span>';

  // Datas de início e fim
  const diInput = document.getElementById('ov-data-inicio');
  const dfInput = document.getElementById('ov-data-fim');
  if (diInput) diInput.value = at.dataInicio ? at.dataInicio.split('T')[0] : '';
  if (dfInput) dfInput.value = at.dataLimite ? at.dataLimite.split('T')[0] : '';

  // Botão Concluir
  const btnC = document.getElementById('ov-btn-concluir');
  if (btnC) {
    if (at.status === 'concluida') {
      btnC.textContent = '✓ Concluída';
      btnC.classList.add('done');
      btnC.onclick = null;
    } else {
      btnC.textContent = '✓ Marcar como Concluída';
      btnC.classList.remove('done');
      btnC.onclick = concluirAtividade;
    }
  }

  const dlWrap = document.getElementById('ov-deadline-wrap');
  const dlSpan = document.getElementById('ov-deadline');
  if (dlWrap && dlSpan) {
    if (at.dataLimite && at.status !== 'concluida') {
      const hoje2 = new Date(); hoje2.setHours(0,0,0,0);
      const dlDate = new Date(at.dataLimite + 'T00:00:00');
      const diffMs = dlDate - hoje2;
      const diffD  = Math.round(diffMs / 86400000);
      const ddmm   = dlDate.toLocaleDateString('pt-BR', {day:'2-digit', month:'2-digit'});
      if (diffD < 0) {
        dlSpan.innerHTML = '<span style="color:var(--red)">⏰ Vencida há ' + Math.abs(diffD) + ' dia' + (Math.abs(diffD)!==1?'s':'') + ' · ' + ddmm + '</span>';
      } else if (diffD === 0) {
        dlSpan.innerHTML = '<span style="color:#d69e2e">⚠️ Vence hoje · ' + ddmm + '</span>';
      } else if (diffD <= 7) {
        dlSpan.innerHTML = '<span style="color:#d69e2e">⚠️ Vence em ' + diffD + ' dia' + (diffD!==1?'s':'') + ' · ' + ddmm + '</span>';
      } else {
        dlSpan.innerHTML = '<span style="color:var(--text3)">📅 Prazo: ' + ddmm + ' (' + diffD + ' dias)</span>';
      }
      dlWrap.style.display = '';
    } else {
      dlWrap.style.display = 'none';
    }
  }

  // Reabrir button — visible only for concluded activities
  const btnReabrir = document.getElementById('ov-btn-reabrir');
  if (btnReabrir) btnReabrir.style.display = at.status === 'concluida' ? '' : 'none';

  // Close menu if was open
  closeOvMenu();

  document.querySelectorAll('.ov-tab').forEach(function(t, i) { t.classList.toggle('active', i === 0); });
  renderOverlayTab('registro');
  document.getElementById('ov-backdrop').classList.add('open');
  document.getElementById('ov-panel').classList.add('open');
}
```

Substituir por:
```javascript
function openAtividade(cId, pbId, atId) {
  _ov_cId = cId; _ov_pbId = pbId; _ov_atId = atId;
  const c  = getCliente(cId);
  const pb = (c?.ativPlaybooks || []).find(p => p.id === pbId);
  if ((pb?.status || 'ativo') === 'cancelado') return;
  const at = (pb?.atividades || []).find(a => a.id === atId);
  if (!at) return;

  // ── Status efetivo (data-based, igual ao render das linhas) ──
  const _hoje = new Date(); _hoje.setHours(0,0,0,0);
  const dl     = at.dataLimite ? new Date(at.dataLimite + 'T00:00:00') : null;
  const diffD  = dl ? Math.round((dl - _hoje) / 86400000) : null;
  const effSt  = at.status === 'concluida' ? 'concluida'
    : (dl && dl < _hoje) ? 'atrasada'
    : (dl && diffD === 0) ? 'hoje'
    : at.status || 'pendente';

  // ── Stripe de cor (Zona 1) ──
  const stStripe = {
    concluida:    'linear-gradient(90deg,#38a169,#68d391)',
    atrasada:     'linear-gradient(90deg,#e53e3e,#fc8181)',
    hoje:         'linear-gradient(90deg,#d69e2e,#f6d860)',
    pendente:     'linear-gradient(90deg,var(--border),var(--border-2))',
    em_andamento: 'linear-gradient(90deg,#3182ce,#63b3ed)'
  };
  const stripeEl = document.getElementById('ov-stripe');
  if (stripeEl) stripeEl.style.background = stStripe[effSt] || stStripe.pendente;

  // ── Título (Zona 2, linha 1) ──
  document.getElementById('ov-titulo').textContent = at.nome || at.titulo || '—';

  // ── Tag de status (Zona 2, linha 1) ──
  const stTagBg  = {concluida:'rgba(56,161,105,.13)',atrasada:'rgba(229,62,62,.12)',hoje:'rgba(214,158,46,.13)',pendente:'var(--border-2)',em_andamento:'rgba(49,130,206,.12)'};
  const stTagClr = {concluida:'#38a169',atrasada:'#e53e3e',hoje:'#d69e2e',pendente:'var(--text3)',em_andamento:'#3182ce'};
  const stLbl    = {concluida:'Concluída',atrasada:'Atrasada',hoje:'Vence hoje',pendente:'Pendente',em_andamento:'Em andamento'};
  const tagEl    = document.getElementById('ov-tag');
  const tagDotEl = document.getElementById('ov-tag-dot');
  const tagLblEl = document.getElementById('ov-tag-lbl');
  if (tagEl) {
    tagEl.style.background = stTagBg[effSt] || stTagBg.pendente;
    tagEl.style.color      = stTagClr[effSt] || stTagClr.pendente;
  }
  if (tagDotEl) tagDotEl.style.background = stTagClr[effSt] || stTagClr.pendente;
  if (tagLblEl) tagLblEl.textContent = stLbl[effSt] || effSt;

  // ── Meta inline (Zona 2, linha 2) ──
  const respId   = at.responsavelId || pb.donoId || '';
  const respNome = respId ? ((getConsultores().find(function(x){return x.id===respId;})||{}).nome||respId) : '—';
  const fmt      = function(d){ return d ? new Date(d+'T00:00:00').toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit',year:'2-digit'}) : '—'; };
  const metaEl   = document.getElementById('ov-meta');
  if (metaEl) {
    metaEl.innerHTML =
      '<span class="ov-head-av">' + (respNome[0]||'?').toUpperCase() + '</span>' +
      ' <b>' + respNome + '</b>' +
      ' · ' + (pb.nome || 'Playbook') +
      (at.dataInicio || at.dataLimite
        ? ' · ' + fmt(at.dataInicio) + ' → <b>' + fmt(at.dataLimite) + '</b>'
        : '');
  }

  // ── KPI Strip (Zona 3) ──
  const inicioEl    = document.getElementById('ov-kpi-inicio');
  const prazoEl     = document.getElementById('ov-kpi-prazo');
  const urgencyEl   = document.getElementById('ov-kpi-urgency');
  const progEl      = document.getElementById('ov-kpi-prog');
  const progFillEl  = document.getElementById('ov-kpi-prog-fill');
  const diInput     = document.getElementById('ov-data-inicio');
  const dfInput     = document.getElementById('ov-data-fim');

  if (inicioEl) inicioEl.textContent = at.dataInicio ? fmt(at.dataInicio) : '—';
  if (prazoEl)  prazoEl.textContent  = at.dataLimite ? fmt(at.dataLimite) : '—';
  if (diInput)  diInput.value        = at.dataInicio  ? at.dataInicio.split('T')[0]  : '';
  if (dfInput)  dfInput.value        = at.dataLimite  ? at.dataLimite.split('T')[0] : '';

  if (urgencyEl) {
    urgencyEl.innerHTML = '';
    if (dl && at.status !== 'concluida') {
      if (diffD < 0) {
        urgencyEl.innerHTML = '<span style="color:var(--red)">' + Math.abs(diffD) + 'd atrás</span>';
      } else if (diffD === 0) {
        urgencyEl.innerHTML = '<span style="color:var(--yellow)">Vence hoje</span>';
      } else if (diffD <= 7) {
        urgencyEl.innerHTML = '<span style="color:var(--yellow)">em ' + diffD + 'd</span>';
      }
    }
  }

  const totalAts = (pb.atividades || []).length;
  const doneAts  = (pb.atividades || []).filter(function(a){ return a.status === 'concluida'; }).length;
  const pct      = totalAts > 0 ? Math.round(doneAts / totalAts * 100) : 0;
  const progClr  = stTagClr[effSt] || 'var(--text3)';
  if (progEl)     progEl.textContent           = doneAts + ' / ' + totalAts;
  if (progEl)     progEl.style.color           = doneAts === totalAts ? 'var(--green)' : 'var(--text)';
  if (progFillEl) { progFillEl.style.width     = pct + '%'; progFillEl.style.background = progClr; }

  // ── Footer (Zona 6) ──
  const footerProgEl = document.getElementById('ov-footer-prog');
  if (footerProgEl) {
    footerProgEl.innerHTML = '<strong>' + doneAts + '/' + totalAts + '</strong> atividade' + (totalAts !== 1 ? 's' : '') + ' concluída' + (totalAts !== 1 ? 's' : '');
  }

  // ── Botão Concluir ──
  const btnC = document.getElementById('ov-btn-concluir');
  if (btnC) {
    if (at.status === 'concluida') {
      btnC.textContent = '✓ Concluída';
      btnC.classList.add('done');
      btnC.onclick = null;
    } else {
      btnC.textContent = '✓ Marcar como Concluída';
      btnC.classList.remove('done');
      btnC.onclick = concluirAtividade;
    }
  }

  // ── Botão Reabrir ──
  const btnReabrir = document.getElementById('ov-btn-reabrir');
  if (btnReabrir) btnReabrir.style.display = at.status === 'concluida' ? '' : 'none';

  closeOvMenu();
  document.querySelectorAll('.ov-tab').forEach(function(t, i) { t.classList.toggle('active', i === 0); });
  renderOverlayTab('registro');
  document.getElementById('ov-backdrop').classList.add('open');
  document.getElementById('ov-panel').classList.add('open');
}
```

- [ ] **Step 2: Substituir o return de `renderOvRegistro()` (linha ~6278)**

Localizar:
```javascript
  return '<div class="ov-reg-form">' +
    '<div class="ov-reg-av">' + cid[0].toUpperCase() + '</div>' +
    '<div class="ov-reg-wrap">' +
      '<textarea class="ov-reg-ta" id="ov-reg-input" placeholder="Adicionar registro..."></textarea>' +
      '<button class="ov-reg-send" onclick="addOvRegistro()">Registrar</button>' +
    '</div>' +
  '</div>' +
  (itens || '<p style="font-size:12px;color:var(--text4);text-align:center;padding:20px">Nenhum registro ainda.</p>');
```

Substituir por:
```javascript
  return '<div class="ov-reg-form">' +
    '<div class="ov-reg-av">' + (cid[0]||'?').toUpperCase() + '</div>' +
    '<div class="ov-reg-wrap">' +
      '<textarea class="ov-reg-ta" id="ov-reg-input" placeholder="Adicionar registro..."></textarea>' +
      '<div class="ov-reg-actions">' +
        '<span class="ov-reg-hint">Registre um andamento ou decisão</span>' +
        '<button class="ov-reg-send" onclick="addOvRegistro()">Registrar</button>' +
      '</div>' +
    '</div>' +
  '</div>' +
  (itens || '<p style="font-size:12px;color:var(--text4);text-align:center;padding:20px">Nenhum registro ainda.</p>');
```

- [ ] **Step 3: Atualizar `saveOvDatas()` para refrescar os KPI display (linha ~6301)**

Localizar dentro de `saveOvDatas()` o bloco que atualiza `ov-deadline-wrap`:
```javascript
  // Atualiza badge de deadline sem fechar o overlay
  const dlWrap = document.getElementById('ov-deadline-wrap');
  const dlSpan = document.getElementById('ov-deadline');
  if (dlWrap && dlSpan) {
    if (at.dataLimite && at.status !== 'concluida') {
      const h = new Date(); h.setHours(0,0,0,0);
      const d = new Date(at.dataLimite + 'T00:00:00');
      const dd = Math.round((d - h) / 86400000);
      const ddmm = d.toLocaleDateString('pt-BR', {day:'2-digit',month:'2-digit'});
      if (dd < 0)      dlSpan.innerHTML = '<span style="color:var(--red)">⏰ Vencida há ' + Math.abs(dd) + ' dia' + (Math.abs(dd)!==1?'s':'') + ' · ' + ddmm + '</span>';
      else if (dd===0) dlSpan.innerHTML = '<span style="color:#d69e2e">⚠️ Vence hoje · ' + ddmm + '</span>';
      else if (dd<=7)  dlSpan.innerHTML = '<span style="color:#d69e2e">⚠️ Vence em ' + dd + ' dia' + (dd!==1?'s':'') + ' · ' + ddmm + '</span>';
      else             dlSpan.innerHTML = '<span style="color:var(--text3)">📅 Prazo: ' + ddmm + ' (' + dd + ' dias)</span>';
      dlWrap.style.display = '';
    } else {
      dlWrap.style.display = 'none';
    }
  }
```

Substituir por:
```javascript
  // Atualiza KPI strip sem fechar o overlay
  const fmt2 = function(d){ return d ? new Date(d+'T00:00:00').toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit',year:'2-digit'}) : '—'; };
  const inicioEl2  = document.getElementById('ov-kpi-inicio');
  const prazoEl2   = document.getElementById('ov-kpi-prazo');
  const urgencyEl2 = document.getElementById('ov-kpi-urgency');
  if (inicioEl2) inicioEl2.textContent = fmt2(at.dataInicio);
  if (prazoEl2)  prazoEl2.textContent  = fmt2(at.dataLimite);
  if (urgencyEl2) {
    urgencyEl2.innerHTML = '';
    if (at.dataLimite && at.status !== 'concluida') {
      const h2 = new Date(); h2.setHours(0,0,0,0);
      const d2 = new Date(at.dataLimite + 'T00:00:00');
      const dd2 = Math.round((d2 - h2) / 86400000);
      if (dd2 < 0)       urgencyEl2.innerHTML = '<span style="color:var(--red)">' + Math.abs(dd2) + 'd atrás</span>';
      else if (dd2 === 0) urgencyEl2.innerHTML = '<span style="color:var(--yellow)">Vence hoje</span>';
      else if (dd2 <= 7)  urgencyEl2.innerHTML = '<span style="color:var(--yellow)">em ' + dd2 + 'd</span>';
    }
  }
  // Atualiza meta inline também
  const metaEl2 = document.getElementById('ov-meta');
  if (metaEl2) {
    const respId2   = at.responsavelId || _getOvAt().pb?.donoId || '';
    const respNome2 = respId2 ? ((getConsultores().find(function(x){return x.id===respId2;})||{}).nome||respId2) : '—';
    const pb2       = _getOvAt().pb;
    metaEl2.innerHTML =
      '<span class="ov-head-av">' + (respNome2[0]||'?').toUpperCase() + '</span>' +
      ' <b>' + respNome2 + '</b>' +
      ' · ' + ((pb2 && pb2.nome) || 'Playbook') +
      (at.dataInicio || at.dataLimite
        ? ' · ' + fmt2(at.dataInicio) + ' → <b>' + fmt2(at.dataLimite) + '</b>'
        : '');
  }
```

- [ ] **Step 4: Verificar funcionamento completo**

Abrir `grv-cs-jornada.html` no Chrome. Executar cada verificação:

1. Clicar numa atividade **concluída** → stripe verde, tag "Concluída" verde, footer "✓ Concluída" outline verde
2. Clicar numa atividade **atrasada** (dataLimite no passado, não concluída) → stripe vermelha, tag "Atrasada" vermelha, KPI prazo com "Xd atrás" em vermelho
3. Clicar numa atividade **pendente sem data** → stripe cinza, tag "Pendente", KPI início e prazo "—"
4. KPI Progresso mostra "9 / 10" com barra preenchida
5. Footer mostra "9/10 atividades concluídas" à esquerda
6. Digitar texto no campo Registro e clicar "Registrar" → nota aparece no feed com avatar e timestamp
7. Clicar na célula Início → date picker nativo abre (comportamento via `showPicker()`)
8. Alterar uma data e sair do campo → KPI atualiza sem fechar o overlay

- [ ] **Step 5: Commit**

```
git add grv-cs-jornada.html
git commit -m "feat(overlay): JS atualizado — stripe/tag/kpi/footer dinâmicos por status"
```

---

## Pós-implementação

Navegar em sequência e confirmar:
1. Dashboard → clicar num cliente → aba Atividades → clicar em atividade atrasada → overlay vermelho
2. Mesma atividade → Registrar texto → feed atualiza com formato novo
3. Clicar em atividade concluída → footer outline verde + tag verde
4. Vencimentos → clicar numa linha → overlay abre na atividade correta
5. Fechar overlay → clicar em outro cliente → overlay reinicia corretamente
