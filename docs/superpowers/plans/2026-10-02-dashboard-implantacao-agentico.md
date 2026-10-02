# Dashboard de Implantação Ampliado — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ampliar `dashboard-implantacoes.html` para cobrir todos os projetos de Implantação/Reimplantação (não só os iniciados em 2026), mostrar o progresso interno de cada projeto (percentual + módulos) e gerar insights/recomendações automáticas por regras, alimentado por um script Python que atualiza os dados sob demanda.

**Architecture:** `atualizar_dados.py` loga no CRM (crm.nxlite.com.br, Frappe Framework), busca todos os `SAG Projeto` de Implantação/Reimplantação, seus módulos (`SAG Modulo`) e anotações, aplica classificação por regras, e grava um `dashboard_data.js` (`const DASHBOARD_DATA = {...}`). O `dashboard-implantacoes.html` carrega esse arquivo via `<script src>` (evita CORS de `file://`) e todo o motor de insights roda em JS no navegador em cima do `DASHBOARD_DATA` carregado.

**Tech Stack:** Python 3.14 stdlib (`urllib`, `unittest`, `unittest.mock` — sem `requests` nem `pytest` instalados nesta máquina), HTML/CSS/JS vanilla embutido em arquivo único (padrão já usado no projeto), Node.js 24 só para os scripts de verificação (`node --check`, simulação via `vm`).

Spec de referência: `docs/superpowers/specs/2026-10-01-dashboard-implantacao-agentico-design.md`.

## Global Constraints

- **Só leitura (GET) contra o CRM.** Nunca usar PUT/DELETE, e só usar POST para `/api/method/login`. Essa é uma regra permanente do projeto, não negociável nesta tarefa.
- **Credenciais só via variável de ambiente** (`NXLITE_USER`, `NXLITE_PASS`), nunca hardcoded em arquivo versionado.
- **Sem dependências externas de Python.** Esta máquina não tem `requests` nem `pytest` instalados — usar só a biblioteca padrão (`urllib`, `json`, `unittest`, `unittest.mock`, `datetime`).
- **`dashboard_data.js` nunca é commitado** — é gerado localmente e contém dados reais de clientes.
- **Sem servidor permanente.** Atualização de dados é sempre por execução manual do script (`python atualizar_dados.py` ou o `.bat`), nunca por um processo rodando em background.
- **Todo texto do dashboard em português**, consistente com o restante do arquivo.
- **Script aborta sem sobrescrever `dashboard_data.js`** se login ou qualquer chamada à API falhar.

---

## Task 1: Lógica pura de classificação e cálculo (TDD, sem rede)

**Files:**
- Create: `atualizar_dados.py`
- Test: `tests/test_atualizar_dados.py`

**Interfaces:**
- Produces: `calcular_atrasado(termino_previsto: str|None, hoje: date) -> str` (`"atrasado"|"no_prazo"|"prazo_nao_informado"`), `dias_desde_ultima_anotacao(anotacoes: list[dict], hoje: date) -> int|None`, `detectar_pausas(anotacoes: list[dict]) -> list[dict]`, `classificar_tema(anotacoes: list[dict]) -> str`, `categoria_motivo(tema: str) -> str` (`"motivo"|"sem_motivo"|"confuso"`), `calcular_prioridade(dias_atraso: int|None) -> str` (`"alta"|"normal"`), constantes `SEM_MOTIVO`, `REVISAR_MANUALMENTE`. Cada `anotacao` é um dict com chaves `"data"` (`"YYYY-MM-DD"`) e `"anotacao"` (texto) — esse é o formato bruto que a API do Frappe devolve para o child table `anotacoes` de `SAG Projeto` (confirmado via `GET /api/resource/SAG Projeto/<nome>`).

- [ ] **Step 1: Escrever os testes (vão falhar por enquanto, `atualizar_dados.py` não existe)**

Criar `tests/test_atualizar_dados.py`:

```python
# -*- coding: utf-8 -*-
import json
import os
import sys
import unittest
from datetime import date
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import atualizar_dados as ad


class TestCalcularAtrasado(unittest.TestCase):
    def test_sem_prazo_informado(self):
        self.assertEqual(ad.calcular_atrasado(None, date(2026, 10, 2)), "prazo_nao_informado")
        self.assertEqual(ad.calcular_atrasado("", date(2026, 10, 2)), "prazo_nao_informado")

    def test_prazo_vencido(self):
        self.assertEqual(ad.calcular_atrasado("2026-01-01", date(2026, 10, 2)), "atrasado")

    def test_prazo_nao_vencido(self):
        self.assertEqual(ad.calcular_atrasado("2027-01-01", date(2026, 10, 2)), "no_prazo")

    def test_prazo_exatamente_hoje_nao_e_atrasado(self):
        self.assertEqual(ad.calcular_atrasado("2026-10-02", date(2026, 10, 2)), "no_prazo")


class TestDiasDesdeUltimaAnotacao(unittest.TestCase):
    def test_sem_anotacoes_retorna_none(self):
        self.assertIsNone(ad.dias_desde_ultima_anotacao([], date(2026, 10, 2)))

    def test_calcula_a_partir_da_mais_recente(self):
        anotacoes = [
            {"data": "2026-09-01", "anotacao": "primeira"},
            {"data": "2026-09-20", "anotacao": "mais recente"},
            {"data": "2026-09-10", "anotacao": "do meio"},
        ]
        self.assertEqual(ad.dias_desde_ultima_anotacao(anotacoes, date(2026, 10, 2)), 12)


class TestDetectarPausas(unittest.TestCase):
    def test_sem_palavra_chave_nao_detecta(self):
        anotacoes = [{"data": "2026-01-01", "anotacao": "cliente confirmou reunião"}]
        self.assertEqual(ad.detectar_pausas(anotacoes), [])

    def test_detecta_pausa_e_congelamento(self):
        anotacoes = [
            {"data": "2026-01-01", "anotacao": "Projeto foi pausado a pedido do cliente"},
            {"data": "2026-02-01", "anotacao": "cliente confirmou reunião"},
            {"data": "2026-03-01", "anotacao": "ficou congelado até segunda ordem"},
        ]
        resultado = ad.detectar_pausas(anotacoes)
        self.assertEqual(len(resultado), 2)
        self.assertEqual(resultado[0]["data"], "2026-01-01")
        self.assertEqual(resultado[1]["data"], "2026-03-01")


class TestClassificarTema(unittest.TestCase):
    def test_sem_anotacoes(self):
        self.assertEqual(ad.classificar_tema([]), ad.SEM_MOTIVO)

    def test_identifica_aguardando_cliente(self):
        anotacoes = [{"data": "2026-01-01", "anotacao": "Estamos aguardando retorno do cliente sobre o módulo financeiro"}]
        self.assertEqual(ad.classificar_tema(anotacoes), "Aguardando decisão/validação do cliente")

    def test_identifica_servidor(self):
        anotacoes = [{"data": "2026-01-01", "anotacao": "Cliente ainda está comprando o servidor novo"}]
        self.assertEqual(ad.classificar_tema(anotacoes), "Atraso do cliente com infraestrutura (servidor)")

    def test_sem_palavra_chave_conhecida_pede_revisao(self):
        anotacoes = [{"data": "2026-01-01", "anotacao": "Reunião realizada, sem pendências relatadas"}]
        self.assertEqual(ad.classificar_tema(anotacoes), ad.REVISAR_MANUALMENTE)


class TestCategoriaMotivo(unittest.TestCase):
    def test_mapeamento(self):
        self.assertEqual(ad.categoria_motivo(ad.SEM_MOTIVO), "sem_motivo")
        self.assertEqual(ad.categoria_motivo(ad.REVISAR_MANUALMENTE), "confuso")
        self.assertEqual(ad.categoria_motivo("Falha técnica / bug do sistema"), "motivo")


class TestCalcularPrioridade(unittest.TestCase):
    def test_atraso_critico(self):
        self.assertEqual(ad.calcular_prioridade(30), "alta")
        self.assertEqual(ad.calcular_prioridade(45), "alta")

    def test_atraso_normal(self):
        self.assertEqual(ad.calcular_prioridade(29), "normal")
        self.assertEqual(ad.calcular_prioridade(0), "normal")

    def test_sem_atraso_informado(self):
        self.assertEqual(ad.calcular_prioridade(None), "normal")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Rodar e confirmar que falha (módulo não existe)**

Run: `python -m unittest discover -s tests -t . -v`
Expected: `ModuleNotFoundError: No module named 'atualizar_dados'` (ou erro de import equivalente).

- [ ] **Step 3: Criar `atualizar_dados.py` com a lógica pura**

```python
# -*- coding: utf-8 -*-
"""Busca projetos de Implantacao/Reimplantacao no CRM nxlite e gera dashboard_data.js.

So leitura (GET). Nunca criar/alterar/apagar registros no CRM.
"""
import json
import os
import sys
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
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `python -m unittest discover -s tests -t . -v`
Expected: `OK` com 13 testes passando (0 falhas).

- [ ] **Step 5: Commit**

```bash
git add atualizar_dados.py tests/test_atualizar_dados.py
git commit -m "feat: logica pura de classificacao de atraso/motivo/pausa do pipeline de implantacao"
```

---

## Task 2: Funções de acesso à API (login, projetos, módulos) com testes mockados

**Files:**
- Modify: `atualizar_dados.py` (adicionar ao final do arquivo)
- Test: `tests/test_atualizar_dados.py` (adicionar novas classes de teste)

**Interfaces:**
- Consumes: nada do Task 1 diretamente (funções independentes), mas mesmo arquivo.
- Produces: `make_opener() -> OpenerDirector`, `call(opener, method: str, path: str, data: dict|None=None) -> tuple[int, str]`, `resource(doctype: str, query: str="") -> str`, `class LoginError(Exception)`, `fazer_login(opener, usuario: str, senha: str) -> None`, `buscar_projetos(opener) -> list[dict]`, `buscar_anotacoes(opener, nome_projeto: str) -> list[dict]`, `buscar_todos_modulos(opener) -> dict[str, list[dict]]` (chave = nome do projeto), `buscar_versions_status(opener, nome_projeto: str) -> list[dict]`.

Campos confirmados ao vivo nesta sessão (consulta `GET /api/resource/DocType/SAG Modulo` e `GET /api/resource/SAG Projeto/<nome>`, só leitura):
- `SAG Modulo`: `nome_modulo` (Data), `status` (Select: Consulta/Fechado/Liberado), `percentual_conclusao` (Percent), `sequencia` (Int), `projeto` (Link para `SAG Projeto`).
- `SAG Projeto.anotacoes` (child table, doctype `projeto_anotacoes`): cada item tem `data` (Date) e `anotacao` (texto).
- `Version`: filtra por `ref_doctype`/`docname`; campo `data` é uma **string JSON** com chave `changed` = lista de `[nome_campo, valor_antigo, valor_novo]`.

- [ ] **Step 1: Escrever os testes mockados (vão falhar, funções não existem)**

Adicionar a `tests/test_atualizar_dados.py` (não remover as classes do Task 1):

```python
class TestFazerLogin(unittest.TestCase):
    @patch("atualizar_dados.call")
    def test_login_sucesso_nao_lanca_erro(self, mock_call):
        mock_call.return_value = (200, '{"message": "Logged In"}')
        ad.fazer_login(opener=object(), usuario="u", senha="p")

    @patch("atualizar_dados.call")
    def test_login_falho_lanca_login_error(self, mock_call):
        mock_call.return_value = (401, '{"message": "invalid"}')
        with self.assertRaises(ad.LoginError):
            ad.fazer_login(opener=object(), usuario="u", senha="p")


class TestBuscarProjetos(unittest.TestCase):
    @patch("atualizar_dados.call")
    def test_retorna_lista_de_projetos(self, mock_call):
        mock_call.return_value = (200, json.dumps({"data": [{"name": "SAGP-00001"}]}))
        resultado = ad.buscar_projetos(opener=object())
        self.assertEqual(resultado, [{"name": "SAGP-00001"}])

    @patch("atualizar_dados.call")
    def test_erro_de_api_lanca_excecao(self, mock_call):
        mock_call.return_value = (500, "erro interno")
        with self.assertRaises(RuntimeError):
            ad.buscar_projetos(opener=object())


class TestBuscarAnotacoes(unittest.TestCase):
    @patch("atualizar_dados.call")
    def test_retorna_child_table_anotacoes(self, mock_call):
        mock_call.return_value = (200, json.dumps({"data": {"anotacoes": [{"data": "2026-01-01", "anotacao": "x"}]}}))
        resultado = ad.buscar_anotacoes(opener=object(), nome_projeto="SAGP-00001")
        self.assertEqual(resultado, [{"data": "2026-01-01", "anotacao": "x"}])

    @patch("atualizar_dados.call")
    def test_sem_anotacoes_retorna_lista_vazia(self, mock_call):
        mock_call.return_value = (200, json.dumps({"data": {}}))
        self.assertEqual(ad.buscar_anotacoes(opener=object(), nome_projeto="SAGP-00002"), [])


class TestBuscarTodosModulos(unittest.TestCase):
    @patch("atualizar_dados.call")
    def test_agrupa_por_projeto_e_ordena_por_sequencia(self, mock_call):
        mock_call.return_value = (200, json.dumps({"data": [
            {"nome_modulo": "Financeiro", "status": "Fechado", "percentual_conclusao": 100.0, "sequencia": 2, "projeto": "SAGP-00001"},
            {"nome_modulo": "Cadastros", "status": "Fechado", "percentual_conclusao": 100.0, "sequencia": 1, "projeto": "SAGP-00001"},
            {"nome_modulo": "Estoque", "status": "Consulta", "percentual_conclusao": 40.0, "sequencia": 1, "projeto": "SAGP-00002"},
        ]})) 
        resultado = ad.buscar_todos_modulos(opener=object())
        self.assertEqual([m["nome_modulo"] for m in resultado["SAGP-00001"]], ["Cadastros", "Financeiro"])
        self.assertEqual(len(resultado["SAGP-00002"]), 1)
        self.assertNotIn("SAGP-00003", resultado)


class TestBuscarVersionsStatus(unittest.TestCase):
    @patch("atualizar_dados.call")
    def test_retorna_lista_de_versions(self, mock_call):
        mock_call.return_value = (200, json.dumps({"data": [{"name": "v1", "creation": "2026-05-01 10:00:00", "data": "{}"}]}))
        resultado = ad.buscar_versions_status(opener=object(), nome_projeto="SAGP-00001")
        self.assertEqual(len(resultado), 1)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m unittest discover -s tests -t . -v`
Expected: `AttributeError: module 'atualizar_dados' has no attribute 'fazer_login'` (ou similar para as demais funções).

- [ ] **Step 3: Implementar as funções de acesso à API**

Adicionar ao final de `atualizar_dados.py`:

```python
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
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `python -m unittest discover -s tests -t . -v`
Expected: `OK` com 21 testes passando (13 do Task 1 + 8 novos).

- [ ] **Step 5: Commit**

```bash
git add atualizar_dados.py tests/test_atualizar_dados.py
git commit -m "feat: funcoes de acesso a API do CRM (login, projetos, modulos, versions)"
```

---

## Task 3: Montagem dos dados, geração do `dashboard_data.js` e script de execução

**Files:**
- Modify: `atualizar_dados.py` (adicionar montagem, agregação, escrita e `main()`)
- Test: `tests/test_atualizar_dados.py` (adicionar testes de agregação, sem rede)
- Create: `atualizar_dados.bat`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: todas as funções dos Tasks 1 e 2.
- Produces: `montar_projeto_atrasado(projeto: dict, anotacoes: list[dict], modulos: list[dict], hoje: date) -> dict`, `extrair_dia_mudanca_status(versions: list[dict], status_alvo: tuple[str,...]) -> str|None`, `montar_projeto_finalizado(projeto: dict, versions: list[dict], modulos: list[dict]) -> dict`, `calcular_visao_geral_por_ano(projetos: list[dict], info_conclusao: dict[str, int|None], hoje: date) -> dict`, `gerar_dashboard_data(opener, hoje: date) -> dict`, `escrever_arquivo_js(dados: dict, caminho: str) -> None`, `main() -> None`.

- [ ] **Step 1: Escrever os testes de agregação (sem rede, vão falhar)**

Adicionar a `tests/test_atualizar_dados.py`:

```python
class TestMontarProjetoAtrasado(unittest.TestCase):
    def test_projeto_vencido_com_tema_identificado(self):
        projeto = {
            "name": "SAGP-00001", "nome_do_projeto": "Teste", "nome_cliente": "Cliente X",
            "nome_lider_projeto_grv": "Fulano", "tipo_de_projeto": "Implantação",
            "termino_previsto": "2026-08-01", "inicio_previsto": "2026-01-01",
            "percentual_conclusao": 40.0,
        }
        anotacoes = [{"data": "2026-09-01", "anotacao": "Aguardando retorno do cliente sobre o financeiro"}]
        modulos = [{"nome_modulo": "Financeiro", "status": "Consulta", "percentual_conclusao": 40.0}]
        entry = ad.montar_projeto_atrasado(projeto, anotacoes, modulos, date(2026, 10, 2))
        self.assertTrue(entry["_prazo_vencido"])
        self.assertEqual(entry["_dias_atraso"], 62)
        self.assertEqual(entry["_tema"], "Aguardando decisão/validação do cliente")
        self.assertEqual(entry["_categoria_motivo"], "motivo")
        self.assertTrue(entry["_motivo_plausivel"])
        self.assertEqual(entry["_prioridade"], "alta")
        self.assertEqual(entry["modulos"][0]["nome"], "Financeiro")

    def test_projeto_sem_anotacoes_e_sem_motivo(self):
        projeto = {"name": "SAGP-00002", "nome_cliente": "Y", "termino_previsto": "2026-09-20", "percentual_conclusao": 0}
        entry = ad.montar_projeto_atrasado(projeto, [], [], date(2026, 10, 2))
        self.assertEqual(entry["_tema"], ad.SEM_MOTIVO)
        self.assertEqual(entry["_categoria_motivo"], "sem_motivo")
        self.assertFalse(entry["_motivo_plausivel"])
        self.assertEqual(entry["_dias_sem_atualizacao"], None)

    def test_projeto_no_prazo_tem_dias_atraso_negativo(self):
        projeto = {"name": "SAGP-00003", "nome_cliente": "Z", "termino_previsto": "2026-12-25", "percentual_conclusao": 0}
        entry = ad.montar_projeto_atrasado(projeto, [], [], date(2026, 10, 2))
        self.assertFalse(entry["_prazo_vencido"])
        self.assertLess(entry["_dias_atraso"], 0)
        self.assertEqual(entry["_prioridade"], "normal")


class TestExtrairDiaMudancaStatus(unittest.TestCase):
    def test_encontra_mudanca_para_status_alvo(self):
        versions = [
            {"creation": "2026-05-01 10:00:00", "data": json.dumps({"changed": [["nome_lider_projeto_grv", "A", "B"]]})},
            {"creation": "2026-06-15 09:30:00", "data": json.dumps({"changed": [["status", "Aberto", "Consulta"]]})},
        ]
        self.assertEqual(ad.extrair_dia_mudanca_status(versions, ("Consulta", "Fechado")), "2026-06-15")

    def test_sem_mudanca_retorna_none(self):
        versions = [{"creation": "2026-05-01 10:00:00", "data": json.dumps({"changed": []})}]
        self.assertIsNone(ad.extrair_dia_mudanca_status(versions, ("Consulta", "Fechado")))


class TestMontarProjetoFinalizado(unittest.TestCase):
    def test_concluido_depois_do_prazo(self):
        projeto = {"name": "SAGP-00010", "nome_cliente": "W", "status": "Consulta",
                   "nome_lider_projeto_grv": "Fulana", "termino_previsto": "2026-05-01",
                   "inicio_previsto": "2026-01-10", "percentual_conclusao": 100.0}
        versions = [{"creation": "2026-05-20 14:00:00", "data": json.dumps({"changed": [["status", "Aberto", "Consulta"]]})}]
        entry = ad.montar_projeto_finalizado(projeto, versions, [])
        self.assertEqual(entry["_dia_mudanca"], "2026-05-20")
        self.assertEqual(entry["_dias_entre_prazo_e_status"], 19)
        self.assertEqual(entry["_ano_inicio"], 2026)

    def test_sem_log_de_mudanca(self):
        projeto = {"name": "SAGP-00011", "nome_cliente": "V", "status": "Fechado",
                   "termino_previsto": "2026-05-01", "inicio_previsto": "2025-11-01"}
        entry = ad.montar_projeto_finalizado(projeto, [], [])
        self.assertIsNone(entry["_dia_mudanca"])
        self.assertIsNone(entry["_dias_entre_prazo_e_status"])
        self.assertEqual(entry["_ano_inicio"], 2025)


class TestCalcularVisaoGeralPorAno(unittest.TestCase):
    def test_agrupa_por_ano_e_soma_todos(self):
        hoje = date(2026, 10, 2)
        projetos = [
            {"name": "P1", "status": "Aberto", "inicio_previsto": "2026-01-01", "termino_previsto": "2026-01-01"},  # atrasado
            {"name": "P2", "status": "Aberto", "inicio_previsto": "2026-02-01", "termino_previsto": "2027-01-01"},  # no prazo
            {"name": "P3", "status": "Consulta", "inicio_previsto": "2026-01-01", "termino_previsto": "2026-01-01"},
            {"name": "P4", "status": "Pausado", "inicio_previsto": "2025-01-01", "termino_previsto": None},
            {"name": "P5", "status": "Cancelado", "inicio_previsto": "2025-06-01", "termino_previsto": None},
        ]
        info_conclusao = {"P3": 5}  # concluiu 5 dias depois do prazo
        resultado = ad.calcular_visao_geral_por_ano(projetos, info_conclusao, hoje)
        self.assertEqual(resultado["2026"]["total"], 3)
        self.assertEqual(resultado["2026"]["atrasados"], 1)
        self.assertEqual(resultado["2026"]["abertos_no_prazo"], 1)
        self.assertEqual(resultado["2026"]["concluidos"], 1)
        self.assertEqual(resultado["2026"]["concluidos_atrasados"], 1)
        self.assertEqual(resultado["2025"]["total"], 2)
        self.assertEqual(resultado["2025"]["pausados"], 1)
        self.assertEqual(resultado["2025"]["cancelados"], 1)
        self.assertEqual(resultado["todos"]["total"], 5)
        self.assertEqual(resultado["todos"]["concluidos_sem_info"], 0)

    def test_concluido_sem_info_quando_sem_log(self):
        hoje = date(2026, 10, 2)
        projetos = [{"name": "P1", "status": "Consulta", "inicio_previsto": "2026-01-01", "termino_previsto": "2026-01-01"}]
        resultado = ad.calcular_visao_geral_por_ano(projetos, {"P1": None}, hoje)
        self.assertEqual(resultado["2026"]["concluidos_sem_info"], 1)
        self.assertEqual(resultado["2026"]["concluidos_no_prazo"], 0)
        self.assertEqual(resultado["2026"]["concluidos_atrasados"], 0)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m unittest discover -s tests -t . -v`
Expected: `AttributeError: module 'atualizar_dados' has no attribute 'montar_projeto_atrasado'` (ou similar).

- [ ] **Step 3: Implementar montagem, agregação, escrita e `main()`**

Adicionar ao final de `atualizar_dados.py`:

```python
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
```

Adicionar os imports que faltam no topo do arquivo (`tempfile`):

```python
import tempfile
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `python -m unittest discover -s tests -t . -v`
Expected: `OK` com 29 testes passando (21 anteriores + 8 novos).

- [ ] **Step 5: Criar o `.bat` de conveniência**

Criar `atualizar_dados.bat`:

```bat
@echo off
setlocal
set /p NXLITE_USER="Usuario CRM (crm.nxlite.com.br): "
set /p NXLITE_PASS="Senha: "
python "%~dp0atualizar_dados.py"
set NXLITE_USER=
set NXLITE_PASS=
pause
```

- [ ] **Step 6: Ignorar o `dashboard_data.js` gerado**

Ler `.gitignore` atual e adicionar a linha `dashboard_data.js` ao final (arquivo tem hoje: `nul`, `check-api.html`, `.env`).

- [ ] **Step 7: Rodar o script contra o CRM real e validar contra os números já auditados**

Run (credenciais via variável de ambiente, apagadas logo em seguida):
```bash
NXLITE_USER='<usuario>' NXLITE_PASS='<senha>' python atualizar_dados.py
```
Expected: `OK: .../dashboard_data.js atualizado em <timestamp>` sem traceback.

Conferir sanidade (números devem ficar na mesma ordem de grandeza dos já auditados nesta sessão — total ~146 projetos, ~42 atrasados, ~48 finalizados em 2026; pequenas diferenças são esperadas porque o tempo passou):
```bash
python -c "
import json
raw = open('dashboard_data.js', encoding='utf-8').read()
dados = json.loads(raw[len('const DASHBOARD_DATA = '):-2])
print('total:', dados['atrasados']['resumo']['total_implantacao_reimplantacao'])
print('vencidos:', len(dados['atrasados']['vencidos']))
print('finalizados:', len(dados['finalizados']['projetos']))
print('anos visao geral:', list(dados['visao_geral_por_ano'].keys()))
"
```
Expected: valores plausíveis (não zero, não ordens de grandeza diferentes do que já vimos nesta sessão) e a lista de anos incluindo "todos".

- [ ] **Step 8: Commit**

```bash
git add atualizar_dados.py atualizar_dados.bat tests/test_atualizar_dados.py .gitignore
git commit -m "feat: monta e grava dashboard_data.js a partir da API do CRM"
```

---

## Task 4: Dashboard passa a carregar `dashboard_data.js` + badge de última atualização

**Files:**
- Modify: `dashboard-implantacoes.html`
- Create: `tests/verify_dashboard_html.js` (harness de verificação reutilizado nos Tasks 4–8)

**Interfaces:**
- Consumes: `DASHBOARD_DATA` (global definida por `dashboard_data.js`, gerado no Task 3).
- Produces: globais `DATA`, `CAT_LABELS`, `CAT_CORES`, `ANOTACOES_MAP`, `PAUSAS_INFO`, `VISAO_GERAL`, `FINALIZADOS` (derivadas de `DASHBOARD_DATA`, consumidas pelos Tasks 5–8).

- [ ] **Step 1: Criar o harness de verificação**

Criar `tests/verify_dashboard_html.js`:

```js
// Uso: node tests/verify_dashboard_html.js dashboard-implantacoes.html
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const os = require('os');
const { execFileSync } = require('child_process');

const htmlPath = process.argv[2];
if (!htmlPath) {
  console.error('uso: node verify_dashboard_html.js <arquivo.html>');
  process.exit(1);
}
const html = fs.readFileSync(htmlPath, 'utf8');

const blocos = [...html.matchAll(/<script(?:\s+src="([^"]+)")?[^>]*>([\s\S]*?)<\/script>/g)];
const inline = blocos.filter(m => !m[1]).map(m => m[2]);
const srcs = blocos.filter(m => m[1]).map(m => m[1]);
if (inline.length === 0) {
  console.error('ERRO: nenhum <script> inline encontrado');
  process.exit(1);
}
const codigoInline = inline.join('\n;\n');

const tmpFile = path.join(os.tmpdir(), 'verify_dashboard_inline.js');
fs.writeFileSync(tmpFile, codigoInline);
execFileSync(process.execPath, ['--check', tmpFile]);
console.log('OK: sintaxe do script inline valida');

const baseDir = path.dirname(htmlPath);
const codigoSrc = srcs.map(src => fs.readFileSync(path.join(baseDir, src), 'utf8')).join('\n;\n');

const idsHtml = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]));

function elementoFalso() {
  const el = {
    _value: '',
    classList: {
      _set: new Set(),
      add(...c) { c.forEach(x => this._set.add(x)); },
      remove(...c) { c.forEach(x => this._set.delete(x)); },
      toggle(c) { this._set.has(c) ? this._set.delete(c) : this._set.add(c); },
      contains(c) { return this._set.has(c); },
    },
    style: {},
    dataset: {},
    children: [],
    textContent: '',
    innerHTML: '',
    get value() { return this._value; },
    set value(v) { this._value = v; },
    appendChild(child) { this.children.push(child); return child; },
    insertBefore(child) { this.children.unshift(child); return child; },
    addEventListener() {},
    removeEventListener() {},
    closest() { return null; },
    querySelectorAll() { return []; },
    querySelector() { return null; },
    scrollIntoView() {},
    remove() {},
    get lastElementChild() { return this.children[this.children.length - 1] || null; },
    get firstChild() { return this.children[0] || null; },
  };
  return el;
}

const elementosPorId = new Map();
const documentStub = {
  getElementById(id) {
    if (!elementosPorId.has(id)) elementosPorId.set(id, elementoFalso());
    return elementosPorId.get(id);
  },
  querySelectorAll() { return []; },
  querySelector() { return null; },
  createElement() { return elementoFalso(); },
  addEventListener() {},
};

const contexto = vm.createContext({
  document: documentStub,
  window: {},
  console,
  Math, JSON, Object, Array, Set, Infinity, Date,
});

vm.runInContext(codigoSrc + '\n;\n' + codigoInline, contexto, { filename: 'dashboard-inline.js' });
console.log('OK: execucao simulada nao lancou erro');

const idsReferenciados = new Set([...codigoInline.matchAll(/getElementById\('([^']+)'\)/g)].map(m => m[1]));
const faltando = [...idsReferenciados].filter(id => !idsHtml.has(id));
if (faltando.length) {
  console.error('ERRO: ids referenciados no JS mas ausentes no HTML:', faltando);
  process.exit(1);
}
console.log('OK: todos os ' + idsReferenciados.size + ' ids referenciados existem no HTML');
```

- [ ] **Step 2: Rodar o harness contra o HTML atual (ainda sem `dashboard_data.js`) para confirmar a baseline**

Run: `node tests/verify_dashboard_html.js dashboard-implantacoes.html`
Expected: falha em "execucao simulada" (`DATA is not defined` ou similar), porque ainda não existe `dashboard_data.js` — isso confirma que o harness detecta o problema antes da correção.

- [ ] **Step 3: Trocar a fonte de dados embutida pelo arquivo externo**

Usar Edit em `dashboard-implantacoes.html`. Antes do `<script>` que contém `const DATA = ...` (a linha é exatamente `<script>`, seguida de uma linha enorme `const DATA = {...}`), inserir o `<script src>`:

old_string:
```
<script>
```
(a primeira ocorrência, imediatamente antes de `const DATA = `)

new_string:
```
<script src="dashboard_data.js"></script>
<script>
```

Em seguida, substituir as 5 linhas gigantes de dados (`const DATA = ...`, `const ANOTACOES_MAP = ...`, `const PAUSAS_INFO = ...`, `const TAB2 = ...`, mais as duas linhas curtas `CAT_LABELS`/`CAT_CORES` entre elas) por atribuições derivadas de `DASHBOARD_DATA`. Como essas linhas são enormes (até 130KB cada), **não usar Edit com old_string contendo o JSON completo** — usar um script Python para localizar e substituir pelo prefixo exato:

```bash
python - <<'EOF'
import re

caminho = "dashboard-implantacoes.html"
texto = open(caminho, encoding="utf-8").read()

novo_bloco = (
    "const DATA = DASHBOARD_DATA.atrasados;\n"
    "const CAT_LABELS = DASHBOARD_DATA.cat_labels;\n"
    "const CAT_CORES = DASHBOARD_DATA.cat_cores;\n"
    "const ANOTACOES_MAP = DASHBOARD_DATA.anotacoes_map;\n"
    "const PAUSAS_INFO = DASHBOARD_DATA.pausas_info;\n"
    "let VISAO_GERAL = DASHBOARD_DATA.visao_geral_por_ano;\n"
    "let FINALIZADOS = DASHBOARD_DATA.finalizados;\n"
)

padrao = re.compile(
    r"const DATA = \{.*?\};\n"
    r"const CAT_LABELS = \{.*?\};\n"
    r"const CAT_CORES = \{.*?\};\n"
    r"const ANOTACOES_MAP = \{.*?\};\n"
    r"const PAUSAS_INFO = \{.*?\};\n"
    r"const TAB2 = \{.*?\};\n",
    re.DOTALL,
)
texto_novo, n = padrao.subn(novo_bloco, texto, count=1)
assert n == 1, f"esperava 1 substituicao, fiz {n}"
open(caminho, "w", encoding="utf-8").write(texto_novo)
print("OK, bloco de dados substituido")
EOF
```

Remover também o bloco `const MOTIVO_TEMA = {...};` (dezenas de linhas logo depois, com os `SAGP-xxxxx` hardcoded) — ele será substituído no Task 8 pelo campo `_tema` já calculado em Python:

```bash
python - <<'EOF'
import re
caminho = "dashboard-implantacoes.html"
texto = open(caminho, encoding="utf-8").read()
texto_novo, n = re.subn(
    r"// Tema de motivo por projeto.*?\nconst MOTIVO_TEMA = \{.*?\n\};\n\n",
    "",
    texto,
    count=1,
    flags=re.DOTALL,
)
assert n == 1, f"esperava 1 substituicao, fiz {n}"
open(caminho, "w", encoding="utf-8").write(texto_novo)
print("OK, MOTIVO_TEMA removido")
EOF
```

- [ ] **Step 4: Adicionar o badge de última atualização**

Usar Edit em `dashboard-implantacoes.html`:

old_string:
```html
<h1>Painel de Implantações e Reimplantações — GRV</h1>
<div class="subtitle">Gerado em 30/09/2026 · Fonte: crm.nxlite.com.br (SAG Projeto)</div>
```

new_string:
```html
<h1>Painel de Implantações e Reimplantações — GRV</h1>
<div class="subtitle">Fonte: crm.nxlite.com.br (SAG Projeto) · <span id="gerado-em-badge">-</span></div>
```

E, logo após o bloco de atribuições `const DATA = DASHBOARD_DATA.atrasados; ...` (inserido no Step 3), adicionar:

```js
function formatarDataHoraBR(isoString) {
  const d = new Date(isoString);
  const pad = n => String(n).padStart(2, '0');
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()} às ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
document.getElementById('gerado-em-badge').textContent = 'Atualizado em ' + formatarDataHoraBR(DASHBOARD_DATA.gerado_em);
```

- [ ] **Step 5: Rodar o harness contra o `dashboard_data.js` real gerado no Task 3**

Run: `node tests/verify_dashboard_html.js dashboard-implantacoes.html`
Expected: as três linhas `OK:` (sintaxe, execução simulada, ids) sem erro.

- [ ] **Step 6: Commit**

```bash
git add dashboard-implantacoes.html tests/verify_dashboard_html.js
git commit -m "feat: dashboard carrega dashboard_data.js externo em vez de dados embutidos"
```

---

## Task 5: Seletor de ano/cohort na aba "Visão geral"

**Files:**
- Modify: `dashboard-implantacoes.html`

**Interfaces:**
- Consumes: `VISAO_GERAL` (global do Task 4, formato `{"<ano>": {total, atrasados, abertos_no_prazo, pausados, concluidos, concluidos_no_prazo, concluidos_atrasados, concluidos_sem_info, cancelados}, ..., "todos": {...}}`).

- [ ] **Step 1: Trocar o rótulo da aba e adicionar o seletor no HTML**

old_string:
```html
  <button class="tab-btn active" data-tab="tab-visao-geral">Visão geral 2026</button>
```
new_string:
```html
  <button class="tab-btn active" data-tab="tab-visao-geral">Visão geral</button>
```

old_string:
```html
<div id="tab-visao-geral" class="tab-content">

<div class="subtitle" style="margin-top:16px">Todos os projetos de Implantação/Reimplantação com início previsto em 2026, por situação atual.</div>
```
new_string:
```html
<div id="tab-visao-geral" class="tab-content">

<div class="controls" style="margin-top:16px">
  <select id="seletor-ano-visao-geral"></select>
</div>
<div class="subtitle" id="visao-geral-subtitulo">-</div>
```

old_string:
```html
<div class="panel">
  <h2>Como os 118 projetos de 2026 se distribuem</h2>
  <div id="chart-visao-geral"></div>
</div>
```
new_string:
```html
<div class="panel">
  <h2 id="visao-geral-titulo">-</h2>
  <div id="chart-visao-geral"></div>
</div>
```

- [ ] **Step 2: Rodar o harness e confirmar que falha (os `document.getElementById` novos ainda não têm JS)**

Run: `node tests/verify_dashboard_html.js dashboard-implantacoes.html`
Expected: ainda passa (os ids novos existem no HTML, só não são usados ainda) — serve de baseline antes de ligar o seletor.

- [ ] **Step 3: Substituir o bloco de KPIs/gráfico fixo por uma função orientada ao seletor**

Usar o script de substituição por regex (o bloco original é identificável pelas linhas exatas já lidas nesta sessão):

old_string:
```js
document.getElementById('vg-total').textContent = VISAO_2026.total_2026;
document.getElementById('vg-atrasados').textContent = VISAO_2026.atrasados;
document.getElementById('vg-no-prazo').textContent = VISAO_2026.abertos_no_prazo;
document.getElementById('vg-pausados').textContent = VISAO_2026.pausados;
document.getElementById('vg-concluidos').textContent = VISAO_2026.concluidos;
document.getElementById('vg-concluidos-no-prazo').textContent = VISAO_2026.concluidos_no_prazo;
document.getElementById('vg-concluidos-atrasados').textContent = VISAO_2026.concluidos_atrasados;
document.getElementById('vg-cancelados').textContent = VISAO_2026.cancelados;

(function renderChartVisaoGeral() {
  const itens = [
    ['Atrasados (prazo vencido)', VISAO_2026.atrasados, true],
    ['Concluídos depois do prazo', VISAO_2026.concluidos_atrasados, true],
    ['Abertos, dentro do prazo', VISAO_2026.abertos_no_prazo, false],
    ['Concluídos dentro do prazo', VISAO_2026.concluidos_no_prazo, false],
    ['Concluídos sem informação de data', VISAO_2026.concluidos_sem_info, false],
    ['Pausados', VISAO_2026.pausados, false],
    ['Cancelados / interrompidos / modelo', VISAO_2026.cancelados, false],
  ];
  const max = Math.max(...itens.map(i => i[1]));
  const el = document.getElementById('chart-visao-geral');
  itens.forEach(([nome, count, critico]) => {
    const row = document.createElement('div');
    row.className = 'bar-row';
    const pct = max ? (count / max * 100).toFixed(0) : 0;
    row.innerHTML = `<div class="bar-name" style="width:240px">${nome}</div><div class="bar-track"><div class="bar-fill${critico ? ' critical' : ''}" style="width:${pct}%">${count}</div></div>`;
    el.appendChild(row);
  });
})();
```

new_string:
```js
let anoVisaoGeralAtual = 'todos';

function renderVisaoGeral() {
  const v = VISAO_GERAL[anoVisaoGeralAtual] || VISAO_GERAL['todos'];
  document.getElementById('vg-total').textContent = v.total;
  document.getElementById('vg-atrasados').textContent = v.atrasados;
  document.getElementById('vg-no-prazo').textContent = v.abertos_no_prazo;
  document.getElementById('vg-pausados').textContent = v.pausados;
  document.getElementById('vg-concluidos').textContent = v.concluidos;
  document.getElementById('vg-concluidos-no-prazo').textContent = v.concluidos_no_prazo;
  document.getElementById('vg-concluidos-atrasados').textContent = v.concluidos_atrasados;
  document.getElementById('vg-cancelados').textContent = v.cancelados;

  const rotuloAno = anoVisaoGeralAtual === 'todos' ? 'todos os anos' : ('iniciados em ' + anoVisaoGeralAtual);
  document.getElementById('visao-geral-titulo').textContent = `Como os ${v.total} projetos ${rotuloAno} se distribuem`;
  document.getElementById('visao-geral-subtitulo').textContent = `Projetos de Implantação/Reimplantação ${rotuloAno}, por situação atual.`;

  const itens = [
    ['Atrasados (prazo vencido)', v.atrasados, true],
    ['Concluídos depois do prazo', v.concluidos_atrasados, true],
    ['Abertos, dentro do prazo', v.abertos_no_prazo, false],
    ['Concluídos dentro do prazo', v.concluidos_no_prazo, false],
    ['Concluídos sem informação de data', v.concluidos_sem_info, false],
    ['Pausados', v.pausados, false],
    ['Cancelados / interrompidos / modelo', v.cancelados, false],
  ];
  const max = Math.max(...itens.map(i => i[1]), 1);
  const el = document.getElementById('chart-visao-geral');
  el.innerHTML = '';
  itens.forEach(([nome, count, critico]) => {
    const row = document.createElement('div');
    row.className = 'bar-row';
    const pct = (count / max * 100).toFixed(0);
    row.innerHTML = `<div class="bar-name" style="width:240px">${nome}</div><div class="bar-track"><div class="bar-fill${critico ? ' critical' : ''}" style="width:${pct}%">${count}</div></div>`;
    el.appendChild(row);
  });
}

const selAnoVisaoGeral = document.getElementById('seletor-ano-visao-geral');
Object.keys(VISAO_GERAL)
  .sort((a, b) => (a === 'todos' ? -1 : b === 'todos' ? 1 : b.localeCompare(a)))
  .forEach(ano => {
    const opt = document.createElement('option');
    opt.value = ano;
    opt.textContent = ano === 'todos' ? 'Todos os anos' : ano;
    selAnoVisaoGeral.appendChild(opt);
  });
selAnoVisaoGeral.value = 'todos';
selAnoVisaoGeral.addEventListener('change', () => {
  anoVisaoGeralAtual = selAnoVisaoGeral.value;
  renderVisaoGeral();
});
renderVisaoGeral();
```

- [ ] **Step 4: Rodar o harness**

Run: `node tests/verify_dashboard_html.js dashboard-implantacoes.html`
Expected: as três linhas `OK:` sem erro.

- [ ] **Step 5: Commit**

```bash
git add dashboard-implantacoes.html
git commit -m "feat: seletor de ano/cohort na aba Visao geral"
```

---

## Task 6: Seletor de ano/cohort na aba "Finalizados" + KPIs/clusters recalculados em JS

**Files:**
- Modify: `dashboard-implantacoes.html`

**Interfaces:**
- Consumes: `FINALIZADOS.projetos` (global do Task 4; cada item tem `_ano_inicio`, `_dia_mudanca`, `_dias_entre_prazo_e_status`, `percentual_conclusao`, `modulos`).

- [ ] **Step 1: Trocar o rótulo da aba, o título do painel e adicionar o seletor**

old_string:
```html
  <button class="tab-btn" data-tab="tab-finalizados">Projetos finalizados em 2026</button>
```
new_string:
```html
  <button class="tab-btn" data-tab="tab-finalizados">Projetos finalizados</button>
```

old_string:
```html
  <div class="kpi">
    <div class="value" id="kpi2-total">-</div>
    <div class="label">Projetos iniciados em 2026 e já em Consulta/Fechado</div>
  </div>
```
new_string:
```html
  <div class="kpi">
    <div class="value" id="kpi2-total">-</div>
    <div class="label" id="kpi2-total-label">Projetos já em Consulta/Fechado</div>
  </div>
```

old_string:
```html
<div class="panel">
  <h2>Projetos finalizados em 2026 (Implantação/Reimplantação) <span class="count" id="count-finalizados"></span></h2>
  <div class="controls">
    <input type="text" id="busca-finalizados" placeholder="Buscar cliente ou projeto...">
    <select id="filtro-lider-finalizados"><option value="">Todos os consultores</option></select>
  </div>
```
new_string:
```html
<div class="panel">
  <h2>Projetos finalizados (Implantação/Reimplantação) <span class="count" id="count-finalizados"></span></h2>
  <div class="controls">
    <select id="seletor-ano-finalizados"></select>
    <input type="text" id="busca-finalizados" placeholder="Buscar cliente ou projeto...">
    <select id="filtro-lider-finalizados"><option value="">Todos os consultores</option></select>
  </div>
```

- [ ] **Step 2: Substituir o bloco "ABA 2" para filtrar por ano e recalcular KPIs/clusters em JS**

old_string:
```js
// ==== ABA 2: Projetos finalizados em 2026 ====
document.getElementById('kpi2-total').textContent = TAB2.total;
document.getElementById('kpi2-com-log').textContent = TAB2.com_log;
document.getElementById('kpi2-passou-prazo').textContent = TAB2.passou_do_prazo_quando_mudou;

const clusterEl = document.getElementById('cluster-badges');
TAB2.clusters.filter(c => c[1] >= 2).forEach(([data, qtd]) => {
  const span = document.createElement('span');
  span.className = 'cluster-badge';
  span.innerHTML = `${data}: <b>${qtd} projetos</b>`;
  clusterEl.appendChild(span);
});

const lideresSet2 = [...new Set(TAB2.projetos.map(p => p.nome_lider_projeto_grv))].sort();
const selLider2 = document.getElementById('filtro-lider-finalizados');
lideresSet2.forEach(l => {
  const opt = document.createElement('option');
  opt.value = l; opt.textContent = l;
  selLider2.appendChild(opt);
});

function renderFinalizados() {
  const busca = document.getElementById('busca-finalizados').value.toLowerCase();
  const lider = document.getElementById('filtro-lider-finalizados').value;
  let rows = TAB2.projetos.filter(p => {
    if (lider && p.nome_lider_projeto_grv !== lider) return false;
    if (busca) {
      const alvo = (p.nome_cliente + ' ' + p.name).toLowerCase();
      if (!alvo.includes(busca)) return false;
    }
    return true;
  });
  document.getElementById('count-finalizados').textContent = '(' + rows.length + ' de ' + TAB2.total + ')';
  const tbody = document.getElementById('tbody-finalizados');
  tbody.innerHTML = '';
  rows.forEach(p => {
    const tr = document.createElement('tr');
    const lote = p._qtd_no_mesmo_dia;
    const loteTxt = lote ? (lote >= 4 ? `<span class="badge" style="background:${CAT_CORES.confuso}">${lote} no mesmo dia</span>` : lote) : '-';
    const diasTxt = p._dias_entre_prazo_e_status === null ? 'sem log' :
      (p._dias_entre_prazo_e_status > 0 ? `<span class="dias ${diasClasse(p._dias_entre_prazo_e_status)}">+${p._dias_entre_prazo_e_status}d</span>` : `${p._dias_entre_prazo_e_status}d (antecipado)`);
    tr.innerHTML = `
      <td><span class="proj-id">${p.name}</span></td>
      <td class="cliente">${p.nome_cliente || ''}</td>
      <td>${p.nome_lider_projeto_grv || ''}</td>
      <td>${p.status}</td>
      <td>${p.termino_previsto}</td>
      <td>${p._dia_mudanca ? p._dia_mudanca : '(sem registro no log)'}</td>
      <td>${diasTxt}</td>
      <td>${loteTxt}</td>
    `;
    tbody.appendChild(tr);
  });
}

document.getElementById('busca-finalizados').addEventListener('input', renderFinalizados);
document.getElementById('filtro-lider-finalizados').addEventListener('change', renderFinalizados);

let sortDir2 = {};
document.querySelectorAll('th[data-sort2]').forEach(th => {
  th.addEventListener('click', () => {
    const key = th.dataset.sort2;
    sortDir2[key] = !sortDir2[key];
    TAB2.projetos.sort((a, b) => {
      let va = a[key], vb = b[key];
      if (va === null) va = sortDir2[key] ? Infinity : -Infinity;
      if (vb === null) vb = sortDir2[key] ? Infinity : -Infinity;
      if (typeof va === 'string') { return sortDir2[key] ? va.localeCompare(vb) : vb.localeCompare(va); }
      return sortDir2[key] ? (va - vb) : (vb - va);
    });
    renderFinalizados();
  });
});

renderFinalizados();
```

new_string:
```js
// ==== ABA: Projetos finalizados ====
let anoFinalizadosAtual = 'todos';

function projetosFinalizadosFiltradosPorAno() {
  if (anoFinalizadosAtual === 'todos') return FINALIZADOS.projetos;
  return FINALIZADOS.projetos.filter(p => String(p._ano_inicio) === anoFinalizadosAtual);
}

function renderFinalizados() {
  const busca = document.getElementById('busca-finalizados').value.toLowerCase();
  const lider = document.getElementById('filtro-lider-finalizados').value;
  const base = projetosFinalizadosFiltradosPorAno();

  const comLog = base.filter(p => p._dia_mudanca).length;
  const passouPrazo = base.filter(p => p._dias_entre_prazo_e_status !== null && p._dias_entre_prazo_e_status > 0).length;
  document.getElementById('kpi2-total').textContent = base.length;
  document.getElementById('kpi2-com-log').textContent = comLog;
  document.getElementById('kpi2-passou-prazo').textContent = passouPrazo;

  const loteBase = {};
  base.forEach(p => { if (p._dia_mudanca) loteBase[p._dia_mudanca] = (loteBase[p._dia_mudanca] || 0) + 1; });

  const clusterEl = document.getElementById('cluster-badges');
  clusterEl.innerHTML = '';
  Object.entries(loteBase).filter(c => c[1] >= 2).sort((a, b) => b[1] - a[1]).forEach(([data, qtd]) => {
    const span = document.createElement('span');
    span.className = 'cluster-badge';
    span.innerHTML = `${data}: <b>${qtd} projetos</b>`;
    clusterEl.appendChild(span);
  });

  let rows = base.filter(p => {
    if (lider && p.nome_lider_projeto_grv !== lider) return false;
    if (busca) {
      const alvo = (p.nome_cliente + ' ' + p.name).toLowerCase();
      if (!alvo.includes(busca)) return false;
    }
    return true;
  });
  document.getElementById('count-finalizados').textContent = '(' + rows.length + ' de ' + base.length + ')';
  const tbody = document.getElementById('tbody-finalizados');
  tbody.innerHTML = '';
  rows.forEach(p => {
    const tr = document.createElement('tr');
    const lote = p._dia_mudanca ? loteBase[p._dia_mudanca] : 0;
    const loteTxt = lote ? (lote >= 4 ? `<span class="badge" style="background:${CAT_CORES.confuso}">${lote} no mesmo dia</span>` : lote) : '-';
    const diasTxt = p._dias_entre_prazo_e_status === null ? 'sem log' :
      (p._dias_entre_prazo_e_status > 0 ? `<span class="dias ${diasClasse(p._dias_entre_prazo_e_status)}">+${p._dias_entre_prazo_e_status}d</span>` : `${p._dias_entre_prazo_e_status}d (antecipado)`);
    tr.innerHTML = `
      <td><span class="proj-id">${p.name}</span></td>
      <td class="cliente">${p.nome_cliente || ''}</td>
      <td>${p.nome_lider_projeto_grv || ''}</td>
      <td>${p.status}</td>
      <td>${p.termino_previsto || '-'}</td>
      <td>${p._dia_mudanca ? p._dia_mudanca : '(sem registro no log)'}</td>
      <td>${diasTxt}</td>
      <td>${loteTxt}</td>
    `;
    tbody.appendChild(tr);
  });
}

const lideresSet2 = [...new Set(FINALIZADOS.projetos.map(p => p.nome_lider_projeto_grv))].sort();
const selLider2 = document.getElementById('filtro-lider-finalizados');
lideresSet2.forEach(l => {
  const opt = document.createElement('option');
  opt.value = l; opt.textContent = l;
  selLider2.appendChild(opt);
});

const selAnoFinalizados = document.getElementById('seletor-ano-finalizados');
const optTodosFinalizados = document.createElement('option');
optTodosFinalizados.value = 'todos';
optTodosFinalizados.textContent = 'Todos os anos';
selAnoFinalizados.appendChild(optTodosFinalizados);
[...new Set(FINALIZADOS.projetos.map(p => p._ano_inicio).filter(a => a !== null))]
  .sort((a, b) => b - a)
  .forEach(ano => {
    const opt = document.createElement('option');
    opt.value = String(ano);
    opt.textContent = String(ano);
    selAnoFinalizados.appendChild(opt);
  });
selAnoFinalizados.value = 'todos';
selAnoFinalizados.addEventListener('change', () => {
  anoFinalizadosAtual = selAnoFinalizados.value;
  renderFinalizados();
});

document.getElementById('busca-finalizados').addEventListener('input', renderFinalizados);
document.getElementById('filtro-lider-finalizados').addEventListener('change', renderFinalizados);

let sortDir2 = {};
document.querySelectorAll('th[data-sort2]').forEach(th => {
  th.addEventListener('click', () => {
    const key = th.dataset.sort2;
    sortDir2[key] = !sortDir2[key];
    FINALIZADOS.projetos.sort((a, b) => {
      let va = a[key], vb = b[key];
      if (va === null || va === undefined) va = sortDir2[key] ? Infinity : -Infinity;
      if (vb === null || vb === undefined) vb = sortDir2[key] ? Infinity : -Infinity;
      if (typeof va === 'string') { return sortDir2[key] ? va.localeCompare(vb) : vb.localeCompare(va); }
      return sortDir2[key] ? (va - vb) : (vb - va);
    });
    renderFinalizados();
  });
});

renderFinalizados();
```

- [ ] **Step 3: Rodar o harness**

Run: `node tests/verify_dashboard_html.js dashboard-implantacoes.html`
Expected: as três linhas `OK:` sem erro.

- [ ] **Step 4: Commit**

```bash
git add dashboard-implantacoes.html
git commit -m "feat: seletor de ano/cohort na aba Finalizados, KPIs e clusters recalculados em JS"
```

---

## Task 7: Progresso (percentual + módulos) nas tabelas e no modal

**Files:**
- Modify: `dashboard-implantacoes.html`

**Interfaces:**
- Consumes: campo `modulos: [{nome, status, percentual_conclusao}]` e `percentual_conclusao` em cada projeto de `DATA.vencidos`, `DATA.nao_vencidos` e `FINALIZADOS.projetos` (produzidos no Task 3).

- [ ] **Step 1: CSS da barra de progresso compacta**

old_string:
```css
  .bar-fill.critical { background: var(--critical); }
```
new_string:
```css
  .bar-fill.critical { background: var(--critical); }
  .progresso-mini { display: flex; align-items: center; gap: 6px; font-variant-numeric: tabular-nums; font-size: 11px; white-space: nowrap; }
  .progresso-mini .trilha { width: 48px; height: 6px; border-radius: 3px; background: var(--panel-2); overflow: hidden; }
  .progresso-mini .preenchido { height: 100%; background: var(--good, #30a66d); }
  .modulo-linha { display: flex; justify-content: space-between; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 12px; }
  .modulo-linha:last-child { border-bottom: none; }
```

- [ ] **Step 2: Função reutilizável de progresso + coluna nova em `tabela-nao-vencidos` e `tabela-finalizados`**

old_string:
```html
      <tr>
        <th data-sort="name">Projeto</th>
        <th data-sort="nome_cliente">Cliente</th>
        <th data-sort="nome_lider_projeto_grv">Consultor</th>
        <th data-sort="termino_previsto">Prazo</th>
        <th data-sort="_dias_atraso">Dias até o prazo</th>
        <th>Última anotação</th>
      </tr>
```
new_string:
```html
      <tr>
        <th data-sort="name">Projeto</th>
        <th data-sort="nome_cliente">Cliente</th>
        <th data-sort="nome_lider_projeto_grv">Consultor</th>
        <th data-sort="termino_previsto">Prazo</th>
        <th data-sort="_dias_atraso">Dias até o prazo</th>
        <th data-sort="percentual_conclusao">Progresso</th>
        <th>Última anotação</th>
      </tr>
```

old_string:
```html
        <th data-sort2="_qtd_no_mesmo_dia">Lote (qtd no mesmo dia)</th>
      </tr>
```
new_string:
```html
        <th data-sort2="_qtd_no_mesmo_dia">Lote (qtd no mesmo dia)</th>
        <th data-sort2="percentual_conclusao">Progresso</th>
      </tr>
```

- [ ] **Step 3: Função `progressoMiniHtml` + uso nas três tabelas**

Inserir logo após a definição de `function diasClasse(dias) { ... }`:

old_string:
```js
function diasClasse(dias) {
  if (dias >= 180) return 'critico';
  if (dias >= 60) return 'alto';
  if (dias >= 14) return 'medio';
  return 'baixo';
}
```
new_string:
```js
function diasClasse(dias) {
  if (dias >= 180) return 'critico';
  if (dias >= 60) return 'alto';
  if (dias >= 14) return 'medio';
  return 'baixo';
}

function progressoMiniHtml(percentual) {
  const pct = Math.max(0, Math.min(100, percentual || 0));
  return `<div class="progresso-mini"><div class="trilha"><div class="preenchido" style="width:${pct}%"></div></div>${pct.toFixed(0)}%</div>`;
}

function modulosListaHtml(modulos) {
  if (!modulos || modulos.length === 0) {
    return '<div class="empty-state">Nenhum módulo cadastrado para este projeto.</div>';
  }
  return modulos.map(m => `
    <div class="modulo-linha">
      <span>${escapeHtml(m.nome || '(sem nome)')}</span>
      <span>${escapeHtml(m.status || '-')} · ${(m.percentual_conclusao || 0).toFixed(0)}%</span>
    </div>
  `).join('');
}
```

Adicionar a coluna nas três renderizações. Em `renderVencidos` (a célula de `percentual_conclusao` já existe como texto simples — trocar pela barra):

old_string:
```js
      <td>${(p.percentual_conclusao||0).toFixed(0)}%</td>
```
new_string:
```js
      <td>${progressoMiniHtml(p.percentual_conclusao)}</td>
```

Em `renderNaoVencidos`:

old_string:
```js
      <td>${p.termino_previsto}</td>
      <td>${-p._dias_atraso}d</td>
      <td class="motivo">${p._motivo}</td>
```
new_string:
```js
      <td>${p.termino_previsto}</td>
      <td>${-p._dias_atraso}d</td>
      <td>${progressoMiniHtml(p.percentual_conclusao)}</td>
      <td class="motivo">${p._motivo}</td>
```

Em `renderFinalizados` (bloco já reescrito no Task 6):

old_string:
```js
      <td>${diasTxt}</td>
      <td>${loteTxt}</td>
    `;
```
new_string:
```js
      <td>${diasTxt}</td>
      <td>${loteTxt}</td>
      <td>${progressoMiniHtml(p.percentual_conclusao)}</td>
    `;
```

- [ ] **Step 4: Sub-aba "Progresso" no modal**

old_string:
```html
    <div class="modal-tabs" id="modal-tabs-nav">
      <button class="modal-tab-btn active" data-modal-tab="timeline">Linha do tempo (resumo)</button>
      <button class="modal-tab-btn" data-modal-tab="completo">Todas as anotações</button>
    </div>
    <div class="modal-body">
      <div id="modal-tab-timeline" class="modal-tab-content"></div>
      <div id="modal-tab-completo" class="modal-tab-content hidden"></div>
    </div>
```
new_string:
```html
    <div class="modal-tabs" id="modal-tabs-nav">
      <button class="modal-tab-btn active" data-modal-tab="timeline">Linha do tempo (resumo)</button>
      <button class="modal-tab-btn" data-modal-tab="completo">Todas as anotações</button>
      <button class="modal-tab-btn" data-modal-tab="progresso">Progresso</button>
    </div>
    <div class="modal-body">
      <div id="modal-tab-timeline" class="modal-tab-content"></div>
      <div id="modal-tab-completo" class="modal-tab-content hidden"></div>
      <div id="modal-tab-progresso" class="modal-tab-content hidden"></div>
    </div>
```

Preencher a nova aba dentro de `abrirModalAnotacoes` (que já localiza `proj` em `DATA.vencidos`):

old_string:
```js
  document.getElementById('modal-anotacoes').classList.remove('hidden');
}

function fecharModalAnotacoes() {
```
new_string:
```js
  document.getElementById('modal-tab-progresso').innerHTML = proj
    ? `<div style="margin-bottom:10px">${progressoMiniHtml(proj.percentual_conclusao)}</div>` + modulosListaHtml(proj.modulos)
    : '<div class="empty-state">Progresso não disponível.</div>';

  document.getElementById('modal-anotacoes').classList.remove('hidden');
}

function fecharModalAnotacoes() {
```

O botão "Progresso" já funciona automaticamente: o listener genérico de `.modal-tab-btn` (final do script) troca `active`/`hidden` por `data-modal-tab`, sem precisar de código novo.

- [ ] **Step 5: Rodar o harness**

Run: `node tests/verify_dashboard_html.js dashboard-implantacoes.html`
Expected: as três linhas `OK:` sem erro.

- [ ] **Step 6: Commit**

```bash
git add dashboard-implantacoes.html
git commit -m "feat: progresso (percentual + modulos) nas tabelas e no modal de detalhes"
```

---

## Task 8: Motivo por tema direto do Python + "Onde agir primeiro" com prioridade

**Files:**
- Modify: `dashboard-implantacoes.html`

**Interfaces:**
- Consumes: `p._tema` (string), `p._prioridade` (`"alta"|"normal"`), `p._dias_sem_atualizacao` (`int|null`) — todos já presentes em cada item de `DATA.vencidos` desde o Task 3.

- [ ] **Step 1: Trocar `MOTIVO_TEMA[p.name]` por `p._tema` no gráfico de motivos**

old_string:
```js
const motivoCount = {};
DATA.vencidos.forEach(p => {
  const tema = MOTIVO_TEMA[p.name] || "Outros";
  motivoCount[tema] = (motivoCount[tema] || 0) + 1;
});
```
new_string:
```js
const motivoCount = {};
DATA.vencidos.forEach(p => {
  motivoCount[p._tema] = (motivoCount[p._tema] || 0) + 1;
});
```

old_string:
```js
    const critico = tema.startsWith('Sem motivo claro');
```
new_string:
```js
    const critico = tema.startsWith('Sem motivo claro') || tema.startsWith('Não identificado');
```

old_string:
```js
    if (filtroTemaAtivo && (MOTIVO_TEMA[p.name] || 'Outros') !== filtroTemaAtivo) return false;
```
new_string:
```js
    if (filtroTemaAtivo && p._tema !== filtroTemaAtivo) return false;
```

- [ ] **Step 2: Estender "Onde agir primeiro" com o ranking de prioridade**

old_string:
```js
  itens.push({ critico: true, html: `${semMotivo.length} projetos não têm nenhuma explicação aceitável registrada.`, comBotao: true });

  listEl.innerHTML = itens.map(it => `<li><span class="dot${it.critico ? ' critical' : ''}"></span><span>${it.html}</span></li>`).join('');
```
new_string:
```js
  itens.push({ critico: true, html: `${semMotivo.length} projetos não têm nenhuma explicação aceitável registrada.`, comBotao: true });

  const criticos = DATA.vencidos
    .filter(p => p._prioridade === 'alta')
    .sort((a, b) => (b._dias_sem_atualizacao || 0) - (a._dias_sem_atualizacao || 0))
    .slice(0, 5);
  if (criticos.length) {
    const descricoes = criticos.map(p => {
      const semAtualizacao = p._dias_sem_atualizacao != null ? `, ${p._dias_sem_atualizacao}d sem atualização` : '';
      return `<b>${p.nome_cliente}</b> (${p._dias_atraso}d atrasado${semAtualizacao})`;
    }).join(', ');
    itens.push({ critico: true, html: `${criticos.length} projeto${criticos.length > 1 ? 's' : ''} em atraso crítico (30+ dias vencido): ${descricoes}.` });
  }

  listEl.innerHTML = itens.map(it => `<li><span class="dot${it.critico ? ' critical' : ''}"></span><span>${it.html}</span></li>`).join('');
```

- [ ] **Step 3: Rodar o harness**

Run: `node tests/verify_dashboard_html.js dashboard-implantacoes.html`
Expected: as três linhas `OK:` sem erro.

- [ ] **Step 4: Abrir o arquivo num navegador e conferir visualmente**

Run: abrir `dashboard-implantacoes.html` diretamente no navegador (duplo clique ou `start dashboard-implantacoes.html` no Windows).
Conferir manualmente: aba "Visão geral" com seletor de ano funcionando, aba "Atrasados" com coluna de progresso e "Onde agir primeiro" mostrando o novo item de atraso crítico (quando houver projeto com 30+ dias), aba "Finalizados" com seletor de ano e coluna de progresso, modal com a aba "Progresso" listando os módulos.

- [ ] **Step 5: Commit**

```bash
git add dashboard-implantacoes.html
git commit -m "feat: motivo por tema direto do pipeline e onde-agir-primeiro com prioridade por atraso critico"
```

---

## Self-Review

**Cobertura da spec:**
- Todos os projetos, não só 2026 → Tasks 3, 5, 6 (pipeline sem filtro de data + seletores de ano/cohort nas duas abas que antes eram fixas em 2026; a aba Atrasados já era all-time e não precisou mudar).
- Progresso interno do projeto (percentual + módulos) → Tasks 3 (dados) e 7 (UI: tabelas + modal).
- Motor de insights por regras → Task 1 (lógica pura), Task 3 (aplicação), Task 8 (exposição na UI: gráfico de motivos e "onde agir primeiro").
- Atualização via script local, sem servidor permanente → Tasks 2–3 (`atualizar_dados.py` + `.bat`), Task 4 (consumo do arquivo gerado + badge de última atualização).
- Limitação assumida sobre motivo automatizado → refletida no `REVISAR_MANUALMENTE` (Task 1) e na "Não identificado" no gráfico/filtro (Task 8).
- Tratamento de erro (prazo não informado, sem anotação, falha de API não sobrescreve arquivo) → Tasks 1 (`calcular_atrasado`/`dias_desde_ultima_anotacao` retornam `None`/`"prazo_nao_informado"`) e 3 (`escrever_arquivo_js` atômico + `main()` aborta sem sobrescrever).

**Placeholders:** nenhum "TBD"/"implementar depois" — todo código é completo e todos os nomes de campo foram confirmados ao vivo contra a API (DocType `SAG Modulo`, child table `anotacoes` de `SAG Projeto`, formato do `Version.data`).

**Consistência de tipos/nomes:** `DASHBOARD_DATA.atrasados` → `DATA` (Task 4) é usado de forma idêntica em Tasks 5, 7, 8. `VISAO_GERAL`/`FINALIZADOS` (Task 4) usados exatamente com esses nomes em Tasks 5/6/7. Campos `_tema`/`_prioridade`/`_dias_sem_atualizacao`/`_numero_pausas`/`modulos` são produzidos em `montar_projeto_atrasado` (Task 3) e consumidos com os mesmos nomes em Tasks 7–8.
