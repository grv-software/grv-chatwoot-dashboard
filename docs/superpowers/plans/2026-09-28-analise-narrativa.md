# Aba Análise — Narrativa de Desempenho: Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformar a aba Análise de uma grade de 11 cards desordenados numa leitura em quatro capítulos sobre a evolução da equipe, removendo os 6 cards ao vivo/duplicados e acrescentando o capítulo de satisfação do cliente.

**Architecture:** Arquivo único `index.html`. A ordem é CSS (Task 1) → remoções (Task 2) → abertura (Task 3) → capítulos (Task 4) → dados de CSAT (Task 5) → cards de CSAT (Task 6) → tabela de equipes (Task 7). Cada task deixa a aba funcionando e é commitável sozinha. Nenhuma lógica de dados históricos muda — `fetchChartData`, `_chartData` e `_chartTrendBase` permanecem como estão.

**Tech Stack:** HTML/CSS/JS puro, Chart.js 4, arquivo único `index.html`, branch `alteracoes`.

**Spec:** `docs/superpowers/specs/2026-09-28-analise-narrativa-design.md`

## Global Constraints

- Arquivo único: `index.html` — todas as edições aqui. Branch `alteracoes`, nunca `main`.
- **Não existe suíte de testes neste projeto.** O ciclo de verificação de cada task é dirigir o app de verdade pela skill `verify` do repo (`.claude/skills/verify/SKILL.md`): sobe `dev-server.js` na 8888, Chrome headless em porta CDP isolada, navega até Análise e lê o estado interno.
- O proxy de `dev-server.js` aponta para **nxticket.com.br, a instância de produção do cliente**. Somente GET. Nunca dirigir fluxo que crie ou altere dados.
- `window._charts` é `undefined` — as globais são `let` de topo de script. Avaliar o nome cru (`_charts`, `_chartData`, `_chartCsat`).
- Token de teste vai em `localStorage` antes da carga: `grv_token` = `rzpghGjyG4cDVYg4tNjSpJBD`, `grv_account` = `1`.
- A aba Análise leva 20–30s para carregar (6 meses × ~15 inboxes). Sempre fazer poll de estado, nunca `sleep` fixo.
- Classes `.am-csat-row`, `.am-csat-stars`, `.am-csat-contact`, `.am-csat-msg`, `.am-csat-date`, `.am-csat-link` e `.csat-row-bad` são **compartilhadas com o modal da aba Agentes**. Reutilizar, nunca renomear.
- `_totalPending` continua em uso pelo KPI "Em aberto agora" do Painel. Não remover.
- Filtro de equipe (`_chartTeamFilter`, incluindo `SAG_FILTER_ID`) continua valendo para toda a aba.

---

### Task 1: CSS — classes da nova narrativa

**Files:**
- Modify: `index.html` — inserir após a linha 178 (`.auth-limited .chart-auth-overlay { display:flex; }`), antes de `#kpi-filter-note.auth-warn`

**Interfaces:**
- Consumes: nada.
- Produces: `.an-hero*`, `.an-dist*`, `.an-coment`, `.an-team-table` — usadas pelas Tasks 3, 6 e 7.

- [ ] **Step 1: Inserir o bloco de CSS novo**

Localizar a linha `.auth-limited .chart-auth-overlay { display:flex; }` e inserir **logo depois** dela:

```css
/* ── ANÁLISE — narrativa ──────────────────────────────── */
.an-hero { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:10px; }
@media (max-width:900px) { .an-hero { grid-template-columns:1fr 1fr; } }
.an-hero-tile { background:var(--bg2); border:1px solid var(--border); border-radius:8px; padding:16px 18px; }
.an-hero-val { font-size:32px; font-weight:800; line-height:1.05; letter-spacing:-.5px; font-variant-numeric:tabular-nums; color:var(--text); }
.an-hero-lbl { font-size:12px; color:var(--text2); margin-top:4px; }
.an-hero-sub { font-size:11px; color:var(--text3); margin-top:2px; }
.an-hero-trend { font-size:12px; font-weight:700; margin-top:8px; display:block; }
.an-sub { font-size:12px; color:var(--text3); margin-top:2px; }

.an-dist { display:flex; flex-direction:column; gap:8px; margin-top:14px; }
.an-dist-row { display:grid; grid-template-columns:58px 1fr 52px; align-items:center; gap:10px; font-size:12px; }
.an-dist-star { letter-spacing:1px; white-space:nowrap; font-size:13px; }
.an-dist-bar { height:18px; border-radius:4px; background:var(--bg3); overflow:hidden; }
.an-dist-fill { height:100%; border-radius:4px; transition:width .3s ease-out; }
.an-dist-num { text-align:right; font-variant-numeric:tabular-nums; color:var(--text2); }

.an-coment { max-height:320px; overflow-y:auto; margin-top:12px; }

.an-team-table { width:100%; border-collapse:collapse; font-size:12px; margin-top:12px; }
.an-team-table th { background:var(--bg3); color:var(--text2); font-size:11px; font-weight:600; padding:8px 10px; border-bottom:2px solid var(--border); text-align:right; }
.an-team-table th:first-child { text-align:left; }
.an-team-table td { padding:8px 10px; border-bottom:1px solid var(--border); font-variant-numeric:tabular-nums; text-align:right; color:var(--text2); }
.an-team-table td:first-child { text-align:left; font-weight:600; color:var(--text); }
.an-team-table tr:last-child td { border:none; }

@media (prefers-reduced-motion:reduce) { .an-dist-fill { transition:none; } }
```

- [ ] **Step 2: Verificar que o CSS é válido e a página segue abrindo**

```bash
node -e "const fs=require('fs');const m=fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*)<\/script>/);fs.writeFileSync(process.env.TMP+'/c.js',m[1]);"
node --check "$TMP/c.js" && echo "JS intacto"
```
Esperado: `JS intacto` (o CSS não toca JS, mas confirma que nada foi cortado fora do lugar).

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "style(analise): classes da narrativa — hero, distribuicao, tabela de equipes"
```

---

### Task 2: Remover os cinco cards ao vivo e o banner de amostra

Remove: donut de canal, eficiência (mensagens/conversa), pico de horário, fila atual, carga por agente, e o `#chart-sample-warn`. O comparativo de equipes fica para a Task 7.

**Files:**
- Modify: `index.html` — HTML linha 742 (`#chart-sample-warn`) e os cards dentro de `#graficos-page`; JS `renderCharts()` blocos 2, 6, 8(carga), 9, 10 e o bloco de `chartPending`/`sampleWarnEl`

**Interfaces:**
- Consumes: nada.
- Produces: `#graficos-page` com 5 cards (volume, tma, tmr, fcr, teams) e `renderCharts()` sem referência a `chart-channel`, `chart-msg`, `chart-peak`, `chart-status`, `chart-agents`.

- [ ] **Step 1: Remover o span do banner de amostra parcial**

Deletar a linha inteira:
```html
    <span id="chart-sample-warn" style="display:none;font-size:10px;color:var(--yellow);background:rgba(234,179,8,.08);border:1px solid rgba(234,179,8,.25);border-radius:4px;padding:2px 7px"></span>
```

- [ ] **Step 2: Remover o card do donut de canal**

Deletar exatamente este bloco (segundo card da `chart-grid-2` da seção Volume):

```html
    <div class="chart-card">
      <div class="metric-card">
        <div><div class="metric-value" id="mv-channel" style="font-size:17px;word-break:break-word">—</div><div class="metric-label">canal com maior volume agora</div></div>
        <span class="badge-live">Ao vivo</span>
      </div>
      <div class="chart-card-hdr" style="margin-top:10px">
        <div><div class="chart-card-title">De onde vêm os atendimentos?</div><div class="chart-card-sub">Distribuição por canal · conversas abertas agora (não representa o período histórico)</div></div>
      </div>
      <div class="chart-wrap"><canvas id="chart-channel"></canvas></div>
    </div>
```

A `chart-grid-2` fica com um card só (o de Volume) até a Task 4 trazer o de resolução para cá.

- [ ] **Step 3: Remover o card de eficiência (mensagens por conversa)**

Deletar exatamente este bloco:

```html
    <div class="chart-card">
      <div class="metric-card">
        <div><div class="metric-value" id="mv-msg">—</div><div class="metric-label">mensagens por conversa este mês</div></div>
        <span class="metric-trend-up" id="mt-msg"></span>
      </div>
      <div class="chart-card-hdr" style="margin-top:10px">
        <div><div class="chart-card-title">Eficiência do Atendimento</div><div class="chart-card-sub">Média de mensagens trocadas por atendimento · Quanto menor, melhor · Meta: <span id="sla-msg-label">10</span> mensagens</div></div>
      </div>
      <div class="chart-wrap"><canvas id="chart-msg"></canvas></div>
      <div class="chart-auth-overlay"><span style="font-size:18px">🔒</span><span style="font-size:12px;color:var(--text3)">Dados históricos requerem permissão de Administrador no Chatwoot<br>(Perfil → Função → Administrador).<br>Os dados ao vivo continuam disponíveis.</span></div>
    </div>
```

- [ ] **Step 4: Remover carga por agente, pico e fila**

Deletar exatamente este trecho contínuo — vai do divisor `Agentes` até o `</div>` que fecha a `chart-grid-2` do Operacional. **Atenção:** o `</div>` final da página (que fecha `#graficos-page`) vem logo depois e **não** deve ser removido.

```html
  <div class="section-divider" style="margin-top:16px"><span class="section-divider-label">Agentes</span></div>
  <div class="chart-card chart-full">
    <div class="chart-card-hdr">
      <div><div class="chart-card-title">Carga por agente agora</div><div class="chart-card-sub">Conversas abertas por atendente</div></div>
      <span class="badge-live">Ao vivo</span>
    </div>
    <div class="chart-wrap" style="height:280px"><canvas id="chart-agents"></canvas></div>
  </div>

  <!-- ── OPERACIONAL ── -->
  <div class="section-divider" style="margin-top:16px"><span class="section-divider-label">Operacional</span></div>
  <div class="chart-grid-2">
    <div class="chart-card">
      <div class="chart-card-hdr">
        <div><div class="chart-card-title">Pico de Horário</div><div class="chart-card-sub">Horários com mais atendimentos agora</div></div>
        <span class="badge-live">Ao vivo</span>
      </div>
      <div class="chart-wrap"><canvas id="chart-peak"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-card-hdr">
        <div><div class="chart-card-title">Fila Atual</div><div class="chart-card-sub">Conversas em aberto agora, por status de fila · Taxa de Resolução do período está na seção Velocidade</div></div>
        <span class="badge-live">Ao vivo</span>
      </div>
      <div class="chart-wrap" style="height:200px"><canvas id="chart-status"></canvas></div>
      <div class="chart-legend">
        <span class="chart-legend-item"><span class="chart-legend-dot" style="background:#ef4444"></span>Abertas</span>
        <span class="chart-legend-item"><span class="chart-legend-dot" style="background:#eab308"></span>Pendentes</span>
      </div>
    </div>
  </div>
```

- [ ] **Step 5: Remover `chartPending` e o bloco do banner em `renderCharts()`**

Localizar e deletar este bloco inteiro (logo após a definição de `chartConvs`):

```js
  const chartPending = (_chartTeamFilter && _chartTeamFilter.size > 0)
    ? _pendingConvs.filter(cv => convMatchesFilter(cv, _chartTeamFilter))
    : _pendingConvs;

  const sampleWarnEl = document.getElementById('chart-sample-warn');
  if (sampleWarnEl) {
    const openTruncated    = _totalOpen    > _rawConvs.length;
    const pendingTruncated = _totalPending > _pendingConvs.length;
    if (openTruncated || pendingTruncated) {
      const parts = [];
      if (openTruncated)    parts.push(`${_rawConvs.length} de ${_totalOpen} abertas`);
      if (pendingTruncated) parts.push(`${_pendingConvs.length} de ${_totalPending} pendentes`);
      sampleWarnEl.textContent = `⚠ Amostra parcial nos cards "Ao vivo" (canal, fila, pico, carga por agente): ${parts.join(' · ')}`;
      sampleWarnEl.style.display = '';
    } else {
      sampleWarnEl.textContent = '';
      sampleWarnEl.style.display = 'none';
    }
  }
```

- [ ] **Step 6: Remover os blocos de render dos cards excluídos**

Deletar, em `renderCharts()`, os blocos delimitados por estes comentários (cada bloco vai do comentário até o `}` que fecha o escopo `{ ... }` logo abaixo dele):
- `/* ── 2. VOLUME POR CANAL ── */`
- `/* ── 6. EFICIÊNCIA — MENSAGENS POR CONVERSA ── */`
- `/* ── 8. CARGA POR AGENTE ── */`
- `/* ── 9. PICO DE HORÁRIO ── */`
- `/* ── 10. STATUS DAS CONVERSAS (fila ao vivo — abertas vs pendentes) ── */`

Cada um começa com `destroyChart('<id>')`. Após a remoção, `renderCharts()` deve conter apenas os blocos 1 (vol), 3 (tma), 4 (tmr), 5 (fcr), 7 (tmr-team) e 8 (comparativo equipes).

- [ ] **Step 7: Verificar sintaxe**

```bash
node -e "const fs=require('fs');const m=fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*)<\/script>/);fs.writeFileSync(process.env.TMP+'/c.js',m[1]);"
node --check "$TMP/c.js" && echo OK
```
Esperado: `OK`.

- [ ] **Step 8: Dirigir o app e confirmar que sobraram exatamente os charts esperados**

Subir conforme a skill `verify` e avaliar na página:
```js
Object.keys(_charts)
```
Esperado: apenas `vol`, `tma`, `tmr`, `fcr`, `tmr-team`, `teams`. **Não pode** conter `channel`, `msg`, `peak`, `status`, `agents`.

E confirmar a contagem de canvas **dentro da aba** — o seletor global pega 7, porque o modal da aba
Agentes tem um canvas próprio (`am-chart`) fora de `#graficos-page`:
```js
document.querySelectorAll('#graficos-page canvas').length
```
Esperado: 6.

Aproveite para remover o `const chartConvs` do topo de `renderCharts()` — ele filtrava conversas
abertas por equipe e só servia aos cards de canal, fila, pico e carga por agente. Sem eles, fica
órfão.

- [ ] **Step 9: Commit**

```bash
git add index.html
git commit -m "refactor(analise): remove cards ao vivo — canal, eficiencia, pico, fila e carga por agente"
```

---

### Task 3: Cabeçalho com o período e faixa de abertura

**Files:**
- Modify: `index.html` — `<div class="chart-hdr">` de `#graficos-page`; HTML após `#chart-loading`; `fetchChartData()` (guardar a janela do baseline); nova função `renderAnaliseHero()` + chamada em `renderCharts()`

**Interfaces:**
- Consumes: `.an-hero*`, `.an-sub` (Task 1); `_chartData`, `_chartTrendBase`, `metricTrend()`, `fmtSec()` (já existentes).
- Produces: `renderAnaliseHero(n, trendPrev)`; `_chartTrendBase` passa a carregar também `since` e `until`; ids `an-periodo-label`, `an-hero-entraram`, `an-hero-resolvidos`, `an-hero-tmr`, `an-hero-csat` e seus sufixos `-trend`/`-sub` — os dois últimos consumidos pela Task 6.

- [ ] **Step 1: Guardar a janela do baseline junto com os números**

`_chartTrendBase` hoje recebe só a resposta da API, que não traz `since`/`until`. O cabeçalho precisa
dessas datas para declarar contra o que está comparando. Em `fetchChartData()`, substituir:

```js
    _chartTrendBase = baseline;
```

por:

```js
    _chartTrendBase = baseline ? { ...baseline, since: trendBase.since, until: trendBase.until } : null;
```

- [ ] **Step 2: Fazer o cabeçalho declarar o período**

Substituir, no `<div class="chart-hdr">` de `#graficos-page`:

```html
    <h2>Análise</h2>
```

por:

```html
    <div>
      <h2 style="margin:0">Análise</h2>
      <div class="an-sub" id="an-periodo-label"></div>
    </div>
```

E remover o texto genérico do fim do cabeçalho, que essa linha nova torna redundante — substituir:

```html
    <span style="font-size:10px;color:var(--text3);margin-left:auto">Período e filtros independentes do painel principal</span>
```

por:

```html
    <span style="margin-left:auto"></span>
```

- [ ] **Step 3: Inserir o HTML da faixa de abertura**

Logo após o fechamento do `<div id="chart-loading">…</div>`, inserir:

```html
  <!-- ABERTURA -->
  <div class="an-hero">
    <div class="an-hero-tile">
      <div class="an-hero-val" id="an-hero-entraram">—</div>
      <div class="an-hero-lbl">entraram</div>
      <span class="an-hero-trend" id="an-hero-entraram-trend"></span>
    </div>
    <div class="an-hero-tile">
      <div class="an-hero-val" id="an-hero-resolvidos">—</div>
      <div class="an-hero-lbl">resolvidos</div>
      <div class="an-hero-sub" id="an-hero-resolvidos-sub"></div>
      <span class="an-hero-trend" id="an-hero-resolvidos-trend"></span>
    </div>
    <div class="an-hero-tile">
      <div class="an-hero-val" id="an-hero-tmr">—</div>
      <div class="an-hero-lbl">até a 1ª resposta</div>
      <span class="an-hero-trend" id="an-hero-tmr-trend"></span>
    </div>
    <div class="an-hero-tile">
      <div class="an-hero-val" id="an-hero-csat">—</div>
      <div class="an-hero-lbl">aprovaram</div>
      <div class="an-hero-sub" id="an-hero-csat-sub"></div>
    </div>
  </div>
```

- [ ] **Step 4: Tirar `metricTrend()` de dentro de `renderCharts()`**

`metricTrend` hoje é uma function declaration **interna** de `renderCharts()`. `renderAnaliseHero`,
que fica no escopo de topo, não a enxergaria — daria `ReferenceError: metricTrend is not defined`
e a exceção abortaria `renderCharts()` inteiro, deixando a aba sem nenhum gráfico.

A função é pura (usa só os parâmetros e `document`), então subir de escopo é seguro. Recortar este
bloco de dentro de `renderCharts()`:

```js
  function metricTrend(elId, current, previous, invertGood) {
    const el = document.getElementById(elId);
    if (!el) return;
    el.className = '';
    if (current == null || previous == null || previous === 0) { el.textContent = ''; return; }
    const pct = Math.round(((current - previous) / previous) * 100);
    if (pct === 0) { el.textContent = ''; return; }
    const up   = pct > 0;
    const good = invertGood ? !up : up;
    el.className   = good ? 'metric-trend-up' : 'metric-trend-dn';
    el.textContent = `${up ? '▲' : '▼'} ${Math.abs(pct)}% vs mês passado`;
    el.title       = 'Comparado com o mesmo trecho decorrido do mês passado (não com o mês inteiro)';
  }
```

e colá-lo no escopo de topo, **antes** de `function renderCharts() {`, sem indentação:

```js
/* Seta de tendência de um número contra o mesmo trecho do mês anterior.
   Vive no topo porque a faixa de abertura também a usa. */
function metricTrend(elId, current, previous, invertGood) {
  const el = document.getElementById(elId);
  if (!el) return;
  el.className = '';
  if (current == null || previous == null || previous === 0) { el.textContent = ''; return; }
  const pct = Math.round(((current - previous) / previous) * 100);
  if (pct === 0) { el.textContent = ''; return; }
  const up   = pct > 0;
  const good = invertGood ? !up : up;
  el.className   = good ? 'metric-trend-up' : 'metric-trend-dn';
  el.textContent = `${up ? '▲' : '▼'} ${Math.abs(pct)}% vs mês passado`;
  el.title       = 'Comparado com o mesmo trecho decorrido do mês passado (não com o mês inteiro)';
}
```

As quatro chamadas existentes dentro de `renderCharts()` (`mt-vol`, `mt-tma`, `mt-tmr`, `mt-fcr`)
continuam funcionando sem alteração.

- [ ] **Step 5: Escrever `renderAnaliseHero()`**

Inserir **antes** de `function renderCharts() {`:

```js
/* Faixa de abertura da Análise — os quatro números do período */
function renderAnaliseHero(n, trendPrev) {
  const d = _chartData[n - 1] || {};
  const set = (id, txt) => { const el = document.getElementById(id); if (el) el.textContent = txt; };

  /* o cabeçalho declara o recorte e contra o que se compara */
  const perEl = document.getElementById('an-periodo-label');
  if (perEl) {
    const f = ts => new Date(ts * 1000).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
    const mes = d.fullLabel ? d.fullLabel.charAt(0).toUpperCase() + d.fullLabel.slice(1) : '';
    perEl.textContent = (mes && _chartTrendBase?.since)
      ? `${mes} · comparado com ${f(_chartTrendBase.since)} a ${f(_chartTrendBase.until)}`
      : mes;
  }

  const entraram   = d.conversations_count;
  const resolvidos = d.resolutions_count;
  set('an-hero-entraram',   entraram   != null ? entraram.toLocaleString('pt-BR')   : '—');
  set('an-hero-resolvidos', resolvidos != null ? resolvidos.toLocaleString('pt-BR') : '—');
  set('an-hero-tmr', fmtSec(d.avg_first_response_time));

  const taxa  = entraram > 0 && resolvidos != null ? Math.round(resolvidos / entraram * 100) : null;
  const subEl = document.getElementById('an-hero-resolvidos-sub');
  if (subEl) {
    subEl.textContent = taxa != null ? `${taxa}% do que entrou` : '';
    subEl.title = 'A API do Chatwoot conta como resolvida no período qualquer conversa fechada nessas datas, mesmo se foi aberta antes. Por isso pode passar de 100%.';
  }

  metricTrend('an-hero-entraram-trend',   entraram,   trendPrev('conversations_count'), false);
  metricTrend('an-hero-resolvidos-trend', resolvidos, trendPrev('resolutions_count'),   false);
  metricTrend('an-hero-tmr-trend',        d.avg_first_response_time, trendPrev('avg_first_response_time'), true);
}
```

- [ ] **Step 6: Chamar a função em `renderCharts()`**

Localizar, dentro de `renderCharts()`, a linha:
```js
  const trendPrev = field => _chartTrendBase ? _chartTrendBase[field] : _chartData[n - 2]?.[field];
```
e inserir **logo depois** dela:
```js
  renderAnaliseHero(n, trendPrev);
```

- [ ] **Step 7: Verificar sintaxe**

```bash
node -e "const fs=require('fs');const m=fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*)<\/script>/);fs.writeFileSync(process.env.TMP+'/c.js',m[1]);"
node --check "$TMP/c.js" && echo OK
```
Esperado: `OK`.

- [ ] **Step 8: Dirigir e conferir contra a API**

Na página, depois dos charts carregarem:
```js
JSON.stringify({
  periodo:    document.getElementById('an-periodo-label').textContent,
  entraram:   document.getElementById('an-hero-entraram').textContent,
  resolvidos: document.getElementById('an-hero-resolvidos').textContent,
  sub:        document.getElementById('an-hero-resolvidos-sub').textContent,
  tmr:        document.getElementById('an-hero-tmr').textContent,
  apiEntraram:   _chartData[_chartData.length-1].conversations_count,
  apiResolvidos: _chartData[_chartData.length-1].resolutions_count,
  baseTemJanela: !!(_chartTrendBase && _chartTrendBase.since)
})
```
Esperado: `periodo` no formato `Setembro de 2026 · comparado com 01/ago a 28/ago` (sem "Invalid Date");
`entraram` e `resolvidos` batendo exatamente com `apiEntraram`/`apiResolvidos` já formatados;
`sub` no formato `NN% do que entrou`; `tmr` como `45min` ou `1hr 20min`; `baseTemJanela:true`.

- [ ] **Step 9: Commit**

```bash
git add index.html
git commit -m "feat(analise): cabecalho declara o periodo e faixa de abertura com quatro numeros"
```

---
### Task 4: Reorganizar os quatro charts restantes em dois capítulos

**Files:**
- Modify: `index.html` — HTML de `#graficos-page` (divisores e ordem dos cards, subtítulos); JS bloco 5 (FCR) em `renderCharts()`

**Interfaces:**
- Consumes: cards sobreviventes da Task 2.
- Produces: estrutura de capítulos onde as Tasks 6 e 7 inserem os seus.

- [ ] **Step 1: Trocar o divisor "Volume" e montar o capítulo 1**

Substituir o divisor existente:
```html
  <div class="section-divider"><span class="section-divider-label">Volume</span></div>
```
por:
```html
  <div class="section-divider"><span class="section-divider-label">1 · Quanto absorvemos</span></div>
```

Garantir que a `chart-grid-2` seguinte contenha, nesta ordem, o card de **Volume de Atendimentos** e o card de **Taxa de Resolução** (hoje o de resolução está na seção Velocidade — movê-lo para cá).

- [ ] **Step 2: Trocar o divisor "Velocidade" e montar o capítulo 2**

Substituir:
```html
  <div class="section-divider" style="margin-top:16px"><span class="section-divider-label">Velocidade</span></div>
```
por:
```html
  <div class="section-divider" style="margin-top:16px"><span class="section-divider-label">2 · Com que velocidade</span></div>
```

A `chart-grid-2` deste capítulo fica com o card de **1ª resposta (TMR)** primeiro e o de **até resolver (TMA)** em seguida.

- [ ] **Step 3: Reescrever o cabeçalho do card de resolução**

Substituir o cabeçalho do card que contém `chart-fcr`:
```html
        <div><div class="chart-card-title">Taxa de Resolução</div><div class="chart-card-sub">Resolvidas ÷ abertas no período · Quanto maior, melhor · Meta: <span id="sla-fcr-label">85%</span> · <span title="A API do Chatwoot conta como &quot;resolvidas no período&quot; qualquer conversa fechada nessas datas, mesmo se foi aberta antes. Por isso o valor pode passar de 100% quando se resolve mais atendimentos antigos do que se abre de novos.">pode passar de 100% ⓘ</span></div></div>
```
por:
```html
        <div><div class="chart-card-title">Resolvidos no período</div><div class="chart-card-sub">Atendimentos encerrados a cada mês · Meta de taxa: <span id="sla-fcr-label">85%</span> <span title="A API do Chatwoot conta como resolvida no período qualquer conversa fechada nessas datas, mesmo se foi aberta antes. Por isso a taxa pode passar de 100%.">ⓘ</span></div></div>
```

E trocar o rótulo da métrica do card, de:
```html
        <div><div class="metric-value" id="mv-fcr">—</div><div class="metric-label">resolvidas este mês</div></div>
```
para:
```html
        <div><div class="metric-value" id="mv-fcr">—</div><div class="metric-label">resolvidos este mês</div></div>
```

- [ ] **Step 4: Fazer o card de resolução liderar com o número absoluto**

No bloco `/* ── 5. FCR ── */` de `renderCharts()`, substituir este trecho:

```js
    const last = fcrVals[n - 1];
    const baseConv = trendPrev('conversations_count') || 0, baseRes = trendPrev('resolutions_count') || 0;
    const prev = baseConv > 0 ? Math.round((baseRes / baseConv) * 100) : null;
    setMetric('mv-fcr', last != null ? `${last}%` : '—');
    metricTrend('mt-fcr', last, prev, false);
```

por:

```js
    const resolvAbs = _chartData[n - 1]?.resolutions_count;
    setMetric('mv-fcr', resolvAbs != null ? resolvAbs.toLocaleString('pt-BR') : '—');
    metricTrend('mt-fcr', resolvAbs, trendPrev('resolutions_count'), false);
```

As variáveis `last`, `baseConv`, `baseRes` e `prev` saem junto — depois desta troca ninguém mais as usa. O gráfico de barras continua plotando a **taxa** (`fcrVals`, definido logo acima e inalterado); só a métrica em destaque do card muda.

- [ ] **Step 5: Acrescentar a ressalva de volatilidade no card de tempo até resolver**

Substituir o subtítulo do card que contém `chart-tma`:
```html
        <div><div class="chart-card-title">Quanto tempo leva pra resolver? (TMA)</div><div class="chart-card-sub">Quanto menor, melhor · Meta SLA: <span id="sla-tma-label">8hr</span></div></div>
```
por:
```html
        <div><div class="chart-card-title">Até resolver</div><div class="chart-card-sub">Quanto menor, melhor · Meta: <span id="sla-tma-label">8hr</span><br><span style="color:var(--yellow)">Média sensível a atendimentos antigos encerrados em lote — saltos grandes entre períodos costumam ser limpeza de fila, não queda de desempenho.</span></div></div>
```

E o título do card de TMR, de `Velocidade de resposta (TMR)` para `Até a primeira resposta`.

- [ ] **Step 6: Dar `aria-label` aos quatro gráficos**

Um `<canvas>` não diz nada a leitor de tela. Acrescentar o atributo em cada um dos quatro:

```html
      <div class="chart-wrap"><canvas id="chart-vol" aria-label="Gráfico de barras: atendimentos abertos por mês no período selecionado"></canvas></div>
```
```html
      <div class="chart-wrap"><canvas id="chart-fcr" aria-label="Gráfico de barras: taxa de resolução por mês, comparada com a meta"></canvas></div>
```
```html
      <div class="chart-wrap"><canvas id="chart-tmr" aria-label="Gráfico de linha: tempo médio até a primeira resposta por mês, comparado com a meta"></canvas></div>
```
```html
      <div class="chart-wrap"><canvas id="chart-tma" aria-label="Gráfico de linha: tempo médio até resolver por mês, comparado com a meta"></canvas></div>
```

- [ ] **Step 7: Verificar sintaxe**

```bash
node -e "const fs=require('fs');const m=fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*)<\/script>/);fs.writeFileSync(process.env.TMP+'/c.js',m[1]);"
node --check "$TMP/c.js" && echo OK
```
Esperado: `OK`.

- [ ] **Step 8: Dirigir e conferir a ordem dos capítulos e o valor absoluto**

```js
JSON.stringify({
  capitulos: [...document.querySelectorAll('.section-divider-label')].map(e=>e.textContent),
  titulos:   [...document.querySelectorAll('.chart-card-title')].map(e=>e.textContent),
  fcrMetric: document.getElementById('mv-fcr').textContent,
  apiResolvidos: _chartData[_chartData.length-1].resolutions_count
})
```
Esperado: `capitulos` começa com `1 · Quanto absorvemos` e `2 · Com que velocidade`; `fcrMetric` igual a `apiResolvidos` formatado; nenhum título contém "TMA" ou "TMR".

- [ ] **Step 9: Commit**

```bash
git add index.html
git commit -m "feat(analise): capitulos 1 e 2, resolvidos lidera pelo absoluto, ressalva no tempo de resolucao"
```

---

### Task 5: Buscar as avaliações de CSAT do mês mais recente

Só dados. Nenhuma UI nesta task.

**Files:**
- Modify: `index.html` — declaração de estado junto a `_chartTrendBase`; nova função `fetchChartCsat()`; chamada em `fetchChartData()`

**Interfaces:**
- Consumes: `api()`, `cfg.account` (já existentes).
- Produces: `_chartCsat` no formato `{ rows: Array, truncado: boolean, since: number, until: number }` — consumido pela Task 6. `rows` são objetos da API com `rating` (number 1–5), `feedback_message` (string), `contact.name`, `conversation_id`, `created_at` (epoch **segundos**).

- [ ] **Step 1: Declarar o estado**

Localizar:
```js
let _chartTrendBase = null;   /* mesmo trecho decorrido do mês anterior — baseline das setas */
```
e inserir logo depois:
```js
let _chartCsat      = null;   /* {rows, truncado, since, until} — avaliações do mês mais recente */
let _chartCsatCache = {};     /* {`${since}:${until}`: {data, ts}} — TTL 5min */
const CSAT_MAX_PAGES = 40;    /* 40 × 25 = 1.000 avaliações; acima disso o card declara amostra */
```

- [ ] **Step 2: Escrever `fetchChartCsat()`**

Inserir logo **antes** de `async function fetchTeamComparison(periods) {`:

```js
/* Avaliações de CSAT de uma janela. Paginação limitada — quando o teto é
   atingido o card declara que está mostrando amostra, nunca trunca calado. */
async function fetchChartCsat(since, until) {
  const key = `${since}:${until}`;
  const now = Date.now(), TTL = 5 * 60 * 1000;
  if (_chartCsatCache[key] && now - _chartCsatCache[key].ts < TTL) return _chartCsatCache[key].data;

  const rows = [];
  let page = 1, truncado = false;
  while (page <= CSAT_MAX_PAGES) {
    const raw = await api(`/v1/accounts/${cfg.account}/csat_survey_responses?page=${page}&since=${since}&until=${until}&sort=-created_at`)
      .catch(() => null);
    if (!raw) break;
    const chunk = Array.isArray(raw) ? raw : Array.isArray(raw.data) ? raw.data : [];
    rows.push(...chunk);
    if (chunk.length < 25) break;
    if (page === CSAT_MAX_PAGES) truncado = true;
    page++;
  }

  const data = { rows, truncado, since, until };
  _chartCsatCache[key] = { data, ts: now };
  return data;
}
```

- [ ] **Step 3: Chamar na carga da aba**

Em `fetchChartData()`, localizar:
```js
    const [results, baseline] = await Promise.all([
      Promise.all(periods.map(fetchMonth)),
      fetchMonth(trendBase).catch(() => null)
    ]);
```
e substituir por:
```js
    const [results, baseline, csat] = await Promise.all([
      Promise.all(periods.map(fetchMonth)),
      fetchMonth(trendBase).catch(() => null),
      fetchChartCsat(cur.since, cur.until).catch(() => null)
    ]);
    _chartCsat = csat;
```

- [ ] **Step 4: Verificar sintaxe**

```bash
node -e "const fs=require('fs');const m=fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*)<\/script>/);fs.writeFileSync(process.env.TMP+'/c.js',m[1]);"
node --check "$TMP/c.js" && echo OK
```
Esperado: `OK`.

- [ ] **Step 5: Dirigir e conferir os dados contra a API**

Na página, depois dos charts carregarem:
```js
JSON.stringify({
  total: _chartCsat.rows.length,
  truncado: _chartCsat.truncado,
  janela: [new Date(_chartCsat.since*1000).toLocaleDateString('pt-BR'), new Date(_chartCsat.until*1000).toLocaleDateString('pt-BR')],
  positivas: _chartCsat.rows.filter(r=>r.rating>=4).length,
  comTexto: _chartCsat.rows.filter(r=>(r.feedback_message||'').trim()).length
})
```
Esperado para setembro/2026: `total` ≈ 468, `truncado:false`, janela `01/09/2026`–`28/09/2026`, `positivas` ≈ 432, `comTexto` ≈ 83. Números exatos variam com a data da execução; o que importa é `total > 0`, `truncado:false` e a janela bater com o mês mais recente de `_chartData`.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat(analise): busca avaliacoes de CSAT do mes mais recente com teto declarado"
```

---

### Task 6: Capítulo 3 — o que o cliente disse

**Files:**
- Modify: `index.html` — HTML do capítulo 3 em `#graficos-page`; nova função `renderAnaliseCsat()`; chamada em `renderCharts()`

**Interfaces:**
- Consumes: `_chartCsat` (Task 5); `.an-dist*`, `.an-coment` (Task 1); `.am-csat-*` e `.csat-row-bad` (compartilhadas com a aba Agentes); ids `an-hero-csat` / `an-hero-csat-sub` (Task 3); `esc()`, `cfg.account` (já existentes).
- Produces: `renderAnaliseCsat()`, `_csatAnaliseFiltro`.

- [ ] **Step 1: Declarar o estado do filtro**

Junto às demais globais da aba (logo após `const CSAT_MAX_PAGES = 40;`):
```js
let _csatAnaliseFiltro = 'todos';  /* 'todos' | 'criticos' */
```

- [ ] **Step 2: Inserir o HTML do capítulo 3**

Após a `chart-grid-2` do capítulo 2, inserir:

```html
  <!-- ── 3 · O QUE O CLIENTE DISSE ── -->
  <div class="section-divider" style="margin-top:16px"><span class="section-divider-label">3 · O que o cliente disse</span></div>
  <div class="chart-grid-2">
    <div class="chart-card">
      <div class="chart-card-hdr">
        <div>
          <div class="chart-card-title">Como avaliaram o atendimento</div>
          <div class="chart-card-sub" id="an-csat-periodo">—</div>
        </div>
      </div>
      <div class="an-dist" id="an-csat-dist"></div>
    </div>
    <div class="chart-card">
      <div class="chart-card-hdr">
        <div>
          <div class="chart-card-title">O que escreveram</div>
          <div class="chart-card-sub" id="an-csat-com-sub">—</div>
        </div>
        <div class="am-csat-filter" id="an-csat-filtro"></div>
      </div>
      <div class="an-coment" id="an-csat-coment"></div>
    </div>
  </div>
```

- [ ] **Step 3: Escrever `renderAnaliseCsat()`**

Inserir antes de `function renderCharts() {`:

```js
/* Capítulo 3 — distribuição de notas e os comentários escritos */
function renderAnaliseCsat() {
  const distEl = document.getElementById('an-csat-dist');
  const comEl  = document.getElementById('an-csat-coment');
  const perEl  = document.getElementById('an-csat-periodo');
  const subEl  = document.getElementById('an-csat-com-sub');
  const filEl  = document.getElementById('an-csat-filtro');
  if (!distEl || !comEl) return;

  const heroSet = (id, txt) => { const el = document.getElementById(id); if (el) el.textContent = txt; };
  const rows = _chartCsat?.rows || [];

  if (!rows.length) {
    const vazio = 'Ainda não há avaliações neste período.';
    distEl.innerHTML = `<div class="chart-na">${vazio}</div>`;
    comEl.innerHTML  = '';
    if (perEl) perEl.textContent = '';
    if (subEl) subEl.textContent = '';
    if (filEl) filEl.innerHTML = '';
    heroSet('an-hero-csat', '—');
    heroSet('an-hero-csat-sub', 'sem avaliações');
    return;
  }

  const mesLabel = new Date(_chartCsat.since * 1000)
    .toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
  const positivas = rows.filter(r => r.rating >= 4).length;
  const pct = Math.round(positivas / rows.length * 1000) / 10;

  heroSet('an-hero-csat', `${pct}%`.replace('.', ','));
  heroSet('an-hero-csat-sub', `de ${rows.length.toLocaleString('pt-BR')} avaliações`);

  if (perEl) {
    perEl.textContent = `${String(pct).replace('.', ',')}% aprovaram · ${rows.length.toLocaleString('pt-BR')} avaliações · ${mesLabel.charAt(0).toUpperCase() + mesLabel.slice(1)}`
      + (_chartCsat.truncado ? ` · amostra das ${CSAT_MAX_PAGES * 25} mais recentes` : '');
  }

  /* distribuição — contagem rotulada na própria linha, cor nunca sozinha */
  const CORES = { 5: 'var(--green)', 4: 'var(--green)', 3: 'var(--yellow)', 2: 'var(--red)', 1: 'var(--red)' };
  const maior = Math.max(...[5,4,3,2,1].map(n => rows.filter(r => r.rating === n).length), 1);
  distEl.innerHTML = [5,4,3,2,1].map(n => {
    const qtd = rows.filter(r => r.rating === n).length;
    const larg = Math.round(qtd / maior * 100);
    return `<div class="an-dist-row">
      <span class="an-dist-star" style="color:${CORES[n]}">${'★'.repeat(n)}</span>
      <span class="an-dist-bar"><span class="an-dist-fill" style="width:${larg}%;background:${CORES[n]}"></span></span>
      <span class="an-dist-num">${qtd.toLocaleString('pt-BR')}</span>
    </div>`;
  }).join('');
  distEl.setAttribute('aria-label',
    `${pct}% das ${rows.length} avaliações de ${mesLabel} foram positivas (4 ou 5 estrelas).`);

  /* comentários */
  const comTexto = rows.filter(r => (r.feedback_message || '').trim());
  const criticos = comTexto.filter(r => r.rating <= 3);
  const lista = _csatAnaliseFiltro === 'criticos' ? criticos : comTexto;

  if (subEl) subEl.textContent = `${comTexto.length} de ${rows.length} deixaram comentário`;
  if (filEl) {
    filEl.innerHTML = `
      <button class="${_csatAnaliseFiltro === 'todos' ? 'active' : ''}" onclick="_csatAnaliseFiltro='todos';renderAnaliseCsat()">Todos (${comTexto.length})</button>
      <button class="${_csatAnaliseFiltro === 'criticos' ? 'active' : ''}" onclick="_csatAnaliseFiltro='criticos';renderAnaliseCsat()">Críticos ≤3★ (${criticos.length})</button>`;
  }

  comEl.innerHTML = lista.length === 0
    ? `<div class="chart-na">${_csatAnaliseFiltro === 'criticos' ? 'Nenhuma crítica escrita neste período.' : 'Nenhum comentário escrito neste período.'}</div>`
    : lista.map(r => {
        const n     = typeof r.rating === 'number' ? Math.max(1, Math.min(5, r.rating)) : 0;
        const cor   = n >= 4 ? 'var(--green)' : n === 3 ? 'var(--yellow)' : 'var(--red)';
        const nome  = r.contact?.name || '—';
        const msg   = (r.feedback_message || '').trim();
        const data  = new Date(r.created_at * 1000).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
        const cid   = r.conversation_id ?? r.message_id;
        const url   = cid ? `https://nxticket.com.br/app/accounts/${cfg.account}/conversations/${cid}` : null;
        return `<div class="am-csat-row${n > 0 && n <= 3 ? ' csat-row-bad' : ''}">
          <span class="am-csat-stars" style="color:${cor}">${'★'.repeat(n)}${'☆'.repeat(5 - n)}</span>
          <span class="am-csat-contact" title="${esc(nome)}">${esc(nome)}</span>
          <span class="am-csat-msg" title="${esc(msg)}">${esc(msg)}</span>
          <span class="am-csat-date">${data}</span>
          ${url ? `<a class="am-csat-link" href="${url}" target="_blank" rel="noopener">Abrir chat →</a>`
                : '<span class="am-csat-link" style="opacity:.35">—</span>'}
        </div>`;
      }).join('');
}
```

- [ ] **Step 4: Chamar em `renderCharts()`**

Logo após a linha `renderAnaliseHero(n, trendPrev);` (inserida na Task 3), acrescentar:
```js
  renderAnaliseCsat();
```

- [ ] **Step 5: Verificar sintaxe**

```bash
node -e "const fs=require('fs');const m=fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*)<\/script>/);fs.writeFileSync(process.env.TMP+'/c.js',m[1]);"
node --check "$TMP/c.js" && echo OK
```
Esperado: `OK`.

- [ ] **Step 6: Dirigir e conferir a distribuição contra os dados brutos**

```js
JSON.stringify({
  linhasDist: [...document.querySelectorAll('.an-dist-row')].map(r=>r.textContent.trim().replace(/\s+/g,' ')),
  somaDist:   [...document.querySelectorAll('.an-dist-num')].reduce((s,e)=>s+parseInt(e.textContent.replace(/\D/g,''))||0,0),
  totalRows:  _chartCsat.rows.length,
  heroPct:    document.getElementById('an-hero-csat').textContent,
  comentarios:document.querySelectorAll('#an-csat-coment .am-csat-row').length,
  comTextoReal:_chartCsat.rows.filter(r=>(r.feedback_message||'').trim()).length
})
```
Esperado: 5 linhas de distribuição; `somaDist` igual a `totalRows`; `comentarios` igual a `comTextoReal`; `heroPct` no formato `92,3%`.

- [ ] **Step 7: Probe — alternar o filtro de críticos**

```js
_csatAnaliseFiltro='criticos'; renderAnaliseCsat();
JSON.stringify({
  mostrados: document.querySelectorAll('#an-csat-coment .am-csat-row').length,
  esperado:  _chartCsat.rows.filter(r=>(r.feedback_message||'').trim() && r.rating<=3).length
})
```
Esperado: `mostrados` igual a `esperado`. Restaurar com `_csatAnaliseFiltro='todos'; renderAnaliseCsat();`.

- [ ] **Step 8: Probe — estado vazio**

```js
const bk=_chartCsat; _chartCsat={rows:[],truncado:false,since:bk.since,until:bk.until};
renderAnaliseCsat();
const out=document.getElementById('an-csat-dist').textContent.trim();
_chartCsat=bk; renderAnaliseCsat(); out
```
Esperado: `Ainda não há avaliações neste período.` e nenhuma exceção no console.

- [ ] **Step 9: Commit**

```bash
git add index.html
git commit -m "feat(analise): capitulo 3 — distribuicao de notas e comentarios reais do cliente"
```

---

### Task 7: Capítulo 4 — tabela de contribuição por equipe

Substitui os dois cards de equipe (`chart-tmr-team` e `chart-teams`) por uma tabela única.

**Files:**
- Modify: `index.html` — HTML dos dois cards de equipe; JS blocos 7 e 8 de `renderCharts()`

**Interfaces:**
- Consumes: `_teamCompData` de `fetchTeamComparison()` — itens no formato `{ name, conversations_count, tma_h, tmr_min }`; `.an-team-table` (Task 1); `agentBadge()`, `_SLA_TMA`, `_SLA_TMR`, `esc()` (já existentes).
- Produces: `renderAnaliseEquipes()`.

- [ ] **Step 1: Substituir o HTML dos dois cards de equipe**

Deletar o card `#tmr-team-card` inteiro e o card `#teams-card` inteiro, junto com o divisor `Equipes`, e inserir no lugar:

```html
  <!-- ── 4 · COMO CADA EQUIPE CONTRIBUIU ── -->
  <div class="section-divider" style="margin-top:16px"><span class="section-divider-label">4 · Como cada equipe contribuiu</span></div>
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
```

- [ ] **Step 2: Escrever `renderAnaliseEquipes()`**

Inserir antes de `function renderCharts() {`:

```js
/* Capítulo 4 — contribuição por equipe. Ordena por volume, não por
   velocidade: ordenar por velocidade cria pódio, e esta tela é da equipe
   inteira se vendo, não um ranking. */
function renderAnaliseEquipes() {
  const wrap  = document.getElementById('an-equipes-wrap');
  const card  = document.getElementById('an-equipes-card');
  const cobEl = document.getElementById('an-equipes-cobertura');
  if (!wrap || !card) return;

  const itens = (_teamCompData?.items || []).slice()
    .sort((a, b) => (b.conversations_count || 0) - (a.conversations_count || 0));

  /* Com uma equipe filtrada não há comparação a fazer */
  if (_chartTeamFilter && _chartTeamFilter.size === 1) { card.style.display = 'none'; return; }
  card.style.display = '';

  if (!itens.length) {
    wrap.innerHTML = '<div class="chart-na">Dados por equipe não disponíveis com este token</div>';
    if (cobEl) cobEl.textContent = '';
    return;
  }

  if (cobEl) cobEl.textContent = `${itens.length} equipe${itens.length > 1 ? 's' : ''} com dados`;

  wrap.innerHTML = `
    <table class="an-team-table">
      <thead>
        <tr>
          <th>Equipe</th>
          <th>Atendimentos</th>
          <th>1ª resposta</th>
          <th>Até resolver</th>
        </tr>
      </thead>
      <tbody>
        ${itens.map(t => `
          <tr>
            <td>${esc(t.name)}</td>
            <td>${(t.conversations_count || 0).toLocaleString('pt-BR')}</td>
            <td>${t.tmr_min == null
                  ? '<span class="agent-badge badge-na">—</span>'
                  : agentBadge(t.tmr_min, t.tmr_min < 60 ? `${Math.round(t.tmr_min)}min` : `${(t.tmr_min / 60).toFixed(1)}hr`, _SLA_TMR, 'min', true)}</td>
            <td>${t.tma_h == null
                  ? '<span class="agent-badge badge-na">—</span>'
                  : agentBadge(t.tma_h, `${t.tma_h.toFixed(1)}hr`, _SLA_TMA, 'h', true)}</td>
          </tr>`).join('')}
      </tbody>
    </table>`;
  wrap.setAttribute('aria-label',
    `Contribuição de ${itens.length} equipes, da que mais atendeu para a que menos atendeu. ${itens[0].name} lidera com ${itens[0].conversations_count} atendimentos.`);
}
```

- [ ] **Step 3: Remover os blocos 7 e 8 de `renderCharts()` e chamar a nova função**

Deletar os blocos `/* ── 7. TMR POR EQUIPE ── */` e `/* ── 8. COMPARATIVO EQUIPES ── */` inteiros (cada um do comentário até o `}` que fecha seu escopo), e no lugar deles inserir:

```js
  /* ── 4 · CONTRIBUIÇÃO POR EQUIPE ── */
  destroyChart('tmr-team');
  destroyChart('teams');
  renderAnaliseEquipes();
```

- [ ] **Step 4: Verificar sintaxe**

```bash
node -e "const fs=require('fs');const m=fs.readFileSync('index.html','utf8').match(/<script>([\s\S]*)<\/script>/);fs.writeFileSync(process.env.TMP+'/c.js',m[1]);"
node --check "$TMP/c.js" && echo OK
```
Esperado: `OK`.

- [ ] **Step 5: Dirigir e conferir a tabela contra os dados**

```js
JSON.stringify({
  linhas: [...document.querySelectorAll('.an-team-table tbody tr')].map(tr=>{
    const td=tr.querySelectorAll('td');
    return {equipe:td[0].textContent.trim(), vol:parseInt(td[1].textContent.replace(/\D/g,''))||0};
  }),
  ordenadoPorVolume: (()=>{ const v=[...document.querySelectorAll('.an-team-table tbody tr')].map(tr=>parseInt(tr.querySelectorAll('td')[1].textContent.replace(/\D/g,''))||0); return v.every((x,i)=>i===0||v[i-1]>=x); })(),
  temSAG: [...document.querySelectorAll('.an-team-table tbody tr')].some(tr=>tr.textContent.includes('SAG')),
  charts: Object.keys(_charts)
})
```
Esperado: `ordenadoPorVolume:true`; `temSAG:true` (sem filtro aplicado); `charts` contém apenas `vol`, `tma`, `tmr`, `fcr` — sem `tmr-team` nem `teams`.

- [ ] **Step 6: Probe — filtrar uma equipe só faz o card sumir**

Abrir `#chart-inbox-trigger`, desmarcar "Todas", marcar uma equipe, aplicar em `#ibp .ibp-ok`, esperar o recarregamento e avaliar:
```js
JSON.stringify({
  filtro: _chartTeamFilter ? [..._chartTeamFilter] : null,
  cardVisivel: document.getElementById('an-equipes-card').style.display !== 'none'
})
```
Esperado: `filtro` com um id e `cardVisivel:false`. Limpar com `clearChartInboxFilter()` e confirmar que o card volta.

- [ ] **Step 7: Commit**

```bash
git add index.html
git commit -m "feat(analise): capitulo 4 — tabela de contribuicao por equipe, ordenada por volume"
```

---

## Verificação final da aba inteira

Após a Task 7, dirigir a aba completa uma vez e conferir o conjunto:

```js
JSON.stringify({
  capitulos: [...document.querySelectorAll('.section-divider-label')].map(e=>e.textContent),
  cards:     document.querySelectorAll('#graficos-page .chart-card').length,
  charts:    Object.keys(_charts),
  heroTiles: document.querySelectorAll('.an-hero-tile').length
})
```

Esperado:
- `capitulos` = `["1 · Quanto absorvemos", "2 · Com que velocidade", "3 · O que o cliente disse", "4 · Como cada equipe contribuiu"]`
- `cards` = 7
- `charts` = `["vol","tma","tmr","fcr"]`
- `heroTiles` = 4
- Console sem exceções
- Screenshot da página inteira para revisão visual
