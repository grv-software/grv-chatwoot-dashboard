# GRV CS — Redesign do Overlay de Atividade

**Status:** Aprovado pelo usuário
**Data:** 2026-07-13
**Contexto:** O overlay lateral de atividade (`.ov-panel`, 420px) está visualmente cru — campos de data como inputs genéricos, sem hierarquia clara, sem contexto do playbook. Este spec cobre o redesign completo do painel mantendo toda a lógica JS existente.

---

## Direção visual aprovada

**"C — Minimal Premium com 6 zonas"**: painel lateral fixo (420px) com stripe de status no topo, header compacto com título + tag + meta inline, KPI strip horizontal, tabs, body e footer integrado.

---

## Estrutura: 6 zonas

### Zona 1 — Stripe de status (4px)
Barra horizontal de 4px no topo do painel. Cor muda conforme estado da atividade:

| Estado       | Cor da stripe              | CSS token       |
|--------------|----------------------------|-----------------|
| Concluída    | `#38a169` → `#68d391`      | `--green`       |
| Atrasada     | `#e53e3e` → `#fc8181`      | `--red`         |
| Vence hoje   | `#d69e2e` → `#f6d860`      | `--yellow`      |
| Pendente     | `#E2DDD7` → `#EDE9E4`      | `--border`      |

Gradiente linear horizontal (`90deg`). Implementado como `background: linear-gradient(...)` no elemento estático do HTML — atualizado via `style` no `openAtividade()`.

### Zona 2 — Header (2 linhas)

**Linha 1:** Título da atividade (18px, weight 800, `--text`, `letter-spacing: -.5px`) + tag de status (pill, 9px uppercase, cor dinâmica) alinhados na mesma linha com `justify-content: space-between`.

**Linha 2 (meta inline):** mini-avatar do responsável (18×18px, border-radius 4px, gradiente laranja) + nome do responsável + `·` + nome do playbook + `·` + datas `DD/MM → DD/MM/AA`. Tudo na mesma linha, `font-size: 11px`, `color: --text4`, com spans para destacar valores em `--text3 font-weight: 600`.

**Padding do header:** `18px 20px 14px`. `border-bottom: 1px solid --border-2`.

As datas continuam sendo inputs `<input type="date">` internamente (para edição via `saveOvDatas()`), mas ficam **ocultos** — a linha meta exibe os valores formatados. Ao clicar na linha de datas, revela os inputs inline (toggle).

### Zona 3 — KPI strip (3 células)

Grid `1fr 1fr 1fr` sem gap, separadas por `border-right: 1px solid --border-2`. Sem border-top (a border-bottom do header já separa).

Células:
- **Início:** label `INÍCIO` (8px uppercase, `--text4`) + valor `DD/MM/AA` (13px, weight 800, `--text`) + hint editável (click abre input de data)
- **Prazo:** label `PRAZO` + valor + badge de urgência quando aplicável (`Vence em Xd` em amarelo, `Xd atrás` em vermelho)
- **Progresso:** label `PROGRESSO` + valor `N/M` (weight 800) com a cor da stripe + mini barra de progresso (4px, `border-radius: 2px`)

Padding de cada célula: `10px 14px`. Click nas células de data revela o `<input type="date">` inline.

### Zona 4 — Tabs

Três tabs: **Registro**, **Checklist**, **Anotação**. Layout idêntico ao atual (`.ov-tab`, `.ov-tab.active`). Apenas reestilização: tab ativa usa `color: --primary` + `border-bottom: 2px solid --primary`. Tab inativa: `color: --text3`. `font-size: 11px`, `font-weight: 600`. `padding: 10px 0`. `border-bottom: 1px solid --border-2`.

### Zona 5 — Body

Padding `16px 20px`. Conteúdo renderizado dinamicamente por `renderOverlayTab()` (sem mudança de lógica).

**Aba Registro:**
- Input row: mini-avatar (28×28px, border-radius 8px) + textarea (`background: --bg`, `border: 1.5px solid --border`, `border-radius: 9px`, `padding: 9px 12px`, `min-height: 56px`, `font-size: 12px`)
- Abaixo do textarea: linha com hint `"Registre um andamento ou decisão"` (`font-size: 10px`, `--text4`) + botão `Registrar` (`background: --primary`, `border-radius: 7px`, `font-size: 11px`)
- Feed de registros: avatar (22×22px) + nome + hora + texto — layout atual mantido, apenas padding e tamanhos revisados
- Empty state: `"Nenhum registro ainda."` centralizado, `font-size: 12px`, `--text4`

**Aba Checklist:** sem mudança estrutural — apenas herda o novo padding do body.

**Aba Anotação:** sem mudança estrutural.

### Zona 6 — Footer

`padding: 11px 20px`. `border-top: 1px solid --border-2`. `background: --bg` (levemente diferente do body branco). Layout flex: `justify-content: space-between`.

- **Esquerda:** texto `"N/M atividades concluídas"` — N em `--green font-weight: 800`, resto em `--text3 font-size: 11px`
- **Direita:** botão principal de ação:
  - Pendente: `"✓ Marcar como Concluída"` — `background: --primary`, `color: #fff`, `border-radius: 9px`, `padding: 9px 22px`, `font-size: 12px`, `font-weight: 700`
  - Concluída: `"✓ Concluída"` — `background: transparent`, `color: --green`, `border: 1.5px solid --green`, mesmo padding

---

## Estados visuais

| Estado     | Stripe                | Tag                              | Botão footer           |
|------------|-----------------------|----------------------------------|------------------------|
| Concluída  | verde                 | `Concluída` verde pill           | outline verde          |
| Atrasada   | vermelho              | `Atrasada` vermelho pill         | laranja sólido         |
| Vence hoje | amarelo               | `Vence hoje` amarelo pill        | laranja sólido         |
| Pendente   | cinza (`--border`)    | `Pendente` cinza pill            | laranja sólido         |

---

## O que não muda

- Lógica de `openAtividade()`, `concluirAtividade()`, `reabrirAtividade()`, `addOvRegistro()`
- Lógica de `saveOvDatas()` — os `<input type="date">` continuam existindo
- Tabs Checklist e Anotação — apenas herdam padding novo
- Menu `···` com opções de editar nome, alterar responsável, alterar prazo, excluir
- Backdrop e animação de slide (`transform: translateX`)
- Largura do painel: 420px fixo

---

## O que muda (resumo técnico)

1. **HTML estático** (`<div class="ov-panel">`) — reescrita completa da marcação interna preservando todos os `id="ov-*"` existentes
2. **CSS** — novos seletores para `.ov-stripe`, `.ov-slim-head`, `.ov-kpi-strip`, `.ov-kpi-cell`, `.ov-slim-footer`. CSS antigo de `.ov-hd`, `.ov-dates-row` removido ou substituído
3. **`openAtividade()`** — adiciona atualização da cor da stripe e da tag de status via `style.background` e `className`
4. **`renderOvRegistro()`** — ajusta HTML gerado para o novo layout do input row e feed

---

## O que está fora do escopo

- Mudança na largura do painel (mantém 420px)
- Redesign das abas Checklist e Anotação internamente
- Animação de entrada/saída (mantém cubic-bezier atual)
- Modo mobile / responsivo
