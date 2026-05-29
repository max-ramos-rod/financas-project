from calendar import monthrange
from datetime import date
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.domain.cartao_fatura import valor_efetivo_transacao
from app.domain.transacao import normalizar_atraso
from app.models import Orcamento, StatusLiquidacao, TipoTransacao, Transacao


def get_transacoes(
    db: Session,
    user_id: int,
    tipo: Optional[TipoTransacao] = None,
    status_liquidacao: Optional[StatusLiquidacao] = None,
    fixa: Optional[bool] = None,
    conta_id: Optional[int] = None,
    categoria_id: Optional[int] = None,
    sem_categoria: bool = False,
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    busca: Optional[str] = None,
    valor_modo: Optional[str] = None,
    valor_ref: Optional[float] = None,
    orcamento: Optional[str] = None,
) -> tuple[List[Transacao], int]:
    query = db.query(Transacao).filter(Transacao.user_id == user_id)

    if tipo:
        query = query.filter(Transacao.tipo == tipo)

    if status_liquidacao:
        query = query.filter(Transacao.status_liquidacao == status_liquidacao)

    if fixa is not None:
        query = query.filter(Transacao.fixa == fixa)

    if conta_id is not None:
        query = query.filter(Transacao.conta_id == conta_id)

    if sem_categoria:
        query = query.filter(Transacao.categoria_id.is_(None))
    elif categoria_id is not None:
        query = query.filter(Transacao.categoria_id == categoria_id)

    if mes is not None and ano is not None:
        inicio = date(ano, mes, 1)
        fim = date(ano, mes, monthrange(ano, mes)[1])
        query = query.filter(Transacao.data >= inicio, Transacao.data <= fim)
    elif ano is not None:
        inicio = date(ano, 1, 1)
        fim = date(ano, 12, 31)
        query = query.filter(Transacao.data >= inicio, Transacao.data <= fim)

    if busca:
        query = query.filter(Transacao.descricao.ilike(f"%{busca}%"))

    transacoes = query.order_by(Transacao.data.desc(), Transacao.id.desc()).all()

    for transacao in transacoes:
        normalizar_atraso(transacao)

    if valor_modo and valor_ref is not None:
        if valor_modo == "igual":
            transacoes = [t for t in transacoes if abs(valor_efetivo_transacao(t) - valor_ref) < 0.005]
        elif valor_modo == "gte":
            transacoes = [t for t in transacoes if valor_efetivo_transacao(t) >= valor_ref]
        elif valor_modo == "lte":
            transacoes = [t for t in transacoes if valor_efetivo_transacao(t) <= valor_ref]

    if orcamento in {"fora", "dentro"}:
        hoje = date.today()
        mes_ref = mes or hoje.month
        ano_ref = ano or hoje.year

        inicio = date(ano_ref, mes_ref, 1)
        fim = date(ano_ref, mes_ref, monthrange(ano_ref, mes_ref)[1])

        transacoes_mes = db.query(Transacao).filter(
            Transacao.user_id == user_id,
            Transacao.tipo == TipoTransacao.SAIDA,
            Transacao.data >= inicio,
            Transacao.data <= fim,
            Transacao.status_liquidacao != StatusLiquidacao.CANCELADO,
        ).all()

        gastos_por_categoria: dict[int, float] = {}
        for t in transacoes_mes:
            if t.categoria_id is None:
                continue
            gastos_por_categoria[t.categoria_id] = gastos_por_categoria.get(t.categoria_id, 0.0) + valor_efetivo_transacao(t)

        orcamentos_mes = db.query(Orcamento).filter(
            Orcamento.user_id == user_id,
            Orcamento.mes == mes_ref,
            Orcamento.ano == ano_ref,
        ).all()
        orcado_por_categoria: dict[int, float] = {}
        for o in orcamentos_mes:
            orcado_por_categoria[o.categoria_id] = orcado_por_categoria.get(o.categoria_id, 0.0) + float(o.valor_planejado or 0.0)

        def _fora_orcamento(t: Transacao) -> bool:
            if t.tipo != TipoTransacao.SAIDA:
                return False
            if t.categoria_id is None:
                return True
            orcado = orcado_por_categoria.get(t.categoria_id)
            if orcado is None:
                return True
            gasto = gastos_por_categoria.get(t.categoria_id, 0.0)
            return gasto > orcado

        if orcamento == "fora":
            transacoes = [t for t in transacoes if _fora_orcamento(t)]
        else:
            transacoes = [t for t in transacoes if t.tipo == TipoTransacao.SAIDA and not _fora_orcamento(t)]

    return transacoes, len(transacoes)


def get_transacao(db: Session, transacao_id: int, user_id: int) -> Optional[Transacao]:
    transacao = db.query(Transacao).filter(
        and_(
            Transacao.id == transacao_id,
            Transacao.user_id == user_id,
        )
    ).first()

    if transacao:
        normalizar_atraso(transacao)

    return transacao
