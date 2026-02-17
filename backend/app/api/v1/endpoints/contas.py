from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date, timedelta
from calendar import monthrange
import uuid

from app.db.session import get_db
from app.api.deps import AccessContext, get_access_context
from app.schemas.conta import (
    ContaCreate,
    ContaUpdate,
    ContaResponse,
    FaturaResumoResponse,
    FaturaItemResponse,
    PagarFaturaRequest,
)
from app.models import Conta, TipoConta, Transacao, TipoTransacao, StatusLiquidacao

from app.crud import crud_conta as crud

router = APIRouter()


def _safe_date_with_day(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, monthrange(year, month)[1]))


def _shift_month(base: date, months: int) -> date:
    month_index = (base.month - 1) + months
    year = base.year + (month_index // 12)
    month = (month_index % 12) + 1
    return date(year, month, 1)


def _calcular_periodo_fatura(ref_date: date, dia_fechamento: int) -> tuple[date, date]:
    fechamento_mes_atual = _safe_date_with_day(ref_date.year, ref_date.month, dia_fechamento)
    if ref_date.day >= fechamento_mes_atual.day:
        periodo_fim = fechamento_mes_atual
    else:
        mes_anterior = _shift_month(ref_date, -1)
        periodo_fim = _safe_date_with_day(mes_anterior.year, mes_anterior.month, dia_fechamento)

    mes_antes = _shift_month(periodo_fim, -1)
    fechamento_anterior = _safe_date_with_day(mes_antes.year, mes_antes.month, dia_fechamento)
    periodo_inicio = fechamento_anterior + timedelta(days=1)
    return periodo_inicio, periodo_fim


def _calcular_vencimento_fatura(periodo_fim: date, dia_vencimento: int) -> date:
    if dia_vencimento > periodo_fim.day:
        return _safe_date_with_day(periodo_fim.year, periodo_fim.month, dia_vencimento)
    proximo_mes = _shift_month(periodo_fim, 1)
    return _safe_date_with_day(proximo_mes.year, proximo_mes.month, dia_vencimento)


def _valor_efetivo(transacao: Transacao) -> float:
    return max(
        0.0,
        (transacao.valor or 0)
        + (transacao.valor_multa or 0)
        + (transacao.valor_juros or 0)
        - (transacao.valor_desconto or 0),
    )

@router.get("", response_model=List[ContaResponse])
def listar_contas(
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Lista todas as contas do usuário"""
    contas = crud.get_contas(db, access_ctx.effective_user.id)
    return contas


@router.get("/{conta_id}", response_model=ContaResponse)
def buscar_conta(
    conta_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Busca uma conta específica"""
    conta = crud.get_conta(db, conta_id, access_ctx.effective_user.id)
    
    if not conta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta não encontrada"
        )
    
    return conta


@router.post("", response_model=ContaResponse, status_code=status.HTTP_201_CREATED)
def criar_conta(
    conta: ContaCreate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Cria uma nova conta"""
    try:
        nova_conta = crud.criar_conta(db, conta, access_ctx.effective_user.id)
        return nova_conta
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{conta_id}", response_model=ContaResponse)
def atualizar_conta(
    conta_id: int,
    conta: ContaUpdate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Atualiza uma conta existente"""
    try:
        conta_atualizada = crud.atualizar_conta(
            db, conta_id, access_ctx.effective_user.id, conta
        )
        
        if not conta_atualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conta não encontrada"
            )
        
        return conta_atualizada
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{conta_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_conta(
    conta_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Deleta uma conta"""
    try:
        sucesso = crud.deletar_conta(db, conta_id, access_ctx.effective_user.id)
        
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conta não encontrada"
            )
        
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{conta_id}/fatura-atual", response_model=FaturaResumoResponse)
def obter_fatura_atual(
    conta_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    conta = crud.get_conta(db, conta_id, access_ctx.effective_user.id)
    if not conta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    if conta.tipo != TipoConta.CARTAO_CREDITO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conta não é cartão de crédito")
    if conta.dia_fechamento is None or conta.dia_vencimento is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cartão sem fechamento/vencimento configurado")

    periodo_inicio, periodo_fim = _calcular_periodo_fatura(date.today(), conta.dia_fechamento)
    vencimento_fatura = _calcular_vencimento_fatura(periodo_fim, conta.dia_vencimento)

    transacoes = db.query(Transacao).filter(
        Transacao.user_id == access_ctx.effective_user.id,
        Transacao.conta_id == conta.id,
        Transacao.tipo == TipoTransacao.SAIDA,
        Transacao.data >= periodo_inicio,
        Transacao.data <= periodo_fim,
        Transacao.status_liquidacao.in_([StatusLiquidacao.PREVISTO, StatusLiquidacao.ATRASADO]),
    ).order_by(Transacao.data.asc(), Transacao.id.asc()).all()

    itens = [
        FaturaItemResponse(
            transacao_id=t.id,
            descricao=t.descricao,
            data=t.data,
            data_vencimento=t.data_vencimento,
            status_liquidacao=t.status_liquidacao.value,
            valor=t.valor,
            valor_multa=t.valor_multa or 0,
            valor_juros=t.valor_juros or 0,
            valor_desconto=t.valor_desconto or 0,
            valor_efetivo=_valor_efetivo(t),
        )
        for t in transacoes
    ]

    valor_total = sum(item.valor_efetivo for item in itens)
    return FaturaResumoResponse(
        conta_id=conta.id,
        conta_nome=conta.nome,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        dia_fechamento=conta.dia_fechamento,
        dia_vencimento=conta.dia_vencimento,
        data_vencimento_fatura=vencimento_fatura,
        total_itens=len(itens),
        valor_total=valor_total,
        itens=itens,
    )


@router.post("/{conta_id}/pagar-fatura", response_model=FaturaResumoResponse)
def pagar_fatura(
    conta_id: int,
    payload: PagarFaturaRequest,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    conta_cartao = crud.get_conta(db, conta_id, access_ctx.effective_user.id)
    if not conta_cartao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    if conta_cartao.tipo != TipoConta.CARTAO_CREDITO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conta não é cartão de crédito")
    if conta_cartao.dia_fechamento is None or conta_cartao.dia_vencimento is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cartão sem fechamento/vencimento configurado")

    conta_pagamento = crud.get_conta(db, payload.conta_pagamento_id, access_ctx.effective_user.id)
    if not conta_pagamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta de pagamento não encontrada")
    if conta_pagamento.id == conta_cartao.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conta de pagamento deve ser diferente do cartão")
    if conta_pagamento.tipo == TipoConta.CARTAO_CREDITO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pagamento deve sair de conta não cartão")

    periodo_inicio, periodo_fim = _calcular_periodo_fatura(date.today(), conta_cartao.dia_fechamento)
    transacoes = db.query(Transacao).filter(
        Transacao.user_id == access_ctx.effective_user.id,
        Transacao.conta_id == conta_cartao.id,
        Transacao.tipo == TipoTransacao.SAIDA,
        Transacao.data >= periodo_inicio,
        Transacao.data <= periodo_fim,
        Transacao.status_liquidacao.in_([StatusLiquidacao.PREVISTO, StatusLiquidacao.ATRASADO]),
    ).order_by(Transacao.data.asc(), Transacao.id.asc()).all()

    if not transacoes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não há itens em aberto na fatura atual")

    valor_total = sum(_valor_efetivo(t) for t in transacoes)
    data_pagamento = payload.data_pagamento or date.today()
    descricao_pagamento = payload.descricao or f"Pagamento fatura {conta_cartao.nome} ({periodo_inicio.strftime('%m/%Y')} - {periodo_fim.strftime('%m/%Y')})"

    # Debita a conta de pagamento e registra uma transferência de controle.
    conta_pagamento.saldo -= valor_total
    pagamento = Transacao(
        user_id=access_ctx.effective_user.id,
        conta_id=conta_pagamento.id,
        categoria_id=None,
        descricao=descricao_pagamento,
        valor=valor_total,
        tipo=TipoTransacao.TRANSFERENCIA,
        data=data_pagamento,
        data_vencimento=data_pagamento,
        data_liquidacao=data_pagamento,
        status_liquidacao=StatusLiquidacao.LIQUIDADO,
        fixa=False,
        recorrente=False,
        confirmada=True,
        transacao_uuid=str(uuid.uuid4()),
        tem_dizimo=False,
        percentual_dizimo=0,
        e_dizimo=False,
        parcelado=False,
        e_emprestimo=False,
        valor_multa=0,
        valor_juros=0,
        valor_desconto=0,
    )
    db.add(pagamento)

    for item in transacoes:
        item.status_liquidacao = StatusLiquidacao.LIQUIDADO
        item.data_liquidacao = data_pagamento
        db.add(item)

    db.add(conta_pagamento)
    db.commit()

    # Retorna resumo atualizado (tende a ficar vazio apos pagamento).
    return obter_fatura_atual(conta_id=conta_id, db=db, access_ctx=access_ctx)
