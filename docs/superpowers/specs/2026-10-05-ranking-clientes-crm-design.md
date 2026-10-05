# Ranking de clientes por conversas abertas (aba Análise) — design

## Contexto

Durante esta sessão, analisamos manualmente (consultando direto o CRM Frappe em `crm.nxlite.com.br`) quais clientes mais abrem conversas no Chatwoot, e os motivos recorrentes de abertura pra alguns deles (CAMPOSCAL, APTAR MARINGA, POÇOSTEC, FERUSI). O usuário quer esse ranking **dentro do dashboard**, na aba Análise, no mesmo formato de tabela já usado no chat — não mais uma consulta manual pontual.

Essa é a **primeira integração do dashboard com o Frappe/CRM NX** — até agora o `index.html` só fala com a API do Chatwoot.

## Decisões já aprovadas

1. **A chave de API do Frappe fica só no servidor**, nunca chega no navegador. Diferente do token do Chatwoot hoje (que é público, lido do Supabase e usado direto pelo navegador) — essa chave toca dado de cliente, e o volume de dados (~19 mil conversas só nos últimos 90 dias) tornaria inviável mandar tudo bruto pro navegador de qualquer forma. Uma Netlify Function nova recebe o período, busca e agrega no servidor, devolve só o ranking pronto.
2. **Reaproveita o seletor de período que a aba Análise já tem** (`#chart-period-sel`, hoje com opções de 1/3/6/12 meses) — não cria um segundo seletor. O card usa o intervalo completo do período selecionado (do primeiro mês ao último, não só o mês mais recente).
3. **"Sem cliente vinculado" aparece como uma linha separada**, no fim da tabela, com uma nota explicando o que é — não é escondido nem descartado.

**Credencial:** já emitida (API Key + Secret de um usuário dedicado, leitura apenas em `Cliente Conversa`) e verificada ao vivo contra a API real antes de escrever este documento.

## Arquitetura

### Netlify Function nova: `netlify/functions/clientes-ranking.js`

- Lê `FRAPPE_API_KEY` e `FRAPPE_API_SECRET` das variáveis de ambiente do Netlify (nunca em código, nunca expostas ao navegador).
- Recebe `since`/`until` (unix segundos, mesmo formato que o resto do app já usa) via query string.
- Converte para o formato de data do Frappe (`YYYY-MM-DD HH:MM:SS`) e pagina `GET /api/resource/Cliente Conversa` (autenticação `Authorization: token <key>:<secret>`), campos `["cliente","cliente_nome"]`, filtro `criacao_conversa` entre `since` e `until`, páginas de 5.000 registros (Frappe aceita páginas grandes, diferente do Chatwoot que trava em 25).
- Agrega por `cliente` no próprio servidor (contagem + nome), ordena desc, devolve os top 15 + a contagem de "sem cliente" (registros com `cliente` nulo).
- **Teto de página:** 20 páginas (100.000 registros — folga generosa sobre o pior caso medido, ~77 mil em 12 meses). Se estourar, devolve `truncado: true` e o ranking parcial, mesmo padrão de aviso já usado no fix de paginação do CSAT e no ranking do SAG.
- **Contrato de resposta:**
  ```json
  {
    "periodo": { "since": 1234567890, "until": 1234567890 },
    "clientes": [{ "cliente": "CLI00644", "nome": "MEXIS INDUSTRIA MECANICA DO BRASIL LTDA", "total": 423 }],
    "semCliente": 8475,
    "truncado": false
  }
  ```
- Se as variáveis de ambiente não estiverem configuradas (a chave ainda pode não ter chegado no Netlify quando isso for implementado), devolve `503` com uma mensagem clara — o card trata isso mostrando "Integração com o CRM ainda não configurada", nunca falha silenciosamente.

### Roteamento

- `netlify.toml` ganha um redirect novo: `/api/clientes-ranking` → `/.netlify/functions/clientes-ranking` (mesmo padrão já usado por `/api/config` e `/api/auth-settings`).
- `dev-server.js` ganha uma rota local equivalente, pra poder testar isso de verdade via a skill `verify` antes de publicar — lendo a mesma chave de uma variável de ambiente local.

## Onde entra na tela

Um card novo na aba Análise, no mesmo estilo visual dos `.chart-card` que já existem (mesmo radius, padding, skeleton de carregamento `.chart-skel-card` enquanto busca). Título: "Clientes que mais abriram conversas". Abaixo do título, a legenda do período atual (reaproveitando o texto que os outros cards já mostram, tipo "Jul/26 a Set/26").

Tabela: posição, nome do cliente, quantidade de conversas. Linha final, visualmente discreta (cor `--text3`, sem destaque): "Sem cliente vinculado — N conversas", com um `title` explicando que são conversas no Chatwoot sem cadastro de cliente correspondente no CRM.

Cache de 5 minutos no navegador por período (mesmo padrão TTL do `_chartTeamCache` que já existe), pra não rebuscar a cada pequena interação na aba.

## Fora de escopo

- Qualquer tela/filtro novo de período — reaproveita o que já existe.
- Drill-down pra ver os motivos de abertura de um cliente específico direto da tela (isso foi feito manualmente nesta sessão lendo threads inteiras — não dá pra automatizar com confiança nesta rodada; fica pra uma iteração futura, se fizer sentido).
- Qualquer escrita no Frappe — só leitura, em todo o fluxo.
