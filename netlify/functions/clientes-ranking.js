const { buildRanking } = require('../../lib/clientes-ranking-core');

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Content-Type': 'application/json',
};

exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 204,
      headers: { ...CORS, 'Access-Control-Allow-Methods': 'GET,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' },
      body: '',
    };
  }

  const apiKey    = process.env.FRAPPE_API_KEY;
  const apiSecret = process.env.FRAPPE_API_SECRET;
  if (!apiKey || !apiSecret) {
    return { statusCode: 503, headers: CORS, body: JSON.stringify({ error: 'Frappe not configured' }) };
  }

  const since = parseInt(event.queryStringParameters?.since, 10);
  const until = parseInt(event.queryStringParameters?.until, 10);
  if (!since || !until) {
    return { statusCode: 400, headers: CORS, body: JSON.stringify({ error: 'since/until obrigatorios' }) };
  }

  try {
    const result = await buildRanking({ since, until, apiKey, apiSecret });
    return { statusCode: 200, headers: CORS, body: JSON.stringify(result) };
  } catch (e) {
    return { statusCode: 502, headers: CORS, body: JSON.stringify({ error: e.message }) };
  }
};
