// Uso: node tests/verify_dashboard_html.js dashboard-implantacoes.html
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const os = require('os');
const { execFileSync } = require('child_process');

const htmlPath = process.argv[2];
if (!htmlPath) {
  console.error('uso: node verify_dashboard_html.js <arquivo.html>');
  process.exit(1);
}
const html = fs.readFileSync(htmlPath, 'utf8');

const blocos = [...html.matchAll(/<script(?:\s+src="([^"]+)")?[^>]*>([\s\S]*?)<\/script>/g)];
const inline = blocos.filter(m => !m[1]).map(m => m[2]);
const srcs = blocos.filter(m => m[1]).map(m => m[1]);
if (inline.length === 0) {
  console.error('ERRO: nenhum <script> inline encontrado');
  process.exit(1);
}
const codigoInline = inline.join('\n;\n');

const tmpFile = path.join(os.tmpdir(), 'verify_dashboard_inline.js');
fs.writeFileSync(tmpFile, codigoInline);
execFileSync(process.execPath, ['--check', tmpFile]);
console.log('OK: sintaxe do script inline valida');

const baseDir = path.dirname(htmlPath);
const codigoSrc = srcs.map(src => fs.readFileSync(path.join(baseDir, src), 'utf8')).join('\n;\n');

const idsHtml = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]));

function elementoFalso() {
  const el = {
    _value: '',
    classList: {
      _set: new Set(),
      add(...c) { c.forEach(x => this._set.add(x)); },
      remove(...c) { c.forEach(x => this._set.delete(x)); },
      toggle(c) { this._set.has(c) ? this._set.delete(c) : this._set.add(c); },
      contains(c) { return this._set.has(c); },
    },
    style: {},
    dataset: {},
    children: [],
    textContent: '',
    _innerHTML: '',
    get innerHTML() { return this._innerHTML; },
    set innerHTML(html) {
      this._innerHTML = html;
      // nao faz parsing real de HTML; so garante que lastElementChild/firstChild
      // apontem para algo utilizavel em vez de null, para o script poder
      // continuar anexando elementos (ex: botao) depois de setar innerHTML.
      this.children = html ? [elementoFalso()] : [];
    },
    get value() { return this._value; },
    set value(v) { this._value = v; },
    appendChild(child) { this.children.push(child); return child; },
    insertBefore(child) { this.children.unshift(child); return child; },
    addEventListener() {},
    removeEventListener() {},
    closest() { return null; },
    querySelectorAll() { return []; },
    querySelector() { return null; },
    scrollIntoView() {},
    remove() {},
    get lastElementChild() { return this.children[this.children.length - 1] || null; },
    get firstChild() { return this.children[0] || null; },
  };
  return el;
}

const elementosPorId = new Map();
const documentStub = {
  getElementById(id) {
    if (!elementosPorId.has(id)) elementosPorId.set(id, elementoFalso());
    return elementosPorId.get(id);
  },
  querySelectorAll() { return []; },
  querySelector() { return null; },
  createElement() { return elementoFalso(); },
  addEventListener() {},
};

const contexto = vm.createContext({
  document: documentStub,
  window: {},
  console,
  Math, JSON, Object, Array, Set, Infinity, Date,
});

vm.runInContext(codigoSrc + '\n;\n' + codigoInline, contexto, { filename: 'dashboard-inline.js' });
console.log('OK: execucao simulada nao lancou erro');

const idsReferenciados = new Set([...codigoInline.matchAll(/getElementById\('([^']+)'\)/g)].map(m => m[1]));
const faltando = [...idsReferenciados].filter(id => !idsHtml.has(id));
if (faltando.length) {
  console.error('ERRO: ids referenciados no JS mas ausentes no HTML:', faltando);
  process.exit(1);
}
console.log('OK: todos os ' + idsReferenciados.size + ' ids referenciados existem no HTML');
