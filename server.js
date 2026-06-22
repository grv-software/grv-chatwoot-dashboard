const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = 8765;
const TARGET = 'nxticket.com.br';
const DIR = __dirname;
const SETTINGS_PASSWORD = 'Grv@h9';

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.ico': 'image/x-icon' };

http.createServer((req, res) => {
  // Autenticação de configurações
  if (req.url === '/api/auth-settings' && req.method !== 'POST') {
    res.writeHead(405, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Method not allowed' }));
    return;
  }
  if (req.method === 'POST' && req.url === '/api/auth-settings') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const { password } = JSON.parse(body);
        const ok = password === SETTINGS_PASSWORD;
        res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ ok }));
      } catch {
        res.writeHead(400);
        res.end('Bad request');
      }
    });
    return;
  }

  if (req.url.startsWith('/api/')) {
    // Proxy para nxticket.com.br — repassa token enviado pelo browser
    const fwd = {};
    if (req.headers['api_access_token']) fwd['api_access_token'] = req.headers['api_access_token'];
    const opts = {
      hostname: TARGET,
      path: req.url,
      method: req.method,
      headers: { 'Accept': 'application/json', ...fwd }
    };
    const proxy = https.request(opts, r => {
      res.writeHead(r.statusCode, { 'Content-Type': r.headers['content-type'] || 'application/json', 'Access-Control-Allow-Origin': '*' });
      r.pipe(res);
    });
    proxy.on('error', e => { res.writeHead(502); res.end(e.message); });
    proxy.end();
  } else {
    // Arquivos estáticos
    const filePath = path.join(DIR, req.url === '/' ? 'index.html' : req.url);
    if (!filePath.startsWith(DIR + path.sep) && filePath !== path.join(DIR, 'index.html')) {
      res.writeHead(403); res.end('Forbidden'); return;
    }
    fs.readFile(filePath, (err, data) => {
      if (err) { res.writeHead(404); res.end('Not found'); return; }
      const ext = path.extname(filePath);
      res.writeHead(200, { 'Content-Type': (MIME[ext] || 'text/plain') + '; charset=utf-8' });
      res.end(data);
    });
  }
}).listen(PORT, () => {
  console.log(`\n  GRV SAC Dashboard → http://localhost:${PORT}\n  Ctrl+C para parar.\n`);
});
