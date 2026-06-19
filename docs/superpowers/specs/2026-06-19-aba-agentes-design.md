# Aba Agentes — Design Spec

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Adicionar aba "Agentes" ao sidebar do dashboard GRV SAC com visão ao vivo, desempenho histórico por período e CSAT por agente.

**Architecture:** Single-file (index.html). Nova página `#agentes-page` seguindo o padrão das páginas existentes (`#painel-page`, `#graficos-page`). Dados de status ao vivo via `/v2/reports/overview`, desempenho histórico via `/v2/reports/summary?type=agent&id=X` para cada agente, CSAT via `/v1/reports/agents/satisfaction`.

**Tech Stack:** HTML/CSS/JS inline, Chart.js 4 (já carregado), Chatwoot API via proxy Node.js em server.js.

---

## Global Constraints

- Single file: todas as mudanças em `index.html`
- Seguir padrões visuais existentes: variáveis CSS (`--bg`, `--surface`, `--text1`, etc.), classes `.chart-card`, `.metric-card`, `.section-divider`, `.badge-live`
- Nenhuma dependência nova — Chart.js já disponível
- API calls via função `api()` existente
- Filtros de agente e período devem ser independentes dos filtros da aba Painel e Análise
- Token pode não ter acesso a `type=agent` — implementar fallback gracioso com mensagem

---

## Seções da Aba

### Controles do topo
- **Seletor de período:** 4 botões tipo pill — `Mês atual` · `3 meses` · `6 meses` · `12 meses`. Estado em `_agentTabPeriod` ('1'|'3'|'6'|'12'). Default: `3 meses`.
- **Filtro de agentes:** botão "Todos os agentes" que abre popup de seleção múltipla (igual ao filtro de inbox existente). Estado em `_agentTabFilter: Set<number>|null`. Quando ativo exibe chips com nome do agente e botão de remover. Aplica em todas as 3 seções.

---

### Seção 1 — Status ao vivo

**Fonte:** `GET /v2/accounts/{account}/reports/overview` — polling a cada 60s (mesmo intervalo do painel).

**Cards de resumo (linha de 4):**
| Card | Valor | Cor |
|---|---|---|
| Online | agentes com `availability_status: online` | verde |
| Ocupado | agentes com `availability_status: busy` | amarelo |
| Offline | agentes com `availability_status: offline` | cinza |
| Conversas abertas | total de conversas abertas agora | azul |

**Tabela de agentes ao vivo** (abaixo dos cards):
Colunas: Nome · Status (bolinha colorida) · Conversas abertas · Mensagem mais antiga (tempo desde `created_at` da conversa mais antiga do agente).

- Quando `_agentTabFilter` ativo: exibe apenas agentes selecionados
- Quando token sem acesso a overview: exibir mensagem "Status ao vivo não disponível com este token"
- Ordenação padrão: status (online primeiro), depois por conversas abertas desc

---

### Seção 2 — Desempenho no período

**Fonte:** Para cada agente em `_agentList`, chamar:
```
GET /v2/accounts/{account}/reports/summary?type=agent&id={id}&since={since}&until={until}
```
Chamadas em paralelo (Promise.all), silenciar erros individuais com catch retornando null.

**Período:** calculado a partir de `_agentTabPeriod`:
- `'1'` → mês atual (1º dia do mês até hoje)
- `'3'` → últimos 3 meses completos
- `'6'` → últimos 6 meses completos
- `'12'` → últimos 12 meses completos

Para o gráfico de detalhe (histórico), buscar mês a mês individualmente e montar array de pontos.

**Tabela de desempenho** (ordenável por qualquer coluna):
| Coluna | Campo API | Formato |
|---|---|---|
| Agente | name | texto |
| Volume | conversations_count | número |
| TMA | avg_resolution_time | fmtSec() |
| TMR | avg_first_response_time | fmtSec() |
| Taxa de Resolução | resolutions_count/conversations_count | % |
| Msgs/Conversa | (incoming+outgoing)/conversations_count | 1 decimal |
| Total de Mensagens | incoming_messages_count + outgoing_messages_count | número |

- Ordenação padrão: Volume decrescente (quem atendeu mais aparece primeiro). Colunas clicáveis para re-ordenar.
- Linhas com `conversations_count === 0` ficam sempre ao final, independente da ordenação
- Clicar em qualquer linha expande o **gráfico de detalhe** abaixo da tabela
- Apenas um agente expandido por vez; clicar no mesmo fecha

**Gráfico de detalhe do agente expandido:**
Gráfico de linha com múltiplas séries: Volume (eixo Y2), TMA (horas, eixo Y1), TMR (minutos, eixo Y1). Labels: meses do período (ex: "Jan", "Fev"…). Cada ponto é um mês. Permite ver evolução ao longo do tempo.

Título: "Evolução de {nome do agente}" · Subtítulo: período selecionado.

---

### Seção 3 — Satisfação do Cliente (CSAT)

**Fonte:** `GET /v1/accounts/{account}/reports/agents/satisfaction?since={since}&until={until}`

**Detecção automática:**
- Se endpoint retornar dados: renderizar tabela de CSAT
- Se retornar vazio ou erro 404: exibir card "Aguardando ativação do CSAT" com instrução:
  > "Para ativar o CSAT no Chatwoot: Configurações → Caixa de entrada → editar → Configurações de colaboração → ativar pesquisa de satisfação."

**Tabela de CSAT** (quando ativo):
| Coluna | Descrição |
|---|---|
| Agente | nome |
| Nota Média | média das avaliações (1–5 estrelas ou emoji) |
| Total de Avaliações | contagem |
| % Positivas | avaliações ≥ 4 / total |

- Filtro de agentes aplica aqui
- Quando filtro ativo com seleção que não tem dados: "Nenhuma avaliação no período para os agentes selecionados"

---

## Variáveis de Estado (novas)

```javascript
let _agentTabPeriod  = '3';        // '1'|'3'|'6'|'12' — meses; default 3
let _agentTabFilter  = null;       // Set<number>|null — ids de agentes selecionados
let _agentList       = [];         // [{id, name, availability_status}] da API /agents
let _agentPerfData   = null;       // {agentId: {summary, months[]}} — cache de desempenho
let _agentOverview   = null;       // dados brutos do overview ao vivo
let _agentCsat       = null;       // dados de CSAT ou null se inativo
let _agentExpanded   = null;       // id do agente com gráfico expandido
let _agentTabDirty   = false;      // true quando precisar re-renderizar ao entrar na aba
```

---

## Funções Novas

- `fetchAgentTab()` — orquestra os 3 fetches em paralelo: overview + summary por agente + CSAT. Define `_agentTabDirty = true` no `fetchAll()` para sincronizar com o refresh automático do painel.
- `renderAgentTab()` — renderiza as 3 seções. Chamada por `showPage()` quando a aba é selecionada.
- `renderAgentLive()` — seção 1 (ao vivo)
- `renderAgentPerf()` — seção 2 (tabela + gráfico expandido)
- `renderAgentCsat()` — seção 3 (CSAT ou placeholder)
- `toggleAgentExpand(id)` — expande/fecha gráfico de detalhe do agente
- `setAgentTabPeriod(p)` — muda período e dispara re-fetch
- `applyAgentTabFilter(ids)` — aplica filtro de agentes

---

## Integração com Fluxo Existente

- `showPage('agentes')` → se `_agentTabDirty` ou sem dados: chama `fetchAgentTab()`, senão `renderAgentTab()`
- `fetchAll()` (refresh automático do painel) → marca `_agentTabDirty = true` para que na próxima visita à aba os dados sejam atualizados
- `visibilitychange` listener existente já cobre a aba (pausa polling quando aba do browser está oculta)
- Sidebar: adicionar item "Agentes" entre "Painel" e "Análise"

---

## Tratamento de Erros

| Cenário | Comportamento |
|---|---|
| Token sem acesso a `type=agent` | Mensagem na seção 2: "Dados por agente requerem permissão de Administrador" |
| Token sem acesso a overview | Seção 1 mostra mensagem, seções 2 e 3 funcionam normalmente |
| Agente sem dados no período | Linha na tabela com `—` em todas as colunas métricas, posicionada ao final |
| CSAT inativo | Card placeholder com instrução de ativação |
| Erro de rede | Toast de erro existente + retry no próximo fetch automático |
