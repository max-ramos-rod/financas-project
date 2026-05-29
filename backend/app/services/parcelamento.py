import uuid
from calendar import monthrange
from datetime import date

from sqlalchemy.orm import Session

from app.contracts import TransacaoRepositoryProtocol
from app.domain.transacao import impacto_no_saldo, recalcular_meta, recalcular_orcamento_mes
from app.models import Conta, StatusLiquidacao, TipoTransacao, Transacao
from app.schemas.transacao import TransacaoCreate


def _add_months(base_date: date, months: int) -> date:
    month_index = (base_date.month - 1) + months
    year = base_date.year + (month_index // 12)
    month = (month_index % 12) + 1
    day = min(base_date.day, monthrange(year, month)[1])
    return date(year, month, day)


def criar_parcelamento(
    db: Session,
    transacao: TransacaoCreate,
    conta: Conta,
    user_id: int,
    repo: TransacaoRepositoryProtocol,
) -> Transacao:
    grupo_uuid = str(uuid.uuid4())
    data_vencimento_base = transacao.data_vencimento or transacao.data
    transacoes_criadas: list[Transacao] = []
    metas_afetadas: set[int] = set()
    orcamentos_afetados: set[tuple[int, int, int]] = set()

    for index in range(1, transacao.total_parcelas + 1):
        parcela_data = _add_months(transacao.data, index - 1)
        parcela_vencimento = _add_months(data_vencimento_base, index - 1)
        is_primeira = index == 1
        status_parcela = transacao.status_liquidacao if is_primeira else StatusLiquidacao.PREVISTO

        parcela = Transacao(
            user_id=user_id,
            transacao_uuid=str(uuid.uuid4()),
            conta_id=transacao.conta_id,
            categoria_id=transacao.categoria_id,
            descricao=transacao.descricao,
            valor=transacao.valor,
            tipo=transacao.tipo,
            data=parcela_data,
            data_vencimento=parcela_vencimento,
            data_liquidacao=transacao.data_liquidacao if (is_primeira and status_parcela == StatusLiquidacao.LIQUIDADO) else None,
            status_liquidacao=status_parcela,
            fixa=transacao.fixa,
            recorrente=transacao.recorrente,
            confirmada=transacao.confirmada,
            tem_dizimo=False,
            percentual_dizimo=transacao.percentual_dizimo,
            parcelado=True,
            parcela_atual=index,
            total_parcelas=transacao.total_parcelas,
            grupo_parcelamento_uuid=grupo_uuid,
            e_emprestimo=transacao.e_emprestimo,
            pessoa_emprestimo=transacao.pessoa_emprestimo,
            observacoes=transacao.observacoes,
            tags=transacao.tags,
            valor_multa=transacao.valor_multa if is_primeira else 0.0,
            valor_juros=transacao.valor_juros if is_primeira else 0.0,
            valor_desconto=transacao.valor_desconto if is_primeira else 0.0,
            meta_id=transacao.meta_id,
        )
        conta.saldo += impacto_no_saldo(parcela)
        transacoes_criadas.append(parcela)
        if parcela.meta_id:
            metas_afetadas.add(parcela.meta_id)
        if parcela.categoria_id and parcela.tipo == TipoTransacao.SAIDA:
            orcamentos_afetados.add((parcela.categoria_id, parcela.data.month, parcela.data.year))

    db.add(conta)
    repo._save_many(db, transacoes_criadas)
    for meta_id in metas_afetadas:
        recalcular_meta(db, user_id, meta_id)
    for categoria_id, mes, ano in orcamentos_afetados:
        recalcular_orcamento_mes(db, user_id, categoria_id, mes, ano)
    db.commit()
    db.refresh(transacoes_criadas[0])
    return transacoes_criadas[0]
