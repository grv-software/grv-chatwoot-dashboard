# GRV CS — Compactação: Minha Carteira e Dashboard

**Status:** Aprovado pelo usuário  
**Data:** 2026-07-10  
**Contexto:** Continuação das correções cirúrgicas de layout (`d671156`). As mudanças de header/avatar/strip/at-cols já foram aplicadas. Este spec cobre as duas telas restantes de uso diário.

---

## Diagnóstico

**Minha Carteira (feed + kanban):** Os cards de feed e kanban têm padding interno de ~14–16px e avatares de ~36px. Em telas com muitos clientes, o CS precisa rolar mais do que o necessário para ver a lista completa. A coluna de kanban também tem `gap` entre cards que pode ser reduzido sem perder separação visual.

**Dashboard:** O grid de KPI cards usa `gap: 16px` e cada `.kpi-card` tem `padding: 14px 16px`. Com 6–8 cards no dashboard, o excesso de gap acumula ~80px de espaço extra. As seções também têm `margin-bottom` generoso que pode ser ajustado.

---

## Escopo

### Minha Carteira — Feed

**O que muda:**
- `.feed-card` padding: reduzir de `14px 16px` → `10px 14px`
- Avatar nos feed cards: reduzir de `36px` → `28px`
- Gap entre feed cards: `10px` → `8px`

**O que não muda:** conteúdo interno dos cards (nome, segmento, health badge, último contato), lógica de ordenação, filtros.

### Minha Carteira — Kanban

**O que muda:**
- `.kcard` padding: reduzir de `12px` → `10px`
- Gap entre colunas do kanban: verificar e reduzir se > 10px
- Avatar nos kcards: reduzir se > 28px

**O que não muda:** número de colunas, lógica de drag-and-drop (se existir), badges de status.

### Dashboard

**O que muda:**
- Grid gap de KPI cards: `16px` → `10px`
- `.kpi-card` padding: `14px 16px` → `10px 14px`
- Espaçamento entre seções (`margin-bottom` das zonas): verificar e reduzir onde > 20px

**O que não muda:** lógica de cálculo dos KPIs, gráficos, tabelas de consultores.

---

## Regras gerais

- Nenhuma mudança em `font-size` de corpo — 12–13px se mantém em todas as telas
- `section-title` permanece 13–14px — já está no limite de legibilidade
- Formulários e modais: padding interno NÃO é reduzido — usabilidade de input requer mais espaço
- `.card-block` global: NÃO alterar — mudanças são cirúrgicas por componente, não por token global
- Nenhuma mudança em lógica JS, roteamento ou dados

---

## O que não está neste spec

- Aba Agenda da Carteira (menos usada, deixar para revisão futura)
- Tela de Vencimentos (estrutura de lista já é naturalmente densa)
- Telas de Implantação, Portfólio, Criar (uso ocasional, não prioritário)
- Dark mode (não existe no sistema ainda)
