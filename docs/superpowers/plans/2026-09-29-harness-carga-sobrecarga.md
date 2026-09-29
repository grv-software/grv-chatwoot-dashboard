# Harness — carga ao vivo, sobrecarga e ranking por equipe — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar ao harness (assistente de chat do GRV SAC Dashboard) 3 capacidades novas: carga ao vivo + detecção de sobrecarga por agente/equipe, ranking restrito a uma equipe, e ranking do inbox SAG por agente (histórico paginado).

**Architecture:** Tudo em `index.html` (arquivo único). Reaproveita ao máximo o motor de entidades/intents do harness já existente (`harnessExtractEntities`, `harnessResolveIntent`, `harnessResponderRanking`, `harnessTeamMemberIds`, `_rawConvs`/`_pendingConvs` já carregados em memória). Zero chamada a modelo de IA — tudo regra + dado real.

**Tech Stack:** JavaScript vanilla no navegador, API REST do Chatwoot via proxy `dev-server.js` (`/api/*` → produção real), sem framework.

## Global Constraints

- Nenhuma chamada a modelo de IA — só regras/regex contra dados reais (`_teamMap`, `_agentList`, `_rawConvs`, `_pendingConvs`) ou chamadas de API já estabelecidas (`api()`), sempre **GET**, nunca mutação.
- Único arquivo tocado: `index.html`. **Nunca** tocar/commitar arquivos de `san-imob/` ou `docs/superpowers/specs/2026-08-03-soma-imob-design-system-v2.md` — são trabalho não commitado de outro projeto (Soma Imob) presente na mesma branch `alteracoes`. Em cada commit deste plano, usar `git commit index.html -m "..."` (ou `git add index.html` seguido de `git commit` sem `-A`) — **nunca `git commit -m` sem pathspec quando houver outros arquivos staged**, e sempre rodar `git status --short` antes e depois pra confirmar que os arquivos do Soma Imob continuam intocados.
- Verificação: usar a skill do repo `c:\Users\Samuel Wallace\Documents\vscode\grv-chatwoot-dashboard\.claude\skills\verify\SKILL.md` (dev-server.js + Chrome headless via CDP) — nunca `taskkill /IM chrome.exe` (mata o Chrome real do usuário); matar processos específicos por PID/porta.
- Teto de paginação do SAG: **150 páginas** (25 conversas/página). Medido ao vivo em 2026-09-29: o mês corrente inteiro do SAG são 73 páginas / 1.810 conversas — o teto dá o dobro de folga.
- Régua de sobrecarga: agente sobrecarregado ⟺ carga ao vivo ≥ 1,5x a média do próprio time, **e** a média do time > 0 (guarda técnica pra evitar comparar com zero).

---

### Task 1: Carga ao vivo e sobrecarga

**Files:**
- Modify: `index.html` (bloco de constantes do harness, ~linha 4264-4270; `harnessResolveIntent`, ~linha 4395-4400; nova seção de execução entre `harnessExecutarFila` e `harnessResponderResumir`, ~linha 4741-4743; `harnessHandleMessage`, ~linha 4884-4886)

**Interfaces:**
- Consumes: `_rawConvs`, `_pendingConvs` (globais já populados, cada item com `.meta.assignee.{id,name}` e `.inbox_id`), `_teamMap` (`{teamId: {id,name}}`), `harnessTeamCandidates()` (retorna `[{key,label,aliases}]`, inclui SAG com `key===SAG_FILTER_ID`), `harnessTeamMemberIds(equipeId)` (já existe, retorna `Promise<number[]|null>`, `null` pra SAG), `SAG_FILTER_ID`, `SAG_INBOX_ID`, `harnessFmtPeriodo` (não usado aqui, é só pra referência de estilo).
- Produces: `harnessCargaAoVivo()` → `{ [agentId]: { nome, valor } }`; `harnessAgentTeamMap()` → `Promise<{ [agentId]: teamId }>`; `harnessExecutarCarga(intent)` → `Promise<string>`; novo `intent.tipo === 'carga'` com forma `{ tipo:'carga', modo:'valor'|'sobrecarga', escopo:'agente'|'equipe'|'todos', agente, equipe, direcao }` (usado pela Task 4, não por outras tasks deste plano).

- [ ] **Step 1: Adicionar as constantes de detecção ao vivo**

Encontre o bloco `HARNESS_FILA` (por volta da linha 4264-4270):

```js
const HARNESS_FILA = Object.entries({
  abertas:       ['abertas agora', 'em aberto agora', 'conversas abertas'],
  pendentes:     ['pendentes', 'pendente'],
  semresposta:   ['sem resposta', 'nao atendidas', 'sem retorno', 'esperando resposta', 'aguardando resposta'],
  naoatribuidas: ['nao atribuida', 'sem atendente', 'sem agente atribuido'],
  online:        ['online agora', 'agentes online', 'quem esta online']
}).map(([key, aliases]) => ({ key, label: key, aliases }));
```

Logo depois desse bloco, adicione:

```js
/* "agora"/"neste momento" pede carga AO VIVO de um agente/equipe específico —
   diferente de HARNESS_FILA, que é sobre a conta inteira. Sobrecarga não
   precisa da palavra "agora": perguntar se alguém "está sobrecarregado" já é
   inerentemente sobre o presente. */
const HARNESS_CARGA_LIVE_RE = /\bagora\b|\bneste momento\b|\bno momento\b|\bnesse momento\b/;
const HARNESS_SOBRECARGA_RE = /sobrecarregad|tranquil[oa]|afogad|precisa de (ajuda|reforco)/;

function harnessDirecaoSobrecarga(norm) {
  return /tranquil[oa]|folgad|mais calm/.test(norm) ? 'tranquilo' : 'sobrecarregado';
}
```

- [ ] **Step 2: Encaixar o intent `carga` na cadeia de prioridade**

Encontre em `harnessResolveIntent` (por volta da linha 4395-4400):

```js
  if (acao === 'filtrar') {
    const limpar = /tira o filtro|limpa filtro|limpa os filtros|limpa todos os filtros|volta pra todas|remove o filtro/.test(norm);
    return { tipo: 'filtrar', limpar, equipe: teams[0] || null, agente: agents[0] || null };
  }

  if (fila) return { tipo: 'fila', fila: fila.key };
```

Substitua por (adiciona o bloco de `carga` entre `filtrar` e `fila` — prioridade: navegar > filtrar > carga > fila > resumir > comparar/ranking > metrica):

```js
  if (acao === 'filtrar') {
    const limpar = /tira o filtro|limpa filtro|limpa os filtros|limpa todos os filtros|volta pra todas|remove o filtro/.test(norm);
    return { tipo: 'filtrar', limpar, equipe: teams[0] || null, agente: agents[0] || null };
  }

  const cargaLive = HARNESS_CARGA_LIVE_RE.test(norm);
  const sobrecarga = HARNESS_SOBRECARGA_RE.test(norm);
  if (sobrecarga || (cargaLive && (teams.length || agents.length))) {
    let escopo;
    if (agents.length) escopo = 'agente';
    else if (teams.length) escopo = 'equipe';
    else if (sobrecarga && /\bequipe\b|\btime\b/.test(norm)) escopo = 'equipe';
    else escopo = 'todos';
    return {
      tipo: 'carga',
      modo: sobrecarga ? 'sobrecarga' : 'valor',
      escopo,
      agente: agents[0] || null,
      equipe: teams[0] || null,
      direcao: sobrecarga ? harnessDirecaoSobrecarga(norm) : null
    };
  }

  if (fila) return { tipo: 'fila', fila: fila.key };
```

- [ ] **Step 3: Escrever as funções de dado e execução**

Encontre `harnessExecutarFila` e o início de `harnessResponderResumir` (por volta da linha 4726-4744):

```js
async function harnessExecutarFila(intent) {
  ...
  return `Tem ${valor} conversa${valor === 1 ? '' : 's'} ${label} agora.`;
}

function harnessResponderResumir() {
```

Insira o bloco abaixo entre as duas funções (depois do `}` que fecha `harnessExecutarFila`, antes de `function harnessResponderResumir`):

```js
/* ── ASSISTENTE — execução: carga ao vivo e sobrecarga ────── */
function harnessCargaAoVivo() {
  const porAgente = {};
  for (const c of [..._rawConvs, ..._pendingConvs]) {
    const a = c.meta?.assignee;
    if (!a) continue;
    if (!porAgente[a.id]) porAgente[a.id] = { nome: a.name, valor: 0 };
    porAgente[a.id].valor++;
  }
  return porAgente;
}

async function harnessAgentTeamMap() {
  const mapa = {};
  const times = harnessTeamCandidates().filter(t => t.key !== SAG_FILTER_ID);
  const listas = await Promise.all(times.map(t => harnessTeamMemberIds(t.key)));
  times.forEach((t, i) => { (listas[i] || []).forEach(agentId => { mapa[agentId] = t.key; }); });
  return mapa;
}

async function harnessExecutarCarga(intent) {
  const carga = harnessCargaAoVivo();

  if (intent.modo === 'valor') {
    if (intent.agente) {
      const valor = carga[intent.agente.key]?.valor || 0;
      return `${intent.agente.label} tem ${valor} atendimento${valor === 1 ? '' : 's'} em aberto agora.`;
    }
    if (intent.equipe) {
      if (intent.equipe.key === SAG_FILTER_ID) {
        const doSag = [..._rawConvs, ..._pendingConvs].filter(c => c.inbox_id === SAG_INBOX_ID).length;
        return `O SAG tem ${doSag} atendimento${doSag === 1 ? '' : 's'} em aberto agora.`;
      }
      const membros = await harnessTeamMemberIds(intent.equipe.key);
      const valor = (membros || []).reduce((soma, id) => soma + (carga[id]?.valor || 0), 0);
      return `A equipe ${intent.equipe.label} tem ${valor} atendimento${valor === 1 ? '' : 's'} em aberto agora.`;
    }
    return 'Me diga qual agente ou equipe você quer ver a carga ao vivo.';
  }

  /* modo 'sobrecarga' */
  const mapa = await harnessAgentTeamMap();
  const somaTime = {}; const contaTime = {}; const mediaTime = {};
  Object.entries(mapa).forEach(([agentId, teamId]) => {
    contaTime[teamId] = (contaTime[teamId] || 0) + 1;
    somaTime[teamId] = (somaTime[teamId] || 0) + (carga[agentId]?.valor || 0);
  });
  Object.keys(contaTime).forEach(teamId => { mediaTime[teamId] = somaTime[teamId] / contaTime[teamId]; });

  if (intent.escopo === 'equipe') {
    if (intent.equipe?.key === SAG_FILTER_ID) {
      return 'O SAG não tem um time fixo de agentes, então não dá pra calcular uma média por pessoa pra comparar sobrecarga. Pergunte sobre uma equipe real, ou "quantos atendimentos o SAG tem agora" pra ver o volume ao vivo.';
    }
    if (intent.equipe) {
      const teamId = intent.equipe.key;
      const media = mediaTime[teamId] || 0;
      const outras = Object.entries(mediaTime).filter(([tid]) => Number(tid) !== Number(teamId)).map(([, m]) => m);
      const mediaOutras = outras.length ? outras.reduce((a, b) => a + b, 0) / outras.length : 0;
      if (media === 0) return `A equipe ${intent.equipe.label} não tem nenhum atendimento em aberto agora.`;
      const status = media >= mediaOutras * 1.5 ? 'está mais carregada que as outras equipes'
        : media <= mediaOutras / 1.5 ? 'está mais tranquila que as outras equipes'
        : 'está com carga parecida com as outras equipes';
      return `A equipe ${intent.equipe.label} ${status}: média de ${media.toFixed(1)} atendimentos por agente agora (outras equipes: ${mediaOutras.toFixed(1)}).`;
    }
    const entradas = Object.entries(mediaTime);
    if (!entradas.length) return 'Não encontrei dados de carga por equipe agora.';
    entradas.sort((a, b) => intent.direcao === 'tranquilo' ? a[1] - b[1] : b[1] - a[1]);
    const [teamId, media] = entradas[0];
    const nome = (_teamMap[teamId] || {}).name || `Time ${teamId}`;
    return intent.direcao === 'tranquilo'
      ? `A equipe ${nome} está mais tranquila agora: média de ${media.toFixed(1)} atendimentos por agente.`
      : `A equipe ${nome} está mais sobrecarregada agora: média de ${media.toFixed(1)} atendimentos por agente.`;
  }

  if (intent.agente) {
    const teamId = mapa[intent.agente.key];
    const valor = carga[intent.agente.key]?.valor || 0;
    if (teamId == null) return `${intent.agente.label} tem ${valor} atendimento${valor === 1 ? '' : 's'} agora, mas não encontrei o time dele(a) pra comparar com a média.`;
    const media = mediaTime[teamId] || 0;
    if (media === 0) return `${intent.agente.label} tem ${valor} atendimento${valor === 1 ? '' : 's'} agora — o time dele(a) está zerado agora, sem média pra comparar.`;
    const razao = valor / media;
    return razao >= 1.5
      ? `Sim — ${intent.agente.label} está sobrecarregado(a): ${valor} atendimentos agora, ${razao.toFixed(1)}x a média do time (${media.toFixed(1)}).`
      : `Não — ${intent.agente.label} está com ${valor} atendimentos agora, dentro da média do time (${media.toFixed(1)}).`;
  }

  const candidatos = Object.entries(carga)
    .map(([agentId, e]) => {
      const teamId = mapa[agentId];
      if (teamId == null || !mediaTime[teamId]) return null;
      return { nome: e.nome, valor: e.valor, razao: e.valor / mediaTime[teamId] };
    })
    .filter(c => c && c.razao >= 1.5)
    .sort((a, b) => b.razao - a.razao);
  if (!candidatos.length) return 'Ninguém está claramente sobrecarregado agora — a carga está equilibrada entre os times.';
  const top = candidatos[0];
  const resto = candidatos.length > 1 ? ` (e mais ${candidatos.length - 1} agente${candidatos.length - 1 === 1 ? '' : 's'})` : '';
  return `${top.nome} está sobrecarregado(a): ${top.valor} atendimentos agora, ${top.razao.toFixed(1)}x a média do time${resto}.`;
}

```

- [ ] **Step 4: Ligar o dispatch em `harnessHandleMessage`**

Encontre (por volta da linha 4884-4886):

```js
    if (intent.tipo === 'navegar')  resposta = harnessExecutarNavegar(intent);
    else if (intent.tipo === 'filtrar')  resposta = harnessExecutarFiltrar(intent);
    else if (intent.tipo === 'fila')     resposta = await harnessExecutarFila(intent);
```

Substitua por:

```js
    if (intent.tipo === 'navegar')  resposta = harnessExecutarNavegar(intent);
    else if (intent.tipo === 'filtrar')  resposta = harnessExecutarFiltrar(intent);
    else if (intent.tipo === 'carga')    resposta = await harnessExecutarCarga(intent);
    else if (intent.tipo === 'fila')     resposta = await harnessExecutarFila(intent);
```

- [ ] **Step 5: Verificar ao vivo**

Siga a skill `verify` do repo (dev-server.js + Chrome headless via CDP, `localStorage.grv_token`/`grv_account` semeados, esperar `_agentList.length` e `Object.keys(_teamMap).length` maiores que 0 antes de testar). Na página, abra o harness (`harnessOpen()`) e rode, uma de cada vez, via `harnessSubmit(texto)`, lendo o texto da última bolha `.harness-msg.assistant`:

1. Busque um agente real: `_agentList[0].name` (qualquer um serve). Pergunte `` `Quantos atendimentos o ${nome} está fazendo agora?` `` — espere uma frase com um número e "em aberto agora".
2. Pergunte `"Quantas conversas a equipe 1 tem em aberto neste momento?"` — espere um número agregado, sem erro no console.
3. Pergunte `"Quem está sobrecarregado agora?"` — espere ou um nome com "x a média do time", ou a frase de "ninguém está claramente sobrecarregado".
4. Pergunte `"Qual time está sobrecarregado?"` e depois `"Qual equipe está mais tranquila?"` — espere nomes de equipes diferentes (ou iguais, se só uma equipe tiver dado) com "média de X atendimentos por agente".
5. Pergunte `"O SAG está sobrecarregado?"` — espere a frase específica de que o SAG não tem roster fixo, **não** um erro nem a resposta de "zero atendimentos".

Confirme no console do CDP que nenhuma exceção foi lançada (`Runtime.exceptionThrown` não deve disparar durante essas 5 perguntas).

- [ ] **Step 6: Commit**

```bash
git status --short   # confirme que só index.html mudou (fora os arquivos pré-existentes do Soma Imob, que devem continuar aparecendo do mesmo jeito)
git commit index.html -m "feat(harness): carga ao vivo e deteccao de sobrecarga por agente/equipe

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 2: Ranking restrito a uma equipe

**Files:**
- Modify: `index.html` (`harnessResolveIntent`, ~linha 4409-4415; `harnessResponderRanking`, ~linha 4681-4689)

**Interfaces:**
- Consumes: `harnessIsRanking(norm)`, `harnessDirecaoRanking(norm)`, `harnessResolvePeriodo`, `harnessTeamMemberIds(equipeId)`, `harnessValorRankingAgente(intent, agenteId)` (todos já existem, assinaturas inalteradas).
- Produces: ranking intent ganha campo opcional `equipe` (`{key,label}|null`); `harnessResponderRanking` passa a restringir os candidatos aos membros do time quando `intent.equipe` está presente e não é o SAG. (O caso `intent.equipe.key === SAG_FILTER_ID` fica para a Task 3 — depois desta task, perguntar pelo SAG aqui ainda responde "Não encontrei agentes na equipe SAG", o que é esperado até a Task 3.)

- [ ] **Step 1: Adicionar o ramo de ranking-por-equipe em `harnessResolveIntent`**

Encontre (por volta da linha 4409-4415):

```js
  if (teams.length === 2) {
    return { tipo: 'comparar', escopo: 'equipe', a: teams[0], b: teams[1], metrica: metrica?.key || 'volume', periodo };
  }
  if (agents.length === 2) {
    return { tipo: 'comparar', escopo: 'agente', a: agents[0], b: agents[1], metrica: metrica?.key || 'volume', periodo };
  }
```

Logo depois, antes do comentário `/* Sem exigir metrica reconhecida... */` e do `if (!teams.length && !agents.length && harnessIsRanking(norm))`, adicione:

```js
  /* Uma equipe citada junto com "quem"/"mais"/"menos" etc. é ranking
     DENTRO daquele time, não equipe-vs-equipe — precisa vir antes do
     ramo de ranking sem equipe (que assume toda a conta) e antes do
     fallback pra 'metrica' (que trataria a equipe como escopo de uma
     pergunta de valor único, não de comparação entre agentes). */
  if (teams.length === 1 && !agents.length && harnessIsRanking(norm)) {
    return { tipo: 'ranking', escopo: 'agente', equipe: teams[0], metrica: metrica?.key || 'volume', direcao: harnessDirecaoRanking(norm), periodo };
  }
```

- [ ] **Step 2: Restringir os candidatos do ranking por agente**

Encontre em `harnessResponderRanking` (por volta da linha 4681-4689):

```js
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
```

Substitua por:

```js
  if (intent.escopo === 'agente') {
    if (!_agentList.length) {
      const agents = await api(`/v1/accounts/${cfg.account}/agents`).catch(() => []);
      if (Array.isArray(agents)) _agentList = agents;
    }

    let candidatos = _agentList;
    if (intent.equipe) {
      const memberIds = await harnessTeamMemberIds(intent.equipe.key);
      candidatos = _agentList.filter(a => (memberIds || []).includes(a.id));
      if (!candidatos.length) return `Não encontrei agentes na equipe ${intent.equipe.label}.`;
    }

    resultados = await Promise.all(candidatos.map(async a => {
      const valor = await harnessValorRankingAgente(intent, a.id);
      return valor == null ? null : { nome: a.name, valor };
    }));
  } else {
```

- [ ] **Step 3: Verificar ao vivo**

Via a skill `verify`, com o harness aberto:

1. Pergunte `"Quem da equipe 1 atendeu mais esse mês?"` — espere um nome de agente real seguido de um número de atendimentos, **não** "Não encontrei agentes na equipe".
2. Pergunte `"Quem da equipe 2 tem o menor tempo de resposta?"` — espere um nome com tempo em minutos.
3. Compare o nome retornado no passo 1 com a lista real de membros da equipe 1: `await api('/v1/accounts/1/teams/6/team_members')` no console da página (ou via `fetch` direto), confirme que o nome retornado está nessa lista.
4. Pergunte `"Dentro do SAG, qual agente mais atende?"` — nesta task ainda é esperado responder "Não encontrei agentes na equipe SAG." (será corrigido na Task 3). Confirme que é essa mensagem exata e não um erro/exceção.

- [ ] **Step 4: Commit**

```bash
git status --short
git commit index.html -m "feat(harness): ranking de agentes restrito a uma equipe

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 3: Ranking do SAG por agente (histórico paginado)

**Files:**
- Modify: `index.html` (nova função antes de `harnessResponderRanking`, ~linha 4676; dispatch dentro de `harnessResponderRanking`, dentro do bloco `if (intent.equipe) { ... }` escrito na Task 2)

**Interfaces:**
- Consumes: `api(path)` (retorna JSON já parseado; para conversas, formato `{ data: { payload: [...], meta: {...} } }`, cada item com `.created_at` (segundos), `.meta.assignee.{id,name}`), `SAG_INBOX_ID` (=17), `cfg.account`, `harnessFmtPeriodo(since,until)`.
- Produces: `harnessResponderRankingSAG(intent)` → `Promise<string>`, chamada por `harnessResponderRanking` quando `intent.equipe?.key === SAG_FILTER_ID`.

- [ ] **Step 1: Escrever a busca paginada e a função de resposta**

Encontre o início de `harnessResponderRanking` (por volta da linha 4676):

```js
async function harnessResponderRanking(intent) {
```

Insira, logo **antes** dessa linha:

```js
const HARNESS_SAG_RANKING_MAX_PAGES = 150;
const HARNESS_SAG_RANKING_BATCH = 8;

/* Paginação real medida em 2026-09-29 contra a API de produção: o mês
   corrente inteiro do inbox SAG são 73 páginas / 1.810 conversas. O teto
   de 150 páginas dá o dobro de folga pra "este mês"/"hoje"; períodos mais
   longos ("trimestre", "6 meses") podem estourar — nesse caso a resposta
   avisa que o número pode estar incompleto, mesmo padrão do aviso de
   truncamento já usado no fix de paginação do CSAT. */
async function harnessBuscarConversasSAGPorAgente(since, until) {
  const porAgente = {};
  let page = 1;
  let parar = false;
  while (!parar && page <= HARNESS_SAG_RANKING_MAX_PAGES) {
    const paginas = Array.from({ length: HARNESS_SAG_RANKING_BATCH }, (_, i) => page + i);
    const respostas = await Promise.all(paginas.map(p =>
      api(`/v1/accounts/${cfg.account}/conversations?inbox_id=${SAG_INBOX_ID}&status=all&assignee_type=all&sort_by=created_at&page=${p}`).catch(() => null)
    ));
    let algumaComDado = false;
    for (const r of respostas) {
      const lista = r?.data?.payload || [];
      if (!lista.length) continue;
      algumaComDado = true;
      for (const c of lista) {
        if (c.created_at < since) { parar = true; continue; }
        if (c.created_at > until) continue;
        const a = c.meta?.assignee;
        if (!a) continue;
        if (!porAgente[a.id]) porAgente[a.id] = { nome: a.name, valor: 0 };
        porAgente[a.id].valor++;
      }
    }
    if (!algumaComDado) parar = true;
    page += HARNESS_SAG_RANKING_BATCH;
  }
  const truncado = page > HARNESS_SAG_RANKING_MAX_PAGES;
  return { porAgente, truncado };
}

async function harnessResponderRankingSAG(intent) {
  const { since, until } = intent.periodo;
  const periodoTxt = harnessFmtPeriodo(since, until);

  if (intent.metrica !== 'volume') {
    return 'Dentro do SAG eu só consigo comparar por quantidade de atendimentos — TMR, TMA e CSAT recortados por esse inbox exigiriam abrir cada conversa uma por uma. Pergunta por quantidade, ou tira o recorte do SAG.';
  }

  const { porAgente, truncado } = await harnessBuscarConversasSAGPorAgente(since, until);
  const validos = Object.values(porAgente);
  if (!validos.length) return `Não encontrei atendimentos no SAG em ${periodoTxt}.`;

  const ordenarAsc = intent.direcao.modo === 'magnitude' ? !intent.direcao.desc : intent.direcao.quer !== 'melhor';
  validos.sort((a, b) => ordenarAsc ? a.valor - b.valor : b.valor - a.valor);

  const top = validos[0];
  let texto = `No SAG, ${top.nome} lidera em ${periodoTxt}: ${top.valor} atendimento${top.valor === 1 ? '' : 's'}.`;
  if (truncado) texto += ' (período longo — contei até o teto de páginas, o número real pode ser um pouco maior.)';
  return texto;
}

```

- [ ] **Step 2: Ligar o caso SAG dentro do ranking por agente**

Encontre o bloco escrito na Task 2, dentro de `harnessResponderRanking`:

```js
    let candidatos = _agentList;
    if (intent.equipe) {
      const memberIds = await harnessTeamMemberIds(intent.equipe.key);
      candidatos = _agentList.filter(a => (memberIds || []).includes(a.id));
      if (!candidatos.length) return `Não encontrei agentes na equipe ${intent.equipe.label}.`;
    }
```

Substitua por:

```js
    let candidatos = _agentList;
    if (intent.equipe && intent.equipe.key === SAG_FILTER_ID) {
      return harnessResponderRankingSAG(intent);
    }
    if (intent.equipe) {
      const memberIds = await harnessTeamMemberIds(intent.equipe.key);
      candidatos = _agentList.filter(a => (memberIds || []).includes(a.id));
      if (!candidatos.length) return `Não encontrei agentes na equipe ${intent.equipe.label}.`;
    }
```

- [ ] **Step 3: Verificar ao vivo**

Via a skill `verify`, com o harness aberto (esse teste é mais lento — a paginação do mês corrente do SAG são ~73 páginas reais, espere alguns segundos pela resposta):

1. Pergunte `"Dentro do SAG, qual agente mais atende?"` — espere `"No SAG, <nome> lidera em <período>: N atendimentos."` com N > 0 e sem o aviso de truncamento (mês corrente cabe no teto).
2. Confirme o número manualmente: no console da página, rode a mesma paginação (ou reaproveite `harnessBuscarConversasSAGPorAgente` diretamente, já que é uma função global) para o mês corrente e compare o `top` retornado — devem bater.
3. Pergunte `"No SAG, quem tem o menor tempo de resposta?"` — espere a frase de que só dá pra comparar por quantidade dentro do SAG, **não** um erro nem um número de TMR.
4. Confirme no console do CDP que nenhuma exceção foi lançada durante essas perguntas.

- [ ] **Step 4: Commit**

```bash
git status --short
git commit index.html -m "feat(harness): ranking do SAG por agente via paginacao historica

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 4: Aceite do catálogo (carga, sobrecarga, ranking por equipe, SAG)

**Files:**
- Modify: `index.html` (só se o aceite achar uma lacuna real — nesse caso, o fix específico entra aqui, seguindo o mesmo padrão de correção usada nas Tasks 1-3)

**Interfaces:**
- Consumes: tudo que as Tasks 1-3 produziram.
- Produces: nenhuma interface nova — esta task só verifica e corrige.

- [ ] **Step 1: Rodar o catálogo de aceite ao vivo**

Via a skill `verify`, com o harness aberto, rode cada pergunta abaixo com `harnessSubmit`, leia a bolha de resposta e confira contra o critério ao lado. Troque `<AGENTE_REAL>` por um `name` de verdade obtido de `_agentList` na própria página antes de montar as perguntas.

| Pergunta | Critério |
|---|---|
| `Quantos atendimentos o <AGENTE_REAL> está fazendo agora?` | Resposta com um número e "em aberto agora" |
| `Quem está sobrecarregado agora?` | Nome + "x a média do time", ou a frase de ninguém sobrecarregado |
| `Qual time está sobrecarregado?` | Nome de equipe real + "média de X atendimentos por agente" |
| `Qual equipe está mais tranquila agora?` | Nome de equipe real, pode ser igual ou diferente da pergunta anterior |
| `A equipe 2 está sobrecarregada?` | Frase comparando a equipe 2 com a média das outras |
| `Quem da equipe 3 tem a pior pontuação?` | Nome de um membro real da equipe 3 (confirme via `team_members` do time da equipe 3) |
| `Quem da equipe técnica tem o menor tempo de resolução?` | Nome de um membro real da equipe técnica com tempo em horas |
| `Dentro do SAG, qual agente mais atende esse mês?` | Nome + contagem, mesmo formato validado na Task 3 |
| `No SAG, qual agente tem mais conversas agora?` | Como não há período "agora" separado, cai no mesmo caminho histórico do mês — aceitável; confirme que responde e não trava |

- [ ] **Step 2: Corrigir qualquer lacuna real encontrada**

Se alguma pergunta da tabela cair em `desconhecido`, travar, ou responder um número visivelmente errado (confira contra a API crua, do jeito que a skill `verify` descreve em "Conferir contra a verdade"), pare e ajuste — não decida um novo comportamento sozinho: descreva a lacuna exata (a mensagem, o intent que ela resolveu com `harnessExtractEntities`/`harnessResolveIntent`, e o que deveria ter acontecido) antes de aplicar o fix mais estreito possível, seguindo o mesmo estilo das correções de catálogo já feitas no harness original (aliases pontuais, nunca uma reescrita ampla).

- [ ] **Step 3: Commit (só se houve fix)**

```bash
git status --short
git commit index.html -m "fix(harness): lacunas do catalogo de carga/sobrecarga/ranking achadas na validacao de aceite

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

Se nenhum fix foi necessário, não crie um commit vazio — apenas reporte que o aceite passou de primeira.
