# Vencimentos: Filtros Avançados + Estados de Playbook — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar 4 filtros à tela Vencimentos (busca, urgência, etapa, produto) + link de navegação para o cliente + estados de playbook (pausado/cancelado) com menu `···` no card.

**Architecture:** Single-file SPA (`grv-cs-jornada.html`). Todos os dados em `localStorage` via `getCliente`/`saveCliente`. Re-render completo da seção no lugar de DOM diff. Cinco tarefas independentes e cumulativas; cada uma é testável isoladamente no browser.

**Tech Stack:** HTML/CSS/JS vanilla inline, sem build step. Node.js só para validação de sintaxe JS.

## Global Constraints

- Arquivo único: `grv-cs-jornada.html` — todas as mudanças neste arquivo
- Sem dependências externas, sem build, sem TypeScript
- Padrão de re-render: funções `renderXxx()` reescrevem `innerHTML` da seção inteira
- CSS tokens existentes: `--primary`, `--border`, `--border-2`, `--surface`, `--red`, `--green`, `--text`, `--text2`, `--text3`, `--radius`
- Classes CSS reutilizáveis existentes: `.ov-dropdown`, `.ov-dropdown-item`, `.ov-dropdown-item.danger`, `.ov-dropdown-divider`, `.pb-card-act`, `showConfirm(title, body, okLabel, cb)`
- Validar sintaxe após cada tarefa: `node -e "const fs=require('fs');const h=fs.readFileSync('grv-cs-jornada.html','utf8');const m=h.match(/<script>([\s\S]*?)<\/script>/g);(m||[]).forEach((b,i)=>{try{new Function(b.replace(/<\/?script>/g,''))}catch(e){console.error('Block',i,e.message)}});console.log('OK')"`

---

## Task 1: Data model — pb.status migration + excluir cancelados de getTodasVencidas

**Files:**
- Modify: `grv-cs-jornada.html` (função `migrateLS` ~linha 1613; função `getTodasVencidas` ~linha 2547)

**Interfaces:**
- Produces: `pb.status: 'ativo'|'pausado'|'cancelado'` disponível em todos os playbooks após load; `getTodasVencidas()` retorna lista sem atividades de playbooks cancelados

- [ ] **Step 1: Adicionar `pb.status` na migração**

Dentro de `migrateLS()`, no `forEach` que itera playbooks (procure `(c.ativPlaybooks || []).forEach(function(pb) {`), adicione a linha de migração logo após as outras migrations de playbook (após `if (!pb.fase)...`):

```javascript
if (!pb.status) { pb.status = 'ativo'; dirty = true; }
```

O bloco resultante deve ficar assim:
```javascript
(c.ativPlaybooks || []).forEach(function(pb) {
  if (!pb.id) { pb.id = 'pb_' + Math.random().toString(36).slice(2,9); dirty = true; }
  if (!pb.donoId) { pb.donoId = c.consultorId || c.csId || ''; dirty = true; }
  if (!pb.fase) { pb.fase = c.status === 'cs_ativo' ? 'cs' : 'implantacao'; dirty = true; }
  if (!pb.status) { pb.status = 'ativo'; dirty = true; }   // ← NOVA LINHA
  (pb.atividades || []).forEach(function(at) {
```

- [ ] **Step 2: Excluir playbooks cancelados de getTodasVencidas**

Dentro de `getTodasVencidas()`, no `forEach` que itera playbooks, adicione um guard logo antes do forEach de atividades:

Encontre a linha: `(c.ativPlaybooks || []).forEach(function(pb) {`
Logo após essa linha, adicione:

```javascript
if ((pb.status || 'ativo') === 'cancelado') return;
```

Resultado:
```javascript
(c.ativPlaybooks || []).forEach(function(pb) {
  if ((pb.status || 'ativo') === 'cancelado') return;   // ← NOVA LINHA
  (pb.atividades || []).forEach(function(at) {
```

- [ ] **Step 3: Validar sintaxe**

```
node -e "const fs=require('fs');const h=fs.readFileSync('grv-cs-jornada.html','utf8');const m=h.match(/<script>([\s\S]*?)<\/script>/g);(m||[]).forEach((b,i)=>{try{new Function(b.replace(/<\/?script>/g,''))}catch(e){console.error('Block',i,e.message)}});console.log('OK')"
```
Esperado: `OK`

- [ ] **Step 4: Testar no browser**

Abrir o arquivo. Abrir DevTools → Console → digitar:
```javascript
getTodasVencidas().slice(0,3).map(v => v.pb.status)
```
Esperado: array com `'ativo'` ou `'pausado'` (nunca `'cancelado'` ou `undefined`).

- [ ] **Step 5: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(playbook): adicionar pb.status ao modelo + excluir cancelados de Vencimentos"
```

---

## Task 2: Vencimentos — 4 novos filtros + lógica de filtragem

**Files:**
- Modify: `grv-cs-jornada.html` (globals ~linha 2574; função `renderVencimentos` ~linha 2576)

**Interfaces:**
- Consumes: `_venc_filter_cons` (já existe, linha 2574)
- Produces: globals `_venc_filter_urgency`, `_venc_filter_etapa`, `_venc_filter_produto`, `_venc_filter_busca` acessíveis em `renderVencimentos`

- [ ] **Step 1: Declarar 4 novos globals de filtro**

Após a linha `let _venc_filter_cons = 'todos';` (~linha 2574), adicione:

```javascript
let _venc_filter_urgency = 'todos';
let _venc_filter_etapa   = 'todos';
let _venc_filter_produto = 'todos';
let _venc_filter_busca   = '';
```

- [ ] **Step 2: Substituir a lógica de filtragem em renderVencimentos**

Dentro de `renderVencimentos()`, substitua:

```javascript
const todos   = _venc_filter_cons === 'todos' ? allVenc
    : allVenc.filter(function(v){ return (v.at.responsavelId || v.pb.donoId) === _venc_filter_cons; });
```

Por:

```javascript
let todos = allVenc.slice();
if (_venc_filter_cons !== 'todos')
  todos = todos.filter(function(v){ return (v.at.responsavelId || v.pb.donoId) === _venc_filter_cons; });
if (_venc_filter_urgency === 'critico')  todos = todos.filter(function(v){ return v.diff < -15; });
if (_venc_filter_urgency === 'atrasado') todos = todos.filter(function(v){ return v.diff < 0 && v.diff >= -15; });
if (_venc_filter_urgency === 'hoje')     todos = todos.filter(function(v){ return v.diff === 0; });
if (_venc_filter_etapa !== 'todos')      todos = todos.filter(function(v){ return (v.cliente.status||'em_implantacao') === _venc_filter_etapa; });
if (_venc_filter_produto !== 'todos')    todos = todos.filter(function(v){ return (v.cliente.produto||'') === _venc_filter_produto; });
if (_venc_filter_busca.trim())           todos = todos.filter(function(v){ return v.cliente.id.toLowerCase().includes(_venc_filter_busca.trim().toLowerCase()); });
```

- [ ] **Step 3: Substituir a filterBar por versão com 5 controles**

Dentro de `renderVencimentos()`, substitua a const `filterBar` inteira (da abertura `'<div style="margin-bottom:20px...'` até o `'</div>'` da filterbar) por:

```javascript
const produtosUnicos = allVenc
  .map(function(v){ return v.cliente.produto||''; })
  .filter(function(p,i,a){ return p && a.indexOf(p)===i; })
  .sort();
const prodOpts = '<option value="todos">Todos os produtos</option>' +
  produtosUnicos.map(function(p){
    return '<option value="'+p+'"'+(_venc_filter_produto===p?' selected':'')+'>'+p+'</option>';
  }).join('');

const selStyle = 'padding:7px 10px;border:1px solid var(--border);border-radius:var(--radius);font-size:13px;font-family:inherit;color:var(--text);outline:none;background:var(--surface);cursor:pointer';

const filterBar =
  '<div style="margin-bottom:20px;display:flex;align-items:center;gap:10px;flex-wrap:wrap">' +
  '<input id="venc-busca" type="text" placeholder="Buscar cliente..." value="' + _venc_filter_busca.replace(/"/g,'&quot;') + '" ' +
    'oninput="_venc_filter_busca=this.value;renderVencimentos();setTimeout(function(){var el=document.getElementById(\'venc-busca\');if(el){el.focus();el.setSelectionRange(_venc_filter_busca.length,_venc_filter_busca.length);}},0)" ' +
    'style="padding:7px 10px;border:1px solid var(--border);border-radius:var(--radius);font-size:13px;font-family:inherit;outline:none;min-width:150px">' +
  '<select onchange="_venc_filter_cons=this.value;renderVencimentos()" style="'+selStyle+'">' + consOpts + '</select>' +
  '<select onchange="_venc_filter_urgency=this.value;renderVencimentos()" style="'+selStyle+'">' +
    '<option value="todos"'+(_venc_filter_urgency==='todos'?' selected':'')+'>Todas urgências</option>' +
    '<option value="critico"'+(_venc_filter_urgency==='critico'?' selected':'')+'>⚠ Crítico (&gt;15d)</option>' +
    '<option value="atrasado"'+(_venc_filter_urgency==='atrasado'?' selected':'')+'>Atrasado (1–15d)</option>' +
    '<option value="hoje"'+(_venc_filter_urgency==='hoje'?' selected':'')+'>Vence hoje</option>' +
  '</select>' +
  '<select onchange="_venc_filter_etapa=this.value;renderVencimentos()" style="'+selStyle+'">' +
    '<option value="todos"'+(_venc_filter_etapa==='todos'?' selected':'')+'>Todas etapas</option>' +
    '<option value="em_implantacao"'+(_venc_filter_etapa==='em_implantacao'?' selected':'')+'>Implantação</option>' +
    '<option value="cs_ativo"'+(_venc_filter_etapa==='cs_ativo'?' selected':'')+'>CS Ativo</option>' +
  '</select>' +
  (produtosUnicos.length
    ? '<select onchange="_venc_filter_produto=this.value;renderVencimentos()" style="'+selStyle+'">' + prodOpts + '</select>'
    : '') +
  '<span style="font-size:12px;color:var(--text3)">' + todos.length + ' de ' + allVenc.length + ' vencimento' + (allVenc.length!==1?'s':'') + '</span>' +
  '<button onclick="exportarVencimentosCSV()" class="btn btn-secondary btn-sm" style="margin-left:auto">⬇ Exportar CSV</button>' +
  '</div>';
```

- [ ] **Step 4: Validar sintaxe**

```
node -e "const fs=require('fs');const h=fs.readFileSync('grv-cs-jornada.html','utf8');const m=h.match(/<script>([\s\S]*?)<\/script>/g);(m||[]).forEach((b,i)=>{try{new Function(b.replace(/<\/?script>/g,''))}catch(e){console.error('Block',i,e.message)}});console.log('OK')"
```
Esperado: `OK`

- [ ] **Step 5: Testar no browser**

Navegar para `#vencimentos`. Verificar:
- 5 controles aparecem na filterbar (busca + consultor + urgência + etapa + produto)
- Selecionar "Crítico" no urgência → só linhas críticas
- Digitar letra no busca → lista filtra em tempo real sem perder foco
- Contador "X de Y vencimentos" atualiza

- [ ] **Step 6: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(vencimentos): 4 filtros avançados — busca, urgência, etapa, produto"
```

---

## Task 3: Vencimentos — link de navegação para cliente + badge Pausado

**Files:**
- Modify: `grv-cs-jornada.html` (função interna `mkRow` dentro de `renderVencimentos` ~linha 2606)

**Interfaces:**
- Consumes: `v.clienteId`, `v.pb.status`, `v.pb.nome`, `v.at.nome`, `v.cliente.id`
- Produces: nome do cliente clicável; badge "⏸ Pausado" visível nas linhas de playbooks pausados

- [ ] **Step 1: Atualizar mkRow — nome do cliente como link**

Dentro da função interna `mkRow(v, stripeClr, diasBg, diasClr)` em `renderVencimentos`, encontre a linha que usa `v.cliente.id` para exibir o nome (procure `venc-nome` e `venc-meta`).

Substitua o bloco `.venc-info`:

```javascript
// ANTES (aproximado):
'<div class="venc-info">' +
  '<div class="venc-nome">'+(v.at.nome||'—')+'</div>' +
  '<div class="venc-meta">'+nome+' · '+(v.pb.nome||'Playbook')+' · <b style="color:var(--text2)">'+respNome+'</b></div>' +
'</div>' +
```

Por:

```javascript
const pauseBadge = (v.pb.status === 'pausado')
  ? '<span style="background:#FFF3EE;color:var(--primary);font-size:10px;font-weight:700;padding:1px 6px;border-radius:4px;margin-left:4px">⏸ Pausado</span>'
  : '';
const clienteLink = '<a href="#cliente/' + encodeURIComponent(v.clienteId) + '" ' +
  'onclick="event.stopPropagation()" ' +
  'style="color:var(--primary);font-weight:600;text-decoration:none">' + v.cliente.id + '</a>';

// ...no return da função:
'<div class="venc-info">' +
  '<div class="venc-nome">'+(v.at.nome||'—')+'</div>' +
  '<div class="venc-meta">'+clienteLink+' · '+(v.pb.nome||'Playbook')+pauseBadge+' · <b style="color:var(--text2)">'+respNome+'</b></div>' +
'</div>' +
```

- [ ] **Step 2: Validar sintaxe**

```
node -e "const fs=require('fs');const h=fs.readFileSync('grv-cs-jornada.html','utf8');const m=h.match(/<script>([\s\S]*?)<\/script>/g);(m||[]).forEach((b,i)=>{try{new Function(b.replace(/<\/?script>/g,''))}catch(e){console.error('Block',i,e.message)}});console.log('OK')"
```
Esperado: `OK`

- [ ] **Step 3: Testar no browser**

Em `#vencimentos`:
- Clicar no nome de um cliente na lista → navega para `#cliente/ID`
- Voltar para `#vencimentos` (browser back ou sidebar)
- Se existir playbook pausado: verificar badge laranja "⏸ Pausado" na meta da linha

- [ ] **Step 4: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(vencimentos): link para cliente na linha + badge Pausado"
```

---

## Task 4: Menu ··· no card de playbook + funções de estado

**Files:**
- Modify: `grv-cs-jornada.html` (globals ~linha 3207; função `renderAbaAtividades` ~linha 3385; nova seção de funções antes de `renderAbaAtividades`)

**Interfaces:**
- Consumes: `excluirPlaybook(pbId, clienteId)` (já existe), `renomearPlaybook(pbId, clienteId)` (já existe), `saveCliente(c)`, `renderCliente(cId)`, `showConfirm(title, body, okLabel, cb)`
- Produces: `togglePbMenu(evt, pbId, clienteId)`, `closePbMenu()`, `pausarPlaybook(pbId, clienteId)`, `reativarPlaybook(pbId, clienteId)`, `cancelarPlaybook(pbId, clienteId)`

- [ ] **Step 1: Declarar globals do menu de playbook**

Após a linha `let _pb_sel_id = null;` (~linha 3207), adicione:

```javascript
let _pb_menu_open = false;
let _pb_menu_id   = null;
```

- [ ] **Step 2: Adicionar funções de menu e estado ANTES de renderAbaAtividades**

Insira o bloco abaixo imediatamente antes da linha `function renderAbaAtividades(c) {`:

```javascript
function togglePbMenu(evt, pbId, clienteId) {
  if (evt) evt.stopPropagation();
  const willOpen = !_pb_menu_open || _pb_menu_id !== pbId;
  if (_pb_menu_id && _pb_menu_id !== pbId) {
    const old = document.getElementById('pbmenu-' + _pb_menu_id);
    if (old) old.style.display = 'none';
  }
  _pb_menu_id   = pbId;
  _pb_menu_open = willOpen;
  const dd = document.getElementById('pbmenu-' + pbId);
  if (dd) dd.style.display = willOpen ? 'block' : 'none';
}

function closePbMenu() {
  if (_pb_menu_id) {
    const old = document.getElementById('pbmenu-' + _pb_menu_id);
    if (old) old.style.display = 'none';
  }
  _pb_menu_open = false;
  _pb_menu_id   = null;
}

function pausarPlaybook(pbId, clienteId) {
  closePbMenu();
  const c  = getCliente(clienteId);
  const pb = (c?.ativPlaybooks||[]).find(function(p){ return p.id === pbId; });
  if (!pb) return;
  pb.status = 'pausado';
  saveCliente(c);
  renderCliente(clienteId);
  showToast('Playbook pausado', 2500);
}

function reativarPlaybook(pbId, clienteId) {
  closePbMenu();
  const c  = getCliente(clienteId);
  const pb = (c?.ativPlaybooks||[]).find(function(p){ return p.id === pbId; });
  if (!pb) return;
  pb.status = 'ativo';
  saveCliente(c);
  renderCliente(clienteId);
  showToast('Playbook reativado', 2500);
}

function cancelarPlaybook(pbId, clienteId) {
  closePbMenu();
  showConfirm(
    'Cancelar playbook',
    'O playbook ficará visível no histórico do cliente como leitura. Atividades não aparecerão em Vencimentos.',
    'Cancelar playbook',
    function() {
      const c  = getCliente(clienteId);
      const pb = (c?.ativPlaybooks||[]).find(function(p){ return p.id === pbId; });
      if (!pb) return;
      pb.status = 'cancelado';
      saveCliente(c);
      updateVencBadge();
      renderCliente(clienteId);
      showToast('Playbook cancelado', 2500);
    }
  );
}
```

- [ ] **Step 3: Substituir actBtns em renderAbaAtividades**

Dentro de `renderAbaAtividades`, encontre o bloco `const actBtns = isSel ? ...` (linhas ~3404–3410). Substitua o bloco inteiro por:

```javascript
const pbSt    = pb.status || 'ativo';
const actBtns = isSel
  ? `<div style="position:relative;display:inline-block;flex-shrink:0">
      <button class="pb-card-act" title="Opções" onclick="event.stopPropagation();togglePbMenu(event,'${pb.id}','${c.id}')">···</button>
      <div id="pbmenu-${pb.id}" class="ov-dropdown" style="display:none;min-width:175px">
        <button class="ov-dropdown-item" onclick="closePbMenu();renomearPlaybook('${pb.id}','${c.id}')">✎ Renomear</button>
        ${pbSt === 'ativo'      ? `<button class="ov-dropdown-item" onclick="pausarPlaybook('${pb.id}','${c.id}')">⏸ Pausar</button>` : ''}
        ${pbSt !== 'ativo'     ? `<button class="ov-dropdown-item" onclick="reativarPlaybook('${pb.id}','${c.id}')">▶ Reativar</button>` : ''}
        ${pbSt !== 'cancelado' ? `<button class="ov-dropdown-item" onclick="cancelarPlaybook('${pb.id}','${c.id}')">✕ Cancelar</button>` : ''}
        <div class="ov-dropdown-divider"></div>
        <button class="ov-dropdown-item danger" onclick="closePbMenu();excluirPlaybook('${pb.id}','${c.id}')">🗑 Excluir</button>
      </div>
    </div>` : '';
```

- [ ] **Step 4: Fechar menu ao clicar fora — adicionar em initData ou route**

Procure a função `initData()` ou `route()` onde outros listeners são registrados. Adicione uma chamada única:

```javascript
document.addEventListener('click', closePbMenu);
```

Se já existir um `document.addEventListener('click', closeOvMenu)`, adicione `closePbMenu` na mesma chamada ou logo após:

```javascript
document.addEventListener('click', function() { closeOvMenu(); closePbMenu(); });
```

(Se o listener de `closeOvMenu` já existir como listener separado, apenas adicione uma linha nova `document.addEventListener('click', closePbMenu)` próxima a ela.)

- [ ] **Step 5: Validar sintaxe**

```
node -e "const fs=require('fs');const h=fs.readFileSync('grv-cs-jornada.html','utf8');const m=h.match(/<script>([\s\S]*?)<\/script>/g);(m||[]).forEach((b,i)=>{try{new Function(b.replace(/<\/?script>/g,''))}catch(e){console.error('Block',i,e.message)}});console.log('OK')"
```
Esperado: `OK`

- [ ] **Step 6: Testar no browser**

1. Abrir detalhe de um cliente → aba Atividades
2. Selecionar um playbook → botão `···` aparece no card
3. Clicar `···` → dropdown abre com Renomear / Pausar / Cancelar / Excluir
4. Clicar Pausar → toast "Playbook pausado", dropdown fecha
5. Clicar `···` novamente → menu mostra Reativar (não Pausar)
6. Clicar Cancelar → confirm dialog aparece; confirmar → toast
7. Clicar `···` → menu mostra Reativar
8. Clicar fora do dropdown → fecha

- [ ] **Step 7: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(playbook): menu ··· com estados pausar/cancelar/reativar"
```

---

## Task 5: Visual do card de playbook por estado + read-only quando cancelado

**Files:**
- Modify: `grv-cs-jornada.html` (template do card em `renderAbaAtividades` ~linha 3413; função `openAtividade` ~linha 3750)

**Interfaces:**
- Consumes: `pb.status` (Task 1), `pbSt` definido na Task 4 (mesmo bloco de pbCards)
- Produces: card visual diferenciado; overlay de atividade bloqueado para cancelados; botão +Atividade oculto para cancelados

- [ ] **Step 1: Atualizar o template do card de playbook**

Dentro do map de `pbCards` em `renderAbaAtividades`, encontre o `return` do template do card (começa com `<div class="at-pb-card${isSel?' sel':''}"...>`).

Adicione antes do `return`:

```javascript
const pbStatusBadge = pbSt === 'pausado'
  ? '<span style="font-size:10px;font-weight:700;color:var(--primary);background:#FFF3EE;padding:1px 5px;border-radius:4px;margin-left:4px">⏸</span>'
  : pbSt === 'cancelado'
  ? '<span style="font-size:10px;font-weight:700;color:var(--text3);background:var(--border-2);padding:1px 5px;border-radius:4px;margin-left:4px">✕</span>'
  : '';

const cardBorderStyle = pbSt === 'pausado'
  ? 'border:2px dashed var(--primary)'
  : '';
const cardOpacity = pbSt === 'cancelado' ? 'opacity:0.6' : '';
```

Atualize o `return` do card para incluir esses valores. Substitua:

```javascript
return `<div class="at-pb-card${isSel?' sel':''}" onclick="selecionarPb('${pb.id}','${c.id}')">
  <div style="display:flex;align-items:flex-start;gap:4px;margin-bottom:2px">
    <div class="at-pb-card-name" style="flex:1">${pb.nome}</div>
    ${actBtns}
  </div>
```

Por:

```javascript
return `<div class="at-pb-card${isSel?' sel':''}" onclick="selecionarPb('${pb.id}','${c.id}')" style="${cardBorderStyle};${cardOpacity}">
  <div style="display:flex;align-items:flex-start;gap:4px;margin-bottom:2px">
    <div class="at-pb-card-name" style="flex:1">${pb.nome}${pbStatusBadge}</div>
    ${actBtns}
  </div>
```

- [ ] **Step 2: Ocultar botão +Atividade quando playbook está cancelado**

No painel direito de `renderAbaAtividades`, procure onde o botão "+ Nova Atividade" ou `+ Atividade` é renderizado para o playbook selecionado. Geralmente é uma condicional sobre `_at_form_pb` ou `selPb`.

Envolva a renderização do botão com:

```javascript
${(selPb?.status || 'ativo') !== 'cancelado' ? `
  <!-- HTML atual do botão +Atividade aqui -->
` : ''}
```

Se o painel direito já usa `selPb`, adicione a verificação antes do botão de adicionar atividade.

- [ ] **Step 3: Bloquear abertura do overlay para playbooks cancelados**

No início da função `openAtividade(cId, pbId, atId)` (procure `function openAtividade`), adicione logo após a obtenção de `c` e `pb`:

```javascript
function openAtividade(cId, pbId, atId) {
  const c  = getCliente(cId);
  const pb = (c?.ativPlaybooks||[]).find(function(p){ return p.id === pbId; });
  if ((pb?.status || 'ativo') === 'cancelado') return;   // ← NOVA LINHA
  // ... resto da função
```

- [ ] **Step 4: Validar sintaxe**

```
node -e "const fs=require('fs');const h=fs.readFileSync('grv-cs-jornada.html','utf8');const m=h.match(/<script>([\s\S]*?)<\/script>/g);(m||[]).forEach((b,i)=>{try{new Function(b.replace(/<\/?script>/g,''))}catch(e){console.error('Block',i,e.message)}});console.log('OK')"
```
Esperado: `OK`

- [ ] **Step 5: Testar no browser**

1. Cancelar um playbook (Task 4)
2. Card do playbook cancelado: opacidade 0.6, badge "✕", sem botão +Atividade no painel direito
3. Clicar em atividade do playbook cancelado → overlay NÃO abre
4. Pausar um playbook → card com borda laranja tracejada e badge "⏸"
5. Clicar em atividade do playbook pausado → overlay abre normalmente
6. Navegar para Vencimentos: atividades do cancelado NÃO aparecem; atividades do pausado aparecem com badge "⏸ Pausado"

- [ ] **Step 6: Commit final**

```bash
git add grv-cs-jornada.html
git commit -m "feat(playbook): visual de estado (pausado/cancelado) + read-only no cancelado"
```
