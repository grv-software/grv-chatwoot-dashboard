# GRV CS — Módulo Jornada do Cliente

**Data:** 2026-06-22  
**Arquivo alvo:** `grv-cs-jornada.html`  
**Tipo:** Protótipo funcional standalone (HTML/CSS/JS puro, sem build step)

---

## Objetivo

Módulo de acompanhamento de clientes para consultores CS/Implantação da GRV Software. Permite ao consultor gerenciar sua carteira de clientes, acompanhar o progresso de cada playbook, registrar anotações e mover clientes entre etapas da jornada. Protótipo local para futura integração ao SAG (sag.grv.com.br).

---

## Arquitetura

**Abordagem:** Single-file SPA com hash routing.

**Roteamento:**
```
#carteira        → Tela 1: Minha Carteira
#jornada         → Tela 2: Jornada (pipeline por etapa)
#cliente/:id     → Tela 3: Detalhe do Cliente
#criar           → Tela 4: Criar Playbook
```

**Layout:** Sidebar fixa (240px, `#1A1A2E`) + área de conteúdo (`#F4F5F7`). Sidebar contém logo GRV, seletor de consultor ativo e navegação das 4 telas.

**Persistência:** `localStorage` — dados fictícios pré-carregados na primeira visita (quando localStorage vazio). Toda mutação persiste imediatamente.

---

## Identidade Visual (SAG)

| Token | Valor |
|---|---|
| Cor primária | `#E05A1E` (laranja GRV) |
| Sidebar | `#1A1A2E` |
| Background | `#F4F5F7` |
| Fonte | Segoe UI / system-ui |
| Border-radius botões | 7px |
| Badges | Fundo suave + texto colorido, sem bordas |
| Tabelas | Fundo branco, header `#FAFBFC`, hover sutil |
| Logo sidebar | Quadrado laranja com "G" + "GRV Software" em branco |
| Itens ativos sidebar | Laranja — nunca azul |

---

## Modelo de Dados (localStorage)

### `grv_cs_consultores`
```json
[
  { "id": "ana-paula", "nome": "Ana Paula Souza" },
  { "id": "carlos",    "nome": "Carlos Menezes" },
  { "id": "maria",     "nome": "Maria Lima" }
]
```

### `grv_cs_clientes`
```json
{
  "id": "KMSIL",
  "projeto": "SAGP-00036",
  "produto": "CPS",
  "consultorId": "ana-paula",
  "etapa": "Engajamento",
  "dataInicio": "2026-03-05",
  "prazo": "2026-09-30",
  "proximaAcao": "Acompanhar uso do módulo Compras",
  "fases": [
    {
      "nome": "1ª Reunião & Kickoff",
      "tarefas": [
        { "id": "t1", "texto": "Apresentar cronograma do projeto", "feita": true }
      ]
    }
  ],
  "registros": [
    { "id": "r1", "autor": "Ana Paula Souza", "data": "2026-03-10T10:00:00", "texto": "Kickoff realizado com sucesso." }
  ],
  "historicoEtapas": [
    { "de": null, "para": "1ª Reunião", "data": "2026-03-05T09:00:00", "motivo": "Início do projeto" }
  ]
}
```

**Regras de negócio:**
- `progresso` é calculado dinamicamente: `tarefas.feita.length / tarefas.total * 100` — nunca armazenado
- `status` é derivado na leitura via `getStatus(cliente)`:
  - Se `etapa` ∈ {Pausado, Interrompido, Cancelado} → retorna a própria etapa como status
  - Se `prazo` existe, hoje > prazo e progresso < 100% → "Atrasado"
  - Caso contrário → "Em ordem"
- `historicoEtapas` é append-only, nunca editável

---

## Dados Fictícios (seed)

| Cliente | Projeto | Produto | Consultor | Etapa | Prazo |
|---|---|---|---|---|---|
| KMSIL | SAGP-00036 | CPS | Ana Paula | Engajamento | 2026-09-30 |
| RAS METAL | SAGP-00091 | CPS | Ana Paula | Evolução | 2026-05-31 (**atrasado**) |
| AXONE | SAGP-00059 | CPS | Ana Paula | Engajamento | 2026-08-02 |
| AÇO ART | SAGP-00068 | CPS | Ana Paula | Pausado | — |
| ALPARGATAS CPS | SAGP-00128 | CPS/IOT | Ana Paula | Conclusão | 2026-11-06 |
| FRAY | SAGP-00039 | CPS | Carlos | 1ª Reunião | 2026-09-21 |
| FELIX INDUSTRIAL | SAGP-00092 | CPS | Carlos | 1ª Reunião | 2026-09-29 |
| USIMAZA EMBRAER | SAGP-00058 | CPS | Carlos | 1ª Reunião | 2026-09-17 |
| CAMPOSC | SAGP-00038 | CPS | Carlos | Pausado | — |
| SOARES FERRAMENTARIA | SAGP-00131 | CPS | Maria | 1ª Reunião | 2026-09-09 |
| LIQUOS | SAGP-00093 | CPS | Maria | Evolução | 2026-09-09 |

---

## Telas

### Tela 1 — Minha Carteira (`#carteira`)

- 4 cards de métricas no topo: Total, Em ordem, Atrasados, Pausados (calculados em tempo real sobre a carteira do consultor ativo)
- Filtro por abas: Todos / Em ordem / Atrasado / Pausado
- Busca por nome de cliente
- Tabela: Nome + Projeto (ID em laranja) | Etapa (badge) | Status (badge derivado) | Progresso (barra inline) | Próxima Ação | Prazo
- Clicar na linha → navega para `#cliente/:id`

### Tela 2 — Jornada (`#jornada`)

- Grid de 7 cards (um por etapa): 🤝 1ª Reunião · ⚡ Engajamento · 📈 Evolução · 🏁 Conclusão · ⏸️ Pausado · 🚫 Interrompido · ❌ Cancelado
- Cada card mostra contagem de clientes **de todos os consultores**
- Clicar no card expande tabela: nome, projeto, consultor, status, progresso, dias na etapa
- "Dias na etapa" = diferença entre hoje e a data da última entrada em `historicoEtapas`

### Tela 3 — Detalhe do Cliente (`#cliente/:id`)

**Header:** nome, projeto (laranja), consultor, etapa (badge), data início, prazo, status badge, dias na etapa, botão "Alterar Etapa"

**Coluna esquerda (65%) — Playbook:**
- Barra de progresso geral
- 4 fases expansíveis com checkboxes
- Marcar checkbox → recalcula progresso + persiste imediatamente
- Tarefas concluídas com strikethrough

**Coluna direita (35%) — Registros + Timeline:**
- Lista de registros (autor, data, texto) em ordem decrescente
- Textarea + botão "Salvar" → prepend com autor = consultor ativo + timestamp ISO
- **Timeline do histórico** (abaixo dos registros): lista cronológica de `historicoEtapas` no formato `"Etapa A → Etapa B • DD/MM/AAAA · motivo: ..."`; primeira entrada exibe só `"→ Etapa A"`

**Modal "Alterar Etapa":**
- Select de nova etapa (exceto a atual)
- Textarea de motivo (obrigatório — botão Salvar desabilitado se vazio)
- Ao salvar: atualiza `etapa`, append em `historicoEtapas`, recalcula status, fecha modal

### Tela 4 — Criar Playbook (`#criar`)

**Parte 1 — Dados:**
- Nome do cliente (text)
- ID do cliente (text, ex: KMSIL)
- Projeto SAGP (text, ex: SAGP-00036)
- Produto (select: CPS / IOT / Portal da Cotação / GRV Connect)
- Consultor responsável (select dos consultores cadastrados)
- Data início (date)
- Prazo final (date)
- Etapa inicial (select das 7 etapas)
- Observações (textarea)

**Parte 2 — Builder de tarefas:**
- Select "Usar modelo base" → pré-popula as 4 fases com tarefas padrão
- 4 abas (1ª Reunião / Engajamento / Evolução / Conclusão)
- Em cada aba: lista de tarefas + campo texto + botão "+ Tarefa" + botão ✕ por tarefa

**Salvar:** cria objeto completo com `historicoEtapas[0]` = `{ de: null, para: etapaInicial, data: now, motivo: "Início do projeto" }`, persiste no localStorage, redireciona para `#cliente/:id` do novo cliente.

---

## Template Padrão de Tarefas

| Fase | Tarefas |
|---|---|
| 1ª Reunião & Kickoff | Apresentar cronograma do projeto · Validar interlocutores e lideranças · Alinhar expectativas e escopo · Configurar acessos ao SAG |
| Engajamento | Acompanhar parametrização inicial · Validar importação de dados · Treinar usuários-chave · Revisar módulos prioritários |
| Evolução | Monitorar adoção do sistema · Resolver pendências técnicas · Realizar checkpoint de progresso · Alinhar próximas etapas com o cliente |
| Conclusão | Validar entrega final com cliente · Coletar feedback (CSAT) · Emitir termo de conclusão · Transição para sustentação |

---

## Casos de Borda

| Cenário | Comportamento |
|---|---|
| Playbook sem tarefas | Progresso = 0%, sem erro |
| Prazo não definido | Exibe "Sem prazo", status nunca deriva "Atrasado" |
| Novo cliente (Tela 4) | Aparece imediatamente na Tela 1 e Tela 2 |
| Carteira vazia | Tela 1 exibe estado vazio: "Nenhum cliente nesta carteira" |
| Modal Alterar Etapa | Botão Salvar desabilitado se motivo vazio |
| `historicoEtapas[0]` | `de: null`, motivo fixo "Início do projeto" |
