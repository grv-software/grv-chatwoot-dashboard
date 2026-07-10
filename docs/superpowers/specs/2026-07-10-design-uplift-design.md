# GRV CS Jornada — Design Uplift

**Status:** Aprovado pelo usuário  
**Data:** 2026-07-10  
**Escopo:** Uplift visual — tokens, componentes e micro-interações. Estrutura de telas e rotas não mudam.  
**Foco:** Minha Carteira · Painel de Atividades · Detalhe do Cliente (telas mais usadas); demais telas recebem os tokens automaticamente.

---

## Diagnóstico

Seis problemas identificados no CSS atual:

1. **Profundidade única** — `--shadow: 0 1px 3px rgba(0,0,0,.07)` aplicada a tudo. Cards, modais e tabelas ficam no mesmo plano visual.
2. **7 padrões de card** — `.metric-card`, `.dash-kpi-card`, `.hero-card`, `.proj-kpi`, `.proj-hero-card`, `.painel-kpi-card`, `.dash-backlog-stat` fazem coisas similares com espaçamentos e tipografia diferentes.
3. **Laranja sem reserva** — `--primary` aparece em botões, barras de progresso, nav ativo, links, badges, avatares. Perde força por estar em tudo.
4. **Fundo azulado genérico** — `--bg: #f8f9fb` não tem relação tonal com `#E05A1E`. Cria frieza desconectada da identidade GRV.
5. **Emoji como ícone** — `.kc-emoji` no Kanban, `.lista-section-emoji` nas listas de clientes, `.es-icon` nos empty states.
6. **Hover sem resposta** — `.nav-item:hover { background: none }` — a interface não responde ao cursor.

---

## Novo sistema de design tokens

### Cores — warm stone palette

```css
/* Neutros quentes — relacionados tonalmente ao laranja */
--bg:       #F5F3F0;   /* substitui #f8f9fb */
--surface:  #FFFFFF;
--surface-2:#FAF9F8;   /* fundo de áreas internas (ex: col esquerda de atividades) */
--border:   #E2DDD7;   /* substitui #e8ecf0 */
--border-2: #EDE9E4;   /* substitui #f0f2f5 */

/* Texto */
--text:  #1A1917;      /* substitui #1a202c */
--text2: #534E4A;      /* substitui #4a5568 */
--text3: #8A847F;      /* substitui #718096 */
--text4: #B5AFA9;      /* substitui #a0aec0 */

/* Acento — reservado para ações e estado ativo */
--primary:       #E05A1E;   /* mantém */
--primary-light: rgba(224,90,30,.10);   /* mantém */

/* Semântico — sem alteração */
--green: #16A34A;  --green-bg: rgba(22,163,74,.1);
--red:   #DC2626;  --red-bg:   rgba(220,38,38,.1);
--yellow:#D97706;  --yellow-bg:rgba(217,119,6,.1);
```

### Sombras — sistema de 3 níveis

```css
--shadow-0: none;                                                          /* bordas de linha — tabelas, linhas */
--shadow-1: 0 1px 3px rgba(0,0,0,.05), 0 1px 2px rgba(0,0,0,.04);        /* cards padrão */
--shadow-2: 0 4px 14px rgba(0,0,0,.08), 0 2px 4px rgba(0,0,0,.04);       /* dropdowns, nav-dropdown, popovers */
--shadow-3: 0 12px 32px rgba(0,0,0,.12), 0 4px 8px rgba(0,0,0,.06);      /* modais, toasts */

/* Remove --shadow atual e substitui por --shadow-1 em todo uso */
```

### Border-radius — padronização

```css
--radius:    10px;   /* era 9px — 1px a mais dá toque mais moderno */
--radius-sm: 6px;    /* inputs, chips, badges, botões pequenos */
/* 12px em modais vira --radius (10px). Demais valores hardcoded eliminados. */
```

### Escala tipográfica

```
32px / 800  / ls -1.2px — valores de KPI (font-variant-numeric: tabular-nums)
20px / 700  / ls -0.3px — títulos de página (.page-title)
16px / 700              — títulos de seção (novo tier — preenche lacuna entre body e page-title)
14px / 400              — body default (mantém)
12px / 400              — meta, descrições
11px / 600  / ls 0.03em — labels inline (mantém .nav-drop-header)
10px / 700  / ls 0.08em — rótulos em caps (CRÍTICO, LABEL, etc.) — substitui os 9px-11px atuais
```

---

## Componente canônico: KPI card

Um único padrão substitui todos os 7 existentes. Estrutura invariável:

```html
<div class="kpi-card">
  <div class="kpi-label">RÓTULO</div>       <!-- 10px caps, --text4 -->
  <div class="kpi-value">42</div>            <!-- 32px 800, tabular-nums, cor semântica -->
  <div class="kpi-sublabel">descrição</div>  <!-- 11px, --text3 -->
</div>
```

```css
.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 16px;
  box-shadow: var(--shadow-1);
}
.kpi-label {
  font-size: 10px; font-weight: 700;
  text-transform: uppercase; letter-spacing: .08em;
  color: var(--text4); margin-bottom: 8px;
}
.kpi-value {
  font-size: 32px; font-weight: 800; line-height: 1;
  letter-spacing: -1.2px; font-variant-numeric: tabular-nums;
}
.kpi-sublabel { font-size: 11px; color: var(--text3); margin-top: 3px; }

/* Variações de cor — só o valor muda */
.kpi-card.v-red    .kpi-value { color: var(--red); }
.kpi-card.v-amber  .kpi-value { color: var(--yellow); }
.kpi-card.v-orange .kpi-value { color: var(--primary); }
.kpi-card.v-green  .kpi-value { color: var(--green); }
```

**Classes a remover:** `.metric-card`, `.mc-label`, `.mc-value`, `.mc-accent`, `.mc-green`, `.mc-red`, `.mc-gray`, `.dash-kpi-card`, `.dash-kpi-label`, `.dash-kpi-value`, `.pkpi-lbl`, `.pkpi-val`, `.proj-kpi`, `.painel-kpi-card` e variantes.

---

## Micro-interações

### Feed cards e activity rows
```css
.feed-card {
  transition: border-color .12s, box-shadow .12s, transform .1s;
}
.feed-card:hover {
  border-color: var(--primary);
  box-shadow: var(--shadow-2);
  transform: translateY(-1px);
}
```

### Nav item hover
```css
.nav-item:hover {
  background: rgba(0,0,0,.03);   /* era: background: none */
  color: var(--text);
}
```

### Botão Concluir no Painel de Atividades
```css
.painel-btn-concluir:hover {
  background: var(--green-bg);
  color: var(--green);
  border-color: rgba(22,163,74,.2);
}
```

### Laranja reservado
Barras de progresso (`.prog-fill`, `.fc-progbar`, `.at-pb-bar-fill`) passam a usar a cor semântica do status do cliente (green/yellow/red) em vez de `var(--primary)`. O laranja fica exclusivo para: botão primário, nav ativo, atividades com prazo hoje, toggle ativo.

---

## Ícones — remoção de emoji

Todas as ocorrências de emoji como ícone funcional são substituídas por SVG inline do set atual (mesmo viewBox 24x24, stroke="currentColor"):

| Local | Emoji atual | SVG proposto |
|-------|-------------|--------------|
| Kanban col "Novo" | 🆕 | `<rect x="12" y="5" width="7" height="7"/>` (layers) |
| Kanban col "Andamento" | ⚙️ | gear icon |
| Kanban col "Pause" | ⏸️ | pause circle |
| Kanban col "Concluído" | ✅ | check circle |
| Lista section header | 🏢 etc. | building icon |
| Empty state `.es-icon` | qualquer emoji | SVG 32px da categoria relevante |

A classe `.kc-emoji` é removida. `.lista-section-emoji` é substituída por `.lista-section-icon` com `<svg class="lista-section-icon">`.

---

## Stripe lateral de criticidade

Atividades no Painel de Atividades e cards de clientes na Minha Carteira ganham stripe lateral de 3px (já existente via `.fc-stripe`) indicando o status sem precisar ler o número:

```css
.act-row         { border-left: 3px solid transparent; }
.act-row.crit    { border-left-color: var(--red);     background: rgba(220,38,38,.04); }
.act-row.atrasado{ border-left-color: var(--yellow);  background: rgba(217,119,6,.04); }
.act-row.hoje    { border-left-color: var(--primary); background: rgba(224,90,30,.04); }
```

---

## Mudanças por tela

### Minha Carteira
- Feed list: hover com lift + borda laranja
- Barra de progresso do cliente: cor semântica (green/yellow/red por health score)
- KPI cards da aba Desempenho: novo padrão `.kpi-card`

### Painel de Atividades
- KPI strip: novo padrão `.kpi-card`
- Activity rows: stripe lateral, ícones SVG por tipo de atividade
- Botão Concluir: hover verde
- Toolbar toggle e tabs: tokens novos

### Detalhe do Cliente
- Header: tokens atualizados (bg, border, shadow-1)
- Barra de progresso das fases: cor semântica
- Empty states: ícone SVG no lugar de emoji

### Projetos GRV (telas secundárias)
- `.proj-kpi` substituído por `.kpi-card`
- Tokens de cor e border atualizados automaticamente via :root
- `.vg-card` (dark card): mantido sem alteração — já funciona bem

---

## O que não muda

- Estrutura HTML de todas as telas
- Hash routing e funções JavaScript
- `--primary: #E05A1E` — cor do acento mantida
- `.nav-item.active::after` — underline laranja no nav ativo
- `.ov-panel` (overlay lateral) — componente já bem executado
- `.vg-card` (dark gradient card) — único componente que já tem "alma"
- Dados, modais, formulários, lógica de playbooks

---

## Não incluso neste uplift

- Dark mode completo (requereria auditoria de todas as telas)
- Redesign de layout ou navegação
- Novos componentes ou funcionalidades
- Fonte customizada
