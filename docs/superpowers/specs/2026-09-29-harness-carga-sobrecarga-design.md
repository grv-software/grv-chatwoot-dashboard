# Harness — carga ao vivo, sobrecarga e ranking por equipe (design)

## Contexto

O assistente "harness" (spec `2026-09-28-assistente-chat-design.md`, plano `2026-09-28-assistente-chat.md`) já responde perguntas sobre volume, TMR, TMA, resolução, CSAT, pontuação, ranking global (agente vs agente, equipe vs equipe), fila ao vivo da conta inteira e navegação/filtro — tudo sem chamada a IA, por casamento de padrão contra dados reais.

Ao preparar um catálogo de 100 novas perguntas de treino com nomes reais da equipe, identificamos 4 lacunas reais que o harness atual não cobre:

1. Carga ao vivo de um agente ou equipe específica ("quantos atendimentos o Fulano tem agora").
2. Detecção de sobrecarga ("quem está sobrecarregado", "qual time está sobrecarregado/mais tranquilo").
3. Ranking restrito a uma equipe ("quem da equipe 2 atendeu mais/menos/tem pior CSAT").
4. Recorte por inbox específico cruzado com agente ("dentro do SAG, qual agente mais atende").

Este documento desenha as 4 capacidades. Nenhuma chamada a modelo de IA — mesma arquitetura de extração de entidades + resolução de intent do harness já implementado.

## Decisões de produto (aprovadas antes deste desenho)

- **Sobrecarga é relativa à média do time**, não um limiar fixo: um agente é "sobrecarregado" quando sua carga ao vivo é ≥ 1,5x a média do próprio time. Time "sobrecarregado"/"mais tranquilo" é o que tem a maior/menor média de carga por agente entre os times reais.
- **O recorte por inbox (SAG) cobre ao vivo E histórico por período**, não só o instante presente — confirmado como viável (ver §5).

## 1. Carga ao vivo por agente/equipe

**Fonte de dados:** `_rawConvs` (conversas abertas) + `_pendingConvs` (pendentes), os mesmos dois arrays globais que já alimentam o card "Fila Atual" da aba Análise. Cada conversa tem `meta.assignee.id`/`.name` e `inbox_id`. **Zero chamada nova à API** — a carga ao vivo é sempre uma contagem em memória do que o dashboard já buscou ao carregar.

```js
function harnessCargaAoVivo() {
  const porAgente = {}; // { agentId: { nome, valor } }
  for (const c of [..._rawConvs, ..._pendingConvs]) {
    const a = c.meta?.assignee;
    if (!a) continue;
    porAgente[a.id] = { nome: a.name, valor: (porAgente[a.id]?.valor || 0) + 1 };
  }
  return porAgente;
}
```

**Perguntas cobertas:** "quantos atendimentos o Fulano está fazendo agora", "quantas conversas a equipe X tem em aberto neste momento", "quem tem mais/menos conversas abertas agora".

## 2. Detecção de sobrecarga

**Mapeamento agente → equipe:** não existe hoje em memória (`_teamMap` só guarda `{id, name}`, sem membros). Busco `team_members` das 4 equipes reais (não o SAG — ele não tem roster fixo, fica de fora dessa comparação) via `harnessTeamMemberIds`, função que já existe, uma vez por pergunta de sobrecarga — 4 chamadas paralelas, rápido.

**Regra:**
```
mediaTime[equipe] = somatório da carga ao vivo dos membros da equipe / nº de membros da equipe
agente sobrecarregado ⟺ cargaAgente ≥ 1.5 × mediaTime[equipe do agente]
                         E mediaTime[equipe do agente] > 0   (guarda técnica — ver nota abaixo)
```

> **Nota de implementação:** a guarda `mediaTime > 0` não é uma segunda régua além da escolhida — é só para evitar o caso degenerado em que a média de um time é 0 (ninguém com conversa aberta) e qualquer agente com 1 conversa "sobrecarregaria" por comparação com zero. Sem isso o resultado seria tecnicamente correto pela fórmula mas sem sentido prático.

**Escopos de pergunta:**
- "Quem está sobrecarregado?" (sem nome) → varre todos os agentes com carga > 0, aponta o(s) que passam do limiar, ordenado pelo maior múltiplo da própria média.
- "O Fulano está sobrecarregado?" (agente citado) → resposta direta sim/não com os números.
- "Qual time está sobrecarregado?" / "qual está mais tranquilo?" → ordena `mediaTime` entre os times reais (SAG fora), maior = sobrecarregado, menor = tranquilo.
- "A equipe 2 está sobrecarregada?" (equipe citada) → compara a média dela com a média das outras equipes, resposta direta.

Direção ("sobrecarregado" vs "tranquilo"/"folgado") decidida por regex simples, mesmo padrão de `harnessDirecaoRanking`.

## 3. Ranking restrito a uma equipe

Reaproveita quase todo o código de ranking que já existe. Hoje `harnessResolveIntent` só entra no ramo de ranking por agente quando a pergunta **não** cita nenhuma equipe/agente (`!teams.length && !agents.length`). Adiciono um ramo antes desse, checado quando a pergunta cita **exatamente uma** equipe e tem cara de ranking ("quem da equipe 2 atendeu mais"):

```js
if (teams.length === 1 && !agents.length && harnessIsRanking(norm)) {
  return { tipo: 'ranking', escopo: 'agente', equipe: teams[0],
           metrica: metrica?.key || 'volume', direcao: harnessDirecaoRanking(norm), periodo };
}
```

Em `harnessResponderRanking`, quando `intent.equipe` existe e **não** é o SAG, a lista de candidatos deixa de ser `_agentList` inteira e passa a ser só os membros daquele time (`harnessTeamMemberIds`, já existe). O resto — busca de valor por agente, ordenação por direção/polaridade da métrica — é o código de hoje, sem mudança. Funciona para volume, TMR, TMA, resolução e CSAT, exatamente como o ranking global já cobre.

Quando `intent.equipe.key === SAG_FILTER_ID`, o caminho é outro — descrito a seguir.

## 4/5. Recorte SAG por agente (ao vivo + histórico)

"Dentro do SAG, qual agente mais atende" cai no mesmo ramo de ranking-por-equipe do item 3 (o SAG já existe como pseudo-equipe de id `-17` no harness), mas como o SAG não tem `team_members`, a fonte de dado é diferente:

- **Se o período resolvido cobre só o instante presente** (isto é, a pergunta não citou nada além do live) — na prática isso não existe como período próprio hoje (o mais próximo é "hoje"), então **todo recorte do SAG usa o mesmo caminho histórico abaixo**, inclusive para "hoje". Mantém uma única forma de calcular, mais fácil de manter.
- **Caminho histórico:** pagino `/v1/accounts/{id}/conversations?inbox_id=17&status=all&assignee_type=all&sort_by=created_at&page=N` (só GET), que devolve mais novo → mais antigo. Paro assim que uma página traz conversa com `created_at` anterior ao início do período. Conto por `meta.assignee.id`.

**Medido ao vivo antes de fechar este desenho** (2026-09-29, GET real contra a instância de produção): o mês corrente inteiro do inbox SAG são **1.810 conversas em 73 páginas** de 25. Um teto de **150 páginas** (~3.750 conversas, o dobro de folga) cobre tranquilamente qualquer pergunta de "este mês" ou "hoje"; períodos maiores ("trimestre", "6 meses") podem estourar o teto — nesse caso a resposta inclui um aviso de que o dado pode estar incompleto, mesmo padrão de aviso já usado no fix de paginação do CSAT.

Busca em lotes paralelos (8 páginas por vez), não sequencial — mesmo padrão do `fetchCsatAll` batelado desta sessão.

**Só cobre volume.** TMR/TMA/CSAT recortados por inbox exigiriam abrir cada conversa individualmente para ler tempos/nota — caro demais para uma resposta de chat. Se pedirem isso ("qual o TMR do SAG por agente"), o harness responde que esse recorte só existe para quantidade de atendimentos, sugerindo perguntar por equipe ou agente sem o recorte de inbox.

## Prioridade na cadeia de intents

A ordem de resolução ganha um novo intent, encaixado entre `filtrar` e `fila` (é um live-lookup, mas por agente/equipe específico, não da conta inteira):

```
navegar > filtrar > carga (novo) > fila > resumir > comparar/ranking > metrica > desconhecido
```

Detecção de `carga`: keyword live (`agora`, `neste momento`, `no momento`, `nesse momento`) + agente/equipe citado, OU qualquer palavra de sobrecarga (`sobrecarregad`, `tranquil[oa]`, `afogad`, `precisa de (ajuda|reforço)`) — essa última dispensa a keyword live, porque perguntar se alguém "está sobrecarregado" já é inerentemente sobre agora.

Isso precisa vir antes do fallback para `metrica`: sem essa checagem, "quantos atendimentos o Fulano tem agora" seria capturado pelo ramo de métrica (volume) e responderia o total do mês corrente, não a contagem ao vivo.

## Fora de escopo

- TMR/TMA/CSAT recortados por inbox específico (§4/5).
- Sobrecarga comparando o SAG com os times reais (SAG não tem roster fixo para calcular uma "média por membro").
- Qualquer forma de alerta/notificação proativa de sobrecarga — o harness só responde quando perguntado, não monitora e avisa sozinho.
