# Harness — reconhecimento de linguagem mais flexível (design)

## Contexto

O harness reconhece hoje uma lista fixa de aliases por conceito (métrica, fila, ação, período) e casa por substring contra a mensagem normalizada (`harnessNormalize` + `norm.includes(alias)` ou `harnessLongestMatch`/`harnessAllMatches`). Isso funciona bem quando a pergunta usa uma das formas cadastradas, mas exige que o usuário "acerte" uma delas — verbos conjugados fora da lista, gírias e frases mais soltas podem não bater com nada.

Pedido do usuário: aceitar mais variações de frase **sem decorar o catálogo**, mantendo a arquitetura já decidida (nenhuma IA, só regra/regex contra dados reais). Explicitamente fora desta rodada: tolerância a erro de digitação, expansão do catálogo de perguntas de exemplo, minigráficos/relatórios visuais.

## Princípio

O código já usa esse truque, sem declará-lo: o alias `'resolvid'` (em `HARNESS_METRICAS.resolucao`) casa com "resolvido", "resolvida", "resolvidos", "resolvidas" só por ser uma raiz, não a palavra inteira. Vou generalizar essa técnica de propósito: trocar aliases de palavra-inteira por raízes curtas o suficiente pra cobrir as conjugações comuns de cada verbo do domínio, mas longas o suficiente pra não colidir com nenhuma outra palavra usada no harness. Nenhum mecanismo novo — mesmo casamento por substring de sempre, só mais consistente.

Toda raiz nova deste documento foi conferida manualmente, letra por letra, contra: os aliases dos outros grupos da mesma tabela (`HARNESS_METRICAS`, `HARNESS_FILA` ou `HARNESS_ACOES`), os aliases das outras duas tabelas, e o vocabulário de nomes reais de agentes/equipes. A prova mais importante encontrada: em português, o verbo tem letras que o substantivo correspondente não tem (ex.: "resolv-" só existe nas formas verbais — "resolveu", "resolvido" — nunca em "resolução"/"resolucao", que não tem "v"). Isso é o que torna a raiz curta segura em vez de ambígua.

## Risco identificado e como ele é evitado

`harnessDetectAcao` funciona diferente das outras tabelas: pega a **primeira** categoria (`navegar` → `filtrar` → `resumir`, nessa ordem) cuja lista bater — não a mais longa, como `harnessLongestMatch` faz para métrica/fila/equipe/agente. Isso quer dizer que se a mesma raiz aparecesse em duas categorias de ação, a ordem de checagem decidiria arbitrariamente qual delas "ganha", silenciosamente, sem aviso.

Regra seguida em toda esta spec: **nenhuma raiz/palavra nova pode aparecer em mais de uma categoria de `HARNESS_ACOES`.** Cada adição abaixo foi conferida contra as outras duas categorias antes de entrar na lista.

Além disso, aliases de ação (diferente de métrica/fila) não passam pelo filtro de tamanho mínimo de `harnessLongestMatch` (`a.length >= 3`) — o casamento é `norm.includes(...)` direto, sem piso de tamanho. Por isso nenhuma raiz de ação nesta spec tem menos de 4 caracteres (ex.: `'abre'`, nunca `'ir'` ou `'vê'`), pra não virar substring de palavras completamente sem relação.

## Tabela completa de mudanças

### `HARNESS_METRICAS`

| Métrica | Antes | Depois | Por quê é seguro |
|---|---|---|---|
| `volume` | `'volume', 'atendimentos', 'conversas', 'chats'` | + raiz **`'atend'`** | Cobre atendeu/atende/atendendo/atendido. Aparece também dentro de `tma`'s `'tempo de atendimento'` e de `fila.naoatribuidas`'s `'sem atendente'` — nos dois casos a frase mais longa vence pelo `harnessLongestMatch` (métrica) ou a prioridade de `fila` sobre `metrica` na resolução de intent (fila), então não há regressão. |
| `resolucao` | `'resolvid'`, `'resolucao'`, `'taxa de resolucao'`, `'taxa'` | `'resolvid'` vira raiz **`'resolv'`** | Cobre resolveu/resolve/resolvendo, além do que já cobria. Não colide com "resolução"/"resolucao" (substantivo, sem "v"). |
| `tmr` | `'1a resposta', 'primeira resposta', 'tempo de resposta', 'tmr', 'meta de resposta'` | + raiz **`'respond'`** | Cobre respondeu/responde/respondendo. Não colide com `fila.semresposta` ("resposta" diverge de "respond" logo depois de "respo"). |
| `tma` | `'tempo de atendimento', 'tempo de resolucao', 'tma', 'tempo pra resolver', 'tempo para resolver'` | sem mudança | Já é baseado em frase com "tempo", que é o que distingue duração de contagem — não faz sentido reduzir a uma raiz solta aqui. |
| `csat` | `'csat', 'satisfacao', 'avaliac', 'nota do cliente', 'estrela'` | `'avaliac'` vira raiz **`'avali'`** | Cobre avaliou/avalia/avaliando/avaliado, além de avaliação/avaliações que já cobria. |
| `score` | `'pontuacao', 'score', 'nota geral'` | sem mudança | Não existe uso natural de "pontuar" como verbo neste domínio — forçar uma raiz aqui criaria uma cobertura artificial sem pergunta real correspondente. |
| `mensagens` | `'mensagens por conversa', 'mensagens'` | sem mudança | É uma contagem, não uma ação — não há verbo a conjugar. |

### `HARNESS_FILA`

| Fila | Antes | Depois | Por quê é seguro |
|---|---|---|---|
| `abertas` | `'abertas agora', 'em aberto agora', 'conversas abertas'` | + `'em andamento'` | Termo comum de atendimento em curso; não aparece em nenhum outro grupo. |
| `pendentes` | `'pendentes', 'pendente'` | + **`'aguardando'`** solto (sem exigir "resposta" junto) | `harnessLongestMatch` sempre prefere a frase mais longa: se a mensagem disser "aguardando resposta", `semresposta` (alias de 20 caracteres) ainda vence sobre o `'aguardando'` solto de `pendentes` (10 caracteres). Só ativa quando "aguardando" aparece sem "resposta" do lado — ex. "aguardando atendimento". |
| `semresposta` | `'sem resposta', 'nao atendidas', 'sem retorno', 'esperando resposta', 'aguardando resposta'` | sem mudança | Já cobre as formas de gerúndio comuns ("esperando"/"aguardando" + "resposta"). |
| `naoatribuidas` | `'nao atribuida', 'sem atendente', 'sem agente atribuido'` | sem mudança nesta rodada | Não encontrei uma variação coloquial que eu pudesse confirmar como uso real da equipe sem arriscar inventar uma gíria que ninguém usa — fica para o caderno de perguntas não reconhecidas (Configurações) capturar o que aparecer de verdade. |
| `online` | `'online agora', 'agentes online', 'quem esta online'` | + **`'logado'`**, **`'conectado'`** | Sinônimos operacionais comuns pra "disponível no sistema"; não colidem com nenhum outro grupo. |

### `HARNESS_ACOES`

| Ação | Antes | Depois | Conferência cruzada |
|---|---|---|---|
| `navegar` | `'vai pra', 'va para', 'abre a aba', 'muda pra aba', 'mostra a aba'` | + **`'abre'`** solto, `'bora pra'`, `'me leva pra'`, `'quero ver a aba'` | Nenhuma dessas palavras/raízes aparece em `filtrar` ou `resumir` hoje nem depois das adições abaixo. |
| `filtrar` | `'mostra so', 'mostra apenas', 'filtra pelo', 'filtra pela', 'filtra por', 'tira o filtro', 'limpa filtro', 'limpa os filtros', 'limpa todos os filtros', 'volta pra todas', 'remove o filtro'` | + raiz **`'filtr'`**, `'quero ver so'`, `'fica so com'` | `'filtr'` não aparece em `navegar`/`resumir`. `'quero ver so'` é distinto de `'quero ver a aba'` (navegar) pela ausência de "a aba". |
| `resumir` | `'resumo geral', 'resumo', 'como estamos', 'o que mudou'` | + `'como anda'`, `'como ta'`, `'panorama'`, `'visao geral'`, `'me atualiza'` | Nenhuma dessas palavras aparece em `navegar`/`filtrar`. |

## Testando

Cada raiz/frase nova entra numa bateria de perguntas **nunca usadas em nenhum catálogo anterior desta sessão** (nem as 80, nem as 100, nem as de aceite das tasks passadas) — frases inventadas na hora, com verbos conjugados fora do padrão, pra provar que a raiz funciona sem depender de uma forma específica já testada. Verificação ao vivo via a skill `verify`, mesmo padrão de sempre.

## Fora de escopo

Tolerância a erro de digitação, expansão do catálogo de perguntas, minigráficos/relatórios visuais no chat, stemmer genérico de português. `fila.naoatribuidas` fica sem adição coloquial nesta rodada — depende do caderno de perguntas não reconhecidas (`Configurações`) mostrar o que a equipe realmente tenta perguntar antes de eu inventar um termo que pode não corresponder ao uso real.
