"""
harness/router.py — Roteamento inteligente do arnês (Arnês IA — novos
intents e roteamento inteligente).

Recebe o resultado já pronto de harness/intent_classifier.py e executa
o pipeline correto pra cada uma das 12 categorias. main.py chama só
`rotear_acao()` — não decide mais sozinho qual bloco rodar, qual query
disparar ou quando chamar Sonnet. Isso mantém a "regra de ouro" do
roteamento (SQL puro é de graça, Haiku resolve ação simples/navegação/
CRUD, Sonnet só entra pra análise complexa) num lugar só, em vez de
espalhada por handlers de endpoint diferentes.

Duas adaptações em relação ao prompt original, registradas aqui porque
mudam a assinatura/arquitetura do que foi pedido:

1. O prompt descreve `rotear_acao` como `async def` com chamadas
   `await db.fetchval(...)` (estilo asyncpg). O resto do backend inteiro
   é síncrono — psycopg2 (não há driver assíncrono no requirements.txt,
   nem app async em main.py). Escrever só este módulo como async
   exigiria misturar dois modelos de concorrência no mesmo processo
   sem nenhum ganho real (FastAPI já roda handlers síncronos numa
   threadpool). Este módulo é síncrono, seguindo o padrão já
   estabelecido em harness/context_builder.py e main.py.

2. O Bloco 3 (EDICAO_CADASTRO) do prompt mostra
   `"endpoint_confirmar": "PATCH /api/clientes/{id}"` como exemplo, mas
   a Parte 5 do mesmo prompt constrói um endpoint genérico
   (`POST /api/confirmar-edicao`). Usamos o endpoint que realmente
   existe, não o do exemplo — senão o frontend chamaria uma rota que
   nunca foi criada.

Duas categorias (ACAO_WHATSAPP, CONFIGURAR_META) não tinham bloco de
roteamento descrito no prompt — só apareciam na tabela de modelo
sugerido. Implementados aqui com o mesmo padrão de "buscar registro →
confirmar antes de agir" das demais categorias Haiku; ver os blocos
correspondentes abaixo para o raciocínio de cada um.
"""
import os
import re
import logging
import urllib.parse

import anthropic

from db import get_connection
from harness.context_builder import build_context
from harness.logger import log_api_call
from harness.intent_classifier import MODELO_CLASSIFICADOR

MODELO_PRINCIPAL = "claude-sonnet-5"

_log = logging.getLogger(__name__)


# ============================================================
# Campos editáveis por tipo de entidade (Parte 5 — confirmação de
# edição). Única fonte de verdade de "o que o Arnês pode alterar" —
# tanto o Bloco 3 (propor a edição) quanto confirmar_edicao() (executar
# depois de aprovado) consultam esta lista, nunca um campo livre.
# ============================================================
CAMPOS_EDITAVEIS = {
    "cliente": ["telefone", "email", "endereco", "observacoes", "corretor_id"],
    "imovel": ["preco", "valor_aluguel", "quartos", "banheiros", "suites",
               "vagas", "area_m2", "status", "exclusivo", "descricao"],
    "pipeline": ["etapa", "observacoes"],
}

TABELAS_POR_ENTIDADE = {
    "cliente": "clientes",
    "imovel": "imoveis",
    "pipeline": "pipeline",
}


# ============================================================
# Helpers de LLM — cada chamada real ao Anthropic loga a si mesma
# (harness/logger.py) e devolve só o texto; quem chama não lida com
# tokens/uso diretamente.
# ============================================================

def _montar_mensagens(historico, pergunta_final):
    """Monta a lista de mensagens no formato da API da Anthropic a partir
    do histórico enviado pelo frontend + a pergunta/prompt final."""
    mensagens = []
    for turno in historico or []:
        if turno.get("role") in ("user", "assistant") and turno.get("content"):
            mensagens.append({"role": turno["role"], "content": turno["content"]})
    mensagens.append({"role": "user", "content": pergunta_final})
    return mensagens


def _uso_da_resposta(resposta):
    """Extrai tokens de input/output/cache da resposta da Anthropic pra logging."""
    usage = resposta.usage
    return {
        "tokens_input": usage.input_tokens,
        "tokens_output": usage.output_tokens,
        "cache_hit_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
    }


def _extrair_texto_resposta(resposta):
    """
    Extrai o texto de uma resposta da Anthropic. `resposta.content[0]`
    nem sempre é o bloco de texto — com extended thinking, o primeiro
    bloco pode ser um ThinkingBlock (sem atributo .text), e o texto de
    verdade vem depois. Descoberto rodando uma pergunta real (BRIEFING)
    que sempre derrubava esta função com AttributeError. Percorre os
    blocos e pega o primeiro que for `type == "text"`, em vez de supor
    a posição.
    """
    for bloco in resposta.content:
        if getattr(bloco, "type", None) == "text":
            return bloco.text
    raise ValueError("Resposta da Anthropic não contém nenhum bloco de texto.")


def _logar_chamada(imobiliaria_id, intencao, modelo, uso):
    try:
        log_api_call({
            "imobiliaria_id": imobiliaria_id,
            "intencao": intencao,
            "modelo": modelo,
            "tokens_input": uso["tokens_input"],
            "tokens_output": uso["tokens_output"],
            "cache_hit_tokens": uso["cache_hit_tokens"],
        })
    except Exception:
        # Logging nunca pode derrubar a resposta ao corretor.
        pass


def _chamar_sonnet_com_contexto(imobiliaria_id, intencao, contexto_estavel, contexto_dinamico, pergunta, historico):
    """
    Chama Claude Sonnet com o contexto completo — usado pra GERAR_PROPOSTA,
    GERAR_MENSAGEM, RELATORIO, CONSULTA_MERCADO e BRIEFING (perguntas que
    exigem raciocínio sobre a carteira, não só formatar um resultado de SQL).

    contexto_estavel vai como bloco de system com cache_control ephemeral —
    é a aplicação real do prompt caching que o design do arnês previu.
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    pergunta_com_contexto = (
        f"{contexto_dinamico}\n\nPergunta do corretor: {pergunta}"
        if contexto_dinamico else pergunta
    )

    resposta = client.messages.create(
        model=MODELO_PRINCIPAL,
        max_tokens=1024,
        system=[{"type": "text", "text": contexto_estavel, "cache_control": {"type": "ephemeral"}}],
        messages=_montar_mensagens(historico, pergunta_com_contexto),
    )
    texto = _extrair_texto_resposta(resposta)
    _logar_chamada(imobiliaria_id, intencao, MODELO_PRINCIPAL, _uso_da_resposta(resposta))
    return texto


def _formatar_resultado_com_haiku(imobiliaria_id, intencao, contexto_estavel, pergunta, linhas, historico):
    """
    Usada por BUSCA_IMOVEL/BUSCA_LEAD: a detecção/filtro já aconteceu em
    SQL (determinístico), o modelo só formata o resultado em linguagem
    natural — nunca decide sozinho quais imóveis/leads existem. Antes
    desta expansão isso ia pro Sonnet; a regra de ouro do roteamento
    diz explicitamente pra nunca chamar Sonnet pelo que Haiku resolve,
    então trocou pro classificador mesmo (MODELO_CLASSIFICADOR).
    """
    if not linhas:
        dados_texto = "(nenhum resultado encontrado para os critérios da pergunta)"
    else:
        dados_texto = "\n".join(str(dict(linha)) for linha in linhas)

    prompt = (
        f"Dados recuperados do banco pra responder à pergunta do corretor:\n"
        f"{dados_texto}\n\n"
        f"Pergunta do corretor: {pergunta}\n\n"
        f"Formate uma resposta natural em português, citando os dados acima "
        f"de forma direta. Se não houver dados, diga isso claramente em vez "
        f"de inventar."
    )
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    resposta = client.messages.create(
        model=MODELO_CLASSIFICADOR,
        max_tokens=600,
        system=[{"type": "text", "text": contexto_estavel, "cache_control": {"type": "ephemeral"}}],
        messages=_montar_mensagens(historico, prompt),
    )
    texto = _extrair_texto_resposta(resposta)
    _logar_chamada(imobiliaria_id, intencao, MODELO_CLASSIFICADOR, _uso_da_resposta(resposta))
    return texto


# ============================================================
# Busca de entidades — usada por NAVEGACAO_DIRETA, EDICAO_CADASTRO e
# ACAO_WHATSAPP. Toda query tem WHERE imobiliaria_id = :id, sem
# exceção — é a regra de isolamento multi-tenant do schema inteiro.
# ============================================================

def _buscar_registros(imobiliaria_id, tipo_entidade, identificador, codigo_imovel):
    """
    Busca registros por identificador (nome, texto livre) ou código
    (só pra imóvel). Retorna lista de dicts — vazia se nada bateu,
    com mais de um item se a busca for ambígua. Quem chama decide o
    que fazer com 0/1/N resultados (ver _resolver_multiplicidade).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if tipo_entidade == "imovel":
                if codigo_imovel:
                    cur.execute(
                        """
                        SELECT id, codigo, tipo, bairro, preco, valor_aluguel,
                               status, quartos, suites, banheiros, vagas,
                               area_m2, exclusivo, descricao
                        FROM imoveis
                        WHERE imobiliaria_id = %(imobiliaria_id)s AND codigo ILIKE %(codigo)s
                        LIMIT 10
                        """,
                        {"imobiliaria_id": imobiliaria_id, "codigo": codigo_imovel},
                    )
                elif identificador:
                    cur.execute(
                        """
                        SELECT id, codigo, tipo, bairro, preco, valor_aluguel,
                               status, quartos, suites, banheiros, vagas,
                               area_m2, exclusivo, descricao
                        FROM imoveis
                        WHERE imobiliaria_id = %(imobiliaria_id)s
                          AND (codigo ILIKE %(busca)s OR bairro ILIKE %(busca)s OR tipo ILIKE %(busca)s)
                        ORDER BY dias_carteira ASC
                        LIMIT 10
                        """,
                        {"imobiliaria_id": imobiliaria_id, "busca": f"%{identificador}%"},
                    )
                else:
                    return []
            elif tipo_entidade == "proposta":
                if not identificador:
                    return []
                cur.execute(
                    """
                    SELECT pr.id, pr.valor, pr.vencimento, pr.status,
                           c.id AS cliente_id, c.nome AS cliente_nome
                    FROM propostas pr
                    JOIN clientes c ON c.id = pr.cliente_id
                    WHERE pr.imobiliaria_id = %(imobiliaria_id)s AND c.nome ILIKE %(busca)s
                    ORDER BY pr.criado_em DESC
                    LIMIT 10
                    """,
                    {"imobiliaria_id": imobiliaria_id, "busca": f"%{identificador}%"},
                )
            else:  # cliente / lead — mesma tabela `clientes`, rótulo de navegação difere
                if not identificador:
                    return []
                cur.execute(
                    """
                    SELECT id, nome, telefone, email, endereco, observacoes, corretor_id
                    FROM clientes
                    WHERE imobiliaria_id = %(imobiliaria_id)s AND nome ILIKE %(busca)s
                    ORDER BY nome
                    LIMIT 10
                    """,
                    {"imobiliaria_id": imobiliaria_id, "busca": f"%{identificador}%"},
                )
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _deep_link(tipo_entidade, registro):
    """
    Deep links por tipo de entidade. NOTA: o frontend hoje é HTML
    estático sem roteamento por id (clientes.html/imoveis.html são
    listagens, não há página de detalhe por registro nem leitura de
    query string ainda). Os links abaixo seguem o formato pedido no
    prompt e ficam prontos pro dia em que o frontend ganhar essas
    rotas — por ora, são dados que o frontend recebe mas ainda não
    consome de verdade. Registrado como gap conhecido, fora do escopo
    deste prompt (que é só backend).
    """
    if tipo_entidade == "lead":
        return f"/atendimento?lead={registro['id']}"
    if tipo_entidade == "cliente":
        return f"/clientes/{registro['id']}"
    if tipo_entidade == "imovel":
        return f"/imoveis/{registro['id']}"
    if tipo_entidade == "proposta":
        return f"/atendimento?lead={registro['cliente_id']}&aba=proposta"
    return "/"


def _deep_link_por_id(tipo_entidade, entidade_id):
    """Mesma ideia de _deep_link, mas a partir só do id (usado por
    confirmar_edicao, que não tem o registro completo em mãos)."""
    mapa = {
        "cliente": f"/clientes/{entidade_id}",
        "imovel": f"/imoveis/{entidade_id}",
        "pipeline": f"/atendimento?lead={entidade_id}",
    }
    return mapa.get(tipo_entidade, "/")


def _label(tipo_entidade, registro):
    if tipo_entidade in ("cliente", "lead"):
        return f"Cadastro de {registro['nome']}"
    if tipo_entidade == "imovel":
        return f"Imóvel {registro['codigo']} — {registro['tipo']} {registro['bairro']}"
    if tipo_entidade == "proposta":
        return f"Proposta de {registro['cliente_nome']}"
    return str(registro.get("id"))


def _montar_opcao_navegacao(registro, tipo_entidade):
    return {"id": str(registro["id"]), "label": _label(tipo_entidade, registro)}


def _resolver_multiplicidade(resultados, tipo_entidade):
    """
    0 resultados → pede pra reformular (não inventa registro).
    >1 resultado → devolve lista de opções pro corretor escolher.
    Exatamente 1 → devolve None, sinalizando "segue com resultados[0]".
    """
    if not resultados:
        return {
            "tipo": "navegacao_nao_encontrada",
            "tipo_entidade": tipo_entidade,
            "mensagem": "Não encontrei nenhum registro com esse nome ou código — tenta descrever de outro jeito?",
        }
    if len(resultados) > 1:
        return {
            "tipo": "navegacao_multiplos",
            "tipo_entidade": tipo_entidade,
            "opcoes": [_montar_opcao_navegacao(r, tipo_entidade) for r in resultados],
        }
    return None


# ============================================================
# Bloco 2 — NAVEGACAO_DIRETA
# ============================================================

def _bloco_navegacao_direta(imobiliaria_id, entidades):
    tipo_entidade = (entidades.get("tipo_entidade") or "cliente").lower()
    tipo_busca = "cliente" if tipo_entidade == "lead" else tipo_entidade

    resultados = _buscar_registros(
        imobiliaria_id, tipo_busca, entidades.get("identificador"), entidades.get("codigo_imovel")
    )
    resolucao = _resolver_multiplicidade(resultados, tipo_entidade)
    if resolucao is not None:
        return resolucao

    registro = resultados[0]
    return {
        "tipo": "navegacao",
        "deep_link": _deep_link(tipo_entidade, registro),
        "label": _label(tipo_entidade, registro),
        "acao": "redirecionar",
    }


# ============================================================
# Bloco 3 — EDICAO_CADASTRO
# ============================================================

def _bloco_edicao_cadastro(imobiliaria_id, entidades):
    """
    Respostas curtas e diretas de propósito (pedido explícito: Arnês
    objetivo, sem textos longos, mas mantendo tom cordial) — cada
    pergunta de volta pede só o que realmente falta, tudo numa única
    frase quando dá pra combinar, e sempre lembra que só altera
    exatamente o que o corretor confirmar (edição é uma escrita real no
    banco, não é reversível por conta própria).
    """
    tipo_entidade_raw = entidades.get("tipo_entidade")

    # Pergunta genérica demais pra saber qual cadastro ("consegue alterar
    # um cadastro?") — antes disto, o classificador simplesmente não
    # extrai tipo_entidade nenhum. Em vez de assumir "cliente" por
    # default (o que fazia o Arnês silenciosamente buscar/editar o tipo
    # errado de registro), pergunta de volta qual entidade o corretor
    # quer alterar.
    if not tipo_entidade_raw:
        return {
            "tipo": "confirmacao_edicao",
            "mensagem": "Claro. Qual cadastro: cliente, imóvel ou proposta?",
            "aguardando": "entidade",
        }

    tipo_entidade = tipo_entidade_raw.lower()
    tipo_busca = "cliente" if tipo_entidade == "lead" else tipo_entidade
    identificador = entidades.get("identificador") or entidades.get("codigo_imovel")
    campo = entidades.get("campo")
    novo_valor = entidades.get("novo_valor")

    falta_identificador = not identificador
    falta_campo = not campo or novo_valor is None

    if falta_identificador and falta_campo:
        return {
            "tipo": "confirmacao_edicao",
            "mensagem": f"Claro. Qual {tipo_busca} e o que quer alterar? Só mudo exatamente o que você escrever.",
            "aguardando": "identificador_e_campo",
        }

    if falta_identificador:
        return {
            "tipo": "confirmacao_edicao",
            "mensagem": f"Qual {tipo_busca} você quer alterar?",
            "aguardando": "identificador",
        }

    if falta_campo:
        return {
            "tipo": "confirmacao_edicao",
            "mensagem": "O que quer alterar e para qual valor? Só mudo exatamente o que você escrever.",
            "aguardando": "campo",
        }

    if campo not in CAMPOS_EDITAVEIS.get(tipo_busca, []):
        return {
            "erro": "Esse campo não pode ser editado pelo Arnês por segurança. Acesse o cadastro completo para alterá-lo.",
            "deep_link": None,
        }

    resultados = _buscar_registros(
        imobiliaria_id, tipo_busca, entidades.get("identificador"), entidades.get("codigo_imovel")
    )
    resolucao = _resolver_multiplicidade(resultados, tipo_entidade)
    if resolucao is not None:
        return resolucao

    registro = resultados[0]
    nome_registro = registro.get("nome") or registro.get("codigo")
    return {
        "tipo": "confirmacao_edicao",
        "entidade": tipo_busca,
        "nome": nome_registro,
        "campo": campo,
        "valor_atual": registro.get(campo),
        "novo_valor": novo_valor,
        "mensagem": f'Confirma trocar {campo} de {nome_registro} para "{novo_valor}"?',
        "endpoint_confirmar": "POST /api/confirmar-edicao",
        "payload": {
            "tipo_entidade": tipo_busca,
            "entidade_id": str(registro["id"]),
            "campo": campo,
            "novo_valor": novo_valor,
        },
    }


def confirmar_edicao(imobiliaria_id, tipo_entidade, entidade_id, campo, novo_valor, usuario_id=None):
    """
    Executa de fato a edição já confirmada pelo gestor no card do
    Bloco 3. Só é chamada pelo endpoint POST /api/confirmar-edicao,
    nunca direto do pipeline de chat — o Bloco 3 só PROPÕE a edição,
    quem efetivamente muda o banco é este endpoint, depois do clique
    de confirmação na interface. É esse "depois do clique" que conta
    como aceite — a linha em historico_edicoes só existe se passar por
    aqui, nunca é criada no momento em que o Arnês só propõe.

    usuario_id é opcional e fica nulo até o sistema ter login real —
    ver comentário da tabela em schema_v2.sql.

    `campo` entra numa f-string do SQL (nome de coluna não pode ser
    parametrizado como valor comum) — seguro aqui porque só chega
    até aqui depois de validado contra CAMPOS_EDITAVEIS, uma lista
    fechada de nomes de coluna reais; `novo_valor` continua
    parametrizado normalmente.
    """
    if campo not in CAMPOS_EDITAVEIS.get(tipo_entidade, []):
        return {
            "erro": "Esse campo não pode ser editado pelo Arnês por segurança. Acesse o cadastro completo para alterá-lo.",
            "deep_link": _deep_link_por_id(tipo_entidade, entidade_id),
        }

    tabela = TABELAS_POR_ENTIDADE.get(tipo_entidade)
    if not tabela:
        return {"erro": f"Tipo de entidade desconhecido: {tipo_entidade}", "deep_link": None}

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Busca o valor atual ANTES de sobrescrever — é o único jeito
            # de guardar valor_anterior no histórico; se o registro não
            # existir nesta imobiliária, nem tenta o UPDATE.
            cur.execute(
                f"SELECT {campo} AS valor_atual FROM {tabela} WHERE id = %(id)s AND imobiliaria_id = %(imobiliaria_id)s",
                {"id": entidade_id, "imobiliaria_id": imobiliaria_id},
            )
            linha_atual = cur.fetchone()
            if not linha_atual:
                return {"erro": "Registro não encontrado nesta imobiliária.", "deep_link": None}
            valor_anterior = linha_atual["valor_atual"]

            cur.execute(
                f"""
                UPDATE {tabela}
                SET {campo} = %(novo_valor)s
                WHERE id = %(id)s AND imobiliaria_id = %(imobiliaria_id)s
                """,
                {"novo_valor": novo_valor, "id": entidade_id, "imobiliaria_id": imobiliaria_id},
            )

            cur.execute(
                """
                INSERT INTO historico_edicoes (
                    imobiliaria_id, usuario_id, tipo_entidade, entidade_id,
                    campo, valor_anterior, valor_novo, origem
                ) VALUES (
                    %(imobiliaria_id)s, %(usuario_id)s, %(tipo_entidade)s, %(entidade_id)s,
                    %(campo)s, %(valor_anterior)s, %(valor_novo)s, 'arnes_ia'
                )
                """,
                {
                    "imobiliaria_id": imobiliaria_id,
                    "usuario_id": usuario_id,
                    "tipo_entidade": tipo_entidade,
                    "entidade_id": entidade_id,
                    "campo": campo,
                    "valor_anterior": str(valor_anterior) if valor_anterior is not None else None,
                    "valor_novo": str(novo_valor),
                },
            )
        conn.commit()
    finally:
        conn.close()

    return {"ok": True, "tipo_entidade": tipo_entidade, "campo": campo, "novo_valor": novo_valor}


# ============================================================
# Bloco 4 — CRIACAO_CADASTRO
# ============================================================

_CAMPOS_INTERNOS_ENTIDADE = {"tipo_entidade", "identificador", "campo", "novo_valor", "codigo_imovel"}


def _bloco_criacao_cadastro(entidades):
    tipo_entidade = (entidades.get("tipo_entidade") or "cliente").lower()
    deep_links = {"cliente": "/clientes/novo", "lead": "/clientes/novo", "imovel": "/imoveis/novo"}
    deep_link = deep_links.get(tipo_entidade, "/clientes/novo")

    # Qualquer entidade extraída pelo classificador que não seja um dos
    # campos de controle (tipo_entidade, campo, etc.) vira campo
    # pré-preenchido no formulário — na prática, raramente vem alguma,
    # já que "cria um novo cliente" normalmente não traz detalhe nenhum.
    campos_prefilled = {
        chave: valor for chave, valor in entidades.items()
        if chave not in _CAMPOS_INTERNOS_ENTIDADE and valor is not None
    }

    mensagem = (
        "Abri o formulário de novo cadastro com os dados que você informou."
        if campos_prefilled else
        "Abri o formulário de novo cadastro pra você preencher."
    )

    return {
        "tipo": "abrir_formulario",
        "deep_link": deep_link,
        "campos_prefilled": campos_prefilled,
        "mensagem": mensagem,
    }


# ============================================================
# Bloco 5 — BUSCA_IMOVEL / BUSCA_LEAD (SQL determinístico + Haiku)
# ============================================================

def _query_imoveis_por_entidades(imobiliaria_id, entidades):
    """
    Monta uma query determinística de imóveis a partir das entidades que
    o classificador conseguiu extrair. Reconhece preco_max/quartos/bairro
    — o que não vier na pergunta simplesmente não vira filtro, em vez de
    a query falhar.
    """
    condicoes = ["imobiliaria_id = %(imobiliaria_id)s", "status = 'ativo'"]
    params = {"imobiliaria_id": imobiliaria_id}

    preco_max = entidades.get("preco_max")
    if preco_max:
        condicoes.append("preco <= %(preco_max)s")
        params["preco_max"] = preco_max

    quartos = entidades.get("quartos")
    if quartos:
        condicoes.append("quartos = %(quartos)s")
        params["quartos"] = quartos

    bairro = entidades.get("bairro")
    if bairro:
        condicoes.append("bairro ILIKE %(bairro)s")
        params["bairro"] = f"%{bairro}%"

    query = f"""
        SELECT codigo, tipo, bairro, preco, status, quartos, dias_carteira, exclusivo
        FROM imoveis
        WHERE {' AND '.join(condicoes)}
        ORDER BY dias_carteira ASC
        LIMIT 20
    """
    return query, params


def _query_leads_por_entidades(imobiliaria_id, entidades):
    """Query determinística de leads — ranking por score é SQL, não LLM (ver análise crítica do arnês)."""
    limite = entidades.get("limite") or 5
    query = """
        SELECT c.id, c.nome, c.score_fechamento, c.temperatura, c.origem, c.telefone,
               EXTRACT(DAY FROM NOW() - c.ultimo_contato)::int AS ultimo_contato_dias,
               p.etapa
        FROM clientes c
        LEFT JOIN pipeline p ON p.cliente_id = c.id
        WHERE c.imobiliaria_id = %(imobiliaria_id)s
        ORDER BY c.score_fechamento DESC
        LIMIT %(limite)s
    """
    return query, {"imobiliaria_id": imobiliaria_id, "limite": limite}


def _bloco_busca(imobiliaria_id, intencao, entidades, pergunta, historico):
    if intencao == "BUSCA_IMOVEL":
        query, params = _query_imoveis_por_entidades(imobiliaria_id, entidades)
    else:
        query, params = _query_leads_por_entidades(imobiliaria_id, entidades)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            linhas = cur.fetchall()
    finally:
        conn.close()

    contexto = build_context(imobiliaria_id, intencao)
    texto = _formatar_resultado_com_haiku(
        imobiliaria_id, intencao, contexto["contexto_estavel"], pergunta, linhas, historico
    )

    resultado = {"tipo": "resposta", "resposta": texto}

    if intencao == "BUSCA_LEAD" and linhas:
        topo = linhas[0]
        if (topo.get("score_fechamento") or 0) >= 80 and topo.get("telefone"):
            primeiro_nome = topo["nome"].split(" ")[0]
            resultado["acao_sugerida"] = {
                "tipo": "ENVIAR_WHATSAPP",
                "cliente_id": str(topo["id"]),
                "mensagem_sugerida": (
                    f"Olá {primeiro_nome}, aqui é da Soma Imob! Vi que você "
                    f"tem bastante interesse e queria saber se ainda posso "
                    f"te ajudar a avançar."
                ),
            }
    return resultado


# ============================================================
# ACAO_WHATSAPP — sem bloco descrito no prompt original (só aparecia
# na tabela de modelo sugerido). Segue o mesmo padrão de
# "buscar → propor, nunca enviar sozinho" das outras categorias Haiku,
# e do scanner proativo (jobs/proactive_scanner.py): o arnês nunca
# dispara WhatsApp de fato, só monta o link wa.me pro corretor
# confirmar o envio manualmente.
# ============================================================

def _bloco_acao_whatsapp(imobiliaria_id, entidades):
    resultados = _buscar_registros(imobiliaria_id, "cliente", entidades.get("identificador"), None)
    resolucao = _resolver_multiplicidade(resultados, "cliente")
    if resolucao is not None:
        return resolucao

    cliente = resultados[0]
    if not cliente.get("telefone"):
        return {
            "tipo": "erro_whatsapp",
            "mensagem": f"{cliente['nome']} não tem telefone cadastrado — não dá pra montar o link do WhatsApp.",
        }

    primeiro_nome = cliente["nome"].split(" ")[0]
    mensagem_sugerida = (
        f"Olá {primeiro_nome}, aqui é da Soma Imob! Vi que você tem interesse "
        f"e queria saber se ainda posso te ajudar a avançar."
    )
    telefone_limpo = "".join(ch for ch in cliente["telefone"] if ch.isdigit())

    return {
        "tipo": "confirmacao_whatsapp",
        "cliente_id": str(cliente["id"]),
        "nome": cliente["nome"],
        "mensagem_sugerida": mensagem_sugerida,
        "whatsapp_url": f"https://wa.me/55{telefone_limpo}?text={urllib.parse.quote(mensagem_sugerida)}",
    }


# ============================================================
# CONFIGURAR_META — também sem bloco descrito no prompt original.
# Não existe tabela de metas no schema: a persistência real hoje é
# 100% frontend (metas.html, via localStorage — ver o painel "Ajustar
# metas com o Arnês" já construído lá, com o mesmo parsing por
# palavra-chave). Este bloco devolve uma proposta no mesmo formato que
# aquele painel já sabe interpretar, pra quando o chat principal (não
# só o painel dedicado de metas.html) também precisar entender pedidos
# de ajuste de meta. Criar uma tabela de metas de verdade é escopo de
# um prompt de backend próprio, não desta expansão de roteamento.
# ============================================================

def _extrair_numeros(texto):
    return re.findall(r"\d+", texto)


def _bloco_configurar_meta(entidades, pergunta):
    numeros = _extrair_numeros(pergunta)
    novo_valor = int(numeros[-1]) if numeros else None

    p = pergunta.lower()
    if "capta" in p:
        campo_meta = "captacoes"
    elif "comiss" in p:
        campo_meta = "comissao"
    else:
        campo_meta = "vendas"

    mensagem = f"Entendi que você quer ajustar a meta de {campo_meta}"
    if novo_valor is not None:
        mensagem += f" para {novo_valor}"
    mensagem += ". Confirma no painel de metas pra eu salvar."

    return {
        "tipo": "proposta_meta",
        "campo_meta": campo_meta,
        "novo_valor": novo_valor,
        "mensagem": mensagem,
    }


# ============================================================
# Bloco 6 — GERAR_PROPOSTA / GERAR_MENSAGEM / RELATORIO /
# CONSULTA_MERCADO / BRIEFING (contexto completo + Sonnet)
# ============================================================

def _bloco_geracao_sonnet(imobiliaria_id, intencao, pergunta, historico):
    contexto = build_context(imobiliaria_id, intencao)
    texto = _chamar_sonnet_com_contexto(
        imobiliaria_id, intencao,
        contexto["contexto_estavel"], contexto["contexto_dinamico"],
        pergunta, historico,
    )
    return {"tipo": "resposta", "resposta": texto}


# ============================================================
# Bloco 7 — OUTRO (Sonnet com contexto mínimo, sem carteira completa)
# ============================================================

def _bloco_outro(imobiliaria_id, pergunta, historico):
    contexto = build_context(imobiliaria_id, "OUTRO")
    texto = _chamar_sonnet_com_contexto(
        imobiliaria_id, "OUTRO",
        contexto["contexto_estavel"], "",  # sem contexto_dinamico de propósito
        pergunta, historico,
    )
    return {"tipo": "resposta", "resposta": texto}


# ============================================================
# Entrada principal — main.py chama só isto.
# ============================================================

def rotear_acao(classificacao, imobiliaria_id, pergunta, historico, fonte):
    """
    Recebe a classificação (harness/intent_classifier.classify_intent),
    o tenant, a pergunta original, o histórico da conversa e a fonte
    ('texto' | 'voz'), e devolve o resultado já processado pra
    main.py repassar ao frontend.
    """
    intencao = classificacao["intencao"]
    entidades = classificacao.get("entidades", {}) or {}

    # Bloco 1 — restrição de voz, verificada ANTES de qualquer outro
    # processamento: nunca vale gastar uma chamada de modelo ou uma
    # query de banco só pra descobrir depois que a ação é bloqueada.
    if classificacao.get("requer_texto") and fonte == "voz":
        _log.info(f"Intent: {intencao} → Pipeline: restricao_voz")
        return {
            "tipo": "restricao_voz",
            "mensagem": "Para alterações de cadastro, digite o comando por segurança. Voz está disponível apenas para consultas.",
            "acao": None,
            "intencao": intencao,
        }

    if intencao == "NAVEGACAO_DIRETA":
        pipeline_ativado = "navegacao_direta"
        resultado = _bloco_navegacao_direta(imobiliaria_id, entidades)
    elif intencao == "EDICAO_CADASTRO":
        pipeline_ativado = "edicao_cadastro"
        resultado = _bloco_edicao_cadastro(imobiliaria_id, entidades)
    elif intencao == "CRIACAO_CADASTRO":
        pipeline_ativado = "criacao_cadastro"
        resultado = _bloco_criacao_cadastro(entidades)
    elif intencao == "CONFIGURAR_META":
        pipeline_ativado = "configurar_meta"
        resultado = _bloco_configurar_meta(entidades, pergunta)
    elif intencao == "ACAO_WHATSAPP":
        pipeline_ativado = "acao_whatsapp"
        resultado = _bloco_acao_whatsapp(imobiliaria_id, entidades)
    elif intencao in ("BUSCA_IMOVEL", "BUSCA_LEAD"):
        pipeline_ativado = "busca_sql_haiku"
        resultado = _bloco_busca(imobiliaria_id, intencao, entidades, pergunta, historico)
    elif intencao == "OUTRO":
        pipeline_ativado = "outro_sonnet_minimo"
        resultado = _bloco_outro(imobiliaria_id, pergunta, historico)
    else:  # GERAR_PROPOSTA, GERAR_MENSAGEM, RELATORIO, CONSULTA_MERCADO, BRIEFING
        pipeline_ativado = "geracao_sonnet"
        resultado = _bloco_geracao_sonnet(imobiliaria_id, intencao, pergunta, historico)

    _log.info(f"Intent: {intencao} → Pipeline: {pipeline_ativado}")
    resultado.setdefault("intencao", intencao)
    return resultado
