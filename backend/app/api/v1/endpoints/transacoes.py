import csv
import io
from datetime import date
from calendar import monthrange

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.api.deps import AccessContext, get_access_context
from app.domain.cartao_fatura import obter_resumo_fatura_por_competencia, valor_efetivo_transacao
from app.models import Conta, StatusLiquidacao, TipoConta, TipoTransacao
from app.core.pagination import PaginationMetaBuilder, PaginationParams
from app.core.responses import PagedResponse
from app.schemas.transacao import (
    TransacaoCreate,
    TransacaoUpdate,
    TransacaoResponse,
    TransacaoFinanceiraResponse,
)

from app.crud import crud_transacao as crud

router = APIRouter()


def _parse_valor_ref(valor_ref: str | None) -> float | None:
    if valor_ref is None or not valor_ref.strip():
        return None
    try:
        return float(valor_ref.replace(".", "").replace(",", ".")) if ("," in valor_ref and "." in valor_ref) else float(valor_ref.replace(",", "."))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="valor_ref invalido")



def _status_fatura(valor_a_pagar: float) -> StatusLiquidacao:
    return StatusLiquidacao.PREVISTO if valor_a_pagar > 0 else StatusLiquidacao.LIQUIDADO


def _competencias_para_periodo(ano: int, mes: int) -> list[tuple[int, int]]:
    base = date(ano, mes, 1)
    competencias: list[tuple[int, int]] = []
    for deslocamento in range(-2, 2):
        month_index = base.month - 1 + deslocamento
        year = base.year + month_index // 12
        month = month_index % 12 + 1
        competencia = (year, month)
        if competencia not in competencias:
            competencias.append(competencia)
    return competencias


def _montar_fatura_financeira(resumo) -> TransacaoFinanceiraResponse:
    status_fatura = _status_fatura(resumo.valor_a_pagar)
    valor_total = resumo.valor_a_pagar if resumo.valor_a_pagar > 0 else resumo.valor_total
    return TransacaoFinanceiraResponse(
        id=-(resumo.conta_id * 1000000 + resumo.competencia_ano * 100 + resumo.competencia_mes),
        user_id=0,
        transacao_uuid=f"fatura-cartao-{resumo.conta_id}-{resumo.competencia_ano}-{resumo.competencia_mes}",
        conta_id=resumo.conta_id,
        categoria_id=None,
        descricao=f"Fatura {resumo.conta_nome}",
        valor=valor_total,
        tipo=TipoTransacao.SAIDA,
        data=resumo.data_fechamento_fatura,
        data_vencimento=resumo.data_vencimento_fatura,
        data_liquidacao=resumo.data_vencimento_fatura if status_fatura == StatusLiquidacao.LIQUIDADO else None,
        status_liquidacao=status_fatura,
        fixa=False,
        recorrente=False,
        confirmada=True,
        tem_dizimo=False,
        percentual_dizimo=0,
        parcelado=False,
        total_parcelas=None,
        e_emprestimo=False,
        pessoa_emprestimo=None,
        observacoes=f"Periodo: {resumo.periodo_inicio.isoformat()} a {resumo.periodo_fim.isoformat()}",
        tags="fatura_cartao",
        valor_multa=0,
        valor_juros=0,
        valor_desconto=0,
        meta_id=None,
        transacao_dizimo_uuid=None,
        e_dizimo=False,
        entrada_origem_id=None,
        parcela_atual=None,
        grupo_parcelamento_uuid=None,
        item_tipo="fatura_cartao",
        fatura_conta_id=resumo.conta_id,
        fatura_competencia_ano=resumo.competencia_ano,
        fatura_competencia_mes=resumo.competencia_mes,
        fatura_periodo_inicio=resumo.periodo_inicio,
        fatura_periodo_fim=resumo.periodo_fim,
        fatura_total_itens=resumo.total_itens,
    )


def _aplicar_filtros_financeiros(
    itens: list[TransacaoFinanceiraResponse],
    *,
    status_liquidacao: StatusLiquidacao | None,
    conta_id: int | None,
    busca: str | None,
    valor_modo: str | None,
    valor_ref: float | None,
) -> list[TransacaoFinanceiraResponse]:
    filtrados = itens
    if status_liquidacao:
        filtrados = [item for item in filtrados if item.status_liquidacao == status_liquidacao]
    if conta_id is not None:
        filtrados = [item for item in filtrados if item.conta_id == conta_id]
    if busca:
        busca_lower = busca.lower()
        filtrados = [item for item in filtrados if busca_lower in item.descricao.lower()]
    if valor_modo and valor_ref is not None:
        if valor_modo == "igual":
            filtrados = [item for item in filtrados if abs(valor_efetivo_transacao(item) - valor_ref) < 0.005]
        elif valor_modo == "gte":
            filtrados = [item for item in filtrados if valor_efetivo_transacao(item) >= valor_ref]
        elif valor_modo == "lte":
            filtrados = [item for item in filtrados if valor_efetivo_transacao(item) <= valor_ref]
    return filtrados

@router.get("", response_model=PagedResponse[TransacaoResponse])
def listar_transacoes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    tipo: TipoTransacao | None = Query(default=None),
    status_liquidacao: StatusLiquidacao | None = Query(default=None),
    fixa: str | None = Query(default=None, pattern="^(fixas|nao_fixas)$"),
    conta_id: int | None = None,
    categoria_id: int | None = None,
    mes: int | None = Query(default=None, ge=1, le=12),
    ano: int | None = Query(default=None, ge=2000, le=2100),
    busca: str | None = None,
    valor_modo: str | None = Query(default=None, pattern="^(igual|gte|lte)$"),
    valor_ref: str | None = None,
    orcamento: str | None = Query(default=None, pattern="^(fora|dentro)$"),
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    fixa_bool = None
    if fixa == "fixas":
        fixa_bool = True
    elif fixa == "nao_fixas":
        fixa_bool = False

    sem_categoria = categoria_id == -1
    categoria_normalizada = None if sem_categoria else categoria_id

    valor_ref_num = None
    if valor_ref is not None and valor_ref.strip():
        try:
            valor_ref_num = float(valor_ref.replace(".", "").replace(",", ".")) if ("," in valor_ref and "." in valor_ref) else float(valor_ref.replace(",", "."))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="valor_ref invalido")

    all_items, total = crud.get_transacoes(
        db=db,
        user_id=access_ctx.effective_user.id,
        tipo=tipo,
        status_liquidacao=status_liquidacao,
        fixa=fixa_bool,
        conta_id=conta_id,
        categoria_id=categoria_normalizada,
        sem_categoria=sem_categoria,
        mes=mes,
        ano=ano,
        busca=busca,
        valor_modo=valor_modo,
        valor_ref=valor_ref_num,
        orcamento=orcamento,
    )
    params = PaginationParams(page=page, page_size=page_size)
    skip = (page - 1) * page_size
    return PagedResponse(
        data=all_items[skip: skip + page_size],
        meta=PaginationMetaBuilder.build(total, params),
    )


@router.get("/visao-financeira", response_model=PagedResponse[TransacaoFinanceiraResponse])
def listar_transacoes_visao_financeira(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    tipo: TipoTransacao | None = Query(default=None),
    status_liquidacao: StatusLiquidacao | None = Query(default=None),
    fixa: str | None = Query(default=None, pattern="^(fixas|nao_fixas)$"),
    conta_id: int | None = None,
    categoria_id: int | None = None,
    mes: int | None = Query(default=None, ge=1, le=12),
    ano: int | None = Query(default=None, ge=2000, le=2100),
    busca: str | None = None,
    valor_modo: str | None = Query(default=None, pattern="^(igual|gte|lte)$"),
    valor_ref: str | None = None,
    orcamento: str | None = Query(default=None, pattern="^(fora|dentro)$"),
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    """
    Lista a visao financeira das transacoes.

    Compras individuais em cartao de credito sao substituidas por uma linha
    consolidada da fatura do cartao no mes de vencimento.
    """
    fixa_bool = None
    if fixa == "fixas":
        fixa_bool = True
    elif fixa == "nao_fixas":
        fixa_bool = False

    sem_categoria = categoria_id == -1
    categoria_normalizada = None if sem_categoria else categoria_id
    valor_ref_num = _parse_valor_ref(valor_ref)

    transacoes, _ = crud.get_transacoes(
        db=db,
        user_id=access_ctx.effective_user.id,
        tipo=tipo,
        status_liquidacao=status_liquidacao,
        fixa=fixa_bool,
        conta_id=conta_id,
        categoria_id=categoria_normalizada,
        sem_categoria=sem_categoria,
        mes=mes,
        ano=ano,
        busca=busca,
        valor_modo=valor_modo,
        valor_ref=valor_ref_num,
        orcamento=orcamento,
    )

    contas_cartao_ids = {
        conta.id
        for conta in db.query(Conta).filter(
            Conta.user_id == access_ctx.effective_user.id,
            Conta.tipo == TipoConta.CARTAO_CREDITO,
        ).all()
    }

    itens: list[TransacaoFinanceiraResponse] = [
        TransacaoFinanceiraResponse.model_validate(transacao, from_attributes=True)
        for transacao in transacoes
        if transacao.conta_id not in contas_cartao_ids
    ]

    inclui_faturas = tipo in (None, TipoTransacao.SAIDA)
    filtros_incompativeis_com_fatura = categoria_id is not None or fixa_bool is not None or orcamento is not None

    if inclui_faturas and not filtros_incompativeis_com_fatura:
        hoje = date.today()
        ano_ref = ano or hoje.year
        meses_ref = [mes] if mes is not None else list(range(1, 13))
        contas_cartao = db.query(Conta).filter(
            Conta.user_id == access_ctx.effective_user.id,
            Conta.tipo == TipoConta.CARTAO_CREDITO,
        ).all()

        faturas: list[TransacaoFinanceiraResponse] = []
        chaves_faturas: set[tuple[int, int, int]] = set()
        for mes_ref in meses_ref:
            inicio_mes = date(ano_ref, mes_ref, 1)
            fim_mes = date(ano_ref, mes_ref, monthrange(ano_ref, mes_ref)[1])
            for conta in contas_cartao:
                if conta_id is not None and conta.id != conta_id:
                    continue
                if conta.dia_fechamento is None or conta.dia_vencimento is None:
                    continue
                for competencia_ano, competencia_mes in _competencias_para_periodo(ano_ref, mes_ref):
                    chave = (conta.id, competencia_ano, competencia_mes)
                    if chave in chaves_faturas:
                        continue
                    try:
                        resumo = obter_resumo_fatura_por_competencia(
                            db,
                            user_id=access_ctx.effective_user.id,
                            conta=conta,
                            competencia_ano=competencia_ano,
                            competencia_mes=competencia_mes,
                        )
                    except ValueError:
                        continue
                    if resumo.total_itens == 0:
                        continue
                    if not (inicio_mes <= resumo.data_vencimento_fatura <= fim_mes):
                        continue
                    chaves_faturas.add(chave)
                    faturas.append(_montar_fatura_financeira(resumo))

        itens.extend(
            _aplicar_filtros_financeiros(
                faturas,
                status_liquidacao=status_liquidacao,
                conta_id=conta_id,
                busca=busca,
                valor_modo=valor_modo,
                valor_ref=valor_ref_num,
            )
        )

    itens.sort(key=lambda item: (item.data, item.id), reverse=True)
    total = len(itens)
    params = PaginationParams(page=page, page_size=page_size)
    skip = (page - 1) * page_size
    return PagedResponse(
        data=itens[skip: skip + page_size],
        meta=PaginationMetaBuilder.build(total, params),
    )


@router.get("/{transacao_id}", response_model=TransacaoResponse)
def buscar_transacao(
    transacao_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Busca uma transação específica"""
    transacao = crud.get_transacao(db, transacao_id, access_ctx.effective_user.id)
    
    if not transacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transação não encontrada"
        )
    
    return transacao


@router.post("", response_model=TransacaoResponse, status_code=status.HTTP_201_CREATED)
def criar_transacao(
    transacao: TransacaoCreate,
    fatura_periodo_inicio: date | None = Query(default=None),
    fatura_periodo_fim: date | None = Query(default=None),
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """
    Cria uma nova transação.
    
    **Sistema de Dízimo Automático:**
    - Se `tem_dizimo=true` e `tipo=entrada`:
      - Cria a entrada normalmente
      - Cria automaticamente uma SAÍDA de dízimo
      - Ambas relacionadas via `transacao_dizimo_uuid`
      - Dízimo criado com `e_dizimo=true`
    
    **Exemplo:**
    ```json
    {
      "conta_id": 1,
      "categoria_id": 5,
      "descricao": "Salário Fevereiro",
      "valor": 5000.00,
      "tipo": "entrada",
      "data": "2024-02-06",
      "tem_dizimo": true,
      "percentual_dizimo": 10.0
    }
    ```
    
    **Resultado:**
    - Entrada: R$ 5.000 (id=1, uuid=abc-123)
    - Saída: R$ 500 (Dízimo, id=2, uuid=abc-123, e_dizimo=true)
    - Saldo: +R$ 4.500
    """
    if fatura_periodo_inicio and fatura_periodo_fim:
        if not (fatura_periodo_inicio <= transacao.data <= fatura_periodo_fim):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Data da transação deve estar entre {fatura_periodo_inicio.isoformat()} e {fatura_periodo_fim.isoformat()}.",
            )
    try:
        nova_transacao = crud.criar_transacao(db, transacao, access_ctx.effective_user.id)
        return nova_transacao
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{transacao_id}/duplicar", response_model=TransacaoResponse, status_code=status.HTTP_201_CREATED)
def duplicar_transacao(
    transacao_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Duplica uma transacao individual usando data e vencimento atuais."""
    try:
        nova_transacao = crud.duplicar_transacao(db, transacao_id, access_ctx.effective_user.id)

        if not nova_transacao:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transação não encontrada"
            )

        return nova_transacao
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{transacao_id}", response_model=TransacaoResponse)
def atualizar_transacao(
    transacao_id: int,
    transacao: TransacaoUpdate,
    fatura_periodo_inicio: date | None = Query(default=None),
    fatura_periodo_fim: date | None = Query(default=None),
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """
    Atualiza uma transação existente.
    
    ⚠️ **Importante:**
    - Não é possível editar transações de dízimo diretamente (e_dizimo=true)
    - Para alterar o dízimo, edite a entrada original
    - Se a entrada tinha dízimo, o dízimo será atualizado automaticamente
    """
    if fatura_periodo_inicio and fatura_periodo_fim and transacao.data is not None:
        if not (fatura_periodo_inicio <= transacao.data <= fatura_periodo_fim):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Data da transação deve estar entre {fatura_periodo_inicio.isoformat()} e {fatura_periodo_fim.isoformat()}.",
            )
    try:
        transacao_atualizada = crud.atualizar_transacao(
            db, transacao_id, access_ctx.effective_user.id, transacao
        )
        
        if not transacao_atualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transação não encontrada"
            )
        
        return transacao_atualizada
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{transacao_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_transacao(
    transacao_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """
    Deleta uma transação.

    ⚠️ **Importante:**
    - Não é possível deletar transações de dízimo diretamente
    - Ao deletar uma entrada com dízimo, o dízimo é deletado automaticamente
    - O saldo da conta é recalculado
    """
    try:
        sucesso = crud.deletar_transacao(db, transacao_id, access_ctx.effective_user.id)

        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transação não encontrada"
            )

        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/export")
def exportar_csv(
    tipo: TipoTransacao | None = Query(default=None),
    status_liquidacao: StatusLiquidacao | None = Query(default=None),
    fixa: str | None = Query(default=None, pattern="^(fixas|nao_fixas)$"),
    conta_id: int | None = None,
    categoria_id: int | None = None,
    mes: int | None = Query(default=None, ge=1, le=12),
    ano: int | None = Query(default=None, ge=2000, le=2100),
    busca: str | None = None,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    fixa_bool = None
    if fixa == "fixas":
        fixa_bool = True
    elif fixa == "nao_fixas":
        fixa_bool = False

    sem_categoria = categoria_id == -1
    categoria_normalizada = None if sem_categoria else categoria_id

    transacoes, _ = crud.get_transacoes(
        db=db,
        user_id=access_ctx.effective_user.id,
        tipo=tipo,
        status_liquidacao=status_liquidacao,
        fixa=fixa_bool,
        conta_id=conta_id,
        categoria_id=categoria_normalizada,
        sem_categoria=sem_categoria,
        mes=mes,
        ano=ano,
        busca=busca,
    )

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "data", "descricao", "tipo", "valor", "status_liquidacao", "conta_id", "categoria_id", "fixa", "observacoes"])
    for t in transacoes:
        writer.writerow([
            t.id,
            t.data.isoformat() if t.data else "",
            t.descricao or "",
            t.tipo.value if t.tipo else "",
            t.valor,
            t.status_liquidacao.value if t.status_liquidacao else "",
            t.conta_id or "",
            t.categoria_id or "",
            "sim" if t.fixa else "nao",
            (t.observacoes or "").replace("\n", " "),
        ])

    buf.seek(0)
    filename = "transacoes"
    if ano:
        filename += f"_{ano}"
        if mes:
            filename += f"_{mes:02d}"
    filename += ".csv"

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
