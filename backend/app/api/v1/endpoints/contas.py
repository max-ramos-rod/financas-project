import io
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import AccessContext, get_access_context
from app.core.pagination import PaginationMetaBuilder, PaginationParams
from app.core.responses import PagedResponse
from app.crud import crud_conta as crud
from app.db.session import get_db
from app.domain.cartao_fatura import (
    determinar_competencia_fatura_atual,
    obter_resumo_fatura_atual,
    obter_resumo_fatura_fechada_atual,
    obter_resumo_fatura_por_competencia,
    valor_efetivo_transacao,
)
from app.models import ContaCartaoCiclo, TipoConta
from app.schemas.conta import (
    ContaCreate,
    ContaResponse,
    ContaUpdate,
    FaturaCicloAjusteRequest,
    FaturaItemResponse,
    FaturaResumoResponse,
    PagarFaturaRequest,
)
from app.services.conta import ContaService

_service = ContaService()

router = APIRouter()


def _buscar_cartao_ou_erro(db: Session, conta_id: int, user_id: int):
    conta = crud.get_conta(db, conta_id, user_id)
    if not conta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta nao encontrada")
    if conta.tipo != TipoConta.CARTAO_CREDITO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conta nao e cartao de credito")
    if conta.dia_fechamento is None or conta.dia_vencimento is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cartao sem fechamento/vencimento configurado")
    return conta


def _resposta_fatura(resumo) -> FaturaResumoResponse:
    itens = [
        FaturaItemResponse(
            transacao_id=t.id,
            descricao=t.descricao,
            data=t.data,
            data_vencimento=t.data_vencimento,
            status_liquidacao=t.status_liquidacao.value,
            tipo=t.tipo.value,
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
        data_vencimento_real=resumo.data_vencimento_real,
        data_vencimento_fatura=resumo.data_vencimento_fatura,
        observacao_ciclo=resumo.observacao_ciclo,
        total_itens=resumo.total_itens,
        valor_total=resumo.valor_total,
        valor_pago=resumo.valor_pago,
        valor_a_pagar=resumo.valor_a_pagar,
        itens=itens,
    )


def _obter_resumo_fatura_ciclo_ou_erro(
    db: Session,
    *,
    conta_id: int,
    competencia_ano: int,
    competencia_mes: int,
    access_ctx: AccessContext,
):
    conta = _buscar_cartao_ou_erro(db, conta_id, access_ctx.effective_user.id)
    try:
        return obter_resumo_fatura_por_competencia(
            db,
            user_id=access_ctx.effective_user.id,
            conta=conta,
            competencia_ano=competencia_ano,
            competencia_mes=competencia_mes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=PagedResponse[ContaResponse])
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

    total = len(contas)
    params = PaginationParams(page=1, page_size=max(total, 1))
    return PagedResponse(data=contas, meta=PaginationMetaBuilder.build(total, params))


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
        return _service.criar(db, conta, access_ctx.effective_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{conta_id}", response_model=ContaResponse)
def atualizar_conta(
    conta_id: int,
    conta: ContaUpdate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    try:
        conta_atualizada = _service.atualizar(db, conta_id, access_ctx.effective_user.id, conta)
        if not conta_atualizada:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta nao encontrada")
        return conta_atualizada
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/{conta_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_conta(
    conta_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    if not _service.deletar(db, conta_id, access_ctx.effective_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta nao encontrada")
    return None


@router.get("/{conta_id}/faturas/{competencia_ano}/{competencia_mes}", response_model=FaturaResumoResponse)
def obter_fatura_por_ciclo(
    conta_id: int,
    competencia_ano: int,
    competencia_mes: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    if competencia_mes < 1 or competencia_mes > 12:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mes da fatura invalido")

    resumo = _obter_resumo_fatura_ciclo_ou_erro(
        db,
        conta_id=conta_id,
        competencia_ano=competencia_ano,
        competencia_mes=competencia_mes,
        access_ctx=access_ctx,
    )
    return _resposta_fatura(resumo)


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

    return _resposta_fatura(resumo)


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

    return _resposta_fatura(resumo)


@router.put("/{conta_id}/faturas/{competencia_ano}/{competencia_mes}/ajuste-ciclo", response_model=FaturaResumoResponse)
def ajustar_ciclo_fatura_por_competencia(
    conta_id: int,
    competencia_ano: int,
    competencia_mes: int,
    payload: FaturaCicloAjusteRequest,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    if competencia_mes < 1 or competencia_mes > 12:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mes da fatura invalido")

    conta = _buscar_cartao_ou_erro(db, conta_id, access_ctx.effective_user.id)
    resumo_ciclo = _obter_resumo_fatura_ciclo_ou_erro(
        db,
        conta_id=conta_id,
        competencia_ano=competencia_ano,
        competencia_mes=competencia_mes,
        access_ctx=access_ctx,
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

    if ciclo is None:
        ciclo = ContaCartaoCiclo(
            conta_id=conta.id,
            competencia_ano=competencia_ano,
            competencia_mes=competencia_mes,
            data_fechamento_prevista=resumo_ciclo.data_fechamento_prevista,
            data_vencimento_prevista=resumo_ciclo.data_vencimento_prevista,
        )

    ciclo.data_fechamento_prevista = resumo_ciclo.data_fechamento_prevista
    ciclo.data_vencimento_prevista = resumo_ciclo.data_vencimento_prevista
    ciclo.data_fechamento_real = payload.data_fechamento_real
    ciclo.data_vencimento_real = payload.data_vencimento_real
    ciclo.observacao = payload.observacao
    db.add(ciclo)
    db.commit()

    resumo = _obter_resumo_fatura_ciclo_ou_erro(
        db,
        conta_id=conta_id,
        competencia_ano=competencia_ano,
        competencia_mes=competencia_mes,
        access_ctx=access_ctx,
    )
    return _resposta_fatura(resumo)


@router.delete("/{conta_id}/faturas/{competencia_ano}/{competencia_mes}/ajuste-ciclo", response_model=FaturaResumoResponse)
def limpar_ajuste_ciclo_fatura_por_competencia(
    conta_id: int,
    competencia_ano: int,
    competencia_mes: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    if competencia_mes < 1 or competencia_mes > 12:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mes da fatura invalido")

    conta = _buscar_cartao_ou_erro(db, conta_id, access_ctx.effective_user.id)
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

    resumo = _obter_resumo_fatura_ciclo_ou_erro(
        db,
        conta_id=conta_id,
        competencia_ano=competencia_ano,
        competencia_mes=competencia_mes,
        access_ctx=access_ctx,
    )
    return _resposta_fatura(resumo)


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


@router.post("/{conta_id}/faturas/{competencia_ano}/{competencia_mes}/pagar", response_model=FaturaResumoResponse)
def pagar_fatura_por_ciclo(
    conta_id: int,
    competencia_ano: int,
    competencia_mes: int,
    payload: PagarFaturaRequest,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    if competencia_mes < 1 or competencia_mes > 12:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mes da fatura invalido")
    resumo_fatura = _obter_resumo_fatura_ciclo_ou_erro(
        db, conta_id=conta_id, competencia_ano=competencia_ano,
        competencia_mes=competencia_mes, access_ctx=access_ctx,
    )
    try:
        _service.pagar_fatura(db, conta_id, access_ctx.effective_user.id, payload, resumo_fatura)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    resumo_atualizado = _obter_resumo_fatura_ciclo_ou_erro(
        db, conta_id=conta_id, competencia_ano=competencia_ano,
        competencia_mes=competencia_mes, access_ctx=access_ctx,
    )
    return _resposta_fatura(resumo_atualizado)


@router.post("/{conta_id}/pagar-fatura", response_model=FaturaResumoResponse)
def pagar_fatura(
    conta_id: int,
    payload: PagarFaturaRequest,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    conta_cartao = _buscar_cartao_ou_erro(db, conta_id, access_ctx.effective_user.id)
    resumo_fatura = obter_resumo_fatura_fechada_atual(
        db, user_id=access_ctx.effective_user.id,
        conta=conta_cartao, ref_date=date.today(),
    )
    try:
        _service.pagar_fatura(db, conta_id, access_ctx.effective_user.id, payload, resumo_fatura)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    resumo = obter_resumo_fatura_fechada_atual(
        db, user_id=access_ctx.effective_user.id,
        conta=conta_cartao, ref_date=date.today(),
    )
    return _resposta_fatura(resumo)


@router.get("/{conta_id}/faturas/{competencia_ano}/{competencia_mes}/pdf")
def exportar_fatura_pdf(
    conta_id: int,
    competencia_ano: int,
    competencia_mes: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    resumo = _obter_resumo_fatura_ciclo_ou_erro(
        db,
        conta_id=conta_id,
        competencia_ano=competencia_ano,
        competencia_mes=competencia_mes,
        access_ctx=access_ctx,
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm, bottomMargin=15 * mm)
    styles = getSampleStyleSheet()
    ParagraphStyle("mono", parent=styles["Normal"], fontName="Courier", fontSize=8)
    title_style = ParagraphStyle("title", parent=styles["Heading1"], fontSize=14, spaceAfter=4)
    sub_style = ParagraphStyle("sub", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#555555"))

    meses_pt = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_nome = meses_pt[competencia_mes] if 1 <= competencia_mes <= 12 else str(competencia_mes)

    story = [
        Paragraph(f"Fatura — {resumo.conta_nome}", title_style),
        Paragraph(f"{mes_nome} {competencia_ano}  •  Período: {resumo.periodo_inicio.strftime('%d/%m/%Y')} a {resumo.periodo_fim.strftime('%d/%m/%Y')}", sub_style),
        Spacer(1, 6 * mm),
    ]

    header = ["Data", "Descrição", "Tipo", "Valor (R$)", "Status"]
    rows = [header]
    for item in resumo.itens:
        data_str = item.data.strftime("%d/%m/%Y") if item.data else ""
        efetivo = valor_efetivo_transacao(item)
        rows.append([
            data_str,
            item.descricao or "",
            item.tipo.value if item.tipo else "",
            f"{efetivo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            item.status_liquidacao.value if item.status_liquidacao else "",
        ])

    col_widths = [22 * mm, None, 20 * mm, 28 * mm, 22 * mm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(table)
    story.append(Spacer(1, 6 * mm))

    def _fmt(v: float) -> str:
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    totals_data = [
        ["Total da fatura", _fmt(resumo.valor_total)],
        ["Pago", _fmt(resumo.valor_pago)],
        ["A pagar", _fmt(resumo.valor_a_pagar)],
    ]
    totals_table = Table(totals_data, colWidths=[50 * mm, 40 * mm])
    totals_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEABOVE", (0, -1), (-1, -1), 0.5, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(totals_table)

    doc.build(story)
    buf.seek(0)

    filename = f"fatura_{conta_id}_{competencia_ano}_{competencia_mes:02d}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
