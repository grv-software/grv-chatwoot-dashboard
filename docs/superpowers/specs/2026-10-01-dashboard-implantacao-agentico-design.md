# Dashboard de implantação — visão completa + insights automáticos

## Contexto

O `dashboard-implantacoes.html` hoje cobre só os projetos de Implantação/Reimplantação
**iniciados em 2026**, com dados colados manualmente (pipeline: script Python busca no
CRM nxlite → cola à mão no HTML). Essa base já foi auditada e validada várias vezes
nesta sessão (contagem de atrasados, motivos de atraso lidos na íntegra das anotações,
histórico de pausas).

Pedido: ampliar para um dashboard que "mostre tudo" sobre implantação — todos os
projetos, não só o recorte de 2026 — com progresso interno de cada projeto, e uma
camada "agêntica" de insights automáticos e recomendações de ação, mantendo a
atualização de dados sob controle manual (sem servidor permanente, sem o dashboard
chamando o CRM direto do navegador).

## Fora de escopo

- Qualquer escrita no CRM (PUT/DELETE). Vale a regra permanente: só leitura (GET).
- Outras áreas do CRM (Leads, Chamados, Agenda de consultores) — o pedido confirmado é
  especificamente sobre projetos de implantação.
- Backend/servidor permanente ou atualização automática por agendamento.
- Insights gerados por LLM em texto livre — a camada de insights é 100% regras
  determinísticas.

## Arquitetura

Três peças, sem servidor:

1. **`atualizar_dados.py`** — script que loga no CRM (mesmo padrão de autenticação já
   usado nesta sessão: `POST /api/method/login` com cookie de sessão), busca:
   - Todos os `SAG Projeto` de `tipo_de_projeto` em (Implantação, Reimplantação),
     **sem filtro de data de início** — qualquer ano, qualquer status.
   - Para cada projeto: módulos (`SAG Modulo`, vinculados via campo Link
     `projeto`) e suas anotações completas (histórico integral, não só a última).
   - Aplica a classificação por regras (seção "Motor de insights") e calcula os
     campos derivados (atrasado, dias sem anotação, nº de pausas).
   - Grava tudo em `dashboard_data.js`.
   - Só GET. Se login ou qualquer chamada falhar, aborta **sem sobrescrever** o
     `dashboard_data.js` anterior.

2. **`dashboard_data.js`** — arquivo gerado (nunca editado à mão), formato
   `const DATA = {...};`, incluindo `gerado_em: "<timestamp ISO>"`. Fica na mesma
   pasta do HTML. Usar `<script src>` em vez de `fetch()` de um `.json` evita o
   bloqueio de CORS que acontece ao abrir um `.json` local via `file://`.

3. **`dashboard-implantacoes.html`** — carrega `dashboard_data.js`, mostra
   "Última atualização: dd/mm hh:mm" no topo (lido de `DATA.gerado_em`), e todo o
   motor de insights roda em JS no navegador em cima do `DATA` carregado — não há
   nenhuma lógica de insight no Python além da classificação de motivo (que precisa
   rodar sobre o texto bruto das anotações, então fica no script de atualização).

**Fluxo de atualização:** rodar `python atualizar_dados.py` (ou um `.bat` de
duplo-clique que chama o script) sempre que quiser dados novos, depois recarregar o
HTML no navegador. Não existe botão dentro da página que dispare a busca — isso
exigiria um servidor rodando continuamente, que foi descartado.

## Escopo dos dados e abas

Remove a restrição "iniciado em 2026" do pipeline de dados. As abas atuais mudam
assim:

- **Visão geral** (antes "Visão geral 2026") — mesmos KPIs (atrasados, pausados,
  concluídos no prazo/atrasado, cancelados), agora com um seletor de ano/cohort
  (Todos / 2026 / 2025 / ...) em vez de ano fixo. Default: Todos.
- **Atrasados** (antes "Atrasados atuais") — sem mudança de filtro (já era
  "atrasados agora", independente de ano de início) — ganha a nova coluna de
  progresso e os novos insights.
- **Finalizados** (antes "Finalizados em 2026") — ganha o mesmo seletor de
  ano/cohort da Visão geral.

Não cria aba nova — expande as três existentes, porque os dados passam a ser um
único pipeline consistente (acaba a diferença entre "dado validado manualmente" e
"dado automático").

## Progresso por projeto

Cada projeto passa a carregar:
- `percentual_conclusao` (já existe no doctype `SAG Projeto`).
- Lista de módulos (`SAG Modulo`) com nome e status de cada um.

Exibição: uma barra de progresso compacta na tabela principal (ao lado do nome do
projeto), e a lista completa de módulos dentro do modal de detalhes que já existe
(nova sub-aba "Progresso" ao lado de "Timeline"/"Completo").

## Motor de insights (regras, roda no navegador)

Entrada: `DATA` já teria os campos brutos; as flags abaixo são calculadas em JS a
partir deles (exceto a classificação de motivo, que vem pronta do Python por operar
sobre texto).

| Regra | Condição | Efeito |
|---|---|---|
| Parado sem atualização | Última anotação há 15+ dias corridos | Alerta "parado sem atualização" |
| Atraso crítico | Aberto, `termino_previsto` vencido há mais de 30 dias | Prioridade alta na lista "onde agir primeiro" |
| Pausado/congelado | Anotação com "pausa"/"pausou"/"congelado"/"congelamento" | Contador de pausas + aparece destacado |
| Prazo não informado | `termino_previsto` vazio | Não conta como atrasado nem no prazo — aparece em categoria própria |
| Motivo do atraso | Classificação por palavra-chave sobre o texto das anotações (ex: "aguardando cliente", "sem retorno", "financeiro", "equipe interna") | Se nenhuma regra bate com confiança, marca `motivo: "não identificado — revisar manualmente"` em vez de arriscar um palpite |

O painel "Onde agir primeiro" (hoje só na aba Atrasados, só 2026) passa a cobrir
todos os projetos atrasados, ordenado por: atraso crítico > dias sem atualização >
demais atrasados.

**Limitação assumida conscientemente:** a classificação de motivo/pausa validada
manualmente nesta sessão foi feita lendo o histórico completo com apoio humano +ia
para julgar nuance. A versão automatizada usa palavras-chave e é menos precisa — por
isso projetos sem match de regra ficam marcados para revisão manual em vez de
receber uma classificação forçada e potencialmente errada.

## Tratamento de erro / dado faltante

- Projeto sem `termino_previsto`: categoria "prazo não informado", nunca
  "atrasado" nem "no prazo".
- Projeto sem nenhuma anotação: "sem atualização registrada" em vez de calcular
  dias-sem-atualização (que exigiria uma data base).
- Falha de autenticação ou de qualquer chamada à API durante `atualizar_dados.py`:
  script aborta com mensagem de erro clara, **não sobrescreve** o
  `dashboard_data.js` existente — o dashboard nunca fica com dado quebrado ou
  parcial.

## Teste

- Rodar `atualizar_dados.py` contra o CRM real (somente GET) e comparar as
  contagens agregadas (total de projetos, atrasados, concluídos, pausados) com os
  números já auditados manualmente nesta sessão, como checagem de sanidade antes
  de aceitar o pipeline como confiável.
- Validar o HTML gerado com a mesma rotina já usada nesta sessão: `node --check`
  no JS embutido, simulação de execução via `vm` com stub de `document`, e
  checagem cruzada de todos os `getElementById(...)` contra os `id="..."`
  existentes no HTML.
