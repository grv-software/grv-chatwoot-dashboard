# Cliente Tabs Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar KPI strip permanente no header do cliente (health, CSAT, NPS, próxima ação), trocar aba padrão para Atividades, reorganizar Visão 360 em 2 colunas sem timeline, e adicionar tipos (Observação/Alerta/Decisão) na aba Notas.

**Architecture:** Single-file SPA `grv-cs-jornada.html`. Todas as mudanças são em CSS inline no `<style>` e em funções JS de render de string HTML. Nenhuma lógica de dado, rota ou cálculo é alterada — as funções `calcHealthScore`, `calcCsatAtual`, `calcNps`, `tempoComoCliente` são usadas como estão.

**Tech Stack:** HTML/CSS/JS puro no arquivo `grv-cs-jornada.html`. Sem build. Teste = abrir no browser e navegar.

## Global Constraints

- Arquivo único: `grv-cs-jornada.html` na raiz — todas as edições aqui.
- Branch: `alteracoes`. Nunca commitar em `main`.
- Não alterar: `calcHealthScore()`, `calcCsatAtual()`, `calcNps()`, `tempoComoCliente()`, `adicionarContato()`, `removerContato()`, `registrarCsat()`, `registrarNps()`, `cancelarFormContato()`, `cancelarFormCsat()`, `cancelarFormNps()`.
- Não alterar: estrutura de `c.ativPlaybooks`, `c.csatRespostas`, `c.npsRespostas`, `c.contatos`, `c.registros`.
- Verificação = abrir `grv-cs-jornada.html` no Chrome, navegar até detalhe de qualquer cliente.
- Commits frequentes por task concluída.

---

### Task 1: CSS — KPI strip, layout 360, contatos, notas, alert bar

**Files:**
- Modify: `grv-cs-jornada.html` — bloco `<style>`, após a linha 537 (`.dc-chips`) e após linha 354 (`.card-block`)

**Interfaces:**
- Produces: classes CSS usadas pelas Tasks 2–5: `.dc-kpi-strip`, `.dc-kpi`, `.dc-kpi-label`, `.dc-kpi-val`, `.dc-kpi-sub`, `.dc-kpi-next`, `.v360-cols`, `.v360-col`, `.contato-link`, `.nota-card`, `.nota-tipo`, `.nota-tipo-alerta`, `.nota-tipo-decisao`, `.nota-tipo-observacao`, `.pb-badge-alert`, `.alert-bar`, `.alert-bar-text`, `.alert-bar-link`

- [ ] **Step 1: Adicionar CSS da KPI strip do header**

Localizar `.dc-chips{...}` (~linha 537). Logo após essa linha, inserir:

```css
.dc-kpi-strip{display:flex;border-top:1px solid var(--border-2)}
.dc-kpi{flex:1;padding:10px 14px;border-right:1px solid var(--border-2)}
.dc-kpi:last-child{border-right:none;flex:2}
.dc-kpi-label{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text4);margin-bottom:4px}
.dc-kpi-val{font-size:22px;font-weight:800;line-height:1;font-variant-numeric:tabular-nums;letter-spacing:-.8px}
.dc-kpi-sub{font-size:10px;color:var(--text3);margin-top:2px}
.dc-kpi-next{font-size:13px;font-weight:700;color:var(--text);margin-top:2px}
```

- [ ] **Step 2: Adicionar CSS do layout 2 colunas da Visão 360**

Logo após o bloco inserido no Step 1, adicionar:

```css
.v360-cols{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}
.v360-col{}
.contato-link{display:inline-flex;align-items:center;gap:3px;font-size:10px;font-weight:600;color:var(--text3);padding:2px 7px;border-radius:5px;background:var(--bg);text-decoration:none;border:1px solid var(--border)}
.contato-link:hover{background:var(--border-2);color:var(--text2)}
```

- [ ] **Step 3: Adicionar CSS das notas tipadas**

Logo após o bloco do Step 2, adicionar:

```css
.nota-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 16px;margin-bottom:8px;box-shadow:var(--shadow-1);border-left:3px solid var(--border)}
.nota-card.tipo-alerta{border-left-color:var(--red)}
.nota-card.tipo-decisao{border-left-color:#2563EB}
.nota-card.tipo-observacao{border-left-color:var(--text4)}
.nota-top{display:flex;align-items:flex-start;gap:8px;margin-bottom:8px}
.nota-tipo{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;padding:2px 7px;border-radius:5px;flex-shrink:0}
.nota-tipo-alerta{background:rgba(220,38,38,.1);color:var(--red)}
.nota-tipo-decisao{background:rgba(37,99,235,.1);color:#2563EB}
.nota-tipo-observacao{background:var(--bg);color:var(--text3)}
.nota-meta{flex:1;display:flex;align-items:center;justify-content:flex-end;gap:8px}
.nota-autor{font-size:11px;font-weight:600;color:var(--text2)}
.nota-data{font-size:11px;color:var(--text4)}
.nota-texto{font-size:13px;color:var(--text);line-height:1.55}
.nota-add-btn{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:700;color:var(--primary);background:rgba(224,90,30,.08);border:1px solid rgba(224,90,30,.15);border-radius:7px;padding:6px 12px;cursor:pointer}
.nota-add-btn:hover{background:rgba(224,90,30,.15)}
.nota-tipo-select{font-size:12px;font-weight:600;background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:5px 8px;cursor:pointer;color:var(--text2)}
```

- [ ] **Step 4: Adicionar CSS do alert bar e pb-badge-alert**

Logo após o bloco do Step 3, adicionar:

```css
.alert-bar{display:flex;align-items:center;gap:10px;background:rgba(220,38,38,.05);border:1px solid rgba(220,38,38,.15);border-radius:8px;padding:8px 12px;margin-bottom:12px;font-size:12px}
.alert-bar-text{flex:1;font-weight:600;color:#B91C1C}
.alert-bar-sub{color:var(--text3);font-weight:400}
.alert-bar-link{font-size:11px;font-weight:700;color:var(--red);cursor:pointer;white-space:nowrap}
.alert-bar-link:hover{text-decoration:underline}
.pb-badge-alert{font-size:9px;font-weight:700;background:rgba(220,38,38,.1);color:var(--red);padding:1px 5px;border-radius:4px}
```

- [ ] **Step 5: Verificar que os novos seletores existem**

Abrir `grv-cs-jornada.html` no browser (Ctrl+F5). Abrir DevTools → Console. Colar:
```javascript
['dc-kpi-strip','v360-cols','contato-link','nota-card','alert-bar','pb-badge-alert'].forEach(c => {
  const el = document.createElement('div');
  el.className = c;
  document.body.appendChild(el);
  const s = getComputedStyle(el);
  console.log(c, ':', s.display || s.border || 'ok');
  el.remove();
});
```
Expected: nenhum erro, valores computados para cada classe.

- [ ] **Step 6: Commit**

```
git add grv-cs-jornada.html
git commit -m "style(cliente): CSS para KPI strip, layout 360, notas tipadas, alert bar"
```

---

### Task 2: `renderCliente()` — KPI strip no header + aba padrão + badge

**Files:**
- Modify: `grv-cs-jornada.html` — linha 5400 (`_cliente_aba` default), linhas 5419–5421 (reset de aba), linhas 5440–5467 (HTML do header e tabs)

**Interfaces:**
- Consumes: `calcHealthScore(c)`, `hsColor(hs)`, `calcCsatAtual(c)`, `calcNps(c)`, `tempoComoCliente(c.dataInicioImplantacao)` — funções existentes.
- Produces: header do cliente com `.dc-kpi-strip` e tabs com badge de atrasadas.

- [ ] **Step 1: Mudar aba padrão global**

Localizar a linha 5400:
```javascript
let _cliente_aba      = '360';
```
Substituir por:
```javascript
let _cliente_aba      = 'atividades';
```

- [ ] **Step 2: Mudar aba padrão no reset de cliente**

Dentro de `renderCliente(id)`, localizar (~linha 5420):
```javascript
    _cliente_aba      = '360';
```
Substituir por:
```javascript
    _cliente_aba      = 'atividades';
```

- [ ] **Step 3: Substituir o bloco de cálculo de variáveis e o HTML do header**

No corpo de `renderCliente(id)`, localizar o bloco que termina com `const abaContent = ...` e o `sec.innerHTML = \`...\``. Substituir o trecho completo (desde `const abaContent` até o fechamento do template string) pelo seguinte:

```javascript
  // ── Cálculos para a KPI strip ──
  const _hs     = calcHealthScore(c);
  const _hsClr  = _hs !== null ? hsColor(_hs) : 'var(--text3)';
  const _csat   = calcCsatAtual(c);
  const _csatClr = _csat !== null
    ? (_csat >= 4 ? 'var(--green)' : _csat >= 3 ? 'var(--yellow)' : 'var(--red)')
    : 'var(--text3)';
  const _csatLastDate = (c.csatRespostas||[]).length
    ? new Date((c.csatRespostas||[]).slice(-1)[0].data).toLocaleDateString('pt-BR')
    : '';
  const _nps    = calcNps(c);
  const _npsClr = _nps !== null
    ? (_nps >= 50 ? 'var(--green)' : _nps >= 0 ? 'var(--yellow)' : 'var(--red)')
    : 'var(--text3)';
  const _npsLbl = _nps !== null
    ? (_nps >= 50 ? 'Excelente' : _nps >= 0 ? 'Bom' : 'Crítico') : '';

  // Próxima atividade não concluída (todos os playbooks ativos)
  const _allPend = (c.ativPlaybooks || [])
    .filter(function(pb){ return pb.status !== 'cancelado' && !pb.encerrado; })
    .reduce(function(arr, pb){ return arr.concat(pb.atividades || []); }, [])
    .filter(function(at){ return at.status !== 'concluida' && at.dataLimite; })
    .sort(function(a,b){ return a.dataLimite.localeCompare(b.dataLimite); });
  const _proxAt    = _allPend[0] || null;
  const _proxData  = _proxAt ? new Date(_proxAt.dataLimite).toLocaleDateString('pt-BR') : '';
  const _proxAcao  = c.proximaAcao || '—';

  // Badge de atrasadas na aba Atividades
  const _totalAtrasadas = (c.ativPlaybooks || []).reduce(function(acc, pb) {
    if (pb.status === 'cancelado') return acc;
    return acc + (pb.atividades || []).filter(function(at){ return at.status === 'atrasada'; }).length;
  }, 0);
  const _tabBadge = _totalAtrasadas > 0
    ? '<span style="font-size:10px;font-weight:700;background:#DC2626;color:#fff;padding:1px 5px;border-radius:10px;margin-left:4px;line-height:1.4">' + _totalAtrasadas + '</span>'
    : '';

  // Tempo como cliente para o subtítulo
  const _tempoStr = c.dataInicioImplantacao ? tempoComoCliente(c.dataInicioImplantacao) : '';

  const abaContent = _cliente_aba === '360'
    ? renderAba360(c)
    : _cliente_aba === 'atividades'
    ? renderAbaAtividades(c)
    : renderAbaNotas(c);

  sec.innerHTML = `
    <div class="dc-header">
      <a class="dc-back" href="#carteira">←</a>
      <div class="dc-avatar-lg" style="background:linear-gradient(135deg,${_ag[0]},${_ag[1]})">${_letter}</div>
      <div class="dc-info">
        <div class="dc-name">${c.id}</div>
        <div class="dc-sub">${c.projeto ? c.projeto + ' · ' : ''}${_consulNome}${_tempoStr ? ' · ' + _tempoStr + ' como cliente' : ''}</div>
        <div class="dc-chips">
          ${_stCS ? '<span class="chip-base chip-status-' + _stCS + '">' + (_stLabels[_stCS]||_stCS) + '</span>' : ''}
          ${c.etapa ? getEtapaBadge(c.etapa) : ''}
          ${c.segmento ? '<span class="chip-base chip-seg">' + c.segmento + '</span>' : ''}
          ${c.produto  ? '<span class="chip-base chip-prod">' + c.produto  + '</span>' : ''}
        </div>
        ${(() => { var lt = getDiasUltimoContato(c); return lt !== null ? '<div style="font-size:11px;color:' + (lt===0?'#22c55e':lt<=7?'var(--text3)':lt<=14?'#eab308':'#ef4444') + ';margin-top:4px">Último contato: ' + (lt===0?'hoje':'há '+lt+' dia'+(lt===1?'':'s')) + '</div>' : ''; })()}
      </div>
    </div>

    <div class="dc-kpi-strip">
      <div class="dc-kpi">
        <div class="dc-kpi-label">Health Score</div>
        <div class="dc-kpi-val" style="color:${_hsClr}">${_hs !== null ? _hs : '—'}</div>
        <div class="dc-kpi-sub">${_hs !== null ? 'Saúde geral' : 'Sem dados suficientes'}</div>
      </div>
      <div class="dc-kpi">
        <div class="dc-kpi-label">CSAT</div>
        <div class="dc-kpi-val" style="color:${_csatClr}">${_csat !== null ? _csat : '—'}${_csat !== null ? '<span style="font-size:13px;color:var(--text4);font-weight:500"> /5</span>' : ''}</div>
        <div class="dc-kpi-sub">${_csatLastDate ? 'Última: ' + _csatLastDate : 'Sem respostas'}</div>
      </div>
      <div class="dc-kpi">
        <div class="dc-kpi-label">NPS</div>
        <div class="dc-kpi-val" style="color:${_npsClr}">${_nps !== null ? _nps : '—'}</div>
        <div class="dc-kpi-sub">${_npsLbl || 'Sem respostas'}</div>
      </div>
      <div class="dc-kpi">
        <div class="dc-kpi-label">Próxima ação</div>
        <div class="dc-kpi-next">${_proxAcao}</div>
        <div class="dc-kpi-sub">${_proxData ? '<span style="color:var(--yellow);font-weight:600">' + _proxData + '</span>' : 'Sem data definida'}</div>
      </div>
    </div>

    <div class="cliente-tabs">
      <button class="cliente-tab${_cliente_aba==='360'?' active':''}" onclick="setClienteAba('360','${c.id}')">Visão 360°</button>
      <button class="cliente-tab${_cliente_aba==='atividades'?' active':''}" onclick="setClienteAba('atividades','${c.id}')">Atividades${_tabBadge}</button>
      <button class="cliente-tab${_cliente_aba==='notas'?' active':''}" onclick="setClienteAba('notas','${c.id}')">Notas</button>
    </div>

    ${abaContent}`;
```

- [ ] **Step 4: Verificar visualmente**

Abrir `grv-cs-jornada.html` → navegar para Minha Carteira → clicar em qualquer cliente. Verificar:
- Aba "Atividades" abre por padrão (não "Visão 360°")
- KPI strip aparece entre o header e as tabs com 4 células: Health · CSAT · NPS · Próxima ação
- Se o cliente tem atividades atrasadas, badge vermelho aparece na tab "Atividades"
- Chip de health não aparece mais no `.dc-chips` (apenas etapa, segmento, produto)

- [ ] **Step 5: Commit**

```
git add grv-cs-jornada.html
git commit -m "feat(cliente): KPI strip no header, aba padrão Atividades, badge de atrasadas"
```

---

### Task 3: Reescrever `renderAba360(c)` — 2 colunas, sem timeline

**Files:**
- Modify: `grv-cs-jornada.html` — função `renderAba360(c)` (linhas 5491–5697)

**Interfaces:**
- Consumes: `calcCsatAtual(c)`, `calcNps(c)`, `tempoComoCliente()`, `adicionarContato()`, `removerContato()`, `registrarCsat()`, `registrarNps()`, `cancelarFormContato()`, `cancelarFormCsat()`, `cancelarFormNps()` — todas existentes, sem mudança.
- Produces: nova `renderAba360(c)` com layout 2 colunas (esquerda: Ciclo de vida + Contatos; direita: CSAT + NPS), 4 cards de referência no topo (Segmento, Produto, CS, Consultor).

- [ ] **Step 1: Substituir a função `renderAba360(c)` completa**

Localizar `function renderAba360(c) {` (~linha 5491). Substituir a função inteira (até a linha 5697 onde fecha o `}`) pelo seguinte:

```javascript
function renderAba360(c) {
  const csNome        = getConsultores().find(function(x){ return x.id === c.csId; })?.nome || '—';
  const consultorNome = getConsultores().find(function(x){ return x.id === c.consultorId; })?.nome || c.consultorId || '—';

  const csatVal  = calcCsatAtual(c);
  const csatClr  = csatVal !== null ? (csatVal >= 4 ? 'var(--green)' : csatVal >= 3 ? 'var(--yellow)' : 'var(--red)') : 'var(--text3)';
  const csatLbl  = csatVal !== null ? (csatVal >= 4 ? 'Excelente' : csatVal >= 3 ? 'Bom' : 'Crítico') : '';
  const npsVal   = calcNps(c);
  const npsClr   = npsVal !== null ? (npsVal >= 50 ? 'var(--green)' : npsVal >= 0 ? 'var(--yellow)' : 'var(--red)') : 'var(--text3)';
  const npsLbl   = npsVal !== null ? (npsVal >= 50 ? 'Excelente' : npsVal >= 0 ? 'Bom' : 'Crítico') : '';

  const dataImplant = c.dataInicioImplantacao ? new Date(c.dataInicioImplantacao).toLocaleDateString('pt-BR') : '—';
  const dataCS      = c.dataInicioCS ? new Date(c.dataInicioCS).toLocaleDateString('pt-BR') : '—';
  const tempo       = c.dataInicioImplantacao ? tempoComoCliente(c.dataInicioImplantacao) : '—';

  const contatosHtml = (c.contatos || []).length === 0
    ? '<p style="font-size:12px;color:var(--text3);margin:0 0 12px">Nenhum contato cadastrado ainda.</p>'
    : '<div style="margin-bottom:12px">' +
      (c.contatos || []).map(function(ct) {
        return '<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px solid var(--border-2)">'
          + '<div style="flex:1;min-width:0">'
            + '<div style="font-size:13px;font-weight:700;color:var(--text)">' + ct.nome
              + (ct.cargo ? '<span style="font-size:11px;color:var(--text3);font-weight:400"> · ' + ct.cargo + '</span>' : '') + '</div>'
            + '<div style="display:flex;gap:6px;margin-top:5px;flex-wrap:wrap">'
              + (ct.email ? '<a href="mailto:' + ct.email + '" class="contato-link"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 7L2 7"/></svg>' + ct.email + '</a>' : '')
              + (ct.whatsapp ? '<a href="https://wa.me/' + ct.whatsapp.replace(/\D/g,'') + '" target="_blank" class="contato-link"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.15 12a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.06 1.18h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.09 8.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 21 16"/></svg>' + ct.whatsapp + '</a>' : '')
            + '</div>'
          + '</div>'
          + '<button onclick="removerContato(\'' + c.id + '\',\'' + ct.id + '\')" title="Remover" style="flex-shrink:0;padding:3px 8px;background:transparent;border:1px solid var(--border);border-radius:4px;color:var(--text3);font-size:11px;cursor:pointer">✕</button>'
        + '</div>';
      }).join('') + '</div>';

  const csatRespHtml = (c.csatRespostas || []).length === 0
    ? '<p style="font-size:12px;color:var(--text3);margin:0 0 12px">Nenhuma pesquisa registrada ainda.</p>'
    : '<div style="margin-bottom:12px">' +
      (c.csatRespostas || []).slice().reverse().slice(0, 5).map(function(r) {
        const clr = r.score >= 4 ? 'var(--green)' : r.score >= 3 ? 'var(--yellow)' : 'var(--red)';
        return '<div style="display:flex;align-items:flex-start;gap:8px;padding:6px 0;border-bottom:1px solid var(--border-2)">'
          + '<div style="width:28px;height:28px;border-radius:6px;background:' + clr + '1a;color:' + clr + ';font-size:12px;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0">' + r.score + '</div>'
          + '<div style="flex:1"><div style="font-size:11px;color:var(--text3)">' + new Date(r.data).toLocaleDateString('pt-BR') + '</div>'
          + (r.obs ? '<div style="font-size:11px;color:var(--text2);margin-top:1px;font-style:italic">"' + r.obs + '"</div>' : '') + '</div>'
        + '</div>';
      }).join('') + '</div>';

  const npsRespHtml = (c.npsRespostas || []).length === 0
    ? '<p style="font-size:12px;color:var(--text3);margin:0 0 12px">Nenhuma resposta registrada ainda.</p>'
    : '<div style="margin-bottom:12px">' +
      (c.npsRespostas || []).slice().reverse().slice(0, 5).map(function(r) {
        const clr  = r.score >= 9 ? 'var(--green)' : r.score >= 7 ? 'var(--text3)' : 'var(--red)';
        const tipo = r.score >= 9 ? 'Promotor' : r.score >= 7 ? 'Neutro' : 'Detrator';
        return '<div style="display:flex;align-items:flex-start;gap:8px;padding:6px 0;border-bottom:1px solid var(--border-2)">'
          + '<div style="width:28px;height:28px;border-radius:6px;background:' + clr + '1a;color:' + clr + ';font-size:12px;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0">' + r.score + '</div>'
          + '<div style="flex:1"><div style="font-size:10px;font-weight:700;color:' + clr + '">' + tipo + '</div>'
          + '<div style="font-size:11px;color:var(--text3)">' + new Date(r.data).toLocaleDateString('pt-BR') + '</div>'
          + (r.comentario ? '<div style="font-size:11px;color:var(--text2);margin-top:1px;font-style:italic">"' + r.comentario + '"</div>' : '') + '</div>'
        + '</div>';
      }).join('') + '</div>';

  return `
    <div class="grid-360">
      <div class="card-360"><div class="c360-label">Segmento</div><div class="c360-value">${c.segmento || '—'}</div></div>
      <div class="card-360"><div class="c360-label">Produto</div><div class="c360-value">${c.produto || '—'}</div></div>
      <div class="card-360"><div class="c360-label">CS Responsável</div><div class="c360-value">${csNome}</div></div>
      <div class="card-360"><div class="c360-label">Consultor Digital</div><div class="c360-value">${consultorNome}</div></div>
    </div>

    <div class="v360-cols">
      <div class="v360-col">

        <div class="card-block" style="margin-bottom:10px">
          <div class="section-title">Ciclo de vida</div>
          <div style="display:flex;gap:24px;flex-wrap:wrap">
            <div>
              <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text4);margin-bottom:3px">Início implantação</div>
              <div style="font-size:13px;font-weight:700;color:var(--text)">${dataImplant}</div>
            </div>
            <div>
              <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text4);margin-bottom:3px">Entrada no CS</div>
              <div style="font-size:13px;font-weight:700;color:var(--primary)">${dataCS}</div>
            </div>
            <div>
              <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text4);margin-bottom:3px">Tempo como cliente</div>
              <div style="font-size:13px;font-weight:700;color:var(--text)">${tempo}</div>
            </div>
          </div>
        </div>

        <div class="card-block">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
            <div class="section-title" style="margin-bottom:0">Contatos</div>
            <button onclick="document.getElementById('ct-form-${c.id}').style.display='block'" style="font-size:11px;font-weight:700;color:var(--primary);background:transparent;border:none;cursor:pointer;padding:0">+ Adicionar</button>
          </div>
          ${contatosHtml}
          <div id="ct-form-${c.id}" style="display:none;background:var(--b-surface);border-radius:8px;padding:12px;margin-top:8px">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px">
              <div><label style="font-size:11px;color:var(--text3);display:block;margin-bottom:4px">Nome *</label><input id="ct-nome-${c.id}" type="text" placeholder="Ex: João Silva" style="width:100%;padding:6px 8px;background:var(--b-bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;box-sizing:border-box"></div>
              <div><label style="font-size:11px;color:var(--text3);display:block;margin-bottom:4px">Cargo</label><input id="ct-cargo-${c.id}" type="text" placeholder="Ex: Gerente de TI" style="width:100%;padding:6px 8px;background:var(--b-bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;box-sizing:border-box"></div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px">
              <div><label style="font-size:11px;color:var(--text3);display:block;margin-bottom:4px">E-mail</label><input id="ct-email-${c.id}" type="email" placeholder="joao@empresa.com" style="width:100%;padding:6px 8px;background:var(--b-bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;box-sizing:border-box"></div>
              <div><label style="font-size:11px;color:var(--text3);display:block;margin-bottom:4px">WhatsApp</label><input id="ct-wpp-${c.id}" type="text" placeholder="(11) 99999-9999" style="width:100%;padding:6px 8px;background:var(--b-bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;box-sizing:border-box"></div>
            </div>
            <div style="display:flex;gap:8px">
              <button onclick="adicionarContato('${c.id}',document.getElementById('ct-nome-${c.id}').value,document.getElementById('ct-cargo-${c.id}').value,document.getElementById('ct-email-${c.id}').value,document.getElementById('ct-wpp-${c.id}').value)" style="flex:1;padding:7px;background:var(--primary);color:#fff;border:none;border-radius:6px;font-size:12px;font-weight:700;cursor:pointer">Salvar contato</button>
              <button onclick="cancelarFormContato('${c.id}')" style="padding:7px 14px;background:transparent;color:var(--text3);border:1px solid var(--border);border-radius:6px;font-size:12px;cursor:pointer">Cancelar</button>
            </div>
          </div>
        </div>

      </div>
      <div class="v360-col">

        <div class="card-block" style="margin-bottom:10px">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
            <div class="section-title" style="margin-bottom:0">CSAT</div>
            ${csatVal !== null ? `<div style="display:flex;align-items:baseline;gap:4px"><span style="font-size:28px;font-weight:800;letter-spacing:-1px;color:${csatClr}">${csatVal}</span><span style="font-size:12px;color:var(--text3)">/5 · ${csatLbl}</span></div>` : ''}
          </div>
          ${csatRespHtml}
          <div id="csat-form-${c.id}" style="display:none;background:var(--b-surface);border-radius:8px;padding:12px;margin-bottom:8px">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px">
              <div><label style="font-size:11px;color:var(--text3);display:block;margin-bottom:4px">Score (1–5)</label><input id="csat-score-${c.id}" type="number" min="1" max="5" step="0.5" style="width:100%;padding:6px 8px;background:var(--b-bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;box-sizing:border-box"></div>
              <div><label style="font-size:11px;color:var(--text3);display:block;margin-bottom:4px">Data</label><input id="csat-data-${c.id}" type="date" style="width:100%;padding:6px 8px;background:var(--b-bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;box-sizing:border-box"></div>
            </div>
            <div style="margin-bottom:10px"><label style="font-size:11px;color:var(--text3);display:block;margin-bottom:4px">Observação (opcional)</label><input id="csat-obs-${c.id}" type="text" placeholder="Ex: cliente satisfeito com onboarding" style="width:100%;padding:6px 8px;background:var(--b-bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;box-sizing:border-box"></div>
            <div style="display:flex;gap:8px">
              <button onclick="registrarCsat('${c.id}',document.getElementById('csat-score-${c.id}').value,document.getElementById('csat-obs-${c.id}').value,document.getElementById('csat-data-${c.id}').value)" style="flex:1;padding:7px;background:var(--primary);color:#fff;border:none;border-radius:6px;font-size:12px;font-weight:700;cursor:pointer">Salvar</button>
              <button onclick="cancelarFormCsat('${c.id}')" style="padding:7px 14px;background:transparent;color:var(--text3);border:1px solid var(--border);border-radius:6px;font-size:12px;cursor:pointer">Cancelar</button>
            </div>
          </div>
          <button onclick="document.getElementById('csat-form-${c.id}').style.display='block';var d=document.getElementById('csat-data-${c.id}');if(d)d.value=new Date().toISOString().slice(0,10)" style="font-size:11px;font-weight:700;color:var(--primary);background:transparent;border:none;cursor:pointer;padding:0">+ Registrar CSAT</button>
        </div>

        <div class="card-block">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
            <div class="section-title" style="margin-bottom:0">NPS</div>
            ${npsVal !== null ? `<div style="display:flex;align-items:baseline;gap:4px"><span style="font-size:28px;font-weight:800;letter-spacing:-1px;color:${npsClr}">${npsVal}</span><span style="font-size:12px;color:var(--text3)">${npsLbl}</span></div>` : ''}
          </div>
          ${npsRespHtml}
          <div id="nps-form-${c.id}" style="display:none;background:var(--b-surface);border-radius:8px;padding:12px;margin-bottom:8px">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px">
              <div><label style="font-size:11px;color:var(--text3);display:block;margin-bottom:4px">Score NPS (0–10)</label><input id="nps-score-${c.id}" type="number" min="0" max="10" style="width:100%;padding:6px 8px;background:var(--b-bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;box-sizing:border-box"></div>
              <div><label style="font-size:11px;color:var(--text3);display:block;margin-bottom:4px">Data</label><input id="nps-data-${c.id}" type="date" style="width:100%;padding:6px 8px;background:var(--b-bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;box-sizing:border-box"></div>
            </div>
            <div style="margin-bottom:10px"><label style="font-size:11px;color:var(--text3);display:block;margin-bottom:4px">Comentário (opcional)</label><input id="nps-com-${c.id}" type="text" placeholder="Ex: indicaria para outros" style="width:100%;padding:6px 8px;background:var(--b-bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;box-sizing:border-box"></div>
            <div style="display:flex;gap:8px">
              <button onclick="registrarNps('${c.id}',document.getElementById('nps-score-${c.id}').value,document.getElementById('nps-com-${c.id}').value,document.getElementById('nps-data-${c.id}').value)" style="flex:1;padding:7px;background:var(--primary);color:#fff;border:none;border-radius:6px;font-size:12px;font-weight:700;cursor:pointer">Salvar</button>
              <button onclick="cancelarFormNps('${c.id}')" style="padding:7px 14px;background:transparent;color:var(--text3);border:1px solid var(--border);border-radius:6px;font-size:12px;cursor:pointer">Cancelar</button>
            </div>
          </div>
          <button onclick="document.getElementById('nps-form-${c.id}').style.display='block';var d=document.getElementById('nps-data-${c.id}');if(d)d.value=new Date().toISOString().slice(0,10)" style="font-size:11px;font-weight:700;color:var(--primary);background:transparent;border:none;cursor:pointer;padding:0">+ Registrar NPS</button>
        </div>

      </div>
    </div>`;
}
```

- [ ] **Step 2: Verificar visualmente**

Abrir o arquivo no Chrome → detalhe de qualquer cliente → clicar em "Visão 360°". Verificar:
- 4 cards no topo: Segmento · Produto · CS Responsável · Consultor Digital (sem "% Implantação")
- 2 colunas abaixo: esquerda com Ciclo de vida + Contatos; direita com CSAT + NPS
- Formulário "+ Adicionar contato" funciona (clique, preenche, salva)
- Formulário "+ Registrar CSAT" funciona
- Formulário "+ Registrar NPS" funciona
- Timeline de histórico de etapas NÃO aparece mais
- Links de e-mail/WhatsApp dos contatos aparecem como chips clicáveis (não emoji)

- [ ] **Step 3: Commit**

```
git add grv-cs-jornada.html
git commit -m "feat(360): 2-col layout, Produto no grid, remove timeline, contatos com chips"
```

---

### Task 4: `renderAbaAtividades()` — alert bar + badge nos playbooks

**Files:**
- Modify: `grv-cs-jornada.html` — função `renderAbaAtividades(c)` (linhas 5762–5914)

**Interfaces:**
- Consumes: nada novo — usa `pb.atividades`, `at.status`, `at.dataLimite` já disponíveis.
- Produces: alert bar consolidada no topo da aba; cada card de playbook com badge de contagem de atrasadas.

- [ ] **Step 1: Adicionar cálculo de atrasadas + hoje no topo da função**

Dentro de `renderAbaAtividades(c)`, logo após `const _hoje = new Date(); _hoje.setHours(0,0,0,0);` (~linha 5764), inserir:

```javascript
  // Contagem consolidada de atrasadas e vencendo hoje
  const _hojStr = new Date().toISOString().slice(0,10);
  var _totalAtrasadas = 0, _totalHoje = 0;
  (c.ativPlaybooks || []).forEach(function(pb) {
    if (pb.status === 'cancelado' || pb.encerrado) return;
    (pb.atividades || []).forEach(function(at) {
      if (at.status === 'concluida') return;
      if (at.status === 'atrasada') _totalAtrasadas++;
      else if (at.dataLimite && at.dataLimite.slice(0,10) === _hojStr) _totalHoje++;
    });
  });
  const _alertBarHtml = (_totalAtrasadas > 0 || _totalHoje > 0)
    ? '<div class="alert-bar">'
        + '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.5" style="flex-shrink:0"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'
        + '<div class="alert-bar-text">'
          + (_totalAtrasadas > 0 ? _totalAtrasadas + ' atividade' + (_totalAtrasadas > 1 ? 's' : '') + ' atrasada' + (_totalAtrasadas > 1 ? 's' : '') : '')
          + (_totalAtrasadas > 0 && _totalHoje > 0 ? '<span class="alert-bar-sub"> · </span>' : '')
          + (_totalHoje > 0 ? '<span class="alert-bar-sub">' + _totalHoje + ' vence' + (_totalHoje > 1 ? 'm' : '') + ' hoje</span>' : '')
        + '</div>'
      + '</div>'
    : '';
```

- [ ] **Step 2: Adicionar badge de atrasadas em cada playbook card**

Dentro do `.map(function(pb) {` que gera `pbCards` (~linhas 5773–5810), localizar a linha que gera o nome do playbook — algo como:

```javascript
`<div class="at-pb-card-name">${pb.nome}...`
```

Adicionar o badge de atrasadas após o nome do playbook. O trecho a modificar tem aproximadamente esta forma:

```javascript
// ANTES (adaptação — leia o código exato antes de editar)
`<div class="at-pb-card-name">${pb.nome}${pb.status === 'pausado' ? ' <span>⏸</span>' : ''}${pb.status === 'cancelado' ? ' <span>✕</span>' : ''}</div>`

// DEPOIS — adicionar badge de atrasadas
```

Após ler o código exato, adicionar após o nome (e antes ou depois do badge de status):

```javascript
// Dentro do map de pbCards, após calcular se é o card selecionado:
var _pbAtrasadas = (pb.atividades || []).filter(function(at){ return at.status === 'atrasada'; }).length;
var _pbAlertBadge = _pbAtrasadas > 0
  ? '<span class="pb-badge-alert">' + _pbAtrasadas + ' atraso</span>'
  : '';
```

E inserir `${_pbAlertBadge}` (ou `'+_pbAlertBadge+'` se for string concat) dentro do elemento `.at-pb-card-name`.

- [ ] **Step 3: Adicionar alert bar no return**

No `return` final da função (~linha 5910), localizar:

```javascript
  return `<div class="at-cols">
    <div class="at-left-col">${leftHtml}</div>
    <div class="at-right-col">${rightHtml}</div>
  </div>`;
```

Substituir por:

```javascript
  return _alertBarHtml + `<div class="at-cols">
    <div class="at-left-col">${leftHtml}</div>
    <div class="at-right-col">${rightHtml}</div>
  </div>`;
```

- [ ] **Step 4: Verificar visualmente**

Abrir o arquivo → detalhe de cliente com atividades atrasadas (ex: João/Priscila do mock) → aba Atividades. Verificar:
- Faixa vermelha suave aparece no topo se houver atrasadas ou vencendo hoje
- Cards de playbook com atrasadas mostram badge "N atraso" em vermelho
- Playbooks sem atrasadas não mostram badge
- A faixa não aparece para clientes sem pendências

- [ ] **Step 5: Commit**

```
git add grv-cs-jornada.html
git commit -m "feat(atividades): alert bar consolidada e badges de atraso nos playbooks"
```

---

### Task 5: `renderAbaNotas()` + `addRegistro()` — tipos de nota

**Files:**
- Modify: `grv-cs-jornada.html` — `renderAbaNotas(c)` (linhas 6507–6524), `addRegistro(clienteId)` (buscar por `function addRegistro`)

**Interfaces:**
- Consumes: `c.registros[]` com campos `{id, autor, data, texto}` — o campo `tipo` é novo e opcional (backward compat: notas sem `tipo` renderizam sem badge).
- Produces: notas com badge de tipo (Observação/Alerta/Decisão), stripe lateral colorida, formulário com select de tipo.

- [ ] **Step 1: Substituir `renderAbaNotas(c)` completa**

Localizar `function renderAbaNotas(c) {` (~linha 6507). Substituir a função inteira (até o `}` de fechamento, ~linha 6524) pelo seguinte:

```javascript
function renderAbaNotas(c) {
  var tipoClasses = { alerta:'tipo-alerta', decisao:'tipo-decisao', observacao:'tipo-observacao' };
  var tipoLabels  = { alerta:'Alerta', decisao:'Decisão', observacao:'Observação' };

  var regsHtml = c.registros && c.registros.length
    ? c.registros.slice().reverse().map(function(r) {
        var t = r.tipo || '';
        var cls = tipoClasses[t] || '';
        var badge = cls
          ? '<span class="nota-tipo nota-tipo-' + t + '">' + (tipoLabels[t] || t) + '</span>'
          : '';
        return '<div class="nota-card ' + cls + '">'
          + '<div class="nota-top">'
            + badge
            + '<div class="nota-meta"><span class="nota-autor">' + r.autor + '</span><span class="nota-data">' + fmtDateTime(r.data) + '</span></div>'
          + '</div>'
          + '<div class="nota-texto">' + r.texto + '</div>'
        + '</div>';
      }).join('')
    : '<div style="color:var(--text3);font-size:13px;padding:16px 0">Nenhuma nota registrada ainda. <a href="#" onclick="document.getElementById(\'nota-form-open-' + c.id + '\').click();return false" style="color:var(--primary);font-weight:600">Adicionar a primeira.</a></div>';

  return '<div style="margin-bottom:16px;display:flex;align-items:center;gap:8px">'
    + '<div style="flex:1;font-size:15px;font-weight:700;color:var(--text)">Notas</div>'
    + '<button id="nota-form-open-' + c.id + '" class="nota-add-btn" onclick="document.getElementById(\'nota-form-wrap-' + c.id + '\').style.display=\'block\';this.style.display=\'none\'">'
      + '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>'
      + ' Nova nota'
    + '</button>'
  + '</div>'
  + '<div id="nota-form-wrap-' + c.id + '" style="display:none;margin-bottom:12px">'
    + '<div class="card-block">'
      + '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">'
        + '<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text4)">Tipo</div>'
        + '<select id="nota-tipo-' + c.id + '" class="nota-tipo-select">'
          + '<option value="observacao">Observação</option>'
          + '<option value="alerta">Alerta</option>'
          + '<option value="decisao">Decisão</option>'
        + '</select>'
      + '</div>'
      + '<textarea id="reg-input-' + c.id + '" placeholder="Escreva sua nota aqui..." style="width:100%;min-height:80px;padding:10px;border:1px solid var(--border);border-radius:var(--radius);font-size:13px;resize:vertical;box-sizing:border-box;font-family:inherit;line-height:1.5"></textarea>'
      + '<div style="display:flex;justify-content:flex-end;gap:8px;margin-top:8px">'
        + '<button onclick="document.getElementById(\'nota-form-wrap-' + c.id + '\').style.display=\'none\';document.getElementById(\'nota-form-open-' + c.id + '\').style.display=\'\'" style="font-size:12px;font-weight:600;color:var(--text3);background:transparent;border:none;padding:6px 10px;cursor:pointer;border-radius:6px">Cancelar</button>'
        + '<button class="btn btn-primary btn-sm" onclick="addRegistro(\'' + c.id + '\')">Salvar nota</button>'
      + '</div>'
    + '</div>'
  + '</div>'
  + '<div id="regs-' + c.id + '">' + regsHtml + '</div>';
}
```

- [ ] **Step 2: Atualizar `addRegistro()` para salvar o tipo**

Buscar `function addRegistro` no arquivo. A função atual deve ler `reg-input-{id}` e salvar o texto. Localizar o objeto de registro que ela constrói — algo como:

```javascript
// Padrão atual (adaptar conforme o código real)
var reg = { id: Date.now(), autor: '...', data: new Date().toISOString(), texto: texto };
```

Modificar para incluir o tipo:

```javascript
// DEPOIS — adicionar tipo
var tipoEl = document.getElementById('nota-tipo-' + clienteId);
var reg = {
  id:    Date.now(),
  autor: /* mesmo que antes */,
  data:  new Date().toISOString(),
  texto: texto,
  tipo:  tipoEl ? tipoEl.value : 'observacao'
};
```

Adapte com os nomes exatos de variáveis encontrados no código real.

- [ ] **Step 3: Verificar visualmente**

Abrir o arquivo → detalhe de cliente → aba Notas. Verificar:
- Notas existentes exibem sem badge de tipo (backward compat — notas antigas sem `r.tipo`)
- Clicar "+ Nova nota" abre o formulário com select de tipo
- Salvar uma nota do tipo "Alerta" → aparece com stripe vermelha e badge "ALERTA"
- Salvar uma nota do tipo "Decisão" → stripe azul e badge "DECISÃO"
- Salvar uma nota do tipo "Observação" → stripe cinza e badge "OBSERVAÇÃO"
- Botão "Cancelar" fecha o formulário sem salvar

- [ ] **Step 4: Commit**

```
git add grv-cs-jornada.html
git commit -m "feat(notas): tipos Observação/Alerta/Decisão com stripe e badge"
```

---

## Pós-implementação

Após as 4 tasks concluídas, verificar o sistema completo:

1. Abrir detalhe de cliente **com** dados completos (healthHistory, csatRespostas, npsRespostas, ativPlaybooks com atrasadas)
2. Verificar KPI strip: 4 células visíveis, valores com cores corretas
3. Navegar para Visão 360 → layout 2 colunas, formulários funcionando
4. Navegar para Atividades → alert bar (se tiver atrasadas), badges nos playbooks
5. Navegar para Notas → adicionar uma de cada tipo, verificar stripe e badge
6. Abrir detalhe de cliente **sem** dados (sem csatRespostas, sem npsRespostas) → KPI strip mostra `—` em vez de crashar

Criar PR da branch `alteracoes` para `main`:

```
gh pr create \
  --title "feat(cliente): redesign abas — header rico, Atividades padrão, Notas tipadas" \
  --body "Redesign completo da tela de detalhe do cliente conforme spec docs/superpowers/specs/2026-07-10-cliente-tabs-redesign.md

## O que muda
- KPI strip permanente no header: Health Score, CSAT, NPS, Próxima ação
- Aba padrão muda de Visão 360 para Atividades
- Badge de atividades atrasadas na tab Atividades
- Visão 360: layout 2 colunas, Produto substitui % Implantação, timeline removida, contatos com chips clicáveis
- Atividades: alert bar consolidada de atrasadas/hoje, badges nos playbooks com atrasos
- Notas: tipos Observação/Alerta/Decisão com stripe lateral e badge, backward-compat com notas sem tipo

## O que não muda
- Lógica de cálculo (calcHealthScore, calcCsatAtual, calcNps)
- Estrutura de dados dos clientes
- Roteamento e hash navigation
- Formulários de CSAT, NPS, Contatos (reposicionados, não reescritos)"
```
