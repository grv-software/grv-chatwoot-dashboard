exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: JSON.stringify({ error: 'Method not allowed' }) };
  }
  try {
    const { password } = JSON.parse(event.body || '{}');
    const expected = process.env.SETTINGS_PASSWORD;
    if (!expected) {
      return { statusCode: 503, body: JSON.stringify({ error: 'Not configured' }) };
    }
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ ok: password === expected }),
    };
  } catch {
    return { statusCode: 400, body: 'Bad request' };
  }
};
