from __future__ import annotations

import unicodedata
from calendar import monthrange
from datetime import date

from sqlalchemy.orm import Session

from app.domain.cartao_fatura import valor_efetivo_transacao
from app.models import Categoria, Meta, Orcamento, StatusLiquidacao, TipoTransacao, Transacao


def impacto_no_saldo(transacao: Transacao) -> float:
    if transacao.status_liquidacao != StatusLiquidacao.LIQUIDADO:
        return 0.0
    efetivo = valor_efetivo_transacao(transacao)
    return efetivo if transacao.tipo == TipoTransacao.ENTRADA else -efetivo


def normalizar_atraso(transacao: Transacao) -> None:
    if (
        transacao.status_liquidacao == StatusLiquidacao.PREVISTO
        and transacao.data_vencimento
        and transacao.data_vencimento < date.today()
    ):
        transacao.status_liquidacao = StatusLiquidacao.ATRASADO


def valor_meta(transacao: Transacao) -> float:
    if transacao.status_liquidacao == StatusLiquidacao.CANCELADO:
        return 0.0
    efetivo = valor_efetivo_transacao(transacao)
    if transacao.tipo == TipoTransacao.ENTRADA:
        return efetivo
    if transacao.tipo == TipoTransacao.SAIDA:
        return -efetivo
    return 0.0


def recalcular_meta(db: Session, user_id: int, meta_id: int) -> None:
    meta = db.query(Meta).filter(Meta.id == meta_id, Meta.user_id == user_id).first()
    if not meta:
        return
    transacoes_meta = db.query(Transacao).filter(
        Transacao.user_id == user_id,
        Transacao.meta_id == meta_id,
    ).all()
    meta.valor_atual = sum(valor_meta(t) for t in transacoes_meta)
    meta.concluida = meta.valor_atual >= meta.valor_alvo
    db.add(meta)


def recalcular_orcamento_mes(db: Session, user_id: int, categoria_id: int, mes: int, ano: int) -> None:
    orcamento = db.query(Orcamento).filter(
        Orcamento.user_id == user_id,
        Orcamento.categoria_id == categoria_id,
        Orcamento.mes == mes,
        Orcamento.ano == ano,
    ).first()
    if not orcamento:
        return
    inicio = date(ano, mes, 1)
    fim = date(ano, mes, monthrange(ano, mes)[1])
    transacoes = db.query(Transacao).filter(
        Transacao.user_id == user_id,
        Transacao.categoria_id == categoria_id,
        Transacao.tipo == TipoTransacao.SAIDA,
        Transacao.data >= inicio,
        Transacao.data <= fim,
        Transacao.status_liquidacao != StatusLiquidacao.CANCELADO,
    ).all()
    orcamento.valor_gasto = sum(valor_efetivo_transacao(t) for t in transacoes)
    db.add(orcamento)


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return ascii_only.strip().lower()


def obter_categoria_dizimo(db: Session, user_id: int) -> Categoria:
    candidatas = db.query(Categoria).filter(
        Categoria.tipo == TipoTransacao.SAIDA
    ).all()

    categoria_usuario = next(
        (c for c in candidatas if c.user_id == user_id and _normalize_text(c.nome) == "dizimo"),
        None,
    )
    if categoria_usuario:
        return categoria_usuario

    categoria_padrao = next(
        (c for c in candidatas if c.user_id is None and c.padrao and _normalize_text(c.nome) == "dizimo"),
        None,
    )
    if categoria_padrao:
        return categoria_padrao

    nova_categoria = Categoria(
        user_id=user_id,
        nome="Dizimo",
        icone="",
        cor="#10B981",
        tipo=TipoTransacao.SAIDA,
        padrao=False,
    )
    db.add(nova_categoria)
    db.flush()
    return nova_categoria
