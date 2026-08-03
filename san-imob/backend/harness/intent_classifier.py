"""
harness/intent_classifier.py — Classificador de intenção (Problema 3).

Roda ANTES de qualquer chamada ao LLM principal. Usa Claude Haiku —
classificar intenção é categorização simples, não exige o modelo caro
que faz raciocínio sobre a carteira inteira.

Sem essa etapa, o pipeline não sabe se deve rodar uma query SQL direta
(ex: BUSCA_IMOVEL por preço/bairro) ou montar o contexto completo e
chamar o modelo principal (ex: GERAR_PROPOSTA) — ou chama o modelo caro
pra tudo (caro demais) ou nada funciona de forma previsível.

Expansão (Arnês IA — novos intents e roteamento inteligente): de 7 para
12 categorias, agora cobrindo navegação direta, edição/criação de
cadastro e configuração de metas — sempre roteadas para Haiku ou SQL,
nunca Sonnet. `modelo_sugerido` e `requer_texto` NÃO vêm do LLM: são
atribuídos aqui em código, de forma determinística, a partir da
intenção já classificada — a "regra de ouro" do roteamento não pode
depender do LLM lembrar de segui-la a cada chamada.
"""
import os
import re
import json
import anthropic

from harness.logger import log_api_call

# O Haiku às vezes envolve o JSON numa cerca de código markdown
# (```json ... ```) mesmo quando instruído a responder só com JSON puro
# — descoberto rodando uma pergunta real de teste ("Como foi a semana
# de vendas?"), que veio corretamente classificada como RELATORIO mas
# falhava o json.loads() e caía silenciosamente em OUTRO. Remove a
# cerca antes de parsear, sem depender do modelo nunca mais errar isso.
_CERCA_MARKDOWN = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _limpar_cerca_markdown(texto):
    return _CERCA_MARKDOWN.sub("", texto.strip()).strip()


def _extrair_texto_resposta(resposta):
    """
    Extrai o texto de uma resposta da Anthropic sem supor que
    content[0] seja sempre o bloco de texto — com extended thinking,
    o primeiro bloco pode ser um ThinkingBlock (sem atributo .text).
    Ver harness/router.py para o mesmo helper (duplicado de propósito,
    cada módulo permanece independente).
    """
    for bloco in resposta.content:
        if getattr(bloco, "type", None) == "text":
            return bloco.text
    raise ValueError("Resposta da Anthropic não contém nenhum bloco de texto.")

MODELO_CLASSIFICADOR = "claude-haiku-4-5-20251001"

CATEGORIAS = [
    # Só Haiku (nunca Sonnet)
    "NAVEGACAO_DIRETA",
    "EDICAO_CADASTRO",
    "CRIACAO_CADASTRO",
    "CONFIGURAR_META",
    "ACAO_WHATSAPP",
    # SQL + Haiku (resultado simples)
    "BUSCA_IMOVEL",
    "BUSCA_LEAD",
    # Contexto completo + Sonnet
    "GERAR_PROPOSTA",
    "GERAR_MENSAGEM",
    "RELATORIO",
    "CONSULTA_MERCADO",
    "BRIEFING",
    "OUTRO",
]

# Regra de ouro do roteamento: SQL puro é de graça, Haiku resolve ação
# simples/navegação/CRUD/classificação, Sonnet só entra pra análise
# complexa ou geração de texto longo. Este dict é a fonte única de
# verdade — nunca decidir o modelo em outro lugar do pipeline.
MODELO_SUGERIDO_POR_INTENCAO = {
    "NAVEGACAO_DIRETA": "haiku",
    "EDICAO_CADASTRO": "haiku",
    "CRIACAO_CADASTRO": "haiku",
    "CONFIGURAR_META": "haiku",
    "ACAO_WHATSAPP": "haiku",
    "BUSCA_IMOVEL": "haiku",
    "BUSCA_LEAD": "haiku",
    "GERAR_PROPOSTA": "sonnet",
    "GERAR_MENSAGEM": "sonnet",
    "RELATORIO": "sonnet",
    "CONSULTA_MERCADO": "sonnet",
    "BRIEFING": "sonnet",
    "OUTRO": "sonnet",
}

# Intenções que alteram dado (edição/criação/configuração) exigem texto —
# por segurança, voz nunca dispara uma escrita no banco sem o gestor
# digitar o comando. Consultas e navegação continuam liberadas por voz.
INTENCOES_QUE_EXIGEM_TEXTO = {
    "EDICAO_CADASTRO",
    "CRIACAO_CADASTRO",
    "CONFIGURAR_META",
}

SYSTEM_PROMPT = """Você classifica a intenção de perguntas de corretores de imóveis
em um CRM brasileiro chamado Soma Imob, cujo assistente de IA se chama
Arnês IA. Responda SOMENTE com um JSON válido, sem nenhum texto
adicional antes ou depois, no formato:

{"intencao": "<uma das categorias>", "confianca": <0 a 1>, "entidades": {}}

Categorias possíveis: NAVEGACAO_DIRETA, EDICAO_CADASTRO, CRIACAO_CADASTRO,
CONFIGURAR_META, ACAO_WHATSAPP, BUSCA_IMOVEL, BUSCA_LEAD, GERAR_PROPOSTA,
GERAR_MENSAGEM, RELATORIO, CONSULTA_MERCADO, BRIEFING, OUTRO

- NAVEGACAO_DIRETA: quer abrir um registro específico (cadastro, imóvel,
  proposta) pelo nome ou código. Ex: "abre o cadastro do Samuel",
  "mostra o imóvel AP047", "vai para a proposta da família Souza"
- EDICAO_CADASTRO: quer alterar um campo de um registro que já existe —
  incluindo perguntas genéricas sobre SER CAPAZ de editar um cadastro,
  mesmo sem dizer qual registro, campo ou valor. Ex: "muda o telefone do
  Samuel para 19 99999-1234", "acrescenta um banheiro no AP047",
  "atualiza o valor do aluguel da CA012 para R$ 3.200", "consegue
  alterar um cadastro?", "dá pra editar um cliente?", "você edita
  cadastro de imóvel?"
- CRIACAO_CADASTRO: quer criar um registro novo. Ex: "cria um novo
  cliente", "cadastra um imóvel novo", "adiciona um lead"
- CONFIGURAR_META: quer definir ou ajustar uma meta. Ex: "muda minha
  meta de vendas para 25", "quero bater R$ 250k de comissão esse mês"
- ACAO_WHATSAPP: quer enviar mensagem via WhatsApp agora. Ex: "manda
  mensagem pro Marcos", "contata a Fernanda"
- BUSCA_IMOVEL: quer encontrar imóveis por critério (preço, bairro,
  quartos). Ex: "imóvel 2 quartos até 500k", "apartamentos no centro"
- BUSCA_LEAD: quer informação sobre clientes/leads (score, temperatura,
  contato). Ex: "qual cliente tem mais chance de fechar?"
- GERAR_PROPOSTA: quer gerar um documento de proposta comercial
- GERAR_MENSAGEM: quer redigir uma comunicação personalizada (sem
  necessariamente enviar)
- RELATORIO: quer um resumo/análise da operação. Ex: "como foi a
  semana?", "resumo do mês", "performance dos corretores"
- CONSULTA_MERCADO: quer inteligência de mercado. Ex: "como está o
  preço de apartamentos em Valinhos?", "qual portal traz mais
  resultado?", "meu imóvel está bem precificado?"
- BRIEFING: pede um briefing do dia ou da situação atual. Ex: "o que
  tenho hoje?", "me atualiza", "o que está urgente?"
- OUTRO: não se encaixa em nenhuma categoria acima

Preencha "entidades" só com o que a pergunta deixar explícito — nunca
invente informação que a pergunta não contém. Estrutura de "entidades"
por categoria (todos os campos são opcionais, preencha só o que estiver
explícito):

- NAVEGACAO_DIRETA / EDICAO_CADASTRO: "tipo_entidade" (cliente | imovel
  | proposta | lead), "identificador" (nome ou texto que identifica o
  registro), "codigo_imovel" (se a referência for por código tipo AP047)
- EDICAO_CADASTRO, além do acima: "campo" (nome do campo a alterar) e
  "novo_valor" (valor novo, como texto). Preencha "tipo_entidade" sempre
  que der pra inferir pelo campo mencionado, mesmo que a palavra "cliente"
  ou "imóvel" não apareça na pergunta (ex: telefone/email/endereço são
  campos de cliente; preço/quartos/banheiros/vagas são campos de imóvel).
  Só deixe "tipo_entidade" vazio quando a pergunta for genérica demais
  pra saber (ex: "consegue alterar um cadastro?")
- BUSCA_IMOVEL: "preco_max" (número, sem formatação), "quartos"
  (número), "bairro" (texto)
- BUSCA_LEAD: "limite" (número de resultados pedidos, padrão implícito
  é 5 se não especificado)

Nunca preencha "modelo_sugerido" ou "requer_texto" — esses campos são
calculados fora do seu escopo, não faça parte da sua resposta."""


def classify_intent(pergunta, imobiliaria_id=None):
    """
    Classifica a intenção de `pergunta` usando Claude Haiku.

    `imobiliaria_id` é opcional só pra não quebrar chamadores que ainda
    não o repassam, mas main.py SEMPRE deve passar o tenant real — sem
    ele o custo desta chamada não é logado (api_logs.imobiliaria_id é
    NOT NULL, e tentar inserir com None falha silenciosamente aqui,
    de propósito, pra nunca derrubar a classificação por causa do log).

    Retorna:
    {
      "intencao": str,
      "confianca": float,
      "modelo_sugerido": "haiku" | "sonnet",
      "requer_texto": bool,   # True = bloquear execução por voz
      "entidades": dict,
    }

    modelo_sugerido e requer_texto são atribuídos deterministicamente a
    partir de MODELO_SUGERIDO_POR_INTENCAO / INTENCOES_QUE_EXIGEM_TEXTO
    — nunca confiar no LLM pra essa parte (ver cabeçalho do módulo).

    Em caso de erro de parsing ou de API, retorna intencao="OUTRO" com
    confianca 0 — o pipeline principal deve tratar isso como "não deu
    pra classificar, peça pro corretor reformular", nunca travar.

    Loga a própria chamada Haiku em api_logs — todo LLM chamado no
    arnês se loga (ver harness/logger.py), inclusive o classificador,
    que antes desta expansão não tinha seu custo registrado em lugar
    nenhum.
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    try:
        resposta = client.messages.create(
            model=MODELO_CLASSIFICADOR,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": pergunta}],
        )
        texto = _limpar_cerca_markdown(_extrair_texto_resposta(resposta))
        resultado = json.loads(texto)
    except (json.JSONDecodeError, IndexError, anthropic.APIError) as erro:
        return {
            "intencao": "OUTRO",
            "confianca": 0.0,
            "modelo_sugerido": MODELO_SUGERIDO_POR_INTENCAO["OUTRO"],
            "requer_texto": "OUTRO" in INTENCOES_QUE_EXIGEM_TEXTO,
            "entidades": {},
            "erro": str(erro),
        }

    if resultado.get("intencao") not in CATEGORIAS:
        resultado["intencao"] = "OUTRO"
        resultado["confianca"] = 0.0

    intencao = resultado["intencao"]
    resultado["modelo_sugerido"] = MODELO_SUGERIDO_POR_INTENCAO[intencao]
    resultado["requer_texto"] = intencao in INTENCOES_QUE_EXIGEM_TEXTO
    resultado.setdefault("entidades", {})

    if imobiliaria_id is not None:
        try:
            usage = resposta.usage
            log_api_call({
                "imobiliaria_id": imobiliaria_id,
                "intencao": intencao,
                "modelo": MODELO_CLASSIFICADOR,
                "tokens_input": usage.input_tokens,
                "tokens_output": usage.output_tokens,
                "cache_hit_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
            })
        except Exception:
            # Logging nunca pode derrubar a classificação em si.
            pass

    return resultado


# ============================================================
# Exemplos de teste — 3 por categoria. Usar num teste real (pytest)
# antes de considerar o classificador pronto pra produção; hoje é só
# documentação de comportamento esperado.
# ============================================================
EXEMPLOS_TESTE = [
    # NAVEGACAO_DIRETA
    ("Abre o cadastro do Samuel", "NAVEGACAO_DIRETA"),
    ("Mostra o imóvel AP047", "NAVEGACAO_DIRETA"),
    ("Vai para a proposta da família Souza", "NAVEGACAO_DIRETA"),
    # EDICAO_CADASTRO
    ("Muda o telefone do Samuel para 19 99999-1234", "EDICAO_CADASTRO"),
    ("Acrescenta um banheiro no AP047", "EDICAO_CADASTRO"),
    ("Atualiza o valor do aluguel da CA012 para R$ 3.200", "EDICAO_CADASTRO"),
    ("Consegue alterar um cadastro?", "EDICAO_CADASTRO"),
    # CRIACAO_CADASTRO
    ("Cria um novo cliente", "CRIACAO_CADASTRO"),
    ("Cadastra um imóvel novo", "CRIACAO_CADASTRO"),
    ("Adiciona um lead chamado João Silva", "CRIACAO_CADASTRO"),
    # CONFIGURAR_META
    ("Muda minha meta de vendas para 25", "CONFIGURAR_META"),
    ("Quero bater R$ 250 mil de comissão esse mês", "CONFIGURAR_META"),
    ("Aumenta a meta de captações pra 10", "CONFIGURAR_META"),
    # ACAO_WHATSAPP
    ("Manda mensagem pro Marcos Andrade agora", "ACAO_WHATSAPP"),
    ("Contata a Fernanda pelo WhatsApp", "ACAO_WHATSAPP"),
    ("Pode avisar a Camila Rocha que a proposta foi aprovada?", "ACAO_WHATSAPP"),
    # BUSCA_IMOVEL
    ("Tem apartamento de 2 quartos até 500 mil na Palmeiras?", "BUSCA_IMOVEL"),
    ("Quais imóveis combinam com família com 2 filhos, perto de escola?", "BUSCA_IMOVEL"),
    ("Mostra as casas de 3 quartos ativas no Centro", "BUSCA_IMOVEL"),
    # BUSCA_LEAD
    ("Qual cliente tem mais chance de fechar essa semana?", "BUSCA_LEAD"),
    ("Quais leads estão sem contato há mais de 7 dias?", "BUSCA_LEAD"),
    ("Como está o score do Marcos Andrade?", "BUSCA_LEAD"),
    # GERAR_PROPOSTA
    ("Monta proposta para o ap. Palmeiras, financiamento 70%, entrada 30%", "GERAR_PROPOSTA"),
    ("Gera uma proposta para a Fernanda Lima na cobertura do Centro", "GERAR_PROPOSTA"),
    ("Preciso de uma proposta com condições de pagamento à vista", "GERAR_PROPOSTA"),
    # GERAR_MENSAGEM
    ("Escreve uma mensagem de atualização pro proprietário Raimundo", "GERAR_MENSAGEM"),
    ("Redige um texto de follow-up pra Juliana Prado", "GERAR_MENSAGEM"),
    ("Monta uma mensagem explicando o financiamento Caixa pro cliente", "GERAR_MENSAGEM"),
    # RELATORIO
    ("Como foi a semana de vendas?", "RELATORIO"),
    ("Quantas visitas fizemos esse mês?", "RELATORIO"),
    ("Me dá um resumo do pipeline atual", "RELATORIO"),
    # CONSULTA_MERCADO
    ("Como está o preço de apartamentos em Valinhos?", "CONSULTA_MERCADO"),
    ("Qual portal traz mais resultado?", "CONSULTA_MERCADO"),
    ("Meu imóvel está bem precificado?", "CONSULTA_MERCADO"),
    # BRIEFING
    ("O que eu tenho hoje?", "BRIEFING"),
    ("Me atualiza", "BRIEFING"),
    ("O que está urgente?", "BRIEFING"),
    # OUTRO
    ("Qual a previsão do tempo pra visita de amanhã?", "OUTRO"),
    ("Oi, tudo bem?", "OUTRO"),
    ("Esquece, era só um teste", "OUTRO"),
]
