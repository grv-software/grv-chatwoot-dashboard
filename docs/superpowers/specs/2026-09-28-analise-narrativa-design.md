# Design Spec — Aba Análise como narrativa de desempenho

**Data:** 2026-09-28
**Projeto:** GRV SAC — Painel de Atendimento
**Status:** Aprovado para implementação
**Escopo:** Apenas a aba Análise (`#graficos-page`). Painel, Agentes e Configurações não mudam.

---

## Contexto

A aba acumulou 11 cards desde o redesign de 2026-06-19. A spec daquela época removeu TMR e FCR
e criou o Pico de Horário; depois disso TMR e FCR voltaram, entraram dois cards de equipe e a
pontuação com CSAT. Ninguém reorganizou o conjunto. O resultado é uma grade sem ordem de leitura,
com sobreposição e com cards que não conseguem informar o que prometem.

A auditoria de 2026-09-28 (verificada contra a API real da conta 1) encontrou:

| Card | Problema |
|------|----------|
| De onde vêm os atendimentos? | 100% das conversas da conta são `WebWidget` ou `Api` — ambas caem em "Chat". O donut é permanentemente de uma cor só. |
| Pico de Horário | Criado para decidir escala de equipe, mas usa só conversas abertas agora. Mostra quando começou o que ainda está na fila, não o padrão de demanda. |
| Fila Atual | Dado ao vivo dentro de uma aba de histórico. Duplica o que o Painel já mostra. |
| Carga por agente agora | Ao vivo **e** individual. Duplica a lista lateral do Painel. |
| Velocidade por equipe + Comparativo Equipes | Os dois mostram TMR por equipe. A mesma barra aparece duas vezes na tela. |

A raiz comum: a aba mistura "agora" com "história". Todo card problemático era um card ao vivo.

## Decisões que orientam o design

**Leitor:** a equipe inteira se vendo. Tom de progresso e reconhecimento. Ranking individual sai
do centro — a aba Agentes já existe para detalhe por pessoa.

**Estrutura:** a Análise passa a ser 100% histórica. Todo dado ao vivo sai. Consequências:
o seletor de período passa a valer para a tela inteira (hoje só afeta alguns cards), e os quatro
cards ao vivo problemáticos saem por uma decisão só.

**Nada de informação se perde.** O Painel já cobre o que sai: a fila está em "Conversas aguardando
atendimento" e no KPI "Em aberto agora"; a carga por pessoa está na lista lateral de agentes.

**Verdade acima de conforto.** O capítulo de satisfação mostra elogios e críticas. Em setembro
foram 468 avaliações, 92,3% positivas e 23 de uma estrela, com texto como *"Não tive retorno no meu
atendimento novamente pela terceira a quarta vez"*. Mostrar só elogio seria bajulação — o inverso
do boletim, e igualmente desonesto. A proporção real é a mensagem.

---

## Estrutura da página

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Análise                                                                   │
│ Setembro de 2026 · comparado com 1–28 de agosto        [Mês ▾] [Equipes ▾]│
└──────────────────────────────────────────────────────────────────────────┘

    5.022              5.077              45min             92,3%
    entraram           resolvidos         1ª resposta       aprovaram
    ▼ 28%              ▼ 27%              ▼ 75% ✓           de 468 avaliações

 ── 1 · Quanto absorvemos ──────────────────────────────────────────────────
 [ Volume de atendimentos        ] [ Resolvidos no período           ]

 ── 2 · Com que velocidade ─────────────────────────────────────────────────
 [ Até a primeira resposta       ] [ Até resolver                    ]

 ── 3 · O que o cliente disse ──────────────────────────────────────────────
 [ Distribuição de estrelas      ] [ Comentários (rolável)           ]

 ── 4 · Como cada equipe contribuiu ────────────────────────────────────────
 [ Tabela: equipe · atendimentos · 1ª resposta · até resolver        ]
```

O cabeçalho declara o período e a janela de comparação. Isso resolve a ambiguidade encontrada na
auditoria, em que a tela comparava um mês pela metade contra um mês inteiro sem dizer.

---

## Abertura — faixa de quatro números

Sem gráfico. É o parágrafo de abertura: os quatro números que resumem o período.

| Tile | Valor | Sublabel | Fonte | Tendência |
|------|-------|----------|-------|-----------|
| Entraram | `conversations_count` | — | `reports/summary` | vs `_chartTrendBase`, ▲ é bom |
| Resolvidos | `resolutions_count` | `N% do que entrou` | idem | vs baseline, ▲ é bom |
| 1ª resposta | `avg_first_response_time` | — | idem | vs baseline, ▼ é bom; ✓ se ≤ `_SLA_TMR` |
| Satisfação | % de avaliações ≥ 4★ | `de N avaliações` | `csat_survey_responses` | — |

A dupla "entraram / resolvidos" é deliberada: dois números grandes lado a lado mostram de imediato
se a fila cresceu ou encolheu no período. A taxa percentual vira sublabel em vez de valor
principal — é justamente o número que passa de 100% e gera desconfiança quando aparece grande e
sem contexto. O `title` do tile carrega a explicação de por que isso acontece.

- Valor: `font-size:32px; font-weight:800; font-variant-numeric:tabular-nums`
- Rótulo: `font-size:12px; color:var(--text2)`
- Tendência: reaproveita `metricTrend()`, que já usa o baseline de mesma duração decorrida

Em telas < 900px a faixa quebra em 2×2.

---

## Capítulo 1 — Quanto absorvemos

**1.1 Volume de atendimentos** — reaproveita `chart-vol` sem mudança de lógica.
Barra vertical, `#3b82f6`, um ponto por mês do período.

**1.2 Resolvidos no período** — reaproveita `chart-fcr`, mas o card passa a exibir a **contagem
absoluta** de resolvidos como métrica principal, com a taxa como secundária. Hoje o card lidera
com a taxa, que é justamente o número que passa de 100% e gera desconfiança. Barra vertical,
verde `#22c55e` quando ≥ meta, amarelo entre meta−15 e meta, vermelho abaixo.

## Capítulo 2 — Com que velocidade

**2.1 Até a primeira resposta** — reaproveita `chart-tmr`. Linha com fill, teal `#14b8a6`, com a
linha tracejada de `_SLA_TMR`. É a melhor notícia do período e hoje está enterrada no meio da
grade: caiu de ~3 horas para 45 minutos.

**2.2 Até resolver** — reaproveita `chart-tma`. Linha com fill, roxo `#8b5cf6`, linha tracejada de
`_SLA_TMA`. **Recebe uma ressalva fixa no subtítulo**, porque a métrica é média sem proteção
contra outlier e oscilou 9h → 56h → 7h → 28h em quatro semanas de setembro sem mudança na
operação:

> *Média sensível a atendimentos antigos encerrados em lote — variações grandes entre períodos
> costumam ser limpeza de fila, não queda de desempenho.*

## Capítulo 3 — O que o cliente disse

Dois cards novos lado a lado (empilham abaixo de 900px).

**3.1 Distribuição de estrelas** — barra horizontal, uma linha por nota (5★ até 1★), com a
contagem rotulada direto na barra (evita ida e volta ao eixo). Verde para 5★ e 4★, amarelo para
3★, vermelho para 2★ e 1★. O glifo ★ e a contagem acompanham a cor, para a informação não depender
de cor sozinha.

Cabeçalho do card: `92,3% aprovaram · 468 avaliações · Setembro de 2026`.

**3.2 Comentários** — lista rolável dos que têm `feedback_message` preenchido, ordenada por data
decrescente. Cada linha: estrelas, nome do contato, texto, data, link "Abrir chat →".
Linhas de 1–3 estrelas recebem a faixa de fundo avermelhada que já existe (`.csat-row-bad`).

Filtro de duas opções no cabeçalho, reaproveitando o padrão do modal de agente:
`Todos (83)` | `Críticos ≤3★ (n)`.

**Janela de tempo:** este capítulo cobre **apenas o mês mais recente do período selecionado**,
sempre declarado no cabeçalho do card. Motivo: são ~19 páginas de API por mês (25 respostas por
página, 468 em setembro); 12 meses seriam ~225 chamadas sequenciais. O resto da página respeita o
seletor normalmente.

**Estados vazios:**
- Sem avaliações no mês → `Ainda não há avaliações neste período.`
- API retorna 401/403 ou CSAT desativado → reaproveita `.csat-placeholder`, que já traz as
  instruções de ativação no Chatwoot.

## Capítulo 4 — Como cada equipe contribuiu

Tabela, não gráfico de barras. Com 13 linhas (12 times + SAG) uma tabela lê melhor e permite
quatro colunas sem poluir.

| Equipe | Atendimentos | 1ª resposta | Até resolver |
|--------|-------------:|------------:|-------------:|

- **Ordenada por atendimentos, decrescente.** Ordenar por velocidade cria pódio; ordenar por
  volume mostra quem carregou quanto, que é contribuição e não nota. Essa escolha é deliberada e
  decorre do tom definido.
- Tempos usam os mesmos badges de meta da aba Agentes (`agentBadge`), que já colorem contra SLA.
- SAG aparece com `—` em "até resolver": é caixa roteadora, `tma_h` é `null` por design.
- Números com `font-variant-numeric:tabular-nums`.
- **O card inteiro some quando há filtro de uma equipe só** — com uma linha não há comparação.

Substitui os dois cards atuais (`chart-tmr-team` e `chart-teams`), eliminando a duplicação de TMR.

**Contagem final:** 11 cards → 7 (volume, resolvidos, 1ª resposta, até resolver, distribuição de
estrelas, comentários, tabela de equipes), mais a faixa de abertura.

---

## O que é removido

| Removido | Motivo | Onde a informação continua |
|----------|--------|----------------------------|
| `chart-channel` | Uma cor só, permanentemente | — (não havia informação) |
| `chart-peak` | Ao vivo; o título promete padrão de demanda que o dado não entrega | — |
| `chart-status` (Fila Atual) | Ao vivo | Painel: "Conversas aguardando" e KPI "Em aberto agora" |
| `chart-agents` | Ao vivo e individual | Painel: lista lateral de agentes; aba Agentes |
| `chart-tmr-team` | Duplica TMR do comparativo | Capítulo 4 |
| `chart-msg` (Eficiência) | Menos mensagens tanto pode ser eficiência quanto cliente que desistiu; não decide nada sem CSAT cruzado | — |
| `#chart-sample-warn` | Avisava sobre truncamento dos cards ao vivo; sem cards ao vivo, vira código morto | — |

---

## Dados e API

| Seção | Fonte | Chamada |
|-------|-------|---------|
| Abertura (3 tiles) | `_chartData[último]` + `_chartTrendBase` | já existentes |
| Abertura (satisfação) | agregação do CSAT do mês | nova, ver abaixo |
| Cap. 1 e 2 | `_chartData` | já existentes |
| Cap. 3 | `/v1/accounts/{acc}/csat_survey_responses?page=N&since&until&sort=-created_at` | nova, ~19 páginas/mês |
| Cap. 4 | `_teamCompData` via `fetchTeamComparison` | já existente |

A busca de CSAT replica `fetchCsatAll()` da aba Agentes (paginação até `chunk.length < 25`).
Guardar em `_chartCsat` com o mesmo TTL de 5 minutos já usado em `_chartTeamCache`, chaveado por
`since:until`, para a troca de período não refazer a busca à toa.

**Teto de paginação: 40 páginas (1.000 avaliações).** Setembro teve 468, então o teto sobra para o
volume atual, mas não é garantido para sempre. Se o teto for atingido, o cabeçalho do card passa a
dizer `amostra das 1.000 mais recentes` em vez de omitir — truncamento silencioso foi exatamente o
defeito corrigido em 2026-09-28 nos cards ao vivo e não deve ser reintroduzido aqui.

---

## Impacto em código

- **HTML `#graficos-page`** — reescrever: faixa de abertura, 4 divisores de capítulo, 7 cards
- **`renderCharts()`** — remover os blocos 2, 6, 7, 9, 10 (canal, mensagens, tmr-team, pico,
  status); manter 1, 3, 4, 5; reescrever o bloco 8 (equipes) como tabela; adicionar render do CSAT
- **`fetchChartData()`** — adicionar busca de CSAT do mês mais recente em paralelo com o resto
- **Remover** `chartPending` e o bloco de `#chart-sample-warn` (ambos criados em 2026-09-28 para os
  cards ao vivo que agora saem)
- **CSS** — novo: `.analise-hero` (faixa de números), `.csat-dist` (barras de estrela),
  `.equipe-table`; remover o que só servia aos cards excluídos
- **Não altera** — `fetchKPIs`, `_rawConvs`, aba Agentes, aba Painel, Configurações, filtro de
  equipe (incluindo o SAG adicionado hoje)

## Regras de qualidade aplicadas

Do skill `ui-ux-pro-max`, categorias §10 (dados), §6 (tipografia e cor), §5 (layout), §1 (acesso):

- Hierarquia por tamanho e espaço, não por cor (§6 `visual-hierarchy`)
- `tabular-nums` em toda coluna numérica (§6 `number-tabular`)
- Contagem rotulada direto na barra de estrelas (§10 `direct-labeling`)
- Granularidade de tempo declarada no cabeçalho (§10 `time-scale-clarity`)
- Estado vazio com texto útil, nunca eixo em branco (§10 `empty-data-state`)
- Grades de fundo em baixo contraste, sem competir com o dado (§10 `gridline-subtle`)
- Cor nunca é o único portador de significado — estrela e contagem acompanham (§10 `color-not-only`)
- `aria-label` em cada card resumindo sua conclusão, para leitor de tela (§10 `screen-reader-summary`)
- Texto ≥ 4.5:1 e marcas de dado ≥ 3:1 contra o fundo (§1 `color-contrast`)
- Sem emoji como ícone estrutural (§4 `no-emoji-icons`) — ★ é dado, não ícone
- Animação de entrada já desligada nos charts; respeitar `prefers-reduced-motion` no que for novo

## Fora de escopo

- Redesign do Painel (tem problemas próprios já mapeados, entre eles o "Tempo médio de duração"
  instável — conversa separada)
- Métrica `unattended` (141 conversas sem resposta) — é card novo no Painel, não na Análise
- Mediana de tempo de resolução — a API do Chatwoot não expõe; exigiria paginar conversa a conversa
- Exportação CSV
- Alertas e notificações
