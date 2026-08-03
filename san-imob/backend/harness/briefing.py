"""
harness/briefing.py — Briefing matinal do dashboard (GET /api/dashboard/briefing).

Mesmo padrão do scanner proativo (jobs/proactive_scanner.py): a
detecção das condições (leads quentes sem contato, propostas vencendo,
alertas pendentes) é SQL puro e determinística. O Haiku só redige o
texto corrido em cima desses dados já levantados — nunca decide
sozinho quais leads/propostas existem, e nunca inventa nomes ou
números além dos que a query devolveu.

Se a chamada ao Haiku falhar por qualquer motivo (rede, rate limit,
etc.), cai num texto determinístico montado só com os números reais —
o briefing nunca falha silenciosamente nem trava o dashboard.
"""
import os
import anthropic

from db import get_connection
from harness.logger import log_api_call

MODELO_BRIEFING = "claude-haiku-4-5-20251001"

QUERY_LEADS_SEM_CONTATO = """
    SELECT id, nome, score_fechamento,
           EXTRACT(DAY FROM NOW() - ultimo_contato)::int AS dias_sem_contato
    FROM clientes
    WHERE imobiliaria_id = %(id)s
      AND score_fechamento >= 80
      AND ultimo_contato < NOW() - INTERVAL '3 days'
    ORDER BY score_fechamento DESC
    LIMIT 5
"""

QUERY_PROPOSTAS_VENCENDO = """
    SELECT p.id, p.cliente_id, c.nome AS cliente_nome, p.valor, p.vencimento
    FROM propostas p
    JOIN clientes c ON c.id = p.cliente_id
    WHERE p.imobiliaria_id = %(id)s
      AND p.status = 'aberta'
      AND p.vencimento BETWEEN NOW() AND NOW() + INTERVAL '7 days'
    ORDER BY p.vencimento ASC
    LIMIT 5
"""

QUERY_ALERTAS_PENDENTES = """
    SELECT COUNT(*) AS total FROM alertas_proativos
    WHERE imobiliaria_id = %(id)s AND status = 'pendente'
"""


def _extrair_texto_resposta(resposta):
    """Mesmo helper duplicado em intent_classifier.py/router.py/
    proactive_scanner.py — ver router.py para o raciocínio completo."""
    for bloco in resposta.content:
        if getattr(bloco, "type", None) == "text":
            return bloco.text
    raise ValueError("Resposta da Anthropic não contém nenhum bloco de texto.")


def _texto_fallback(leads, propostas, alertas_pendentes):
    """Usado só se a chamada ao Haiku falhar — texto determinístico,
    sem IA, montado com os mesmos números reais que o prompt receberia."""
    if not leads and not propostas and not alertas_pendentes:
        return "Bom dia! Nenhuma pendência urgente no momento — pipeline sob controle."

    partes = ["Bom dia."]
    if leads:
        partes.append(
            f"{len(leads)} lead(s) quente(s) sem contato recente, incluindo {leads[0]['nome']}."
        )
    if propostas:
        partes.append(f"{len(propostas)} proposta(s) vencendo nos próximos dias.")
    if alertas_pendentes:
        partes.append(f"{alertas_pendentes} alerta(s) do Arnês aguardando revisão.")
    return " ".join(partes)


def gerar_briefing(imobiliaria_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(QUERY_LEADS_SEM_CONTATO, {"id": imobiliaria_id})
            leads = [dict(r) for r in cur.fetchall()]

            cur.execute(QUERY_PROPOSTAS_VENCENDO, {"id": imobiliaria_id})
            propostas = [dict(r) for r in cur.fetchall()]

            cur.execute(QUERY_ALERTAS_PENDENTES, {"id": imobiliaria_id})
            alertas_pendentes = cur.fetchone()["total"]
    finally:
        conn.close()

    dados_texto = (
        f"Leads quentes sem contato: "
        f"{[(l['nome'], l['score_fechamento'], l['dias_sem_contato']) for l in leads]}\n"
        f"Propostas vencendo em breve: "
        f"{[(p['cliente_nome'], float(p['valor'])) for p in propostas]}\n"
        f"Alertas proativos pendentes: {alertas_pendentes}"
    )

    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        resposta = client.messages.create(
            model=MODELO_BRIEFING,
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": (
                    "Você é o Arnês IA, assistente de um CRM imobiliário chamado "
                    "Soma Imob. Escreva um briefing matinal curto (2-3 frases "
                    "corridas, em texto simples, tom direto e cordial, em "
                    "português) para o corretor com base SOMENTE nestes dados "
                    "reais:\n\n" + dados_texto +
                    "\n\nSem markdown, sem títulos, sem emojis, sem negrito — "
                    "só texto corrido, objetivo, sem rodeios. Se não houver "
                    "nada urgente, diga que está tudo tranquilo. Não invente "
                    "nenhum número ou nome além dos fornecidos acima."
                ),
            }],
        )
        texto = _extrair_texto_resposta(resposta).strip()
        try:
            usage = resposta.usage
            log_api_call({
                "imobiliaria_id": imobiliaria_id,
                "intencao": "BRIEFING_DASHBOARD",
                "modelo": MODELO_BRIEFING,
                "tokens_input": usage.input_tokens,
                "tokens_output": usage.output_tokens,
                "cache_hit_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
            })
        except Exception:
            # Logging nunca pode derrubar o briefing em si.
            pass
    except Exception:
        texto = _texto_fallback(leads, propostas, alertas_pendentes)

    return {
        "texto": texto,
        "leads_sem_contato": [
            {
                "id": str(l["id"]),
                "nome": l["nome"],
                "score": l["score_fechamento"],
                "dias_sem_contato": l["dias_sem_contato"],
            }
            for l in leads
        ],
        "propostas_vencendo": [
            {
                "id": str(p["id"]),
                "cliente_id": str(p["cliente_id"]),
                "cliente_nome": p["cliente_nome"],
                "valor": float(p["valor"]),
                "vencimento": p["vencimento"].isoformat(),
            }
            for p in propostas
        ],
        "alertas_pendentes": alertas_pendentes,
    }
