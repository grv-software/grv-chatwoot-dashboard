# Harness — reconhecimento de linguagem mais flexível — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ampliar as tabelas de aliases do harness (`HARNESS_METRICAS`, `HARNESS_FILA`, `HARNESS_ACOES`) pra aceitar verbos conjugados e frases mais soltas, sem trocar o mecanismo de casamento nem adicionar IA/stemmer.

**Architecture:** Generalizar o truque de raiz curta que o código já usa informalmente (ex.: `'resolvid'` casa com "resolvido"/"resolvida" por ser substring). Cada adição é uma raiz ou frase nova numa lista já existente — nenhuma função nova, nenhum mecanismo novo.

**Tech Stack:** JavaScript vanilla no navegador, mesmo `index.html`.

## Global Constraints

- Nenhuma chamada a modelo de IA, nenhum stemmer genérico — só listas de aliases casadas por substring (`harnessLongestMatch`/`harnessAllMatches` para métrica/fila, `norm.includes(...)` para ação), exatamente como já existe.
- **Regra crítica de `HARNESS_ACOES`:** essa tabela usa "primeira categoria que bater" (não a mais longa) e não tem piso de tamanho mínimo de alias. Nenhuma raiz/palavra nova pode aparecer em mais de uma categoria (`navegar`/`filtrar`/`resumir`), e nenhuma raiz de ação pode ter menos de 4 caracteres.
- Único arquivo tocado: `index.html`. **Nunca** tocar/commitar `san-imob/` nem `docs/superpowers/specs/2026-08-03-soma-imob-design-system-v2.md` — trabalho não commitado de outro projeto (Soma Imob) presente na mesma branch `alteracoes`. Sempre `git commit index.html -m "..."` com pathspec explícito, nunca `-A`/`.`; sempre `git status --short` antes e depois de cada commit.
- Verificação: skill do repo `c:\Users\Samuel Wallace\Documents\vscode\grv-chatwoot-dashboard\.claude\skills\verify\SKILL.md` (dev-server.js + Chrome headless via CDP, GET-only contra produção real). Nunca `taskkill /IM chrome.exe` — matar só o processo que você mesmo subiu, por PID.
- Toda pergunta de teste deste plano usa frases **nunca usadas em nenhum catálogo anterior desta sessão** (nem as 80, nem as 100, nem as de aceite dos planos de carga/sobrecarga) — o objetivo é provar que a raiz nova funciona por si só, não reconfirmar frases que já passavam.

---

### Task 1: `HARNESS_METRICAS` — raízes de volume, resolução, TMR e CSAT

**Files:**
- Modify: `index.html` (bloco `HARNESS_METRICAS`, ~linha 4255-4263)

**Interfaces:**
- Consumes: nada de outras tasks.
- Produces: nada que outras tasks deste plano consomem diretamente — cada task mexe numa tabela independente.

- [ ] **Step 1: Editar as aliases**

Encontre:

```js
const HARNESS_METRICAS = Object.entries({
  volume:    ['volume', 'atendimentos', 'conversas', 'chats'],
  resolucao: ['resolvid', 'resolucao', 'taxa de resolucao', 'taxa'],
  tmr:       ['1a resposta', 'primeira resposta', 'tempo de resposta', 'tmr', 'meta de resposta'],
  tma:       ['tempo de atendimento', 'tempo de resolucao', 'tma', 'tempo pra resolver', 'tempo para resolver'],
  csat:      ['csat', 'satisfacao', 'avaliac', 'nota do cliente', 'estrela'],
  score:     ['pontuacao', 'score', 'nota geral'],
  mensagens: ['mensagens por conversa', 'mensagens']
}).map(([key, aliases]) => ({ key, label: key, aliases }));
```

Substitua por:

```js
const HARNESS_METRICAS = Object.entries({
  volume:    ['volume', 'atendimentos', 'conversas', 'chats', 'atend'],
  resolucao: ['resolv', 'resolucao', 'taxa de resolucao', 'taxa'],
  tmr:       ['1a resposta', 'primeira resposta', 'tempo de resposta', 'tmr', 'meta de resposta', 'respond'],
  tma:       ['tempo de atendimento', 'tempo de resolucao', 'tma', 'tempo pra resolver', 'tempo para resolver'],
  csat:      ['csat', 'satisfacao', 'avali', 'nota do cliente', 'estrela'],
  score:     ['pontuacao', 'score', 'nota geral'],
  mensagens: ['mensagens por conversa', 'mensagens']
}).map(([key, aliases]) => ({ key, label: key, aliases }));
```

(`'resolvid'` some porque `'resolv'` já é substring dela — manter as duas seria redundante.)

- [ ] **Step 2: Verificar ao vivo com um teste que prova a diferença**

Testar só "a pergunta funciona" não prova que a raiz nova é a responsável — o padrão de volume, por exemplo, já cai em `'volume'` por padrão quando não reconhece nenhuma métrica. O teste que prova de verdade é de **duas mensagens em sequência**, usando a memória de conversa do harness (`_harnessMemory.metrica`): a primeira fixa uma métrica diferente, a segunda usa só o verbo conjugado (sem nenhuma palavra já cadastrada antes desta task). Sem a raiz nova, a segunda mensagem falha de dois jeitos possíveis dependendo se ela ainda cita algum outro dado reconhecível (um período, um nome): ou não reconhece nada e cai em "não entendi", ou reconhece o período/nome mas herda a métrica errada da pergunta anterior (porque o verbo sozinho não bastou pra marcar a métrica como citada de propósito). Com a raiz nova, os dois casos se resolvem certo: a métrica muda pra a que a segunda pergunta realmente pediu.

Via a skill `verify`, com o harness aberto, rode em sequência (mesma conversa, não reabrir o harness entre uma e outra):

1. `"Qual o TMR da equipe 1 esse mes?"` (fixa memória em `tmr`) → espere resposta sobre tempo de resposta.
2. `"E quantos ela atendeu?"` → **antes da Step 1 desta task, isso herdaria TMR da memória** (porque "atendeu" não batia em nenhum alias de métrica). Depois da mudança, espere uma resposta sobre **volume** (contagem de atendimentos), não sobre tempo.
3. `"Qual o CSAT do Ageu Carvalho esse mes?"` (fixa memória em `csat`) → espere resposta sobre satisfação.
4. `"E quantos ele resolveu?"` → espere resposta sobre **resolução** (contagem/taxa), não sobre CSAT.
5. `"Como o Ageu Carvalho foi avaliado esse mes?"` → espere resposta sobre **CSAT** (a palavra "avaliado" não batia em `'avaliac'`, só em `'avali'`).
6. `"Ele respondeu rapido esse mes?"` (sem citar "tempo de resposta"/"tmr") → espere resposta sobre **TMR**.

Confirme lendo o texto de cada bolha de resposta — se qualquer uma delas responder sobre a métrica errada (herdada da mensagem anterior em vez da nova), a raiz não pegou; pare e revise antes de seguir.

- [ ] **Step 3: Commit**

```bash
git status --short
git commit index.html -m "feat(harness): raizes de verbo para volume/resolucao/tmr/csat

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 2: `HARNESS_FILA` — "em andamento", "aguardando" solto, "logado"/"conectado"

**Files:**
- Modify: `index.html` (bloco `HARNESS_FILA`, ~linha 4265-4271)

**Interfaces:**
- Consumes: nada.
- Produces: nada consumido por outras tasks.

- [ ] **Step 1: Editar as aliases**

Encontre:

```js
const HARNESS_FILA = Object.entries({
  abertas:       ['abertas agora', 'em aberto agora', 'conversas abertas'],
  pendentes:     ['pendentes', 'pendente'],
  semresposta:   ['sem resposta', 'nao atendidas', 'sem retorno', 'esperando resposta', 'aguardando resposta'],
  naoatribuidas: ['nao atribuida', 'sem atendente', 'sem agente atribuido'],
  online:        ['online agora', 'agentes online', 'quem esta online']
}).map(([key, aliases]) => ({ key, label: key, aliases }));
```

Substitua por:

```js
const HARNESS_FILA = Object.entries({
  abertas:       ['abertas agora', 'em aberto agora', 'conversas abertas', 'em andamento'],
  pendentes:     ['pendentes', 'pendente', 'aguardando'],
  semresposta:   ['sem resposta', 'nao atendidas', 'sem retorno', 'esperando resposta', 'aguardando resposta'],
  naoatribuidas: ['nao atribuida', 'sem atendente', 'sem agente atribuido'],
  online:        ['online agora', 'agentes online', 'quem esta online', 'logado', 'conectado']
}).map(([key, aliases]) => ({ key, label: key, aliases }));
```

- [ ] **Step 2: Verificar ao vivo**

Via a skill `verify`, com o harness aberto:

1. `"Quantas conversas estao em andamento agora?"` → espere a mesma resposta de "abertas" (um número de conversas abertas agora).
2. `"Tem gente aguardando?"` (sem a palavra "resposta") → espere a resposta de **pendentes**, não de "sem resposta" e não "não reconheci".
3. `"Aguardando resposta tem quantas?"` (com a palavra "resposta" desta vez) → confirme que continua caindo em **semresposta** (a frase mais longa precisa continuar vencendo — isso prova que a adição do Step 1 não quebrou o comportamento antigo).
4. `"Quem esta logado agora?"` e `"Quantos agentes estao conectados?"` → espere as duas caindo em **online**, com a contagem de agentes.

- [ ] **Step 3: Commit**

```bash
git status --short
git commit index.html -m "feat(harness): girias de fila (em andamento, aguardando, logado/conectado)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 3: `HARNESS_ACOES` — novas frases de navegar/filtrar/resumir sem colisão

**Files:**
- Modify: `index.html` (bloco `HARNESS_ACOES`, ~linha 4319-4324)

**Interfaces:**
- Consumes: nada.
- Produces: nada consumido por outras tasks. Esta é a tabela mais sensível — o Step 2 inclui verificação de regressão explícita, não só de coisa nova.

- [ ] **Step 1: Editar as aliases**

Encontre:

```js
const HARNESS_ACOES = {
  navegar: ['vai pra', 'va para', 'abre a aba', 'muda pra aba', 'mostra a aba'],
  filtrar: ['mostra so', 'mostra apenas', 'filtra pelo', 'filtra pela', 'filtra por',
            'tira o filtro', 'limpa filtro', 'limpa os filtros', 'limpa todos os filtros', 'volta pra todas', 'remove o filtro'],
  resumir: ['resumo geral', 'resumo', 'como estamos', 'o que mudou']
};
```

Substitua por:

```js
const HARNESS_ACOES = {
  navegar: ['vai pra', 'va para', 'abre a aba', 'muda pra aba', 'mostra a aba',
            'abre', 'bora pra', 'me leva pra', 'quero ver a aba'],
  filtrar: ['mostra so', 'mostra apenas', 'filtra pelo', 'filtra pela', 'filtra por',
            'tira o filtro', 'limpa filtro', 'limpa os filtros', 'limpa todos os filtros', 'volta pra todas', 'remove o filtro',
            'filtr', 'quero ver so', 'fica so com'],
  resumir: ['resumo geral', 'resumo', 'como estamos', 'o que mudou',
            'como anda', 'como ta', 'panorama', 'visao geral', 'me atualiza']
};
```

- [ ] **Step 2: Verificar ao vivo — funcionalidade nova**

Via a skill `verify`, com o harness aberto:

1. `"Abre a analise"` → espere navegar pra aba Análise (confirme visualmente ou via `harnessPaginaAtiva()` que virou `'graficos'`).
2. `"Bora pra aba de agentes"` → espere navegar pra Agentes.
3. `"Fica so com a equipe 3"` → espere filtrar pela equipe 3 (confirme o filtro aplicado, ex. `_teamFilter`/`_agentTabTeamFilter` conforme a aba ativa).
4. `"Quero ver so o SAG"` → espere filtrar pelo SAG.
5. `"Como anda tudo?"` → espere uma resposta de resumo.
6. `"Me atualiza sobre o painel"` → espere uma resposta de resumo.

- [ ] **Step 3: Verificar ao vivo — regressão (nada quebrou)**

Ainda na mesma sessão do harness, confirme que frases antigas continuam caindo na categoria certa (a tabela ganhou palavras novas, isso não pode ter mudado o resultado das frases que já existiam):

1. `"Vai pra Agentes"` → ainda navega pra Agentes.
2. `"Mostra so a equipe 2"` → ainda filtra pela equipe 2 (não pode ter virado "navegar" por causa da palavra nova `'abre'` ou qualquer outra adição).
3. `"Resumo geral"` → ainda cai em resumir.
4. `"Limpa todos os filtros"` → ainda limpa o filtro (esse é o caso que o harness original já teve que corrigir uma vez — confirme que continua funcionando).

Se qualquer um desses 4 tiver mudado de categoria, pare — significa que uma das raízes novas colidiu com uma frase antiga, o que a spec explicitamente exige evitar. Descreva qual frase mudou de comportamento e qual adição do Step 1 causou antes de decidir o que fazer.

- [ ] **Step 4: Commit**

```bash
git status --short
git commit index.html -m "feat(harness): mais frases de navegar/filtrar/resumir, sem colisao entre categorias

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 4: Aceite final combinado

**Files:**
- Modify: `index.html` (só se o aceite achar uma lacuna real)

**Interfaces:**
- Consumes: tudo que as Tasks 1-3 produziram.
- Produces: nenhuma interface nova.

- [ ] **Step 1: Bateria combinada**

Via a skill `verify`, com o harness aberto, rode cada pergunta e confira o critério — todas usam frases que não apareceram em nenhum catálogo nem nas Tasks 1-3 acima:

| Pergunta | Critério |
|---|---|
| `"O time 1 andou atendendo bem esse mes?"` | Resposta sobre volume/desempenho da equipe 1, não "não reconheci" |
| `"Quantas ele resolveu essa semana?"` (depois de uma pergunta anterior fixando outra métrica na memória) | Troca pra resolução, não herda a métrica antiga |
| `"Ninguem ta respondendo direito hoje?"` | Resposta relacionada a TMR (tempo de resposta) |
| `"Tem alguem conectado no sistema agora?"` | Resposta de agentes online |
| `"Bora ver o painel"` | Navega pro Painel |
| `"Fica so com o Ageu Carvalho"` | Filtra pelo agente Ageu Carvalho |
| `"Da um panorama de como ta tudo"` | Resposta de resumo |

- [ ] **Step 2: Corrigir qualquer lacuna real encontrada**

Se alguma pergunta cair em `desconhecido`, travar, ou resolver a categoria/métrica errada, pare e descreva exatamente a mensagem, o que `harnessExtractEntities`/`harnessDetectAcao`/`harnessResolveIntent` resolveram pra ela (avalie direto no console da página), e o que deveria ter acontecido — antes de aplicar o fix mais estreito possível (mais uma raiz pontual, nunca uma reescrita ampla). Depois de corrigir, rode de novo a mesma pergunta que falhou, e rode também uma pergunta de cada Task 1-3 já verificada antes, pra garantir que o fix não quebrou nada.

- [ ] **Step 3: Commit (só se houve fix)**

```bash
git status --short
git commit index.html -m "fix(harness): lacunas do reconhecimento de linguagem achadas na validacao de aceite

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

Se nenhum fix foi necessário, não crie um commit vazio — apenas reporte que o aceite passou de primeira.
