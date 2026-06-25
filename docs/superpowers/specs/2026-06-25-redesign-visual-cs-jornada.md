# Design Spec — Redesign Visual e Funcional do GRV CS Jornada

**Data:** 2026-06-25
**Escopo:** `grv-cs-jornada.html` — redesign completo de navegação, visual e modelo de dados

---

## Contexto

O sistema atual tem telas parecidas, muito carregadas de blocos quadrados e navegação pouco intuitiva. O objetivo é tornar o app fluido, moderno e fácil de usar — mantendo toda a funcionalidade existente, com visual alinhado ao SAG (Sistema de Atendimento GRV).

### Sequenciamento

Esta spec **depende de v3 (abas 360°/Atividades/Notas) estar concluída**. Não interrompe v3 — estende sua estrutura de dados. O plano de implementação deve ser executado após o merge de v3.

---

## Modelo de Dados Consolidado

### Cliente — permanente e eterno

O cliente **nunca morre** no sistema. Ele existe enquanto estiver contratado, acumulando histórico desde a implantação até o CS contínuo. Não há conceito de "encerrado" — apenas de "fase atual".

```
Cliente
  ├── id, nome, cnpj, segmento
  ├── status: 'em_implantacao' | 'cs_ativo'
  ├── csId (consultor CS responsável)
  ├── dataInicioImplantacao
  ├── dataInicioCS (null enquanto em implantação)
  ├── csat (média das avaliações)
  ├── Notas[] (registro livre, histórico)
  └── ativPlaybooks[]            ← nome canônico; mantém compatibilidade com v3
        ├── id, titulo
        ├── donoId (consultor que criou/é responsável)
        ├── fase: 'implantacao' | 'cs'
        ├── progresso (calculado das atividades)
        └── atividades[]
              ├── id, titulo
              ├── responsavelId (pode ser diferente do dono do playbook)
              ├── status: 'pendente' | 'em_andamento' | 'concluida' | 'atrasada'
              ├── dataLimite
              ├── registros[]    ← log de atualizações (quem, quando, texto)
              ├── checklist[]    ← sub-itens com done:boolean
              └── anotacoes[]    ← notas privadas do responsável
```

### Regra de Minha Carteira

> Um consultor vê um cliente na sua carteira se ele é **dono de pelo menos um playbook** desse cliente.

Atividades delegadas a ele (mas cujo playbook é de outro) aparecem em notificações/filtros, não em Minha Carteira.

**Migração do seed:** Os 38 clientes do `SEED_CLIENTES` não têm `donoId` nos playbooks. O task de migração deve popular `playbook.donoId = cliente.csId` para todos os playbooks existentes, e inicializar `registros: []`, `checklist: []`, `anotacoes: []` em cada atividade.

### Regras de Status do Cliente

Calculado a partir dos playbooks de implantação do consultor logado:

| Status | Stripe | Badge | Regra |
|---|---|---|---|
| `inicio` | azul `#3182ce` | "Início" | progresso < 15% |
| `em_ordem` | verde `#38a169` | "Em ordem" | sem atividades atrasadas e nenhum prazo em ≤7 dias |
| `atencao` | amarelo `#d69e2e` | "Atenção" | alguma atividade com `dataLimite` entre hoje e +7 dias, sem atraso real |
| `atrasado` | vermelho `#e53e3e` | "Atrasado" | alguma atividade com `dataLimite < hoje` e `status !== 'concluida'` |

Função `getStatusCliente(cliente, consultorId)`:
```javascript
function getStatusCliente(cliente, consultorId) {
  const meusPbs = (cliente.ativPlaybooks || [])
    .filter(pb => pb.donoId === consultorId);
  const atividades = meusPbs.flatMap(pb => pb.atividades || []);
  const hoje = new Date(); hoje.setHours(0,0,0,0);
  const em7dias = new Date(hoje); em7dias.setDate(em7dias.getDate() + 7);
  const pendentes = atividades.filter(a => a.status !== 'concluida');
  if (pendentes.some(a => a.dataLimite && new Date(a.dataLimite) < hoje))
    return 'atrasado';
  if (pendentes.some(a => a.dataLimite && new Date(a.dataLimite) <= em7dias))
    return 'atencao';
  const progresso = calcProgresso(meusPbs);
  if (progresso < 15) return 'inicio';
  return 'em_ordem';
}
```

### Transição Implantação → CS (auto-advance adaptado)

**Trigger:** última atividade do playbook de implantação marcada como `concluida`.

**Comportamento:**
1. Sistema detecta que todas as atividades do playbook de fase `'implantacao'` estão `concluida`
2. Exibe toast: *"Implantação concluída! Mover cliente para CS Ativo?"* com botão [Confirmar]
3. Ao confirmar: `cliente.status = 'cs_ativo'`, `cliente.dataInicioCS = new Date().toISOString()`
4. O evento é adicionado como registro automático no historial: *"Implantação encerrada — cliente movido para CS Ativo"*
5. O playbook de implantação permanece visível com badge "Encerrado" (read-only)

O `historicoEtapas` existente é preservado como fonte dos eventos automáticos que aparecem no feed do Registro de cada atividade.

---

## Telas

### 1. Sidebar — estilo SAG

Aplicada em **todas as telas**. Não mais dark (#1a202c).

| Elemento | Valor |
|---|---|
| Background | `#ffffff` |
| Borda direita | `1px solid #e8ecf0` |
| Item inativo | texto `#4a5568`, ícone outline cinza (opacity 0.45) |
| Item ativo | background `#FFF3EE`, texto `#E05A1E`, ícone opacity 1 |
| Logo GRV | ícone laranja `#E05A1E` + texto "GRV Software" |
| Rodapé | "Consultor ativo" → avatar laranja + nome |

Itens de navegação:
- **Projetos GRV** (ícone globo)
- **Minha Carteira** (ícone grid)
- **Criar Playbook** (ícone +)

---

### 2. Minha Carteira

**Remoção:** view "Jornada" removida. Ficam apenas **Feed** e **Kanban**.

#### 2a. View Feed

Card por cliente com:
- **Stripe colorida** (4px, posição left) indicando urgência: vermelho=atrasado, verde=em ordem, amarelo=atenção, azul=início
- Avatar circular com inicial da empresa (gradiente por tipo)
- Nome da empresa + fase atual + playbook
- Badge de status (pill colorido): "Atrasado" / "Em ordem" / "Atenção" / "Início"
- CSAT com estrela (se disponível)
- Mini progress bar (64px)

Clicar no card navega para o detalhe do cliente.

#### 2b. View Kanban

Colunas fixas (ordem fixa, da esquerda para a direita):

| Coluna | Regra |
|---|---|
| 1ª Reunião | `status === 'em_implantacao'` e progresso < 15% |
| Implantação | `status === 'em_implantacao'` e 15% ≤ progresso < 50% |
| Evolução | `status === 'em_implantacao'` e 50% ≤ progresso < 85% |
| Conclusão | `status === 'em_implantacao'` e progresso ≥ 85% |
| CS Ativo | `status === 'cs_ativo'` |

Progresso calculado sobre o `ativPlaybook` de fase `'implantacao'` cujo `donoId === consultorAtivo`. Se o consultor não tem playbook de implantação, usa o primeiro `ativPlaybook` disponível.

```javascript
function getKanbanColuna(cliente, consultorId) {
  if (cliente.status === 'cs_ativo') return 'CS Ativo';
  const pb = (cliente.ativPlaybooks || []).find(
    p => p.fase === 'implantacao' && p.donoId === consultorId
  ) || (cliente.ativPlaybooks || [])[0];
  const prog = calcProgresso(pb);
  if (prog < 15)  return '1ª Reunião';
  if (prog < 50)  return 'Implantação';
  if (prog < 85)  return 'Evolução';
  return 'Conclusão';
}
```

Card Kanban:
- Stripe colorida no topo (3px, border-radius top)
- Nome da empresa
- Nome do playbook
- Progress % + badge de status
- Clicar navega para o detalhe

#### Toolbar compartilhada

- Campo de busca (filtro por nome)
- Filtro de status (dropdown)
- Toggle Feed ↔ Kanban (direita, pill com ícones)

---

### 3. Detalhe do Cliente

Header fixo com:
- Botão ← (volta para Minha Carteira)
- Avatar + nome + CNPJ + consultor CS
- Chips de status, segmento, playbook

Tabs: **Visão 360°** | **Atividades** | **Notas**

#### 3a. Visão 360°

Grid 2 colunas:
- Card Progresso: % total + barras por fase (Implantação / Evolução / Conclusão)
- Card CSAT: média com estrela + histograma de avaliações
- Card Checklist (largura total): itens da fase atual com check visual

Informações históricas (quando `status === 'cs_ativo'`):
- Data de início da implantação
- Data de entrada no CS
- Tempo como cliente (ex: "1 ano e 4 meses")

#### 3b. Atividades

Layout master-detail em grid `220px 1fr`:

**Painel esquerdo — Playbooks:**
- Lista de playbooks do consultor logado neste cliente
- Cada item: nome, contagem de atividades, mini progress bar laranja
- Item ativo com borda laranja + shadow suave
- Botão "+ Novo Playbook" (dashed border)

**Painel direito — Atividades do playbook selecionado:**
- Header: nome do playbook + botão "+ Atividade"
- Lista de atividades com:
  - Checkbox (verde quando done)
  - Nome da atividade
  - Nome do responsável (pode diferir do dono do playbook)
  - Badge de status
- **Clicar em qualquer linha** → abre overlay de atividade

#### Overlay de Atividade (slide-over)

Aparece **por cima** da tela atual (não navega). Anima da direita (`transform: translateX(100%)` → `0`). Backdrop semi-transparente (`rgba(15,20,30,.35)`) fecha ao clicar.

Estrutura do painel (420px largura):
```
Header:
  [Título da atividade]                    [✕]
  [Avatar responsável] Nome · [Badge status]
  [Registro] [Checklist] [Anotação]
─────────────────────────────────────────
Body (scroll):
  conteúdo da aba ativa
```

**Aba Registro:**
- Campo de texto (textarea) + botão "Registrar" — adiciona nova entrada no topo
- Timeline cronológica: avatar + quem + quando + texto da mensagem
- Eventos automáticos intercalados (ex: "Severiano marcou como Concluída — 15 jun 14h22")

**Aba Checklist:**
- Progress bar (calculada dos itens)
- Lista de sub-itens com checkbox individual
- Botão "+ Adicionar item" ao final

**Aba Anotação:**
- Textarea para nova anotação privada
- Cards amarelos (`#FFFBEB`) com anotações anteriores (data + autor + texto)

#### 3c. Notas

- Textarea no topo para nova nota
- Cards brancos com data, autor e texto em ordem cronológica reversa

---

### 4. Projetos GRV

Visão gerencial de toda a equipe.

**KPIs (4 cards):**
- Clientes ativos (total)
- CSAT médio (com estrela)
- Em atraso (count + %)
- Progresso médio

**Gráficos (3, lado a lado):**
1. **Donut** — distribuição de status: Em ordem / Atrasado / Atenção / Início
2. **Barras** — ativações por mês (últimos 6 meses)
3. **Gauge/barras horizontais** — indicadores CS: CSAT, SLA compliance, engajamento, % em atraso, % conclusões

**Tabela de Consultores:**
- Colunas: Consultor, Clientes, CSAT, Atrasados, Progresso (mini bar)
- Ordenável por CSAT e atrasados

---

## Tokens de Design

```css
--primary:   #E05A1E;
--bg:        #f8f9fb;
--surface:   #ffffff;
--border:    #e8ecf0;
--border-2:  #f0f2f5;
--text:      #1a202c;
--text2:     #4a5568;
--text3:     #718096;
--text4:     #a0aec0;
--radius:    12px;
--radius-sm: 9px;
--green:     #38a169;
--red:       #e53e3e;
--yellow:    #d69e2e;
--blue:      #3182ce;

/* status badge backgrounds */
--b-green-bg: #F0FFF4;
--b-red-bg:   #FFF5F5;
--b-orange-bg:#FFF3EE;
--b-blue-bg:  #EBF8FF;
```

---

## Interações e Animações

| Evento | Comportamento |
|---|---|
| Hover em card Feed | borda laranja + shadow suave |
| Clicar atividade | overlay slide-in 220ms cubic-bezier(.4,0,.2,1) |
| Fechar overlay | click no backdrop ou ✕ |
| Toggle Feed/Kanban | troca instantânea, sem animação de página |
| Navegar tabs cliente | troca de conteúdo, sem reload |
| Navegar tabs overlay | troca de conteúdo, sem animação |

---

## O Que Muda vs. Versão Atual

| Área | Antes | Depois |
|---|---|---|
| Sidebar | Dark `#1a202c` | Branca estilo SAG |
| Minha Carteira views | Lista, Jornada, Kanban | Feed, Kanban |
| Cards de cliente | Blocos quadrados | Rounded + stripe colorida |
| Atividade — clique | Expande no lugar | Overlay slide-over |
| Overlay — conteúdo | Apenas registro | Registro + Checklist + Anotação |
| Atividade — responsável | Campo de texto | Link para consultor (nome + avatar) |
| Playbook — dono | Não existia | `donoId` obrigatório |
| Cliente — lifecycle | "Encerrado" apagava | CS Ativo permanente |
| Projetos GRV | Gráficos presentes | Mantidos + tabela de consultores |

---

## Fora do Escopo

- Autenticação real / multi-tenant
- Notificações push para atividades delegadas
- Comentários em atividades de outros consultores
- Filtros avançados na tabela de consultores

---

## Checklist de Correções Aplicadas (revisão técnica)

- [x] Sequenciamento explícito: executa após v3
- [x] `getStatusCliente()` com regra completa para "Atenção" (≤7 dias) e "Início" (<15%)
- [x] Auto-advance adaptado: conclusão do playbook implantação → toast → `cs_ativo`
- [x] `historicoEtapas` preservado como fonte de eventos automáticos no Registro
- [x] Migração do seed: `donoId`, `registros[]`, `checklist[]`, `anotacoes[]`
- [x] Array canônico `ativPlaybooks[]` — consistente com v3, usado em todo o spec
- [x] `getKanbanColuna()` definida com regra explícita por faixas de progresso
