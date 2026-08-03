// ============================================================
// config.js — Configuração global de conexão com a API.
// Carregado antes do <script> de cada página (index.html, imoveis.html,
// clientes.html, atendimento.html). É o único arquivo JS/CSS
// compartilhado entre as telas — todo o resto continua autocontido.
// ============================================================

const API_BASE = 'http://localhost:8000/api';
const IMOBILIARIA_ID = '00000000-0000-0000-0000-000000000001'; // Imobiliária Valinhos (seed.sql) — mock fixo no MVP, sem autenticação real ainda

const API_HEADERS = {
  'Content-Type': 'application/json',
  'X-Imobiliaria-Id': IMOBILIARIA_ID
};

// Helper genérico de fetch com timeout — usado por todas as páginas
// pra não repetir try/catch e AbortController em cada uma.
// Lança o erro (não engole) — quem chama decide o que fazer (mostrar
// banner, manter mock, etc).
//
// Timeout em 30s, não 8s: /chat faz até duas chamadas reais e
// sequenciais à Anthropic (classificador + resposta principal), e uma
// pergunta roteada pro Sonnet com contexto completo pode passar de
// 10-15s sozinha. Com 8s, toda chamada ao Sonnet era abortada pelo
// próprio frontend antes do backend terminar — descoberto testando de
// verdade pelo navegador (o servidor respondia certo, mas tarde
// demais pro timeout antigo).
async function apiFetch(caminho, opcoes = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000);

  try {
    const resposta = await fetch(API_BASE + caminho, {
      headers: API_HEADERS,
      signal: controller.signal,
      ...opcoes
    });
    clearTimeout(timeoutId);

    if (!resposta.ok) {
      const erro = new Error(`Erro ${resposta.status} em ${caminho}`);
      erro.status = resposta.status;
      throw erro;
    }
    return await resposta.json();
  } catch (erro) {
    clearTimeout(timeoutId);
    throw erro;
  }
}
