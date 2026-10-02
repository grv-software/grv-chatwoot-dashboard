# -*- coding: utf-8 -*-
"""Busca projetos de Implantacao/Reimplantacao no CRM nxlite e gera dashboard_data.js.

So leitura (GET). Nunca criar/alterar/apagar registros no CRM.
"""
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
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


def montar_projeto_atrasado(projeto, anotacoes, modulos, hoje):
    """Combina um SAG Projeto 'Aberto' com os campos derivados (atraso, motivo, pausas, progresso)."""
    dias_atraso = None
    semanas_atraso = None
    if projeto.get("termino_previsto"):
        data_prazo = datetime.strptime(projeto["termino_previsto"], "%Y-%m-%d").date()
        dias_atraso = (hoje - data_prazo).days
        semanas_atraso = dias_atraso // 7
    tema = classificar_tema(anotacoes)
    categoria = categoria_motivo(tema)
    pausas = detectar_pausas(anotacoes)
    ultima_anotacao = anotacoes[-1]["anotacao"] if anotacoes else "Sem anotações registradas."
    return {
        "name": projeto["name"],
        "nome_do_projeto": projeto.get("nome_do_projeto"),
        "nome_cliente": projeto.get("nome_cliente"),
        "nome_lider_projeto_grv": projeto.get("nome_lider_projeto_grv"),
        "tipo_de_projeto": projeto.get("tipo_de_projeto"),
        "termino_previsto": projeto.get("termino_previsto"),
        "inicio_previsto": projeto.get("inicio_previsto"),
        "percentual_conclusao": projeto.get("percentual_conclusao") or 0.0,
        "modulos": [
            {"nome": m.get("nome_modulo"), "status": m.get("status"), "percentual_conclusao": m.get("percentual_conclusao") or 0.0}
            for m in modulos
        ],
        "_prazo_vencido": calcular_atrasado(projeto.get("termino_previsto"), hoje) == "atrasado",
        "_dias_atraso": dias_atraso,
        "_semanas_atraso": semanas_atraso,
        "_dias_sem_atualizacao": dias_desde_ultima_anotacao(anotacoes, hoje),
        "_motivo": ultima_anotacao,
        "_tema": tema,
        "_categoria_motivo": categoria,
        "_motivo_plausivel": categoria == "motivo",
        "_justificativa_plausibilidade": (
            f'Classificado automaticamente como "{tema}".' if categoria == "motivo"
            else "Sem causa externa identificada automaticamente nas anotações."
        ),
        "_teve_pausa": len(pausas) > 0,
        "_numero_pausas": len(pausas),
        "_prioridade": calcular_prioridade(dias_atraso),
    }


def extrair_dia_mudanca_status(versions, status_alvo):
    """Primeira data (YYYY-MM-DD) em que o campo 'status' mudou para um dos status_alvo."""
    for v in versions:
        mudancas = json.loads(v["data"]).get("changed", [])
        for mudanca in mudancas:
            campo, _antigo, novo = mudanca
            if campo == "status" and novo in status_alvo:
                return v["creation"].split(" ")[0]
    return None


def montar_projeto_finalizado(projeto, versions, modulos):
    """Combina um SAG Projeto concluido (Consulta/Fechado) com o log de quando mudou de status."""
    dia_mudanca = extrair_dia_mudanca_status(versions, ("Consulta", "Fechado"))
    dias_entre = None
    if dia_mudanca and projeto.get("termino_previsto"):
        d_mudanca = datetime.strptime(dia_mudanca, "%Y-%m-%d").date()
        d_prazo = datetime.strptime(projeto["termino_previsto"], "%Y-%m-%d").date()
        dias_entre = (d_mudanca - d_prazo).days
    ano_inicio = int(projeto["inicio_previsto"][:4]) if projeto.get("inicio_previsto") else None
    return {
        "name": projeto["name"],
        "nome_cliente": projeto.get("nome_cliente"),
        "status": projeto.get("status"),
        "nome_lider_projeto_grv": projeto.get("nome_lider_projeto_grv"),
        "termino_previsto": projeto.get("termino_previsto"),
        "percentual_conclusao": projeto.get("percentual_conclusao") or 0.0,
        "modulos": [
            {"nome": m.get("nome_modulo"), "status": m.get("status"), "percentual_conclusao": m.get("percentual_conclusao") or 0.0}
            for m in modulos
        ],
        "_ano_inicio": ano_inicio,
        "_dia_mudanca": dia_mudanca,
        "_dias_entre_prazo_e_status": dias_entre,
    }


def calcular_visao_geral_por_ano(projetos, info_conclusao, hoje):
    """Agrupa os projetos por ano de inicio_previsto e calcula os KPIs da Visao Geral.

    info_conclusao: dict {nome_projeto: dias_entre_prazo_e_status} para projetos
    Consulta/Fechado (vem de montar_projeto_finalizado). Retorna
    {"2024": {...}, "2025": {...}, ..., "todos": {...}}.
    """
    def kpis_de(lista):
        abertos = [p for p in lista if p["status"] == "Aberto"]
        atrasados = [p for p in abertos if calcular_atrasado(p.get("termino_previsto"), hoje) == "atrasado"]
        concluidos = [p for p in lista if p["status"] in ("Consulta", "Fechado")]
        concluidos_no_prazo = concluidos_atrasados = concluidos_sem_info = 0
        for p in concluidos:
            dias = info_conclusao.get(p["name"])
            if dias is None:
                concluidos_sem_info += 1
            elif dias > 0:
                concluidos_atrasados += 1
            else:
                concluidos_no_prazo += 1
        pausados = [p for p in lista if p["status"] == "Pausado"]
        cancelados = [p for p in lista if p["status"] in ("Cancelado", "Interrompido", "Modelo")]
        return {
            "total": len(lista),
            "atrasados": len(atrasados),
            "abertos_no_prazo": len(abertos) - len(atrasados),
            "pausados": len(pausados),
            "concluidos": len(concluidos),
            "concluidos_no_prazo": concluidos_no_prazo,
            "concluidos_atrasados": concluidos_atrasados,
            "concluidos_sem_info": concluidos_sem_info,
            "cancelados": len(cancelados),
        }

    anos = sorted({p["inicio_previsto"][:4] for p in projetos if p.get("inicio_previsto")})
    resultado = {ano: kpis_de([p for p in projetos if (p.get("inicio_previsto") or "")[:4] == ano]) for ano in anos}
    resultado["todos"] = kpis_de(projetos)
    return resultado


def _contar_por(projetos, campo):
    contagem = {}
    for p in projetos:
        chave = p.get(campo) or "(vazio)"
        contagem[chave] = contagem.get(chave, 0) + 1
    return contagem


def gerar_dashboard_data(opener, hoje):
    projetos = buscar_projetos(opener)
    modulos_por_projeto = buscar_todos_modulos(opener)

    vencidos, nao_vencidos, finalizados = [], [], []
    anotacoes_map, pausas_info, info_conclusao = {}, {}, {}

    for p in projetos:
        nome = p["name"]
        modulos = modulos_por_projeto.get(nome, [])
        if p["status"] == "Aberto":
            anotacoes = buscar_anotacoes(opener, nome)
            anotacoes_map[nome] = [{"data": a.get("data"), "texto": a.get("anotacao")} for a in anotacoes]
            pausas = detectar_pausas(anotacoes)
            pausas_info[nome] = [{"data": e.get("data"), "motivo": e.get("anotacao"), "prazo": None} for e in pausas]
            entry = montar_projeto_atrasado(p, anotacoes, modulos, hoje)
            if entry["_prazo_vencido"]:
                vencidos.append(entry)
            elif p.get("ritmo_andamento") == "Atrasado":
                nao_vencidos.append(entry)
        elif p["status"] in ("Consulta", "Fechado"):
            versions = buscar_versions_status(opener, nome)
            entry = montar_projeto_finalizado(p, versions, modulos)
            finalizados.append(entry)
            info_conclusao[nome] = entry["_dias_entre_prazo_e_status"]

    resumo = {
        "total_implantacao_reimplantacao": len(projetos),
        "por_tipo": _contar_por(projetos, "tipo_de_projeto"),
        "por_status": _contar_por(projetos, "status"),
        "abertos": sum(1 for p in projetos if p["status"] == "Aberto"),
        "atrasados_flag_sistema": sum(1 for p in projetos if p.get("ritmo_andamento") == "Atrasado"),
        "atrasados_prazo_vencido": len(vencidos),
        "atrasados_prazo_nao_vencido": len(nao_vencidos),
    }

    lideres_count = {}
    for p in vencidos:
        lideres_count[p["nome_lider_projeto_grv"]] = lideres_count.get(p["nome_lider_projeto_grv"], 0) + 1
    lideres = sorted(lideres_count.items(), key=lambda kv: kv[1], reverse=True)

    return {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "atrasados": {
            "resumo": resumo,
            "vencidos": vencidos,
            "nao_vencidos": nao_vencidos,
            "lideres": [list(l) for l in lideres],
        },
        "visao_geral_por_ano": calcular_visao_geral_por_ano(projetos, info_conclusao, hoje),
        "finalizados": {"projetos": finalizados},
        "cat_labels": {
            "motivo": "Motivo identificado",
            "sem_motivo": "Sem motivo claro",
            "confuso": "Registro confuso",
        },
        "cat_cores": {
            "motivo": "#0ca30c",
            "sem_motivo": "#d03b3b",
            "confuso": "#52514e",
            "inconsistente": "#898781",
        },
        "anotacoes_map": anotacoes_map,
        "pausas_info": pausas_info,
    }


def escrever_arquivo_js(dados, caminho):
    """Escreve 'const DASHBOARD_DATA = {...};' de forma atomica (escreve em temp, depois renomeia)."""
    conteudo = "const DASHBOARD_DATA = " + json.dumps(dados, ensure_ascii=False) + ";\n"
    diretorio = os.path.dirname(os.path.abspath(caminho)) or "."
    fd, tmp_path = tempfile.mkstemp(dir=diretorio, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(conteudo)
        os.replace(tmp_path, caminho)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def main():
    usuario = os.environ.get("NXLITE_USER")
    senha = os.environ.get("NXLITE_PASS")
    if not usuario or not senha:
        print("Defina NXLITE_USER e NXLITE_PASS antes de rodar.", file=sys.stderr)
        sys.exit(1)

    caminho_saida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_data.js")
    opener = make_opener()
    try:
        fazer_login(opener, usuario, senha)
        dados = gerar_dashboard_data(opener, date.today())
        escrever_arquivo_js(dados, caminho_saida)
    except Exception as e:
        print(f"Falha ao atualizar os dados, dashboard_data.js NAO foi sobrescrito: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"OK: {caminho_saida} atualizado em {dados['gerado_em']}")
    print(f"  atrasados: {len(dados['atrasados']['vencidos'])}  finalizados: {len(dados['finalizados']['projetos'])}")


if __name__ == "__main__":
    main()
