const http  = require('http');
const https = require('https');
const fs    = require('fs');
const path  = require('path');
const { buildRanking } = require('./lib/clientes-ranking-core');

const PORT   = 8888;
const TARGET = 'nxticket.com.br';

const MIME = { '.html':'text/html', '.js':'application/javascript', '.css':'text/css',
               '.json':'application/json', '.png':'image/png', '.svg':'image/svg+xml' };

http.createServer((req, res) => {
  /* ranking de clientes (Frappe) — nao e proxy, resolve local */
  if (req.url.startsWith('/api/clientes-ranking')) {
    const u = new URL(req.url, 'http://localhost');
    const since = parseInt(u.searchParams.get('since'), 10);
    const until = parseInt(u.searchParams.get('until'), 10);
    const apiKey    = process.env.FRAPPE_API_KEY;
    const apiSecret = process.env.FRAPPE_API_SECRET;
    if (!apiKey || !apiSecret) {
      res.writeHead(503, { 'content-type': 'application/json', 'access-control-allow-origin': '*' });
      res.end(JSON.stringify({ error: 'Frappe not configured' }));
      return;
    }
    if (!since || !until) {
      res.writeHead(400, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ error: 'since/until obrigatorios' }));
      return;
    }
    buildRanking({ since, until, apiKey, apiSecret })
      .then(result => {
        res.writeHead(200, { 'content-type': 'application/json', 'access-control-allow-origin': '*' });
        res.end(JSON.stringify(result));
      })
      .catch(err => {
        res.writeHead(502, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      });
    return;
  }

  /* proxy /api/* → nxticket.com.br/api/* */
  if (req.url.startsWith('/api/')) {
    const opts = {
      hostname: TARGET,
      path: req.url,           /* /api/v1/... já é o path correto */
      method: req.method,
      headers: { ...req.headers, host: TARGET }
    };
    const proxy = https.request(opts, pr => {
      res.writeHead(pr.statusCode, { ...pr.headers, 'access-control-allow-origin': '*' });
      pr.pipe(res, { end: true });
    });
    proxy.on('error', e => { res.writeHead(502); res.end(e.message); });
    req.pipe(proxy, { end: true });
    return;
  }

  /* arquivos estáticos */
  const file = req.url === '/' ? '/index.html' : req.url;
  const full = path.join(__dirname, file);
  fs.readFile(full, (err, data) => {
    if (err) { res.writeHead(404); res.end('Not found'); return; }
    const ext = path.extname(full);
    res.writeHead(200, { 'content-type': MIME[ext] || 'text/plain' });
    res.end(data);
  });
}).listen(PORT, () => console.log(`Dev server: http://localhost:${PORT}`));
