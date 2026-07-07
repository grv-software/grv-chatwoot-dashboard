# Spec — Projetos GRV: Sub-páginas Portfólio / Implantação / Customer

**Data:** 2026-07-07  
**Escopo:** `grv-cs-jornada.html` — reestruturação da tela Projetos GRV

---

## Contexto

Hoje "Projetos GRV" é uma única tela com três visualizações (Dashboard, Lista, Kanban) que misturam clientes em implantação (`status: 'em_implantacao'`) e clientes em Customer Success (`status: 'cs_ativo'`). Esses dois universos têm responsáveis, métricas e workflows completamente diferentes e merecem visões separadas.

O campo `c.status` já distingue os dois tipos. A separação é real nos dados — só não estava exposta na navegação.

---

## Modelo de dados (sem alteração de schema)

```
c.status: 'em_implantacao' | 'cs_ativo'   ← distinção já existe
c.consultorId  → responsável na fase de Implantação (Consultor Digital)
c.csId         → responsável na fase de Customer Success (CS Responsável)
c.dataInicioImplantacao → início da implantação
c.dataInicioCS          → início do CS (null se ainda em implantação)
```

**Única mudança de dado necessária:** o formulário "Criar Playbook" não pede `csId`. Será adicionado um campo opcional "CS Responsável" no formulário de criação, para que novos clientes possam já sair com o campo preenchido.

---

## Navegação

### Dropdown no topnav

O item "Projetos GRV" no topnav ganha um chevron (▾) e abre um dropdown ao hover:

```
Projetos GRV  Implantação ▾
                ┌────────────────────────┐
                │ PROJETOS GRV           │
                │ ─────────────────────  │
                │   Portfólio            │
                │ ▌ Implantação      12  │  ← ativo: borda laranja esquerda
                │   Customer          8  │
                └────────────────────────┘
```

- O item ativo é indicado com borda esquerda laranja + fundo `--primary-light`
- O nome da sub-página ativa aparece como badge ao lado de "Projetos GRV" no topnav
- Badge de contagem (clientes daquele tipo) em cada item do dropdown
- Clicar num item fecha o dropdown e troca a sub-página

### Variáveis globais novas

```javascript
const PROJ_TAB_KEY = 'grv_cs_proj_tab';
let _proj_tab = localStorage.getItem(PROJ_TAB_KEY) || 'implantacao';
// 'portfolio' | 'implantacao' | 'customer'
```

As variáveis existentes `_proj_view`, `_proj_consultor`, `_proj_etapa`, `_proj_status` permanecem, mas passam a ser escopadas por tab (cada tab tem seu próprio estado de view/filtro).

---

## Sub-página: Portfólio

**Dados:** todos os clientes (`getClientes()` sem filtro de status)  
**Conteúdo:** o dashboard atual, sem alterações estruturais.

Única adição: o hero escuro (`vg-card`) passa a mostrar a divisão dos dois mundos na legenda:

```
N projetos ativos  ·  X em implantação  ·  Y em CS
```

Implementado adicionando dois itens na `.vg-legend` com as contagens por status.

---

## Sub-página: Implantação

**Dados:** `clientes.filter(c => c.status === 'em_implantacao')`  
**Responsável:** `c.consultorId` (Consultor Digital)

### KPIs (4 cards)

| Label | Cálculo |
|---|---|
| Em Implantação | `count` de clientes filtrados |
| No Prazo | clientes onde `getStatus(c) !== 'Atrasado'` |
| Progresso Médio | média de `calcProgresso(c.ativPlaybooks)` |
| Tempo Médio na Etapa | média de `getDiasNaEtapa(c)` |

### Views e filtros

Toggle **Lista ↔ Kanban** (igual ao atual, mas filtrado por `em_implantacao`).

Filtros: Consultor Digital (`consultorId`), Etapa, Status.

**Colunas da lista:**

| Coluna | Campo |
|---|---|
| Cliente | `c.id` + `c.projeto` |
| Consultor Digital | `c.consultorId` → nome |
| Etapa | `getEtapaBadge(c.etapa)` |
| Progresso | barra + `%` |
| Prazo | `fmtDate(c.prazo)`, vermelho se atrasado |
| Status | `getStatusBadge(getStatus(c))` |

Kanban: colunas pelas etapas `ETAPAS` (excluindo Pausado/Interrompido/Cancelado do layout principal).

---

## Sub-página: Customer

**Dados:** `clientes.filter(c => c.status === 'cs_ativo')`  
**Responsável:** `c.csId` (CS Responsável)

### KPIs (4 cards)

| Label | Cálculo |
|---|---|
| Em Customer | `count` de clientes filtrados |
| Health Médio | média de `calcHealthScore(c)` |
| CSAT Médio | média de `calcCsatAtual(c)` |
| Sem Contato +30d | clientes onde `getDiasUltimoContato(c) > 30` |

### View e filtros

Apenas **Lista** (sem Kanban — clientes em CS não têm etapa de implantação).

Lista ordenada por padrão por Health Score crescente (menor = maior risco no topo).

Filtro: CS Responsável (`csId`), ordenação.

**Colunas da lista:**

| Coluna | Campo |
|---|---|
| Cliente | `c.id` + segmento |
| CS Responsável | `c.csId` → nome |
| Health Score | pill colorida: verde ≥ 70, amarelo 40–69, vermelho < 40 |
| CSAT | `calcCsatAtual(c)` + ★, `—` se sem dados |
| Último Contato | `getDiasUltimoContato(c)` dias, vermelho se > 30 |
| Próxima Ação | `c.proximaAcao` ou `—` |

---

## Mudança no formulário "Criar Playbook"

Adicionar campo opcional **CS Responsável** no formulário de criação de cliente:

```html
<select id="f-cs" name="csId">
  <option value="">— Definir depois —</option>
  <!-- consultores -->
</select>
```

O campo é salvo como `c.csId` no objeto do cliente. É opcional — pode ser preenchido depois pela aba 360 do cliente (que já exibe o campo mas não permite edição; essa edição também será liberada).

---

## Funções JS afetadas

| Função | Mudança |
|---|---|
| `renderProjetosGRV()` | Lê `_proj_tab`, despacha para `renderPortfolio()`, `renderImplantacao()`, ou `renderCustomer()` |
| `renderDashboardProjetos()` | Renomeada internamente para `renderPortfolio()`, sem mudança funcional |
| `renderImplantacao()` | Nova: KPIs + filtro + lista/kanban filtrados por `em_implantacao` |
| `renderCustomer()` | Nova: KPIs + filtro + lista filtrada por `cs_ativo`, ordenada por health |
| `setProjetosTab(tab)` | Nova: persiste `_proj_tab`, re-renderiza |
| `salvarPlaybook()` | Lê o novo campo `f-cs` e salva em `c.csId` |
| HTML do topnav | Item "Projetos GRV" vira grupo com dropdown hover |

---

## Fora do escopo

- Histórico de mudança de CS Responsável
- Transição automática de Implantação → Customer (o botão "Confirmar CS Ativo" já existe)
- Notificações por troca de responsável
- Kanban na aba Customer (clientes em CS não têm etapa de implantação)
- Permissões por tipo de usuário (qualquer um vê tudo)
