# GRV CS Jornada — Detalhe do Cliente: Abas 360° / Atividades / Notas

**Data:** 2026-06-25
**Arquivo alvo:** `grv-cs-jornada.html`
**Tipo:** Redesign da tela de detalhe do cliente com sistema de abas + Atividades aninhadas

---

## Objetivo

Transformar a tela de detalhe do cliente de um layout fixo de duas colunas em uma interface com 3 abas especializadas: Visão 360° (perfil + progresso), Atividades (registro de reuniões por playbook) e Notas (anotações gerais). Adicionar campos de Segmento e CS ao modelo de dados.

---

## Glossário de "Playbook" no sistema — DISTINÇÃO OBRIGATÓRIA

Existem três conceitos distintos que usam o nome "Playbook". O implementador deve conhecer os três:

| Conceito | Nome no código | O que é |
|---|---|---|
| Menu lateral "Criar Playbook" | `renderCriarPlaybook()` | Tela para criar templates de fases/tarefas e atribuir a clientes. **Não muda.** |
| Checklist de implantação | `c.fases[]` | As fases/tarefas que aparecem no detalhe do cliente. Exibidas na Visão 360°. **Não muda.** |
| Container de atividades | `c.ativPlaybooks[]` | **NOVO.** Agrupa atividades de reunião por tema (Implantação, Visita, etc.). Aparece na aba "Atividades". |

Para evitar colisão, o novo array no cliente se chama **`ativPlaybooks`** (não `playbooks`).

---

## Pré-condição verificada

Funções existentes que continuam inalteradas:
- `toggleFase(idx)`, `checkTask(clienteId, faseIdx, tarefaId)` — mantidas
- `addRegistro(clienteId)` — mantida, migra para aba Notas
- `SEED_CONSULTORES` — usado para resolver `csId` → nome na Visão 360°
- Hash routing `#cliente/ID` — inalterado
- `renderCriarPlaybook()` e menu lateral "Criar Playbook" — **não tocados**

Função a ser reescrita:
- `renderCliente(id)` — reescrita completa para suportar abas

---

## Arquitetura

Single-file SPA (`grv-cs-jornada.html`) sem build step. Todas as mudanças são CSS + JS inline.

**Estado global novo** (resetado toda vez que `renderCliente(id)` é chamado com um `id` diferente do cliente atual, garantindo estado limpo ao navegar entre clientes):

```javascript
let _cliente_id_atual = null;  // detecta troca de cliente
let _cliente_aba      = '360'; // '360' | 'atividades' | 'notas'
let _pb_expandidos    = {};    // { [pbId]: true } — quais ativPlaybooks estão abertos
let _at_sel           = null;  // id da atividade selecionada no painel direito
let _pb_form_open     = false; // true quando form "+ Novo Atividade-Playbook" está aberto
let _at_form_pb       = null;  // id do ativPlaybook com form de nova atividade aberto
```

**Reset ao navegar:** No início de `renderCliente(id)`, se `id !== _cliente_id_atual`, resetar todos os 5 estados acima e atribuir `_cliente_id_atual = id`.

Re-render via `renderCliente(id)` ao mudar aba, selecionar atividade ou criar itens.

---

## Estrutura Visual

### Header do Cliente (fixo, acima das abas)

Mantém o layout atual — nome do cliente, código do projeto, produto, badges de etapa/status, botão "Alterar Etapa" e grid de meta-info (Consultor, Início, Prazo, Dias na etapa). Nenhuma mudança visual.

### Abas

```
[ Visão 360° ]  [ Atividades ]  [ Notas ]
```

Aba ativa: sublinhado laranja `#E05A1E`, texto bold. Abas inativas: texto `var(--text3)`. Clique chama `setClienteAba(aba, clienteId)` — atualiza `_cliente_aba` e re-renderiza.

---

## Aba 1 — Visão 360°

### Grid de Campos Rápidos

4 cards em grid `1fr 1fr 1fr 1fr` abaixo das abas:

| Card | Valor | Fonte |
|---|---|---|
| Segmento | ex: "Saúde" | `c.segmento` (novo campo) |
| CS Responsável | ex: "Valentina Souza" | `SEED_CONSULTORES.find(x => x.id === c.csId)?.nome` |
| Consultor Digital | ex: "Severiano Rocha" | `SEED_CONSULTORES.find(x => x.id === c.consultorId)?.nome` |
| % Implantação | ex: "38%" + barra | `getProgresso(c)` (já existe) |

Estilo: card branco com sombra, label cinza uppercase 10px, valor bold 18px. Campo vazio exibe "—".

### Checklist de Fases

Idêntico ao layout atual (fases colapsáveis com tarefas checkbox). Título da seção: "Playbook de Implantação". Abaixo do título, link: `"Ver Atividades →"` que chama `setClienteAba('atividades', c.id)`.

### Histórico de Etapas

Idêntico ao layout atual (timeline com dots laranja). Movido da coluna direita para cá, abaixo do checklist.

---

## Aba 2 — Atividades

### Layout Master-Detail

Grid `260px 1fr`. Coluna esquerda: lista de ativPlaybooks e atividades. Coluna direita: painel de detalhes da atividade selecionada.

### Coluna Esquerda — Lista

**Cabeçalho:** botão "+ Novo" (laranja outline, largura total). Clique: `_pb_form_open = true`, re-renderiza. Form inline exibe input de nome + botões "Criar" / "Cancelar".

**Cada ativPlaybook:**
```
📋 Implantação                    ▾
   ○ 1ª Reunião de engajamento
   ● 2ª Reunião de engajamento   ← selecionada
   [ + Atividade ]
```

- Nome em bold, ícone 📋, chevron ▾/▸ para colapsar/expandir via `toggleAtivPlaybook(pbId, clienteId)`
- Estado expandido/colapsado: `_pb_expandidos[pbId]` — inicializa como `true` (expandido) ao criar
- Atividade com ≥1 registro: ● (U+25CF)
- Atividade sem registro: ○ (U+25CB)
- Atividade selecionada (`_at_sel === at.id`): fundo `#FFF3EE`, cor `var(--primary)`, borda esquerda `3px solid #E05A1E`, font-weight 600
- `[ + Atividade ]` aparece ao final das atividades do playbook. Clique: `_at_form_pb = pbId`, re-renderiza. Form inline: input de nome + "Criar" / "Cancelar"

**Criação de ativPlaybook:**
- Input Enter ou clique "Criar" → gera `id: 'pb_' + Date.now()`, `criadoEm: new Date().toISOString()`, `atividades: []`
- Adiciona a `c.ativPlaybooks`, `_pb_form_open = false`, `_pb_expandidos[novoId] = true`, re-renderiza

**Criação de atividade:**
- Input Enter ou clique "Criar" → gera `id: 'at_' + Date.now()`, `registros: []`
- Adiciona a `ativPlaybooks[pbId].atividades`, `_at_form_pb = null`, `_at_sel = novoId`, re-renderiza

### Coluna Direita — Painel

**Estado vazio (`_at_sel === null`):**
```
        📝
  Selecione uma atividade
  para registrar reunião,
  decisão ou detalhe.
```
Centralizado vertical e horizontalmente, texto `var(--text3)`.

**Estado com atividade selecionada:**
```
2ª Reunião de engajamento
──────────────────────────────────────────────────
Severiano Rocha · 15/02/2026 · 14:30
"Kickoff realizado com sucesso. Equipe bem engajada."
──────────────────────────────────────────────────
┌──────────────────────────────────────────────┐
│ Registrar reunião, decisão ou detalhe...     │
│                                              │
└──────────────────────────────────────────────┘
[ Salvar registro ]
```

- Nome da atividade: `font-size:18px; font-weight:700` no topo
- Registros em ordem cronológica reversa (mais recente primeiro)
- Cada registro: `.at-reg-meta` (autor · data hora) + `.at-reg-text` (texto)
- Separador `border-bottom: 1px solid var(--border)` entre registros
- Textarea (`id="at-reg-input"`) + botão "Salvar registro" ao final
- Salvar chama `addRegistroAtividade(clienteId, pbId, atId)`: lê textarea, valida não vazio, prepende `{id: 'reg_'+Date.now(), autor: consultorNome, data: ISO, texto}` ao array `atividade.registros`, limpa textarea, re-renderiza
- `consultorNome`: nome do consultor ativo no contexto (usar `_consultor_ativo` se existir, senão o `c.consultorId` resolvido via SEED_CONSULTORES)

### Modelo de Dados — ativPlaybooks

```javascript
// Novo campo em cada objeto de SEED_CLIENTES:
ativPlaybooks: [
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
            texto: 'Reunião de kickoff realizada. Cliente bem receptivo. Alinhado cronograma das próximas etapas.'
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

Todos os 38 clientes recebem `ativPlaybooks: []` por padrão. **3 clientes** (ex: ROBOTIX, KMSIL, e um terceiro) recebem `ativPlaybooks` com dados de exemplo realistas para demonstração imediata.

---

## Aba 3 — Notas

Layout de coluna única, largura total. O array `c.registros` existente (notas gerais) migra para esta aba sem alteração no modelo.

**Lista de notas:** `.at-reg-meta` (autor · data hora) + `.at-reg-text` (texto). Ordem cronológica reversa.

**Formulário:** `<textarea id="reg-input-${c.id}">` + botão "Salvar nota". Chama `addRegistro(clienteId)` — função existente, sem alteração.

**Estado vazio:** `<div style="color:var(--text3);font-size:13px;padding:16px 0">Nenhuma nota ainda.</div>`

---

## Modelo de Dados — Campos Novos nos Clientes

```javascript
// Adicionado a cada objeto em SEED_CLIENTES:
segmento:     'Saúde',        // picklist: 'Saúde'|'Indústria'|'Varejo'|'Serviços'|'Agronegócio'|'Educação'
csId:         'ana-paula',    // referencia SEED_CONSULTORES[].id — mesmo padrão do consultorId existente
ativPlaybooks: [],            // array conforme estrutura acima
```

- `csId` usa os mesmos ids de `SEED_CONSULTORES` (ex: `'ana-paula'`, `'severiano'`). Um consultor pode ser CS de clientes que não atende diretamente.
- Segmentos distribuídos realisticamente: Saúde ~30%, Indústria ~25%, Varejo ~20%, Serviços ~15%, outros ~10%.
- `csId` distribuído entre os 7 consultores como se fossem CS de contas diferentes.

---

## Funções Novas (globais, chamáveis via onclick)

| Função | Descrição |
|---|---|
| `setClienteAba(aba, clienteId)` | Atualiza `_cliente_aba`, re-renderiza |
| `toggleAtivPlaybook(pbId, clienteId)` | Alterna `_pb_expandidos[pbId]`, re-renderiza |
| `selecionarAtividade(pbId, atId, clienteId)` | Atualiza `_pb_expandidos[pbId]=true`, `_at_sel=atId`, re-renderiza |
| `abrirFormPlaybook(clienteId)` | `_pb_form_open=true`, re-renderiza |
| `cancelarFormPlaybook(clienteId)` | `_pb_form_open=false`, re-renderiza |
| `criarAtivPlaybook(clienteId)` | Lê input, cria objeto, push em `c.ativPlaybooks`, reset form, re-renderiza |
| `abrirFormAtividade(pbId, clienteId)` | `_at_form_pb=pbId`, re-renderiza |
| `cancelarFormAtividade(clienteId)` | `_at_form_pb=null`, re-renderiza |
| `criarAtividade(pbId, clienteId)` | Lê input, cria objeto, push em `ativPlaybook.atividades`, seleciona nova, re-renderiza |
| `addRegistroAtividade(clienteId, pbId, atId)` | Lê textarea, prepend registro, re-renderiza |

---

## CSS Novo

```css
/* Abas do cliente */
.cliente-tabs{display:flex;gap:0;border-bottom:2px solid var(--border);margin-bottom:24px}
.cliente-tab{padding:10px 20px;font-size:13px;font-weight:600;color:var(--text3);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-2px;background:none;border-top:none;border-left:none;border-right:none}
.cliente-tab.active{color:var(--primary);border-bottom-color:var(--primary)}
.cliente-tab:hover:not(.active){color:var(--text)}

/* Grid 360° */
.grid-360{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.card-360{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px 20px}
.c360-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text3);margin-bottom:8px}
.c360-value{font-size:17px;font-weight:700;color:var(--text);line-height:1.3}
.c360-prog{height:6px;background:#edf2f7;border-radius:3px;margin-top:8px}
.c360-prog-fill{height:100%;border-radius:3px;background:var(--primary)}

/* Atividades master-detail */
.pb-layout{display:grid;grid-template-columns:260px 1fr;gap:0;min-height:440px;border:1px solid var(--border);border-radius:var(--radius);overflow:hidden}
.pb-sidebar{border-right:1px solid var(--border);padding:14px 10px;background:#fafbfc;overflow-y:auto}
.pb-panel{padding:24px;overflow-y:auto;background:#fff}
.pb-title-row{display:flex;align-items:center;gap:6px;padding:6px 8px;cursor:pointer;border-radius:6px;font-size:13px;font-weight:700;color:var(--text);margin-bottom:4px}
.pb-title-row:hover{background:#f0f4f8}
.pb-chev{font-size:10px;margin-left:auto;color:var(--text3)}
.pb-item{padding:6px 10px 6px 24px;border-radius:6px;cursor:pointer;display:flex;align-items:center;gap:7px;font-size:12px;color:var(--text2);margin-bottom:2px}
.pb-item:hover{background:#f0f4f8}
.pb-item.active{background:#FFF3EE;color:var(--primary);border-left:3px solid var(--primary);padding-left:21px;font-weight:600}
.pb-add-btn{width:100%;padding:7px;border:1px dashed var(--border);border-radius:6px;background:none;color:var(--text3);font-size:12px;cursor:pointer;text-align:center;margin:6px 0 14px}
.pb-add-btn:hover{border-color:var(--primary);color:var(--primary)}
.pb-inline-form{padding:4px 8px 8px;display:flex;gap:6px}
.pb-inline-input{flex:1;padding:5px 8px;border:1px solid var(--border);border-radius:6px;font-size:12px}

/* Painel de atividade */
.at-empty{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:var(--text3);text-align:center;gap:8px;font-size:13px}
.at-title{font-size:18px;font-weight:700;color:var(--text);margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid var(--border)}
.at-reg-item{padding:12px 0;border-bottom:1px solid var(--border)}
.at-reg-item:last-of-type{border-bottom:none}
.at-reg-meta{font-size:11px;color:var(--text3);margin-bottom:4px}
.at-reg-text{font-size:13px;color:var(--text);line-height:1.6}
.at-write{margin-top:20px;padding-top:16px;border-top:1px solid var(--border)}
```

---

## Reset de Estado ao Navegar

No início de `renderCliente(id)`:
```javascript
if (id !== _cliente_id_atual) {
  _cliente_id_atual = id;
  _cliente_aba      = '360';
  _pb_expandidos    = {};
  _at_sel           = null;
  _pb_form_open     = false;
  _at_form_pb       = null;
}
```

Garante que ao abrir um novo cliente, o usuário começa sempre na Visão 360° com estado limpo.

---

## O que NÃO muda

- Hash routing e navegação geral
- `renderProjetosGRV`, `renderCarteira`, `renderKanban`
- Lógica de `checkTask` e auto-advance de etapa
- Modal "Alterar Etapa"
- Tela "Criar Playbook" (menu lateral) e `renderCriarPlaybook()`
- Todos os charts e dashboard de projetos

---

## Casos de Borda

| Cenário | Comportamento |
|---|---|
| Cliente sem `ativPlaybooks` | Aba Atividades mostra só o botão "+ Novo" |
| Atividade sem registros | Painel direito mostra só a área de escrita, sem lista acima |
| Cliente sem `registros` | Aba Notas mostra "Nenhuma nota ainda." |
| ativPlaybook colapsado, atividade selecionada | Atividade permanece `_at_sel`; colapsado só oculta os itens da lista |
| `csId` não encontrado em SEED_CONSULTORES | Campo exibe "—" |
| Criação com input vazio | Não cria — validar `nome.trim() !== ''` antes de adicionar |
| Navegar para outro cliente e voltar | Estado completamente resetado (aba volta a 360°) |
