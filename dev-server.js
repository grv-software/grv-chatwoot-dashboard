const http  = require('http');
const https = require('https');
const fs    = require('fs');
const path  = require('path');

const PORT   = 8888;
const TARGET = 'nxticket.com.br';

const MIME = { '.html':'text/html', '.js':'application/javascript', '.css':'text/css',
               '.json':'application/json', '.png':'image/png', '.svg':'image/svg+xml' };

http.createServer((req, res) => {
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
