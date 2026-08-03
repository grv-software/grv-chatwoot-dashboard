# Health Score + NPS + CSAT Histórico + Last Touch — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add four CS health signals to `grv-cs-jornada.html`: Last Touch badge, CSAT histórico, Health Score 0–100, and NPS by client.

**Architecture:** All changes in a single file (`grv-cs-jornada.html`). New utility functions added after `calcProgresso` (line 1664). Data stored in `localStorage` via existing `saveCliente`. Migrations run in `migrateLS` IIFE. UI slots: feed card (`renderFeedCard`), client header (`renderCliente`), Visão 360° tab (`renderAba360`), Visão Geral KPI grid (`renderVisaoGeral`).

**Tech Stack:** Vanilla JS, single-file SPA, `localStorage` as DB, hash routing.

## Global Constraints

- Single file only: `grv-cs-jornada.html` — no new files
- No build step — validate with `node -e "require('fs').readFileSync('grv-cs-jornada.html','utf8')" && echo OK` after each task
- All new JS uses `function` declarations (not arrow functions at top level) for consistency with existing code
- Existing CSS classes only — inline styles for one-off values
- Each task ends with a git commit on branch `alteracoes`

---

### Task 1: Last Touch

**Files:**
- Modify: `grv-cs-jornada.html:1664` (after `calcProgresso`)
- Modify: `grv-cs-jornada.html:1957` (before `return alertas;` in `computeAlertas`)
- Modify: `grv-cs-jornada.html:2810` (in `renderFeedCard`)
- Modify: `grv-cs-jornada.html:3308` (in `renderCliente` dc-chips)

**Interfaces:**
- Produces: `getDiasUltimoContato(cliente) → number|null` (days since last contact, or null if no data)

- [ ] **Step 1: Add `getDiasUltimoContato` after `calcProgresso` (line 1664)**

Insert immediately after the closing `}` of `calcProgresso`:

```javascript
function getDiasUltimoContato(cliente) {
  var hoje = new Date(); hoje.setHours(0,0,0,0);
  var ultima = null;
  function chk(d) { if (d) { var dt = new Date(d); dt.setHours(0,0,0,0); if (!ultima || dt > ultima) ultima = dt; } }
  (cliente.registros||[]).forEach(function(r){ chk(r.data); });
  (cliente.ativPlaybooks||[]).forEach(function(pb){
    (pb.atividades||[]).forEach(function(at){
      (at.registros||[]).forEach(function(r){ chk(r.data); });
    });
  });
  if (!ultima) return null;
  return Math.round((hoje - ultima) / 86400000);
}
```

- [ ] **Step 2: Add sem_contato alert in `computeAlertas` before `return alertas;` (line 1957)**

```javascript
  const semContato30 = (clientes || []).filter(function(c) {
    var d = getDiasUltimoContato(c); return d !== null && d > 30;
  });
  if (semContato30.length > 0) alertas.push({ sev: 'atencao',
    titulo: semContato30.length + ' cliente(s) sem contato há mais de 30 dias',
    acao: 'Agendar touchpoint: ' + semContato30.slice(0,3).map(function(c){ return c.id; }).join(', ') + (semContato30.length > 3 ? ' e outros...' : '') });
```

- [ ] **Step 3: Add last touch badge in `renderFeedCard` (line 2810)**

After `const csat = c.csat ? 'CSAT ★ ' + c.csat : '';` add:

```javascript
  const ltDias = getDiasUltimoContato(c);
  const ltBadge = (ltDias !== null && ltDias > 14)
    ? '<div style="font-size:10px;font-weight:700;color:' + (ltDias >= 30 ? '#ef4444' : '#eab308') + ';margin-top:3px">' + ltDias + 'd sem contato</div>'
    : '';
```

And in the `fc-right` section (line 2823) after the status badge span, add `+ ltBadge +`.

The full `fc-right` becomes:
```javascript
      '<div class="fc-right">' +
        '<span class="status-badge b-' + st + '">' + statusLabel(st) + '</span>' +
        ltBadge +
        (csat ? '<div class="fc-csat">' + csat + '</div>' : '') +
        '<div class="fc-prog"><div class="fc-progbar" style="width:' + prog + '%;background:' + pColor + '"></div></div>' +
      '</div>'
```

- [ ] **Step 4: Add last touch line in client header (`renderCliente`, line 3308)**

After `</div>` that closes `.dc-chips`, add a new line inside `.dc-info`:

```javascript
          ${(() => { const lt = getDiasUltimoContato(c); return lt !== null ? '<div style="font-size:11px;color:' + (lt===0?'#22c55e':lt<=7?'var(--text3)':lt<=14?'#eab308':'#ef4444') + ';margin-top:4px">Último contato: ' + (lt===0?'hoje':'há '+lt+' dia'+(lt===1?'':'s')) + '</div>' : ''; })()}
```

- [ ] **Step 5: Syntax check**

```bash
node -e "new Function(require('fs').readFileSync('grv-cs-jornada.html','utf8').replace(/<script[^>]*>/gi,'').replace(/<\/script>/gi,''))" && echo "OK"
```

- [ ] **Step 6: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(cs): last touch — getDiasUltimoContato + badge no feed card + alerta 30d + linha no header"
```

---

### Task 2: CSAT Histórico

**Files:**
- Modify: `grv-cs-jornada.html:1624` (migrateLS — after pb.atividades forEach closes)
- Modify: `grv-cs-jornada.html:1664+` (after getDiasUltimoContato)
- Modify: `grv-cs-jornada.html:3440` (renderAba360 — before closing backtick)

**Interfaces:**
- Consumes: `getDiasUltimoContato` from Task 1
- Produces: `calcCsatAtual(cliente) → number|null` (avg of last 3 csatRespostas, or c.csat, or null)
- Produces: `registrarCsat(clienteId, score, obs, data)` — saves new entry, re-renders
- Produces: `cancelarFormCsat(clienteId)` — hides inline form, re-renders

- [ ] **Step 1: Migrate `csat` → `csatRespostas[]` in `migrateLS` (after line 1624)**

Inside the `clientes.forEach` in `migrateLS`, after the `(c.ativPlaybooks || []).forEach(...)` block closes:

```javascript
      if (!c.csatRespostas) {
        c.csatRespostas = c.csat ? [{ id:'csat_m', score: c.csat, data: c.dataInicioCS||c.dataInicio||'2025-01-01', obs:'' }] : [];
        dirty = true;
      }
```

- [ ] **Step 2: Add `calcCsatAtual` after `getDiasUltimoContato`**

```javascript
function calcCsatAtual(cliente) {
  var resps = (cliente.csatRespostas||[]).slice(-3);
  if (!resps.length) return cliente.csat || null;
  return Math.round(resps.reduce(function(s,r){ return s+r.score; },0)/resps.length*10)/10;
}
```

- [ ] **Step 3: Add CSAT save/cancel functions (after `calcCsatAtual`)**

```javascript
function registrarCsat(clienteId, score, obs, data) {
  var c = getCliente(clienteId);
  if (!c) return;
  if (!c.csatRespostas) c.csatRespostas = [];
  c.csatRespostas.push({ id:'csat_'+Date.now(), score: parseFloat(score), data: data, obs: obs||'' });
  c.csat = calcCsatAtual(c);
  saveCliente(c);
  _cliente_aba = '360';
  renderCliente(clienteId);
}

function cancelarFormCsat(clienteId) {
  _cliente_aba = '360';
  renderCliente(clienteId);
}
```

- [ ] **Step 4: Add CSAT card in `renderAba360` before closing backtick (around line 3441)**

The closing backtick of `renderAba360` is `` ` `` on line 3441. Insert before it:

```javascript
    <div class="card-block" style="margin-top:16px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
        <div class="section-title" style="margin-bottom:0">Satisfação (CSAT)</div>
        ${(function(){
          var csat = calcCsatAtual(c);
          return csat !== null ? '<span style="font-size:22px;font-weight:800;color:'+(csat>=4?'#22c55e':csat>=3?'#eab308':'#ef4444')+'">'+csat+' <span style="font-size:12px;color:var(--text3)">/ 5</span></span>' : '';
        })()}
      </div>
      ${(c.csatRespostas||[]).length === 0 ? '<p style="font-size:12px;color:var(--text3);margin:0 0 12px">Nenhuma pesquisa registrada ainda.</p>' :
        '<div style="display:flex;flex-direction:column;gap:6px;margin-bottom:12px">' +
        (c.csatRespostas||[]).slice().reverse().map(function(r){
          var clr = r.score>=4?'#22c55e':r.score>=3?'#eab308':'#ef4444';
          return '<div style="display:flex;align-items:center;gap:10px;padding:6px 8px;background:var(--b-surface);border-radius:6px;font-size:12px">' +
            '<span style="font-weight:800;color:'+clr+';min-width:20px">'+r.score+'</span>' +
            '<span style="color:var(--text3)">' + new Date(r.data).toLocaleDateString('pt-BR') + '</span>' +
            (r.obs ? '<span style="color:var(--text2);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+r.obs+'</span>' : '') +
            '</div>';
        }).join('') + '</div>'
      }
      <div id="csat-form-${c.id}" style="display:none;background:var(--b-surface);border-radius:8px;padding:12px;margin-bottom:8px">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px">
          <div>
            <label style="font-size:11px;color:var(--text3);display:block;margin-bottom:4px">Score (1–5)</label>
            <input id="csat-score-${c.id}" type="number" min="1" max="5" step="0.5" style="width:100%;padding:6px 8px;background:var(--b-bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px">
          </div>
          <div>
            <label style="font-size:11px;color:var(--text3);display:block;margin-bottom:4px">Data</label>
            <input id="csat-data-${c.id}" type="date" style="width:100%;padding:6px 8px;background:var(--b-bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px">
          </div>
        </div>
        <div style="margin-bottom:10px">
          <label style="font-size:11px;color:var(--text3);display:block;margin-bottom:4px">Observação (opcional)</label>
          <input id="csat-obs-${c.id}" type="text" placeholder="Ex: cliente muito satisfeito com onboarding" style="width:100%;padding:6px 8px;background:var(--b-bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;box-sizing:border-box">
        </div>
        <div style="display:flex;gap:8px">
          <button onclick="registrarCsat('${c.id}',document.getElementById('csat-score-${c.id}').value,document.getElementById('csat-obs-${c.id}').value,document.getElementById('csat-data-${c.id}').value)" style="flex:1;padding:7px;background:var(--primary);color:#fff;border:none;border-radius:6px;font-size:12px;font-weight:700;cursor:pointer">Salvar</button>
          <button onclick="cancelarFormCsat('${c.id}')" style="padding:7px 14px;background:transparent;color:var(--text3);border:1px solid var(--border);border-radius:6px;font-size:12px;cursor:pointer">Cancelar</button>
        </div>
      </div>
      <button onclick="document.getElementById('csat-form-${c.id}').style.display='block';var d=document.getElementById('csat-data-${c.id}');if(d)d.value=new Date().toISOString().slice(0,10)" style="font-size:12px;color:var(--primary);background:transparent;border:1px solid var(--primary);border-radius:6px;padding:5px 12px;cursor:pointer;font-weight:600">+ Registrar CSAT</button>
    </div>
```

- [ ] **Step 5: Syntax check + commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(cs): CSAT histórico — migração csatRespostas[], calcCsatAtual, card em Visão 360°"
```

---

### Task 3: Health Score

**Files:**
- Modify: `grv-cs-jornada.html` (after `calcCsatAtual`)
- Modify: `grv-cs-jornada.html:2804` (`renderFeedCard`)
- Modify: `grv-cs-jornada.html:3305` (`renderCliente` dc-chips)
- Modify: `grv-cs-jornada.html:2149` (`renderVisaoGeral` KPI grid closing div)

**Interfaces:**
- Consumes: `calcSlaCompliance`, `calcCsatAtual`, `calcProgresso`, `getDiasUltimoContato`
- Produces: `calcHealthScore(cliente) → number|null` (0–100)
- Produces: `hsColor(score) → string` (CSS color for the score)

- [ ] **Step 1: Add `calcHealthScore` and `hsColor` after `calcCsatAtual`**

```javascript
function hsColor(score) {
  return score === null ? 'var(--text4)' : score >= 75 ? '#22c55e' : score >= 50 ? '#eab308' : '#ef4444';
}

function calcHealthScore(cliente) {
  var sla  = calcSlaCompliance([cliente]);
  var csat = calcCsatAtual(cliente);
  var prog = calcProgresso(cliente.ativPlaybooks || []);
  var dias = getDiasUltimoContato(cliente);
  var sSla  = sla  !== null ? sla  / 100 * 30 : 15;
  var sCsat = csat !== null ? csat / 5   * 30 : 15;
  var sProg = prog / 100 * 25;
  var sCont = dias === null ? 7.5 : dias === 0 ? 15 : dias <= 7 ? 12 : dias <= 14 ? 8 : dias <= 30 ? 4 : 0;
  return Math.round(sSla + sCsat + sProg + sCont);
}
```

- [ ] **Step 2: Add Health Score circle in `renderFeedCard`**

After `const ltBadge = ...` add:
```javascript
  const hs  = calcHealthScore(c);
  const hsC = hsColor(hs);
  const hsCircle = '<div style="width:36px;height:36px;border-radius:50%;border:2.5px solid ' + hsC + ';display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;color:' + hsC + ';flex-shrink:0">' + (hs !== null ? hs : '—') + '</div>';
```

And add `hsCircle +` inside the `fc-right` div, before status badge. The full `fc-right`:
```javascript
      '<div class="fc-right">' +
        hsCircle +
        '<span class="status-badge b-' + st + '">' + statusLabel(st) + '</span>' +
        ltBadge +
        (csat ? '<div class="fc-csat">' + csat + '</div>' : '') +
        '<div class="fc-prog"><div class="fc-progbar" style="width:' + prog + '%;background:' + pColor + '"></div></div>' +
      '</div>'
```

- [ ] **Step 3: Add Health Score in client header dc-chips (renderCliente line 3308)**

After the last `chip-prod` span, add:
```javascript
          ${(() => { var hs = calcHealthScore(c); if (hs === null) return ''; var clr = hsColor(hs); return '<span style="font-size:11px;font-weight:800;color:'+clr+';background:'+clr+'1a;padding:2px 8px;border-radius:12px;border:1px solid '+clr+'55">Health '+hs+'</span>'; })()}
```

- [ ] **Step 4: Add Health Médio KPI in `renderVisaoGeral` (line 2143–2148)**

Change the last `.vg-kpi` (SLA no Prazo) to remove `border-right:none`, then add after it:
```javascript
        ${(() => {
          var scores = getClientes().map(calcHealthScore).filter(function(s){ return s !== null; });
          var med = scores.length ? Math.round(scores.reduce(function(a,b){return a+b;},0)/scores.length) : null;
          var clr = hsColor(med);
          return '<div class="vg-kpi" style="border-right:none"><div class="vg-kpi-n" style="color:'+clr+'">'+(med!==null?med:'—')+'</div><div class="vg-kpi-l">Health Médio</div><div class="vg-kpi-pct">score 0–100</div></div>';
        })()}
```

- [ ] **Step 5: Syntax check + commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(cs): health score 0-100 — círculo no feed card, chip no header cliente, KPI Visão Geral"
```

---

### Task 4: NPS

**Files:**
- Modify: `grv-cs-jornada.html` (after `calcHealthScore`)
- Modify: `grv-cs-jornada.html:3441` (renderAba360 — after CSAT card, before closing backtick)

**Interfaces:**
- Produces: `calcNps(cliente) → number|null` (-100 to +100)
- Produces: `registrarNps(clienteId, score, comentario, data)` — saves entry, re-renders
- Produces: `cancelarFormNps(clienteId)` — hides form, re-renders

- [ ] **Step 1: Add `calcNps`, `registrarNps`, `cancelarFormNps` after `calcHealthScore`**

```javascript
function calcNps(cliente) {
  var resps = cliente.npsRespostas || [];
  if (!resps.length) return null;
  var prom = resps.filter(function(r){ return r.score >= 9; }).length;
  var detr = resps.filter(function(r){ return r.score <= 6; }).length;
  return Math.round((prom - detr) / resps.length * 100);
}

function registrarNps(clienteId, score, comentario, data) {
  var c = getCliente(clienteId);
  if (!c) return;
  if (!c.npsRespostas) c.npsRespostas = [];
  c.npsRespostas.push({ id:'nps_'+Date.now(), score: parseInt(score,10), data: data, comentario: comentario||'' });
  saveCliente(c);
  _cliente_aba = '360';
  renderCliente(clienteId);
}

function cancelarFormNps(clienteId) {
  _cliente_aba = '360';
  renderCliente(clienteId);
}
```

- [ ] **Step 2: Add NPS card in `renderAba360` after CSAT card, before closing backtick**

```javascript
    <div class="card-block" style="margin-top:16px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
        <div class="section-title" style="margin-bottom:0">Net Promoter Score (NPS)</div>
        ${(function(){
          var nps = calcNps(c);
          if (nps === null) return '';
          var clr = nps >= 50 ? '#22c55e' : nps >= 0 ? '#eab308' : '#ef4444';
          var label = nps >= 50 ? 'Excelente' : nps >= 0 ? 'Bom' : 'Crítico';
          return '<span style="font-size:22px;font-weight:800;color:'+clr+'">'+nps+' <span style="font-size:12px;color:var(--text3)">'+label+'</span></span>';
        })()}
      </div>
      ${(c.npsRespostas||[]).length === 0 ? '<p style="font-size:12px;color:var(--text3);margin:0 0 12px">Nenhuma resposta registrada ainda.</p>' :
        '<div style="display:flex;flex-direction:column;gap:6px;margin-bottom:12px">' +
        (c.npsRespostas||[]).slice().reverse().map(function(r){
          var clr = r.score>=9?'#22c55e':r.score>=7?'var(--text3)':'#ef4444';
          var tipo = r.score>=9?'Promotor':r.score>=7?'Neutro':'Detrator';
          return '<div style="display:flex;align-items:center;gap:10px;padding:6px 8px;background:var(--b-surface);border-radius:6px;font-size:12px">' +
            '<span style="font-weight:800;color:'+clr+';min-width:24px">'+r.score+'</span>' +
            '<span style="color:'+clr+';font-size:10px;font-weight:700">'+tipo+'</span>' +
            '<span style="color:var(--text3)">' + new Date(r.data).toLocaleDateString('pt-BR') + '</span>' +
            (r.comentario ? '<span style="color:var(--text2);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+r.comentario+'</span>' : '') +
            '</div>';
        }).join('') + '</div>'
      }
      <div id="nps-form-${c.id}" style="display:none;background:var(--b-surface);border-radius:8px;padding:12px;margin-bottom:8px">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px">
          <div>
            <label style="font-size:11px;color:var(--text3);display:block;margin-bottom:4px">Score NPS (0–10)</label>
            <input id="nps-score-${c.id}" type="number" min="0" max="10" style="width:100%;padding:6px 8px;background:var(--b-bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px">
          </div>
          <div>
            <label style="font-size:11px;color:var(--text3);display:block;margin-bottom:4px">Data</label>
            <input id="nps-data-${c.id}" type="date" style="width:100%;padding:6px 8px;background:var(--b-bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px">
          </div>
        </div>
        <div style="margin-bottom:10px">
          <label style="font-size:11px;color:var(--text3);display:block;margin-bottom:4px">Comentário (opcional)</label>
          <input id="nps-com-${c.id}" type="text" placeholder="Ex: muito satisfeito, indicaria" style="width:100%;padding:6px 8px;background:var(--b-bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;box-sizing:border-box">
        </div>
        <div style="display:flex;gap:8px">
          <button onclick="registrarNps('${c.id}',document.getElementById('nps-score-${c.id}').value,document.getElementById('nps-com-${c.id}').value,document.getElementById('nps-data-${c.id}').value)" style="flex:1;padding:7px;background:var(--primary);color:#fff;border:none;border-radius:6px;font-size:12px;font-weight:700;cursor:pointer">Salvar</button>
          <button onclick="cancelarFormNps('${c.id}')" style="padding:7px 14px;background:transparent;color:var(--text3);border:1px solid var(--border);border-radius:6px;font-size:12px;cursor:pointer">Cancelar</button>
        </div>
      </div>
      <button onclick="document.getElementById('nps-form-${c.id}').style.display='block';var d=document.getElementById('nps-data-${c.id}');if(d)d.value=new Date().toISOString().slice(0,10)" style="font-size:12px;color:var(--primary);background:transparent;border:1px solid var(--primary);border-radius:6px;padding:5px 12px;cursor:pointer;font-weight:600">+ Registrar NPS</button>
    </div>
```

- [ ] **Step 3: Syntax check + commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(cs): NPS — calcNps, card em Visão 360° com histórico e formulário"
```

---

## Self-Review

**Spec coverage:**
- ✅ Last Touch: `getDiasUltimoContato` + badge + alerta + header → Task 1
- ✅ Health Score: `calcHealthScore` + `hsColor` + feed circle + header chip + Visão Geral KPI → Task 3
- ✅ CSAT histórico: migration + `calcCsatAtual` + UI card → Task 2
- ✅ NPS: `calcNps` + UI card → Task 4

**Type consistency:**
- `calcSlaCompliance([cliente])` — wraps single client in array ✅
- `calcProgresso(cliente.ativPlaybooks || [])` — passes array ✅
- `getDiasUltimoContato(c)` — passes client object ✅
- `calcCsatAtual(c)` — defined before `calcHealthScore` uses it ✅

**Placeholder check:** None found. All steps have complete code.
