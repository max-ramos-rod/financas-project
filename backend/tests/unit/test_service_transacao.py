from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.models import StatusLiquidacao, TipoConta, TipoTransacao, Transacao
from app.services.transacao import TransacaoService

from .conftest import FakeTransacaoRepository, make_conta, make_db, make_transacao_create

USER_ID = 1


def _service(conta=None) -> tuple[TransacaoService, FakeTransacaoRepository, MagicMock]:
    repo = FakeTransacaoRepository()
    svc = TransacaoService(repo=repo)
    db = make_db(conta)
    return svc, repo, db


@patch("app.services.transacao.recalcular_meta")
@patch("app.services.transacao.recalcular_orcamento_mes")
class TestCriarSimples:
    def test_saida_prevista_nao_altera_saldo(self, mock_orc, mock_meta):
        conta = make_conta(saldo=500.0)
        svc, repo, db = _service(conta)
        tc = make_transacao_create(
            tipo=TipoTransacao.SAIDA,
            status_liquidacao=StatusLiquidacao.PREVISTO,
            valor=100.0,
        )
        svc.criar(db, tc, USER_ID)
        assert conta.saldo == 500.0

    def test_entrada_liquidada_aumenta_saldo(self, mock_orc, mock_meta):
        conta = make_conta(saldo=200.0)
        svc, repo, db = _service(conta)
        tc = make_transacao_create(
            tipo=TipoTransacao.ENTRADA,
            status_liquidacao=StatusLiquidacao.LIQUIDADO,
            valor=300.0,
            data_liquidacao=date(2024, 1, 15),
        )
        svc.criar(db, tc, USER_ID)
        assert conta.saldo == pytest.approx(500.0)

    def test_saida_liquidada_diminui_saldo(self, mock_orc, mock_meta):
        conta = make_conta(saldo=500.0)
        svc, repo, db = _service(conta)
        tc = make_transacao_create(
            tipo=TipoTransacao.SAIDA,
            status_liquidacao=StatusLiquidacao.LIQUIDADO,
            valor=150.0,
            data_liquidacao=date(2024, 1, 15),
        )
        svc.criar(db, tc, USER_ID)
        assert conta.saldo == pytest.approx(350.0)

    def test_criar_retorna_transacao_com_dados_corretos(self, mock_orc, mock_meta):
        conta = make_conta()
        svc, repo, db = _service(conta)
        tc = make_transacao_create(descricao="Aluguel", valor=800.0)
        result = svc.criar(db, tc, USER_ID)
        assert isinstance(result, Transacao)
        assert result.descricao == "Aluguel"
        assert result.valor == pytest.approx(800.0)

    def test_conta_nao_encontrada_levanta_erro(self, mock_orc, mock_meta):
        svc, repo, db = _service(conta=None)
        tc = make_transacao_create()
        with pytest.raises(ValueError, match="Conta nao encontrada"):
            svc.criar(db, tc, USER_ID)

    def test_cartao_credito_saida_vira_previsto(self, mock_orc, mock_meta):
        conta = make_conta(tipo=TipoConta.CARTAO_CREDITO)
        svc, repo, db = _service(conta)
        tc = make_transacao_create(
            tipo=TipoTransacao.SAIDA,
            status_liquidacao=StatusLiquidacao.LIQUIDADO,
            data_liquidacao=date(2024, 1, 15),
        )
        result = svc.criar(db, tc, USER_ID)
        assert result.status_liquidacao == StatusLiquidacao.PREVISTO

    def test_commit_chamado(self, mock_orc, mock_meta):
        conta = make_conta()
        svc, repo, db = _service(conta)
        tc = make_transacao_create()
        svc.criar(db, tc, USER_ID)
        db.commit.assert_called_once()


@patch("app.services.parcelamento.recalcular_meta")
@patch("app.services.parcelamento.recalcular_orcamento_mes")
class TestCriarParcelado:
    def test_parcelado_cria_todas_parcelas(self, mock_orc, mock_meta):
        conta = make_conta(saldo=0.0)
        svc, repo, db = _service(conta)
        tc = make_transacao_create(parcelado=True, total_parcelas=3, valor=90.0)
        svc.criar(db, tc, USER_ID)
        assert len(repo.saved) == 3

    def test_parcelado_retorna_primeira_parcela(self, mock_orc, mock_meta):
        conta = make_conta(saldo=0.0)
        svc, repo, db = _service(conta)
        tc = make_transacao_create(parcelado=True, total_parcelas=3, valor=90.0)
        result = svc.criar(db, tc, USER_ID)
        assert result.parcela_atual == 1

    def test_parcelado_parcela1_herda_status_parcelado_demais_previsto(self, mock_orc, mock_meta):
        conta = make_conta(saldo=0.0)
        svc, repo, db = _service(conta)
        tc = make_transacao_create(
            parcelado=True,
            total_parcelas=2,
            valor=50.0,
            status_liquidacao=StatusLiquidacao.LIQUIDADO,
            data_liquidacao=date(2024, 1, 15),
        )
        svc.criar(db, tc, USER_ID)
        parcelas = repo.saved
        assert parcelas[0].status_liquidacao == StatusLiquidacao.LIQUIDADO
        assert parcelas[1].status_liquidacao == StatusLiquidacao.PREVISTO

    def test_parcelado_recorrente_levanta_erro(self, mock_orc, mock_meta):
        conta = make_conta()
        svc, repo, db = _service(conta)
        tc = make_transacao_create(parcelado=True, total_parcelas=2, recorrente=True)
        with pytest.raises(ValueError, match="parcelada e recorrente"):
            svc.criar(db, tc, USER_ID)

    def test_parcelado_dizimo_levanta_erro(self, mock_orc, mock_meta):
        conta = make_conta()
        svc, repo, db = _service(conta)
        tc = make_transacao_create(
            parcelado=True,
            total_parcelas=2,
            tipo=TipoTransacao.ENTRADA,
            tem_dizimo=True,
        )
        with pytest.raises(ValueError, match="dizimo"):
            svc.criar(db, tc, USER_ID)

    def test_parcelado_avanca_meses(self, mock_orc, mock_meta):
        conta = make_conta(saldo=0.0)
        svc, repo, db = _service(conta)
        tc = make_transacao_create(
            parcelado=True,
            total_parcelas=3,
            data=date(2024, 1, 15),
        )
        svc.criar(db, tc, USER_ID)
        datas = [t.data for t in repo.saved]
        assert datas[0] == date(2024, 1, 15)
        assert datas[1] == date(2024, 2, 15)
        assert datas[2] == date(2024, 3, 15)


@patch("app.services.dizimo.obter_categoria_dizimo")
@patch("app.services.transacao.recalcular_meta")
@patch("app.services.transacao.recalcular_orcamento_mes")
class TestCriarComDizimo:
    def test_dizimo_cria_saida_automatica(self, mock_orc, mock_meta, mock_cat):
        categoria_dizimo = MagicMock()
        categoria_dizimo.id = 99
        mock_cat.return_value = categoria_dizimo

        conta = make_conta(saldo=1000.0)
        svc, repo, db = _service(conta)
        tc = make_transacao_create(
            tipo=TipoTransacao.ENTRADA,
            tem_dizimo=True,
            percentual_dizimo=10.0,
            valor=1000.0,
            status_liquidacao=StatusLiquidacao.PREVISTO,
        )
        svc.criar(db, tc, USER_ID)

        # ENTRADA is flushed via self._repo._save(); SAIDA dízimo via db.add()
        assert len(repo.saved) == 1
        assert repo.saved[0].tipo == TipoTransacao.ENTRADA

        # The dízimo Transacao was passed to db.add()
        db_add_calls = [call[0][0] for call in db.add.call_args_list if isinstance(call[0][0], Transacao)]
        dizimo = next((t for t in db_add_calls if getattr(t, "e_dizimo", False)), None)
        assert dizimo is not None
        assert dizimo.tipo == TipoTransacao.SAIDA
        assert dizimo.valor == pytest.approx(100.0)

    def test_dizimo_saida_nao_gera_dizimo(self, mock_orc, mock_meta, mock_cat):
        conta = make_conta()
        svc, repo, db = _service(conta)
        tc = make_transacao_create(
            tipo=TipoTransacao.SAIDA,
            tem_dizimo=True,
        )
        svc.criar(db, tc, USER_ID)
        assert all(not t.e_dizimo for t in repo.saved)


@patch("app.services.transacao.get_transacao")
@patch("app.services.transacao.recalcular_meta")
@patch("app.services.transacao.recalcular_orcamento_mes")
class TestDeletar:
    def _make_transacao(self, conta_id=1, meta_id=None, categoria_id=1, valor=100.0) -> Transacao:
        t = Transacao()
        t.id = 1
        t.user_id = USER_ID
        t.conta_id = conta_id
        t.meta_id = meta_id
        t.categoria_id = categoria_id
        t.valor = valor
        t.valor_multa = 0.0
        t.valor_juros = 0.0
        t.valor_desconto = 0.0
        t.tipo = TipoTransacao.SAIDA
        t.status_liquidacao = StatusLiquidacao.LIQUIDADO
        t.data = date(2024, 1, 15)
        t.e_dizimo = False
        t.tem_dizimo = False
        t.transacao_dizimo_uuid = None
        return t

    def test_deletar_inexistente_retorna_false(self, mock_orc, mock_meta, mock_get):
        mock_get.return_value = None
        svc, repo, db = _service()
        result = svc.deletar(db, 999, USER_ID)
        assert result is False

    def test_deletar_e_dizimo_levanta_erro(self, mock_orc, mock_meta, mock_get):
        t = self._make_transacao()
        t.e_dizimo = True
        mock_get.return_value = t
        conta = make_conta()
        svc, repo, db = _service(conta)
        with pytest.raises(ValueError, match="dizimo"):
            svc.deletar(db, 1, USER_ID)

    def test_deletar_remove_do_repo(self, mock_orc, mock_meta, mock_get):
        t = self._make_transacao()
        mock_get.return_value = t
        conta = make_conta()
        repo = FakeTransacaoRepository()
        repo._save(None, t)
        svc = TransacaoService(repo=repo)
        db = make_db(conta)
        result = svc.deletar(db, 1, USER_ID)
        assert result is True
        assert len(repo.saved) == 0

    def test_deletar_reverte_saldo_liquidado(self, mock_orc, mock_meta, mock_get):
        t = self._make_transacao(valor=200.0)
        mock_get.return_value = t
        conta = make_conta(saldo=300.0)
        repo = FakeTransacaoRepository()
        repo._save(None, t)
        svc = TransacaoService(repo=repo)
        db = make_db(conta)
        svc.deletar(db, 1, USER_ID)
        assert conta.saldo == pytest.approx(500.0)

    def test_deletar_commit_chamado(self, mock_orc, mock_meta, mock_get):
        t = self._make_transacao()
        mock_get.return_value = t
        conta = make_conta()
        repo = FakeTransacaoRepository()
        repo._save(None, t)
        svc = TransacaoService(repo=repo)
        db = make_db(conta)
        svc.deletar(db, 1, USER_ID)
        db.commit.assert_called_once()
