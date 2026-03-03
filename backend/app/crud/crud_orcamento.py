from calendar import monthrange
from datetime import date
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models import Orcamento, StatusLiquidacao, TipoTransacao, Transacao
from app.schemas.orcamento import OrcamentoCreate, OrcamentoUpdate


def _valor_efetivo_transacao(transacao: Transacao) -> float:
    return max(
        0.0,
        (transacao.valor or 0)
        + (transacao.valor_multa or 0)
        + (transacao.valor_juros or 0)
        - (transacao.valor_desconto or 0),
    )


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

    return sum(_valor_efetivo_transacao(t) for t in transacoes)


def get_orcamentos(db: Session, user_id: int, mes: Optional[int] = None, ano: Optional[int] = None) -> List[Orcamento]:
    """Lista todos os orcamentos do usuario"""
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
    """Busca um orcamento especifico"""
    orcamento = db.query(Orcamento).filter(
        and_(
            Orcamento.id == orcamento_id,
            Orcamento.user_id == user_id,
        )
    ).first()

    if orcamento:
        orcamento.valor_gasto = _calcular_valor_gasto_orcamento(db, orcamento)
    return orcamento


def get_orcamento_categoria_mes(db: Session, categoria_id: int, mes: int, ano: int, user_id: int) -> Optional[Orcamento]:
    """Busca orcamento por categoria, mes e ano"""
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


def criar_orcamento(db: Session, orcamento: OrcamentoCreate, user_id: int) -> Orcamento:
    """Cria um novo orcamento"""
    db_orcamento = Orcamento(
        user_id=user_id,
        **orcamento.model_dump(),
    )
    db.add(db_orcamento)
    db.commit()
    db.refresh(db_orcamento)
    db_orcamento.valor_gasto = _calcular_valor_gasto_orcamento(db, db_orcamento)
    return db_orcamento


def atualizar_orcamento(db: Session, orcamento_id: int, user_id: int, orcamento_update: OrcamentoUpdate) -> Optional[Orcamento]:
    """Atualiza um orcamento existente"""
    db_orcamento = get_orcamento(db, orcamento_id, user_id)
    if not db_orcamento:
        return None

    update_data = orcamento_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_orcamento, key, value)

    db_orcamento.valor_gasto = _calcular_valor_gasto_orcamento(db, db_orcamento)

    db.add(db_orcamento)
    db.commit()
    db.refresh(db_orcamento)
    db_orcamento.valor_gasto = _calcular_valor_gasto_orcamento(db, db_orcamento)
    return db_orcamento


def deletar_orcamento(db: Session, orcamento_id: int, user_id: int) -> bool:
    """Deleta um orcamento"""
    db_orcamento = db.query(Orcamento).filter(
        and_(
            Orcamento.id == orcamento_id,
            Orcamento.user_id == user_id,
        )
    ).first()
    if not db_orcamento:
        return False

    db.delete(db_orcamento)
    db.commit()
    return True
