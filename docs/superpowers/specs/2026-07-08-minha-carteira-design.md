# Minha Carteira — Design Spec

**Data:** 2026-07-08  
**Status:** Aprovado  
**Escopo:** Reestruturar Minha Carteira em 3 sub-abas role-aware (Agenda / Carteira / Desempenho) com persona switcher para teste

---

## Objetivo

Transformar Minha Carteira de uma lista passiva em uma **ferramenta operacional ativa**, diferente por papel: o analista de CS vê saúde e risco de churn; o analista de Implantação vê atraso, pausados e handoff. Ao abrir a tela, o consultor já sabe o que fazer primeiro — sem precisar varrer a lista inteira.

---

## Personas e dados de teste

Dois consultores fictícios adicionados ao mock data:

| Consultor | `id` | `tipo` | Clientes atribuídos |
|---|---|---|---|
| Priscila | `'priscila'` | `'implantacao'` | 6–8 clientes com playbooks ativos: 2 atrasados, 1 pausado, 1 sem engajamento (>14d), 2 em andamento, 1 pronto para handoff (≥90%) |
| João | `'joao'` | `'cs'` | 6–8 clientes `cs_ativo`: 2 com health <40, 1 silencioso (>30d), 2 com `proximaAcao` preenchida, 2 saudáveis |

**Campo novo no objeto consultor:** `tipo: 'cs' | 'implantacao'`

**Como detectar o papel na renderização:** `getConsultores().find(c => c.id === cid)?.tipo`

---

## Persona Switcher

**Onde:** dentro do cabeçalho de Minha Carteira, à direita do nome da tela.

**Visual:** dois pill-buttons lado a lado — sem borda, sem sombra. O ativo usa `background: var(--primary)`, texto branco, `font-weight:600`. O inativo usa `background: transparent`, `color: var(--text3)`, `font-weight:400`. Tamanho: 12px, `padding: 4px 10px`, `border-radius: 20px`. Transição `background 150ms ease`.

**Comportamento:** `onclick="setConsultorAtivo('priscila'); renderCarteira()"` — a troca re-renderiza tudo, incluindo a sub-aba ativa.

**Nota de produção:** em produção, o switcher não existe — `getConsultorAtivo()` retorna o usuário logado. O switcher é affordance de teste apenas.

---

## Navegação — 3 Sub-abas

### Estado

```javascript
const CARTEIRA_TAB_KEY = 'grv_cs_tab_carteira';
let _carteira_tab = localStorage.getItem(CARTEIRA_TAB_KEY) || 'agenda';
```

### Nav dropdown

O item "Minha Carteira" no topnav ganha um chevron e um dropdown com 3 opções:
- Agenda
- Carteira
- Desempenho

Comportamento idêntico ao dropdown de Projetos GRV já existente. `onclick` de cada item chama `setCarteiraTab('agenda')` etc.

### Tab bar interna

Dentro da seção, uma barra de tabs fina (igual às abas de detalhe do cliente). Destaque via `border-bottom: 2px solid var(--primary)` na tab ativa. Tabs: **Agenda · Carteira · Desempenho**.

---

## Aba Agenda

### Princípio visual

**Nenhum elemento visual grita.** As seções são separadas por espaçamento (16px), não por divisórias pesadas. O vermelho aparece apenas nas badges de urgência — o resto usa os neutros do sistema.

### Estrutura — seções colapsáveis

Cada seção tem um cabeçalho em linha:

```
[ícone SVG]  Label da seção          [chip com count]  [chevron]
```

- Label: `12px / font-weight:600 / color: var(--text2) / text-transform: uppercase / letter-spacing: 0.05em`
- Chip de count: `10px / font-weight:700 / padding: 1px 6px / border-radius: 10px`
  - Seção de urgência: chip vermelho `#dc2626` com texto branco
  - Seções neutras: `background: var(--border)` com `color: var(--text2)`
- Chevron: `16px / color: var(--text4)`, rotaciona 90° quando colapsada
- Body da seção: lista de cards (ver card abaixo)
- Seção 1 sempre expandida; Seções 2 e 3 colapsadas por padrão

### Cards de Agenda

Card horizontal compacto — altura fixa `52px`, `padding: 10px 12px`, `border-radius: var(--radius-sm)`, `background: var(--surface)`, sombra mínima `box-shadow: 0 1px 3px rgba(0,0,0,.06)`.

**Layout interno:**
```
[stripe 3px]  [avatar 28px]  [nome + motivo da urgência]  [info direita]  [··· se urgente]
```

- Stripe esquerda 3px: vermelho se urgente, amarelo se atenção, verde se saudável
- Avatar: círculo 28px com gradiente (já existe `avatarGradiente()`)
- Nome: `13px / font-weight:600 / color: var(--text)`
- Motivo (subtexto): `11px / color: var(--text3)` — "Health 38 · 4d ↓" ou "Pausado · 18d sem contato" ou "Agendar revisão trimestral"
- Info direita (CS): health score em circle `32px` com cor + seta de tendência ↑↓→ em `10px`
- Info direita (Implantação): progresso `XX%` em `font-weight:700` + status badge existente
- Botão `···` aparece apenas em urgentes, alinhado à direita extrema

**Seta de tendência:**
- ↑ verde `var(--green)` se health subiu ≥ 5 pts na semana
- ↓ vermelho `#dc2626` se caiu ≥ 5 pts
- → cinza `var(--text4)` se estável (variação < 5 pts)
- Calculada comparando `c.healthScore` com `c.healthHistory?.at(-1)?.valor` (último registro armazenado)

### Seções por papel

**João (CS):**

| # | Label | Critério | Colapsada? |
|---|---|---|---|
| 1 | ⚡ Atenção agora | `isUrgente(c)` — health < 40 ou > 30d sem contato | Não |
| 2 | Próxima ação pendente | `c.proximaAcao` preenchido e não urgente | Sim |
| 3 | Em dia | Resto, ordenado por health asc | Sim |

**Priscila (Implantação):**

| # | Label | Critério | Colapsada? |
|---|---|---|---|
| 1 | ⚡ Atenção agora | `isUrgente(c)` — atrasado ou > 14d sem contato ou pausado | Não |
| 2 | Pronto para handoff | `calcProgresso(meusPbs) >= 90` e não urgente | Sim |
| 3 | Em andamento | Resto, ordenado por progresso asc | Sim |

### Empty state

Quando Seção 1 estiver vazia:

```
[ícone SVG checkmark-circle, 32px, color: var(--green)]
"Sua carteira está sob controle hoje."
[12px / color: var(--text3) / text-align: center / padding: 32px]
```

Seções 2 e 3 continuam renderizando normalmente.

---

## Aba Carteira

### Feed card — melhorias

O card existente mantém sua estrutura. Mudanças:

1. **Tendência do health score:** seta ↑↓→ ao lado do círculo de health, `10px`, mesma lógica da Agenda
2. **Próxima ação:** linha adicional abaixo do `fc-meta`, apenas se `c.proximaAcao` preenchido
   - Estilo: `11px / font-style: italic / color: var(--text3) / max-width: 200px / white-space: nowrap / overflow: hidden / text-overflow: ellipsis`
3. **Badge Pausado:** se playbook pausado, aparece ao lado do status badge — pill `10px / background: var(--text4) @ 15% opacity / color: var(--text3)`
4. **Nada mais é adicionado.** Não aumentar altura do card.

### Kanban — colunas por papel

**João (CS):** colunas por tier de saúde:
```
[ Crítico  health < 40 ]  [ Atenção  40–70 ]  [ Saudável  > 70 ]
```
Cabeçalho da coluna mostra count e cor semântica no label (vermelho / amarelo / verde).

**Priscila (Implantação):** colunas por etapa (mantém `KANBAN_COLUNAS` atual).

### Persistência de view

Chave separada no localStorage por papel:
- `grv_cs_view_carteira_cs` para João
- `grv_cs_view_carteira_impl` para Priscila

Evita que trocar de persona redefina a preferência de view da outra persona.

---

## Aba Desempenho

### Layout

Grid 2×2 de KPI chips + lista de destaques abaixo. Total da tela: cabe em 1 viewport sem scroll.

### KPI chip

Card branco `background: var(--surface)`, `border-radius: var(--radius)`, `padding: 16px`, `box-shadow: 0 1px 3px rgba(0,0,0,.06)`.

```
[valor grande]
[label pequeno]
```

- Valor: `28px / font-weight: 800 / font-variant-numeric: tabular-nums`
- Label: `10px / font-weight: 500 / text-transform: uppercase / letter-spacing: 0.06em / color: var(--text3)`
- Cor do valor: semântica quando aplicável (vermelho se KPI ruim, verde se bom, neutro se informativo)

**João (CS):**

| KPI | Valor | Cor |
|---|---|---|
| Health médio | média de `calcHealthScore(c)` | < 50 → vermelho; ≥ 70 → verde; resto → neutro |
| Contactados no mês | `% com getDiasUltimoContato(c) <= 30` | < 60% → amarelo; ≥ 80% → verde |
| CSAT médio | média de `c.csat` (onde preenchido) | ≤ 3 → vermelho; ≥ 4 → verde |
| Em risco | count `isUrgente(c)` | > 0 → vermelho; 0 → verde |

**Priscila (Implantação):**

| KPI | Valor | Cor |
|---|---|---|
| Projetos em dia | `% onde getStatus(c) !== 'Atrasado'` | < 70% → vermelho; ≥ 90% → verde |
| Progresso médio | média de `calcProgresso(meusPbs)` | neutro (informativo) |
| Pausados | count playbooks `estado === 'pausado'` | > 0 → amarelo; 0 → verde |
| Prontos para handoff | count `calcProgresso >= 90` | > 0 → verde (positivo) |

### Lista de destaques

Abaixo do grid 2×2, um título `12px / uppercase` + lista de 3 itens compacta.

- CS: "3 clientes com maior queda de health esta semana" — nome + "health X ↓ -Y"
- Implantação: "3 projetos mais críticos" — nome + "X dias de atraso" ou "Pausado · Xd"

Se não houver itens (tudo bem): empty state curto — *"Nada crítico esta semana."*

---

## Extensão de `isUrgente` para incluir pausado

A função atual verifica `getStatus(c) === 'Atrasado' || getDiasUltimoContato(c) > 14` para não-cs_ativo. Precisa incluir playbook pausado:

```javascript
function isUrgente(c) {
  if (c.status !== 'cs_ativo') {
    var pb = (c.ativPlaybooks || []).find(p => p.donoId === getConsultorAtivo());
    var pausado = pb && pb.estado === 'pausado';
    return getStatus(c) === 'Atrasado' || getDiasUltimoContato(c) > 14 || pausado;
  }
  var h = calcHealthScore(c);
  return (h !== null && h < 40) || getDiasUltimoContato(c) > 30;
}
```

A lógica CS (`cs_ativo`) não muda.

## Dados de `healthHistory` no mock

Cada cliente dos dois consultores de teste recebe um campo `healthHistory` simples:

```javascript
healthHistory: [{ data: '2026-07-01', valor: 55 }]  // valor de 7 dias atrás
```

A seta de tendência compara `calcHealthScore(c)` atual com `c.healthHistory?.at(-1)?.valor`. Se o campo não existir, seta não aparece (safe fallback).

---

## Princípios visuais (ui-ux-pro-max)

- **Densidade controlada:** no máximo 3 informações por card de Agenda, 4 por card de feed. Nunca empilhar texto corrido.
- **Hierarquia via peso tipográfico**, não via cor. A urgência aparece no stripe lateral e na badge — o texto em si usa escala de cinza.
- **Espaçamento 8pt:** gap entre cards 8px, gap entre seções 16px, padding interno dos cards 10–16px.
- **Touch targets ≥ 44px:** botões `···`, tabs, pills do switcher e chevrons de seção.
- **Cor semântica separada do accent:** vermelho `#dc2626` é exclusivo de urgência/risco. O laranja `var(--primary)` é exclusivo de ações primárias. Nunca misturar.
- **SVG para ícones**, nunca emoji. Ícones da lib já usada no app (stroke, 2px).
- **Sem horizontal scroll** em nenhuma sub-aba.
- **Foco visível** em todos os interativos (tab key navigation).
- **prefers-reduced-motion:** o pulse animation do badge de urgência respeita `@media (prefers-reduced-motion: reduce)`.

---

## O que não muda

- Clique na linha/card abre o cliente (comportamento existente).
- Função `isUrgente(c)` — reutilizada sem alteração da lógica.
- Funções `calcHealthScore`, `getStatus`, `getDiasUltimoContato`, `calcProgresso` — sem alteração.
- Rota `#carteira` permanece, sub-abas são estado interno (não rotas separadas).
- O restante do app (Projetos GRV, Vencimentos, cliente detail) não é tocado.
