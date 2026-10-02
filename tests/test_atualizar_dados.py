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
