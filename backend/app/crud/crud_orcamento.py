from calendar import monthrange
from datetime import date
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.domain.cartao_fatura import valor_efetivo_transacao
from app.models import Orcamento, StatusLiquidacao, TipoTransacao, Transacao


def _calcular_valor_gasto_orcamento(db: Session, orcamento: Orcamento) -> float:
    inicio = date(orcamento.ano, orcamento.mes, 1)
    fim = date(orcamento.ano, orcamento.mes, monthrange(orcamento.ano, orcamento.mes)[1])

    transacoes = db.query(Transacao).filter(
        Transacao.user_id == orcamento.user_id,
        Transacao.categoria_id == orcamento.categoria_id,
        Transacao.tipo == TipoTransacao.SAIDA,
        Transacao.data >= inicio,
        Transacao.data <= fim,
        Transacao.status_liquidacao != StatusLiquidacao.CANCELADO,
    ).all()

    return sum(valor_efetivo_transacao(t) for t in transacoes)


def get_orcamentos(db: Session, user_id: int, mes: Optional[int] = None, ano: Optional[int] = None) -> List[Orcamento]:
    query = db.query(Orcamento).filter(Orcamento.user_id == user_id)
    if mes:
        query = query.filter(Orcamento.mes == mes)
    if ano:
        query = query.filter(Orcamento.ano == ano)
    orcamentos = query.all()
    for orcamento in orcamentos:
        orcamento.valor_gasto = _calcular_valor_gasto_orcamento(db, orcamento)
    return orcamentos


def get_orcamento(db: Session, orcamento_id: int, user_id: int) -> Optional[Orcamento]:
    orcamento = db.query(Orcamento).filter(
        and_(
            Orcamento.id == orcamento_id,
            Orcamento.user_id == user_id,
        )
    ).first()
    if orcamento:
        orcamento.valor_gasto = _calcular_valor_gasto_orcamento(db, orcamento)
    return orcamento


def get_orcamento_categoria_mes(
    db: Session, categoria_id: int, mes: int, ano: int, user_id: int
) -> Optional[Orcamento]:
    orcamento = db.query(Orcamento).filter(
        and_(
            Orcamento.categoria_id == categoria_id,
            Orcamento.mes == mes,
            Orcamento.ano == ano,
            Orcamento.user_id == user_id,
        )
    ).first()
    if orcamento:
        orcamento.valor_gasto = _calcular_valor_gasto_orcamento(db, orcamento)
    return orcamento
