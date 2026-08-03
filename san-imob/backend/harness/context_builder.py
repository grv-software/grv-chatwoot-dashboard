"""
harness/context_builder.py — Monta o contexto completo da imobiliária (Problema 2).

Decisão arquitetural (não é aberta a debate sem nova análise): SEM
pgvector, SEM busca semântica. A carteira de uma imobiliária-alvo
(centenas de imóveis, poucos milhares de leads) cabe inteira e
formatada num contexto de ~100-150k tokens, e as perguntas reais do
produto (ranking por score, filtro por preço/quartos) são resolvidas
melhor por SQL do que por similaridade vetorial — RAG erra justamente
nesses dois casos, que são o coração do produto. Ver análise crítica
do arnês para o raciocínio completo.

O contexto sai dividido em duas partes:
- contexto_estavel: instrução de sistema da Soma IA — candidato a
  prompt caching, muda raramente.
- contexto_dinamico: carteira, leads, alertas — muda ao longo do dia.
  NUNCA cachear esta parte: cachear dado que muda gera resposta
  desatualizada (imóvel já reservado, lead já contatado) sem que
  ninguém perceba o erro.
"""
from db import get_connection

INSTRUCAO_SISTEMA = """Você é a Soma IA, assistente do CRM Soma Imob.
Responda com base apenas no contexto fornecido abaixo — nunca invente
preço, endereço ou condição de imóvel que não esteja explicitamente
listado. Se o contexto não tiver a informação necessária pra responder
com segurança, diga isso claramente em vez de adivinhar.
Use linguagem e terminologia do mercado imobiliário brasileiro (CRECI,
financiamento Caixa, entrada, parcelas).
Seja objetivo: frases curtas, direto ao ponto, tom cordial mas sem
rodeios nem parágrafos longos. Exceção: quando o pedido for para gerar
um documento que o corretor vai enviar a terceiros (proposta comercial,
mensagem de WhatsApp), use o tamanho necessário para esse conteúdo —
a objetividade vale para respostas de conversa/dúvida, não para o
conteúdo do documento em si."""


def _formatar_imoveis(imoveis):
    linhas = [f"CARTEIRA DE IMÓVEIS ({len(imoveis)} ativos):"]
    for im in imoveis:
        tag_str = " | Exclusivo" if im["exclusivo"] else ""
        linhas.append(
            f"#{im['codigo']} | {im['tipo']} | {im['bairro']} | "
            f"R$ {im['preco']:,.0f} | {im['status'].capitalize()} | "
            f"{im['dias_carteira']} dias{tag_str}"
        )
    return "\n".join(linhas)


def _formatar_leads_relevantes(leads):
    linhas = ["LEADS QUENTES E MORNOS (score ≥ 50):"]
    for lead in leads:
        dias = lead.get("dias_desde_contato")
        contato_str = f"{dias} dias" if dias is not None else "sem registro"
        linhas.append(
            f"{lead['nome']} | Score {lead['score_fechamento']} | "
            f"{lead['temperatura'].capitalize()} | {lead.get('etapa') or 'sem etapa'} | "
            f"último contato: {contato_str}"
        )
    return "\n".join(linhas)


def _formatar_leads_resumo(contagem_por_etapa):
    linhas = ["LEADS COM SCORE BAIXO (score < 50, resumo por etapa):"]
    for etapa, total in contagem_por_etapa.items():
        linhas.append(f"- {etapa}: {total} leads")
    return "\n".join(linhas)


def _formatar_alertas(alertas):
    if not alertas:
        return "ALERTAS:\n(nenhum alerta pendente no momento)"
    linhas = ["ALERTAS:"]
    for alerta in alertas:
        linhas.append(f"- {alerta['descricao']}")
    return "\n".join(linhas)


def build_context(imobiliaria_id, intencao, dados_extras=None):
    """
    Monta o contexto completo pra enviar ao LLM.

    Retorna {"contexto_estavel": str, "contexto_dinamico": str}.
    contexto_estavel é o candidato a prompt caching; contexto_dinamico
    nunca deve ser cacheado.

    `intencao` vem do intent_classifier — reservado pra uso futuro (ver
    observação no fim do arquivo). Hoje ainda busca tudo, sem recorte
    por tipo de pergunta.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT codigo, tipo, bairro, preco, status, quartos,
                       dias_carteira, exclusivo
                FROM imoveis
                WHERE imobiliaria_id = %(id)s AND status = 'ativo'
                ORDER BY dias_carteira ASC
                """,
                {"id": imobiliaria_id},
            )
            imoveis = cur.fetchall()

            cur.execute(
                """
                SELECT c.nome, c.score_fechamento, c.temperatura, p.etapa,
                       EXTRACT(DAY FROM NOW() - c.ultimo_contato)::int AS dias_desde_contato
                FROM clientes c
                LEFT JOIN pipeline p ON p.cliente_id = c.id
                WHERE c.imobiliaria_id = %(id)s AND c.score_fechamento >= 50
                ORDER BY c.score_fechamento DESC
                """,
                {"id": imobiliaria_id},
            )
            leads_relevantes = cur.fetchall()

            cur.execute(
                """
                SELECT p.etapa, COUNT(*) AS total
                FROM clientes c
                JOIN pipeline p ON p.cliente_id = c.id
                WHERE c.imobiliaria_id = %(id)s AND c.score_fechamento < 50
                GROUP BY p.etapa
                """,
                {"id": imobiliaria_id},
            )
            contagem_por_etapa = {row["etapa"]: row["total"] for row in cur.fetchall()}

            cur.execute(
                """
                SELECT tipo, mensagem_sugerida
                FROM alertas_proativos
                WHERE imobiliaria_id = %(id)s AND status = 'pendente'
                ORDER BY criado_em DESC
                LIMIT 20
                """,
                {"id": imobiliaria_id},
            )
            alertas_raw = cur.fetchall()
    finally:
        conn.close()

    alertas = [{"descricao": a["mensagem_sugerida"] or a["tipo"]} for a in alertas_raw]

    contexto_dinamico = "\n\n".join([
        _formatar_imoveis(imoveis),
        _formatar_leads_relevantes(leads_relevantes),
        _formatar_leads_resumo(contagem_por_etapa),
        _formatar_alertas(alertas),
    ])

    return {
        "contexto_estavel": INSTRUCAO_SISTEMA,
        "contexto_dinamico": contexto_dinamico,
    }


# ============================================================
# Exemplo de saída de contexto_dinamico (documentação, não é código
# executado):
#
# CARTEIRA DE IMÓVEIS (481 ativos):
# #1023 | Ap. 2q | Palmeiras | R$ 480.000 | Ativo | 12 dias | Exclusivo
# #1044 | Casa 3q | Centro | R$ 620.000 | Ativo | 45 dias
# ...
#
# LEADS QUENTES E MORNOS (score ≥ 50):
# Marcos Andrade | Score 94 | Quente | em_atendimento | último contato: 3 dias
# Fernanda Lima | Score 91 | Quente | proposta | último contato: 1 dias
# ...
#
# LEADS COM SCORE BAIXO (score < 50, resumo por etapa):
# - aberto: 214 leads
# - arquivado: 58 leads
#
# ALERTAS:
# - Proposta Família Souza vence em 24h — sem contato em 48h
# - 8 leads sem contato há mais de 7 dias
#
# ============================================================
# Observação pra quem for evoluir este módulo: hoje build_context()
# ignora o parâmetro `intencao` e sempre busca as quatro seções
# inteiras. O próximo passo natural — só depois de medir tokens reais
# via harness/logger.py — é usar a intenção pra pular seções que não
# importam pra aquela pergunta (ex: BUSCA_IMOVEL não precisa da lista
# de leads). Isso reduz tokens de input sem precisar de busca semântica.
# ============================================================
