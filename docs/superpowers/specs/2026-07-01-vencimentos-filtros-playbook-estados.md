# Spec — Vencimentos: Filtros Avançados + Navegação + Estados de Playbook

**Data:** 2026-07-01
**Escopo:** `grv-cs-jornada.html` — dois blocos independentes sobre a tela Vencimentos e o modelo de estado de playbooks

---

## Contexto

A tela Vencimentos hoje tem apenas um filtro (por consultor) e as linhas não navegam para o cliente. Playbooks não têm estado — apenas o booleano `encerrado` para implantações concluídas. Esta spec adiciona filtros completos à tela Vencimentos e introduz um ciclo de vida de playbook (ativo → pausado / cancelado → reativo).

---

## Bloco A — Vencimentos: Filtros Avançados + Navegação

### Estado dos filtros

Variáveis globais de estado do filtro (junto de `_venc_filter_cons`):

```javascript
let _venc_filter_cons    = 'todos';   // já existe
let _venc_filter_urgency = 'todos';   // 'todos' | 'critico' | 'atrasado' | 'hoje'
let _venc_filter_etapa   = 'todos';   // 'todos' | 'em_implantacao' | 'cs_ativo'
let _venc_filter_produto = 'todos';   // 'todos' | qualquer valor de c.produto
let _venc_filter_busca   = '';        // string livre
```

### Filterbar

Cinco controles em linha (`display:flex; flex-wrap:wrap; gap:12px`):

1. **Input busca** — `placeholder="Buscar cliente..."`, `oninput` atualiza `_venc_filter_busca` e chama `renderVencimentos()`. Filtra por `v.cliente.id` (nome do cliente) case-insensitive.
2. **Select consultor** — já existe, mantido.
3. **Select urgência** — opções: Todas urgências / Crítico (>15d) / Atrasado (1–15d) / Vence hoje.
4. **Select etapa** — opções: Todas etapas / Implantação / CS Ativo.
5. **Select produto** — opções geradas dinamicamente dos valores únicos de `c.produto` entre todos os clientes com vencimento. Inclui "Todos os produtos" como padrão.
6. **Botão Exportar CSV** — `margin-left:auto`, já existe.

### Lógica de filtragem

`renderVencimentos()` aplica os cinco filtros sobre `getTodasVencidas()` em sequência:

```javascript
let todos = getTodasVencidas();

if (_venc_filter_cons !== 'todos')
  todos = todos.filter(v => (v.at.responsavelId || v.pb.donoId) === _venc_filter_cons);

if (_venc_filter_urgency !== 'todos') {
  if (_venc_filter_urgency === 'critico')  todos = todos.filter(v => v.diff < -15);
  if (_venc_filter_urgency === 'atrasado') todos = todos.filter(v => v.diff < 0 && v.diff >= -15);
  if (_venc_filter_urgency === 'hoje')     todos = todos.filter(v => v.diff === 0);
}

if (_venc_filter_etapa !== 'todos')
  todos = todos.filter(v => v.cliente.status === _venc_filter_etapa);

if (_venc_filter_produto !== 'todos')
  todos = todos.filter(v => (v.cliente.produto || '') === _venc_filter_produto);

if (_venc_filter_busca.trim())
  todos = todos.filter(v => v.cliente.id.toLowerCase().includes(_venc_filter_busca.trim().toLowerCase()));
```

### Navegação para o cliente

Em `mkRow`, o nome do cliente vira um link:

```html
<a href="#cliente/ID" style="color:var(--primary);font-weight:600;text-decoration:none">
  NOME_CLIENTE
</a>
```

O link usa `href` hash routing existente — clicar navega para `#cliente/ID` sem quebrar o botão Concluir ou o menu `···` adjacentes.

### Badge "Pausado" na linha

Quando `v.pb.status === 'pausado'`, a `.venc-meta` exibe após o nome do playbook:

```html
<span style="background:#FFF3EE;color:var(--primary);font-size:10px;font-weight:700;padding:1px 6px;border-radius:4px;margin-left:4px">⏸ Pausado</span>
```

---

## Bloco B — Estados de Playbook

### Modelo de dados

Campo novo em cada playbook: `pb.status: 'ativo' | 'pausado' | 'cancelado'` (ausente = `'ativo'`).

Migração automática no carregamento: em `migrateCliente(c)` (já existe), para cada playbook sem `status`, setar `pb.status = 'ativo'`.

### Ciclo de vida

```
ativo ──→ pausado ──→ ativo        (reativar)
ativo ──→ cancelado ──→ ativo      (reativar)
pausado ──→ cancelado ──→ ativo    (reativar)
```

Não há transição direta cancelado → pausado; reativar sempre volta para `'ativo'`.

### UI — menu ··· no card do playbook

O card de playbook selecionado (`isSel === true`) em `renderAbaAtividades` substitui os botões ✎ e × atuais por um botão `···` que abre um dropdown posicionado absolutamente:

```
··· → dropdown (min-width: 180px):
  ✎  Renomear
  ⏸  Pausar          → visível se pb.status === 'ativo'
  ▶  Reativar        → visível se pb.status === 'pausado' || 'cancelado'
  ✕  Cancelar        → visível se pb.status === 'ativo' || 'pausado'
  ─── divider ───
  🗑  Excluir         → sempre visível (abre confirm dialog existente)
```

O dropdown usa as classes `.ov-dropdown` e `.ov-dropdown-item` já definidas no CSS, com `position:absolute; top:calc(100% + 2px); right:0; z-index:400`.

Funções JS necessárias:

- `togglePbMenu(evt, pbId, clienteId)` — abre/fecha dropdown, fecha qualquer outro aberto
- `pausarPlaybook(pbId, clienteId)` — seta `pb.status = 'pausado'`, salva, renderiza
- `reativarPlaybook(pbId, clienteId)` — seta `pb.status = 'ativo'`, salva, renderiza
- `cancelarPlaybook(pbId, clienteId)` — `showConfirm(...)` → seta `pb.status = 'cancelado'`, salva, renderiza

### Visual do card por estado

| Estado | Card | Borda | Opacidade | Botão + Atividade |
|---|---|---|---|---|
| `ativo` | normal | `var(--border)` | 1 | visível |
| `pausado` | badge "⏸ Pausado" (laranja) | `2px dashed var(--primary)` | 1 | visível |
| `cancelado` | badge "✕ Cancelado" (cinza) | `var(--border)` | 0.6 | oculto |

Badge inline no nome do playbook:
```html
<!-- pausado -->
<span style="font-size:10px;font-weight:700;color:var(--primary);background:#FFF3EE;padding:1px 5px;border-radius:4px;margin-left:4px">⏸</span>

<!-- cancelado -->
<span style="font-size:10px;font-weight:700;color:var(--text3);background:var(--border-2);padding:1px 5px;border-radius:4px;margin-left:4px">✕</span>
```

### Efeitos em outras telas

**Vencimentos (`getTodasVencidas`):** excluir atividades de playbooks com `pb.status === 'cancelado'`. Atividades de playbooks `'pausado'` permanecem — identificadas pelo badge na linha (Bloco A).

**Progresso (`calcProgresso`):** não muda — pausado/cancelado ainda conta para o % (o progresso reflete o que foi feito, não o que resta).

**Criação de atividade:** quando `pb.status === 'cancelado'`, o botão "+ Atividade" fica oculto e a lista de atividades é read-only (sem checkboxes clicáveis, sem abertura de overlay).

---

## Fora do escopo

- Motivo/anotação ao pausar ou cancelar
- Histórico de mudanças de estado do playbook
- Notificações para o consultor dono quando o playbook é pausado por outro
