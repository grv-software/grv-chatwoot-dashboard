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
            {"name": "P1", "status": "Aberto", "inicio_previsto": "2026-01-01", "termino_previsto": "2026-01-01"},
            {"name": "P2", "status": "Aberto", "inicio_previsto": "2026-02-01", "termino_previsto": "2027-01-01"},
            {"name": "P3", "status": "Consulta", "inicio_previsto": "2026-01-01", "termino_previsto": "2026-01-01"},
            {"name": "P4", "status": "Pausado", "inicio_previsto": "2025-01-01", "termino_previsto": None},
            {"name": "P5", "status": "Cancelado", "inicio_previsto": "2025-06-01", "termino_previsto": None},
        ]
        info_conclusao = {"P3": 5}
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


if __name__ == "__main__":
    unittest.main()
