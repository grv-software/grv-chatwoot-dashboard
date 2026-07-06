# Spec — Atribuição de Responsável em Playbooks/Atividades + Vencimentos Pessoal

**Data:** 2026-07-06  
**Escopo:** `grv-cs-jornada.html` — dois blocos independentes mas acoplados

---

## Contexto

Hoje a responsabilidade de uma atividade é derivada indiretamente: o cliente pertence a um consultor (`cliente.consultorId`), portanto todas as atividades do cliente são "desse consultor". Isso impede que playbooks e atividades sejam atribuídos a pessoas diferentes do dono do cliente.

O modelo desejado (similar ao Sense Data): responsabilidade vive na atividade e no playbook, não no cliente. Um playbook tem um dono (`pb.donoId`), cada atividade pode ter seu próprio responsável (`at.responsavelId`). Vencimentos filtra por essa cadeia.

---

## Modelo de dados

Os campos já existem no schema, mas não têm UI de atribuição no momento da criação/edição:

```
Cliente
  └── Playbook  →  pb.donoId: string (consultorId)
        └── Atividade  →  at.responsavelId: string (consultorId) | undefined
        └── Atividade  →  at.responsavelId: string | undefined
```

**Cadeia de herança (fallback):**
1. `at.responsavelId` — responsável explícito da atividade
2. `pb.donoId` — dono do playbook (quando atividade não tem responsável)
3. `cliente.consultorId` — dono do cliente (quando playbook também não tem dono)

Nunca deve ficar vazio: a cadeia sempre resolve para alguém.

**Migração em `migrateLS()`:** nenhuma migration necessária — os campos já existem e a cadeia de fallback garante compatibilidade com dados antigos.

---

## Bloco A — UI de atribuição no playbook e atividades

### A1. Dono do playbook (`pb.donoId`)

**Onde:** cabeçalho do card do playbook em `renderAbaAtividades`, logo abaixo do nome, acima das atividades.

**Visual:**
```
┌──────────────────────────────────────────┐
│ Onboarding Técnico          ··· [⏸]      │
│ Dono  [👤 Samuel Wallace ▼]              │  ← novo
│ ──────────────────────────────────────── │
│ ☐ Configurar ambiente   15/07  [👤 G ▼] │
│ ☐ Treinamento           22/07  [👤 S ▼] │
│ ☐ Validar integração    28/07  [👤 S ▼] │  ← herdado (tracejado)
└──────────────────────────────────────────┘
```

**Comportamento:**
- Chip `[👤 Nome ▼]` — clicar abre um `<select>` inline com todos os consultores
- Salva `pb.donoId` imediatamente ao mudar; re-renderiza a aba
- Padrão ao criar novo playbook: `pb.donoId = _meu_consultor_id` (perfil ativo) ou `cliente.consultorId` se perfil não configurado

**Função JS necessária:**
```javascript
function setDonoPlaybook(clienteId, pbId, consultorId) {
  var c = getCliente(clienteId);
  var pb = (c.ativPlaybooks||[]).find(function(p){ return p.id === pbId; });
  if (!pb) return;
  pb.donoId = consultorId;
  saveCliente(c);
  renderCliente(clienteId);
}
```

### A2. Responsável da atividade (`at.responsavelId`)

**Onde:** linha de cada atividade dentro do card do playbook, à direita da data limite.

**Visual — chip de responsável:**
- Responsável explícito: fundo sólido, borda normal, avatar colorido + nome curto + ▼
- Responsável herdado (do playbook ou cliente): borda tracejada, cor mais fraca, mesmo conteúdo
- Chip ausente quando playbook está cancelado (atividades read-only)

**Comportamento:**
- Clicar no chip abre um `<select>` popup com todos os consultores + opção "Herdar do playbook"
- Ao selecionar "Herdar do playbook", remove `at.responsavelId` (undefined)
- Salva imediatamente; chama `renderCliente(clienteId)` para re-renderizar a aba

**Função JS necessária:**
```javascript
function setResponsavelAtividade(clienteId, pbId, atId, consultorId) {
  var c = getCliente(clienteId);
  var pb = (c.ativPlaybooks||[]).find(function(p){ return p.id === pbId; });
  if (!pb) return;
  var at = (pb.atividades||[]).find(function(a){ return a.id === atId; });
  if (!at) return;
  if (consultorId === '') { delete at.responsavelId; }
  else { at.responsavelId = consultorId; }
  saveCliente(c);
  renderCliente(clienteId);
}
```

**Helper de resolução (usado em todo o sistema):**
```javascript
function resolverResponsavel(at, pb, cliente) {
  return at.responsavelId || pb.donoId || cliente.consultorId || '';
}
```

---

## Bloco B — Perfil ativo + Vencimentos pessoal

### B1. Perfil ativo (`_meu_consultor_id`)

**Storage:** `localStorage.getItem('grv_meu_consultor')` — persiste entre sessões.

**Onde configurar:** pequeno seletor no topo da tela **Minha Carteira**, substituindo ou complementando o selector de consultor atual.

```
Minha Carteira  |  Visualizando como: [Samuel Wallace ▼]
```

**Funções JS:**
```javascript
var _meu_consultor_id = localStorage.getItem('grv_meu_consultor') || '';

function setMeuConsultor(id) {
  _meu_consultor_id = id;
  localStorage.setItem('grv_meu_consultor', id);
  renderCarteira();
}
```

**Impacto em Minha Carteira:** filtra clientes pela cadeia — se perfil configurado, usa `_meu_consultor_id`; se não, comportamento atual.

### B2. Lógica de filtro em Vencimentos

**Função `resolverResponsavel` aplicada em `getTodasVencidas`:** cada item do resultado já carrega o responsável resolvido.

**Mudança no filtro de consultor em `renderVencimentos`:**

Antes:
```javascript
todos = todos.filter(function(v){ return v.cliente.consultorId === _venc_filter_cons; });
```

Depois:
```javascript
todos = todos.filter(function(v){
  var resp = resolverResponsavel(v.at, v.pb, v.cliente);
  return resp === _venc_filter_cons;
});
```

**Default ao abrir Vencimentos:** se `_meu_consultor_id` está configurado, `_venc_filter_cons` inicia com esse valor (não mais `'todos'`). O usuário ainda pode limpar o filtro para ver todos.

### B3. Exibição na linha de Vencimentos

A linha já mostra o responsável resolvido (`v.at.responsavelId || v.pb.donoId`). Com a nova lógica, adicionar um indicador quando o responsável vem de herança:

- Responsável explícito: nome normal
- Herdado do playbook: nome + `(playbook)`  
- Herdado do cliente: nome + `(cliente)`

Isso ajuda o gestor a entender a origem da atribuição sem abrir o cliente.

---

## Impacto em telas existentes

| Tela | Mudança |
|---|---|
| Aba Atividades (cliente) | + seletor de dono no card do playbook + chip de responsável por atividade |
| Minha Carteira | + seletor de perfil ativo no topo |
| Vencimentos | lógica de filtro usa `resolverResponsavel()` + default para perfil ativo |
| Export CSV | coluna "Responsável" usa `resolverResponsavel()` |
| `getTodasVencidas` | adiciona campo `resp` resolvido em cada item do resultado |

---

## Fora do escopo

- Notificações por email quando atividade é atribuída
- Histórico de mudanças de responsável
- Atribuição em massa (selecionar várias atividades e reatribuir)
- Permissões: qualquer usuário ainda pode ver tudo; perfil ativo só afeta o filtro padrão
