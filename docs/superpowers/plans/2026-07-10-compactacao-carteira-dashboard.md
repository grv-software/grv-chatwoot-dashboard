# Compactação Minha Carteira e Dashboard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduzir padding e tamanho de avatar nas telas Minha Carteira (feed + kanban) e Dashboard para aumentar densidade de informação sem alterar lógica ou tipografia.

**Architecture:** Todas as mudanças são exclusivamente em CSS dentro do bloco `<style>` de `grv-cs-jornada.html`. Nenhum JS tocado. Cada task é um conjunto de edits em linhas específicas identificadas, seguido de verificação visual e commit.

**Tech Stack:** HTML/CSS puro. Arquivo único `grv-cs-jornada.html`. Branch `alteracoes`.

## Global Constraints

- Arquivo único: `grv-cs-jornada.html` — todas as edições aqui.
- Branch: `alteracoes`. Nunca commitar em `main`.
- Não alterar: `font-size` de corpo, `section-title`, lógica JS, formulários/modais.
- `.card-block` padding global: NÃO alterar — mudanças são por seletor específico.
- Verificação = abrir `grv-cs-jornada.html` no Chrome e navegar para cada tela.
- Commits por task concluída.

---

### Task 1: Feed da Minha Carteira — avatar menor + padding compacto

**Files:**
- Modify: `grv-cs-jornada.html` — linha 471 (`.feed-card`), linha 474 (`.fc-body`), linha 475 (`.fc-avatar`)

**Interfaces:**
- Consumes: nada de outras tasks.
- Produces: feed cards mais compactos visíveis na rota `#carteira` aba Feed.

- [ ] **Step 1: Reduzir padding do `.feed-card`**

Localizar linha 471:
```css
/* DE: */
.feed-card{display:flex;...;padding:12px 16px;...}
/* PARA: */
.feed-card{display:flex;...;padding:10px 14px;...}
```

Editar apenas o valor de `padding` — manter todos os outros valores intactos.

- [ ] **Step 2: Reduzir gap do `.fc-body`**

Localizar linha 474:
```css
/* DE: */
.fc-body{display:flex;gap:12px;...}
/* PARA: */
.fc-body{display:flex;gap:8px;...}
```

- [ ] **Step 3: Reduzir avatar `.fc-avatar`**

Localizar linha 475:
```css
/* DE: */
.fc-avatar{width:38px;height:38px;border-radius:10px;...;font-size:14px;font-weight:700;...}
/* PARA: */
.fc-avatar{width:28px;height:28px;border-radius:7px;...;font-size:12px;font-weight:700;...}
```

- [ ] **Step 4: Verificar**

Abrir `grv-cs-jornada.html` → Minha Carteira → aba Feed. Verificar:
- Cards de cliente ficaram ligeiramente mais compactos verticalmente
- Avatar menor (28px) mas legível
- Nenhum texto cortado ou sobreposição
- Hover ainda funciona (border laranja + sombra)

- [ ] **Step 5: Commit**

```
git add grv-cs-jornada.html
git commit -m "style(carteira): feed cards compactos — avatar 38→28px, padding 12→10px"
```

---

### Task 2: Kanban da Minha Carteira — cards e colunas compactos

**Files:**
- Modify: `grv-cs-jornada.html` — linha 496 (`.ck-wrap`), linha 501 (`.ck-card`), linha 648 (`.kcard`)

**Interfaces:**
- Consumes: nada de outras tasks.
- Produces: kanban mais denso na rota `#carteira` aba Kanban.

- [ ] **Step 1: Reduzir gap e padding do wrapper `.ck-wrap`**

Localizar linha 496:
```css
/* DE: */
.ck-wrap{display:flex;gap:14px;overflow-x:auto;padding:16px 24px}
/* PARA: */
.ck-wrap{display:flex;gap:10px;overflow-x:auto;padding:12px 16px}
```

- [ ] **Step 2: Reduzir padding do card `.ck-card`**

Localizar linha 501:
```css
/* DE: */
.ck-card{background:var(--surface);border-radius:var(--radius);padding:11px 13px;...}
/* PARA: */
.ck-card{background:var(--surface);border-radius:var(--radius);padding:9px 11px;...}
```

- [ ] **Step 3: Reduzir padding do card `.kcard` (kanban secundário)**

Localizar linha 648:
```css
/* DE: */
.kcard{background:var(--surface);border-radius:var(--radius);padding:12px;...}
/* PARA: */
.kcard{background:var(--surface);border-radius:var(--radius);padding:10px;...}
```

- [ ] **Step 4: Verificar**

Abrir `grv-cs-jornada.html` → Minha Carteira → aba Kanban. Verificar:
- Colunas com mais cards visíveis sem scroll horizontal adicional
- Padding interno dos cards reduzido mas conteúdo (nome, fase, barra de progresso) sem sobreposição
- Stripe colorida lateral (`.ck-stripe`) visível e não afetada
- Hover ainda funciona

- [ ] **Step 5: Commit**

```
git add grv-cs-jornada.html
git commit -m "style(carteira): kanban compacto — ck-card 11→9px, ck-wrap gap 14→10px, kcard 12→10px"
```

---

### Task 3: Dashboard — KPI cards e chips compactos

**Files:**
- Modify: `grv-cs-jornada.html` — linha 756 (`.kpi-card`), linha 872 (`.kpi-chip`)

**Interfaces:**
- Consumes: nada de outras tasks.
- Produces: dashboard mais compacto na rota `#visao-geral` (ou `/`).

- [ ] **Step 1: Reduzir padding do `.kpi-card`**

Localizar linha 756:
```css
/* DE: */
.kpi-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px 16px;box-shadow:var(--shadow-1)}
/* PARA: */
.kpi-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:10px 14px;box-shadow:var(--shadow-1)}
```

- [ ] **Step 2: Reduzir padding do `.kpi-chip`**

Localizar linha 872:
```css
/* DE: */
.kpi-chip{background:var(--surface);border-radius:var(--radius);padding:16px;...}
/* PARA: */
.kpi-chip{background:var(--surface);border-radius:var(--radius);padding:12px 14px;...}
```

- [ ] **Step 3: Verificar**

Abrir `grv-cs-jornada.html` → Dashboard (rota inicial ou `#visao-geral`). Verificar:
- KPI cards ficaram ligeiramente mais compactos
- O valor de 32px (`.kpi-value`) ainda é legível e não colide com label/sublabel
- Nenhum card com conteúdo cortado
- Chips de KPI igualmente compactos

- [ ] **Step 4: Commit**

```
git add grv-cs-jornada.html
git commit -m "style(dashboard): kpi-card 14→10px pad, kpi-chip 16→12px pad"
```

---

## Pós-implementação

Após as 3 tasks, navegar em sequência:
1. Dashboard → confirmar KPI cards
2. Minha Carteira Feed → confirmar cards e avatares
3. Minha Carteira Kanban → confirmar colunas
4. Clicar num cliente → confirmar que o header compactado (`d671156`) ainda está correto
5. Abrir aba Atividades de um cliente com atrasadas → confirmar que alert bar aparece
