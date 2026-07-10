# GRV CS — Redesign das Abas do Detalhe do Cliente

**Status:** Aprovado pelo usuário
**Data:** 2026-07-10
**Escopo:** Reorganização do header e das 3 abas (Visão 360, Atividades, Notas) na tela de detalhe do cliente. Estrutura de rotas, dados e lógica de negócio não mudam.

---

## Diagnóstico

Seis problemas identificados nas abas atuais:

1. **Health score ausente** — `c.healthHistory` existe e é calculado, mas não aparece em nenhum lugar da tela de detalhe. O CS precisa sair da tela para saber a saúde do cliente.
2. **Header sem contexto vital** — o header atual mostra nome, chips de status e etapa, mas não CSAT, NPS nem próxima ação. O CS abre a tela sem o estado do cliente.
3. **Visão 360 sobrecarregada** — 6 blocos heterogêneos (KPIs estáticos, timeline, ciclo de vida, contatos, CSAT, NPS) sem hierarquia clara. Nada tem prioridade.
4. **Atividades exige navegação cega** — sem visão consolidada de atrasos, o CS precisa clicar em cada playbook para descobrir o que está vencido.
5. **Notas sem estrutura** — campo texto único sem tipo, sem distinção entre observação, alerta e decisão. Informações importantes se perdem no scroll.
6. **Ícones oversized** — `es-icon` a 40px e ícones de empty state a 32px são grandes demais para o contexto denso de uma tela de detalhe.

---

## Abordagem escolhida: Header rico + tabs focadas (Opção A)

Manter a estrutura de 3 tabs existente. Enriquecer o header para que os 4 indicadores vitais (health, CSAT, NPS, próxima ação) sejam sempre visíveis — independentemente da aba ativa. Cada aba ganha um propósito único e claro.

---

## Novo header do cliente

### Estrutura

```
[← Minha Carteira]  [Avatar]  [Nome — Razão Social]          [Editar] [+ Atividade]
                              [Código SAGP · X dias como cliente]
                              [CS Ativo] [Engajamento] [Segmento] [Produto]

┌─ Health Score ──┬─ CSAT ──────────┬─ NPS ───────┬─ Próxima ação ─────────────────┐
│  82  ↑+4       │  4.2 /5         │  32          │  QBR mensal                    │
│  vs mês ant.   │  Última: 03/07  │  Bom         │  Amanhã · 14h · Ana Costa      │
└─────────────────┴─────────────────┴──────────────┴────────────────────────────────┘
```

### Regras da KPI strip

- **Health Score:** valor de `calcHealthScore(c)`. Cor: verde ≥ 70, amarelo ≥ 40, vermelho < 40. Subtítulo: delta vs mês anterior (se `healthHistory` tiver ≥ 2 entradas).
- **CSAT:** valor de `calcCsatAtual(c)`. Formato `X.X / 5`. Subtítulo: data da última resposta.
- **NPS:** valor de `calcNps(c)`. Cor: verde ≥ 50, amarelo ≥ 0, vermelho < 0. Subtítulo: label semântico (Excelente / Bom / Crítico).
- **Próxima ação:** Exibir `c.proximaAcao` como label principal. Para a data/horário, buscar a atividade não concluída com `at.dataLimite` mais próxima do dia atual entre todos os playbooks ativos. Se não houver atividade futura, exibir apenas `c.proximaAcao` sem data. Se `c.proximaAcao` estiver vazio, exibir `—`.
- Se qualquer valor estiver ausente (sem respostas CSAT, sem NPS, sem saúde), exibir `—` no lugar do número.

### CSS da strip

```css
.dc-kpi-strip{display:flex;border-top:1px solid var(--border-2)}
.dc-kpi{
  flex:1;padding:10px 14px;border-right:1px solid var(--border-2);
}
.dc-kpi:last-child{border-right:none;flex:2}
.dc-kpi-label{
  font-size:9px;font-weight:700;text-transform:uppercase;
  letter-spacing:.08em;color:var(--text4);margin-bottom:4px;
}
.dc-kpi-val{
  font-size:22px;font-weight:800;line-height:1;
  font-variant-numeric:tabular-nums;letter-spacing:-.8px;
}
.dc-kpi-sub{font-size:10px;color:var(--text3);margin-top:2px}
```

---

## Aba Visão 360

**Propósito:** referência estática do cliente. Não é dashboard — é ficha cadastral + histórico.

### Layout (2 colunas)

**Coluna esquerda:**
1. Grid 4 cards: Segmento · Produto · CS Responsável · Consultor Digital
2. Bloco "Ciclo de vida": Início implantação · Entrada CS · Tempo como cliente
3. Bloco "Contatos": lista compacta com links de e-mail e WhatsApp + botão "+ Adicionar"

**Coluna direita:**
4. Bloco "CSAT": score atual grande + lista das últimas 3 respostas (score pill + data + obs)
5. Bloco "NPS": score atual grande + lista das últimas 3 respostas (score pill + tipo Promotor/Neutro/Detrator + data + comentário)

### Mudanças vs atual

- **Remove:** bloco de "Histórico de etapas" (timeline) da Visão 360. Esse histórico vai para uma futura aba de Histórico ou fica acessível via botão "Ver histórico" dentro do bloco Ciclo de vida.
- **Remove:** bloco laranja de ciclo de vida separado — integrado ao card "Ciclo de vida" acima.
- **Mantém:** formulários inline de CSAT e NPS (+ Registrar).
- **Mantém:** formulário inline de contato (+ Adicionar).

### Contatos — novo layout

```
[JS]  João Silva                  
      Diretor de TI               
      [✉ E-mail] [📞 WhatsApp]   
```

Links substituem os emoji `✉` e `📱` por ícones SVG de 10px dentro de chips clicáveis (`.contato-link`).

### Empty states nestas abas

Ícones SVG de **24px** (não 40px). Texto em 13px, cor `var(--text3)`.

---

## Aba Atividades

**Propósito:** ação. O CS chega aqui para saber o que fazer e executar.

**Aba padrão ao abrir a tela de detalhe** (substituir `_cliente_aba` default de `'360'` para `'at'`).

### Alerta consolidado

Faixa vermelha suave no topo da aba, antes da coluna de playbooks:

```
[⚠]  2 atividades atrasadas · 1 vence hoje          [Ver todas]
```

- Aparece apenas se houver atividades atrasadas ou com prazo hoje (across ALL playbooks).
- "Ver todas" filtra a lista de atividades na coluna direita para mostrar todas as atrasadas/hoje, independente do playbook selecionado.
- CSS: `background: rgba(220,38,38,.05)`, `border: 1px solid rgba(220,38,38,.15)`, `border-radius: 8px`, `padding: 8px 12px`.

### Layout (2 colunas — mantém estrutura atual)

**Coluna esquerda — Playbooks (220px fixo):**
- Label "PLAYBOOKS" em caps 9px
- Cada playbook card: nome + badge de alerta se houver atrasos + meta "N ativ · N concluídas" + barra de progresso 3px
- Barra de progresso: verde se ≥ 80% concluído, laranja se < 80%
- Badge de alerta: `<span class="pb-badge-alert">N atraso</span>` em vermelho suave
- Playbook selecionado: borda laranja + `box-shadow: 0 0 0 2px rgba(224,90,30,.1)`
- "+ Novo playbook": botão dashed, sem preenchimento

**Coluna direita — Atividades:**
- Header: nome do playbook selecionado + select de dono + botão "+ Atividade"
- Cada row de atividade:
  - Stripe lateral 3px de criticidade (vermelho = atrasada, laranja = hoje, transparente = demais)
  - Checkbox (16px, border-radius 4px)
  - Ícone SVG 26px (container circular, cor `var(--text3)`) por tipo de atividade
  - Nome da atividade
  - Badge SLA: "3d atrás" (vermelho), "Hoje" (laranja), "+5 dias" (amarelo), data de conclusão (verde)
  - Nome do responsável (pill cinza)
  - Badge de status: Atrasada / Em andamento / Pendente / Concluída

### Ícones por tipo de atividade

Mesmos SVGs implementados no uplift anterior (Task 5). Nenhuma mudança de ícone.

### Empty state da aba Atividades

Ícone SVG 24px + "Nenhum playbook criado ainda." + botão "+ Novo playbook".

---

## Aba Notas

**Propósito:** memória. O CS registra o que aconteceu, o que foi decidido, o que precisa de atenção.

### Estrutura

```
Notas                                              [+ Nova nota]
┌────────────────────────────────────────────────────────────┐
│ [ALERTA]  Ana Costa · 07/07                                │
│ Cliente sinalizou insatisfação com tempo de resposta...    │
├────────────────────────────────────────────────────────────┤
│ [DECISÃO]  Pedro Lima · 03/07                              │
│ Alinhado novo ciclo de QBR trimestral a partir de agosto.  │
├────────────────────────────────────────────────────────────┤
│ [OBSERVAÇÃO]  Ana Costa · 28/06                            │
│ Reunião muito produtiva. Cliente demonstrou interesse...   │
└────────────────────────────────────────────────────────────┘
```

### Tipos de nota (novo)

Três tipos, cada um com stripe lateral colorida e badge:

| Tipo | Stripe | Badge |
|------|--------|-------|
| Observação | `var(--text4)` (cinza) | Fundo neutro |
| Alerta | `var(--red)` | Fundo vermelho suave |
| Decisão | `#2563EB` (azul) | Fundo azul suave |

### Formulário de nova nota

```
Tipo: [Observação ▾]
[textarea placeholder="Escreva sua nota aqui..."]
                                   [Cancelar] [Salvar nota]
```

- Formulário oculto por padrão. Aparece ao clicar "+ Nova nota".
- Tipo é um `<select>` com 3 opções: Observação, Alerta, Decisão.
- O tipo selecionado define a stripe e o badge da nota salva.

### Migração de dados

O campo `tipo` é novo. Notas existentes em `c.registros[]` não têm `r.tipo`. Renderizar sem badge de tipo (apenas stripe cinza) se `r.tipo` for `undefined` ou `null`.

### Empty state

Ícone SVG 24px + "Nenhuma nota registrada." + link "Adicionar primeira nota".

---

## Ordem das tabs

```
[Visão 360] [Atividades ⚠N] [Notas]
```

- **Default ao abrir:** Atividades (substituir `_cliente_aba = '360'` por `_cliente_aba = 'at'` em `renderCliente()`).
- **Badge no tab de Atividades:** número de atividades atrasadas (vermelho). Não aparece se zero.
- Ordem visual: Visão 360 primeiro (referência), Atividades segundo (ação), Notas terceiro (memória).

---

## O que não muda

- Funções de cálculo: `calcHealthScore()`, `calcCsatAtual()`, `calcNps()`, `getProgresso()`, `tempoComoCliente()`
- Estrutura de dados de `c.ativPlaybooks[]`, `c.csatRespostas[]`, `c.npsRespostas[]`, `c.contatos[]`, `c.registros[]`
- Hash routing e `renderCliente(id)` como orquestradora
- Formulários inline de CSAT, NPS, contato (apenas reposicionados)
- Lógica de playbook: criar, pausar, cancelar, excluir
- Lógica de atividade: criar, concluir, alterar responsável
- CSS de chips (`.chip-base`, `.chip-status-*`, `.chip-seg`, `.chip-prod`)

---

## Não incluso neste redesign

- Timeline de histórico de etapas (removida da Visão 360; pode ser aba futura)
- Dark mode
- Edição inline de CSAT/NPS existentes
- Comentários ou threads em atividades individuais
- Filtro ou busca dentro de Notas
