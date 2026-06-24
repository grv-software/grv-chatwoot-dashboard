const ALLOWED = ['token','account','sla_tma','sla_tmr','sla_fcr','sla_msg',
                 'threshold','refresh_sec','weight_tma','weight_tmr','weight_fcr',
                 'weight_msg','weight_csat'];

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Content-Type': 'application/json',
};

exports.handler = async (event) => {
  const SUPABASE_URL = process.env.SUPABASE_URL;
  const SERVICE_KEY  = process.env.SUPABASE_SERVICE_KEY;

  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 204,
      headers: {
        ...CORS,
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
      body: '',
    };
  }

  if (!SUPABASE_URL || !SERVICE_KEY) {
    return { statusCode: 503, headers: CORS, body: JSON.stringify({ error: 'Supabase not configured' }) };
  }

  /* GET — leitura pública */
  if (event.httpMethod === 'GET') {
    try {
      const res = await fetch(
        `${SUPABASE_URL}/rest/v1/dashboard_config?id=eq.1&select=*`,
        { headers: { apikey: SERVICE_KEY, Authorization: `Bearer ${SERVICE_KEY}` } }
      );
      const rows = await res.json();
      return { statusCode: 200, headers: CORS, body: JSON.stringify(rows[0] || {}) };
    } catch (e) {
      return { statusCode: 500, headers: CORS, body: JSON.stringify({ error: e.message }) };
    }
  }

  /* POST — upsert com senha */
  if (event.httpMethod === 'POST') {
    try {
      const body     = JSON.parse(event.body || '{}');
      const { password, ...fields } = body;
      const expected = process.env.SETTINGS_PASSWORD;

      if (!expected) {
        return { statusCode: 503, headers: CORS, body: JSON.stringify({ error: 'SETTINGS_PASSWORD not configured' }) };
      }
      if (password !== expected) {
        return { statusCode: 200, headers: CORS, body: JSON.stringify({ ok: false }) };
      }

      const payload = { id: 1, updated_at: new Date().toISOString() };
      for (const key of ALLOWED) {
        if (fields[key] !== undefined) payload[key] = fields[key];
      }

      const res = await fetch(`${SUPABASE_URL}/rest/v1/dashboard_config`, {
        method: 'POST',
        headers: {
          apikey: SERVICE_KEY,
          Authorization: `Bearer ${SERVICE_KEY}`,
          'Content-Type': 'application/json',
          Prefer: 'resolution=merge-duplicates',
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.text();
        return { statusCode: 500, headers: CORS, body: JSON.stringify({ error: err }) };
      }

      return { statusCode: 200, headers: CORS, body: JSON.stringify({ ok: true }) };
    } catch (e) {
      return { statusCode: 500, headers: CORS, body: JSON.stringify({ error: e.message }) };
    }
  }

  return { statusCode: 405, headers: CORS, body: JSON.stringify({ error: 'Method not allowed' }) };
};
