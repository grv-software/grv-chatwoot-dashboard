# Assistente de Chat Embutido (sem IA externa) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Painel de chat flutuante no GRV SAC Dashboard que entende comando e pergunta em linguagem natural-ish sem nenhuma chamada a modelo de IA, reconhecendo equipe/agente/período/métrica na frase e executando por cima das funções que o dashboard já usa.

**Architecture:** Tudo em `index.html`. Ordem: casca visual com resposta fixa (Task 1) → tabelas de entidade e casamento de padrão puro (Task 2) → montagem de entidades (Task 3) → detecção de ação/intenção (Task 4) → execução de navegar/filtrar (Task 5) → execução de pergunta de métrica (Task 6) → execução de comparar/ranking/fila/resumir (Task 7) → liga tudo no handler de envio + memória de conversa (Task 8) → caderno de perguntas não entendidas + seção em Configurações (Task 9) → validação de aceite contra as 80 perguntas do catálogo (Task 10). Cada task deixa o app funcionando e é commitável sozinha.

**Tech Stack:** HTML/CSS/JS puro, arquivo único `index.html`, branch `alteracoes`.

**Spec:** `docs/superpowers/specs/2026-09-28-assistente-chat-design.md`

## Global Constraints

- Arquivo único: `index.html` — todas as edições aqui. Branch `alteracoes`, nunca `main`.
- **Sem chamada a modelo de IA/API externa em nenhuma hipótese.** Todo "entendimento" é casamento de padrão local.
- **Não existe suíte de testes neste projeto.** Funções puras (sem DOM/API) são testadas com `node --eval` contra um `index.html` com stubs mínimos. Qualquer coisa que toque DOM ou API real é verificada com a skill `verify` do repo (`.claude/skills/verify/SKILL.md`): sobe `dev-server.js`, Chrome headless em porta CDP isolada, token de teste em `localStorage`.
- O proxy de `dev-server.js` aponta para **nxticket.com.br, produção real do cliente**. Só GET. Nunca escrever/alterar dado do Chatwoot.
- Perguntar nunca muda o filtro/período que está selecionado na tela — só um comando explícito de filtro faz isso (spec §2.6).
- Perguntas de comparação reaproveitam a mesma janela de comparação já corrigida nesta sessão (mesmo trecho decorrido do período anterior) — nunca um mês anterior completo contra um período parcial.
- Ambiguidade nunca pausa esperando confirmação — sempre assume o candidato mais específico e diz qual escolheu (spec §2.5).
- Todas as funções novas usam o prefixo `harness` para não colidir com nada existente.
- `getAgentTabRange`/`getAgentMonths` do spec **não** são reaproveitadas: são acopladas ao estado da própria aba Agentes (`_agentTabPeriod`/`_agentCustomRange`), não a um período arbitrário digitado no chat. O harness resolve seu próprio período com `harnessRangeFromMes`/`harnessRangeFromRelativo` (Task 4), cobrindo o mesmo conjunto de casos (mês nomeado, relativo, N meses).
- `agentBadge` do spec (cores de meta) também não é reaproveitada literalmente: as bolhas do chat são texto puro (`textContent`, nunca `innerHTML` — zero superfície de XSS mesmo com nomes vindos do Chatwoot). A meta é comunicada com ✓/✗ inline no próprio texto, não com o badge colorido em HTML. Badge visual pode entrar numa v2 se fizer sentido.

---

### Task 1: Casca visual — painel, botão flutuante, abrir/fechar

**Files:**
- Modify: `index.html` — CSS antes da linha 509 (`</style>`); HTML depois da linha 976 (`<div id="toast">…</div>`); JS no fim do `<script>`, antes de `</script>` (linha 4127)

**Interfaces:**
- Consumes: nada.
- Produces: `#harness-toggle`, `#harness-panel`, `#harness-messages`, `#harness-input`; funções `harnessOpen()`, `harnessClose()`, `harnessAppendMessage(role, text)`, `harnessHandleMessage(text)` (versão mínima, substituída na Task 8); global `_harnessOpen`.

- [ ] **Step 1: CSS do painel e do botão**

Localizar a linha `}` que fecha o bloco `@media (max-width:800px) { ... }` (linha 508), logo antes de `</style>` (linha 509), e inserir depois dela:

```css
/* ── ASSISTENTE (harness) ──────────────────────────────── */
#harness-toggle { position:fixed; right:20px; bottom:20px; width:52px; height:52px; border-radius:50%;
  background:linear-gradient(135deg,var(--accent),#8b5cf6); border:none; cursor:pointer; z-index:500;
  display:flex; align-items:center; justify-content:center; font-size:22px; color:#fff;
  box-shadow:0 4px 16px rgba(0,0,0,.35); transition:transform .15s; }
#harness-toggle:hover { transform:scale(1.06); }
#harness-panel { position:fixed; top:0; right:-420px; width:400px; height:100vh; background:var(--bg2);
  border-left:1px solid var(--border); box-shadow:-8px 0 24px rgba(0,0,0,.3); z-index:499;
  display:flex; flex-direction:column; transition:right .22s ease-out; }
#harness-panel.open { right:0; }
.harness-head { display:flex; align-items:center; justify-content:space-between; padding:14px 16px;
  border-bottom:1px solid var(--border); flex-shrink:0; }
.harness-head-title { font-size:14px; font-weight:700; color:var(--text); }
.harness-close { background:none; border:none; color:var(--text3); font-size:18px; cursor:pointer; }
.harness-close:hover { color:var(--text); }
.harness-body { flex:1; overflow-y:auto; padding:14px 16px; display:flex; flex-direction:column; gap:10px; }
.harness-msg { max-width:85%; padding:9px 12px; border-radius:12px; font-size:13px; line-height:1.45; white-space:pre-wrap; }
.harness-msg.user { align-self:flex-end; background:var(--accent); color:#fff; border-bottom-right-radius:3px; }
.harness-msg.assistant { align-self:flex-start; background:var(--bg3); color:var(--text); border-bottom-left-radius:3px; }
.harness-suggestions { display:flex; flex-wrap:wrap; gap:6px; padding:0 16px 12px; }
.harness-chip { padding:5px 10px; border-radius:14px; border:1px solid var(--border); background:var(--bg3);
  color:var(--text2); font-size:11px; cursor:pointer; }
.harness-chip:hover { border-color:var(--accent); color:var(--accent); }
.harness-foot { display:flex; gap:8px; padding:12px 16px; border-top:1px solid var(--border); flex-shrink:0; }
.harness-input { flex:1; padding:9px 12px; border-radius:8px; border:1px solid var(--border); background:var(--bg3);
  color:var(--text); font-size:13px; outline:none; }
.harness-input:focus { border-color:var(--accent); }
.harness-send { padding:9px 14px; border-radius:8px; border:none; background:var(--accent); color:#fff;
  font-size:13px; font-weight:600; cursor:pointer; }
.harness-send:hover { opacity:.88; }
@media (max-width:480px) { #harness-panel { width:100vw; right:-100vw; } }
```

- [ ] **Step 2: HTML do painel e do botão**

Localizar `<div id="toast" role="alert" aria-live="assertive"></div>` (linha 976) e inserir logo depois:

```html

<!-- ASSISTENTE (harness) -->
<button id="harness-toggle" onclick="harnessOpen()" aria-label="Abrir assistente" title="Assistente">✨</button>
<div id="harness-panel" role="dialog" aria-label="Assistente do dashboard">
  <div class="harness-head">
    <span class="harness-head-title">Assistente</span>
    <button class="harness-close" onclick="harnessClose()" aria-label="Fechar">✕</button>
  </div>
  <div class="harness-body" id="harness-messages"></div>
  <div class="harness-suggestions" id="harness-suggestions"></div>
  <div class="harness-foot">
    <input type="text" class="harness-input" id="harness-input" placeholder="Pergunte algo…"
      onkeydown="if(event.key==='Enter') harnessSend();">
    <button class="harness-send" onclick="harnessSend()">Enviar</button>
  </div>
</div>
```

- [ ] **Step 3: JS de abrir/fechar/enviar (resposta fixa por enquanto)**

Localizar o fim do arquivo — a linha `}).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });` seguida de `</script>` (linha 4127) — e inserir **antes** de `</script>`:

```js

/* ── ASSISTENTE (harness) ──────────────────────────────── */
let _harnessOpen = false;

function harnessOpen() {
  _harnessOpen = true;
  document.getElementById('harness-panel')?.classList.add('open');
  if (!document.getElementById('harness-messages').children.length) {
    harnessAppendMessage('assistant', 'Oi! Pergunte sobre volume, tempo de resposta, resolução, CSAT, ranking, ou peça pra filtrar/navegar. Ex: "Como está a equipe 2 este mês?"');
    harnessRenderSuggestions();
  }
  setTimeout(() => document.getElementById('harness-input')?.focus(), 250);
}

function harnessClose() {
  _harnessOpen = false;
  document.getElementById('harness-panel')?.classList.remove('open');
}

function harnessRenderSuggestions() {
  const el = document.getElementById('harness-suggestions');
  if (!el) return;
  const exemplos = [
    'Como está a equipe 2 este mês?',
    'Quantas conversas estão abertas agora?',
    'Mostra só a equipe 2',
    'Quem atendeu mais esse mês?'
  ];
  el.innerHTML = exemplos.map(ex => `<button class="harness-chip" onclick="harnessSubmit(${JSON.stringify(ex)})">${esc(ex)}</button>`).join('');
}

function harnessAppendMessage(role, text) {
  const el = document.getElementById('harness-messages');
  if (!el) return;
  const bubble = document.createElement('div');
  bubble.className = `harness-msg ${role}`;
  bubble.textContent = text;
  el.appendChild(bubble);
  el.scrollTop = el.scrollHeight;
}

function harnessSend() {
  const input = document.getElementById('harness-input');
  if (!input) return;
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  harnessSubmit(text);
}

function harnessSubmit(text) {
  const sugEl = document.getElementById('harness-suggestions');
  if (sugEl) sugEl.innerHTML = '';
  harnessAppendMessage('user', text);
  harnessHandleMessage(text);
}

/* Handler do envio — versão mínima; a Task 8 substitui o corpo inteiro
   pelo pipeline real de extração/resolução/execução/formatação. */
function harnessHandleMessage(text) {
  harnessAppendMessage('assistant', 'Ainda estou aprendendo a responder isso.');
}
```

- [ ] **Step 4: Verificar sintaxe**

```bash
node -e "const fs=require('fs');const m=fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*)<\/script>/);fs.writeFileSync(process.env.TMP+'/c.js',m[1]);"
node --check "$TMP/c.js" && echo OK
```
Esperado: `OK`.

- [ ] **Step 5: Dirigir e confirmar a casca funciona**

Subir conforme a skill `verify`. Na página:
```js
JSON.stringify({
  fechadoInicialmente: !document.getElementById('harness-panel').classList.contains('open')
})
```
Esperado: `fechadoInicialmente:true`.

Clicar em `#harness-toggle`, esperar 300ms, avaliar:
```js
JSON.stringify({
  aberto: document.getElementById('harness-panel').classList.contains('open'),
  primeiraMsg: document.querySelector('.harness-msg.assistant')?.textContent.slice(0,3),
  sugestoes: document.querySelectorAll('.harness-chip').length
})
```
Esperado: `aberto:true`, `primeiraMsg:"Oi!"`, `sugestoes:4`.

Digitar `oi` no `#harness-input`, disparar Enter (ou chamar `harnessSend()` depois de setar `.value`), esperar 200ms:
```js
JSON.stringify([...document.querySelectorAll('.harness-msg')].map(e=>({classe:e.className, texto:e.textContent})))
```
Esperado: bolha `user` com "oi", bolha `assistant` com "Ainda estou aprendendo a responder isso.".

Tirar um screenshot do painel aberto e olhar — confirma visualmente que desliza da direita, não escurece o resto da tela.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat(harness): casca visual do assistente — painel, botao flutuante, abrir/fechar"
```

---

### Task 2: Normalização e casamento de padrão (funções puras)

**Files:**
- Modify: `index.html` — inserir logo **antes** da função `harnessOpen()` adicionada na Task 1

**Interfaces:**
- Consumes: nada.
- Produces: `harnessNormalize(s)`, `harnessNumeroPorExtenso(s)`, `harnessLongestMatch(normMsg, candidates)`, `harnessAllMatches(normMsg, candidates)` — usadas pela Task 3. `candidates` é sempre `[{key, label, aliases:[string,...]}]`; os matchers retornam `{key, label, matchLen, ambiguous?}` ou `null`/`[]`.

- [ ] **Step 1: Escrever as funções**

Inserir imediatamente antes de `/* ── ASSISTENTE (harness) ──────────────────────────────── */` (o comentário que abre a Task 1, Step 3):

```js
/* ── ASSISTENTE — normalização e casamento de padrão ─────── */
function harnessNormalize(s) {
  return (s || '')
    .toLowerCase()
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function harnessNumeroPorExtenso(s) {
  return s.replace(/\bum\b/g, '1').replace(/\bdois\b/g, '2').replace(/\btres\b/g, '3');
}

/* Maior alias que aparece na mensagem, com desempate alfabético quando
   dois candidatos empatam no mesmo tamanho de alias (nunca pergunta de
   volta — sempre assume o mais específico e sinaliza ambiguidade). */
function harnessLongestMatch(normMsg, candidates) {
  let bestLen = 0;
  let tied = [];
  candidates.forEach(c => {
    (c.aliases || [c.label]).forEach(alias => {
      const a = harnessNormalize(alias);
      if (a && a.length >= 3 && normMsg.includes(a)) {
        if (a.length > bestLen) { bestLen = a.length; tied = [c]; }
        else if (a.length === bestLen && !tied.includes(c)) { tied.push(c); }
      }
    });
  });
  if (!tied.length) return null;
  tied.sort((x, y) => x.label.localeCompare(y.label, 'pt-BR'));
  return { key: tied[0].key, label: tied[0].label, matchLen: bestLen, ambiguous: tied.length > 1 };
}

/* Até 2 candidatos distintos que aparecem na mensagem — usado para
   detectar intenção de comparação (duas equipes ou dois agentes citados). */
function harnessAllMatches(normMsg, candidates) {
  const found = [];
  candidates.forEach(c => {
    (c.aliases || [c.label]).forEach(alias => {
      const a = harnessNormalize(alias);
      if (a && a.length >= 3 && normMsg.includes(a)) {
        const existing = found.find(f => f.key === c.key);
        if (!existing) found.push({ key: c.key, label: c.label, matchLen: a.length });
        else if (a.length > existing.matchLen) existing.matchLen = a.length;
      }
    });
  });
  found.sort((a, b) => b.matchLen - a.matchLen);
  return found.slice(0, 2);
}
```

- [ ] **Step 2: Verificar sintaxe**

```bash
node -e "const fs=require('fs');const m=fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*)<\/script>/);fs.writeFileSync(process.env.TMP+'/c.js',m[1]);"
node --check "$TMP/c.js" && echo OK
```
Esperado: `OK`.

- [ ] **Step 3: Testar as funções puras isoladas, sem subir o app**

**Não** dá pra `eval` o script inteiro desde o início: a primeira linha do `<script>` já chama
`localStorage.getItem(...)`, que não existe no Node. Isolar só o bloco que a Task 2 acabou de
inserir, entre os dois comentários-âncora — nenhuma dependência de DOM/`localStorage` nesse trecho:

```bash
node -e "
const fs=require('fs');
const src=fs.readFileSync('index.html','utf8');
const start = src.indexOf('/* ── ASSISTENTE — normalização e casamento de padrão');
/* O comentário '/* ── ASSISTENTE (harness) ── *\/' aparece 3 vezes no arquivo
   (CSS da Task 1, HTML da Task 1, e este JS) — sem o segundo argumento,
   indexOf pega a primeira ocorrência (a do CSS, que vem ANTES de start) e
   o slice sai vazio. Buscar a partir de start. */
const end   = src.indexOf('/* ── ASSISTENTE (harness) ──────────────────────────────── */', start);
eval(src.slice(start, end));

console.log('normalize:', harnessNormalize('Não Tá Dando Certo, ÊÊÊ'));
console.log('numero:', harnessNumeroPorExtenso(harnessNormalize('equipe dois')));

const cands = [
  { key: 1, label: 'Equipe 1' },
  { key: 2, label: 'Equipe 2' },
  { key: 3, label: 'Guilherme Cabral', aliases: ['Guilherme Cabral', 'Guilherme'] },
  { key: 4, label: 'Guilherme Ribeiro', aliases: ['Guilherme Ribeiro', 'Guilherme'] }
];
console.log('longest exato:', JSON.stringify(harnessLongestMatch(harnessNormalize('mostra a equipe 2'), cands)));
console.log('longest empate (deve ser Guilherme Cabral, alfabetico):', JSON.stringify(harnessLongestMatch(harnessNormalize('como esta o guilherme'), cands)));
console.log('longest especifico (deve ser Guilherme Ribeiro):', JSON.stringify(harnessLongestMatch(harnessNormalize('como esta o guilherme ribeiro'), cands)));
console.log('allMatches duas equipes:', JSON.stringify(harnessAllMatches(harnessNormalize('compara equipe 1 com equipe 2'), cands)));
"
```
Esperado:
- `normalize`: `"nao ta dando certo, eee"`
- `numero`: `"equipe 2"`
- `longest exato`: objeto com `key:2, label:"Equipe 2"`
- `longest empate`: objeto com `key:3, label:"Guilherme Cabral", ambiguous:true`
- `longest especifico`: objeto com `key:4, label:"Guilherme Ribeiro", ambiguous:false`
- `allMatches duas equipes`: array com os dois objetos, `key:1` e `key:2`

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat(harness): normalizacao e casamento de padrao por maior alias"
```

---

### Task 3: Tabelas de entidade e extração

**Files:**
- Modify: `index.html` — inserir logo depois das funções da Task 2, antes de `harnessOpen()`

**Interfaces:**
- Consumes: `harnessNormalize`, `harnessNumeroPorExtenso`, `harnessLongestMatch`, `harnessAllMatches` (Task 2); globais já existentes `_teamMap`, `_agentList`, `SAG_FILTER_ID`.
- Produces: `harnessExtractEntities(rawMessage)` → `{ norm, teams:[], agents:[], mes, periodoRel, metrica, fila, pagina }`. `teams`/`agents` são arrays (0–2 itens, formato `{key,label,matchLen}`); os demais são `{key,label,matchLen,ambiguous}` ou `null`.

- [ ] **Step 1: Escrever as tabelas e os montadores de candidatos**

```js
/* ── ASSISTENTE — tabelas de entidade ─────────────────────── */
const HARNESS_MESES = ['janeiro','fevereiro','marco','abril','maio','junho',
  'julho','agosto','setembro','outubro','novembro','dezembro'];

const HARNESS_PERIODOS_RELATIVOS = [
  { key: 'hoje',       aliases: ['hoje'] },
  { key: 'semana',     aliases: ['essa semana', 'esta semana'] },
  { key: 'mes',        aliases: ['esse mes', 'este mes', 'mes atual', 'mes corrente'] },
  { key: 'mespassado', aliases: ['mes passado', 'mes anterior'] },
  { key: '3m',         aliases: ['3 meses', 'ultimos 3 meses', 'esse trimestre', 'este trimestre', 'trimestre'] },
  { key: '6m',         aliases: ['6 meses', 'ultimos 6 meses', 'semestre'] },
  { key: '12m',        aliases: ['12 meses', 'ultimos 12 meses', 'um ano', 'ultimo ano'] }
].map(p => ({ key: p.key, label: p.key, aliases: p.aliases }));

const HARNESS_METRICAS = Object.entries({
  volume:    ['volume', 'atendimentos', 'conversas', 'chats'],
  resolucao: ['resolvid', 'resolucao', 'taxa de resolucao', 'taxa'],
  tmr:       ['1a resposta', 'primeira resposta', 'tempo de resposta', 'tmr'],
  tma:       ['tempo de atendimento', 'tempo de resolucao', 'tma', 'tempo pra resolver', 'tempo para resolver'],
  csat:      ['csat', 'satisfacao', 'avaliac', 'nota do cliente'],
  score:     ['pontuacao', 'score', 'nota geral'],
  mensagens: ['mensagens por conversa', 'mensagens']
}).map(([key, aliases]) => ({ key, label: key, aliases }));

const HARNESS_FILA = Object.entries({
  abertas:       ['abertas agora', 'em aberto agora', 'conversas abertas'],
  pendentes:     ['pendentes', 'pendente'],
  semresposta:   ['sem resposta', 'nao atendidas', 'sem retorno'],
  naoatribuidas: ['nao atribuida', 'sem atendente', 'sem agente atribuido'],
  online:        ['online agora', 'agentes online', 'quem esta online']
}).map(([key, aliases]) => ({ key, label: key, aliases }));

const HARNESS_PAGINAS = [
  { key: 'painel',        label: 'painel',        aliases: ['painel', 'inicio'] },
  { key: 'agentes',       label: 'agentes',       aliases: ['agentes'] },
  { key: 'graficos',      label: 'graficos',      aliases: ['analise', 'graficos'] },
  { key: 'configuracoes', label: 'configuracoes', aliases: ['configuracoes', 'config'] }
];

function harnessTeamCandidates() {
  const list = Object.values(_teamMap).map(t => ({ key: t.id, label: t.name, aliases: [t.name, t.name.replace(/_/g, ' ')] }));
  list.push({ key: SAG_FILTER_ID, label: 'SAG', aliases: ['sag'] });
  return list;
}

function harnessAgentCandidates() {
  return _agentList.map(a => ({ key: a.id, label: a.name, aliases: [a.name, a.name.split(' ')[0]] }));
}

/* Extrai todas as entidades reconhecíveis de uma mensagem, independente
   de ordem ou frase exata (spec §2.2). */
function harnessExtractEntities(rawMessage) {
  let norm = harnessNormalize(rawMessage);
  norm = harnessNumeroPorExtenso(norm);

  const teams  = harnessAllMatches(norm, harnessTeamCandidates());
  const agents = harnessAllMatches(norm, harnessAgentCandidates());
  const mes    = harnessLongestMatch(norm, HARNESS_MESES.map((nome, idx) => ({ key: idx, label: nome, aliases: [nome] })));
  const periodoRel = harnessLongestMatch(norm, HARNESS_PERIODOS_RELATIVOS);
  const metrica = harnessLongestMatch(norm, HARNESS_METRICAS);
  const fila    = harnessLongestMatch(norm, HARNESS_FILA);
  const pagina  = harnessLongestMatch(norm, HARNESS_PAGINAS);

  return { norm, teams, agents, mes, periodoRel, metrica, fila, pagina };
}
```

- [ ] **Step 2: Verificar sintaxe**

```bash
node -e "const fs=require('fs');const m=fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*)<\/script>/);fs.writeFileSync(process.env.TMP+'/c.js',m[1]);"
node --check "$TMP/c.js" && echo OK
```
Esperado: `OK`.

- [ ] **Step 3: Testar a extração com dados reais, via app rodando**

Subir conforme a skill `verify`, esperar `_teamMap`/`_agentList` carregarem (poll em `_agentList.length>0`), e avaliar:
```js
JSON.stringify(harnessExtractEntities('quantas conversas a equipe 2 teve em agosto'))
```
Esperado: `teams` com 1 item `label` contendo "equipe 2"; `mes.key === 7` (agosto, índice 0-based); `metrica.key === 'volume'`.

```js
JSON.stringify(harnessExtractEntities('compara equipe 1 com equipe 2'))
```
Esperado: `teams` com 2 itens.

```js
JSON.stringify(harnessExtractEntities('quantas conversas estao abertas agora'))
```
Esperado: `fila.key === 'abertas'`.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat(harness): tabelas de entidade e extracao a partir da mensagem"
```

---

### Task 4: Detecção de ação e resolução de intenção

**Files:**
- Modify: `index.html` — inserir logo depois de `harnessExtractEntities` (Task 3), antes de `harnessOpen()`

**Interfaces:**
- Consumes: `harnessExtractEntities` (Task 3); `harnessNormalize`.
- Produces: `harnessDetectAcao(norm)`, `harnessResolvePeriodo(mes, periodoRel)`, `harnessRangeFromMes(monthIdx)`, `harnessRangeFromRelativo(key)`, `harnessPrevWindow(since, until)`, `harnessResolveIntent(entities)` → objeto `{ tipo, ... }` onde `tipo` é um de `'navegar'|'filtrar'|'resumir'|'fila'|'comparar'|'ranking'|'metrica'|'desconhecido'`.

- [ ] **Step 1: Ações e período**

```js
/* ── ASSISTENTE — ação e período ──────────────────────────── */
const HARNESS_ACOES = {
  navegar: ['vai pra', 'va para', 'abre a aba', 'muda pra aba', 'mostra a aba'],
  filtrar: ['mostra so', 'mostra apenas', 'filtra pelo', 'filtra pela', 'filtra por',
            'tira o filtro', 'limpa filtro', 'limpa os filtros', 'volta pra todas', 'remove o filtro'],
  resumir: ['resumo geral', 'resumo', 'como estamos', 'o que mudou']
};

function harnessDetectAcao(norm) {
  for (const [acao, frases] of Object.entries(HARNESS_ACOES)) {
    for (const f of frases) if (norm.includes(harnessNormalize(f))) return acao;
  }
  return 'perguntar';
}

function harnessRangeFromRelativo(key) {
  const now = new Date();
  const until = Math.floor(now.getTime() / 1000);
  if (key === 'hoje') {
    return { since: Math.floor(new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime() / 1000), until };
  }
  if (key === 'semana') {
    const dow = now.getDay(), diffToMon = (dow === 0 ? -6 : 1 - dow);
    const s = new Date(now.getFullYear(), now.getMonth(), now.getDate() + diffToMon);
    return { since: Math.floor(s.getTime() / 1000), until };
  }
  if (key === 'mes') {
    return { since: Math.floor(new Date(now.getFullYear(), now.getMonth(), 1).getTime() / 1000), until };
  }
  if (key === 'mespassado') {
    const s = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const e = new Date(now.getFullYear(), now.getMonth(), 0, 23, 59, 59);
    return { since: Math.floor(s.getTime() / 1000), until: Math.floor(e.getTime() / 1000) };
  }
  const n = key === '3m' ? 3 : key === '6m' ? 6 : 12;
  const s = new Date(now.getFullYear(), now.getMonth() - n + 1, 1);
  return { since: Math.floor(s.getTime() / 1000), until };
}

function harnessRangeFromMes(monthIdx) {
  const now = new Date();
  let year = now.getFullYear();
  if (monthIdx > now.getMonth()) year -= 1;
  const s = new Date(year, monthIdx, 1);
  const e = new Date(year, monthIdx + 1, 0, 23, 59, 59);
  const until = Math.min(e.getTime(), now.getTime());
  return { since: Math.floor(s.getTime() / 1000), until: Math.floor(until / 1000) };
}

/* Mesmo trecho decorrido do período anterior — mesma fórmula já corrigida
   no Painel e na Análise nesta sessão. Nunca comparar mês parcial com mês
   anterior completo. */
function harnessPrevWindow(since, until) {
  const dur = until - since;
  const prevUntil = since - 1;
  return { since: prevUntil - dur, until: prevUntil };
}

function harnessResolvePeriodo(mes, periodoRel) {
  if (mes) return harnessRangeFromMes(mes.key);
  if (periodoRel) return harnessRangeFromRelativo(periodoRel.key);
  return harnessRangeFromRelativo('mes');
}
```

- [ ] **Step 2: Detecção de ranking e `harnessResolveIntent`**

```js
function harnessIsRanking(norm) {
  return /\bquem\b/.test(norm) || /\b(mais|menos|melhor|pior|maior|menor)\b/.test(norm);
}

/* "mais"/"maior" e "menos"/"menor" pedem o valor bruto — não dependem de
   saber se subir é bom ou ruim pra métrica ("menor tempo de resposta" quer
   o valor literalmente menor). "melhor"/"pior" são avaliativos e só fazem
   sentido combinados com a polaridade da métrica, resolvida na execução
   (Task 7). Sem isso, "menor tmr" acabava invertido: tratado como "pior",
   quando na verdade é o melhor resultado possível pra essa métrica. */
function harnessDirecaoRanking(norm) {
  if (/\b(maior|mais)\b/.test(norm)) return { modo: 'magnitude', desc: true };
  if (/\b(menor|menos)\b/.test(norm)) return { modo: 'magnitude', desc: false };
  if (/\bpior\b/.test(norm)) return { modo: 'avaliativo', quer: 'pior' };
  return { modo: 'avaliativo', quer: 'melhor' };
}

function harnessResolveIntent(entities) {
  const { teams, agents, mes, periodoRel, metrica, fila, pagina, norm } = entities;
  const acao = harnessDetectAcao(norm);

  if (acao === 'navegar' && pagina) {
    return { tipo: 'navegar', pagina: pagina.key };
  }

  if (acao === 'filtrar') {
    const limpar = /tira o filtro|limpa filtro|limpa os filtros|volta pra todas|remove o filtro/.test(norm);
    return { tipo: 'filtrar', limpar, equipe: teams[0] || null, agente: agents[0] || null };
  }

  if (fila) return { tipo: 'fila', fila: fila.key };

  if (acao === 'resumir' && !teams.length && !agents.length) {
    return { tipo: 'resumir' };
  }

  const periodo = harnessResolvePeriodo(mes, periodoRel);
  const comparar = /comparad|melhorou|piorou|subiu|caiu|melhor que|pior que/.test(norm);

  if (teams.length === 2) {
    return { tipo: 'comparar', escopo: 'equipe', a: teams[0], b: teams[1], metrica: metrica?.key || 'volume', periodo };
  }
  if (agents.length === 2) {
    return { tipo: 'comparar', escopo: 'agente', a: agents[0], b: agents[1], metrica: metrica?.key || 'volume', periodo };
  }

  /* Sem exigir metrica reconhecida: "quem atendeu mais" não cita nenhuma
     palavra da tabela de métricas (só "atendimentos"/"atendeu" bate, e
     "atendeu" — verbo conjugado — não está na lista de aliases), mas ainda
     assim é claramente uma pergunta de ranking. Sem métrica explícita,
     assume volume — é a leitura mais natural de "quem fez mais". */
  if (!teams.length && !agents.length && harnessIsRanking(norm)) {
    const escopoRanking = /\bequipe\b|\btime\b/.test(norm) ? 'equipe' : 'agente';
    return { tipo: 'ranking', escopo: escopoRanking, metrica: metrica?.key || 'volume', direcao: harnessDirecaoRanking(norm), periodo };
  }

  if (metrica || teams.length || agents.length) {
    return { tipo: 'metrica', metrica: metrica?.key || 'volume', equipe: teams[0] || null, agente: agents[0] || null, periodo, comparar };
  }

  return { tipo: 'desconhecido' };
}
```

- [ ] **Step 3: Verificar sintaxe**

```bash
node -e "const fs=require('fs');const m=fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*)<\/script>/);fs.writeFileSync(process.env.TMP+'/c.js',m[1]);"
node --check "$TMP/c.js" && echo OK
```
Esperado: `OK`.

- [ ] **Step 4: Testar a resolução de intenção com o app rodando**

```js
JSON.stringify(harnessResolveIntent(harnessExtractEntities('mostra so a equipe 2')))
```
Esperado: `{"tipo":"filtrar","limpar":false,"equipe":{...equipe 2...},"agente":null}`

```js
JSON.stringify(harnessResolveIntent(harnessExtractEntities('quantas conversas estao abertas agora')))
```
Esperado: `{"tipo":"fila","fila":"abertas"}`

```js
JSON.stringify(harnessResolveIntent(harnessExtractEntities('compara equipe 1 com equipe 2')))
```
Esperado: `tipo:"comparar"`, `escopo:"equipe"`, `metrica:"volume"` (nenhuma métrica citada, cai no padrão).

```js
JSON.stringify(harnessResolveIntent(harnessExtractEntities('quem atendeu mais esse mes')))
```
Esperado: `{"tipo":"ranking","escopo":"agente","metrica":"volume","direcao":{"modo":"magnitude","desc":true}, ...}` — sem métrica explícita ("atendeu" não está na tabela de aliases, só "atendimentos"), cai no padrão `volume`; "mais" resolve pra `{modo:'magnitude', desc:true}`.

Testar também a distinção entre magnitude e avaliativo:
```js
JSON.stringify(harnessResolveIntent(harnessExtractEntities('quem tem o menor tempo de resposta')).direcao)
```
Esperado: `{"modo":"magnitude","desc":false}` — "menor" pede o valor literalmente menor, não é avaliado como "pior".

```js
JSON.stringify(harnessResolveIntent(harnessExtractEntities('qual agente tem a pior pontuacao')).direcao)
```
Esperado: `{"modo":"avaliativo","quer":"pior"}`.

```js
JSON.stringify(harnessResolveIntent(harnessExtractEntities('bom dia')))
```
Esperado: `{"tipo":"desconhecido"}`

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "feat(harness): deteccao de acao e resolucao de intencao"
```

---

### Task 5: Execução — navegar e filtrar

**Files:**
- Modify: `index.html` — inserir logo depois de `harnessResolveIntent` (Task 4), antes de `harnessOpen()`

**Interfaces:**
- Consumes: `showPage`, `_teamFilter`/`syncInboxBar`/`applyInboxAndRender` (Painel), `_chartTeamFilter`/`syncChartInboxBar`/`fetchChartData` (Análise), `_agentTabFilter`/`updateAgentFilterUI`/`fetchAgentTab` (Agentes), `_agentTabTeamFilter`/`syncAgentTeamUI`/`applyAgentTeamFilter` (Agentes, filtro por equipe), `_agentFilter`/`syncAgentTableHighlight`/`syncAgentChip` (Painel, filtro por agente), `removeAgentFilter`, `clearAgentFilter`, `clearInboxFilter`, `clearChartInboxFilter`.
- Produces: `harnessPaginaAtiva()`, `harnessExecutarNavegar(intent)`, `harnessExecutarFiltrar(intent)` — ambos retornam a string de resposta (texto para a bolha do assistente).

- [ ] **Step 1: Descobrir a página ativa e navegar**

```js
/* ── ASSISTENTE — execução: navegar e filtrar ─────────────── */
const HARNESS_PAGINA_LABEL = { painel: 'Painel', agentes: 'Agentes', graficos: 'Análise', configuracoes: 'Configurações' };

function harnessPaginaAtiva() {
  if (document.getElementById('agentes-page')?.style.display !== 'none') return 'agentes';
  if (document.getElementById('graficos-page')?.style.display !== 'none') return 'graficos';
  if (document.getElementById('config-page')?.style.display !== 'none') return 'configuracoes';
  return 'painel';
}

function harnessExecutarNavegar(intent) {
  showPage(intent.pagina);
  return `Prontinho — abri ${HARNESS_PAGINA_LABEL[intent.pagina]}.`;
}
```

- [ ] **Step 2: Filtrar, por página ativa**

```js
function harnessExecutarFiltrar(intent) {
  const pagina = harnessPaginaAtiva();

  if (intent.limpar) {
    if (pagina === 'painel')   { clearInboxFilter(); removeAgentFilter(); }
    if (pagina === 'graficos') { clearChartInboxFilter(); }
    if (pagina === 'agentes')  { clearAgentFilter(); }
    return 'Filtros limpos.';
  }

  if (intent.agente) {
    if (pagina === 'painel') {
      _agentFilter = { id: intent.agente.key, name: intent.agente.label };
      syncAgentTableHighlight(); syncAgentChip(); applyInboxAndRender();
      return `Filtrando o Painel por ${intent.agente.label}.`;
    }
    if (pagina === 'agentes') {
      _agentTabFilter = new Set([intent.agente.key]);
      updateAgentFilterUI(); _agentPerfData = null; _agentMonthCache = {}; fetchAgentTab();
      return `Filtrando a aba Agentes por ${intent.agente.label}.`;
    }
    return `Esse filtro por agente não existe na aba ${HARNESS_PAGINA_LABEL[pagina]}. Vai pra Painel ou Agentes primeiro.`;
  }

  if (intent.equipe) {
    if (pagina === 'painel') {
      _teamFilter = new Set([intent.equipe.key]);
      syncInboxBar(); applyInboxAndRender();
      return `Filtrando o Painel por ${intent.equipe.label}.`;
    }
    if (pagina === 'graficos') {
      _chartTeamFilter = new Set([intent.equipe.key]);
      syncChartInboxBar(); fetchChartData();
      return `Filtrando a Análise por ${intent.equipe.label}.`;
    }
    if (pagina === 'agentes') {
      _agentTabTeamFilter = new Set([intent.equipe.key]);
      syncAgentTeamUI(); applyAgentTeamFilter();
      return `Filtrando os agentes da equipe ${intent.equipe.label}.`;
    }
    return `Vai pra Painel, Agentes ou Análise pra eu filtrar por equipe.`;
  }

  return 'Me diga qual equipe ou agente você quer filtrar.';
}
```

- [ ] **Step 3: Verificar sintaxe**

```bash
node -e "const fs=require('fs');const m=fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*)<\/script>/);fs.writeFileSync(process.env.TMP+'/c.js',m[1]);"
node --check "$TMP/c.js" && echo OK
```
Esperado: `OK`.

- [ ] **Step 4: Testar de verdade, no app rodando (Painel)**

Garantir que está na página Painel (`showPage('painel')`), depois:
```js
(function(){
  const intent = harnessResolveIntent(harnessExtractEntities('mostra so a equipe 2'));
  const resposta = harnessExecutarFiltrar(intent);
  return JSON.stringify({ resposta, filtroAtivo: _teamFilter ? [..._teamFilter] : null });
})()
```
Esperado: `filtroAtivo` com o id real da "equipe 2" do seu Chatwoot.

```js
(function(){
  const resposta = harnessExecutarFiltrar(harnessResolveIntent(harnessExtractEntities('tira o filtro')));
  return JSON.stringify({ resposta, filtroAtivo: _teamFilter });
})()
```
Esperado: `filtroAtivo:null`.

- [ ] **Step 5: Testar navegar**

```js
(function(){
  const resposta = harnessExecutarNavegar(harnessResolveIntent(harnessExtractEntities('vai pra agentes')));
  return JSON.stringify({ resposta, paginaAtiva: harnessPaginaAtiva() });
})()
```
Esperado: `paginaAtiva:"agentes"`.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat(harness): execucao de navegar e filtrar reaproveitando os setters existentes"
```

---

### Task 6: Execução — perguntas de métrica

A maior task: busca de dado (memória ou API nova) e formatação de resposta pra volume/resolução/TMR/TMA/CSAT/pontuação/mensagens, por conta inteira, equipe ou agente.

**Files:**
- Modify: `index.html` — inserir logo depois da Task 5, antes de `harnessOpen()`

**Interfaces:**
- Consumes: `api`, `cfg`, `aggregateSummaries`, `fetchChartCsat`, `calcAgentScore`, `fmtSec`, `esc`, `_SLA_TMA`/`_SLA_TMR`/`_SLA_FCR`/`_SLA_MSG`, `INBOX_TEAM_MAP`, `SAG_FILTER_ID`, `SAG_INBOX_ID`, `harnessPrevWindow`.
- Produces: `harnessFmtPeriodo(since,until)`, `harnessFmtEscopoNome(intent)`, `harnessTeamMemberIds(equipeId)`, `harnessFetchSummary({equipeId,agenteId,since,until})`, `harnessFetchCsat({equipeId,agenteId,since,until})` → `{total,positivos,pct,media}`, `harnessFmtComparacao(metrica,atual,anterior)`, `harnessResponderMetrica(intent)` (async, retorna string) — usada pela Task 8.

- [ ] **Step 1: Busca de dado — resumo e CSAT por escopo**

```js
/* ── ASSISTENTE — execução: perguntas de métrica ──────────── */
function harnessFmtPeriodo(since, until) {
  const f = ts => new Date(ts * 1000).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: '2-digit' });
  return `${f(since)} a ${f(until)}`;
}

function harnessFmtEscopoNome(intent) {
  if (intent.agente) return intent.agente.label;
  if (intent.equipe) return intent.equipe.label;
  return 'A conta inteira';
}

async function harnessTeamMemberIds(equipeId) {
  if (equipeId === SAG_FILTER_ID) return null;
  const members = await api(`/v1/accounts/${cfg.account}/teams/${equipeId}/team_members`).catch(() => []);
  return Array.isArray(members) ? members.map(m => m.id) : [];
}

async function harnessFetchSummary({ equipeId, agenteId, since, until }) {
  if (agenteId != null) {
    return api(`/v2/accounts/${cfg.account}/reports/summary?type=agent&id=${agenteId}&since=${since}&until=${until}`).catch(() => null);
  }
  if (equipeId != null) {
    if (equipeId === SAG_FILTER_ID) {
      return api(`/v2/accounts/${cfg.account}/reports/summary?type=inbox&id=${SAG_INBOX_ID}&since=${since}&until=${until}`).catch(() => null);
    }
    const inboxIds = Object.entries(INBOX_TEAM_MAP).filter(([, tid]) => Number(tid) === Number(equipeId)).map(([iid]) => Number(iid));
    if (!inboxIds.length) return null;
    const results = await Promise.all(inboxIds.map(id =>
      api(`/v2/accounts/${cfg.account}/reports/summary?type=inbox&id=${id}&since=${since}&until=${until}`).catch(() => null)
    ));
    return aggregateSummaries(results.filter(Boolean));
  }
  return api(`/v2/accounts/${cfg.account}/reports/summary?type=account&since=${since}&until=${until}`).catch(() => null);
}

async function harnessFetchCsat({ equipeId, agenteId, since, until }) {
  const { rows } = await fetchChartCsat(since, until).catch(() => ({ rows: [] }));
  let filtered = rows;
  if (agenteId != null) {
    filtered = rows.filter(r => r.assigned_agent?.id === agenteId);
  } else if (equipeId != null) {
    const ids = await harnessTeamMemberIds(equipeId);
    filtered = ids ? rows.filter(r => ids.includes(r.assigned_agent?.id)) : rows;
  }
  const nums = filtered.map(r => typeof r.rating === 'number' ? r.rating : null).filter(v => v !== null);
  const total = filtered.length;
  const positivos = nums.filter(n => n >= 4).length;
  const media = nums.length ? nums.reduce((a, b) => a + b, 0) / nums.length : null;
  return { total, positivos, pct: total ? Math.round(positivos / total * 100) : null, media };
}
```

- [ ] **Step 2: Comparação e formatação da resposta**

```js
function harnessFmtComparacao(metrica, atual, anterior) {
  const campo = metrica === 'volume' ? 'conversations_count'
    : metrica === 'resolucao' ? 'resolutions_count'
    : metrica === 'tmr' ? 'avg_first_response_time'
    : metrica === 'tma' ? 'avg_resolution_time' : null;
  if (!campo) return '';
  const a = atual[campo], b = anterior[campo];
  if (a == null || b == null || b === 0) return '';
  const pct = Math.round((a - b) / b * 100);
  if (pct === 0) return 'Igual ao período anterior.';
  return `${pct > 0 ? 'Subiu' : 'Caiu'} ${Math.abs(pct)}% em relação ao mesmo trecho do período anterior.`;
}

async function harnessResponderMetrica(intent) {
  const { since, until } = intent.periodo;
  const escopo = { equipeId: intent.equipe?.key, agenteId: intent.agente?.key, since, until };
  const nome = harnessFmtEscopoNome(intent);
  const periodoTxt = harnessFmtPeriodo(since, until);

  if (intent.metrica === 'csat') {
    const csat = await harnessFetchCsat(escopo);
    if (!csat.total) return `${nome} não teve avaliações de CSAT em ${periodoTxt}.`;
    let texto = `${nome} teve ${csat.pct}% de aprovação em ${periodoTxt}, com ${csat.total} avaliaç${csat.total === 1 ? 'ão' : 'ões'}.`;
    if (intent.comparar) {
      const prev = harnessPrevWindow(since, until);
      const csatPrev = await harnessFetchCsat({ ...escopo, since: prev.since, until: prev.until });
      if (csatPrev.total) texto += ` No período anterior era ${csatPrev.pct}%.`;
    }
    return texto;
  }

  if (intent.metrica === 'score') {
    if (!intent.agente) return 'Pontuação é uma métrica por agente — me diga o nome de quem você quer ver.';
    const summary = await harnessFetchSummary(escopo);
    const csat = await harnessFetchCsat(escopo);
    const nota = calcAgentScore(summary, csat.media);
    if (nota == null) return `${nome} não teve atendimentos em ${periodoTxt}.`;
    return `${nome} está com pontuação ${nota}/100 em ${periodoTxt}.`;
  }

  const summary = await harnessFetchSummary(escopo);
  if (!summary || !summary.conversations_count) return `${nome} não teve atendimentos em ${periodoTxt}.`;

  let texto;
  if (intent.metrica === 'volume') {
    texto = `${nome} teve ${summary.conversations_count.toLocaleString('pt-BR')} atendimentos em ${periodoTxt}.`;
  } else if (intent.metrica === 'resolucao') {
    const taxa = Math.round((summary.resolutions_count || 0) / summary.conversations_count * 100);
    texto = `${nome} resolveu ${(summary.resolutions_count || 0).toLocaleString('pt-BR')} atendimentos em ${periodoTxt} — taxa de ${taxa}% (meta: ${_SLA_FCR}%)`
      + (taxa > 100 ? '. Pode passar de 100% porque a API conta como resolvida no período qualquer conversa fechada nessas datas, mesmo se foi aberta antes.' : '.');
  } else if (intent.metrica === 'tmr') {
    const tmrM = summary.avg_first_response_time != null ? summary.avg_first_response_time / 60 : null;
    texto = tmrM == null ? `${nome} não tem tempo de 1ª resposta calculável em ${periodoTxt}.`
      : `${nome} levou em média ${fmtSec(summary.avg_first_response_time)} pra responder em ${periodoTxt} — meta é ${_SLA_TMR}min ${tmrM <= _SLA_TMR ? '✓' : '✗'}.`;
  } else if (intent.metrica === 'tma') {
    const tmaH = summary.avg_resolution_time != null ? summary.avg_resolution_time / 3600 : null;
    texto = tmaH == null ? `${nome} não tem tempo de resolução calculável em ${periodoTxt}.`
      : `${nome} levou em média ${fmtSec(summary.avg_resolution_time)} pra resolver em ${periodoTxt} — meta é ${_SLA_TMA}hr ${tmaH <= _SLA_TMA ? '✓' : '✗'}.`;
  } else {
    const totalMsgs = (summary.incoming_messages_count || 0) + (summary.outgoing_messages_count || 0);
    const media = +(totalMsgs / summary.conversations_count).toFixed(1);
    texto = `${nome} teve em média ${media.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} mensagens por conversa em ${periodoTxt} — meta é até ${_SLA_MSG}.`;
  }

  if (intent.comparar) {
    const prev = harnessPrevWindow(since, until);
    const summaryPrev = await harnessFetchSummary({ ...escopo, since: prev.since, until: prev.until });
    if (summaryPrev && summaryPrev.conversations_count) {
      const cmp = harnessFmtComparacao(intent.metrica, summary, summaryPrev);
      if (cmp) texto += ` ${cmp}`;
    }
  }
  return texto;
}
```

- [ ] **Step 3: Verificar sintaxe**

```bash
node -e "const fs=require('fs');const m=fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*)<\/script>/);fs.writeFileSync(process.env.TMP+'/c.js',m[1]);"
node --check "$TMP/c.js" && echo OK
```
Esperado: `OK`.

- [ ] **Step 4: Conferir contra a API real (skill `verify`)**

Buscar em paralelo, de dentro da própria página, o número esperado direto da API, e comparar com o que `harnessResponderMetrica` devolve — mesmo padrão de auditoria já usado nesta sessão:

```js
(async () => {
  const intent = harnessResolveIntent(harnessExtractEntities('quantos atendimentos a equipe 2 teve nos ultimos 3 meses'));
  const resposta = await harnessResponderMetrica(intent);
  const since = intent.periodo.since, until = intent.periodo.until;
  const inboxIds = Object.entries(INBOX_TEAM_MAP).filter(([,tid]) => Number(tid) === Number(intent.equipe.key)).map(([iid]) => Number(iid));
  const somaReal = (await Promise.all(inboxIds.map(id =>
    fetch(`/api/v2/accounts/${cfg.account}/reports/summary?type=inbox&id=${id}&since=${since}&until=${until}`, { headers: { api_access_token: cfg.token } }).then(r=>r.json())
  ))).reduce((s,r)=>s+(r.conversations_count||0),0);
  return JSON.stringify({ resposta, somaReal });
})()
```
Esperado: o número citado em `resposta` bate exatamente com `somaReal`.

Repetir o mesmo padrão de conferência para uma pergunta de CSAT e uma de agente:
```js
(async () => {
  const intent = harnessResolveIntent(harnessExtractEntities('qual a satisfacao do cliente esse mes'));
  const resposta = await harnessResponderMetrica(intent);
  return JSON.stringify({ resposta });
})()
```
Esperado: frase citando `%` de aprovação e contagem de avaliações, nenhuma exceção.

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "feat(harness): execucao de perguntas de metrica — volume, resolucao, tmr, tma, csat, pontuacao"
```

---

### Task 7: Execução — comparar, ranking, fila ao vivo, resumir

**Files:**
- Modify: `index.html` — inserir logo depois da Task 6, antes de `harnessOpen()`

**Interfaces:**
- Consumes: `harnessFetchSummary`, `harnessFmtPeriodo`, `harnessPrevWindow`, `calcAgentScore`, `_agentList`, `_teamMap`, `api`, `cfg`, `_chartData`, `_agentPerfData`, `document.getElementById`.
- Produces: `harnessResponderComparar(intent)`, `harnessResponderRanking(intent)`, `harnessExecutarFila(intent)`, `harnessResponderResumir()` — todas async, retornam string.

- [ ] **Step 1: Comparar**

```js
/* ── ASSISTENTE — execução: comparar, ranking, fila, resumo ── */
function harnessValorPorMetrica(metrica, s) {
  if (!s) return null;
  if (metrica === 'volume')    return s.conversations_count || 0;
  if (metrica === 'resolucao') return s.conversations_count > 0 ? Math.round((s.resolutions_count || 0) / s.conversations_count * 100) : null;
  if (metrica === 'tmr')       return s.avg_first_response_time != null ? Math.round(s.avg_first_response_time / 60) : null;
  if (metrica === 'tma')       return s.avg_resolution_time != null ? +(s.avg_resolution_time / 3600).toFixed(1) : null;
  if (metrica === 'mensagens') return s.conversations_count > 0 ? +(((s.incoming_messages_count || 0) + (s.outgoing_messages_count || 0)) / s.conversations_count).toFixed(1) : null;
  return s.conversations_count || 0;
}

function harnessUnidadeMetrica(metrica) {
  return metrica === 'resolucao' ? '%' : metrica === 'csat' ? '%' : metrica === 'tmr' ? 'min' : metrica === 'tma' ? 'hr' : '';
}

async function harnessResponderComparar(intent) {
  const { since, until } = intent.periodo;
  const campo = intent.escopo === 'equipe' ? 'equipeId' : 'agenteId';
  const [sa, sb] = await Promise.all([
    harnessFetchSummary({ [campo]: intent.a.key, since, until }),
    harnessFetchSummary({ [campo]: intent.b.key, since, until })
  ]);
  const va = harnessValorPorMetrica(intent.metrica, sa);
  const vb = harnessValorPorMetrica(intent.metrica, sb);
  const unidade = harnessUnidadeMetrica(intent.metrica);
  return `Em ${harnessFmtPeriodo(since, until)}: ${intent.a.label} = ${va ?? '—'}${unidade}, ${intent.b.label} = ${vb ?? '—'}${unidade}.`;
}
```

- [ ] **Step 2: Ranking**

```js
/* Valor de um agente pra ranking. 'score' e 'csat' não vêm do
   reports/summary — precisam de uma busca de CSAT à parte, igual à
   Task 6. Ranking por CSAT usa o % de aprovação (não a contagem bruta
   de avaliações — "quem recebeu mais avaliações" vs "quem tem a melhor
   nota" colapsam na mesma métrica nesta v1; distinguir contagem de
   qualidade fica pra uma iteração futura). */
async function harnessValorRankingAgente(intent, agenteId) {
  const { since, until } = intent.periodo;
  if (intent.metrica === 'score') {
    const s = await harnessFetchSummary({ agenteId, since, until });
    if (!s || !s.conversations_count) return null;
    const csat = await harnessFetchCsat({ agenteId, since, until });
    return calcAgentScore(s, csat.media);
  }
  if (intent.metrica === 'csat') {
    const csat = await harnessFetchCsat({ agenteId, since, until });
    return csat.total ? csat.pct : null;
  }
  const s = await harnessFetchSummary({ agenteId, since, until });
  if (!s || !s.conversations_count) return null;
  return harnessValorPorMetrica(intent.metrica, s);
}

async function harnessResponderRanking(intent) {
  const { since, until } = intent.periodo;
  const periodoTxt = harnessFmtPeriodo(since, until);
  let resultados;

  if (intent.escopo === 'agente') {
    if (!_agentList.length) {
      const agents = await api(`/v1/accounts/${cfg.account}/agents`).catch(() => []);
      if (Array.isArray(agents)) _agentList = agents;
    }
    resultados = await Promise.all(_agentList.map(async a => {
      const valor = await harnessValorRankingAgente(intent, a.id);
      return valor == null ? null : { nome: a.name, valor };
    }));
  } else {
    /* Equipe não tem CSAT nem pontuação individual calculável aqui —
       cai pra volume, que é o que faz sentido comparar entre equipes
       quando a métrica pedida foi score/csat. */
    const metricaEquipe = (intent.metrica === 'score' || intent.metrica === 'csat') ? 'volume' : intent.metrica;
    resultados = await Promise.all(harnessTeamCandidates().map(async t => {
      const s = await harnessFetchSummary({ equipeId: t.key, since, until });
      if (!s || !s.conversations_count) return null;
      const valor = harnessValorPorMetrica(metricaEquipe, s);
      return valor == null ? null : { nome: t.label, valor };
    }));
  }

  const validos = resultados.filter(Boolean);
  if (!validos.length) return `Não encontrei dados suficientes em ${periodoTxt}.`;

  /* "mais"/"maior"/"menos"/"menor" pedem o valor bruto, direto — não
     olham pra polaridade da métrica. "melhor"/"pior" são avaliativos:
     pra métrica onde menor é melhor (tmr/tma/mensagens), "melhor" tem
     que ordenar ascendente, não descendente. */
  const lowerIsBetter = intent.metrica === 'tmr' || intent.metrica === 'tma' || intent.metrica === 'mensagens';
  let ordenarAsc;
  if (intent.direcao.modo === 'magnitude') {
    ordenarAsc = !intent.direcao.desc;
  } else {
    const querMelhor = intent.direcao.quer === 'melhor';
    ordenarAsc = lowerIsBetter ? querMelhor : !querMelhor;
  }
  validos.sort((a, b) => ordenarAsc ? a.valor - b.valor : b.valor - a.valor);

  const top = validos[0];
  const unidade = harnessUnidadeMetrica(intent.metrica);
  const valorFmt = Number.isInteger(top.valor) ? top.valor : top.valor.toFixed(1);
  return `${top.nome} lidera em ${periodoTxt}: ${valorFmt}${unidade}.`;
}
```

- [ ] **Step 3: Fila ao vivo e resumo**

```js
async function harnessExecutarFila(intent) {
  if (intent.fila === 'online') {
    if (!_agentList.length) {
      const agents = await api(`/v1/accounts/${cfg.account}/agents`).catch(() => []);
      if (Array.isArray(agents)) _agentList = agents;
    }
    const online = _agentList.filter(a => a.availability_status === 'online').length;
    return `${online} de ${_agentList.length} agentes estão online agora.`;
  }
  const r = await api(`/v2/accounts/${cfg.account}/reports/conversations?type=account`).catch(() => null);
  if (!r) return 'Não consegui buscar o estado da fila agora.';
  const label = { abertas: 'abertas', pendentes: 'pendentes', semresposta: 'sem nenhuma resposta', naoatribuidas: 'sem atendente atribuído' }[intent.fila];
  const valor = { abertas: r.open, pendentes: r.pending, semresposta: r.unattended, naoatribuidas: r.unassigned }[intent.fila];
  if (valor == null) return 'Não encontrei esse dado ao vivo agora.';
  return `Tem ${valor} conversa${valor === 1 ? '' : 's'} ${label} agora.`;
}

function harnessResponderResumir() {
  const pagina = harnessPaginaAtiva();
  if (pagina === 'graficos' && _chartData.length) {
    const d = _chartData[_chartData.length - 1];
    return `No período atual da Análise: ${(d.conversations_count || 0).toLocaleString('pt-BR')} atendimentos, `
      + `${(d.resolutions_count || 0).toLocaleString('pt-BR')} resolvidos, 1ª resposta em ${fmtSec(d.avg_first_response_time)}.`;
  }
  if (pagina === 'agentes' && _agentPerfData && !_agentPerfData._authError) {
    const entradas = Object.values(_agentPerfData).filter(e => e.agent && e.summary?.conversations_count);
    return `${entradas.length} agentes com atendimento no período selecionado da aba Agentes.`;
  }
  return 'Abra o Painel, Agentes ou Análise pra eu resumir o que está na tela.';
}
```

- [ ] **Step 4: Verificar sintaxe**

```bash
node -e "const fs=require('fs');const m=fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*)<\/script>/);fs.writeFileSync(process.env.TMP+'/c.js',m[1]);"
node --check "$TMP/c.js" && echo OK
```
Esperado: `OK`.

- [ ] **Step 5: Conferir contra a API real (skill `verify`)**

```js
(async () => {
  const respostaFila = await harnessExecutarFila(harnessResolveIntent(harnessExtractEntities('quantas conversas estao abertas agora')));
  const real = await fetch(`/api/v2/accounts/${cfg.account}/reports/conversations?type=account`, { headers: { api_access_token: cfg.token } }).then(r=>r.json());
  return JSON.stringify({ respostaFila, real });
})()
```
Esperado: o número em `respostaFila` bate com `real.open`.

```js
(async () => {
  const resposta = await harnessResponderRanking(harnessResolveIntent(harnessExtractEntities('quem atendeu mais esse mes')));
  return resposta;
})()
```
Esperado: frase citando um nome real de agente e um número, sem exceção (pode demorar alguns segundos — 63 chamadas paralelas).

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat(harness): execucao de comparar, ranking, fila ao vivo e resumo"
```

---

### Task 8: Liga tudo — handler real de envio e memória de conversa

Substitui a resposta fixa da Task 1 pelo pipeline completo, e acrescenta a memória de última equipe/agente/período citado.

**Files:**
- Modify: `index.html` — substituir o corpo de `harnessHandleMessage` (Task 1); inserir `_harnessMemory` junto às demais globais do harness

**Interfaces:**
- Consumes: `harnessExtractEntities`, `harnessResolveIntent`, `harnessExecutarNavegar`, `harnessExecutarFiltrar`, `harnessResponderMetrica`, `harnessResponderComparar`, `harnessResponderRanking`, `harnessExecutarFila`, `harnessResponderResumir`, `harnessAppendMessage`.
- Produces: `harnessHandleMessage(text)` (versão final), `_harnessMemory`.

- [ ] **Step 1: Memória de conversa e substituição do handler**

Localizar `let _harnessOpen = false;` (Task 1) e inserir logo depois:
```js
let _harnessMemory = { equipeId: null, agenteId: null, periodo: null };
```

Substituir o corpo inteiro de `harnessHandleMessage` (Task 1):
```js
function harnessHandleMessage(text) {
  harnessAppendMessage('assistant', 'Ainda estou aprendendo a responder isso.');
}
```
por:
```js
async function harnessHandleMessage(text) {
  const entities = harnessExtractEntities(text);
  let intent = harnessResolveIntent(entities);

  /* preenche com a memória da conversa quando a frase não citou a entidade */
  if (intent.tipo === 'metrica') {
    if (!intent.equipe && !intent.agente) {
      if (_harnessMemory.agenteId != null) intent.agente = { key: _harnessMemory.agenteId, label: _harnessMemory.agenteLabel };
      else if (_harnessMemory.equipeId != null) intent.equipe = { key: _harnessMemory.equipeId, label: _harnessMemory.equipeLabel };
    }
    _harnessMemory.equipeId = intent.equipe?.key ?? null;
    _harnessMemory.equipeLabel = intent.equipe?.label ?? null;
    _harnessMemory.agenteId = intent.agente?.key ?? null;
    _harnessMemory.agenteLabel = intent.agente?.label ?? null;
  }

  let resposta;
  try {
    if (intent.tipo === 'navegar')  resposta = harnessExecutarNavegar(intent);
    else if (intent.tipo === 'filtrar')  resposta = harnessExecutarFiltrar(intent);
    else if (intent.tipo === 'fila')     resposta = await harnessExecutarFila(intent);
    else if (intent.tipo === 'comparar') resposta = await harnessResponderComparar(intent);
    else if (intent.tipo === 'ranking')  resposta = await harnessResponderRanking(intent);
    else if (intent.tipo === 'resumir')  resposta = harnessResponderResumir();
    else if (intent.tipo === 'metrica')  resposta = await harnessResponderMetrica(intent);
    else {
      logUnmatchedQuestion(text);
      resposta = 'Não reconheci essa pergunta. Posso responder sobre volume, tempo de resposta, resolução, CSAT, ranking, comparar equipes/agentes, fila ao vivo, ou filtrar/navegar. Tenta reformular citando uma equipe, agente, período ou métrica.';
    }
  } catch (e) {
    console.error('harness:', e);
    resposta = 'Deu um erro buscando esse dado. Tenta de novo em alguns segundos.';
  }
  harnessAppendMessage('assistant', resposta);
}
```

Nota: `logUnmatchedQuestion` é definida na Task 9 — esta task fica com uma referência à frente (ok em JS, `function` é hoisted e a chamada só ocorre em runtime, depois de todo o script já ter carregado).

- [ ] **Step 2: Verificar sintaxe**

```bash
node -e "const fs=require('fs');const m=fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*)<\/script>/);fs.writeFileSync(process.env.TMP+'/c.js',m[1]);"
node --check "$TMP/c.js" && echo OK
```
Esperado: `OK` — mesmo `logUnmatchedQuestion` ainda não existindo, `node --check` só valida sintaxe, não resolve referências.

- [ ] **Step 3: Testar a conversa de 2 turnos (memória) via skill `verify`**

Abrir o painel, mandar duas mensagens em sequência pela UI de verdade (`harnessSubmit(...)`), esperar cada resposta:
```js
(async () => {
  harnessSubmit('quantas conversas a equipe 2 teve em agosto');
  await new Promise(r => setTimeout(r, 4000));
  const r1 = document.querySelectorAll('.harness-msg.assistant');
  const primeira = r1[r1.length - 1].textContent;

  harnessSubmit('e em setembro?');
  await new Promise(r => setTimeout(r, 4000));
  const r2 = document.querySelectorAll('.harness-msg.assistant');
  const segunda = r2[r2.length - 1].textContent;

  return JSON.stringify({ primeira, segunda });
})()
```
Esperado: `segunda` cita "equipe 2" mesmo sem o nome ter sido repetido na segunda mensagem, com números de setembro (mês diferente de agosto).

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat(harness): liga extracao-resolucao-execucao-resposta e memoria de conversa"
```

---

### Task 9: Caderno de perguntas não entendidas

**Files:**
- Modify: `index.html` — JS logo depois da Task 8; HTML dentro de `#config-page`, antes do comentário `<!-- Ações -->`

**Interfaces:**
- Consumes: `localStorage`, `esc`.
- Produces: `logUnmatchedQuestion(text)`, `renderHarnessUnmatchedList()` — chamada por `loadConfigPage()` (Task existente) e por um botão "Limpar" novo.

- [ ] **Step 1: Log em localStorage**

```js
/* ── ASSISTENTE — caderno de perguntas não entendidas ─────── */
const HARNESS_UNMATCHED_KEY = 'grv_harness_unmatched';
const HARNESS_UNMATCHED_MAX = 200;

function logUnmatchedQuestion(text) {
  const norm = harnessNormalize(text);
  if (!norm) return;
  let lista = [];
  try { lista = JSON.parse(localStorage.getItem(HARNESS_UNMATCHED_KEY) || '[]'); } catch { lista = []; }
  const existente = lista.find(e => e.texto === norm);
  if (existente) {
    existente.contagem++;
    existente.ultimaVez = Date.now();
  } else {
    lista.push({ texto: norm, original: text, contagem: 1, ultimaVez: Date.now() });
  }
  lista.sort((a, b) => b.ultimaVez - a.ultimaVez);
  if (lista.length > HARNESS_UNMATCHED_MAX) lista = lista.slice(0, HARNESS_UNMATCHED_MAX);
  localStorage.setItem(HARNESS_UNMATCHED_KEY, JSON.stringify(lista));
  renderHarnessUnmatchedList();
}

function clearHarnessUnmatched() {
  localStorage.removeItem(HARNESS_UNMATCHED_KEY);
  renderHarnessUnmatchedList();
}

function renderHarnessUnmatchedList() {
  const el = document.getElementById('harness-unmatched-list');
  if (!el) return;
  let lista = [];
  try { lista = JSON.parse(localStorage.getItem(HARNESS_UNMATCHED_KEY) || '[]'); } catch { lista = []; }
  if (!lista.length) {
    el.innerHTML = '<p style="font-size:12px;color:var(--text3)">Nenhuma pergunta não reconhecida até agora.</p>';
    return;
  }
  lista.sort((a, b) => b.contagem - a.contagem);
  el.innerHTML = `<table class="agent-table"><thead><tr><th>Pergunta</th><th>Vezes</th></tr></thead><tbody>`
    + lista.map(e => `<tr><td>${esc(e.original)}</td><td>${e.contagem}</td></tr>`).join('')
    + `</tbody></table>`;
}
```

- [ ] **Step 2: Seção nova em Configurações**

Localizar, dentro de `#config-page`, o comentário:
```html
    <!-- Ações -->
```
e inserir **antes** dele:
```html
    <!-- Assistente -->
    <div class="config-card">
      <h3>Perguntas que o assistente não soube responder</h3>
      <p style="font-size:12px;color:var(--text2);margin-bottom:12px">Guardado só neste navegador. Use pra saber o que ensinar ao assistente depois.</p>
      <div id="harness-unmatched-list"></div>
      <button onclick="clearHarnessUnmatched()" style="margin-top:8px;padding:6px 14px;border:1px solid var(--border);border-radius:5px;background:var(--bg2);color:var(--text3);cursor:pointer;font-size:12px">Limpar</button>
    </div>

```

- [ ] **Step 3: Chamar o render ao abrir Configurações**

Localizar, em `showPage(page)`:
```js
  if (page === 'configuracoes') { loadConfigPage(); renderGruposList(); }
```
e substituir por:
```js
  if (page === 'configuracoes') { loadConfigPage(); renderGruposList(); renderHarnessUnmatchedList(); }
```

- [ ] **Step 4: Verificar sintaxe**

```bash
node -e "const fs=require('fs');const m=fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*)<\/script>/);fs.writeFileSync(process.env.TMP+'/c.js',m[1]);"
node --check "$TMP/c.js" && echo OK
```
Esperado: `OK`.

- [ ] **Step 5: Testar via skill `verify`**

```js
(async () => {
  harnessSubmit('blablabla isso nao existe');
  await new Promise(r => setTimeout(r, 500));
  showPage('configuracoes');
  await new Promise(r => setTimeout(r, 200));
  return JSON.stringify({
    linhaNaTabela: document.getElementById('harness-unmatched-list').textContent.includes('blablabla'),
    localStorage: JSON.parse(localStorage.getItem('grv_harness_unmatched'))
  });
})()
```
Esperado: `linhaNaTabela:true`, `localStorage` com um item `contagem:1`.

Enviar a mesma frase de novo e conferir que `contagem` sobe pra 2 em vez de duplicar a linha.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat(harness): caderno de perguntas nao entendidas em Configuracoes"
```

---

### Task 10: Validação de aceite — as 80 perguntas do catálogo

Critério de aceite da spec (§5): as 80 perguntas resolvem pra um `tipo` reconhecido (nunca `'desconhecido'`) na camada de extração/resolução — rápido, sem rede, cobertura exaustiva. Depois, uma amostra representativa (uma por categoria) é conferida fim a fim contra a API real.

**Files:**
- Nenhum arquivo novo. Só execução/verificação.

**Interfaces:**
- Consumes: `harnessExtractEntities`, `harnessResolveIntent`, e todas as funções de execução das Tasks 5–7.

- [ ] **Step 1: Rodar as 80 perguntas contra a extração/resolução, via skill `verify`**

Com o app aberto e `_teamMap`/`_agentList` carregados, avaliar (substituir os nomes de agente pelos reais da sua conta, se diferentes dos usados como exemplo nesta sessão):

```js
JSON.stringify((() => {
  const perguntas = [
    "Quantos atendimentos tivemos esse mês?","Quantas conversas entraram em agosto?","Qual foi o volume dos últimos 3 meses?",
    "Como está o volume comparado ao mês passado?","Quantos atendimentos a equipe 2 teve em setembro?","Qual mês teve mais atendimentos nos últimos 6 meses?",
    "Quantas conversas o SAG recebeu esse mês?","O volume subiu ou caiu essa semana?",
    "Qual o tempo médio de resposta esse mês?","Quanto tempo a equipe_tecnica leva pra resolver?","A 1ª resposta melhorou em relação ao mês passado?",
    "Qual o TMR do Arthur Gomes?","Quanto tempo leva pra resolver, em média, esse trimestre?","Estamos dentro da meta de resposta?",
    "Qual equipe responde mais rápido?","O tempo de resolução da consultoria está muito alto?",
    "Qual a taxa de resolução desse mês?","Quantos atendimentos foram resolvidos em agosto?","Estamos batendo a meta de resolução?",
    "Por que a taxa de resolução passou de 100%?","Quantos ficaram sem resolver esse mês?","Qual agente resolve mais conversas?",
    "A equipe 3 está resolvendo dentro da meta?","Quantas conversas o Guilherme Ribeiro resolveu?",
    "Qual a satisfação do cliente esse mês?","Quantas avaliações recebemos em setembro?","Tem alguma avaliação ruim recente?",
    "Qual agente tem a melhor nota de CSAT?","Quantos clientes deram 1 estrela?","Me mostra os comentários negativos desse mês",
    "Qual a % de aprovação da equipe 1?","Alguém comentou algo sobre o Cristiano Gatto?",
    "Qual equipe atendeu mais esse mês?","Compara equipe 1 com equipe 2","Qual equipe está pior em tempo de resposta?",
    "Quantas equipes têm dado disponível esse período?","Como está o SAG comparado com as outras equipes?","Qual equipe tem a pontuação mais baixa?",
    "A consultoria melhorou desde o mês passado?","Quais equipes estão fora da meta de resolução?",
    "Como está o Arthur Gomes esse mês?","Qual a pontuação do Vitor Augusto?","Quantas conversas a Priscila Costa atendeu?",
    "O Mauricio Santos está dentro da meta?","Quem são os agentes com nota abaixo de 50?","Mostra o perfil do Guilherme Cabral",
    "Quantos agentes estão com amostra pequena esse mês?","Qual agente teve a maior melhora este trimestre?",
    "Quantas conversas estão abertas agora?","Tem gente esperando resposta?","Quantas conversas estão pendentes?",
    "Quantas conversas estão sem nenhuma resposta?","Tem conversa sem atendente atribuído?","Qual o tempo de espera mais longo agora?",
    "Quantos agentes estão online agora?","Quantas conversas o Ageu Carvalho tem em aberto agora?",
    "Mostra só a equipe 2","Filtra pelo Arthur Gomes","Tira o filtro de agente","Volta pra todas as equipes",
    "Muda pra 3 meses","Vai pra aba Agentes","Me mostra a Análise desse trimestre","Limpa todos os filtros",
    "Quem atendeu mais esse mês?","Qual agente tem a pior pontuação?","Quem tem o menor tempo de resposta?",
    "Qual equipe cresceu mais desde o mês passado?","Quem recebeu mais avaliações de CSAT?","Qual o agente mais rápido pra resolver?",
    "Quem está abaixo da meta de mensagens por conversa?","Qual inbox recebe mais atendimento?",
    "Quantos inboxes a conta tem?","Qual a meta de SLA configurada hoje?","Quantos agentes existem no total?",
    "Quais equipes existem no Chatwoot?","Qual o canal com mais volume?","O CSAT está ativado em todos os inboxes?",
    "Quantas etiquetas (labels) existem?","Resumo geral: como estamos esse mês?"
  ];
  const semReconhecimento = perguntas.filter(p => harnessResolveIntent(harnessExtractEntities(p)).tipo === 'desconhecido');
  return { total: perguntas.length, semReconhecimento };
})())
```

Esperado: `total:80`, `semReconhecimento` uma lista **curta** (idealmente vazia). As perguntas puramente informativas sobre a conta (ex: "Quantos inboxes a conta tem?", "Quantas etiquetas existem?") não têm métrica/entidade reconhecível pelo motor atual e **vão cair em `desconhecido` — isso é esperado e aceitável nesta v1**, porque a spec (§6, fora de escopo) não cobre um catálogo de entidade pra "inbox" ou "label". Se `semReconhecimento` tiver mais de ~8 perguntas (mais do que essas puramente de conta/config), há uma lacuna real no motor de extração — investigar qual categoria falhou antes de prosseguir.

- [ ] **Step 2: Conferir fim a fim uma pergunta de cada categoria, contra a API real**

Uma por categoria (10 perguntas), via `harnessSubmit` na UI de verdade, olhando a bolha de resposta:
```js
(async () => {
  const perguntas = [
    "Quantos atendimentos tivemos esse mês?",
    "Qual o tempo médio de resposta esse mês?",
    "Qual a taxa de resolução desse mês?",
    "Qual a satisfação do cliente esse mês?",
    "Compara equipe 1 com equipe 2",
    "Como está o Arthur Gomes esse mês?",
    "Quantas conversas estão abertas agora?",
    "Vai pra aba Agentes",
    "Quem atendeu mais esse mês?",
    "Resumo geral: como estamos esse mês?"
  ];
  const respostas = [];
  for (const p of perguntas) {
    harnessSubmit(p);
    await new Promise(r => setTimeout(r, 3000));
    const bolhas = document.querySelectorAll('.harness-msg.assistant');
    respostas.push({ pergunta: p, resposta: bolhas[bolhas.length - 1].textContent });
  }
  return JSON.stringify(respostas, null, 1);
})()
```
Esperado: todas as 10 respostas citam número real (nenhuma genérica tipo "não reconheci"), console sem exceção.

- [ ] **Step 3: Screenshot final do painel aberto com uma conversa real**

Tirar um screenshot do painel depois do Step 2 — confirma visualmente que as bolhas renderizam bem, o texto não estoura o painel, e a experiência parece "viva" como pedido no design.

- [ ] **Step 4: Registrar o resultado no spec (nota de aceite)**

Se `semReconhecimento` do Step 1 ficou dentro do esperado (só perguntas de conta/inbox/label fora de escopo do motor de entidade), não é necessário nenhum código novo — a v1 está aceita conforme a spec. Caso contrário, criar um commit adicional cobrindo a lacuna encontrada antes de considerar a task fechada.

Sem commit de código nesta task caso tudo passe — é só verificação.

---

## Verificação final do recurso inteiro

Depois da Task 10, com o app aberto:
```js
JSON.stringify({
  toggleExiste: !!document.getElementById('harness-toggle'),
  painelFechado: !document.getElementById('harness-panel').classList.contains('open'),
  funcoesPrincipais: ['harnessExtractEntities','harnessResolveIntent','harnessHandleMessage','logUnmatchedQuestion','renderHarnessUnmatchedList'].every(fn => typeof window[fn] === 'function' || typeof eval(fn) === 'function')
})
```
Esperado: todos `true`, console limpo, nenhuma mudança em `san-imob/` (`git status --short` só mostra os arquivos do Soma Imob que já estavam lá antes desta sessão).
