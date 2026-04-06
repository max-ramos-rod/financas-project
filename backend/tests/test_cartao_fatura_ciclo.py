from datetime import date

from app.domain.cartao_fatura import calcular_periodo_fatura, calcular_vencimento_fatura


def test_calcular_periodo_fatura_antes_do_fechamento():
    inicio, fim = calcular_periodo_fatura(date(2026, 4, 4), 20)

    assert inicio == date(2026, 2, 21)
    assert fim == date(2026, 3, 20)


def test_calcular_periodo_fatura_apos_o_fechamento():
    inicio, fim = calcular_periodo_fatura(date(2026, 4, 25), 20)

    assert inicio == date(2026, 3, 21)
    assert fim == date(2026, 4, 20)


def test_calcular_periodo_fatura_com_fechamento_no_fim_de_fevereiro():
    inicio, fim = calcular_periodo_fatura(date(2026, 3, 1), 31)

    assert inicio == date(2026, 2, 1)
    assert fim == date(2026, 2, 28)


def test_calcular_vencimento_fatura_no_mes_seguinte_quando_necessario():
    vencimento = calcular_vencimento_fatura(date(2026, 4, 20), 10)

    assert vencimento == date(2026, 5, 10)
