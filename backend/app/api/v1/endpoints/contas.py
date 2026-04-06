from datetime import date
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import AccessContext, get_access_context
from app.crud import crud_conta as crud
from app.db.session import get_db
from app.domain.cartao_fatura import (
    determinar_competencia_fatura_atual,
    obter_resumo_fatura_atual,
    obter_resumo_fatura_fechada_atual,
    valor_efetivo_transacao,
)
from app.models import ContaCartaoCiclo, StatusLiquidacao, TipoConta, TipoTransacao, Transacao
from app.schemas.conta import (
    ContaCreate,
    ContaResponse,
    ContaUpdate,
    FaturaCicloAjusteRequest,
    FaturaItemResponse,
    FaturaResumoResponse,
    PagarFaturaRequest,
)

router = APIRouter()


@router.get("", response_model=List[ContaResponse])
def listar_contas(
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    contas = crud.get_contas(db, access_ctx.effective_user.id)

    for conta in contas:
        if conta.tipo != TipoConta.CARTAO_CREDITO:
            continue
        try:
            resumo = obter_resumo_fatura_atual(
                db,
                user_id=access_ctx.effective_user.id,
                conta=conta,
            )
        except ValueError:
            continue

        conta.valor_fatura_aberta = resumo.valor_total
        conta.total_itens_fatura_aberta = resumo.total_itens
        conta.periodo_fatura_inicio = resumo.periodo_inicio
        conta.periodo_fatura_fim = resumo.periodo_fim
        conta.data_fechamento_fatura = resumo.data_fechamento_fatura
        conta.data_vencimento_fatura = resumo.data_vencimento_fatura
        resumo_fechado = obter_resumo_fatura_fechada_atual(
            db,
            user_id=access_ctx.effective_user.id,
            conta=conta,
        )
        conta.valor_fatura_fechada = resumo_fechado.valor_a_pagar
        conta.valor_fatura_fechada_pago = resumo_fechado.valor_pago
        conta.valor_fatura_fechada_total = resumo_fechado.valor_total
        conta.total_itens_fatura_fechada = resumo_fechado.total_itens
        conta.periodo_fatura_fechada_inicio = resumo_fechado.periodo_inicio
        conta.periodo_fatura_fechada_fim = resumo_fechado.periodo_fim
        conta.data_vencimento_fatura_fechada = resumo_fechado.data_vencimento_fatura

    return contas


@router.get("/{conta_id}", response_model=ContaResponse)
def buscar_conta(
    conta_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    conta = crud.get_conta(db, conta_id, access_ctx.effective_user.id)

    if not conta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta nao encontrada",
        )

    if conta.tipo == TipoConta.CARTAO_CREDITO:
        try:
            resumo = obter_resumo_fatura_atual(
                db,
                user_id=access_ctx.effective_user.id,
                conta=conta,
            )
            conta.valor_fatura_aberta = resumo.valor_total
            conta.total_itens_fatura_aberta = resumo.total_itens
            conta.periodo_fatura_inicio = resumo.periodo_inicio
            conta.periodo_fatura_fim = resumo.periodo_fim
            conta.data_fechamento_fatura = resumo.data_fechamento_fatura
            conta.data_vencimento_fatura = resumo.data_vencimento_fatura
            resumo_fechado = obter_resumo_fatura_fechada_atual(
                db,
                user_id=access_ctx.effective_user.id,
                conta=conta,
            )
            conta.valor_fatura_fechada = resumo_fechado.valor_a_pagar
            conta.valor_fatura_fechada_pago = resumo_fechado.valor_pago
            conta.valor_fatura_fechada_total = resumo_fechado.valor_total
            conta.total_itens_fatura_fechada = resumo_fechado.total_itens
            conta.periodo_fatura_fechada_inicio = resumo_fechado.periodo_inicio
            conta.periodo_fatura_fechada_fim = resumo_fechado.periodo_fim
            conta.data_vencimento_fatura_fechada = resumo_fechado.data_vencimento_fatura
        except ValueError:
            pass

    return conta


@router.post("", response_model=ContaResponse, status_code=status.HTTP_201_CREATED)
def criar_conta(
    conta: ContaCreate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    try:
        nova_conta = crud.criar_conta(db, conta, access_ctx.effective_user.id)
        return nova_conta
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.put("/{conta_id}", response_model=ContaResponse)
def atualizar_conta(
    conta_id: int,
    conta: ContaUpdate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    try:
        conta_atualizada = crud.atualizar_conta(db, conta_id, access_ctx.effective_user.id, conta)

        if not conta_atualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conta nao encontrada",
            )

        return conta_atualizada
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete("/{conta_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_conta(
    conta_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    try:
        sucesso = crud.deletar_conta(db, conta_id, access_ctx.effective_user.id)

        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conta nao encontrada",
            )

        return None
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{conta_id}/fatura-atual", response_model=FaturaResumoResponse)
def obter_fatura_atual(
    conta_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    conta = crud.get_conta(db, conta_id, access_ctx.effective_user.id)
    if not conta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta nao encontrada")

    try:
        resumo = obter_resumo_fatura_atual(
            db,
            user_id=access_ctx.effective_user.id,
            conta=conta,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

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
            valor_efetivo=valor_efetivo_transacao(t),
        )
        for t in resumo.itens
    ]

    return FaturaResumoResponse(
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
        observacao_ciclo=resumo.observacao_ciclo,
        total_itens=resumo.total_itens,
        valor_total=resumo.valor_total,
        valor_pago=resumo.valor_pago,
        valor_a_pagar=resumo.valor_a_pagar,
        itens=itens,
    )


@router.get("/{conta_id}/fatura-fechada", response_model=FaturaResumoResponse)
def obter_fatura_fechada(
    conta_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    conta = crud.get_conta(db, conta_id, access_ctx.effective_user.id)
    if not conta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta nao encontrada")

    try:
        resumo = obter_resumo_fatura_fechada_atual(
            db,
            user_id=access_ctx.effective_user.id,
            conta=conta,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

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
            valor_efetivo=valor_efetivo_transacao(t),
        )
        for t in resumo.itens
    ]

    return FaturaResumoResponse(
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
        observacao_ciclo=resumo.observacao_ciclo,
        total_itens=resumo.total_itens,
        valor_total=resumo.valor_total,
        valor_pago=resumo.valor_pago,
        valor_a_pagar=resumo.valor_a_pagar,
        itens=itens,
    )


@router.put("/{conta_id}/fatura-atual/ajuste-ciclo", response_model=FaturaResumoResponse)
def ajustar_ciclo_fatura_atual(
    conta_id: int,
    payload: FaturaCicloAjusteRequest,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    conta = crud.get_conta(db, conta_id, access_ctx.effective_user.id)
    if not conta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta nao encontrada")
    if conta.tipo != TipoConta.CARTAO_CREDITO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conta nao e cartao de credito")
    if conta.dia_fechamento is None or conta.dia_vencimento is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cartao sem fechamento/vencimento configurado")

    referencia = date.today()
    competencia_ano, competencia_mes = determinar_competencia_fatura_atual(
        db,
        conta=conta,
        ref_date=referencia,
    )
    resumo_atual = obter_fatura_atual(conta_id=conta_id, db=db, access_ctx=access_ctx)

    ciclo = (
        db.query(ContaCartaoCiclo)
        .filter(
            ContaCartaoCiclo.conta_id == conta.id,
            ContaCartaoCiclo.competencia_ano == competencia_ano,
            ContaCartaoCiclo.competencia_mes == competencia_mes,
        )
        .first()
    )

    if ciclo is None:
        ciclo = ContaCartaoCiclo(
            conta_id=conta.id,
            competencia_ano=competencia_ano,
            competencia_mes=competencia_mes,
            data_fechamento_prevista=resumo_atual.data_fechamento_prevista,
            data_vencimento_prevista=resumo_atual.data_vencimento_prevista,
        )

    ciclo.data_fechamento_prevista = resumo_atual.data_fechamento_prevista
    ciclo.data_vencimento_prevista = resumo_atual.data_vencimento_prevista
    ciclo.data_fechamento_real = payload.data_fechamento_real
    ciclo.data_vencimento_real = payload.data_vencimento_real
    ciclo.observacao = payload.observacao
    db.add(ciclo)
    db.commit()

    return obter_fatura_atual(conta_id=conta_id, db=db, access_ctx=access_ctx)


@router.delete("/{conta_id}/fatura-atual/ajuste-ciclo", response_model=FaturaResumoResponse)
def limpar_ajuste_ciclo_fatura_atual(
    conta_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    conta = crud.get_conta(db, conta_id, access_ctx.effective_user.id)
    if not conta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta nao encontrada")
    if conta.tipo != TipoConta.CARTAO_CREDITO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conta nao e cartao de credito")

    competencia_ano, competencia_mes = determinar_competencia_fatura_atual(
        db,
        conta=conta,
        ref_date=date.today(),
    )
    ciclo = (
        db.query(ContaCartaoCiclo)
        .filter(
            ContaCartaoCiclo.conta_id == conta.id,
            ContaCartaoCiclo.competencia_ano == competencia_ano,
            ContaCartaoCiclo.competencia_mes == competencia_mes,
        )
        .first()
    )
    if ciclo:
        db.delete(ciclo)
        db.commit()

    return obter_fatura_atual(conta_id=conta_id, db=db, access_ctx=access_ctx)


@router.post("/{conta_id}/pagar-fatura", response_model=FaturaResumoResponse)
def pagar_fatura(
    conta_id: int,
    payload: PagarFaturaRequest,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    conta_cartao = crud.get_conta(db, conta_id, access_ctx.effective_user.id)
    if not conta_cartao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta nao encontrada")
    if conta_cartao.tipo != TipoConta.CARTAO_CREDITO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conta nao e cartao de credito")
    if conta_cartao.dia_fechamento is None or conta_cartao.dia_vencimento is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cartao sem fechamento/vencimento configurado")

    conta_pagamento = crud.get_conta(db, payload.conta_pagamento_id, access_ctx.effective_user.id)
    if not conta_pagamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta de pagamento nao encontrada")
    if conta_pagamento.id == conta_cartao.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conta de pagamento deve ser diferente do cartao")
    if conta_pagamento.tipo == TipoConta.CARTAO_CREDITO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pagamento deve sair de conta nao cartao")

    resumo_fatura = obter_resumo_fatura_fechada_atual(
        db,
        user_id=access_ctx.effective_user.id,
        conta=conta_cartao,
        ref_date=date.today(),
    )
    periodo_inicio = resumo_fatura.periodo_inicio
    periodo_fim = resumo_fatura.periodo_fim
    transacoes = (
        db.query(Transacao)
        .filter(
            Transacao.user_id == access_ctx.effective_user.id,
            Transacao.conta_id == conta_cartao.id,
            Transacao.tipo == TipoTransacao.SAIDA,
            Transacao.data >= periodo_inicio,
            Transacao.data <= periodo_fim,
            Transacao.status_liquidacao.in_([StatusLiquidacao.PREVISTO, StatusLiquidacao.ATRASADO]),
        )
        .order_by(Transacao.data.asc(), Transacao.id.asc())
        .all()
    )

    if not transacoes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nao ha itens em aberto na fatura fechada")

    valor_total = sum(valor_efetivo_transacao(t) for t in transacoes)
    data_pagamento = payload.data_pagamento or date.today()
    descricao_pagamento = payload.descricao or (
        f"FTPG {conta_cartao.nome} ({periodo_inicio.strftime('%d/%m')} a {periodo_fim.strftime('%d/%m')})"
    )

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
        tags="pagamento_fatura",
    )
    db.add(pagamento)

    for item in transacoes:
        item.status_liquidacao = StatusLiquidacao.LIQUIDADO
        item.data_liquidacao = data_pagamento
        db.add(item)

    db.add(conta_pagamento)
    db.commit()

    return obter_fatura_fechada(conta_id=conta_id, db=db, access_ctx=access_ctx)
