from datetime import date, timedelta

import pytest

from app.domain.transacao import impacto_no_saldo, normalizar_atraso, valor_meta
from app.models import StatusLiquidacao, TipoTransacao, Transacao


def _t(**kwargs) -> Transacao:
    defaults = dict(
        valor=100.0,
        valor_multa=0.0,
        valor_juros=0.0,
        valor_desconto=0.0,
        tipo=TipoTransacao.SAIDA,
        status_liquidacao=StatusLiquidacao.PREVISTO,
        data_vencimento=None,
    )
    defaults.update(kwargs)
    t = Transacao()
    for k, v in defaults.items():
        setattr(t, k, v)
    return t


class TestImpactoNoSaldo:
    def test_previsto_nao_afeta_saldo(self):
        t = _t(status_liquidacao=StatusLiquidacao.PREVISTO, tipo=TipoTransacao.SAIDA)
        assert impacto_no_saldo(t) == 0.0

    def test_atrasado_nao_afeta_saldo(self):
        t = _t(status_liquidacao=StatusLiquidacao.ATRASADO, tipo=TipoTransacao.SAIDA)
        assert impacto_no_saldo(t) == 0.0

    def test_cancelado_nao_afeta_saldo(self):
        t = _t(status_liquidacao=StatusLiquidacao.CANCELADO, tipo=TipoTransacao.SAIDA)
        assert impacto_no_saldo(t) == 0.0

    def test_liquidado_saida_subtrai(self):
        t = _t(status_liquidacao=StatusLiquidacao.LIQUIDADO, tipo=TipoTransacao.SAIDA, valor=200.0)
        assert impacto_no_saldo(t) == -200.0

    def test_liquidado_entrada_soma(self):
        t = _t(status_liquidacao=StatusLiquidacao.LIQUIDADO, tipo=TipoTransacao.ENTRADA, valor=300.0)
        assert impacto_no_saldo(t) == 300.0

    def test_liquidado_saida_com_juros(self):
        t = _t(
            status_liquidacao=StatusLiquidacao.LIQUIDADO,
            tipo=TipoTransacao.SAIDA,
            valor=100.0,
            valor_juros=10.0,
        )
        assert impacto_no_saldo(t) == -110.0

    def test_liquidado_entrada_com_desconto(self):
        t = _t(
            status_liquidacao=StatusLiquidacao.LIQUIDADO,
            tipo=TipoTransacao.ENTRADA,
            valor=100.0,
            valor_desconto=15.0,
        )
        assert impacto_no_saldo(t) == 85.0


class TestNormalizarAtraso:
    def test_previsto_passado_vira_atrasado(self):
        t = _t(
            status_liquidacao=StatusLiquidacao.PREVISTO,
            data_vencimento=date.today() - timedelta(days=1),
        )
        normalizar_atraso(t)
        assert t.status_liquidacao == StatusLiquidacao.ATRASADO

    def test_previsto_hoje_permanece_previsto(self):
        t = _t(
            status_liquidacao=StatusLiquidacao.PREVISTO,
            data_vencimento=date.today(),
        )
        normalizar_atraso(t)
        assert t.status_liquidacao == StatusLiquidacao.PREVISTO

    def test_previsto_futuro_permanece_previsto(self):
        t = _t(
            status_liquidacao=StatusLiquidacao.PREVISTO,
            data_vencimento=date.today() + timedelta(days=5),
        )
        normalizar_atraso(t)
        assert t.status_liquidacao == StatusLiquidacao.PREVISTO

    def test_liquidado_passado_nao_muda(self):
        t = _t(
            status_liquidacao=StatusLiquidacao.LIQUIDADO,
            data_vencimento=date.today() - timedelta(days=10),
        )
        normalizar_atraso(t)
        assert t.status_liquidacao == StatusLiquidacao.LIQUIDADO

    def test_sem_data_vencimento_nao_muda(self):
        t = _t(status_liquidacao=StatusLiquidacao.PREVISTO, data_vencimento=None)
        normalizar_atraso(t)
        assert t.status_liquidacao == StatusLiquidacao.PREVISTO


class TestValorMeta:
    def test_cancelado_retorna_zero(self):
        t = _t(status_liquidacao=StatusLiquidacao.CANCELADO, tipo=TipoTransacao.SAIDA, valor=500.0)
        assert valor_meta(t) == 0.0

    def test_entrada_retorna_positivo(self):
        t = _t(status_liquidacao=StatusLiquidacao.LIQUIDADO, tipo=TipoTransacao.ENTRADA, valor=200.0)
        assert valor_meta(t) == 200.0

    def test_saida_retorna_negativo(self):
        t = _t(status_liquidacao=StatusLiquidacao.LIQUIDADO, tipo=TipoTransacao.SAIDA, valor=150.0)
        assert valor_meta(t) == -150.0

    def test_previsto_entrada_conta_para_meta(self):
        t = _t(status_liquidacao=StatusLiquidacao.PREVISTO, tipo=TipoTransacao.ENTRADA, valor=100.0)
        assert valor_meta(t) == 100.0
