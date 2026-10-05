const FRAPPE_BASE = 'https://crm.nxlite.com.br';
const PAGE_SIZE = 5000;
const MAX_PAGES = 20;

function fmtFrappeDate(unixSeconds) {
  const d = new Date(unixSeconds * 1000);
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

async function buildRanking({ since, until, apiKey, apiSecret }) {
  const sinceFmt = fmtFrappeDate(since);
  const untilFmt = fmtFrappeDate(until);
  const headers = { Authorization: `token ${apiKey}:${apiSecret}` };

  const contagem = {};
  let semCliente = 0;
  let truncado = false;

  for (let page = 0; page < MAX_PAGES; page++) {
    const url = new URL(`${FRAPPE_BASE}/api/resource/Cliente Conversa`);
    url.searchParams.set('fields', JSON.stringify(['cliente', 'cliente_nome']));
    url.searchParams.set('filters', JSON.stringify([
      ['criacao_conversa', '>=', sinceFmt],
      ['criacao_conversa', '<=', untilFmt]
    ]));
    url.searchParams.set('limit_start', String(page * PAGE_SIZE));
    url.searchParams.set('limit_page_length', String(PAGE_SIZE));

    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`Frappe HTTP ${res.status}`);
    const json = await res.json();
    const rows = json.data || [];
    if (!rows.length) break;

    for (const row of rows) {
      if (!row.cliente) { semCliente++; continue; }
      if (!contagem[row.cliente]) contagem[row.cliente] = { nome: row.cliente_nome || row.cliente, total: 0 };
      contagem[row.cliente].total++;
    }

    if (rows.length < PAGE_SIZE) break;
    if (page === MAX_PAGES - 1) truncado = true;
  }

  const clientes = Object.entries(contagem)
    .map(([cliente, v]) => ({ cliente, nome: v.nome, total: v.total }))
    .sort((a, b) => b.total - a.total)
    .slice(0, 15);

  return { periodo: { since, until }, clientes, semCliente, truncado };
}

module.exports = { buildRanking, fmtFrappeDate };
