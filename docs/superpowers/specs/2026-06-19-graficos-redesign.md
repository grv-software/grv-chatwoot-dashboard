# Design Spec — Redesign da Aba Gráficos (Análise)

**Data:** 2026-06-19  
**Projeto:** GRV SAC — Painel de Atendimento  
**Status:** Aprovado para implementação

---

## Contexto

O painel atual possui uma aba "Gráficos" com 5 charts (TMA, TMR, FCR, Volume, Carga por Agente). Os problemas identificados:

- Siglas de call center (TMA, TMR, FCR) não são intuitivas para usuários leigos
- Todos os gráficos usam a mesma cor azul, dificultando leitura rápida
- Não há indicadores de tendência (melhora/piora vs. período anterior)
- TMR frequentemente indisponível na API com token limitado
- FCR é a métrica menos intuitiva sem metas de referência definidas
- Falta gráfico de pico de horário — essencial para decisões de escala de equipe

**Público-alvo:** Gestores/supervisores E atendentes usam o mesmo painel.  
**Decisões suportadas:** Volume/escala de equipe, tempo de resposta, comparação entre agentes.  
**Metas formais:** Ainda não definidas — o painel serve para descoberta de baseline.

---

## Abordagem Escolhida

**B — Reestruturado por decisão:** reorganiza os charts em duas seções temáticas com nomes em português direto, remove FCR e TMR, adiciona gráfico de pico de horário e donut de status.

---

## Design

### 1. Renomeação da aba

`Gráficos` → `Análise` na sidebar. Mais claro para usuários não-técnicos.

### 2. Estrutura da página

A página passa de uma grade flat para duas seções com separador visual:

```
── Operacional ─────────────────────────────────────────────────
[ Volume de Atendimentos ] [ Pico de Horário ] [ Status das Conversas ]

── Desempenho ──────────────────────────────────────────────────
[ Tempo Médio de Atendimento ]  [ Atendimentos por Agente ]
```

Separador: linha fina `var(--border)` com label centralizado em `var(--text3)`.

### 3. Seletor de período

Mantido no topo da página. Afeta apenas os gráficos baseados em período (Volume e TMA). Os gráficos de tempo real (Pico, Status, Agente) ignoram o seletor e exibem `Ao vivo` no cabeçalho.

---

## Especificação de cada gráfico

### 3.1 Volume de Atendimentos
- **Tipo:** Barra vertical
- **Dado:** `conversations_count` da API `/v2/accounts/{id}/reports/summary` por mês
- **Cor:** `#3b82f6` (azul, `var(--accent)`)
- **Subtítulo:** *"Total de atendimentos iniciados no período"*
- **Tendência:** `+12% vs anterior` em verde se cresceu, vermelho se caiu
- **Sem mudança de lógica** — apenas renomeia e adiciona tendência

### 3.2 Pico de Horário *(novo)*
- **Tipo:** Barra vertical
- **Dado:** `_rawConvs` — agrupa `created_at` por hora do dia (0–23), conta por hora
- **Cor:** `#f97316` (laranja, `var(--orange)`)
- **Subtítulo:** *"Horários com mais atendimentos em aberto agora"*
- **Label no topo da barra mais alta:** "Pico"
- **Sem seletor de período** — usa conversas abertas em tempo real
- **Cabeçalho:** exibe `Ao vivo` em verde pulsante no lugar de tendência

### 3.3 Status das Conversas *(novo)*
- **Tipo:** Donut (doughnut chart do Chart.js)
- **Dado:** `_rawConvs` — conta por `status`: open / resolved / pending
- **Cores:** 
  - Abertas: `#ef4444` (vermelho)
  - Resolvidas: `#22c55e` (verde)
  - Pendentes: `#eab308` (amarelo)
- **Subtítulo:** *"Distribuição atual das conversas"*
- **Legenda:** embaixo do donut — `● Abertas  ● Resolvidas  ● Pendentes`
- **Sem seletor de período** — tempo real

### 3.4 Tempo Médio de Atendimento
- **Tipo:** Linha com fill
- **Dado:** `avg_resolution_time` (segundos → "Xhr Ymin")
- **Cor:** `#8b5cf6` (roxo)
- **Subtítulo:** *"Quanto tempo em média para resolver um atendimento. Quanto menor, melhor."*
- **Tendência:** verde se **caiu** (melhora), vermelho se subiu (piora) — invertido vs. Volume
- **Remove sigla:** "TMA" some completamente da interface visível

### 3.5 Atendimentos por Agente
- **Tipo:** Barra horizontal
- **Dado:** `_rawConvs` — conta por `meta.assignee.name`, top 15
- **Cor:** `#14b8a6` (teal)
- **Subtítulo:** *"Conversas abertas por atendente agora"*
- **Largura:** full-width (ocupa linha inteira)
- **Sem seletor de período** — tempo real

### Removidos
- **TMR** — frequentemente indisponível com token limitado; confuso sem contexto
- **FCR** — métrica de call center, não intuitiva sem metas definidas

---

## Layout de cada card

```
┌─────────────────────────────────────────────────┐
│ Tempo Médio de Atendimento         ↓ 18% vs ant. │  ← cabeçalho
│ Quanto tempo em média...                          │  ← subtítulo cinza
│                                                   │
│  [                gráfico                       ] │
└─────────────────────────────────────────────────┘
```

- **Título:** `font-size:14px; font-weight:600; var(--text)`
- **Subtítulo:** `font-size:11px; var(--text3); margin-top:2px`
- **Tendência:** `font-size:12px; font-weight:600` — verde `#22c55e` / vermelho `#ef4444`
- **`Ao vivo`:** badge pequeno verde pulsante — criar classe `.badge-live` nova (verde `#22c55e`), pois `.badge-pulse` existente é laranja/urgência
- **Altura do canvas:** 220px para todos (exceto Agente: 280px pois tem mais labels)

---

## Grid responsivo

| Viewport | Operacional | Desempenho |
|----------|-------------|------------|
| ≥ 900px  | 3 colunas   | 2 colunas (TMA + Agente full) |
| < 900px  | 1 coluna    | 1 coluna   |

---

## Cálculo de tendência

Para Volume e TMA, calculado comparando o período selecionado com o período imediatamente anterior de mesma duração:

```
tendência = ((valorAtual - valorAnterior) / valorAnterior) * 100
```

A API já é chamada com `since`/`until` por mês — basta comparar `_chartData[último]` vs `_chartData[penúltimo]`.  
Para exibição: `↑ 8%` ou `↓ 12%`. Para TMA, ↓ é positivo (verde); para Volume, ↑ é positivo (verde).

---

## Dados e API

| Gráfico | Fonte | Endpoint |
|---------|-------|----------|
| Volume | API relatórios | `/v2/accounts/{id}/reports/summary?type=account` (fallback: per-inbox) |
| TMA | API relatórios | mesmo endpoint acima |
| Pico de Horário | Local | `_rawConvs[].created_at` → agrupado por hora |
| Status | Local | `_rawConvs[].status` → contagem |
| Agente | Local | `_rawConvs[].meta.assignee.name` → contagem |

Nenhuma nova chamada de API é necessária — todos os dados já estão disponíveis.

---

## Impacto em código existente

- `renderCharts()`: reescrever com 5 novos gráficos (remove TMR e FCR, adiciona Pico e Status)
- `fetchChartData()`: manter lógica, adicionar cálculo de tendência comparando períodos
- HTML `#graficos-page`: reestruturar grid com separadores de seção
- CSS: adicionar `.section-divider`, atualizar `.chart-grid` para 3 colunas em Operacional
- Sidebar: renomear "Gráficos" → "Análise" no item de navegação
- Não altera: `fetchKPIs`, `_rawConvs`, filtro por agente, filtro por inbox

---

## Fora de escopo

- Filtro por agente na aba Análise (sem metas definidas, a comparação ainda não gera ação clara)
- Gráfico de CSAT (não confirmado disponível na API com o token atual)
- Linhas de meta/SLA nos gráficos (metas ainda não definidas)
- Export de dados (não solicitado)
