# Design Spec — Assistente de chat embutido (sem IA externa)

**Data:** 2026-09-28
**Projeto:** GRV SAC — Painel de Atendimento
**Status:** Aprovado para implementação
**Escopo:** Painel flutuante novo, disponível em Painel/Agentes/Análise/Configurações. Não altera nenhuma tela existente além de acrescentar o botão de abertura.

---

## Contexto

Pedido original: trazer pra dentro do dashboard "o conceito harness" — uma IA que conversa, muda filtro por mensagem e busca qualquer informação da API do Chatwoot, do jeito que se conversa com o Claude nesta sessão.

Decisão tomada durante o brainstorming, e que muda a arquitetura inteira: **sem chamada a modelo de IA nenhum**. Nada de Netlify Function nova, nada de chave de API secreta, nada de custo por pergunta. O "entendimento" vem de um leitor de padrões que roda 100% no navegador, reconhecendo pedaços da frase (quem, quando, o quê, ação) contra dados reais já carregados no dashboard (`_teamMap`, `_agentList`) e executando através das mesmas funções que o resto da UI já usa.

**Por que isso é aceitável apesar de não ser "IA de verdade":** o dashboard já tem toda a lógica de busca e formatação de dado pronta e testada (nesta mesma sessão, auditada linha por linha). O assistente não recalcula nada — só decide qual pergunta o usuário fez e chama a função certa. A "inteligência" percebida vem de reconhecer bem os pedaços da frase, não de gerar texto livre.

---

## 1 · Visual e localização

Botão flutuante circular, ícone de estrela, fixo no canto inferior direito, visível em todas as páginas (`#content`, `#agentes-page`, `#graficos-page`, `#config-page`). Ao clicar, abre um painel deslizando da direita:

- Largura ~400px, altura cheia da viewport, `position:fixed`, `z-index` acima dos modais existentes.
- **Sem backdrop** — diferente dos modais do dashboard, não escurece nem bloqueia o resto da tela. O usuário continua vendo e interagindo com a página atrás.
- Cabeçalho: título "Assistente" + botão fechar.
- Corpo: lista de mensagens rolável (bolhas usuário à direita, assistente à esquerda, reaproveitando a paleta de cores já usada nos badges — verde/amarelo/vermelho quando a resposta cita uma métrica com meta).
- Rodapé: input de texto + botão enviar. Quando a conversa está vazia, mostra 3–4 chips de sugestão (ex: "Como está a equipe 2 este mês?", "Quantas conversas estão abertas agora?").
- Anima entrada/saída com slide + fade (~200ms), sem bloquear input durante a animação.

Implementado como um único bloco HTML/CSS/JS na base do arquivo, fora de qualquer `<div>` de página específica — existe uma vez, funciona em qualquer aba.

---

## 2 · Arquitetura do "entendimento"

### 2.1 Normalização
Toda mensagem passa por: minúsculas, remoção de acento, colapso de espaços.

### 2.2 Extração de entidades (independente de posição na frase)
Varre o texto procurando o **casamento mais longo** em cada uma destas listas, sem exigir ordem ou frase exata:

| Entidade | Fonte | Exemplos que casam |
|---|---|---|
| Equipe | `_teamMap` + `SAG_FILTER_ID` | "equipe 2", "equipe dois", "sag", "consultoria" |
| Agente | `_agentList` | "arthur", "arthur gomes", "guilherme ribeiro" |
| Período relativo | tabela fixa | "esse mês", "mês passado", "essa semana", "hoje", "3 meses", "6 meses", "12 meses", "esse trimestre" (= 3 meses) |
| Mês nomeado | tabela fixa (jan–dez) | "agosto", "setembro" → mês calendário completo, ano corrente |
| Métrica | tabela fixa de sinônimos | "volume/atendimentos" · "resolvidos/resolução/taxa" · "tempo de resposta/1ª resposta/tmr" · "tempo de atendimento/tempo de resolução/tma" · "csat/satisfação/nota/avaliação" · "pontuação/score" · "mensagens por conversa" |
| Fila ao vivo | tabela fixa | "abertas agora", "pendentes", "sem resposta"/"não atendidas" (`unattended`), "não atribuídas" (`unassigned`), "online agora" |

**Fora de escopo da v1, deliberadamente:** intervalo de datas livre por texto ("de 1 a 15 de agosto"). O seletor de período personalizado já existe na UI para isso; o chat cobre mês relativo, mês nomeado inteiro e N-meses.

### 2.3 Detecção de ação
Verbos/expressões, checados nesta ordem de prioridade:
1. **Navegar** — "vai pra", "abre", "muda pra aba" + nome de página
2. **Filtrar** — "mostra só", "filtra", "filtra pelo/pela", "tira o filtro", "limpa filtro", "volta pra todas"
3. **Resumir** — "resumo", "como estamos", "o que mudou" sem entidade específica de equipe/agente
4. **Perguntar** — qualquer combinação de métrica + (equipe|agente|conta) + período; é o padrão quando nenhum verbo de ação explícito é encontrado mas há métrica reconhecida

### 2.4 Duas entidades do mesmo tipo → comparação
Se a frase contém dois nomes de equipe (ou dois de agente) junto de uma métrica, vira intenção de comparação: busca os dois, responde lado a lado. ("Compara equipe 1 com equipe 2")

### 2.5 Desambiguação
Conforme decidido: **nunca pausa esperando confirmação.** Quando dois candidatos empatam (ex.: "silva" casa com dois agentes), escolhe o de casamento mais específico (nome completo > substring) e, em empate real, o primeiro por ordem alfabética — sempre dizendo explicitamente quem escolheu, para o usuário corrigir se for o caso.

### 2.6 Execução
- **Filtrar/Navegar** → chama diretamente a função já existente (`setKpiPeriod`, `setAgentTabPeriod`, `showPage`, atribuição a `_teamFilter`/`_chartTeamFilter`/`_agentTabFilter` + a função de aplicar já usada pelo clique manual). Nunca duplica lógica de filtro.
- **Perguntar** → resolve dado assim:
  1. Se o que foi pedido (equipe/agente + período) já é exatamente o que está carregado na aba ativa, lê das variáveis já em memória (`_chartData`, `_agentPerfData`, `_teamCompData`, KPIs do Painel) — sem rede.
  2. Senão, faz uma chamada nova à API usando o mesmo formato de request que o dashboard já usa pra aquele dado (`reports/summary` por tipo, `csat_survey_responses`, `reports/conversations` para fila ao vivo) — **sem alterar o filtro/período que está selecionado na tela.**
- **Resumir** → lê os números já calculados da página ativa (KPIs do Painel, faixa de abertura da Análise, etc.) e monta 3–4 linhas.

### 2.7 Formatação da resposta
Um gerador de frase por tipo de métrica, sempre a partir de número real:
> "Equipe 2 teve 229 atendimentos em setembro, tempo de 1ª resposta de 19min ✓ (meta: 30min)."

Reaproveita `fmtSec`, `agentBadge` (cores de meta) e os textos que a própria Análise já usa pra explicar taxa >100%, quando a pergunta cair nesse caso.

**Perguntas de comparação** ("comparado ao mês passado", "melhorou", "subiu ou caiu") **reaproveitam a mesma janela de comparação já corrigida nesta sessão** — mesmo trecho decorrido do período anterior (`_chartTrendBase`/`trendPrev`), nunca um mês anterior completo contra um período parcial. Reintroduzir a comparação injusta aqui anularia a correção feita no Painel e na Análise.

### 2.8 Quando não reconhece nada
Não responde "não entendi" seco. Responde com 3–4 exemplos de comando que funcionam, no mesmo tom dos chips de sugestão. Registra a frase (ver §3).

---

## 3 · Caderno de perguntas não entendidas

- `localStorage['grv_harness_unmatched']` — array de `{ texto, contagem, ultimaVez }`, chave por texto normalizado, teto de 200 entradas distintas (LRU: descarta a menos recente ao estourar).
- Nova seção em Configurações: "Perguntas que o assistente não soube responder", tabela ordenada por contagem desc, botão "Limpar".
- **Limitação explícita da v1:** local ao navegador, não sincroniza entre pessoas/aparelhos.

---

## 4 · Memória de conversa

- Últimas entidades citadas (equipe/agente/período) guardadas em variável de sessão, só pra resolver perguntas de seguimento ("e em setembro?").
- Some ao fechar o painel. Histórico de mensagens (bolhas) também é só de sessão — recarregar a página limpa tudo. Nenhum conteúdo de conversa é persistido.

---

## 5 · Catálogo de treino (80 perguntas)

As 80 perguntas abaixo são o conjunto de teste/validação da implementação — cada uma precisa funcionar fim a fim antes de considerar a v1 pronta. Não são regras hardcoded; são casos de aceite do mecanismo de extração de entidades (§2.2–2.4).

**1 · Volume de atendimentos**
"Quantos atendimentos tivemos esse mês?" · "Quantas conversas entraram em agosto?" · "Qual foi o volume dos últimos 3 meses?" · "Como está o volume comparado ao mês passado?" · "Quantos atendimentos a equipe 2 teve em setembro?" · "Qual mês teve mais atendimentos nos últimos 6 meses?" · "Quantas conversas o SAG recebeu esse mês?" · "O volume subiu ou caiu essa semana?"

**2 · Velocidade**
"Qual o tempo médio de resposta esse mês?" · "Quanto tempo a equipe_tecnica leva pra resolver?" · "A 1ª resposta melhorou em relação ao mês passado?" · "Qual o TMR do Arthur Gomes?" · "Quanto tempo leva pra resolver, em média, esse trimestre?" · "Estamos dentro da meta de resposta?" · "Qual equipe responde mais rápido?" · "O tempo de resolução da consultoria está muito alto?"

**3 · Taxa de resolução**
"Qual a taxa de resolução desse mês?" · "Quantos atendimentos foram resolvidos em agosto?" · "Estamos batendo a meta de resolução?" · "Por que a taxa de resolução passou de 100%?" · "Quantos ficaram sem resolver esse mês?" · "Qual agente resolve mais conversas?" · "A equipe 3 está resolvendo dentro da meta?" · "Quantas conversas o Guilherme Ribeiro resolveu?"

**4 · CSAT / satisfação**
"Qual a satisfação do cliente esse mês?" · "Quantas avaliações recebemos em setembro?" · "Tem alguma avaliação ruim recente?" · "Qual agente tem a melhor nota de CSAT?" · "Quantos clientes deram 1 estrela?" · "Me mostra os comentários negativos desse mês" · "Qual a % de aprovação da equipe 1?" · "Alguém comentou algo sobre o Cristiano Gatto?"

**5 · Comparativo entre equipes**
"Qual equipe atendeu mais esse mês?" · "Compara equipe 1 com equipe 2" · "Qual equipe está pior em tempo de resposta?" · "Quantas equipes têm dado disponível esse período?" · "Como está o SAG comparado com as outras equipes?" · "Qual equipe tem a pontuação mais baixa?" · "A consultoria melhorou desde o mês passado?" · "Quais equipes estão fora da meta de resolução?"

**6 · Agente individual**
"Como está o Arthur Gomes esse mês?" · "Qual a pontuação do Vitor Augusto?" · "Quantas conversas a Priscila Costa atendeu?" · "O Mauricio Santos está dentro da meta?" · "Quem são os agentes com nota abaixo de 50?" · "Mostra o perfil do Guilherme Cabral" · "Quantos agentes estão com amostra pequena esse mês?" · "Qual agente teve a maior melhora este trimestre?"

**7 · Fila e status ao vivo**
"Quantas conversas estão abertas agora?" · "Tem gente esperando resposta?" · "Quantas conversas estão pendentes?" · "Quantas conversas estão sem nenhuma resposta?" · "Tem conversa sem atendente atribuído?" · "Qual o tempo de espera mais longo agora?" · "Quantos agentes estão online agora?" · "Quantas conversas o Ageu Carvalho tem em aberto agora?"

**8 · Navegação e controle**
"Mostra só a equipe 2" · "Filtra pelo Arthur Gomes" · "Tira o filtro de agente" · "Volta pra todas as equipes" · "Muda pra 3 meses" · "Vai pra aba Agentes" · "Me mostra a Análise desse trimestre" · "Limpa todos os filtros"

**9 · Ranking**
"Quem atendeu mais esse mês?" · "Qual agente tem a pior pontuação?" · "Quem tem o menor tempo de resposta?" · "Qual equipe cresceu mais desde o mês passado?" · "Quem recebeu mais avaliações de CSAT?" · "Qual o agente mais rápido pra resolver?" · "Quem está abaixo da meta de mensagens por conversa?" · "Qual inbox recebe mais atendimento?"

**10 · Conta, inboxes e configuração**
"Quantos inboxes a conta tem?" · "Qual a meta de SLA configurada hoje?" · "Quantos agentes existem no total?" · "Quais equipes existem no Chatwoot?" · "Qual o canal com mais volume?" · "O CSAT está ativado em todos os inboxes?" · "Quantas etiquetas (labels) existem?" · "Resumo geral: como estamos esse mês?"

---

## 6 · Fora de escopo (v1)

- Qualquer chamada a modelo de IA / API externa.
- Intervalo de datas livre por texto ("de 1 a 15 de agosto") — usar o seletor de período personalizado já existente.
- Sincronização do caderno de perguntas não entendidas entre pessoas/aparelhos.
- Persistência de histórico de conversa entre sessões.
- Ações de escrita no Chatwoot (responder conversa, mudar status, atribuir agente) — só leitura e navegação/filtro dentro do próprio dashboard.
- Voz/áudio.

---

## 7 · Impacto em código

- **Novo, isolado:** bloco de HTML/CSS/JS do painel (`#harness-panel`, `#harness-toggle`) + funções `parseHarnessMessage()`, `extractEntities()`, `resolveIntent()`, `executeHarnessIntent()`, `formatHarnessReply()`, `logUnmatchedQuestion()`.
- **Reaproveita sem modificar:** `_teamMap`, `_agentList`, `api()`, `setKpiPeriod`, `setAgentTabPeriod`, `showPage`, `applyInboxAndRender`, `fmtSec`, `agentBadge`, `calcAgentScore`, `getAgentTabRange`/`getAgentMonths`, `trendPrev`/`_chartTrendBase`, `_chartData`/`_agentPerfData`/`_teamCompData`, `_inboxMap`, `INBOX_TEAM_MAP`.
- **Chamadas novas, mas finas (via o mesmo helper `api()`, sem lógica de negócio nova):** algumas perguntas do catálogo (labels, canned responses, "qual inbox recebe mais atendimento") batem em endpoints que hoje nenhuma tela do dashboard usa. São wrappers de leitura simples — o assistente não ganha uma API paralela, só chama o mesmo `api()` para um endpoint que ainda não tinha consumidor.
- **Configurações:** nova seção somando a lista de perguntas não entendidas.
- **Não altera:** nenhuma lógica de cálculo, filtro ou fetch existente — o assistente é uma camada de orquestração por cima do que já existe.
