"""
jobs/proactive_scanner.py — Scanner do modo proativo (Problema 4).

Roda periodicamente via cron/scheduler externo (de hora em hora já
cobre os três casos abaixo — não precisa ser real-time). A DETECÇÃO
das condições é SQL puro e determinístico, nunca chamada de LLM. O
modelo (Haiku) só entra depois, pra redigir o texto da sugestão dos
casos já filtrados — é isso que mantém o custo do modo proativo
previsível: uma chamada de LLM por alerta novo, não uma por lead ou
imóvel verificado.

Nenhum alerta é enviado automaticamente em nenhuma circunstância. Todo
resultado vira uma linha em alertas_proativos com status='pendente',
esperando aprovação do corretor na interface (painel "Atividade da IA").
"""
import os
import anthropic
from db import get_connection

MODELO_REDACAO = "claude-haiku-4-5-20251001"

QUERY_LEADS_SEM_CONTATO = """
    SELECT c.id, c.nome, c.score_fechamento, c.ultimo_contato
    FROM clientes c
    WHERE c.imobiliaria_id = %(imobiliaria_id)s
      AND c.score_fechamento >= 80
      AND c.ultimo_contato < NOW() - INTERVAL '3 days'
      AND NOT EXISTS (
        SELECT 1 FROM alertas_proativos a
        WHERE a.cliente_id = c.id
          AND a.tipo = 'LEAD_SEM_CONTATO'
          AND a.criado_em > NOW() - INTERVAL '24 hours'
      )
"""

QUERY_PROPOSTAS_VENCENDO = """
    SELECT p.id, p.cliente_id, p.vencimento, c.nome
    FROM propostas p
    JOIN clientes c ON c.id = p.cliente_id
    WHERE p.imobiliaria_id = %(imobiliaria_id)s
      AND p.status = 'aberta'
      AND p.vencimento BETWEEN NOW() AND NOW() + INTERVAL '48 hours'
      AND NOT EXISTS (
        SELECT 1 FROM alertas_proativos a
        WHERE a.proposta_id = p.id
          AND a.tipo = 'PROPOSTA_VENCENDO'
          AND a.criado_em > NOW() - INTERVAL '24 hours'
      )
"""

QUERY_PROPRIETARIOS_SEM_FEEDBACK = """
    SELECT i.id, i.codigo, i.bairro,
      MAX(v.data_visita) AS ultima_visita
    FROM imoveis i
    LEFT JOIN visitas v ON v.imovel_id = i.id
    WHERE i.imobiliaria_id = %(imobiliaria_id)s
      AND i.status = 'ativo'
    GROUP BY i.id, i.codigo, i.bairro
    HAVING MAX(v.data_visita) < NOW() - INTERVAL '7 days'
       OR MAX(v.data_visita) IS NULL
"""

# Deduplicação da condição 3 é feita em Python (ver scan_proprietarios_sem_feedback)
# porque a query já usa HAVING/GROUP BY e adicionar mais um NOT EXISTS
# correlacionado ali deixaria a query difícil de ler sem ganho real.
QUERY_ALERTA_RECENTE_IMOVEL = """
    SELECT 1 FROM alertas_proativos
    WHERE imovel_id = %(imovel_id)s
      AND tipo = 'PROPRIETARIO_SEM_FEEDBACK'
      AND criado_em > NOW() - INTERVAL '24 hours'
"""


def _extrair_texto_resposta(resposta):
    """
    Extrai o texto de uma resposta da Anthropic sem supor que
    content[0] seja sempre o bloco de texto — com extended thinking,
    o primeiro bloco pode ser um ThinkingBlock (sem atributo .text).
    Mesmo helper duplicado em harness/router.py e
    harness/intent_classifier.py — cada módulo permanece independente.
    """
    for bloco in resposta.content:
        if getattr(bloco, "type", None) == "text":
            return bloco.text
    raise ValueError("Resposta da Anthropic não contém nenhum bloco de texto.")


def _redigir_sugestao(prompt_contexto):
    """Chama Haiku só pra redigir o texto — a detecção já aconteceu em SQL."""
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    resposta = client.messages.create(
        model=MODELO_REDACAO,
        max_tokens=150,
        messages=[{"role": "user", "content": prompt_contexto}],
    )
    return _extrair_texto_resposta(resposta).strip()


def _salvar_alerta(cur, imobiliaria_id, tipo, mensagem_sugerida,
                    cliente_id=None, imovel_id=None, proposta_id=None):
    cur.execute(
        """
        INSERT INTO alertas_proativos (
            imobiliaria_id, tipo, cliente_id, imovel_id, proposta_id,
            mensagem_sugerida, status
        ) VALUES (
            %(imobiliaria_id)s, %(tipo)s, %(cliente_id)s, %(imovel_id)s,
            %(proposta_id)s, %(mensagem_sugerida)s, 'pendente'
        )
        """,
        {
            "imobiliaria_id": imobiliaria_id,
            "tipo": tipo,
            "cliente_id": cliente_id,
            "imovel_id": imovel_id,
            "proposta_id": proposta_id,
            "mensagem_sugerida": mensagem_sugerida,
        },
    )


def scan_leads_sem_contato(cur, imobiliaria_id):
    """Condição 1: lead quente (score >= 80) sem contato há 3+ dias."""
    cur.execute(QUERY_LEADS_SEM_CONTATO, {"imobiliaria_id": imobiliaria_id})
    for lead in cur.fetchall():
        sugestao = _redigir_sugestao(
            f"Escreva uma mensagem curta de WhatsApp (2-3 frases, tom cordial "
            f"e direto) pra retomar contato com {lead['nome']}, um lead quente "
            f"(score {lead['score_fechamento']}) sem contato há alguns dias."
        )
        _salvar_alerta(cur, imobiliaria_id, "LEAD_SEM_CONTATO", sugestao, cliente_id=lead["id"])


def scan_propostas_vencendo(cur, imobiliaria_id):
    """Condição 2: proposta aberta vencendo nas próximas 48h."""
    cur.execute(QUERY_PROPOSTAS_VENCENDO, {"imobiliaria_id": imobiliaria_id})
    for proposta in cur.fetchall():
        sugestao = _redigir_sugestao(
            f"Escreva uma mensagem curta lembrando {proposta['nome']} que a "
            f"proposta está vencendo em breve, com tom de urgência gentil, "
            f"sem pressionar demais."
        )
        _salvar_alerta(
            cur, imobiliaria_id, "PROPOSTA_VENCENDO", sugestao,
            cliente_id=proposta["cliente_id"], proposta_id=proposta["id"],
        )


def scan_proprietarios_sem_feedback(cur, imobiliaria_id):
    """Condição 3: imóvel ativo sem visita registrada nos últimos 7 dias."""
    cur.execute(QUERY_PROPRIETARIOS_SEM_FEEDBACK, {"imobiliaria_id": imobiliaria_id})
    for imovel in cur.fetchall():
        cur.execute(QUERY_ALERTA_RECENTE_IMOVEL, {"imovel_id": imovel["id"]})
        if cur.fetchone():
            continue  # já existe alerta recente pra esse imóvel — dedup

        sugestao = _redigir_sugestao(
            f"Escreva uma mensagem curta de atualização pro proprietário do "
            f"imóvel #{imovel['codigo']} ({imovel['bairro']}), explicando que "
            f"não há visita recente registrada e perguntando se ele quer "
            f"ajustar preço ou condições."
        )
        _salvar_alerta(cur, imobiliaria_id, "PROPRIETARIO_SEM_FEEDBACK", sugestao, imovel_id=imovel["id"])


def run_scan(imobiliaria_id):
    """
    Ponto de entrada do job — chamar via cron/scheduler a cada hora,
    uma vez por imobiliaria_id ativa (uma chamada externa por tenant,
    não um loop escondido dentro do módulo, pra manter o isolamento
    multi-tenant visível em quem orquestra o agendamento).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            scan_leads_sem_contato(cur, imobiliaria_id)
            scan_propostas_vencendo(cur, imobiliaria_id)
            scan_proprietarios_sem_feedback(cur, imobiliaria_id)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Uso: python proactive_scanner.py <imobiliaria_id>")
        sys.exit(1)
    run_scan(sys.argv[1])
