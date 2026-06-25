# Cliente Detalhe — Abas 360° / Atividades / Notas — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 3 tabs (Visão 360°, Atividades, Notas) to the client detail screen in `grv-cs-jornada.html`, with a nested master-detail activity system and new `segmento`/`csId` fields.

**Architecture:** Single-file SPA edit — CSS + JS inline, no build step. New global state tracks active tab and atividade-playbook UI state. `renderCliente(id)` is rewritten to dispatch to 3 render functions; all other functions untouched.

**Tech Stack:** Vanilla JS, Chart.js v4 (not involved), CSS custom properties, localStorage.

## Global Constraints

- File: `grv-cs-jornada.html` on branch `alteracoes`
- No new files — all changes inline
- `renderCriarPlaybook()` and `checkTask()` must not be touched
- `prog-pct-${c.id}` and `prog-bar-${c.id}` IDs must be preserved (used by `checkTask` DOM updates)
- CSS variables `--primary: #E05A1E`, `--text2: #4a5568`, `--surface: #ffffff` — use existing tokens
- `getConsultorAtivo()` returns `localStorage.getItem('grv_cs_consultor_ativo')` — already exists at line ~995
- No comments added to code
- Test by opening the file in a browser (file:// or live server) and navigating between clients

---

### Task 1: CSS + Global State

**Files:**
- Modify: `grv-cs-jornada.html:350-351` (CSS block before `</style>`)
- Modify: `grv-cs-jornada.html:2167` (global state after `let _open_fases = {}`)

**Interfaces:**
- Produces: CSS classes `cliente-tabs`, `cliente-tab`, `grid-360`, `card-360`, `pb-layout`, `pb-sidebar`, `pb-panel`, `pb-title-row`, `pb-item`, `pb-add-btn`, `pb-inline-form`, `pb-inline-input`, `pb-chev`, `at-empty`, `at-title`, `at-reg-item`, `at-reg-meta`, `at-reg-text`, `at-write`
- Produces: globals `_cliente_id_atual`, `_cliente_aba`, `_pb_expandidos`, `_at_sel`, `_pb_form_open`, `_at_form_pb`

- [ ] **Step 1: Insert CSS block**

Find the line `@keyframes toast-in{from{transform:translateY(8px);opacity:0}to{transform:translateY(0);opacity:1}}` and insert the CSS block immediately before `</style>`:

Old string (end of existing CSS + closing tag):
```
@keyframes toast-in{from{transform:translateY(8px);opacity:0}to{transform:translateY(0);opacity:1}}
</style>
```

New string:
```
@keyframes toast-in{from{transform:translateY(8px);opacity:0}to{transform:translateY(0);opacity:1}}

/* ── Abas do cliente ─────────────────────────────── */
.cliente-tabs{display:flex;gap:0;border-bottom:2px solid var(--border);margin-bottom:24px}
.cliente-tab{padding:10px 20px;font-size:13px;font-weight:600;color:var(--text3);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-2px;background:none;border-top:none;border-left:none;border-right:none}
.cliente-tab.active{color:var(--primary);border-bottom-color:var(--primary)}
.cliente-tab:hover:not(.active){color:var(--text)}

/* ── Grid 360° ───────────────────────────────────── */
.grid-360{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.card-360{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px 20px}
.c360-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text3);margin-bottom:8px}
.c360-value{font-size:17px;font-weight:700;color:var(--text);line-height:1.3}
.c360-prog{height:6px;background:#edf2f7;border-radius:3px;margin-top:8px}
.c360-prog-fill{height:100%;border-radius:3px;background:var(--primary)}

/* ── Atividades master-detail ─────────────────────── */
.pb-layout{display:grid;grid-template-columns:260px 1fr;gap:0;min-height:440px;border:1px solid var(--border);border-radius:var(--radius);overflow:hidden}
.pb-sidebar{border-right:1px solid var(--border);padding:14px 10px;background:#fafbfc;overflow-y:auto}
.pb-panel{padding:24px;overflow-y:auto;background:#fff}
.pb-title-row{display:flex;align-items:center;gap:6px;padding:6px 8px;cursor:pointer;border-radius:6px;font-size:13px;font-weight:700;color:var(--text);margin-bottom:4px}
.pb-title-row:hover{background:#f0f4f8}
.pb-chev{font-size:10px;margin-left:auto;color:var(--text3)}
.pb-item{padding:6px 10px 6px 24px;border-radius:6px;cursor:pointer;display:flex;align-items:center;gap:7px;font-size:12px;color:var(--text2);margin-bottom:2px}
.pb-item:hover{background:#f0f4f8}
.pb-item.active{background:#FFF3EE;color:var(--primary);border-left:3px solid var(--primary);padding-left:21px;font-weight:600}
.pb-add-btn{width:100%;padding:7px;border:1px dashed var(--border);border-radius:6px;background:none;color:var(--text3);font-size:12px;cursor:pointer;text-align:center;margin:6px 0 14px}
.pb-add-btn:hover{border-color:var(--primary);color:var(--primary)}
.pb-inline-form{padding:4px 8px 8px;display:flex;gap:6px}
.pb-inline-input{flex:1;padding:5px 8px;border:1px solid var(--border);border-radius:6px;font-size:12px}

/* ── Painel de atividade ─────────────────────────── */
.at-empty{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:var(--text3);text-align:center;gap:8px;font-size:13px}
.at-title{font-size:18px;font-weight:700;color:var(--text);margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid var(--border)}
.at-reg-item{padding:12px 0;border-bottom:1px solid var(--border)}
.at-reg-item:last-of-type{border-bottom:none}
.at-reg-meta{font-size:11px;color:var(--text3);margin-bottom:4px}
.at-reg-text{font-size:13px;color:var(--text);line-height:1.6}
.at-write{margin-top:20px;padding-top:16px;border-top:1px solid var(--border)}
</style>
```

- [ ] **Step 2: Insert global state variables**

Find the line `let _open_fases = {};` (around line 2167) and replace it:

Old string:
```
let _open_fases = {};
```

New string:
```
let _open_fases       = {};
let _cliente_id_atual = null;
let _cliente_aba      = '360';
let _pb_expandidos    = {};
let _at_sel           = null;
let _pb_form_open     = false;
let _at_form_pb       = null;
```

- [ ] **Step 3: Test in browser**

Open the file in a browser. Navigate to any client detail (click a client from the list). Verify the page still loads without JS errors (open DevTools > Console). The existing layout should be unchanged — no CSS conflicts yet.

- [ ] **Step 4: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(cliente): CSS de abas + estado global para detalhe do cliente"
```

---

### Task 2: Seed Data — segmento, csId, ativPlaybooks

**Files:**
- Modify: `grv-cs-jornada.html` — SEED_CLIENTES array (lines 522–966)

**Interfaces:**
- Consumes: `SEED_CONSULTORES` ids: `'ana-paula'`, `'carlos'`, `'maria'`, `'cristiano'`, `'felipe'`, `'silvia'`, `'severiano'`
- Produces: Every client has `segmento`, `csId`, `ativPlaybooks` fields; 3 clients (KMSIL, RAS METAL, ROBOTIX) have demo `ativPlaybooks`

**Assignment table** — use these exact values for each client:

| Client ID | segmento | csId |
|---|---|---|
| KMSIL | 'Saúde' | 'cristiano' |
| RAS METAL | 'Indústria' | 'felipe' |
| AXONE | 'Serviços' | 'silvia' |
| AÇO ART | 'Indústria' | 'carlos' |
| ALPARGATAS CPS | 'Indústria' | 'maria' |
| FRAY | 'Saúde' | 'ana-paula' |
| FELIX INDUSTRIAL | 'Indústria' | 'severiano' |
| USIMAZA EMBRAER | 'Indústria' | 'silvia' |
| CAMPOSC | 'Agronegócio' | 'carlos' |
| SOARES FERRAMENTARIA | 'Indústria' | 'ana-paula' |
| LIQUOS | 'Saúde' | 'cristiano' |
| METALVALE | 'Indústria' | 'felipe' |
| SIMONSEN | 'Varejo' | 'maria' |
| MECATRON | 'Indústria' | 'severiano' |
| POLIMOLD | 'Indústria' | 'ana-paula' |
| ELETROTINS | 'Indústria' | 'carlos' |
| BORBOREMA | 'Varejo' | 'felipe' |
| RETALHOMAX | 'Varejo' | 'silvia' |
| TORNEFER | 'Indústria' | 'maria' |
| INDALPE | 'Saúde' | 'cristiano' |
| ROTOFER | 'Indústria' | 'ana-paula' |
| AGROFLEX | 'Agronegócio' | 'carlos' |
| LAMIFER | 'Indústria' | 'severiano' |
| PLASVALE | 'Saúde' | 'felipe' |
| LAMINEX | 'Serviços' | 'silvia' |
| COMPRESSEI | 'Indústria' | 'maria' |
| NXTEC | 'Serviços' | 'ana-paula' |
| SENSORTEC | 'Serviços' | 'cristiano' |
| METATRON | 'Indústria' | 'carlos' |
| PLASTIMETAL | 'Indústria' | 'severiano' |
| IOTSYSTEM | 'Serviços' | 'felipe' |
| NXPRIME | 'Serviços' | 'maria' |
| ROBOTIX | 'Serviços' | 'silvia' |
| AUTOMIND | 'Serviços' | 'ana-paula' |
| USINAGEM3D | 'Indústria' | 'cristiano' |
| FERROPLAST | 'Indústria' | 'carlos' |
| MAXPRESS | 'Indústria' | 'felipe' |
| FUNDIFER | 'Indústria' | 'severiano' |

**Pattern** — for each client, the `consultorId` line looks like:
```
id:'CLIENTEID', projeto:'SAGP-XXXXX', produto:'CPS', consultorId:'xxx',
```

Add `segmento` and `csId` on the same line, and add `ativPlaybooks: [],` after `proximaAcao`. Repeat for all 38 clients. Steps 1–3 below show the 3 demo clients in full; steps 4–5 cover the remaining 35 using the same pattern.

- [ ] **Step 1: Edit KMSIL** (demo ativPlaybooks — 1 playbook, 2 atividades, 1 registro)

Old string:
```
    id:'KMSIL', projeto:'SAGP-00036', produto:'CPS', consultorId:'ana-paula',
    etapa:'Engajamento', dataInicio:'2026-03-05', prazo:'2026-09-30',
    proximaAcao:'Acompanhar uso do módulo Compras',
```

New string:
```
    id:'KMSIL', projeto:'SAGP-00036', produto:'CPS', consultorId:'ana-paula', segmento:'Saúde', csId:'cristiano',
    etapa:'Engajamento', dataInicio:'2026-03-05', prazo:'2026-09-30',
    proximaAcao:'Acompanhar uso do módulo Compras',
    ativPlaybooks:[
      {id:'pb_k1',nome:'Implantação CPS',criadoEm:'2026-03-10T09:00:00',atividades:[
        {id:'at_k1',nome:'1ª Reunião de engajamento',registros:[
          {id:'reg_k1',autor:'Ana Paula Souza',data:'2026-03-10T14:00:00',texto:'Kickoff realizado com equipe de TI. Alinhado acesso ao ambiente de homologação.'}
        ]},
        {id:'at_k2',nome:'2ª Reunião de engajamento',registros:[]}
      ]}
    ],
```

- [ ] **Step 2: Edit RAS METAL** (demo ativPlaybooks — 2 playbooks, 2+1 atividades, 3 registros)

Old string:
```
    id:'RAS METAL', projeto:'SAGP-00091', produto:'CPS', consultorId:'ana-paula',
    etapa:'Evolução', dataInicio:'2026-01-30', prazo:'2026-05-11',
    proximaAcao:'Resolver pendência de importação de dados',
```

New string:
```
    id:'RAS METAL', projeto:'SAGP-00091', produto:'CPS', consultorId:'ana-paula', segmento:'Indústria', csId:'felipe',
    etapa:'Evolução', dataInicio:'2026-01-30', prazo:'2026-05-11',
    proximaAcao:'Resolver pendência de importação de dados',
    ativPlaybooks:[
      {id:'pb_r1',nome:'Implantação CPS',criadoEm:'2026-02-01T09:00:00',atividades:[
        {id:'at_r1',nome:'1ª Reunião de engajamento',registros:[
          {id:'reg_r1',autor:'Ana Paula Souza',data:'2026-02-01T14:00:00',texto:'Kickoff realizado. Cliente com dificuldades de acesso ao sistema legado.'},
          {id:'reg_r2',autor:'Ana Paula Souza',data:'2026-02-08T10:30:00',texto:'Follow-up: acesso ao sistema legado resolvido. Importação de dados agendada.'}
        ]},
        {id:'at_r2',nome:'2ª Reunião de evolução',registros:[
          {id:'reg_r3',autor:'Ana Paula Souza',data:'2026-03-15T15:00:00',texto:'Parametrização do módulo Compras concluída. Aguardando validação do cliente.'}
        ]}
      ]},
      {id:'pb_r2',nome:'Visita técnica',criadoEm:'2026-03-20T09:00:00',atividades:[
        {id:'at_r3',nome:'Visita de campo',registros:[]}
      ]}
    ],
```

- [ ] **Step 3: Edit ROBOTIX** (demo ativPlaybooks — 1 playbook, 3 atividades, 2 registros)

Old string:
```
    id:'ROBOTIX', projeto:'SAGP-00131', produto:'NX/IOT', consultorId:'severiano',
```

Find the `proximaAcao` line for ROBOTIX (around line 899) and add `ativPlaybooks` after it. First check the exact text:

```
    id:'ROBOTIX', projeto:'SAGP-00131', produto:'NX/IOT', consultorId:'severiano',
```

New string (same line with fields added):
```
    id:'ROBOTIX', projeto:'SAGP-00131', produto:'NX/IOT', consultorId:'severiano', segmento:'Serviços', csId:'silvia',
```

Then find ROBOTIX's `proximaAcao` line and add `ativPlaybooks` after it. Read lines ~897–910 to find the exact `proximaAcao` text for ROBOTIX, then:

Old string (ROBOTIX proximaAcao):
```
    proximaAcao:'Integrar sensores com linha de montagem',
    fases: mkFases([
```

New string:
```
    proximaAcao:'Integrar sensores com linha de montagem',
    ativPlaybooks:[
      {id:'pb_rob1',nome:'Implantação NX/IOT',criadoEm:'2026-04-05T09:00:00',atividades:[
        {id:'at_rob1',nome:'1ª Reunião de engajamento',registros:[
          {id:'reg_rob1',autor:'Severiano Rocha',data:'2026-04-05T14:00:00',texto:'Kickoff realizado com sucesso. Equipe técnica bem engajada. Cronograma de instalação dos sensores definido.'}
        ]},
        {id:'at_rob2',nome:'Configuração de sensores',registros:[
          {id:'reg_rob2',autor:'Severiano Rocha',data:'2026-04-20T16:00:00',texto:'12 sensores instalados na linha de produção principal. Testes de conectividade OK.'}
        ]},
        {id:'at_rob3',nome:'Treinamento de usuários',registros:[]}
      ]}
    ],
    fases: mkFases([
```

- [ ] **Step 4: Edit remaining 35 clients — add segmento + csId to the id line**

For each client below, find the exact `id:'X', projeto:` line and append `segmento:'Y', csId:'Z',` after the `consultorId:'...',`. All get `ativPlaybooks: [],` added after their `proximaAcao` line.

Use the lookup table from the beginning of this task. Example pattern (AXONE):

Old string:
```
    id:'AXONE', projeto:'SAGP-00059', produto:'CPS', consultorId:'ana-paula',
    etapa:'Engajamento', dataInicio:'2026-03-10', prazo:'2026-08-02',
    proximaAcao:'Agendamento de treinamento avançado',
```

New string:
```
    id:'AXONE', projeto:'SAGP-00059', produto:'CPS', consultorId:'ana-paula', segmento:'Serviços', csId:'silvia',
    etapa:'Engajamento', dataInicio:'2026-03-10', prazo:'2026-08-02',
    proximaAcao:'Agendamento de treinamento avançado',
    ativPlaybooks:[],
```

Apply this same pattern to the remaining 35 clients (AÇO ART, ALPARGATAS CPS, FRAY, FELIX INDUSTRIAL, USIMAZA EMBRAER, CAMPOSC, SOARES FERRAMENTARIA, LIQUOS, METALVALE, SIMONSEN, MECATRON, POLIMOLD, ELETROTINS, BORBOREMA, RETALHOMAX, TORNEFER, INDALPE, ROTOFER, AGROFLEX, LAMIFER, PLASVALE, LAMINEX, COMPRESSEI, NXTEC, SENSORTEC, METATRON, PLASTIMETAL, IOTSYSTEM, NXPRIME, AUTOMIND, USINAGEM3D, FERROPLAST, MAXPRESS, FUNDIFER) using values from the lookup table.

- [ ] **Step 5: Test in browser**

Open DevTools > Console. Run: `getCliente('KMSIL').ativPlaybooks[0].atividades.length` — expect `2`. Run: `getCliente('AXONE').segmento` — expect `'Serviços'`. Run: `getCliente('RAS METAL').csId` — expect `'felipe'`.

- [ ] **Step 6: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(seed): adiciona segmento, csId e ativPlaybooks aos 38 clientes"
```

---

### Task 3: renderCliente rewrite + setClienteAba + renderAba360

**Files:**
- Modify: `grv-cs-jornada.html:2169-2279` — replace entire `renderCliente` function
- Add: `setClienteAba` function after `renderCliente`
- Add: `renderAba360` function after `setClienteAba`

**Interfaces:**
- Consumes: globals from Task 1 (`_cliente_id_atual`, `_cliente_aba`, `_pb_expandidos`, `_at_sel`, `_pb_form_open`, `_at_form_pb`)
- Consumes: `getCliente(id)`, `getProgresso(c)`, `getStatus(c)`, `getDiasNaEtapa(c)`, `getConsultores()`, `getConsultorAtivo()` — all existing
- Consumes: `fmtDate(s)`, `fmtDateTime(s)`, `getEtapaBadge(e)`, `getStatusBadge(s)` — all existing
- Consumes: `renderAbaAtividades(c)`, `renderAbaNotas(c)` — produced by Task 4 and Task 5
- Produces: `renderCliente(id)`, `setClienteAba(aba, clienteId)`, `renderAba360(c)`

- [ ] **Step 1: Replace renderCliente**

Find the entire existing `renderCliente` function. The old string begins with `function renderCliente(id) {` and ends with the closing `}` just before `function toggleFase(idx)`. Replace the entire block:

Old string:
```
function renderCliente(id) {
  const c   = getCliente(id);
  const sec = document.getElementById('sec-cliente');

  if (!c) {
    sec.innerHTML = `<div class="empty-state"><div class="es-icon">❓</div><div class="es-text">Cliente não encontrado.</div></div>`;
    return;
  }

  const prog   = getProgresso(c);
  const status = getStatus(c);
  const dias   = getDiasNaEtapa(c);
  const consul = getConsultores().find(x => x.id === c.consultorId)?.nome || c.consultorId;

  const fasesHtml = c.fases.map((f, fi) => {
    const feitas = f.tarefas.filter(t => t.feita).length;
    const isOpen = _open_fases[fi] !== false;
    return `<div class="phase-row">
      <div class="phase-hdr" onclick="toggleFase(${fi})">
        <div class="phase-hdr-left">
          <span class="phase-name">${f.nome}</span>
          <span class="phase-ct">${feitas}/${f.tarefas.length}</span>
        </div>
        <span class="phase-chev${isOpen?' open':''}">▶</span>
      </div>
      <div class="phase-body${isOpen?' open':''}">
        ${f.tarefas.map(t => `
          <div class="task-item${t.feita?' done':''}" id="ti_${t.id}">
            <input type="checkbox" id="ck_${t.id}"${t.feita?' checked':''}
              onchange="checkTask('${c.id}',${fi},'${t.id}')">
            <label for="ck_${t.id}">${t.texto}</label>
          </div>`).join('')}
      </div>
    </div>`;
  }).join('');

  const regsHtml = c.registros.length
    ? c.registros.map(r => `
      <div class="reg-item">
        <div class="reg-meta"><strong>${r.autor}</strong> · ${fmtDateTime(r.data)}</div>
        <div class="reg-text">${r.texto}</div>
      </div>`).join('')
    : `<div style="color:var(--text3);font-size:13px;padding:8px 0">Nenhum registro ainda.</div>`;

  const tlHtml = c.historicoEtapas.map(h => {
    const label = h.de
      ? `${h.de} → <strong style="color:var(--primary)">${h.para}</strong>`
      : `→ <strong style="color:var(--primary)">${h.para}</strong>`;
    return `<div class="tl-item">
      <div class="tl-dot"></div>
      <div class="tl-body">
        ${label}
        <div class="tl-meta">${fmtDateTime(h.data)} · ${h.motivo}</div>
      </div>
    </div>`;
  }).join('');

  sec.innerHTML = `
    <a class="back-link" href="#carteira">← Voltar à carteira</a>
    <div class="detail-header">
      <div class="dh-top">
        <div>
          <h2>${c.id}</h2>
          <div class="dh-projeto">${c.projeto} · ${c.produto}</div>
        </div>
        <div class="dh-badges">
          ${getEtapaBadge(c.etapa)}
          ${getStatusBadge(status)}
          <button class="btn btn-primary btn-sm" onclick="openModal('${c.id}')">Alterar Etapa</button>
        </div>
      </div>
      <div class="dh-meta">
        <div class="dh-meta-item"><span class="dh-meta-label">Consultor</span><span class="dh-meta-value">${consul}</span></div>
        <div class="dh-meta-item"><span class="dh-meta-label">Início</span><span class="dh-meta-value">${fmtDate(c.dataInicio)}</span></div>
        <div class="dh-meta-item">
          <span class="dh-meta-label">Prazo</span>
          <span class="dh-meta-value" style="${status==='Atrasado'?'color:var(--red)':''}">${fmtDate(c.prazo)}</span>
        </div>
        <div class="dh-meta-item"><span class="dh-meta-label">Dias na etapa</span><span class="dh-meta-value">${dias} dia${dias!==1?'s':''}</span></div>
      </div>
    </div>

    <div class="detail-layout">
      <div>
        <div class="card-block">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
            <div class="section-title" style="margin-bottom:0">Playbook</div>
            <span id="prog-pct-${c.id}" style="font-size:15px;font-weight:700;color:var(--primary)">${prog}%</span>
          </div>
          <div class="prog-wrap" style="height:8px;margin-bottom:18px">
            <div class="prog-fill" id="prog-bar-${c.id}" style="width:${prog}%"></div>
          </div>
          ${fasesHtml}
        </div>
      </div>
      <div>
        <div class="card-block">
          <div class="section-title">Registros</div>
          <div id="regs-${c.id}">${regsHtml}</div>
          <div class="reg-form">
            <textarea id="reg-input-${c.id}" placeholder="Adicionar anotação..."></textarea>
            <button class="btn btn-primary btn-sm" style="margin-top:8px" onclick="addRegistro('${c.id}')">Salvar registro</button>
          </div>
        </div>
        <div class="card-block" style="margin-top:16px">
          <div class="section-title">Histórico de etapas</div>
          <div class="tl-wrap">${tlHtml}</div>
        </div>
      </div>
    </div>`;
}
```

New string:
```
function renderCliente(id) {
  const sec = document.getElementById('sec-cliente');
  const c   = getCliente(id);

  if (!c) {
    sec.innerHTML = `<div class="empty-state"><div class="es-icon">❓</div><div class="es-text">Cliente não encontrado.</div></div>`;
    return;
  }

  if (id !== _cliente_id_atual) {
    _cliente_id_atual = id;
    _cliente_aba      = '360';
    _pb_expandidos    = {};
    _at_sel           = null;
    _pb_form_open     = false;
    _at_form_pb       = null;
    if (c.ativPlaybooks && c.ativPlaybooks.length > 0) {
      _pb_expandidos[c.ativPlaybooks[0].id] = true;
    }
  }

  const status = getStatus(c);
  const dias   = getDiasNaEtapa(c);
  const consul = getConsultores().find(x => x.id === c.consultorId)?.nome || c.consultorId;

  const abaContent = _cliente_aba === '360'
    ? renderAba360(c)
    : _cliente_aba === 'atividades'
    ? renderAbaAtividades(c)
    : renderAbaNotas(c);

  sec.innerHTML = `
    <a class="back-link" href="#carteira">← Voltar à carteira</a>
    <div class="detail-header">
      <div class="dh-top">
        <div>
          <h2>${c.id}</h2>
          <div class="dh-projeto">${c.projeto} · ${c.produto}</div>
        </div>
        <div class="dh-badges">
          ${getEtapaBadge(c.etapa)}
          ${getStatusBadge(status)}
          <button class="btn btn-primary btn-sm" onclick="openModal('${c.id}')">Alterar Etapa</button>
        </div>
      </div>
      <div class="dh-meta">
        <div class="dh-meta-item"><span class="dh-meta-label">Consultor</span><span class="dh-meta-value">${consul}</span></div>
        <div class="dh-meta-item"><span class="dh-meta-label">Início</span><span class="dh-meta-value">${fmtDate(c.dataInicio)}</span></div>
        <div class="dh-meta-item">
          <span class="dh-meta-label">Prazo</span>
          <span class="dh-meta-value" style="${status==='Atrasado'?'color:var(--red)':''}">${fmtDate(c.prazo)}</span>
        </div>
        <div class="dh-meta-item"><span class="dh-meta-label">Dias na etapa</span><span class="dh-meta-value">${dias} dia${dias!==1?'s':''}</span></div>
      </div>
    </div>

    <div class="cliente-tabs">
      <button class="cliente-tab${_cliente_aba==='360'?' active':''}" onclick="setClienteAba('360','${c.id}')">Visão 360°</button>
      <button class="cliente-tab${_cliente_aba==='atividades'?' active':''}" onclick="setClienteAba('atividades','${c.id}')">Atividades</button>
      <button class="cliente-tab${_cliente_aba==='notas'?' active':''}" onclick="setClienteAba('notas','${c.id}')">Notas</button>
    </div>

    ${abaContent}`;
}

function setClienteAba(aba, clienteId) {
  _cliente_aba = aba;
  renderCliente(clienteId);
}
```

- [ ] **Step 2: Add renderAba360 after setClienteAba**

Insert the following function immediately after the `setClienteAba` closing brace:

```javascript
function renderAba360(c) {
  const prog   = getProgresso(c);
  const csNome = getConsultores().find(x => x.id === c.csId)?.nome || '—';
  const consultorNome = getConsultores().find(x => x.id === c.consultorId)?.nome || c.consultorId;

  const fasesHtml = c.fases.map((f, fi) => {
    const feitas = f.tarefas.filter(t => t.feita).length;
    const isOpen = _open_fases[fi] !== false;
    return `<div class="phase-row">
      <div class="phase-hdr" onclick="toggleFase(${fi})">
        <div class="phase-hdr-left">
          <span class="phase-name">${f.nome}</span>
          <span class="phase-ct">${feitas}/${f.tarefas.length}</span>
        </div>
        <span class="phase-chev${isOpen?' open':''}">▶</span>
      </div>
      <div class="phase-body${isOpen?' open':''}">
        ${f.tarefas.map(t => `
          <div class="task-item${t.feita?' done':''}" id="ti_${t.id}">
            <input type="checkbox" id="ck_${t.id}"${t.feita?' checked':''}
              onchange="checkTask('${c.id}',${fi},'${t.id}')">
            <label for="ck_${t.id}">${t.texto}</label>
          </div>`).join('')}
      </div>
    </div>`;
  }).join('');

  const tlHtml = c.historicoEtapas.map(h => {
    const label = h.de
      ? `${h.de} → <strong style="color:var(--primary)">${h.para}</strong>`
      : `→ <strong style="color:var(--primary)">${h.para}</strong>`;
    return `<div class="tl-item">
      <div class="tl-dot"></div>
      <div class="tl-body">
        ${label}
        <div class="tl-meta">${fmtDateTime(h.data)} · ${h.motivo}</div>
      </div>
    </div>`;
  }).join('');

  return `
    <div class="grid-360">
      <div class="card-360">
        <div class="c360-label">Segmento</div>
        <div class="c360-value">${c.segmento || '—'}</div>
      </div>
      <div class="card-360">
        <div class="c360-label">CS Responsável</div>
        <div class="c360-value">${csNome}</div>
      </div>
      <div class="card-360">
        <div class="c360-label">Consultor Digital</div>
        <div class="c360-value">${consultorNome}</div>
      </div>
      <div class="card-360">
        <div class="c360-label">% Implantação</div>
        <div class="c360-value">${prog}%</div>
        <div class="c360-prog"><div class="c360-prog-fill" style="width:${prog}%"></div></div>
      </div>
    </div>

    <div class="card-block">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
        <div class="section-title" style="margin-bottom:0">Playbook de Implantação</div>
        <span id="prog-pct-${c.id}" style="font-size:15px;font-weight:700;color:var(--primary)">${prog}%</span>
      </div>
      <div class="prog-wrap" style="height:8px;margin-bottom:12px">
        <div class="prog-fill" id="prog-bar-${c.id}" style="width:${prog}%"></div>
      </div>
      <div style="margin-bottom:16px">
        <a href="#" onclick="setClienteAba('atividades','${c.id}');return false;" style="font-size:12px;color:var(--primary);text-decoration:none;font-weight:600">Ver Atividades →</a>
      </div>
      ${fasesHtml}
    </div>

    <div class="card-block" style="margin-top:16px">
      <div class="section-title">Histórico de etapas</div>
      <div class="tl-wrap">${tlHtml}</div>
    </div>`;
}
```

- [ ] **Step 3: Test in browser**

Navigate to client KMSIL. Verify:
- 3 tabs appear: "Visão 360°", "Atividades", "Notas"
- Visão 360° tab is active by default
- Grid shows 4 cards: Segmento "Saúde", CS "Cristiano..." , Consultor Digital "Ana Paula...", % Implantação with a bar
- Checklist still shows phases; checking a checkbox updates `prog-pct-${c.id}` and `prog-bar-${c.id}`
- "Ver Atividades →" link switches to Atividades tab (empty placeholder until Task 4)
- Navigate to another client — state resets (tabs back to 360°)

- [ ] **Step 4: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(cliente): aba Visão 360° com grid de campos e checklist"
```

---

### Task 4: renderAbaAtividades + navigation mutations

**Files:**
- Modify: `grv-cs-jornada.html` — add functions after `renderAba360`

**Interfaces:**
- Consumes: `_pb_expandidos`, `_at_sel`, `_pb_form_open`, `_at_form_pb` from Task 1
- Consumes: `c.ativPlaybooks[]` structure from Task 2
- Produces: `renderAbaAtividades(c)`, `toggleAtivPlaybook(pbId, clienteId)`, `selecionarAtividade(pbId, atId, clienteId)`, `abrirFormPlaybook(clienteId)`, `cancelarFormPlaybook(clienteId)`, `abrirFormAtividade(pbId, clienteId)`, `cancelarFormAtividade(clienteId)`

- [ ] **Step 1: Add renderAbaAtividades and navigation mutations after renderAba360**

Insert the following block immediately after the closing `}` of `renderAba360`:

```javascript
function renderAbaAtividades(c) {
  const pbs = c.ativPlaybooks || [];

  const newPbFormHtml = _pb_form_open
    ? `<div class="pb-inline-form">
        <input class="pb-inline-input" id="pb-nome-input" placeholder="Nome do playbook..." onkeydown="if(event.key==='Enter')criarAtivPlaybook('${c.id}')">
        <button class="btn btn-primary btn-sm" onclick="criarAtivPlaybook('${c.id}')">Criar</button>
        <button class="btn btn-sm" onclick="cancelarFormPlaybook('${c.id}')">✕</button>
       </div>`
    : `<button class="pb-add-btn" onclick="abrirFormPlaybook('${c.id}')">+ Novo</button>`;

  const pbListHtml = pbs.map(pb => {
    const expanded = _pb_expandidos[pb.id];
    const atsHtml  = expanded ? pb.atividades.map(at => {
      const hasRegs = at.registros && at.registros.length > 0;
      const active  = _at_sel === at.id;
      return `<div class="pb-item${active?' active':''}" onclick="selecionarAtividade('${pb.id}','${at.id}','${c.id}')">
        <span>${hasRegs ? '●' : '○'}</span>
        <span>${at.nome}</span>
      </div>`;
    }).join('') + (_at_form_pb === pb.id
      ? `<div class="pb-inline-form">
          <input class="pb-inline-input" id="at-nome-input-${pb.id}" placeholder="Nome da atividade..." onkeydown="if(event.key==='Enter')criarAtividade('${pb.id}','${c.id}')">
          <button class="btn btn-primary btn-sm" onclick="criarAtividade('${pb.id}','${c.id}')">Criar</button>
          <button class="btn btn-sm" onclick="cancelarFormAtividade('${c.id}')">✕</button>
         </div>`
      : `<button class="pb-add-btn" onclick="abrirFormAtividade('${pb.id}','${c.id}')">+ Atividade</button>`) : '';

    return `<div>
      <div class="pb-title-row" onclick="toggleAtivPlaybook('${pb.id}','${c.id}')">
        <span>📋</span>
        <span>${pb.nome}</span>
        <span class="pb-chev">${expanded ? '▾' : '▸'}</span>
      </div>
      ${atsHtml}
    </div>`;
  }).join('');

  let panelHtml;
  if (!_at_sel) {
    panelHtml = `<div class="at-empty">
      <div style="font-size:32px">📝</div>
      <div>Selecione uma atividade<br>para registrar reunião,<br>decisão ou detalhe.</div>
    </div>`;
  } else {
    let foundAt = null, foundPbId = null;
    for (const pb of pbs) {
      const at = pb.atividades.find(a => a.id === _at_sel);
      if (at) { foundAt = at; foundPbId = pb.id; break; }
    }
    if (!foundAt) {
      panelHtml = `<div class="at-empty"><div>Atividade não encontrada.</div></div>`;
    } else {
      const regsHtml = foundAt.registros.length
        ? foundAt.registros.map(r => `
          <div class="at-reg-item">
            <div class="at-reg-meta">${r.autor} · ${fmtDateTime(r.data)}</div>
            <div class="at-reg-text">${r.texto}</div>
          </div>`).join('')
        : '';
      panelHtml = `
        <div class="at-title">${foundAt.nome}</div>
        ${regsHtml}
        <div class="at-write">
          <textarea id="at-reg-input" placeholder="Registrar reunião, decisão ou detalhe..." style="width:100%;min-height:90px;padding:10px;border:1px solid var(--border);border-radius:var(--radius);font-size:13px;resize:vertical;box-sizing:border-box"></textarea>
          <button class="btn btn-primary btn-sm" style="margin-top:8px" onclick="addRegistroAtividade('${c.id}','${foundPbId}','${foundAt.id}')">Salvar registro</button>
        </div>`;
    }
  }

  return `<div class="pb-layout">
    <div class="pb-sidebar">
      ${newPbFormHtml}
      ${pbListHtml}
    </div>
    <div class="pb-panel">${panelHtml}</div>
  </div>`;
}

function toggleAtivPlaybook(pbId, clienteId) {
  _pb_expandidos[pbId] = !_pb_expandidos[pbId];
  renderCliente(clienteId);
}

function selecionarAtividade(pbId, atId, clienteId) {
  _pb_expandidos[pbId] = true;
  _at_sel = atId;
  renderCliente(clienteId);
}

function abrirFormPlaybook(clienteId) {
  _pb_form_open = true;
  renderCliente(clienteId);
}

function cancelarFormPlaybook(clienteId) {
  _pb_form_open = false;
  renderCliente(clienteId);
}

function abrirFormAtividade(pbId, clienteId) {
  _at_form_pb = pbId;
  renderCliente(clienteId);
}

function cancelarFormAtividade(clienteId) {
  _at_form_pb = null;
  renderCliente(clienteId);
}
```

- [ ] **Step 2: Test in browser**

Navigate to client RAS METAL. Click "Atividades" tab. Verify:
- Left sidebar shows playbook "Implantação CPS" expanded with 2 atividades
- Bullet "●" appears next to "1ª Reunião de engajamento" (has registro) and "2ª Reunião de evolução"
- Click an atividade — right panel shows its name + registros list + textarea + "Salvar registro" button
- Click "▸" chevron next to "Visita técnica" — it expands, shows "Visita de campo" with "○" bullet
- Click "+ Novo" button — inline form appears with input; "✕" cancels it
- Click "+ Atividade" under a playbook — inline form appears below that playbook's atividades

Navigate to client AXONE (no ativPlaybooks). Click "Atividades" tab. Verify: only "+ Novo" button, right panel shows empty state.

- [ ] **Step 3: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(cliente): aba Atividades com master-detail e navegação de playbooks"
```

---

### Task 5: Create mutations + renderAbaNotas

**Files:**
- Modify: `grv-cs-jornada.html` — add functions after the navigation mutations from Task 4

**Interfaces:**
- Consumes: `getCliente(id)`, `saveCliente(c)` — existing DB layer functions
- Consumes: `getConsultores()`, `getConsultorAtivo()` — existing, at line ~995
- Consumes: `_pb_form_open`, `_at_form_pb`, `_at_sel`, `_pb_expandidos` from Task 1
- Produces: `criarAtivPlaybook(clienteId)`, `criarAtividade(pbId, clienteId)`, `addRegistroAtividade(clienteId, pbId, atId)`, `renderAbaNotas(c)`

- [ ] **Step 1: Add create mutations and renderAbaNotas after cancelarFormAtividade**

Insert the following block immediately after the closing `}` of `cancelarFormAtividade`:

```javascript
function criarAtivPlaybook(clienteId) {
  const input = document.getElementById('pb-nome-input');
  const nome  = input?.value?.trim();
  if (!nome) return;
  const c  = getCliente(clienteId);
  const id = 'pb_' + Date.now();
  c.ativPlaybooks = c.ativPlaybooks || [];
  c.ativPlaybooks.push({id, nome, criadoEm: new Date().toISOString(), atividades: []});
  saveCliente(c);
  _pb_form_open      = false;
  _pb_expandidos[id] = true;
  renderCliente(clienteId);
}

function criarAtividade(pbId, clienteId) {
  const input = document.getElementById('at-nome-input-' + pbId);
  const nome  = input?.value?.trim();
  if (!nome) return;
  const c  = getCliente(clienteId);
  const pb = (c.ativPlaybooks || []).find(p => p.id === pbId);
  if (!pb) return;
  const id = 'at_' + Date.now();
  pb.atividades.push({id, nome, registros: []});
  saveCliente(c);
  _at_form_pb = null;
  _at_sel     = id;
  renderCliente(clienteId);
}

function addRegistroAtividade(clienteId, pbId, atId) {
  const ta    = document.getElementById('at-reg-input');
  const texto = ta?.value?.trim();
  if (!texto) return;
  const c     = getCliente(clienteId);
  const pb    = (c.ativPlaybooks || []).find(p => p.id === pbId);
  if (!pb) return;
  const at    = pb.atividades.find(a => a.id === atId);
  if (!at) return;
  const ativo = getConsultorAtivo();
  const autor = getConsultores().find(x => x.id === ativo)?.nome || 'Consultor';
  at.registros.unshift({id:'reg_'+Date.now(), autor, data: new Date().toISOString(), texto});
  saveCliente(c);
  renderCliente(clienteId);
}

function renderAbaNotas(c) {
  const regsHtml = c.registros.length
    ? c.registros.map(r => `
      <div class="at-reg-item">
        <div class="at-reg-meta">${r.autor} · ${fmtDateTime(r.data)}</div>
        <div class="at-reg-text">${r.texto}</div>
      </div>`).join('')
    : `<div style="color:var(--text3);font-size:13px;padding:16px 0">Nenhuma nota ainda.</div>`;

  return `<div class="card-block">
    <div class="section-title">Notas</div>
    <div id="regs-${c.id}">${regsHtml}</div>
    <div class="reg-form at-write">
      <textarea id="reg-input-${c.id}" placeholder="Adicionar anotação..." style="width:100%;min-height:90px;padding:10px;border:1px solid var(--border);border-radius:var(--radius);font-size:13px;resize:vertical;box-sizing:border-box"></textarea>
      <button class="btn btn-primary btn-sm" style="margin-top:8px" onclick="addRegistro('${c.id}')">Salvar nota</button>
    </div>
  </div>`;
}
```

- [ ] **Step 2: Test full flow — create ativPlaybook**

Navigate to client AXONE (no ativPlaybooks). Click "Atividades" tab. Click "+ Novo". Type "Visita Comercial". Press Enter or click "Criar". Verify:
- New playbook "Visita Comercial" appears in sidebar, expanded
- Right panel shows empty state (no atividade selected)
- DevTools: `getCliente('AXONE').ativPlaybooks.length` → `1`

- [ ] **Step 3: Test full flow — create atividade + salvar registro**

Still on AXONE Atividades tab. Click "+ Atividade" under "Visita Comercial". Type "1ª Visita de campo". Press Enter. Verify:
- New atividade appears in sidebar with "○" bullet, selected (highlighted)
- Right panel shows atividade name, empty registros list, textarea + button
- Type "Visita agendada para 30/06." Click "Salvar registro". Verify:
  - Registro appears in the panel with autor name + timestamp
  - Bullet changes from "○" to "●"
  - `getCliente('AXONE').ativPlaybooks[0].atividades[0].registros.length` → `1`

- [ ] **Step 4: Test Notas tab**

Navigate to client KMSIL. Click "Notas" tab. Verify:
- Existing registros (from `c.registros`) appear in the card
- Textarea + "Salvar nota" button at bottom
- Type a note, click "Salvar nota". Verify it appears at top of list (prepended).
- `getCliente('KMSIL').registros[0].texto` matches the note just typed.

- [ ] **Step 5: Test state reset**

Navigate to KMSIL > Atividades tab > select an atividade. Then navigate to another client (click back and open a different client). Verify: arrives on Visão 360° tab, no atividade selected, first ativPlaybook auto-expanded if the client has one.

- [ ] **Step 6: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(cliente): criar playbooks/atividades, salvar registros e aba Notas"
```

---

## Spec Coverage Check

| Spec requirement | Covered by |
|---|---|
| Visão 360° grid 4 cards (segmento, CS, consultor, %) | Task 3 renderAba360 |
| `prog-pct-${c.id}` and `prog-bar-${c.id}` IDs preserved | Task 3 renderAba360 checklist section |
| Link "Ver Atividades →" in 360° | Task 3 renderAba360 |
| Histórico de etapas in 360° | Task 3 renderAba360 tlHtml |
| Abas com sublinhado laranja, aba ativa bold | Task 1 CSS `.cliente-tab.active` |
| Master-detail grid 260px 1fr | Task 1 CSS `.pb-layout` |
| ativPlaybook expand/collapse | Task 4 toggleAtivPlaybook |
| ● / ○ bullet para atividade com/sem registros | Task 4 renderAbaAtividades |
| Atividade selecionada: fundo #FFF3EE, borda esquerda | Task 1 CSS `.pb-item.active` |
| Form inline criar ativPlaybook | Task 4 renderAbaAtividades + Task 5 criarAtivPlaybook |
| Form inline criar atividade | Task 4 renderAbaAtividades + Task 5 criarAtividade |
| Painel vazio com "Selecione uma atividade" | Task 4 renderAbaAtividades panelHtml empty state |
| Registros em ordem cronológica reversa (prepend) | Task 5 addRegistroAtividade unshift |
| consultorNome via getConsultorAtivo() | Task 5 addRegistroAtividade |
| Estado reset ao trocar cliente | Task 3 renderCliente state reset block |
| Auto-expand primeiro ativPlaybook | Task 3 renderCliente state reset block |
| Aba Notas com registros gerais + addRegistro | Task 5 renderAbaNotas |
| segmento + csId em todos 38 clientes | Task 2 |
| Demo ativPlaybooks em KMSIL, RAS METAL, ROBOTIX | Task 2 steps 1-3 |
| Criação com input vazio: não cria | Task 5 criarAtivPlaybook + criarAtividade (if !nome return) |
| csId não encontrado → exibe "—" | Task 3 renderAba360 (?.nome \|\| '—') |
