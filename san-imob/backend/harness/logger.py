"""
harness/logger.py — Observabilidade de custo do arnês de IA (Problema 5).

Toda chamada ao LLM — classificador, geração de resposta reativa,
redação de sugestão proativa — deve terminar chamando log_api_call().
Sem isso, a estimativa de R$ 15-25/usuário/mês nunca é validada contra
a realidade: ela só vira número de verdade quando alguém consulta esta
tabela, e não dá pra reconstruir o histórico depois se não foi logado
desde o início.

Expansão (Arnês IA — novos intents e roteamento inteligente): cada
linha agora também guarda quanto essa chamada ECONOMIZOU por ter sido
roteada pra Haiku em vez de Sonnet — a "regra de ouro" do roteamento
(harness/router.py) só vira validação real de negócio se der pra somar
essa economia ao longo do mês (GET /api/metricas/economia).
"""
from db import get_connection

# Tabela de preços da Anthropic em BRL por 1.000 tokens. Única fonte de
# verdade de custo do sistema — atualizar aqui quando a Anthropic mudar
# preço ou o câmbio USD/BRL variar significativamente.
TABELA_PRECOS_BRL_POR_1K = {
    "claude-sonnet-5": {"input": 0.017, "output": 0.085, "cache_hit": 0.0017},
    "claude-haiku-4-5-20251001": {"input": 0.0013, "output": 0.0065, "cache_hit": 0.00013},
}

# Custo médio de uma chamada Sonnet típica do arnês (contexto completo
# + resposta), em BRL — usado só como referência pra estimar quanto
# uma chamada roteada pra Haiku "economizou" por não ter ido pro
# modelo caro. É uma média grosseira de propósito (não recalcula por
# tamanho real de contexto): o objetivo é dar uma ordem de grandeza pro
# painel de admin, não um valor contábil exato.
CUSTO_SONNET_ESTIMADO_BRL = 0.10


def calcular_custo(modelo, tokens_input, tokens_output, cache_hit_tokens=0):
    """
    Calcula o custo estimado em BRL de uma chamada ao LLM.

    tokens_input já inclui os tokens vindos do cache. cache_hit_tokens é
    o subconjunto deles cobrado com desconto — o restante
    (tokens_input - cache_hit_tokens) é cobrado à tarifa cheia de input.
    """
    precos = TABELA_PRECOS_BRL_POR_1K.get(modelo)
    if not precos:
        raise ValueError(f"Modelo sem tabela de preço cadastrada: {modelo}")

    tokens_input_normal = max(tokens_input - cache_hit_tokens, 0)
    custo_input = (tokens_input_normal / 1000) * precos["input"]
    custo_cache = (cache_hit_tokens / 1000) * precos["cache_hit"]
    custo_output = (tokens_output / 1000) * precos["output"]
    return round(custo_input + custo_cache + custo_output, 4)


def calcular_economia(modelo, custo_real_brl):
    """
    Estima quanto uma chamada roteada pra Haiku economizou por não ter
    ido pro Sonnet. Só faz sentido pra chamadas Haiku — uma chamada que
    já é Sonnet não "economizou" nada em relação a si mesma, e SQL puro
    (sem chamada de LLM nenhuma) nunca passa por log_api_call, então
    nem entra nessa conta.
    """
    if "haiku" not in modelo.lower():
        return 0.0
    return round(max(CUSTO_SONNET_ESTIMADO_BRL - custo_real_brl, 0.0), 4)


def log_api_call(dados):
    """
    Insere um registro em api_logs. `dados` é um dict com, no mínimo:
    imobiliaria_id, modelo, tokens_input, tokens_output. Opcionais:
    usuario_id, intencao, cache_hit_tokens, latencia_ms, aprovado.

    custo_estimado_brl e economia_estimada_brl são calculados aqui
    dentro (não recebidos de fora) — assim a fórmula de custo/economia
    fica centralizada num único lugar, e uma mudança de preço da
    Anthropic exige editar um arquivo só.

    Retorna o custo calculado, útil pra quem chamou exibir na hora.
    """
    custo = calcular_custo(
        dados["modelo"],
        dados["tokens_input"],
        dados["tokens_output"],
        dados.get("cache_hit_tokens", 0),
    )
    economia = calcular_economia(dados["modelo"], custo)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO api_logs (
                    imobiliaria_id, usuario_id, intencao, modelo,
                    tokens_input, tokens_output, cache_hit_tokens,
                    custo_estimado_brl, economia_estimada_brl,
                    latencia_ms, aprovado
                ) VALUES (
                    %(imobiliaria_id)s, %(usuario_id)s, %(intencao)s, %(modelo)s,
                    %(tokens_input)s, %(tokens_output)s, %(cache_hit_tokens)s,
                    %(custo_estimado_brl)s, %(economia_estimada_brl)s,
                    %(latencia_ms)s, %(aprovado)s
                )
                """,
                {
                    "imobiliaria_id": dados["imobiliaria_id"],
                    "usuario_id": dados.get("usuario_id"),
                    "intencao": dados.get("intencao"),
                    "modelo": dados["modelo"],
                    "tokens_input": dados["tokens_input"],
                    "tokens_output": dados["tokens_output"],
                    "cache_hit_tokens": dados.get("cache_hit_tokens", 0),
                    "custo_estimado_brl": custo,
                    "economia_estimada_brl": economia,
                    "latencia_ms": dados.get("latencia_ms"),
                    "aprovado": dados.get("aprovado"),
                },
            )
        conn.commit()
    finally:
        conn.close()

    return custo


def get_custo_mensal(imobiliaria_id, ano, mes):
    """
    Retorna o custo acumulado de API de uma imobiliária num mês
    específico — usado no painel de administração pra checar a margem
    real contra a estimativa de R$ 15-25/usuário/mês.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COALESCE(SUM(custo_estimado_brl), 0) AS custo_total_brl,
                    COUNT(*) AS total_chamadas,
                    COALESCE(SUM(tokens_input), 0) AS total_tokens_input,
                    COALESCE(SUM(tokens_output), 0) AS total_tokens_output,
                    COALESCE(SUM(cache_hit_tokens), 0) AS total_cache_hit_tokens
                FROM api_logs
                WHERE imobiliaria_id = %(imobiliaria_id)s
                  AND EXTRACT(YEAR FROM criado_em) = %(ano)s
                  AND EXTRACT(MONTH FROM criado_em) = %(mes)s
                """,
                {"imobiliaria_id": imobiliaria_id, "ano": ano, "mes": mes},
            )
            return cur.fetchone()
    finally:
        conn.close()


def get_economia_mensal(imobiliaria_id, ano, mes):
    """
    Retorna quanto foi economizado num mês por rotear chamadas pra
    Haiku/SQL em vez de Sonnet — usado em GET /api/metricas/economia
    pra validar, com número real, que o roteamento do router.py está
    funcionando (e não só "parece que está" pela leitura do código).

    total_chamadas_haiku conta só as chamadas que de fato geraram
    economia (modelo Haiku) — chamadas Sonnet entram no total geral de
    api_logs mas não neste recorte, já que por definição não
    "economizaram" nada.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COALESCE(SUM(economia_estimada_brl), 0) AS economia_total_brl,
                    COUNT(*) FILTER (WHERE economia_estimada_brl > 0) AS total_chamadas_haiku
                FROM api_logs
                WHERE imobiliaria_id = %(imobiliaria_id)s
                  AND EXTRACT(YEAR FROM criado_em) = %(ano)s
                  AND EXTRACT(MONTH FROM criado_em) = %(mes)s
                """,
                {"imobiliaria_id": imobiliaria_id, "ano": ano, "mes": mes},
            )
            return cur.fetchone()
    finally:
        conn.close()
