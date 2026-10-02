# -*- coding: utf-8 -*-
"""Busca projetos de Implantacao/Reimplantacao no CRM nxlite e gera dashboard_data.js.

So leitura (GET). Nunca criar/alterar/apagar registros no CRM.
"""
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from http.cookiejar import CookieJar

BASE_URL = "https://crm.nxlite.com.br"

TEMA_KEYWORDS = {
    "Aguardando decisão/validação do cliente": [
        "aguardando cliente", "aguardando retorno", "aguardando validação",
        "aguardando decisão", "sem retorno do cliente", "aguardando aprovação",
    ],
    "Baixo engajamento / não adoção do cliente": [
        "baixo engajamento", "não está usando", "não utiliza", "não adotou",
        "resistência do cliente", "não acessa o sistema",
    ],
    "Pendente só encerramento formal (CSAT/termo)": [
        "só falta o csat", "pendente csat", "encerramento formal",
        "termo de encerramento", "só assinatura", "só falta assinar",
    ],
    "Falha técnica / bug do sistema": [
        "bug", "erro no sistema", "falha técnica", "travando", "não funciona",
    ],
    "Atraso do cliente com infraestrutura (servidor)": [
        "servidor", "infraestrutura", "comprando servidor",
    ],
    "Congelamento por decisão do cliente": [
        "congelado", "congelamento", "pausa solicitada", "pediu para pausar",
        "pediu pra pausar",
    ],
}
SEM_MOTIVO = "Sem motivo claro / sem anotação"
REVISAR_MANUALMENTE = "Não identificado — revisar manualmente"
PAUSA_KEYWORDS = ["pausa", "pausou", "pausado", "congelado", "congelamento"]


def calcular_atrasado(termino_previsto, hoje):
    """Retorna 'atrasado', 'no_prazo' ou 'prazo_nao_informado'."""
    if not termino_previsto:
        return "prazo_nao_informado"
    data_prazo = datetime.strptime(termino_previsto, "%Y-%m-%d").date()
    return "atrasado" if data_prazo < hoje else "no_prazo"


def dias_desde_ultima_anotacao(anotacoes, hoje):
    """Dias corridos desde a anotação mais recente. None se não houver nenhuma."""
    datas = [datetime.strptime(a["data"], "%Y-%m-%d").date() for a in anotacoes if a.get("data")]
    if not datas:
        return None
    return (hoje - max(datas)).days


def detectar_pausas(anotacoes):
    """Anotações (dict original) cujo texto contém palavra-chave de pausa/congelamento."""
    eventos = []
    for a in anotacoes:
        texto = (a.get("anotacao") or "").lower()
        if any(kw in texto for kw in PAUSA_KEYWORDS):
            eventos.append(a)
    return eventos


def classificar_tema(anotacoes):
    """Classifica o motivo do atraso em um dos temas fixos, por palavra-chave."""
    if not anotacoes:
        return SEM_MOTIVO
    texto = " ".join((a.get("anotacao") or "") for a in anotacoes).lower()
    for tema, palavras in TEMA_KEYWORDS.items():
        if any(p in texto for p in palavras):
            return tema
    return REVISAR_MANUALMENTE


def categoria_motivo(tema):
    """Mapeia o tema para a categoria usada no badge da coluna 'Motivo'."""
    if tema == SEM_MOTIVO:
        return "sem_motivo"
    if tema == REVISAR_MANUALMENTE:
        return "confuso"
    return "motivo"


def calcular_prioridade(dias_atraso):
    """'alta' quando o atraso já passou de 30 dias, senão 'normal'."""
    return "alta" if dias_atraso is not None and dias_atraso >= 30 else "normal"


def make_opener():
    cj = CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def call(opener, method, path, data=None):
    url = BASE_URL + path
    headers = {"Accept": "application/json"}
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with opener.open(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def resource(doctype, query=""):
    return "/api/resource/" + urllib.parse.quote(doctype) + query


class LoginError(Exception):
    pass


def fazer_login(opener, usuario, senha):
    status, raw = call(opener, "POST", "/api/method/login", {"usr": usuario, "pwd": senha})
    if status != 200:
        raise LoginError(f"login falhou (status={status}): {raw[:300]}")


def buscar_projetos(opener):
    """Todos os SAG Projeto de Implantacao/Reimplantacao, qualquer ano/status."""
    q = urllib.parse.urlencode({
        "fields": json.dumps([
            "name", "nome_do_projeto", "nome_cliente", "tipo_de_projeto", "status",
            "ritmo_andamento", "nome_lider_projeto_grv", "inicio_previsto",
            "termino_previsto", "percentual_conclusao",
        ]),
        "filters": json.dumps([["tipo_de_projeto", "in", ["Implantação", "Reimplantação"]]]),
        "limit_page_length": 0,
    })
    status, raw = call(opener, "GET", resource("SAG Projeto", "?" + q))
    if status != 200:
        raise RuntimeError(f"busca de SAG Projeto falhou (status={status}): {raw[:300]}")
    return json.loads(raw)["data"]


def buscar_anotacoes(opener, nome_projeto):
    """Anotacoes completas (child table) de um SAG Projeto especifico."""
    status, raw = call(opener, "GET", resource("SAG Projeto", "/" + urllib.parse.quote(nome_projeto)))
    if status != 200:
        raise RuntimeError(f"busca de anotações de {nome_projeto} falhou (status={status}): {raw[:300]}")
    return json.loads(raw)["data"].get("anotacoes", [])


def buscar_todos_modulos(opener):
    """Todos os SAG Modulo, agrupados por nome do projeto (uma unica chamada)."""
    q = urllib.parse.urlencode({
        "fields": json.dumps(["nome_modulo", "status", "percentual_conclusao", "sequencia", "projeto"]),
        "limit_page_length": 0,
    })
    status, raw = call(opener, "GET", resource("SAG Modulo", "?" + q))
    if status != 200:
        raise RuntimeError(f"busca de SAG Modulo falhou (status={status}): {raw[:300]}")
    modulos = json.loads(raw)["data"]
    por_projeto = {}
    for m in modulos:
        por_projeto.setdefault(m["projeto"], []).append(m)
    for lista in por_projeto.values():
        lista.sort(key=lambda m: m.get("sequencia") or 0)
    return por_projeto


def buscar_versions_status(opener, nome_projeto):
    """Historico de Version (log de mudancas de campo) de um SAG Projeto."""
    q = urllib.parse.urlencode({
        "fields": json.dumps(["name", "creation", "data"]),
        "filters": json.dumps([["ref_doctype", "=", "SAG Projeto"], ["docname", "=", nome_projeto]]),
        "order_by": "creation asc",
        "limit_page_length": 0,
    })
    status, raw = call(opener, "GET", resource("Version", "?" + q))
    if status != 200:
        raise RuntimeError(f"busca de Version de {nome_projeto} falhou (status={status}): {raw[:300]}")
    return json.loads(raw)["data"]
