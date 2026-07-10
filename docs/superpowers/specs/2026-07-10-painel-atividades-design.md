# Painel de Atividades — Design Spec

**Status:** Aprovado pelo usuário  
**Data:** 2026-07-10  
**Origem:** Redesign da tela "Vencimentos"

---

## Contexto

A tela atual de "Vencimentos" mostra atividades atrasadas com filtros por consultor, urgência, etapa e produto. Ela funciona, mas é operacionalmente básica: exibe uma única lista flat sem distinção de prioridade operacional clara, sem visão de planejamento, e sem agrupamento por cliente.

**O que muda:** Renomear para "Painel de Atividades" e estruturar em três sub-abas com KPIs no topo.

---

## Nome e Rota

- **Label no nav:** `Painel de Atividades` (ícone de sino permanece)
- **Rota hash:** mantém `vencimentos` (sem quebrar bookmarks/histórico)
- **Dropdown no nav:** ativa ao hover, com três itens que setam `_venc_tab` e re-renderizam a tela

---

## Estrutura da Tela

### 1. KPI Strip (sempre visível)

Quatro cards em linha horizontal:

| Card | Valor | Cor |
|------|-------|-----|
| Críticas | atividades vencidas há 4+ dias da minha fila | vermelho `#dc2626` |
| Vencem hoje | diff === 0, minha fila | amarelo `#eab308` |
| Esta semana | diff 1–7 dias, todas as filas | laranja `var(--primary)` |
| SLA em dia | % de atividades com prazo não vencido / total ativas | verde `#22c55e` |

### 2. Toolbar

- **Toggle "Minha fila / Time todo"** — default: Minha fila. Filtra por `getConsultorAtivo()` vs sem filtro
- **Tabs "A resolver / A planejar / Por cliente"** — controla qual sub-view é exibida

### 3. Sub-views

#### A resolver (default)
Agrupamentos em ordem de urgência:

- **Crítico** — `diff < -3` (vencido há 4+ dias) — stripe vermelho
- **Atrasado** — `-3 ≤ diff < 0` (vencido há 1–3 dias) — stripe amarelo
- **Vence hoje** — `diff === 0` — stripe laranja (primary)

Cada linha (`venc-row`):
- Ícone tipo de atividade (mapeado por `at.tipo`)
- Nome da atividade — CLIENTE (link clicável para `#cliente/ID`)
- Meta: consultor responsável · segmento
- Badge de prazo (ex: "Venceu há 3 dias" / "Hoje")
- Botão **✓ Concluir** — expande campo de nota inline

**Inline note:** ao clicar Concluir, aparece um `<textarea>` abaixo da linha com botões "Salvar" e "Cancelar". Salvar chama `concluirVencComNota(evt, clienteId, pbId, atId, notaId)` que:
1. Marca `at.status = 'concluida'`
2. Adiciona entrada em `at.registros` com o texto da nota (se preenchida)
3. Re-renderiza

Estado vazio (sem atividades na fila): mensagem "Tudo em dia! ✅"

#### A planejar
- Atividades com `diff > 0 && diff ≤ 30` (não vencidas, próximos 30 dias)
- Agrupadas por semana: Esta semana (1–7d) / Próxima semana (8–14d) / Em 2–3 semanas (15–21d) / Em 3–4 semanas (22–30d)
- Linhas mais simples: data formatada, nome da atividade, cliente, consultor, badge "Em X dias"
- Sem botão Concluir (planejamento, não execução)

#### Por cliente
- **Chips multi-select** no topo: 🔴 Vencidas / 🟡 A vencer / 🟢 Em dia — default: apenas "Vencidas" ativo
- Ao menos um chip deve estar sempre ativo (não deixa desmarcar o último)
- Clientes ordenados por criticidade: mais vencidas primeiro, depois por health score crescente
- Cada cliente: acordeão com header (avatar com `avatarGradiente()`, nome, health dot, stats) e linhas das atividades filtradas
- Clientes sem atividades no filtro atual não aparecem

---

## Dropdown do Nav

Estrutura usando o padrão existente (`.nav-group` + `.nav-dropdown` + `.nav-drop-item`):

```
PAINEL DE ATIVIDADES
────────────────────
A resolver       [badge: count vencidas]
A planejar       [badge: count próximos 7d]
Por cliente
```

Clicar em um item do dropdown chama `setVencTab('resolver'|'planejar'|'cliente')` que seta `_venc_tab` e navega para `#vencimentos`.

---

## Estado Global

Novos globais (adicionados junto com os `_venc_filter_*` existentes):

```javascript
let _venc_tab   = 'resolver';    // 'resolver' | 'planejar' | 'cliente'
let _venc_fila  = 'minha';       // 'minha' | 'time'
let _venc_chips = ['vencidas'];  // subset de ['vencidas','avencer','emdia']
```

---

## Dados

Todas as sub-views usam `getTodasVencidas(maxDiasFuturos)` como fonte:
- A resolver: `getTodasVencidas(0)` — diff ≤ 0
- A planejar: `getTodasVencidas(30)` filtrado para `diff > 0`
- Por cliente: `getTodasVencidas(30)` para vencidas+avencer; emdia seria diff > 30 (sem limite útil — omitir esse chip ou tratar separado)

KPIs: calculados por `getKpiVencimentos()` que agrega contagens e calcula SLA.

---

## CSS Adições

Prefixo `.painel-*` para todos os novos elementos. Reutilizar classes `.venc-row`, `.venc-stripe`, `.venc-avatar`, `.venc-info`, `.venc-nome`, `.venc-meta`, `.venc-group`, `.venc-group-label`, `.venc-dot` já existentes.

Novas classes: `.painel-kpi-strip`, `.painel-kpi-card`, `.painel-toolbar`, `.painel-toggle-group`, `.painel-toggle-btn`, `.painel-tabs`, `.painel-tab`, `.painel-due` (+ modificadores), `.painel-note-area`, `.painel-note-input`, `.painel-note-save`, `.painel-note-cancel`, `.painel-week-header`, `.painel-filter-chips`, `.painel-chip`, `.painel-client-group`, `.painel-client-header`, `.painel-chevron`, `.painel-client-rows`, `.painel-client-row`, `.venc-empty`.

---

## Não muda

- Hash route `vencimentos` — permanece idêntico
- `concluirVenc()` — permanece (usado em outros contextos)
- `getTodasVencidas()` — permanece sem alteração
- `updateVencBadge()` — permanece (conta apenas diff ≤ 0, sem filtro de consultor)
- Filtros avançados da versão atual (dropdowns de consultor/produto/etapa/busca) — **removidos** da nova renderização (substituídos pelo toggle Minha fila / Time todo e pelos chips da view Por cliente)
