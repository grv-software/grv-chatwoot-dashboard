# GRV CS — Dashboard Estratégico de Projetos

**Data:** 2026-06-23
**Arquivo alvo:** `grv-cs-jornada.html`
**Tipo:** Evolução incremental do módulo existente

---

## Objetivo

Enriquecer a tela "Projetos GRV" com um dashboard BI executivo que permita ao gestor ver a saúde do portfólio completo de implantações em um relance — sem precisar ler tabelas linha a linha. O dashboard é a view padrão da tela; Lista e Kanban continuam disponíveis no toggle.

---

## Arquitetura

### Toggle order (mudança)

De: `☰ Lista | ⊞ Kanban`
Para: `📊 Dashboard | ☰ Lista | ⊞ Kanban`

`localStorage: grv_cs_projetos_view` — valor padrão muda de `'lista'` para `'dashboard'`.

### Biblioteca de gráficos

Adicionar `<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>` no `<head>`.

Sem outras dependências novas. Chart.js v4 é standalone, ~60KB minificado.

### Filtro no modo Dashboard

No modo Dashboard, apenas o dropdown **"Consultor"** fica visível (para isolar um consultor específico ou ver todos). Os filtros de Etapa e Status são omitidos — o dashboard já os exibe como dimensões.

---

## Definições de Status para o Dashboard

O helper existente `getStatus(c)` retorna: `'Pausado' | 'Interrompido' | 'Cancelado' | 'Atrasado' | 'Em ordem'`. Para o dashboard, introduzir `getStatusDash(c)` que retorna um dos 6 buckets do dashboard:

| Bucket dashboard | Condição |
|---|---|
| `'Não Iniciado'` | `c.etapa === '1ª Reunião'` AND `getStatus(c) !== 'Atrasado'` |
| `'Em Andamento'` | `['Engajamento','Evolução','Conclusão'].includes(c.etapa)` AND `getStatus(c) !== 'Atrasado'` AND `getProgresso(c) < 100` |
| `'Atrasado'` | `getStatus(c) === 'Atrasado'` |
| `'Pausado'` | `c.etapa === 'Pausado' \|\| c.etapa === 'Interrompido'` |
| `'Concluído'` | `getProgresso(c) === 100` |
| `'Cancelado'` | `c.etapa === 'Cancelado'` |

Prioridade de aplicação: Cancelado > Concluído > Atrasado > Pausado > Em Andamento > Não Iniciado.

Helper `computeDashboardKPIs(clientes)`:
```javascript
function computeDashboardKPIs(clientes) {
  const r = { total:0, naoIniciado:0, emAndamento:0, atrasado:0, pausado:0, concluido:0, cancelado:0 };
  clientes.forEach(c => {
    r.total++;
    const s = getStatusDash(c);
    if (s==='Não Iniciado')  r.naoIniciado++;
    else if (s==='Em Andamento') r.emAndamento++;
    else if (s==='Atrasado')     r.atrasado++;
    else if (s==='Pausado')      r.pausado++;
    else if (s==='Concluído')    r.concluido++;
    else if (s==='Cancelado')    r.cancelado++;
  });
  return r;
}
```

---

## Layout do Dashboard

```
┌─ TOGGLE ─────────────────────────────────────────────────────────┐
│ [📊 Dashboard ●] [☰ Lista] [⊞ Kanban]   Consultor: [Todos ▾]   │
└──────────────────────────────────────────────────────────────────┘

┌─ KPI ROW (7 cards) ──────────────────────────────────────────────┐
│ [Total] [Não Iniciado] [Em Andamento] [Atrasados*] [Pausados]   │
│ [Concluídos] [Cancelados]                                        │
└──────────────────────────────────────────────────────────────────┘

┌─ CHART ROW (55/45 split) ────────────────────────────────────────┐
│ [Chart 1: Donut Distribuição]  │  [Chart 2: Barras por Produto]  │
└──────────────────────────────────────────────────────────────────┘

┌─ ATIVAÇÃO ROW ───────────────────────────────────────────────────┐
│ [Chart 3a: Gauge CPS]  [Chart 3b: Gauge NX]  [Backlog stats]    │
└──────────────────────────────────────────────────────────────────┘

┌─ ALERTAS OPERACIONAIS ───────────────────────────────────────────┐
│ ● CRÍTICO: ...   ● ATENÇÃO: ...                                  │
└──────────────────────────────────────────────────────────────────┘

┌─ PERFORMANCE POR CONSULTOR ──────────────────────────────────────┐
│ [Chart 4: Barras Horizontais]                                    │
│ [Tabela detalhada]                                               │
└──────────────────────────────────────────────────────────────────┘
```

---

## Seção 1 — KPI Row

7 cards em `display:grid; grid-template-columns: repeat(7,1fr); gap:12px`.
Em telas < 900px: `repeat(4,1fr)` na primeira linha + `repeat(3,1fr)` na segunda.

Cada card: `background:#fff; border-radius:7px; padding:16px 18px; box-shadow: var(--shadow)`.

| Card | Número cor | Fundo card | Border-top |
|---|---|---|---|
| Total | `#1A1A2E` | branco | nenhuma |
| Não Iniciado | `#718096` | branco | nenhuma |
| Em Andamento | `#3182ce` | branco | nenhuma |
| Atrasados | `#e53e3e` | `#FFF5F5` | `3px solid #e53e3e` |
| Pausados | `#d69e2e` | `#FFFFF0` | nenhuma |
| Concluídos | `#38a169` | `#F0FFF4` | nenhuma |
| Cancelados | `#4a5568` | branco | nenhuma |

Número: `font-size:32px; font-weight:700; line-height:1`.
Label: `font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:#718096; margin-bottom:4px`.

Animação `countUp`: nos primeiros 400ms após renderização, incrementar de 0 até o valor final (usando `requestAnimationFrame`). Suave e comunica dinamismo.

---

## Seção 2 — Chart 1: Donut Distribuição de Status

**Posição:** Coluna esquerda (55% da linha de charts).
**Tipo:** `doughnut` (Chart.js).

```javascript
{
  type: 'doughnut',
  data: {
    labels: ['Concluídos', 'Em Andamento', 'Atrasados', 'Pausados', 'Não Iniciado', 'Cancelados'],
    datasets: [{ data: [...], backgroundColor: ['#38a169','#3182ce','#e53e3e','#d69e2e','#718096','#4a5568'],
                 borderWidth: 2, borderColor: '#fff', hoverOffset: 6 }]
  },
  options: {
    cutout: '65%',
    plugins: {
      legend: { position: 'right', labels: { boxWidth: 12, padding: 16, font: { size: 12 } } },
      tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed} (${pct}%)` } }
    }
  }
}
```

**Elemento central** (texto sobre o canvas via CSS absolute): número total em `font-size:28px; font-weight:700` + label "projetos" em `font-size:11px; color:#718096`.

---

## Seção 2 — Chart 2: Barras Agrupadas por Produto

**Posição:** Coluna direita (45% da linha de charts).
**Tipo:** `bar` agrupado (Chart.js).

Eixo X: produtos presentes nos dados (`CPS`, `NX/IOT`, etc. — derivados dinamicamente de `c.produto`).
Séries (datasets): Em Andamento (azul `#3182ce`), Atrasados (vermelho `#e53e3e`), Pausados (âmbar `#d69e2e`), Concluídos (verde `#38a169`).

```javascript
{
  type: 'bar',
  data: { labels: produtos, datasets: [...] },
  options: {
    plugins: { legend: { position: 'bottom' } },
    scales: {
      y: { beginAtZero: true, grid: { color: '#edf2f7' }, ticks: { stepSize: 1 } },
      x: { grid: { display: false } }
    },
    animation: { duration: 500, easing: 'easeOutQuart' }
  }
}
```

---

## Seção 3 — Chart 3: Gauges Ativação

**Ativação** = porcentagem de projetos concluídos **dentro do prazo** sobre o total de projetos concluídos por produto. Meta: **85%**.

Um concluído "no prazo" = `getProgresso(c) === 100` AND `c.prazo !== null` AND `new Date(c.prazo) >= data de conclusão` (aproximado: `new Date(c.prazo) >= new Date(c.dataInicio)` — não há data de conclusão real no modelo; usar `prazo >= today` como proxy: se o projeto atingiu 100% e o prazo ainda não venceu).

Dois gauges lado a lado, um por produto principal (CPS, NX). Cada gauge:
- Semi-donut (doughnut com `rotation: -90`, `circumference: 180`)
- Dois datasets: [valor realizado (cor vermelha/verde conforme vs meta), restante (cinza claro)]
- Centro do arco: `XX%` em negrito + produto em label pequeno
- Abaixo do arco: "Meta: 85%" com linha tracejada visual (via CSS `position:absolute; left:85%; height:...`)

Se valor < meta → número em `#e53e3e`. Se ≥ meta → `#38a169`.

```javascript
{
  type: 'doughnut',
  data: {
    datasets: [{ data: [valor, 100-valor], backgroundColor: [cor, '#edf2f7'],
                 borderWidth: 0, circumference: 180, rotation: -90 }]
  },
  options: { cutout: '72%', plugins: { legend: { display:false }, tooltip: { enabled:false } } }
}
```

**Backlog stats** (à direita dos gauges): dois `stat-card` simples.
- "Backlog Total: X dias" — soma de `Math.max(0, today - new Date(c.prazo))` em dias para todos atrasados
- "Média por projeto: Y dias" — backlog total / quantidade de atrasados
- Ambos em texto grande (24px), vermelho se backlog > 5000 dias.

---

## Seção 4 — Alertas Operacionais

Cards com borda esquerda colorida, background suave. Computados a partir dos KPIs.

Regras de alerta (thresholds derivados da planilha real do usuário):

| Condição | Severidade | Mensagem | Ação |
|---|---|---|---|
| `atrasados/total > 0.15` | CRÍTICO | `Portfólio atrasado: XX% (N/M projetos)` | `Acima de 15% — escalar para gestão` |
| `backlogDias > 3000` | CRÍTICO | `Backlog em dias atrasados: X.XXX dias` | `Ação imediata de vazão necessária` |
| `estouroDeSemanas > 20` | CRÍTICO | `Estouro de prazo: N projetos ultrapassaram data limite` | `Revisar escopo ou formalizar extensão` |
| `pausados/total > 0.10` | ATENÇÃO | `Projetos pausados: N (XX% do portfólio)` | `Confirmar data de retomada com cliente` |
| `mediaDiasAtrasados > 90` | ATENÇÃO | `Média de atraso: XX dias/projeto` | `Confirmar plano de recuperação` |

"Estouro de semanas" = projetos com `getStatus === 'Atrasado'` (prazo vencido sem conclusão).

Se nenhum alerta disparar: exibir card verde "Portfólio saudável — sem alertas críticos no momento."

CSS para alertas:
```css
.alerta-card { padding:14px 16px; border-radius:7px; margin-bottom:8px; display:flex; align-items:flex-start; gap:12px }
.alerta-critico { background:#FFF5F5; border-left:4px solid #e53e3e }
.alerta-atencao { background:#FFFFF0; border-left:4px solid #d69e2e }
.alerta-ok      { background:#F0FFF4; border-left:4px solid #38a169 }
.alerta-dot     { width:8px; height:8px; border-radius:50%; flex-shrink:0; margin-top:4px }
.alerta-dot-red    { background:#e53e3e }
.alerta-dot-yellow { background:#d69e2e }
.alerta-dot-green  { background:#38a169 }
```

---

## Seção 5 — Performance por Consultor

### Chart 4: Barras Horizontais

Tipo: `bar` com `indexAxis: 'y'` (Chart.js). Eixo Y = nomes dos consultores. Barras empilhadas: Em Andamento | Atrasados | Pausados | Concluídos. Ordenado por `%Atrasados` decrescente.

```javascript
{
  type: 'bar',
  data: { labels: consultorNomes, datasets: [
    { label:'Em Andamento', data:[...], backgroundColor:'#3182ce', stack:'s' },
    { label:'Atrasados',    data:[...], backgroundColor:'#e53e3e', stack:'s' },
    { label:'Pausados',     data:[...], backgroundColor:'#d69e2e', stack:'s' },
    { label:'Concluídos',   data:[...], backgroundColor:'#38a169', stack:'s' },
  ]},
  options: {
    indexAxis: 'y',
    plugins: { legend: { position:'bottom' } },
    scales: {
      x: { stacked:true, grid:{ color:'#edf2f7' } },
      y: { stacked:true, grid:{ display:false } }
    },
    animation: { duration:500 }
  }
}
```

### Tabela detalhada

Abaixo do chart, tabela `data-table` com colunas:

`Consultor | Total | Em Andamento | Atrasados | % Atrasados | Pausados | Concluídos`

Coluna `% Atrasados`: badge pill — vermelho (`> 30%`), amarelo (`15–30%`), verde (`< 15%`).
Ordenação padrão: `% Atrasados` decrescente.
Header `% Atrasados` clicável para inverter ordem (toggle `asc/desc`).

---

## Seed Data Expandido

Para o dashboard ser visualmente rico e representativo da planilha real, expandir o seed com:

**Consultores adicionais (totalizar 7):**
```javascript
{ id:'cristiano',  nome:'Cristiano Santos' },
{ id:'felipe',     nome:'Felipe Alves' },
{ id:'silvia',     nome:'Silvia Costa' },
{ id:'severiano',  nome:'Severiano Rocha' },
```

**Clientes adicionais (~25 clientes novos):** distribuídos entre os 7 consultores, com produtos `'CPS'` e `'NX/IOT'`, etapas variadas e prazos mistos (alguns vencidos para gerar atrasados, alguns nulos para pausados).

Distribuição alvo dos 36 clientes totais:
- Não Iniciado: 5–7
- Em Andamento: 8–10
- Atrasados: 10–12 (inclui alguns com prazo < today)
- Pausados: 5–6
- Concluídos: 4–5 (progresso 100%)
- Cancelados: 1–2

Produtos: ~60% CPS, ~30% NX/IOT, ~10% CPS/IOT misto.

Os clientes extras são dados fictícios representativos (nomes de empresas industriais do setor de manufatura/metalurgia). Datas de prazo vencidas: usar datas entre `2025-09-01` e `2026-05-30` para gerar atrasados.

---

## Responsividade

| Largura | KPI grid | Chart row | Gauge row |
|---|---|---|---|
| ≥ 1200px | `repeat(7,1fr)` | 55/45 | side-by-side |
| 900–1199px | `repeat(4,1fr)` linha 1 + `repeat(3,1fr)` linha 2 | 50/50 | side-by-side |
| < 900px | `repeat(2,1fr)` | stacked | stacked |

Charts: `canvas` com `height:260px; max-width:100%`. Chart.js respeita o container width automaticamente.

---

## Função Principal

```javascript
let _dashCharts = {}; // guarda instâncias Chart.js para destroy() antes de re-render

function renderDashboardProjetos(clientes, consultores) {
  // 1. destroy instâncias anteriores
  Object.values(_dashCharts).forEach(ch => ch.destroy());
  _dashCharts = {};

  // 2. computar KPIs
  const kpis = computeDashboardKPIs(clientes);

  // 3. innerHTML do sec-projetos com estrutura HTML
  // 4. após innerHTML: initCharts(kpis, clientes, consultores)
  // 5. countUp animado nos KPI cards
}

function initCharts(kpis, clientes, consultores) {
  _dashCharts.donut  = new Chart(document.getElementById('ch-donut'),   chartDonutConfig(kpis));
  _dashCharts.barras = new Chart(document.getElementById('ch-barras'),  chartBarrasConfig(clientes));
  _dashCharts.cps    = new Chart(document.getElementById('ch-gauge-cps'), chartGaugeConfig(clientes,'CPS'));
  _dashCharts.nx     = new Chart(document.getElementById('ch-gauge-nx'),  chartGaugeConfig(clientes,'NX/IOT'));
  _dashCharts.consul = new Chart(document.getElementById('ch-consul'),  chartConsulConfig(clientes, consultores));
}
```

Chamar `renderDashboardProjetos` de dentro de `renderProjetosGRV()` quando `_proj_view === 'dashboard'`.

---

## Constraint Importante

- Nenhuma instância Chart.js deve persistir ao trocar de view. O `_dashCharts` garante `destroy()` antes de cada re-render.
- Os charts usam IDs fixos no canvas. Garantir que o HTML do dashboard só existe no DOM quando `_proj_view === 'dashboard'`.
- `computeDashboardKPIs` e `getStatusDash` devem ser funções puras (sem efeitos colaterais).

---

## Fora de Escopo

- Tarefas com vencimento por cliente (sub-projeto separado)
- Alertas na tela Minha Carteira (sub-projeto separado)
- Exportação CSV / PDF
- Filtro de período (data range)
- Gráfico de tendência temporal
