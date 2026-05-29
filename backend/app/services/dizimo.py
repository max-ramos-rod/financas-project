import uuid

from sqlalchemy.orm import Session

from app.domain.transacao import obter_categoria_dizimo
from app.models import StatusLiquidacao, TipoTransacao, Transacao


def criar_transacao_dizimo(
    db: Session,
    db_transacao: Transacao,
    percentual_dizimo: float,
    user_id: int,
) -> Transacao:
    """
    Cria a transação de dízimo automático vinculada a db_transacao.
    Requer que db_transacao já tenha ID (flush prévio necessário).
    Muta db_transacao: seta tem_dizimo, percentual_dizimo, transacao_dizimo_uuid.
    """
    dizimo_uuid = str(uuid.uuid4())
    db_transacao.tem_dizimo = True
    db_transacao.percentual_dizimo = percentual_dizimo
    db_transacao.transacao_dizimo_uuid = dizimo_uuid

    valor_dizimo = db_transacao.valor * (percentual_dizimo / 100)
    categoria_dizimo = obter_categoria_dizimo(db, user_id)

    dizimo = Transacao(
        user_id=user_id,
        transacao_uuid=str(uuid.uuid4()),
        conta_id=db_transacao.conta_id,
        categoria_id=categoria_dizimo.id,
        descricao=f"Dizimo de {db_transacao.descricao}",
        valor=valor_dizimo,
        tipo=TipoTransacao.SAIDA,
        data=db_transacao.data,
        data_vencimento=db_transacao.data_vencimento or db_transacao.data,
        status_liquidacao=StatusLiquidacao.PREVISTO,
        fixa=True,
        recorrente=False,
        confirmada=False,
        tem_dizimo=False,
        e_dizimo=True,
        entrada_origem_id=db_transacao.id,
        transacao_dizimo_uuid=dizimo_uuid,
    )
    db.add(dizimo)
    return dizimo
