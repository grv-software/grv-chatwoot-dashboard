# Ranking de clientes por conversas (integração Frappe) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar, num card novo da aba Análise, o ranking de clientes que mais abriram conversas no período selecionado — primeira integração do dashboard com o CRM Frappe (`crm.nxlite.com.br`).

**Architecture:** Um módulo compartilhado (`lib/clientes-ranking-core.js`) faz a busca paginada + agregação contra o Frappe; dois consumidores finos o chamam — uma Netlify Function (produção) e uma rota nova no `dev-server.js` (local) — cada um lendo a chave de API só do próprio ambiente de servidor, nunca expondo ela ao navegador. O `index.html` só fala com `/api/clientes-ranking`, nunca direto com o Frappe.

**Tech Stack:** Node puro (sem dependências — o projeto não tem `package.json`), Netlify Functions, JavaScript vanilla no navegador.

## Global Constraints

- Nenhuma chamada de escrita ao Frappe em nenhum ponto — só `GET`.
- A chave de API (`FRAPPE_API_KEY`/`FRAPPE_API_SECRET`) nunca aparece em código, nunca chega ao navegador, nunca em texto puro num comando de terminal — sempre lida de variável de ambiente.
- Teto de paginação: 20 páginas de 5.000 registros (100.000 registros) contra `Cliente Conversa`. Se estourar, a resposta marca `truncado: true` e mostra o ranking parcial — nunca trunca calado.
- Único arquivo de UI tocado: `index.html`, reaproveitando os estilos `.chart-card`, `.chart-full`, `.an-team-table`, `.chart-na` que já existem — não criar um novo seletor de período, reaproveitar `#chart-period-sel`.
- Arquivos desta feature: `lib/clientes-ranking-core.js`, `netlify/functions/clientes-ranking.js`, `netlify.toml`, `dev-server.js`, `index.html`. **Nunca tocar** `san-imob/`, `__pycache__/`, `resultado2.txt`, `resultado_iniciados.txt`, `tests/__pycache__/`, `docs/superpowers/specs/2026-08-03-soma-imob-design-system-v2.md` — são arquivos de outro projeto/sessão presentes na mesma árvore. Sempre `git commit <arquivos exatos> -m "..."`, nunca `-A`/`.`; sempre `git status --short` antes e depois de cada commit.
- Verificação ao vivo via a skill do repo `c:\Users\Samuel Wallace\Documents\vscode\grv-chatwoot-dashboard\.claude\skills\verify\SKILL.md`, estendida nesta feature pra também cobrir a chamada ao Frappe (GET-only, mesma regra de sempre).

---

### Task 1: Módulo compartilhado `lib/clientes-ranking-core.js`

**Files:**
- Create: `lib/clientes-ranking-core.js`

**Interfaces:**
- Consumes: nada (usa só `fetch` nativo do Node 18+, já confirmado disponível nesta máquina — Node 24).
- Produces: `async function buildRanking({ since, until, apiKey, apiSecret })` → `Promise<{ periodo: {since, until}, clientes: [{cliente, nome, total}], semCliente: number, truncado: boolean }>`, usado pelas Tasks 2 e 3. Também exporta `fmtFrappeDate(unixSeconds)` para reaproveitar nos testes.

- [ ] **Step 1: Escrever o script de verificação (antes do módulo existir)**

Crie, na raiz do projeto (temporário — apague no Step 6, depois de commitar só o módulo), um arquivo `verify-core.js`:

```js
const assert = require('assert');
const { buildRanking, fmtFrappeDate } = require('./lib/clientes-ranking-core.js');

(async () => {
  assert.strictEqual(fmtFrappeDate(1759276800), '2025-10-01 00:00:00', 'formato de data Frappe incorreto');

  const now = Math.floor(Date.now() / 1000);
  const since = now - 7 * 24 * 3600;
  const result = await buildRanking({
    since, until: now,
    apiKey: process.env.FRAPPE_API_KEY,
    apiSecret: process.env.FRAPPE_API_SECRET
  });

  assert.ok(Array.isArray(result.clientes), 'clientes deve ser array');
  assert.ok(result.clientes.length <= 15, 'nunca mais que 15 no ranking');
  assert.ok(typeof result.semCliente === 'number', 'semCliente deve ser number');
  for (let i = 1; i < result.clientes.length; i++) {
    assert.ok(result.clientes[i - 1].total >= result.clientes[i].total, 'ranking precisa estar ordenado desc');
  }
  console.log('OK —', result.clientes.length, 'clientes, semCliente =', result.semCliente, 'truncado =', result.truncado);
  console.log(JSON.stringify(result.clientes.slice(0, 3), null, 2));
})().catch(e => { console.error('FALHOU:', e.message); process.exit(1); });
```

(`1759276800` corresponde a `2025-10-01 00:00:00` em horário local — se a máquina estiver em outro fuso, ajuste o valor esperado pra bater com `new Date(1759276800*1000)` no fuso local, o importante é testar o formato `YYYY-MM-DD HH:MM:SS`, não o valor exato do timestamp.)

- [ ] **Step 2: Rodar e confirmar que falha (módulo ainda não existe)**

```bash
node verify-core.js
```

Esperado: `Error: Cannot find module '.../lib/clientes-ranking-core.js'`.

- [ ] **Step 3: Implementar o módulo**

```js
const FRAPPE_BASE = 'https://crm.nxlite.com.br';
const PAGE_SIZE = 5000;
const MAX_PAGES = 20;

function fmtFrappeDate(unixSeconds) {
  const d = new Date(unixSeconds * 1000);
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

async function buildRanking({ since, until, apiKey, apiSecret }) {
  const sinceFmt = fmtFrappeDate(since);
  const untilFmt = fmtFrappeDate(until);
  const headers = { Authorization: `token ${apiKey}:${apiSecret}` };

  const contagem = {};
  let semCliente = 0;
  let truncado = false;

  for (let page = 0; page < MAX_PAGES; page++) {
    const url = new URL(`${FRAPPE_BASE}/api/resource/Cliente Conversa`);
    url.searchParams.set('fields', JSON.stringify(['cliente', 'cliente_nome']));
    url.searchParams.set('filters', JSON.stringify([
      ['criacao_conversa', '>=', sinceFmt],
      ['criacao_conversa', '<=', untilFmt]
    ]));
    url.searchParams.set('limit_start', String(page * PAGE_SIZE));
    url.searchParams.set('limit_page_length', String(PAGE_SIZE));

    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`Frappe HTTP ${res.status}`);
    const json = await res.json();
    const rows = json.data || [];
    if (!rows.length) break;

    for (const row of rows) {
      if (!row.cliente) { semCliente++; continue; }
      if (!contagem[row.cliente]) contagem[row.cliente] = { nome: row.cliente_nome || row.cliente, total: 0 };
      contagem[row.cliente].total++;
    }

    if (rows.length < PAGE_SIZE) break;
    if (page === MAX_PAGES - 1) truncado = true;
  }

  const clientes = Object.entries(contagem)
    .map(([cliente, v]) => ({ cliente, nome: v.nome, total: v.total }))
    .sort((a, b) => b.total - a.total)
    .slice(0, 15);

  return { periodo: { since, until }, clientes, semCliente, truncado };
}

module.exports = { buildRanking, fmtFrappeDate };
```

- [ ] **Step 4: Rodar de novo com as credenciais reais (via variável de ambiente, nunca em texto no comando)**

```bash
export FRAPPE_API_KEY=8b59db66515b51e
export FRAPPE_API_SECRET=3a0a3c2843d7cfe
node verify-core.js
```

Esperado: imprime `OK — N clientes, semCliente = ..., truncado = false` e os 3 primeiros do ranking, sem lançar exceção.

- [ ] **Step 5: Conferir contra a verdade**

No mesmo terminal, rode uma contagem independente pro cliente que apareceu em 1º lugar, comparando com uma chamada direta ao Frappe (mesmo filtro de data, `filters=[["cliente","=","<codigo_do_1o_colocado>"],["criacao_conversa",">=","<sinceFmt>"],["criacao_conversa","<=","<untilFmt>"]]`, usando `frappe.client.get_count` via `GET /api/method/frappe.client.get_count?doctype=Cliente Conversa&filters=...`). O número tem que bater com o `total` que `buildRanking` retornou pra esse cliente.

- [ ] **Step 6: Apagar o script temporário e commitar só o módulo**

```bash
rm verify-core.js
git status --short
git add lib/clientes-ranking-core.js
git commit lib/clientes-ranking-core.js -m "feat(crm): modulo compartilhado de ranking de clientes (Frappe)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
git status --short
```

---

### Task 2: Netlify Function + redirect

**Files:**
- Create: `netlify/functions/clientes-ranking.js`
- Modify: `netlify.toml`

**Interfaces:**
- Consumes: `buildRanking` de `../../lib/clientes-ranking-core.js` (Task 1).
- Produces: endpoint HTTP `GET /api/clientes-ranking?since=N&until=N` em produção, consumido pela Task 4.

- [ ] **Step 1: Escrever a function**

```js
const { buildRanking } = require('../../lib/clientes-ranking-core');

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Content-Type': 'application/json',
};

exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 204,
      headers: { ...CORS, 'Access-Control-Allow-Methods': 'GET,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' },
      body: '',
    };
  }

  const apiKey    = process.env.FRAPPE_API_KEY;
  const apiSecret = process.env.FRAPPE_API_SECRET;
  if (!apiKey || !apiSecret) {
    return { statusCode: 503, headers: CORS, body: JSON.stringify({ error: 'Frappe not configured' }) };
  }

  const since = parseInt(event.queryStringParameters?.since, 10);
  const until = parseInt(event.queryStringParameters?.until, 10);
  if (!since || !until) {
    return { statusCode: 400, headers: CORS, body: JSON.stringify({ error: 'since/until obrigatorios' }) };
  }

  try {
    const result = await buildRanking({ since, until, apiKey, apiSecret });
    return { statusCode: 200, headers: CORS, body: JSON.stringify(result) };
  } catch (e) {
    return { statusCode: 502, headers: CORS, body: JSON.stringify({ error: e.message }) };
  }
};
```

- [ ] **Step 2: Verificar a sintaxe e o handler sem precisar do netlify-cli**

Não há `netlify-cli` instalado neste projeto — rode o handler direto via Node, simulando o `event`:

```bash
export FRAPPE_API_KEY=8b59db66515b51e
export FRAPPE_API_SECRET=3a0a3c2843d7cfe
node -e "
const { handler } = require('./netlify/functions/clientes-ranking.js');
const now = Math.floor(Date.now()/1000);
handler({ httpMethod: 'GET', queryStringParameters: { since: String(now - 7*24*3600), until: String(now) } })
  .then(r => { console.log('status', r.statusCode); console.log(JSON.parse(r.body).clientes?.slice(0,3)); })
  .catch(e => { console.error(e); process.exit(1); });
"
```

Esperado: `status 200` e os 3 primeiros clientes do ranking impressos.

- [ ] **Step 3: Testar o caso sem credencial configurada**

```bash
node -e "
const { handler } = require('./netlify/functions/clientes-ranking.js');
delete process.env.FRAPPE_API_KEY;
handler({ httpMethod: 'GET', queryStringParameters: { since: '1', until: '2' } })
  .then(r => console.log('status', r.statusCode, r.body));
"
```

Esperado: `status 503` e corpo `{"error":"Frappe not configured"}`.

- [ ] **Step 4: Adicionar o redirect no `netlify.toml`**

Encontre:

```toml
[[redirects]]
  from = "/api/config"
  to = "/.netlify/functions/config"
  status = 200
  force = true

[[redirects]]
  from = "/api/*"
  to = "https://nxticket.com.br/api/:splat"
  status = 200
  force = true
```

Substitua por (o redirect novo entra **antes** do catch-all `/api/*` — ordem importa no Netlify, a primeira regra que bater vence):

```toml
[[redirects]]
  from = "/api/config"
  to = "/.netlify/functions/config"
  status = 200
  force = true

[[redirects]]
  from = "/api/clientes-ranking"
  to = "/.netlify/functions/clientes-ranking"
  status = 200
  force = true

[[redirects]]
  from = "/api/*"
  to = "https://nxticket.com.br/api/:splat"
  status = 200
  force = true
```

- [ ] **Step 5: Commit**

```bash
git status --short
git add netlify/functions/clientes-ranking.js netlify.toml
git commit netlify/functions/clientes-ranking.js netlify.toml -m "feat(crm): netlify function do ranking de clientes

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 3: Rota local no `dev-server.js`

**Files:**
- Modify: `dev-server.js`

**Interfaces:**
- Consumes: `buildRanking` de `./lib/clientes-ranking-core.js` (Task 1).
- Produces: endpoint HTTP local `GET /api/clientes-ranking?since=N&until=N` em `http://localhost:8888`, usado pela verificação ao vivo da Task 4 e 5.

- [ ] **Step 1: Adicionar a rota, antes do proxy genérico**

Encontre, no topo do arquivo:

```js
const http  = require('http');
const https = require('https');
const fs    = require('fs');
const path  = require('path');
```

Substitua por:

```js
const http  = require('http');
const https = require('https');
const fs    = require('fs');
const path  = require('path');
const { buildRanking } = require('./lib/clientes-ranking-core');
```

Encontre:

```js
http.createServer((req, res) => {
  /* proxy /api/* → nxticket.com.br/api/* */
  if (req.url.startsWith('/api/')) {
```

Substitua por (o branch novo entra **antes** do proxy genérico — `/api/clientes-ranking` também começa com `/api/`, precisa ser capturado primeiro):

```js
http.createServer((req, res) => {
  /* ranking de clientes (Frappe) — nao e proxy, resolve local */
  if (req.url.startsWith('/api/clientes-ranking')) {
    const u = new URL(req.url, 'http://localhost');
    const since = parseInt(u.searchParams.get('since'), 10);
    const until = parseInt(u.searchParams.get('until'), 10);
    const apiKey    = process.env.FRAPPE_API_KEY;
    const apiSecret = process.env.FRAPPE_API_SECRET;
    if (!apiKey || !apiSecret) {
      res.writeHead(503, { 'content-type': 'application/json', 'access-control-allow-origin': '*' });
      res.end(JSON.stringify({ error: 'Frappe not configured' }));
      return;
    }
    if (!since || !until) {
      res.writeHead(400, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ error: 'since/until obrigatorios' }));
      return;
    }
    buildRanking({ since, until, apiKey, apiSecret })
      .then(result => {
        res.writeHead(200, { 'content-type': 'application/json', 'access-control-allow-origin': '*' });
        res.end(JSON.stringify(result));
      })
      .catch(err => {
        res.writeHead(502, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      });
    return;
  }

  /* proxy /api/* → nxticket.com.br/api/* */
  if (req.url.startsWith('/api/')) {
```

- [ ] **Step 2: Rodar e testar ao vivo**

```bash
export FRAPPE_API_KEY=8b59db66515b51e
export FRAPPE_API_SECRET=3a0a3c2843d7cfe
node dev-server.js &
sleep 1
SINCE=$(( $(date +%s) - 7*24*3600 ))
UNTIL=$(date +%s)
curl -s "http://localhost:8888/api/clientes-ranking?since=$SINCE&until=$UNTIL" | node -e "
let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{
  const j = JSON.parse(d);
  console.log('clientes:', j.clientes?.length, 'semCliente:', j.semCliente, 'truncado:', j.truncado);
});
"
```

Esperado: imprime uma contagem de clientes > 0 e `semCliente` > 0, sem erro.

- [ ] **Step 3: Confirmar que o proxy antigo do Chatwoot continua funcionando (regressão)**

```bash
curl -s -o /dev/null -w "HTTP_CODE=%{http_code}\n" "http://localhost:8888/api/v1/accounts/1/agents" -H "api_access_token: rzpghGjyG4cDVYg4tNjSpJBD"
```

Esperado: `HTTP_CODE=200` — confirma que a rota nova não quebrou o proxy genérico que já existia.

- [ ] **Step 4: Commit**

```bash
git status --short
git add dev-server.js
git commit dev-server.js -m "feat(crm): rota local do ranking de clientes no dev-server

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 4: Card novo na aba Análise

**Files:**
- Modify: `index.html` (CSS perto de `.an-team-table`, ~linha 198-203; HTML dentro de `#graficos-page`, ~linha 920-932; JS: globais perto de `_chartTeamCache`, `fetchChartData()`, `renderCharts()`)

**Interfaces:**
- Consumes: `fetch('/api/clientes-ranking?since=N&until=N')` (Tasks 2/3), `esc()`, `harnessFmtPeriodo(since,until)` (já existem no arquivo).
- Produces: nada consumido por outra task — é o último elo da cadeia.

- [ ] **Step 1: CSS da linha "sem cliente"**

Encontre:

```css
.an-team-table tr:last-child td { border:none; }
```

Logo depois, adicione:

```css
.an-rank-sem-cliente td { color:var(--text3); font-style:italic; }
```

- [ ] **Step 2: HTML do card novo**

Encontre:

```html
  <div class="chart-card chart-full" id="an-equipes-card">
    <div class="chart-card-hdr">
      <div>
        <div class="chart-card-title">Contribuição por equipe</div>
        <div class="chart-card-sub" id="an-equipes-sub">Ordenado por volume atendido no último mês do período</div>
      </div>
      <span id="an-equipes-cobertura" style="font-size:10px;color:var(--text3)"></span>
    </div>
    <div id="an-equipes-wrap"></div>
  </div>

</div>
```

Substitua por:

```html
  <div class="chart-card chart-full" id="an-equipes-card">
    <div class="chart-card-hdr">
      <div>
        <div class="chart-card-title">Contribuição por equipe</div>
        <div class="chart-card-sub" id="an-equipes-sub">Ordenado por volume atendido no último mês do período</div>
      </div>
      <span id="an-equipes-cobertura" style="font-size:10px;color:var(--text3)"></span>
    </div>
    <div id="an-equipes-wrap"></div>
  </div>

  <!-- ── 5 · CLIENTES QUE MAIS ABRIRAM CONVERSAS ── -->
  <div class="section-divider" style="margin-top:16px"><span class="section-divider-label">5 · Clientes que mais abriram conversas</span></div>
  <div class="chart-card chart-full" id="an-clientes-card">
    <div class="chart-card-hdr">
      <div>
        <div class="chart-card-title">Clientes que mais abriram conversas</div>
        <div class="chart-card-sub" id="an-clientes-sub">—</div>
      </div>
    </div>
    <div id="an-clientes-wrap"></div>
  </div>

</div>
```

- [ ] **Step 3: Globais e função de busca**

Encontre:

```js
let _chartTeamCache  = {};   /* {`${id}:${since}:${until}`: {data, ts}} — TTL 5min */
```

Logo depois, adicione:

```js
let _clientesRankingData  = null;
let _clientesRankingCache = {}; /* {`${since}:${until}`: {data, ts}} — TTL 5min */
```

Encontre `async function fetchTeamComparison(periods) {` (função inteira já existe) e, logo **depois** do fechamento dessa função (antes da próxima função no arquivo), adicione:

```js
async function fetchClientesRanking(periods) {
  const since = periods[0].since;
  const until = periods[periods.length - 1].until;
  const key = `${since}:${until}`;
  const now = Date.now(), TTL = 5 * 60 * 1000;
  if (_clientesRankingCache[key] && now - _clientesRankingCache[key].ts < TTL) return _clientesRankingCache[key].data;

  try {
    const res = await fetch(`/api/clientes-ranking?since=${since}&until=${until}`);
    const data = await res.json();
    if (!res.ok) data._erro = data.error || `HTTP ${res.status}`;
    _clientesRankingCache[key] = { data, ts: now };
    return data;
  } catch (e) {
    return { _erro: e.message };
  }
}
```

- [ ] **Step 4: Ligar a busca em `fetchChartData()`**

Encontre:

```js
    _teamCompData = await fetchTeamComparison(periods).catch(() => null);
    renderCharts();
```

Substitua por:

```js
    _teamCompData = await fetchTeamComparison(periods).catch(() => null);
    _clientesRankingData = await fetchClientesRanking(periods).catch(() => null);
    renderCharts();
```

- [ ] **Step 5: Função de renderização**

Encontre o final de `function renderAnaliseEquipes() {` (função inteira já existe) e, logo **depois** do fechamento dessa função, adicione:

```js
function renderAnaliseClientesRanking(data) {
  const wrap = document.getElementById('an-clientes-wrap');
  const sub  = document.getElementById('an-clientes-sub');
  if (!wrap) return;

  if (!data || data._erro === 'Frappe not configured') {
    wrap.innerHTML = '<div class="chart-na">Integração com o CRM ainda não configurada</div>';
    if (sub) sub.textContent = '';
    return;
  }
  if (!data || data._erro) {
    wrap.innerHTML = '<div class="chart-na">Não consegui carregar o ranking agora</div>';
    if (sub) sub.textContent = '';
    return;
  }

  const { clientes, semCliente, truncado, periodo } = data;
  if (sub) sub.textContent = `${harnessFmtPeriodo(periodo.since, periodo.until)}${truncado ? ' · amostra parcial' : ''}`;

  if (!clientes.length) {
    wrap.innerHTML = '<div class="chart-na">Nenhum dado no período</div>';
    return;
  }

  wrap.innerHTML = `
    <table class="an-team-table">
      <thead><tr><th>#</th><th>Cliente</th><th>Conversas</th></tr></thead>
      <tbody>
        ${clientes.map((c, i) => `
          <tr>
            <td>${i + 1}</td>
            <td>${esc(c.nome)}</td>
            <td>${c.total.toLocaleString('pt-BR')}</td>
          </tr>`).join('')}
        ${semCliente > 0 ? `
          <tr class="an-rank-sem-cliente" title="Conversas do Chatwoot sem cadastro de cliente correspondente no CRM">
            <td></td><td>Sem cliente vinculado</td><td>${semCliente.toLocaleString('pt-BR')}</td>
          </tr>` : ''}
      </tbody>
    </table>`;
}
```

- [ ] **Step 6: Chamar a renderização em `renderCharts()`**

Encontre:

```js
  renderAnaliseEquipes();
```

Substitua por:

```js
  renderAnaliseEquipes();
  renderAnaliseClientesRanking(_clientesRankingData);
```

- [ ] **Step 7: Verificar ao vivo**

Via a skill `verify`, com as variáveis de ambiente do Frappe exportadas antes de subir o `dev-server.js` (`export FRAPPE_API_KEY=... FRAPPE_API_SECRET=...`, mesma chave das tasks anteriores):

1. Abra a aba Análise, espere os cards carregarem.
2. Confirme que o card "Clientes que mais abriram conversas" aparece, com uma tabela de até 15 linhas + a linha final "Sem cliente vinculado" (se `semCliente > 0`).
3. Troque o seletor de período da aba (`#chart-period-sel`) pra outro valor (ex: de "6 meses" pra "3 meses") e confirme que o card atualiza os números (não fica estático) e o `chart-card-sub` muda a data mostrada.
4. No console da página, rode `fetch('/api/clientes-ranking?since=...&until=...').then(r=>r.json()).then(console.log)` com o mesmo `since`/`until` que o card está usando naquele momento, e confirme que os 3 primeiros nomes/contagens batem com o que a tabela mostra.

- [ ] **Step 8: Commit**

```bash
git status --short
git add index.html
git commit index.html -m "feat(crm): card de ranking de clientes na aba Analise

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 5: Aceite final (sem credencial configurada + regressão geral)

**Files:**
- Modify: nenhum, a menos que o aceite ache uma lacuna real.

**Interfaces:**
- Consumes: tudo que as Tasks 1-4 produziram.

- [ ] **Step 1: Testar o estado "sem credencial configurada" de ponta a ponta**

```bash
# sem exportar FRAPPE_API_KEY/FRAPPE_API_SECRET desta vez
node dev-server.js &
sleep 1
```

Abra o dashboard, vá pra aba Análise, confirme que o card mostra exatamente **"Integração com o CRM ainda não configurada"** (não um erro genérico, não uma tela em branco, não um erro no console que quebre o resto da aba).

- [ ] **Step 2: Confirmar que nada mais na aba Análise quebrou**

Com o card em estado "não configurada", confirme que os outros cards da aba (Volume, Resolvidos, 1ª resposta, Até resolver, CSAT, Contribuição por equipe) continuam carregando normalmente — a falha do card novo não pode travar a renderização dos outros.

- [ ] **Step 3: Rodar de novo com a credencial, confirmar que volta ao normal**

```bash
export FRAPPE_API_KEY=8b59db66515b51e
export FRAPPE_API_SECRET=3a0a3c2843d7cfe
```

Recarregue a página, confirme que o card volta a mostrar o ranking de verdade.

- [ ] **Step 4: Corrigir qualquer lacuna real encontrada**

Se algo falhar, pare e descreva exatamente o que encontrou (a tela, a mensagem de erro, o que o plano esperava) antes de decidir o fix — mesmo padrão de sempre: fix mais estreito possível, re-testar a mesma coisa que falhou, depois re-testar pelo menos um passo de cada task anterior pra garantir que nada quebrou.

- [ ] **Step 5: Commit (só se houve fix)**

```bash
git status --short
git commit index.html -m "fix(crm): lacunas do ranking de clientes achadas na validacao de aceite

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

Se nenhum fix foi necessário, não crie um commit vazio — apenas reporte que o aceite passou de primeira.
