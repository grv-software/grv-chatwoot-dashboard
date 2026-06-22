# CSAT no Modal de Agente — Design Spec

## Objetivo

Adicionar uma aba "CSAT" no modal de perfil de agente do GRV SAC Dashboard, exibindo as avaliações individuais do agente com filtro por nota e link direto para o chat correspondente no Chatwoot.

## Contexto

O modal de agente já exibe: score geral, indicadores (melhor/pior mês, tendência), gráfico TMA/TMR/Volume por mês e tabela mensal de métricas. Os dados CSAT já são buscados com paginação completa em `fetchAgentTab()`, mas apenas o agregado (total + % positivas) é usado na aba de agentes. Este spec adiciona o detalhamento individual no modal sem chamadas extras à API.

Volume esperado: 70–150 respostas por agente por período.

---

## Arquitetura

### Novo estado global

```javascript
let _agentCsatByAgent = {};
// { [agentId]: [{rating, feedback_message, contact, conversation_id, created_at}, ...] }
```

Populado em `fetchAgentTab()` ao processar `csatList`, indexado por `r.assigned_agent.id`. Limpo junto com `_agentMonthCache` ao trocar período.

### Mudança em fetchAgentTab()

Após `csatList.forEach(r => { byAgent[...] })`, adicionar:

```javascript
_agentCsatByAgent = {};
csatList.forEach(r => {
  const id = r.assigned_agent?.id;
  if (!id) return;
  if (!_agentCsatByAgent[id]) _agentCsatByAgent[id] = [];
  _agentCsatByAgent[id].push(r);
});
```

### Link de conversa

Prioridade: `r.conversation_id` → `r.conversation?.id` → fallback `r.message_id` (abre mensagem, não conversa).

URL: `https://nxticket.com.br/app/accounts/${cfg.account}/conversations/${id}`

---

## Interface

### Abas no modal

Abaixo da linha nome/score, antes dos highlights, adicionar:

```html
<div class="am-tabs">
  <button class="am-tab active" data-tab="perf">Desempenho</button>
  <button class="am-tab" data-tab="csat">CSAT</button>
</div>
```

A aba ativa recebe classe `active` com sublinhado. Clicar alterna `display` entre `#am-perf-content` e `#am-csat-content`.

### Aba Desempenho

Wrapper `<div id="am-perf-content">` envolve o conteúdo atual (highlights + gráfico + tabela). Sem mudança visual.

### Aba CSAT

```html
<div id="am-csat-content" style="display:none">
  <!-- linha de resumo -->
  <div class="am-csat-header">
    <span>21 avaliações · 84% positivas</span>
    <div class="am-csat-filter">
      <button class="active" data-filter="all">Todas (21)</button>
      <button data-filter="bad">Ruins ≤3★ (3)</button>
    </div>
  </div>
  <!-- lista -->
  <div id="am-csat-list"></div>
  <!-- paginação -->
  <button id="am-csat-more" style="display:none">Ver mais 25</button>
</div>
```

### Linha de resposta

Cada item renderizado em `renderCsatModal()`:

```
[★★★★☆]  [nome do contato]  [comentário truncado 80 chars]  [data]  [Abrir chat →]
```

- Estrelas: `★`.repeat(rating) + `☆`.repeat(5 - rating), coloridas conforme nota:
  - rating 5 → `var(--green)`
  - rating 4 → `var(--yellow)`
  - rating ≤ 3 → `var(--red)`
- Linhas com `rating ≤ 3`: classe `csat-row-bad` com `background: rgba(239,68,68,0.06)`
- Comentário vazio: exibir `—`
- Data: `fmtDate(created_at)` (já existente)
- "Abrir chat →": `<a href="..." target="_blank">` — se não houver `conversation_id`, exibir link com `title="Link aproximado via message_id"`
- Sem comentário e sem feedback_message: linha ainda exibida (rating já é informação útil)

### Paginação client-side

Variável `_csatModalPage` (inteiro, reseta ao abrir modal ou trocar filtro). Exibe `_csatModalPage * 25` itens. Botão "Ver mais 25" aparece se há mais itens.

---

## Ordenação

Dois modos de ordenação controlados por `_csatModalSort`:

- `date-desc` (padrão): mais recente primeiro — `r.created_at` decrescente
- `rating-asc`: pior primeiro — `r.rating` crescente, empate por `r.created_at` decrescente

Botão toggle no header da aba CSAT, ao lado do filtro:

```html
<button id="am-csat-sort" title="Alternar ordenação">🕓 Data ↓</button>
<!-- ao clicar vira: -->
<button id="am-csat-sort" title="Alternar ordenação">★ Nota ↑</button>
```

Resetar para `date-desc` ao: (1) abrir o modal, (2) trocar filtro (all ↔ bad).

---

## Filtro

Dois estados: `all` (todas as respostas) e `bad` (rating ≤ 3). Filtro é client-side puro sobre `_agentCsatByAgent[id]`. Trocar filtro reseta `_csatModalPage = 1`, `_csatModalSort = 'date-desc'` e re-renderiza.

Contagens nos botões calculadas ao abrir a aba, ex: `Ruins ≤3★ (3)`.

---

## Estado vazio

- Agente sem respostas CSAT no período: "Nenhuma avaliação no período selecionado."
- Filtro "Ruins" sem itens: "Nenhuma avaliação negativa no período. 👍"
- CSAT não disponível (erro de fetch): não exibir a aba CSAT no modal.

---

## CSS (adições mínimas)

```css
.am-tabs { display:flex; gap:4px; margin: 8px 0 12px; border-bottom: 1px solid var(--border); }
.am-tab  { padding:6px 14px; font-size:13px; background:none; border:none; cursor:pointer;
           color:var(--text2); border-bottom:2px solid transparent; margin-bottom:-1px; }
.am-tab.active { color:var(--text1); border-bottom-color:var(--accent); font-weight:600; }

.am-csat-header  { display:flex; justify-content:space-between; align-items:center;
                   font-size:12px; color:var(--text2); margin-bottom:10px; }
.am-csat-filter  { display:flex; gap:6px; }
.am-csat-filter button { padding:3px 10px; border-radius:12px; font-size:11px;
                         border:1px solid var(--border); background:none; cursor:pointer; color:var(--text2); }
.am-csat-filter button.active { background:var(--accent); color:#fff; border-color:var(--accent); }

.am-csat-row     { display:flex; align-items:center; gap:10px; padding:7px 0;
                   border-bottom:1px solid var(--border); font-size:12px; }
.am-csat-row.csat-row-bad { background:rgba(239,68,68,0.06); border-radius:4px; padding:7px 6px; }
.am-csat-emoji   { font-size:16px; flex-shrink:0; }
.am-csat-contact { font-weight:600; min-width:120px; color:var(--text1); }
.am-csat-msg     { color:var(--text2); flex:1; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; }
.am-csat-date    { color:var(--text3); font-size:11px; flex-shrink:0; }
.am-csat-link    { color:var(--accent); flex-shrink:0; white-space:nowrap; }
```

---

## Escopo fora deste spec

- Paginação server-side de CSAT (para volumes >500 — não necessário agora)
- Exibição de CSAT na aba principal de agentes (já existe o agregado)
- Filtro por nota específica (1★, 2★, etc.) — "Ruins ≤3★" cobre o caso de uso
