# Central de Atenção — Design Spec

**Data:** 2026-07-07  
**Status:** Aprovado  
**Escopo:** Enriquecer as 3 abas do menu Projetos GRV sem adicionar nova tela

---

## Objetivo

Permitir que consultores e gestores identifiquem e atuem sobre clientes urgentes em segundos, sem precisar varrer a lista inteira. A urgência fica visível no próprio nav, filtrável por aba e acionável via menu rápido diretamente na linha.

---

## Componentes

### 1. Badge de Urgências no Nav

**Onde:** span `#nav-proj-subbadge` já existe dentro de `#nav-projetos`. Adicionar um novo span `#nav-urg-badge` ao lado.

**Comportamento:**
- Exibe o total de clientes urgentes em **todas as abas** somadas.
- Atualiza toda vez que qualquer render de aba for chamado: `renderPortfolio`, `renderImplantacao`, `renderCustomer`.
- Oculto (display:none) quando contagem = 0.
- Estilo: pill vermelho (#dc2626), 9.5px bold, animação `box-shadow` pulse de 2.5s.

**Função helper:** `countUrgentes()` — percorre `getClientes()` com `isUrgente(c)` e retorna inteiro. Chamada ao final de cada render.

---

### 2. Botão ⚡ Urgentes por Aba

**Onde:** linha de controles acima da tabela/kanban em cada aba (nas views Lista e Kanban; não aparece na view Dashboard, que já agrega por visão geral).

**Comportamento:**
- Toggle. Estado padrão: desligado (mostra todos).
- Quando ligado: filtra a lista/kanban para exibir apenas linhas urgentes; exibe hint abaixo dos controles: "Mostrando N urgentes de X clientes [× Limpar]".
- Limpar desliga o filtro.
- O filtro é por aba: ligar em Customer não afeta Implantação.
- Estado não persiste entre navegações (sempre começa desligado).

**Não aparece** quando a aba não tem nenhum urgente (botão escondido, não desabilitado, para não gerar dúvida).

---

### 3. Botão `···` só em Linhas Urgentes

**Onde:** coluna de ação no extremo direito da tabela, apenas nas linhas onde `isUrgente(c) === true`.

**Linhas normais:** a célula fica vazia (não renderizar o botão — evitar a sensação de ação vazia).

**Popover:** abre alinhado à direita da célula, acima ou abaixo dependendo de espaço. Fecha ao clicar fora ou ao abrir outro popover.

**Ações do popover:**
| Ação | Comportamento |
|------|--------------|
| Registrar contato | Navega para aba Atividades do cliente, foco no campo de novo registro |
| Atualizar próxima ação | Abre modal inline de edição do campo `proximaAcao` do cliente |
| Abrir cliente | `navigate('cliente-' + c.id)` (comportamento já existente no clique da linha) |

---

## Critério de Urgência (`isUrgente`)

Uma função central decide se um cliente é urgente. Mesma lógica usada para badge, filtro e `···`.

```
isUrgente(c):
  se c.status !== 'cs_ativo'  →  Implantação
    urgente se: c.atrasado === true  OU  getDiasUltimoContato(c) > 14
  
  se c.status === 'cs_ativo'  →  Customer / Portfólio
    urgente se: calcHealthScore(c) < 40  OU  getDiasUltimoContato(c) > 30
```

Não há urgência parcial — é binário. O critério pode evoluir sem alterar os componentes, pois é centralizado.

---

## Ação "Atualizar próxima ação"

Único componente novo de UI fora da lista. Modal leve inline (não rota nova):

- Título: nome do cliente
- Campo textarea: `c.proximaAcao` pré-preenchido
- Botões: Salvar / Cancelar
- Salvar: atualiza o campo no estado local e re-renderiza a aba atual.
- Não persiste em servidor nesta iteração (mesma mecânica de edição já existente no app).

---

## O que não muda

- Estrutura das rotas e abas.
- Comportamento do clique na linha (abre cliente).
- View Dashboard em qualquer aba — o botão Urgentes não aparece lá.
- Linhas normais — sem ação `···`, sem destaque de cor.
- Colunas existentes das tabelas — não adicionar coluna, o `···` ocupa célula já existente (ou última coluna).

---

## Implementação: pontos de atenção

- `isUrgente` deve ser pura (sem side effects) para ser chamada por badge e por render.
- O badge atualiza **após** o `sec.innerHTML` ser escrito, nunca antes.
- O popover usa `position:absolute` dentro de `position:relative` na célula — evitar z-index global desnecessário.
- Fechar popover ao scroll da tabela (listener `scroll` no table-wrap, remove classe `.vis`).
- Em Kanban, o `···` aparece no card urgente (não em coluna), mesma lógica de popover.
