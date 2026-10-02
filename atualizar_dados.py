# -*- coding: utf-8 -*-
"""Busca projetos de Implantacao/Reimplantacao no CRM nxlite e gera dashboard_data.js.

So leitura (GET). Nunca criar/alterar/apagar registros no CRM.
"""
from datetime import datetime

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
