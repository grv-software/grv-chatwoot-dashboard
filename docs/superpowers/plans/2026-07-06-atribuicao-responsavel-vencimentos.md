# Atribuição de Responsável + Vencimentos Pessoal — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar UI para atribuir dono de playbook e responsável por atividade, e corrigir Vencimentos para filtrar por essa cadeia de responsabilidade.

**Architecture:** SPA single-file `grv-cs-jornada.html` com localStorage como banco. Todas as funções são declarações `function` (hoisted). `getConsultorAtivo()` já existe e retorna o perfil ativo do localStorage. `getMinhaCarteira()` já filtra por `pb.donoId`. A mudança é: (1) expor essa atribuição via UI dentro do playbook/atividade e (2) corrigir o filtro de Vencimentos para usar a cadeia `at.responsavelId → pb.donoId → cliente.consultorId`.

**Tech Stack:** HTML/CSS/JS inline, sem build step, localStorage.

## Global Constraints

- Arquivo único: `grv-cs-jornada.html` — todas as alterações vão nele
- Usar `function` declarations no topo de nível (não arrow functions ou `const fn =`) para garantir hoisting
- `saveCliente(c)` + `renderCliente(clienteId)` após qualquer mutação de dados
- Sem dependências externas novas
- Branch: `alteracoes`

---

## Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `grv-cs-jornada.html` | Todas as alterações — 4 blocos independentes descritos abaixo |

Seções do arquivo a tocar (buscar pelo texto âncora):

| Seção | Âncora para localizar |
|---|---|
| Globals Vencimentos | `let _venc_filter_cons    = 'todos';` |
| Helper `getDiasUltimoContato` | `function getDiasUltimoContato` |
| `getTodasVencidas` | `function getTodasVencidas` |
| `renderVencimentos` · filtro | `if (_venc_filter_cons !== 'todos')` |
| `renderVencimentos` · `mkRow` | `function mkRow(v, stripeClr` |
| `renderAbaAtividades` · cabeçalho direito | `const rightHtml =` / `<div class="at-right-hd">` |
| `renderAbaAtividades` · linha de atividade | `return \`<div class="at-row-new"` |
| Export CSV | `function exportarProjetosCSV` |

---

## Task 1 — `resolverResponsavel` + default de Vencimentos

**Files:** Modify `grv-cs-jornada.html`

**Interfaces:**
- Produces: `resolverResponsavel(at, pb, cliente) → string` (consultorId, nunca vazio se cliente tem consultorId)

- [ ] **Step 1: Adicionar `resolverResponsavel` após `getDiasUltimoContato`**

Localizar a função `getDiasUltimoContato` e inserir logo depois:

```javascript
function resolverResponsavel(at, pb, cliente) {
  return (at && at.responsavelId) || (pb && pb.donoId) || (cliente && cliente.consultorId) || '';
}
```

- [ ] **Step 2: Corrigir default de `_venc_filter_cons`**

Localizar a linha:
```javascript
let _venc_filter_cons    = 'todos';
```

Substituir por:
```javascript
let _venc_filter_cons    = getConsultorAtivo();
```

> `getConsultorAtivo()` está declarada antes desta linha (linha ~1637) e retorna `localStorage.getItem(DB.ATIVO) || 'ana-paula'` — sempre tem valor.

- [ ] **Step 3: Verificar no browser**

Abrir `http://localhost:7799/grv-cs-jornada.html` → Vencimentos.  
O filtro de consultor deve abrir já selecionado com o consultor ativo (não "Todos os consultores").  
Se o select mostrar o nome certo: ✅

- [ ] **Step 4: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(vencimentos): filtrar por responsável + default para consultor ativo"
```

---

## Task 2 — Dono do playbook: `setDonoPlaybook` + UI

**Files:** Modify `grv-cs-jornada.html`

**Interfaces:**
- Consumes: `resolverResponsavel` (Task 1), `getConsultorAtivo()`, `getConsultores()`
- Produces: `setDonoPlaybook(clienteId, pbId, consultorId)` — salva `pb.donoId` e re-renderiza

- [ ] **Step 1: Adicionar `setDonoPlaybook`**

Adicionar a função depois de `setResponsavelAtividade` (que adicionaremos na Task 3) ou logo após `cancelarFormContato`:

```javascript
function setDonoPlaybook(clienteId, pbId, consultorId) {
  var c = getCliente(clienteId);
  if (!c) return;
  var pb = (c.ativPlaybooks || []).find(function(p) { return p.id === pbId; });
  if (!pb) return;
  pb.donoId = consultorId;
  saveCliente(c);
  renderCliente(clienteId);
}
```

- [ ] **Step 2: Adicionar chip de dono no cabeçalho da coluna direita**

Localizar em `renderAbaAtividades` o bloco:
```javascript
rightHtml = `
  <div class="at-right-hd">
    <div class="at-right-title">${selPb.nome}</div>
```

Substituir por:
```javascript
const donoAtual = selPb.donoId || c.consultorId || '';
const donoNome  = donoAtual ? (getConsultores().find(function(x){ return x.id === donoAtual; }) || {}).nome || donoAtual : '—';
const donoOpts  = getConsultores().map(function(con) {
  return '<option value="'+con.id+'"'+(con.id===donoAtual?' selected':'')+'>'+con.nome+'</option>';
}).join('');

rightHtml = `
  <div class="at-right-hd">
    <div style="display:flex;align-items:center;gap:8px;flex:1;min-width:0">
      <div class="at-right-title" style="flex:1">${selPb.nome}</div>
      <div style="display:flex;align-items:center;gap:5px;flex-shrink:0">
        <span style="font-size:10px;color:var(--text3);font-weight:600;text-transform:uppercase;letter-spacing:.05em">Dono</span>
        <select onchange="setDonoPlaybook('${c.id}','${selPb.id}',this.value)"
          style="font-size:11px;font-weight:600;padding:3px 6px;background:var(--b-surface);border:1px solid var(--border);border-radius:5px;color:var(--text);cursor:pointer;max-width:130px">
          ${donoOpts}
        </select>
      </div>
    </div>
```

> O restante do bloco `at-right-hd` (botão + Atividade, badge Cancelado, etc.) fica igual.

- [ ] **Step 3: Verificar no browser**

Abrir um cliente → aba Atividades → selecionar um playbook.  
No cabeçalho direito deve aparecer "Dono [Select com o nome atual ▼]".  
Mudar o select → atualiza imediatamente → reabrir a aba confirma que salvou. ✅

- [ ] **Step 4: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(atividades): seletor de dono do playbook no cabeçalho"
```

---

## Task 3 — Responsável por atividade: `setResponsavelAtividade` + chip

**Files:** Modify `grv-cs-jornada.html`

**Interfaces:**
- Consumes: `resolverResponsavel` (Task 1), `getConsultores()`
- Produces: `setResponsavelAtividade(clienteId, pbId, atId, consultorId)` — salva `at.responsavelId` (ou remove se `''`) e re-renderiza

- [ ] **Step 1: Adicionar `setResponsavelAtividade`**

Adicionar logo após `setDonoPlaybook` (Task 2):

```javascript
function setResponsavelAtividade(clienteId, pbId, atId, consultorId) {
  var c = getCliente(clienteId);
  if (!c) return;
  var pb = (c.ativPlaybooks || []).find(function(p) { return p.id === pbId; });
  if (!pb) return;
  var at = (pb.atividades || []).find(function(a) { return a.id === atId; });
  if (!at) return;
  if (consultorId === '') { delete at.responsavelId; }
  else { at.responsavelId = consultorId; }
  saveCliente(c);
  renderCliente(clienteId);
}
```

- [ ] **Step 2: Substituir o span estático de responsável pelo chip interativo**

Localizar dentro de `renderAbaAtividades`, na função de mapeamento de atividades:

```javascript
      ${resp ? '<span class="at-row-resp">'+resp+'</span>' : ''}
```

Esta linha usa `resp = at.responsavelId || selPb.donoId || ''` (já calculado acima).

Substituir por:

```javascript
      ${(() => {
        var respExplicito = at.responsavelId;
        var respHerdado   = selPb.donoId || c.consultorId || '';
        var respId        = respExplicito || respHerdado;
        var respNome      = respId ? ((getConsultores().find(function(x){return x.id===respId;})||{}).nome||respId).split(' ')[0] : '—';
        var isHerdado     = !respExplicito;
        var opts = '<option value="">↩ Herdar do playbook</option>' +
          getConsultores().map(function(con){
            return '<option value="'+con.id+'"'+(con.id===respId&&!isHerdado?' selected':'')+'>'+con.nome+'</option>';
          }).join('');
        var borderStyle = isHerdado
          ? 'border:1px dashed var(--border);color:var(--text3)'
          : 'border:1px solid var(--border);color:var(--text2)';
        return '<select onchange="setResponsavelAtividade(\''+c.id+'\',\''+selPb.id+'\',\''+at.id+'\',this.value)" onclick="event.stopPropagation()" '
          + 'style="font-size:10px;font-weight:600;padding:2px 5px;background:var(--b-surface);'+borderStyle+';border-radius:5px;cursor:pointer;max-width:90px" '
          + 'title="'+(isHerdado?'Herdado do playbook':'Responsável explícito')+'">'
          + opts + '</select>';
      })()}
```

> O `onclick="event.stopPropagation()"` impede que clicar no select abra o overlay da atividade.

- [ ] **Step 3: Verificar no browser**

Abrir cliente → Atividades → selecionar playbook.  
Cada atividade deve mostrar um select de responsável na linha.  
Atividades sem `responsavelId` explícito: borda tracejada, texto mais fraco.  
Mudar o select → salva → reabrir aba confirma. ✅  
Selecionar "↩ Herdar do playbook" → volta para borda tracejada. ✅

- [ ] **Step 4: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(atividades): chip de responsável por atividade com herança visual"
```

---

## Task 4 — Filtro de Vencimentos usa `resolverResponsavel`

**Files:** Modify `grv-cs-jornada.html`

**Interfaces:**
- Consumes: `resolverResponsavel` (Task 1)

- [ ] **Step 1: Corrigir filtro por consultor em `renderVencimentos`**

Localizar dentro de `renderVencimentos`:
```javascript
  if (_venc_filter_cons !== 'todos')
    todos = todos.filter(function(v){ return (v.at.responsavelId || v.pb.donoId) === _venc_filter_cons; });
```

Substituir por:
```javascript
  if (_venc_filter_cons !== 'todos')
    todos = todos.filter(function(v){ return resolverResponsavel(v.at, v.pb, v.cliente) === _venc_filter_cons; });
```

- [ ] **Step 2: Adicionar indicador de herança em `mkRow`**

Localizar dentro de `mkRow`:
```javascript
    const resp        = v.at.responsavelId || v.pb.donoId || '';
    const respNome    = resp ? (getConsultores().find(x=>x.id===resp)?.nome || resp) : '—';
```

Substituir por:
```javascript
    const respExplicito = v.at.responsavelId;
    const resp          = resolverResponsavel(v.at, v.pb, v.cliente);
    const respCon       = getConsultores().find(function(x){ return x.id === resp; });
    const respNome      = respCon ? respCon.nome : (resp || '—');
    const respSufixo    = !respExplicito && v.pb.donoId && v.pb.donoId === resp
      ? ' <span style="font-size:9px;color:var(--text3)">(pb)</span>'
      : !respExplicito && !v.pb.donoId
      ? ' <span style="font-size:9px;color:var(--text3)">(cliente)</span>'
      : '';
```

E localizar onde `respNome` é usado na linha `.venc-meta`:
```javascript
        '<div class="venc-meta">'+clienteLink+' · '+(v.pb.nome||'Playbook')+pauseBadge+' · <b style="color:var(--text2)">'+respNome+'</b></div>' +
```

Substituir por:
```javascript
        '<div class="venc-meta">'+clienteLink+' · '+(v.pb.nome||'Playbook')+pauseBadge+' · <b style="color:var(--text2)">'+respNome+'</b>'+respSufixo+'</div>' +
```

- [ ] **Step 3: Atualizar Export CSV para usar `resolverResponsavel`**

Localizar em `exportarProjetosCSV` (ou `exportarVencimentosCSV` se existir) a linha que escreve o responsável. Buscar por `responsavelId` nessa função e garantir que usa:
```javascript
resolverResponsavel(v.at, v.pb, v.cliente)
```
em vez de `v.at.responsavelId || v.pb.donoId`.

- [ ] **Step 4: Verificar no browser**

Abrir Vencimentos.  
O filtro já abre com o consultor ativo selecionado.  
Linhas devem mostrar o responsável correto — com `(pb)` ou `(cliente)` quando a herança é indireta.  
Mudar filtro para "Todos" → mostra tudo. ✅  
Selecionar outro consultor → filtra pelas atividades atribuídas a ele (não pelo cliente). ✅

- [ ] **Step 5: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(vencimentos): filtro por responsável direto via resolverResponsavel"
```

---

## Self-Review do Plano

**Cobertura do spec:**

| Requisito do spec | Task |
|---|---|
| `resolverResponsavel(at, pb, cliente)` helper | Task 1 |
| Default `_venc_filter_cons` para consultor ativo | Task 1 |
| `setDonoPlaybook` | Task 2 |
| Chip dono no cabeçalho do playbook (direita) | Task 2 |
| `setResponsavelAtividade` | Task 3 |
| Chip responsável em cada linha de atividade | Task 3 |
| Visual herdado vs explícito (borda tracejada) | Task 3 |
| Filtro Vencimentos usa cadeia de responsabilidade | Task 4 |
| Indicador de herança na linha de Vencimentos | Task 4 |
| Export CSV usa `resolverResponsavel` | Task 4 |

**Fora do escopo confirmado:**  
Perfil ativo em Minha Carteira — `getConsultorAtivo()` já existe e já é usado. Sem alteração necessária.
