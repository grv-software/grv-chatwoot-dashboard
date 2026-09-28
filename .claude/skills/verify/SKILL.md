---
name: verify
description: Sobe o GRV SAC Dashboard e o dirige por CDP (Chrome headless) para observar mudanças em runtime. Use ao verificar qualquer alteração em index.html.
---

# Verificar o GRV SAC Dashboard

App de arquivo único (`index.html`, ~4000 linhas) servido por `dev-server.js`,
que faz proxy de `/api/*` para **nxticket.com.br (produção)**.

> ⚠️ O proxy aponta para a instância real do cliente. Use **somente GET**.
> Nunca dirija fluxos que criem/alterem conversas, contatos ou configurações.

## Subir

```bash
node dev-server.js &                      # porta 8888
curl -sf http://localhost:8888/index.html -o /dev/null && echo UP
```

Chrome headless isolado (porta CDP própria, perfil próprio — não colida com o
Chrome do usuário):

```bash
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --headless=new --disable-gpu --no-sandbox \
  --remote-debugging-port=9333 --user-data-dir="$SCRATCH/cp-verify" about:blank &
```

Não existe `chromium-cli`, `playwright` nem `puppeteer` na máquina. O driver é
CDP puro com `fetch` + `WebSocket` nativos do Node (24+). Veja
`drive.js` no scratchpad da sessão — `newTab` / `connect` / `ev` / `shot`.

## Autenticar

O dashboard lê o token do `localStorage` **na carga**. Semeie e recarregue:

```js
localStorage.setItem('grv_token','<token admin>');
localStorage.setItem('grv_account','1');
location.reload();
```

Sem isso o app abre o modal de token e nada renderiza.

## Dirigir

Navegação é por clique no rótulo da sidebar (`Painel` / `Agentes` / `Análise`):

```js
[...document.querySelectorAll('*')]
  .filter(x => x.textContent.trim()==='Análise' && !x.children.length)[0].click()
```

**Espere os dados, não durma um tempo fixo.** A aba Análise dispara 6 meses ×
~15 inboxes de `reports/summary` e leva **20–30s**. A aba Agentes busca 63
agentes. Faça poll de `_charts.vol.data.labels.length` / do sumiço do texto
"Carregando".

## Armadilhas

- **`window._charts` é `undefined`.** As globais são `let` de topo de script,
  que não viram propriedade de `window`. Avalie o nome cru: `_charts`,
  `_rawConvs`, `_chartData`, `_totalOpen`, `_chartTeamFilter`.
- **Existem 3 botões com texto "Aplicar"** (filtro de agente `#agp`, período
  personalizado `#agdr`, filtro de equipe `#ibp`). `querySelectorAll('button')`
  + `find(texto==='Aplicar')` pega o errado e falha em silêncio. Mire no
  container: `#ibp .ibp-ok`.
- **O filtro "CAIXAS"/"EQUIPES" filtra por _time_, não por inbox.** As opções
  vêm de `_teamMap`. O inbox SAG (17) não é um time e nunca aparece lá.
- O auto-refresh (`REFRESH_SEC`) dispara `fetchAll()` durante os `sleep` e
  muda contagens ao vivo entre um passo e outro — diferenças de ±2 conversas
  são drift real, não bug.

## Fluxos que valem dirigir

| Mudou | Dirija |
|---|---|
| Aba Análise | Sidebar → Análise; espere os charts; leia `_charts.<id>.data` |
| Filtro de equipe | `#chart-inbox-trigger` → marque caixa → `#ibp .ibp-ok` |
| Cards "Ao vivo" | Compare com a API crua no mesmo tick (busque `/api/v1/.../conversations` de dentro da página) |
| Aba Agentes | Sidebar → Agentes; `Ver perfil →` abre o modal; aba CSAT |
| Estado raro (truncamento, lista vazia) | Mute a global, chame `renderCharts()`, restaure depois |

## Conferir contra a verdade

O padrão mais forte aqui é comparar o que o chart mostra com a API crua,
buscada de dentro da própria página no mesmo instante:

```js
const h = { api_access_token: '<token>' };
const inb = await fetch('/api/v1/accounts/1/inboxes', { headers: h }).then(r => r.json());
// …pagine /conversations?status=open e compare com _charts.status.data.datasets[0].data
```
