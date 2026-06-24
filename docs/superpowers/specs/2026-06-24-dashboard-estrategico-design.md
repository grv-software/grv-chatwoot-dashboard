# GRV CS Jornada — Dashboard Estratégico v2 + Sidebar Colapsável

**Data:** 2026-06-24  
**Arquivo alvo:** `grv-cs-jornada.html`  
**Tipo:** Redesign do dashboard de Projetos GRV + sidebar colapsável

---

## Objetivo

Transformar o dashboard de Projetos GRV em um instrumento de decisão estratégica para gestores de implantação. O gestor deve conseguir responder 3 perguntas em menos de 10 segundos, lendo de cima para baixo, sem scroll obrigatório na Zona 1. Visual no nível do GRV SAC (grv-chatwoot-dashboard.netlify.app).

**Público:** Gestores (decisão estratégica) e consultores (contexto operacional). Clientes não têm acesso.

---

## Arquitetura

Single-file SPA (`grv-cs-jornada.html`) — sem build step. Todas as mudanças são CSS + JS inline. Chart.js v4 via CDN já presente. Sidebar colapsável via CSS `width` transition + classe `sidebar--collapsed` no `<aside>`.

---

## Sidebar Colapsável

### Comportamento
- Botão `☰` fixo no topo da sidebar, sempre visível
- **Expandida** (240px, padrão): logo + texto completo, nav com labels, select de consultor visível
- **Colapsada** (56px): apenas ícones das nav items, sem texto. Logo vira só o quadrado laranja "G". Select de consultor some.
- Hover sobre ícone colapsado: tooltip nativo (`title`) com o nome do item
- Transição: `width 0.2s ease`, `overflow: hidden`
- Preferência persistida: `localStorage.setItem('grv_cs_sidebar_collapsed', '1')`
- Conteúdo (`.content`) usa `flex: 1` — expande automaticamente para ocupar o espaço liberado

### Implementação
- Classe CSS `.sidebar--collapsed` no `<aside class="sidebar">`
- Toggle via `toggleSidebar()` — adiciona/remove a classe + persiste no localStorage
- No load: `if (localStorage.getItem('grv_cs_sidebar_collapsed')) aside.classList.add('sidebar--collapsed')`
- CSS: quando `.sidebar--collapsed`, `.sb-logo-text`, `.sb-section`, labels e texto dos `.nav-item` ficam com `opacity: 0; width: 0; overflow: hidden`

---

## Dashboard — 3 Zonas de Decisão

O dashboard mantém o toggle 📊 Dashboard | ☰ Lista | ⊞ Kanban e o filtro por consultor. A estrutura interna das 3 zonas substitui o layout atual.

---

### Zona 1 — "Está tudo bem?" (above the fold)

**Objetivo:** O gestor bate o olho e já sabe se precisa agir. Nenhum scroll necessário.

#### Banner de Saúde do Portfólio
Faixa horizontal, largura total, antes dos KPIs. Cor e texto dinâmicos baseados em `pctAtrasado = kpis.atrasado / kpis.total`:

| Condição | Cor de fundo | Ícone | Frase |
|---|---|---|---|
| `< 10%` | `#F0FFF4` (verde claro), borda esquerda `#38a169` | ✅ | *"Portfólio saudável — {n} projetos ativos, tudo dentro do esperado"* |
| `10–20%` | `#FFFFF0` (amarelo claro), borda esquerda `#d69e2e` | ⚠️ | *"Atenção — {pct}% do portfólio precisa de acompanhamento ({n} projetos atrasados)"* |
| `> 20%` | `#FFF5F5` (vermelho claro), borda esquerda `#e53e3e` | 🚨 | *"Portfólio em risco — {pct}% atrasados, acima do limite saudável de 20%"* |

#### 3 Hero Metrics
Grid `1fr 1fr 1fr` abaixo do banner. Números 56px, bold, com breathing room.

| Metric | Valor | Trend |
|---|---|---|
| Projetos Ativos | `kpis.total - kpis.cancelado` | `▲▼ N vs mês ant.` |
| Atrasados | `kpis.atrasado` + `(pct%)` em subtexto | `▲▼ N vs mês ant.` em vermelho/verde |
| Concluídos no Mês | `kpis.concluido` | `▲▼ N vs mês ant.` |

**Trend simulado:** função `simulateTrend(value, seed)` — usa `Math.sin(seed) * 0.1 * value` arredondado para gerar variação determinística de ±10% (mesmo resultado a cada render, não aleatório).

#### Top 3 Alertas
Ao lado direito das hero metrics (grid `2fr 1fr`). Só os 3 mais críticos de `computeAlertas()`. Formato compacto: ícone + título + ação em uma linha. Link "Ver todos ↓" âncora para a Zona 2.

---

### Zona 2 — "Onde estão os problemas?"

**Objetivo:** Identificar produto e consultor com maior concentração de risco.

#### Chart: Distribuição por Status
- **Manchete narrativa** acima: `computeNarrativaDonut(kpis, clientes)` → ex: *"CPS concentra 70% dos atrasos — 7 dos 10 projetos atrasados são CPS"*
- Donut Chart.js com cores sólidas semânticas (já existentes — gradiente não é suportado nativamente em doughnut no Chart.js v4)
- Label central: número total em 28px + "projetos" em 11px, via plugin `afterDraw`
- Legenda à direita com percentual calculado em cada item (`(valor/total*100).toFixed(0)%`)

#### Chart: Performance por Consultor
- **Manchete narrativa**: `computeNarrativaConsultor(data)` → ex: *"Felipe concentra a maior carga de atrasos — 40% da carteira dele está atrasada"*
- Barras horizontais empilhadas (Chart.js, `indexAxis: 'y'`)
- Consultor com `pctAtrasado > 30%`: nome em **vermelho** no label do eixo Y, barra de atrasados mais saturada
- Tabela de performance abaixo do chart, ordenável (já existe, manter)

#### Alertas Completos (todos, não só top 3)
Seção expandida com todos os alertas de `computeAlertas()`. Mantém o layout de cards atual com melhorias visuais.

---

### Zona 3 — "Estamos batendo as metas?"

**Objetivo:** Comparar resultado atual com a meta acordada.

#### Gauges de Ativação (CPS e NX)
- Semi-donut mantido, mas com **linha de meta** desenhada via `Chart.js plugin afterDraw`
- A linha de meta (85%) é uma marca no arco, com label "meta 85%" ao lado
- Cor do valor: verde se `>= 85%`, vermelho se `< 85%`
- Subtexto: `{noPrazo}/{concluidos} concluídos no prazo`

#### Chart: Status por Produto
- **Manchete**: ex: *"NX tem taxa de conclusão 2× maior que CPS neste período"*
- Barras agrupadas existentes + linha de meta horizontal tracejada em laranja (`#E05A1E`, opacidade 0.6) no percentual de 85% convertido para quantidade
- Gradiente de preenchimento nas barras via plugin

#### Card: Backlog de Atrasos
- Mantém o card atual
- Adicionar indicador de tendência: `▲ 23 dias vs mês ant.` em vermelho se piorou

---

## Visual SAC-Level — Padrões Globais

### Tipografia hero
```css
.hero-value { font-size: 56px; font-weight: 800; line-height: 1; letter-spacing: -1px; }
.hero-trend  { font-size: 12px; font-weight: 600; margin-top: 4px; }
.hero-label  { font-size: 12px; color: var(--text3); text-transform: uppercase; letter-spacing: .06em; margin-bottom: 8px; }
```

### Section headers
```css
.dash-zone-title { font-size: 11px; font-weight: 700; color: var(--text3); text-transform: uppercase;
                   letter-spacing: .1em; padding-bottom: 12px; border-bottom: 1px solid var(--border);
                   margin-bottom: 20px; }
```

### Manchetes narrativas
```css
.chart-headline { font-size: 14px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.chart-subline  { font-size: 12px; color: var(--text3); margin-bottom: 16px; }
```

### Gradiente nas barras (Chart.js)
- Usar `ctx.createLinearGradient(0, 0, 0, height)` com `addColorStop(0, cor)` e `addColorStop(1, cor + '66')`
- Aplicar em `chartBarrasConfig` e `chartConsulConfig`

### Linha de meta nos charts
- Adicionar dataset extra tipo `'line'` com `data: Array(n).fill(metaValue)`, `borderColor: '#E05A1E'`, `borderDash: [4,4]`, `pointRadius: 0`, `borderWidth: 1.5`

---

## Funções Novas / Modificadas

| Função | Status | Descrição |
|---|---|---|
| `toggleSidebar()` | Nova | Adiciona/remove `.sidebar--collapsed`, persiste localStorage |
| `simulateTrend(value, seed)` | Nova | Retorna `{delta, dir}` — variação determinística ±10% |
| `renderTrendBadge(delta, dir, invertido)` | Nova | HTML do badge `▲▼ N vs mês ant.` com cor semântica |
| `computeSaudePortfolio(kpis)` | Nova | Retorna `{nivel, cor, icone, frase}` para o banner |
| `computeNarrativaDonut(kpis, clientes)` | Nova | String da manchete do donut |
| `computeNarrativaConsultor(data)` | Nova | String da manchete de performance |
| `renderZona1(kpis, clientes)` | Nova | HTML completo da Zona 1 |
| `renderZona2(kpis, clientes, consultores)` | Nova | HTML completo da Zona 2 |
| `renderZona3(kpis, clientes, consultores)` | Nova | HTML completo da Zona 3 |
| `renderDashboardProjetos()` | Modificada | Chama as 3 zonas em sequência |
| `initCharts()` | Modificada | Adiciona gradientes, plugin de meta line, manchetes |
| `chartDonutConfig()` | Modificada | Gradiente + label central via plugin |
| `chartBarrasConfig()` | Modificada | Gradiente + linha de meta dataset |
| `chartConsulConfig()` | Modificada | Label vermelho para consultores acima de 30% |
| `chartGaugeConfig()` | Modificada | Plugin afterDraw para linha de meta 85% |

---

## Casos de Borda

| Cenário | Comportamento |
|---|---|
| 0 projetos (filtro por consultor sem dados) | Banner verde "Nenhum projeto encontrado", Zonas 2 e 3 ocultadas |
| 0 atrasados | Banner verde, hero "Atrasados" = 0 sem trend badge |
| Sidebar colapsada em tela pequena | Permanece colapsada, sem responsividade extra |
| `pctAtrasado` = exatamente 10% ou 20% | `>= 10%` entra em atenção, `> 20%` em risco |
| Consultor com 0 projetos | Não aparece na tabela nem no chart de consultor |

---

## O que NÃO muda

- Toggle Dashboard / Lista / Kanban
- Filtro por consultor (dropdown)
- Toda a lógica de Lista e Kanban
- `getStatusDash()`, `computeDashboardKPIs()`, `computeAlertas()`, `computeBacklog()`, `computeAtivacao()`
- Telas Minha Carteira, Detalhe do Cliente, Criar Playbook
- Seed data (38 clientes, 7 consultores)
