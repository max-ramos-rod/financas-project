from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import Conta, ContaCartaoCiclo, StatusLiquidacao, TipoConta, TipoTransacao, Transacao


@dataclass
class ResumoFatura:
    conta_id: int
    conta_nome: str
    competencia_ano: int
    competencia_mes: int
    periodo_inicio: date
    periodo_fim: date
    dia_fechamento: int
    dia_vencimento: int
    data_fechamento_prevista: date
    data_fechamento_real: date | None
    data_fechamento_fatura: date
    data_vencimento_prevista: date
    data_vencimento_fatura: date
    data_vencimento_real: date | None
    observacao_ciclo: str | None
    total_itens: int
    valor_total: float
    valor_pago: float
    valor_a_pagar: float
    itens: list[Transacao]


def safe_date_with_day(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, monthrange(year, month)[1]))


def shift_month(base: date, months: int) -> date:
    month_index = (base.month - 1) + months
    year = base.year + (month_index // 12)
    month = (month_index % 12) + 1
    return date(year, month, 1)


def calcular_periodo_fatura(ref_date: date, dia_fechamento: int) -> tuple[date, date]:
    fechamento_mes_atual = safe_date_with_day(ref_date.year, ref_date.month, dia_fechamento)
    if ref_date.day >= fechamento_mes_atual.day:
        periodo_fim = fechamento_mes_atual
    else:
        mes_anterior = shift_month(ref_date, -1)
        periodo_fim = safe_date_with_day(mes_anterior.year, mes_anterior.month, dia_fechamento)

    mes_antes = shift_month(periodo_fim, -1)
    fechamento_anterior = safe_date_with_day(mes_antes.year, mes_antes.month, dia_fechamento)
    periodo_inicio = fechamento_anterior + timedelta(days=1)
    return periodo_inicio, periodo_fim


def calcular_vencimento_fatura(periodo_fim: date, dia_vencimento: int) -> date:
    if dia_vencimento > periodo_fim.day:
        return safe_date_with_day(periodo_fim.year, periodo_fim.month, dia_vencimento)
    proximo_mes = shift_month(periodo_fim, 1)
    return safe_date_with_day(proximo_mes.year, proximo_mes.month, dia_vencimento)


def _competencia_anterior(ano: int, mes: int) -> tuple[int, int]:
    if mes == 1:
        return ano - 1, 12
    return ano, mes - 1


def _competencia_seguinte(ano: int, mes: int) -> tuple[int, int]:
    if mes == 12:
        return ano + 1, 1
    return ano, mes + 1


def _fechamento_previsto_competencia(ano: int, mes: int, dia_fechamento: int) -> date:
    return safe_date_with_day(ano, mes, dia_fechamento)


def _buscar_ciclo_override(
    db: Session,
    *,
    conta_id: int,
    competencia_ano: int,
    competencia_mes: int,
) -> ContaCartaoCiclo | None:
    return (
        db.query(ContaCartaoCiclo)
        .filter(
            ContaCartaoCiclo.conta_id == conta_id,
            ContaCartaoCiclo.competencia_ano == competencia_ano,
            ContaCartaoCiclo.competencia_mes == competencia_mes,
        )
        .first()
    )


def _dados_basicos_competencia(
    db: Session,
    *,
    conta: Conta,
    competencia_ano: int,
    competencia_mes: int,
) -> tuple[ContaCartaoCiclo | None, date, date, date | None, date | None, str | None]:
    data_fechamento_prevista = _fechamento_previsto_competencia(competencia_ano, competencia_mes, conta.dia_fechamento)
    data_vencimento_prevista = calcular_vencimento_fatura(data_fechamento_prevista, conta.dia_vencimento)
    ciclo = _buscar_ciclo_override(
        db,
        conta_id=conta.id,
        competencia_ano=competencia_ano,
        competencia_mes=competencia_mes,
    )
    data_fechamento_real = ciclo.data_fechamento_real if ciclo else None
    data_vencimento_real = ciclo.data_vencimento_real if ciclo else None
    observacao = ciclo.observacao if ciclo else None
    return (
        ciclo,
        data_fechamento_prevista,
        data_vencimento_prevista,
        data_fechamento_real,
        data_vencimento_real,
        observacao,
    )


def obter_datas_ciclo_fatura(
    db: Session,
    *,
    conta: Conta,
    competencia_ano: int,
    competencia_mes: int,
) -> dict[str, date | int | str | None]:
    if conta.dia_fechamento is None or conta.dia_vencimento is None:
        raise ValueError("Cartao sem fechamento/vencimento configurado.")

    (
        _ciclo,
        data_fechamento_prevista,
        data_vencimento_prevista,
        data_fechamento_real,
        data_vencimento_real,
        observacao,
    ) = _dados_basicos_competencia(
        db,
        conta=conta,
        competencia_ano=competencia_ano,
        competencia_mes=competencia_mes,
    )

    data_fechamento_fatura = data_fechamento_real or data_fechamento_prevista
    data_vencimento_fatura = data_vencimento_real or data_vencimento_prevista

    competencia_ano_anterior, competencia_mes_anterior = _competencia_anterior(competencia_ano, competencia_mes)
    (
        _ciclo_anterior,
        data_fechamento_prevista_anterior,
        _data_vencimento_prevista_anterior,
        data_fechamento_real_anterior,
        _data_vencimento_real_anterior,
        _observacao_anterior,
    ) = _dados_basicos_competencia(
        db,
        conta=conta,
        competencia_ano=competencia_ano_anterior,
        competencia_mes=competencia_mes_anterior,
    )
    data_fechamento_anterior = data_fechamento_real_anterior or data_fechamento_prevista_anterior
    periodo_inicio = data_fechamento_anterior + timedelta(days=1)

    return {
        "competencia_ano": competencia_ano,
        "competencia_mes": competencia_mes,
        "periodo_inicio": periodo_inicio,
        "periodo_fim": data_fechamento_fatura,
        "data_fechamento_prevista": data_fechamento_prevista,
        "data_fechamento_real": data_fechamento_real,
        "data_fechamento_fatura": data_fechamento_fatura,
        "data_vencimento_prevista": data_vencimento_prevista,
        "data_vencimento_real": data_vencimento_real,
        "data_vencimento_fatura": data_vencimento_fatura,
        "observacao_ciclo": observacao,
    }


def determinar_competencia_fatura_atual(
    db: Session,
    *,
    conta: Conta,
    ref_date: date,
) -> tuple[int, int]:
    competencia_ano = ref_date.year
    competencia_mes = ref_date.month
    dados_mes_atual = obter_datas_ciclo_fatura(
        db,
        conta=conta,
        competencia_ano=competencia_ano,
        competencia_mes=competencia_mes,
    )
    if ref_date <= dados_mes_atual["periodo_fim"]:
        return competencia_ano, competencia_mes
    return _competencia_seguinte(competencia_ano, competencia_mes)


def valor_efetivo_transacao(transacao: Transacao) -> float:
    return max(
        0.0,
        (transacao.valor or 0)
        + (transacao.valor_multa or 0)
        + (transacao.valor_juros or 0)
        - (transacao.valor_desconto or 0),
    )


def _obter_resumo_fatura_por_competencia(
    db: Session,
    *,
    user_id: int,
    conta: Conta,
    competencia_ano: int,
    competencia_mes: int,
) -> ResumoFatura:
    if conta.tipo != TipoConta.CARTAO_CREDITO:
        raise ValueError("Conta nao e cartao de credito.")
    if conta.dia_fechamento is None or conta.dia_vencimento is None:
        raise ValueError("Cartao sem fechamento/vencimento configurado.")

    dados_ciclo = obter_datas_ciclo_fatura(
        db,
        conta=conta,
        competencia_ano=competencia_ano,
        competencia_mes=competencia_mes,
    )
    periodo_inicio = dados_ciclo["periodo_inicio"]
    periodo_fim = dados_ciclo["periodo_fim"]
    vencimento_fatura = dados_ciclo["data_vencimento_fatura"]

    transacoes = (
        db.query(Transacao)
        .filter(
            Transacao.user_id == user_id,
            Transacao.conta_id == conta.id,
            Transacao.tipo == TipoTransacao.SAIDA,
            Transacao.data >= periodo_inicio,
            Transacao.data <= periodo_fim,
            Transacao.status_liquidacao != StatusLiquidacao.CANCELADO,
        )
        .order_by(Transacao.data.asc(), Transacao.id.asc())
        .all()
    )

    valor_total = sum(valor_efetivo_transacao(item) for item in transacoes)
    valor_pago = sum(valor_efetivo_transacao(item) for item in transacoes if item.status_liquidacao == StatusLiquidacao.LIQUIDADO)
    valor_a_pagar = sum(
        valor_efetivo_transacao(item)
        for item in transacoes
        if item.status_liquidacao in [StatusLiquidacao.PREVISTO, StatusLiquidacao.ATRASADO]
    )

    return ResumoFatura(
        conta_id=conta.id,
        conta_nome=conta.nome,
        competencia_ano=competencia_ano,
        competencia_mes=competencia_mes,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        dia_fechamento=conta.dia_fechamento,
        dia_vencimento=conta.dia_vencimento,
        data_fechamento_prevista=dados_ciclo["data_fechamento_prevista"],
        data_fechamento_real=dados_ciclo["data_fechamento_real"],
        data_fechamento_fatura=dados_ciclo["data_fechamento_fatura"],
        data_vencimento_prevista=dados_ciclo["data_vencimento_prevista"],
        data_vencimento_fatura=vencimento_fatura,
        data_vencimento_real=dados_ciclo["data_vencimento_real"],
        observacao_ciclo=dados_ciclo["observacao_ciclo"],
        total_itens=len(transacoes),
        valor_total=valor_total,
        valor_pago=valor_pago,
        valor_a_pagar=valor_a_pagar,
        itens=transacoes,
    )


def obter_resumo_fatura_por_competencia(
    db: Session,
    *,
    user_id: int,
    conta: Conta,
    competencia_ano: int,
    competencia_mes: int,
) -> ResumoFatura:
    return _obter_resumo_fatura_por_competencia(
        db,
        user_id=user_id,
        conta=conta,
        competencia_ano=competencia_ano,
        competencia_mes=competencia_mes,
    )


def obter_resumo_fatura_atual(
    db: Session,
    *,
    user_id: int,
    conta: Conta,
    ref_date: date | None = None,
) -> ResumoFatura:
    referencia = ref_date or date.today()
    competencia_ano, competencia_mes = determinar_competencia_fatura_atual(
        db,
        conta=conta,
        ref_date=referencia,
    )
    resumo = _obter_resumo_fatura_por_competencia(
        db,
        user_id=user_id,
        conta=conta,
        competencia_ano=competencia_ano,
        competencia_mes=competencia_mes,
    )
    itens_em_aberto = [
        item for item in resumo.itens
        if item.status_liquidacao in [StatusLiquidacao.PREVISTO, StatusLiquidacao.ATRASADO]
    ]
    return ResumoFatura(
        conta_id=resumo.conta_id,
        conta_nome=resumo.conta_nome,
        competencia_ano=resumo.competencia_ano,
        competencia_mes=resumo.competencia_mes,
        periodo_inicio=resumo.periodo_inicio,
        periodo_fim=resumo.periodo_fim,
        dia_fechamento=resumo.dia_fechamento,
        dia_vencimento=resumo.dia_vencimento,
        data_fechamento_prevista=resumo.data_fechamento_prevista,
        data_fechamento_real=resumo.data_fechamento_real,
        data_fechamento_fatura=resumo.data_fechamento_fatura,
        data_vencimento_prevista=resumo.data_vencimento_prevista,
        data_vencimento_fatura=resumo.data_vencimento_fatura,
        data_vencimento_real=resumo.data_vencimento_real,
        observacao_ciclo=resumo.observacao_ciclo,
        total_itens=len(itens_em_aberto),
        valor_total=resumo.valor_a_pagar,
        valor_pago=0.0,
        valor_a_pagar=resumo.valor_a_pagar,
        itens=itens_em_aberto,
    )


def obter_resumo_fatura_fechada_atual(
    db: Session,
    *,
    user_id: int,
    conta: Conta,
    ref_date: date | None = None,
) -> ResumoFatura:
    referencia = ref_date or date.today()
    competencia_aberta_ano, competencia_aberta_mes = determinar_competencia_fatura_atual(
        db,
        conta=conta,
        ref_date=referencia,
    )
    competencia_fechada_ano, competencia_fechada_mes = _competencia_anterior(
        competencia_aberta_ano,
        competencia_aberta_mes,
    )
    return _obter_resumo_fatura_por_competencia(
        db,
        user_id=user_id,
        conta=conta,
        competencia_ano=competencia_fechada_ano,
        competencia_mes=competencia_fechada_mes,
    )
