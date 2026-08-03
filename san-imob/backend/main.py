"""
main.py — API REST da Soma Imob.

Expõe o arnês (harness/) e o banco (db.py) pro frontend estático em
san-imob/. Autenticação simplificada de MVP: todo endpoint recebe o
header X-Imobiliaria-Id e usa como tenant em toda query — sem OAuth
por enquanto (ver .env.example e README do backend).

Rodar com: uvicorn main:app --reload --port 8000
"""
import logging
import urllib.parse
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import get_connection
from harness.logger import get_custo_mensal, get_economia_mensal
from harness.intent_classifier import classify_intent
from harness.router import rotear_acao, confirmar_edicao
from harness.briefing import gerar_briefing

load_dotenv()

# Sem isso, todo logging.getLogger(__name__).info(...) do projeto
# (ex: harness/router.py logando qual bloco foi ativado por chamada,
# pedido explicitamente na Parte 2) é descartado em silêncio — o root
# logger do Python vem no nível WARNING por padrão, então nenhuma
# mensagem INFO aparece sem essa configuração. Descoberto rodando o
# backend pela primeira vez: o log de debug do router simplesmente
# nunca aparecia em lugar nenhum.
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s: %(message)s")

app = FastAPI(title="Soma Imob API")

# Taxa de comissão média usada pra estimar faturamento a partir do
# valor das propostas aceitas — mesma taxa (2,8%) já documentada no
# tooltip "Como o Arnês calculou isso" de metas.html. Reaproveitada
# aqui pra não ter dois números diferentes de comissão média no
# mesmo produto.
TAXA_COMISSAO_MEDIA = 0.028

# CORS: o frontend abre como file:// (Origin: null) ou via
# `python -m http.server` em alguma porta localhost — não dá pra saber
# a porta de antemão, por isso o regex além do "null" explícito.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_imobiliaria_id(x_imobiliaria_id: str = Header(..., alias="X-Imobiliaria-Id")):
    """Extrai o tenant do header. MVP: sem validar se o UUID existe de
    fato — isso vira uma consulta em `imobiliarias` quando tiver login real."""
    return x_imobiliaria_id


class ChatRequest(BaseModel):
    pergunta: str
    historico: list = []
    fonte: str = "texto"  # 'texto' | 'voz' — usado pra bloquear ações de escrita disparadas por voz


class EtapaUpdate(BaseModel):
    nova_etapa: str


class ImovelCreate(BaseModel):
    tipo: str
    bairro: str
    preco: float
    quartos: Optional[int] = None
    area_m2: Optional[float] = None
    exclusivo: bool = False
    status: str = "ativo"


class ConfirmarEdicaoBody(BaseModel):
    tipo_entidade: str
    entidade_id: str
    campo: str
    novo_valor: str
    usuario_id: Optional[str] = None  # fica nulo até existir login real


# ============================================================
# Prefixos de código de imóvel (Arnês IA — geração automática de
# código). Chaves em minúsculo, batendo com os 6 valores do <select>
# de tipo no formulário "Novo imóvel" do frontend (Apartamento, Casa,
# Cobertura, Terreno, Comercial, Rural) — o prompt original listava
# categorias diferentes (sala_comercial, galpao, chacara) que não
# existem em lugar nenhum do frontend; usamos os tipos reais.
# ============================================================
PREFIXOS_IMOVEL = {
    "apartamento": "AP",
    "casa": "CA",
    "cobertura": "CO",
    "terreno": "TE",
    "comercial": "CM",
    "rural": "RU",
}


def gerar_codigo_imovel(imobiliaria_id, tipo):
    """
    Gera o próximo código sequencial pro prefixo do tipo de imóvel
    (AP001, AP002, ...). O código nunca muda depois de gerado e nunca é
    reutilizado, mesmo se o imóvel for arquivado ou vendido — por isso
    conta quantos códigos com esse prefixo já existem (incluindo os
    inativos) em vez de reaproveitar buracos na sequência.
    """
    prefixo = PREFIXOS_IMOVEL.get((tipo or "").strip().lower(), "IM")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS total FROM imoveis
                WHERE imobiliaria_id = %(imobiliaria_id)s
                  AND codigo LIKE %(prefixo_like)s
                """,
                {"imobiliaria_id": imobiliaria_id, "prefixo_like": f"{prefixo}%"},
            )
            total = cur.fetchone()["total"]
    finally:
        conn.close()

    proximo = total + 1
    return f"{prefixo}{proximo:03d}"


# ============================================================
# ENDPOINT 1 — Chat com a Soma IA
# ============================================================

@app.post("/api/chat")
def chat(req: ChatRequest, imobiliaria_id: str = Depends(get_imobiliaria_id)):
    # Classificação sempre em Haiku, e sempre logada com o tenant real
    # (classify_intent loga a própria chamada quando recebe imobiliaria_id
    # — ver harness/intent_classifier.py).
    classificacao = classify_intent(req.pergunta, imobiliaria_id=imobiliaria_id)

    # rotear_acao decide o pipeline (SQL puro, Haiku ou Sonnet) e já
    # loga qualquer chamada de LLM que faça internamente — main.py não
    # loga de novo aqui. Cada chamada real ao Anthropic se loga sozinha
    # (harness/logger.py), então um log final agregado em main.py só
    # duplicaria a linha em api_logs sem nenhum ganho de observabilidade.
    return rotear_acao(
        classificacao=classificacao,
        imobiliaria_id=imobiliaria_id,
        pergunta=req.pergunta,
        historico=req.historico,
        fonte=req.fonte,
    )


# ============================================================
# ENDPOINT 2 — Listar imóveis
# ============================================================

@app.get("/api/imoveis")
def listar_imoveis(
    status: str = Query("todos"),
    busca: str = Query(""),
    imobiliaria_id: str = Depends(get_imobiliaria_id),
):
    condicoes = ["imobiliaria_id = %(imobiliaria_id)s"]
    params = {"imobiliaria_id": imobiliaria_id}

    if status and status != "todos":
        condicoes.append("status = %(status)s")
        params["status"] = status

    if busca:
        condicoes.append("(codigo ILIKE %(busca)s OR bairro ILIKE %(busca)s OR tipo ILIKE %(busca)s)")
        params["busca"] = f"%{busca}%"

    query = f"""
        SELECT id, codigo, tipo, bairro, preco, status, exclusivo, dias_carteira
        FROM imoveis
        WHERE {' AND '.join(condicoes)}
        ORDER BY dias_carteira ASC
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            linhas = cur.fetchall()
    finally:
        conn.close()

    imoveis = []
    for linha in linhas:
        item = dict(linha)
        item["id"] = str(item["id"])
        item["preco"] = float(item["preco"])
        item["codigo"] = item["codigo"] if str(item["codigo"]).startswith("#") else f"#{item['codigo']}"
        imoveis.append(item)

    return {"total": len(imoveis), "imoveis": imoveis}


# ============================================================
# ENDPOINT 2b — Criar imóvel (Arnês IA — geração automática de código)
# ============================================================

@app.post("/api/imoveis")
def criar_imovel(dados: ImovelCreate, imobiliaria_id: str = Depends(get_imobiliaria_id)):
    codigo = gerar_codigo_imovel(imobiliaria_id, dados.tipo)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO imoveis (
                    imobiliaria_id, codigo, tipo, bairro, preco,
                    quartos, area_m2, exclusivo, status
                ) VALUES (
                    %(imobiliaria_id)s, %(codigo)s, %(tipo)s, %(bairro)s, %(preco)s,
                    %(quartos)s, %(area_m2)s, %(exclusivo)s, %(status)s
                )
                RETURNING id
                """,
                {
                    "imobiliaria_id": imobiliaria_id,
                    "codigo": codigo,
                    "tipo": dados.tipo,
                    "bairro": dados.bairro,
                    "preco": dados.preco,
                    "quartos": dados.quartos,
                    "area_m2": dados.area_m2,
                    "exclusivo": dados.exclusivo,
                    "status": dados.status,
                },
            )
            novo_id = cur.fetchone()["id"]
        conn.commit()
    finally:
        conn.close()

    return {"id": str(novo_id), "codigo": codigo}


# ============================================================
# ENDPOINT 3 — Listar clientes/leads
# ============================================================

@app.get("/api/clientes")
def listar_clientes(
    filtro: str = Query("todos"),
    busca: str = Query(""),
    imobiliaria_id: str = Depends(get_imobiliaria_id),
):
    condicoes = ["c.imobiliaria_id = %(imobiliaria_id)s"]
    params = {"imobiliaria_id": imobiliaria_id}

    if filtro == "alta-chance":
        condicoes.append("c.score_fechamento >= 80")
    elif filtro == "sem-contato":
        condicoes.append("c.ultimo_contato < NOW() - INTERVAL '7 days'")

    if busca:
        condicoes.append("c.nome ILIKE %(busca)s")
        params["busca"] = f"%{busca}%"

    query = f"""
        SELECT c.id, c.nome, c.score_fechamento, c.temperatura, c.origem,
               EXTRACT(DAY FROM NOW() - c.ultimo_contato)::int AS ultimo_contato_dias,
               p.etapa AS etapa_pipeline,
               (SELECT COUNT(*) FROM imoveis_interesse ii WHERE ii.cliente_id = c.id) AS imoveis_interesse
        FROM clientes c
        LEFT JOIN pipeline p ON p.cliente_id = c.id
        WHERE {' AND '.join(condicoes)}
        ORDER BY c.score_fechamento DESC
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            linhas = cur.fetchall()
    finally:
        conn.close()

    clientes = []
    for linha in linhas:
        item = dict(linha)
        item["id"] = str(item["id"])
        clientes.append(item)

    return {"total": len(clientes), "clientes": clientes}


# ============================================================
# ENDPOINT 4 — Dados do pipeline Kanban
# ============================================================

ETAPAS_PIPELINE = [
    "aberto", "em_atendimento", "visita", "proposta",
    "documentacao", "concluido", "arquivado",
]


@app.get("/api/pipeline")
def listar_pipeline(imobiliaria_id: str = Depends(get_imobiliaria_id)):
    query = """
        SELECT c.id, c.nome, c.temperatura, c.origem,
               EXTRACT(DAY FROM NOW() - c.ultimo_contato)::int AS ultimo_contato_dias,
               p.etapa,
               (SELECT COUNT(*) FROM imoveis_interesse ii WHERE ii.cliente_id = c.id) AS imoveis_interesse
        FROM pipeline p
        JOIN clientes c ON c.id = p.cliente_id
        WHERE p.imobiliaria_id = %(imobiliaria_id)s
        ORDER BY c.score_fechamento DESC
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, {"imobiliaria_id": imobiliaria_id})
            linhas = cur.fetchall()
    finally:
        conn.close()

    colunas = {etapa: {"total": 0, "leads": []} for etapa in ETAPAS_PIPELINE}
    for linha in linhas:
        item = dict(linha)
        item["id"] = str(item["id"])
        etapa = item.pop("etapa")
        destino = etapa if etapa in colunas else "aberto"
        colunas[destino]["leads"].append(item)

    for etapa in colunas:
        colunas[etapa]["total"] = len(colunas[etapa]["leads"])

    return {"colunas": colunas}


# ============================================================
# ENDPOINT 5 — Mover card no Kanban
# ============================================================

@app.patch("/api/pipeline/{cliente_id}/etapa")
def mover_etapa(
    cliente_id: str,
    body: EtapaUpdate,
    imobiliaria_id: str = Depends(get_imobiliaria_id),
):
    if body.nova_etapa not in ETAPAS_PIPELINE:
        raise HTTPException(status_code=400, detail=f"Etapa inválida: {body.nova_etapa}")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE pipeline
                SET etapa = %(nova_etapa)s, atualizado_em = NOW()
                WHERE cliente_id = %(cliente_id)s AND imobiliaria_id = %(imobiliaria_id)s
                """,
                {
                    "nova_etapa": body.nova_etapa,
                    "cliente_id": cliente_id,
                    "imobiliaria_id": imobiliaria_id,
                },
            )
            atualizou = cur.rowcount > 0
        conn.commit()
    finally:
        conn.close()

    if not atualizou:
        raise HTTPException(status_code=404, detail="Lead não encontrado nesta imobiliária.")

    return {"ok": True}


# ============================================================
# ENDPOINT 6 — Alertas proativos pendentes
# ============================================================

@app.get("/api/alertas")
def listar_alertas(imobiliaria_id: str = Depends(get_imobiliaria_id)):
    query = """
        SELECT a.id, a.tipo, a.mensagem_sugerida, a.criado_em, c.nome AS cliente_nome
        FROM alertas_proativos a
        LEFT JOIN clientes c ON c.id = a.cliente_id
        WHERE a.imobiliaria_id = %(imobiliaria_id)s AND a.status = 'pendente'
        ORDER BY a.criado_em DESC
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, {"imobiliaria_id": imobiliaria_id})
            linhas = cur.fetchall()
    finally:
        conn.close()

    alertas = []
    for linha in linhas:
        item = dict(linha)
        item["id"] = str(item["id"])
        item["criado_em"] = item["criado_em"].isoformat()
        alertas.append(item)

    return {"alertas": alertas}


# ============================================================
# ENDPOINT 7 — Aprovar ou rejeitar alerta
# ============================================================

@app.post("/api/alertas/{alerta_id}/aprovar")
def aprovar_alerta(alerta_id: str, imobiliaria_id: str = Depends(get_imobiliaria_id)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.mensagem_sugerida, c.telefone
                FROM alertas_proativos a
                LEFT JOIN clientes c ON c.id = a.cliente_id
                WHERE a.id = %(id)s AND a.imobiliaria_id = %(imobiliaria_id)s
                """,
                {"id": alerta_id, "imobiliaria_id": imobiliaria_id},
            )
            alerta = cur.fetchone()
            if not alerta:
                raise HTTPException(status_code=404, detail="Alerta não encontrado.")

            cur.execute(
                """
                UPDATE alertas_proativos
                SET status = 'aprovado', aprovado_em = NOW()
                WHERE id = %(id)s AND imobiliaria_id = %(imobiliaria_id)s
                """,
                {"id": alerta_id, "imobiliaria_id": imobiliaria_id},
            )
        conn.commit()
    finally:
        conn.close()

    # No MVP não disparamos WhatsApp automaticamente — devolvemos o link
    # wa.me pro corretor clicar e confirmar o envio manualmente.
    whatsapp_url = None
    if alerta.get("telefone"):
        telefone_limpo = "".join(ch for ch in alerta["telefone"] if ch.isdigit())
        texto = urllib.parse.quote(alerta["mensagem_sugerida"] or "")
        whatsapp_url = f"https://wa.me/55{telefone_limpo}?text={texto}"

    return {"ok": True, "whatsapp_url": whatsapp_url}


@app.post("/api/alertas/{alerta_id}/rejeitar")
def rejeitar_alerta(alerta_id: str, imobiliaria_id: str = Depends(get_imobiliaria_id)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE alertas_proativos
                SET status = 'rejeitado'
                WHERE id = %(id)s AND imobiliaria_id = %(imobiliaria_id)s
                """,
                {"id": alerta_id, "imobiliaria_id": imobiliaria_id},
            )
            atualizou = cur.rowcount > 0
        conn.commit()
    finally:
        conn.close()

    if not atualizou:
        raise HTTPException(status_code=404, detail="Alerta não encontrado.")

    return {"ok": True}


# ============================================================
# ENDPOINT 8 — Métricas do dashboard
# ============================================================

@app.get("/api/metricas")
def metricas(imobiliaria_id: str = Depends(get_imobiliaria_id)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS total FROM imoveis WHERE imobiliaria_id = %(id)s AND status = 'ativo'",
                {"id": imobiliaria_id},
            )
            imoveis_ativos = cur.fetchone()["total"]

            cur.execute(
                "SELECT COUNT(*) AS total FROM clientes WHERE imobiliaria_id = %(id)s",
                {"id": imobiliaria_id},
            )
            leads_abertos = cur.fetchone()["total"]

            cur.execute(
                """
                SELECT COUNT(*) AS total FROM clientes
                WHERE imobiliaria_id = %(id)s AND ultimo_contato < NOW() - INTERVAL '3 days'
                """,
                {"id": imobiliaria_id},
            )
            tarefas_atrasadas = cur.fetchone()["total"]

            cur.execute(
                "SELECT COUNT(*) AS total FROM propostas WHERE imobiliaria_id = %(id)s AND status = 'aberta'",
                {"id": imobiliaria_id},
            )
            propostas_abertas = cur.fetchone()["total"]

            cur.execute(
                """
                SELECT COUNT(*) AS total FROM propostas
                WHERE imobiliaria_id = %(id)s AND status = 'aberta'
                  AND vencimento BETWEEN NOW() AND NOW() + INTERVAL '7 days'
                """,
                {"id": imobiliaria_id},
            )
            propostas_vencendo_semana = cur.fetchone()["total"]

            # KPIs do dashboard.html (Arnês IA agêntico) — não existiam até
            # aqui: essa tela sempre mostrou números fixos, sem consulta
            # nenhuma ao banco. TAXA_COMISSAO_MEDIA reaproveita a mesma
            # taxa (2,8%) já documentada no tooltip "Como o Arnês calculou
            # isso" de metas.html, pra não inventar um segundo número.
            # "Venda fechada" = proposta com status 'aceita' criada este
            # mês — o schema não tem uma data de fechamento separada da
            # data de criação da proposta, então usamos criado_em como
            # aproximação (mesma limitação já aceita em propostas_vencendo_semana).
            cur.execute(
                """
                SELECT COUNT(*) AS total,
                       COALESCE(AVG(valor), 0) AS ticket_medio,
                       COALESCE(SUM(valor), 0) AS soma_valor
                FROM propostas
                WHERE imobiliaria_id = %(id)s AND status = 'aceita'
                  AND EXTRACT(YEAR FROM criado_em) = EXTRACT(YEAR FROM NOW())
                  AND EXTRACT(MONTH FROM criado_em) = EXTRACT(MONTH FROM NOW())
                """,
                {"id": imobiliaria_id},
            )
            linha_vendas_mes = cur.fetchone()
            vendas_fechadas_mes = linha_vendas_mes["total"]
            ticket_medio_mes_brl = round(float(linha_vendas_mes["ticket_medio"]), 2)
            faturamento_comissao_mes_brl = round(float(linha_vendas_mes["soma_valor"]) * TAXA_COMISSAO_MEDIA, 2)

            taxa_conversao_pct = round((vendas_fechadas_mes / leads_abertos * 100), 2) if leads_abertos else 0.0
    finally:
        conn.close()

    agora = datetime.now(timezone.utc)
    try:
        custo = get_custo_mensal(imobiliaria_id, agora.year, agora.month)
        custo_api_mes_brl = round(float(custo["custo_total_brl"]), 2) if custo else 0.0
    except Exception:
        custo_api_mes_brl = 0.0

    return {
        "imoveis_ativos": imoveis_ativos,
        "leads_abertos": leads_abertos,
        "tarefas_atrasadas": tarefas_atrasadas,
        "propostas_abertas": propostas_abertas,
        "propostas_vencendo_semana": propostas_vencendo_semana,
        "custo_api_mes_brl": custo_api_mes_brl,
        "vendas_fechadas_mes": vendas_fechadas_mes,
        "faturamento_comissao_mes_brl": faturamento_comissao_mes_brl,
        "ticket_medio_mes_brl": ticket_medio_mes_brl,
        "taxa_conversao_pct": taxa_conversao_pct,
    }


# ============================================================
# ENDPOINT 8b — KPIs do dashboard.html (Arnês IA agêntico)
#
# Mesmos 4 números já expostos em GET /api/metricas (vendas_fechadas_mes,
# faturamento_comissao_mes_brl, ticket_medio_mes_brl, taxa_conversao_pct),
# só que num endpoint próprio pro dashboard.html não depender de um
# endpoint genérico de "métricas gerais" — consulta duplicada de
# propósito, seguindo o mesmo padrão do projeto de manter cada endpoint
# independente (ver _extrair_texto_resposta duplicado em 3 módulos do
# harness/).
# ============================================================

@app.get("/api/dashboard/kpis")
def dashboard_kpis(imobiliaria_id: str = Depends(get_imobiliaria_id)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS total FROM clientes WHERE imobiliaria_id = %(id)s",
                {"id": imobiliaria_id},
            )
            leads_abertos = cur.fetchone()["total"]

            cur.execute(
                """
                SELECT COUNT(*) AS total,
                       COALESCE(AVG(valor), 0) AS ticket_medio,
                       COALESCE(SUM(valor), 0) AS soma_valor
                FROM propostas
                WHERE imobiliaria_id = %(id)s AND status = 'aceita'
                  AND EXTRACT(YEAR FROM criado_em) = EXTRACT(YEAR FROM NOW())
                  AND EXTRACT(MONTH FROM criado_em) = EXTRACT(MONTH FROM NOW())
                """,
                {"id": imobiliaria_id},
            )
            linha = cur.fetchone()
    finally:
        conn.close()

    vendas_fechadas_mes = linha["total"]
    ticket_medio_mes_brl = round(float(linha["ticket_medio"]), 2)
    faturamento_comissao_mes_brl = round(float(linha["soma_valor"]) * TAXA_COMISSAO_MEDIA, 2)
    taxa_conversao_pct = round((vendas_fechadas_mes / leads_abertos * 100), 2) if leads_abertos else 0.0

    return {
        "vendas_fechadas_mes": vendas_fechadas_mes,
        "faturamento_comissao_mes_brl": faturamento_comissao_mes_brl,
        "ticket_medio_mes_brl": ticket_medio_mes_brl,
        "taxa_conversao_pct": taxa_conversao_pct,
    }


# ============================================================
# ENDPOINT 8c — Briefing matinal do dashboard.html (Arnês IA)
# ============================================================

@app.get("/api/dashboard/briefing")
def dashboard_briefing(imobiliaria_id: str = Depends(get_imobiliaria_id)):
    return gerar_briefing(imobiliaria_id)


# ============================================================
# ENDPOINT 8d — Alertas proativos pendentes pro dashboard.html
#
# Mesma consulta de listar_alertas (ENDPOINT 6) — endpoint próprio no
# namespace /api/dashboard/, consumido pelo grid "O que o Arnês
# recomenda agora" de dashboard.html (aprovar/ignorar continuam usando
# POST /api/alertas/{id}/aprovar e /rejeitar, que já existem).
# ============================================================

@app.get("/api/dashboard/alertas")
def dashboard_alertas(imobiliaria_id: str = Depends(get_imobiliaria_id)):
    query = """
        SELECT a.id, a.tipo, a.mensagem_sugerida, a.criado_em, c.nome AS cliente_nome
        FROM alertas_proativos a
        LEFT JOIN clientes c ON c.id = a.cliente_id
        WHERE a.imobiliaria_id = %(imobiliaria_id)s AND a.status = 'pendente'
        ORDER BY a.criado_em DESC
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, {"imobiliaria_id": imobiliaria_id})
            linhas = cur.fetchall()
    finally:
        conn.close()

    alertas = []
    for linha in linhas:
        item = dict(linha)
        item["id"] = str(item["id"])
        item["criado_em"] = item["criado_em"].isoformat()
        alertas.append(item)

    return {"alertas": alertas}


# ============================================================
# ENDPOINT 9 — Economia estimada por roteamento (Arnês IA — Problema 5)
# ============================================================

@app.get("/api/metricas/economia")
def metricas_economia(imobiliaria_id: str = Depends(get_imobiliaria_id)):
    agora = datetime.now(timezone.utc)
    try:
        economia = get_economia_mensal(imobiliaria_id, agora.year, agora.month)
        economia_total_brl = round(float(economia["economia_total_brl"]), 2) if economia else 0.0
        total_chamadas_haiku = economia["total_chamadas_haiku"] if economia else 0
    except Exception:
        economia_total_brl = 0.0
        total_chamadas_haiku = 0

    return {
        "economia_estimada_brl": economia_total_brl,
        "total_chamadas_haiku": total_chamadas_haiku,
    }


# ============================================================
# ENDPOINT 10 — Confirmar edição de cadastro (Arnês IA — Parte 5)
#
# Chamado depois que o corretor aprova o card de confirmação que o
# Bloco 3 do router (EDICAO_CADASTRO) devolveu — nunca é o próprio
# pipeline de chat que executa a edição, só este endpoint, disparado
# por uma ação explícita na interface.
# ============================================================

@app.post("/api/confirmar-edicao")
def confirmar_edicao_endpoint(body: ConfirmarEdicaoBody, imobiliaria_id: str = Depends(get_imobiliaria_id)):
    resultado = confirmar_edicao(
        imobiliaria_id=imobiliaria_id,
        tipo_entidade=body.tipo_entidade,
        entidade_id=body.entidade_id,
        campo=body.campo,
        novo_valor=body.novo_valor,
        usuario_id=body.usuario_id,
    )
    if resultado.get("erro"):
        raise HTTPException(status_code=400, detail=resultado)
    return resultado


# ============================================================
# ENDPOINT 10b — Histórico de edições feitas via Arnês IA (auditoria)
#
# Cada linha só existe depois do aceite explícito no card de
# confirmação (POST /api/confirmar-edicao é o único caminho que grava
# em historico_edicoes — ver harness/router.py:confirmar_edicao).
# usuario_nome vem nulo enquanto o sistema não tiver login real.
# ============================================================

@app.get("/api/historico-edicoes")
def historico_edicoes(
    tipo_entidade: Optional[str] = Query(None),
    entidade_id: Optional[str] = Query(None),
    limite: int = Query(50, le=200),
    imobiliaria_id: str = Depends(get_imobiliaria_id),
):
    condicoes = ["h.imobiliaria_id = %(imobiliaria_id)s"]
    params = {"imobiliaria_id": imobiliaria_id, "limite": limite}

    if tipo_entidade:
        condicoes.append("h.tipo_entidade = %(tipo_entidade)s")
        params["tipo_entidade"] = tipo_entidade

    if entidade_id:
        condicoes.append("h.entidade_id = %(entidade_id)s")
        params["entidade_id"] = entidade_id

    query = f"""
        SELECT h.id, h.tipo_entidade, h.entidade_id, h.campo,
               h.valor_anterior, h.valor_novo, h.origem, h.criado_em,
               h.usuario_id, u.nome AS usuario_nome
        FROM historico_edicoes h
        LEFT JOIN usuarios u ON u.id = h.usuario_id
        WHERE {' AND '.join(condicoes)}
        ORDER BY h.criado_em DESC
        LIMIT %(limite)s
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            linhas = cur.fetchall()
    finally:
        conn.close()

    historico = []
    for linha in linhas:
        item = dict(linha)
        item["id"] = str(item["id"])
        item["entidade_id"] = str(item["entidade_id"])
        item["usuario_id"] = str(item["usuario_id"]) if item["usuario_id"] else None
        item["criado_em"] = item["criado_em"].isoformat()
        historico.append(item)

    return {"total": len(historico), "historico": historico}


# ============================================================
# Health check — usado pelo frontend pra saber se deve mostrar o
# banner de "tentando reconectar"
# ============================================================

@app.get("/api/health")
def health():
    return {"status": "ok"}
