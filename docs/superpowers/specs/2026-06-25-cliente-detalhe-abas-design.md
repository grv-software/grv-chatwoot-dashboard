# GRV CS Jornada — Detalhe do Cliente: Abas 360° / Playbooks / Notas

**Data:** 2026-06-25
**Arquivo alvo:** `grv-cs-jornada.html`
**Tipo:** Redesign da tela de detalhe do cliente com sistema de abas + Playbooks aninhados

---

## Objetivo

Transformar a tela de detalhe do cliente de um layout fixo de duas colunas em uma interface com 3 abas especializadas: Visão 360° (perfil + progresso), Playbooks (registro de atividades e reuniões) e Notas (anotações gerais). Adicionar campos de Segmento e CS ao modelo de dados.

---

## Pré-condição verificada

Funções existentes que continuam inalteradas:
- `renderCliente(id)` — será reescrita
- `toggleFase(idx)`, `checkTask(clienteId, faseIdx, tarefaId)` — mantidas
- `addRegistro(clienteId)` — mantida, migra para aba Notas
- `SEED_CLIENTES`, `SEED_CONSULTORES` — recebem campos novos (`segmento`, `csNome`, `playbooks`)
- Hash routing `#cliente/ID` — inalterado

---

## Arquitetura

Single-file SPA (`grv-cs-jornada.html`) sem build step. Todas as mudanças são CSS + JS inline. O estado das abas é gerenciado por `_cliente_aba` (string global: `'360'|'playbooks'|'notas'`). O estado do playbook selecionado e da atividade ativa são `_pb_sel` (id do playbook) e `_at_sel` (id da atividade). Re-render via `renderCliente(id)` ao mudar aba ou selecionar atividade.

---

## Estrutura Visual

### Header do Cliente (fixo, acima das abas)

Mantém o layout atual — nome do cliente, código do projeto, produto, badges de etapa/status, botão "Alterar Etapa" e grid de meta-info (Consultor, Início, Prazo, Dias na etapa). Nenhuma mudança visual.

### Abas

```
[ Visão 360° ]  [ Playbooks ]  [ Notas ]
```

Aba ativa: sublinhado laranja `#E05A1E`, texto bold. Abas inativas: texto `var(--text3)`. Clique chama `setClienteAba(aba, clienteId)` — atualiza `_cliente_aba` e re-renderiza.

---

## Aba 1 — Visão 360°

### Grid de Campos Rápidos

4 cards em grid `1fr 1fr 1fr 1fr` abaixo das abas:

| Card | Valor | Fonte |
|---|---|---|
| Segmento | ex: "Saúde" | `c.segmento` (novo campo) |
| CS Responsável | ex: "Valentina Souza" | `c.csNome` (novo campo) |
| Consultor Digital | ex: "Severiano Rocha" | `SEED_CONSULTORES.find(consultorId).nome` |
| % Implantação | ex: "38%" + barra | `getProgresso(c)` (já existe) |

Estilo: card branco com sombra, label cinza uppercase 10px, valor bold 18px.

### Checklist de Fases

Idêntico ao layout atual (fases colapsáveis com tarefas checkbox). Título da seção: "Playbook de Implantação". Abaixo do título, link: `"Ver Playbooks →"` que chama `setClienteAba('playbooks', c.id)`.

### Histórico de Etapas

Idêntico ao layout atual (timeline com dots laranja). Movido da coluna direita para cá.

---

## Aba 2 — Playbooks

### Layout Master-Detail

Grid `260px 1fr`. Coluna esquerda: lista de playbooks e atividades. Coluna direita: painel de detalhes da atividade selecionada.

### Coluna Esquerda — Lista

**Cabeçalho:** botão "+ Novo Playbook" (laranja outline, largura total). Clique exibe inline form com input de nome + botões "Criar" / "Cancelar".

**Cada Playbook:**
```
📋 Implantação                    ▾
   ○ 1ª Reunião de engajamento
   ● 2ª Reunião de engajamento   ←(selecionada, highlighted)
   [ + Atividade ]
```

- Nome do playbook em bold, ícone de pasta, chevron para colapsar/expandir
- Atividade com registro(s): ● (círculo cheio cinza-escuro)
- Atividade sem registro: ○ (círculo vazio)
- Atividade selecionada: fundo laranja claro `#FFF3EE`, texto laranja, borda esquerda `#E05A1E`
- `[ + Atividade ]` exibe inline input ao clicar

**Criação de Playbook (inline):**
Input de nome + Enter ou botão "Criar". Gera id `pb_<timestamp>`. Adiciona a `c.playbooks`, re-renderiza.

**Criação de Atividade (inline):**
Input de nome abaixo das atividades existentes + Enter ou botão "Criar". Gera id `at_<timestamp>`. Adiciona à `playbooks[pbId].atividades`.

### Coluna Direita — Painel

**Estado vazio (nenhuma atividade selecionada):**
Ícone + texto "Selecione uma atividade para registrar."

**Estado com atividade selecionada:**
```
2ª Reunião de engajamento
─────────────────────────────────────────────────
Severiano Rocha · 15/02/2026 · 14:30
"Kickoff realizado com sucesso. Equipe bem engajada."

─────────────────────────────────────────────────
┌────────────────────────────────────────────────┐
│ Registrar reunião, decisão ou detalhe...       │
│                                                │
└────────────────────────────────────────────────┘
[ Salvar registro ]
```

- Nome da atividade em `font-size:18px;font-weight:700` no topo
- Registros em ordem cronológica reversa (mais recente no topo)
- Cada registro: linha com autor + data formatada, depois o texto
- Separador `<hr>` entre registros
- Textarea + botão "Salvar registro" fixos no final
- Salvar: prepende novo registro ao array `atividade.registros`, limpa textarea, re-renderiza

### Modelo de Dados — Playbooks

```javascript
// Novo campo em cada cliente:
playbooks: [
  {
    id: 'pb_1',
    nome: 'Implantação',
    criadoEm: '2026-01-20T09:00:00',
    atividades: [
      {
        id: 'at_1',
        nome: '1ª Reunião de engajamento',
        registros: [
          {
            id: 'reg_1',
            autor: 'Severiano Rocha',
            data: '2026-01-20T14:00:00',
            texto: 'Reunião de kickoff realizada. Cliente bem receptivo...'
          }
        ]
      },
      {
        id: 'at_2',
        nome: '2ª Reunião de engajamento',
        registros: []
      }
    ]
  }
]
```

Clientes no SEED receberão `playbooks: []` por padrão. 2–3 clientes receberão playbooks com dados de exemplo para demonstração.

---

## Aba 3 — Notas

Layout de coluna única. O array `c.registros` existente (notas gerais) migra integralmente para esta aba.

**Lista de notas:** autor em bold + data formatada na primeira linha, texto abaixo. Ordem cronológica reversa.

**Formulário:** textarea + botão "Salvar nota". Chama a função `addRegistro(clienteId)` existente sem alteração.

**Estado vazio:** mensagem "Nenhuma nota ainda." em cinza.

---

## Modelo de Dados — Campos Novos nos Clientes

```javascript
// Adicionado a cada objeto em SEED_CLIENTES:
segmento: 'Saúde',   // picklist: 'Saúde'|'Indústria'|'Varejo'|'Serviços'|'Agronegócio'|'Educação'
csNome:   'Valentina Souza',  // nome livre, referencia um dos CS da equipe GRV
playbooks: [],       // array conforme estrutura acima
```

Segmentos distribuídos realisticamente entre os 38 clientes. `csNome` usa nomes fictícios consistentes (ex: Valentina Souza, Hidalgo Ferreira, Ana Paula Souza — os próprios consultores acumulam o papel de CS nos dados de seed).

---

## Estado Global Novo

```javascript
let _cliente_aba = '360';   // aba ativa: '360' | 'playbooks' | 'notas'
let _pb_sel      = null;    // id do playbook expandido
let _at_sel      = null;    // id da atividade selecionada
let _pb_form_open = false;  // true quando form "+ Novo Playbook" está aberto
```

Funções novas de nível global (chamáveis via `onclick`):
- `setClienteAba(aba, clienteId)` — muda `_cliente_aba`, re-renderiza
- `selecionarAtividade(pbId, atId, clienteId)` — muda `_at_sel`, re-renderiza
- `togglePlaybook(pbId, clienteId)` — colapsa/expande playbook na lista
- `abrirFormPlaybook(clienteId)` / `criarPlaybook(clienteId)` — fluxo de criação
- `abrirFormAtividade(pbId, clienteId)` / `criarAtividade(pbId, clienteId)` — fluxo de criação
- `addRegistroAtividade(clienteId, pbId, atId)` — salva registro na atividade selecionada

---

## CSS Novo

```css
/* Abas */
.cliente-tabs { display:flex; gap:0; border-bottom:2px solid var(--border); margin-bottom:24px; }
.cliente-tab  { padding:10px 20px; font-size:13px; font-weight:600; color:var(--text3);
                cursor:pointer; border-bottom:2px solid transparent; margin-bottom:-2px; }
.cliente-tab.active { color:var(--primary); border-bottom-color:var(--primary); }
.cliente-tab:hover:not(.active) { color:var(--text); }

/* Grid 360° */
.grid-360 { display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:16px; margin-bottom:24px; }
.card-360  { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius);
             padding:16px 20px; }
.c360-label { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.07em;
              color:var(--text3); margin-bottom:8px; }
.c360-value { font-size:17px; font-weight:700; color:var(--text); }

/* Playbooks master-detail */
.pb-layout  { display:grid; grid-template-columns:260px 1fr; gap:0; min-height:400px;
              border:1px solid var(--border); border-radius:var(--radius); overflow:hidden; }
.pb-sidebar { border-right:1px solid var(--border); padding:16px 12px;
              background:var(--surface); overflow-y:auto; }
.pb-panel   { padding:24px; overflow-y:auto; }
.pb-item    { padding:8px 10px; border-radius:6px; cursor:pointer; display:flex;
              align-items:center; gap:8px; font-size:13px; margin-bottom:2px; }
.pb-item:hover { background:#f7fafc; }
.pb-item.active { background:#FFF3EE; color:var(--primary); border-left:3px solid var(--primary);
                  padding-left:7px; font-weight:600; }
.pb-item-dot { font-size:10px; flex-shrink:0; }
.pb-title   { font-size:13px; font-weight:700; color:var(--text); margin-bottom:8px;
              display:flex; align-items:center; gap:8px; cursor:pointer; }
.pb-add-btn { width:100%; padding:8px; border:1px dashed var(--border); border-radius:6px;
              background:none; color:var(--text3); font-size:12px; cursor:pointer;
              text-align:center; margin-bottom:12px; }
.pb-add-btn:hover { border-color:var(--primary); color:var(--primary); }

/* Painel de atividade */
.at-reg-item { padding:12px 0; border-bottom:1px solid var(--border); }
.at-reg-meta { font-size:11px; color:var(--text3); margin-bottom:4px; }
.at-reg-text { font-size:13px; color:var(--text); line-height:1.5; }
```

---

## O que NÃO muda

- Hash routing e navegação geral
- `renderProjetosGRV`, `renderCarteira`, `renderKanban`
- Lógica de `checkTask` e auto-advance de etapa
- Modal "Alterar Etapa"
- Telas Criar Playbook, Projetos GRV, Minha Carteira
- Todos os charts e dashboard de projetos

---

## Casos de Borda

| Cenário | Comportamento |
|---|---|
| Cliente sem playbooks | Aba Playbooks mostra só o botão "+ Novo Playbook" |
| Atividade sem registros | Painel direito mostra área de escrita sem lista acima |
| Cliente sem notas | Aba Notas mostra "Nenhuma nota ainda." |
| Playbook colapsado, atividade selecionada | Atividade permanece selecionada; colapsado só esconde a lista |
| `csNome` vazio | Campo exibe "—" (hífen) |
