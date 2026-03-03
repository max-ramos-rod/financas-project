import csv
import io
import unicodedata
from calendar import monthrange
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import AccessContext, get_access_context
from app.db.session import get_db
from app.models import Categoria, StatusLiquidacao, TipoTransacao, Transacao
from app.schemas.relatorio import DRECategoriaResumo, DREMensalResponse

# ReportLab opcional: usa layout moderno quando disponivel.
try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

router = APIRouter()


def _valor_efetivo(transacao: Transacao) -> float:
    return max(
        0.0,
        (transacao.valor or 0)
        + (transacao.valor_multa or 0)
        + (transacao.valor_juros or 0)
        - (transacao.valor_desconto or 0),
    )


def _pdf_safe_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(ch for ch in normalized if ord(ch) < 128 and not unicodedata.combining(ch))
    escaped = ascii_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return escaped


def _build_simple_pdf(lines: list[str]) -> bytes:
    prepared_lines = lines[:52]
    text_parts = ["BT", "/F1 10 Tf", "40 800 Td", "14 TL"]
    for idx, line in enumerate(prepared_lines):
        safe_line = _pdf_safe_text(line)
        if idx == 0:
            text_parts.append(f"({safe_line}) Tj")
        else:
            text_parts.append(f"T* ({safe_line}) Tj")
    text_parts.append("ET")
    stream = "\n".join(text_parts).encode("latin-1", errors="ignore")

    objects = []
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objects.append(b"2 0 obj\n<< /Type /Pages /Count 1 /Kids [3 0 R] >>\nendobj\n")
    objects.append(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )
    objects.append(
        b"4 0 obj\n<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"\nendstream\nendobj\n"
    )
    objects.append(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode("ascii")
    )
    return bytes(pdf)


def _fmt_money(value: float) -> str:
    signal = "-" if value < 0 else ""
    abs_value = abs(value)
    integer = int(abs_value)
    decimal = int(round((abs_value - integer) * 100))
    int_part = f"{integer:,}".replace(",", ".")
    return f"{signal}R$ {int_part},{decimal:02d}"


def _fmt_pct(part: float, total: float) -> str:
    if total == 0:
        return "0,0%"
    return f"{part / total * 100:.1f}%".replace(".", ",")


def _pad_row(label: str, value: str, total_width: int = 90) -> str:
    label = (label or "")[:60]
    value = value or ""
    spaces = max(2, total_width - len(label) - len(value))
    return f"{label}{' ' * spaces}{value}"


def _build_reportlab_pdf(dre: DREMensalResponse) -> bytes:
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("ReportLab indisponivel")

    dark_blue = colors.HexColor("#1A2B4A")
    medium_blue = colors.HexColor("#2D5086")
    green = colors.HexColor("#1A7A4A")
    red = colors.HexColor("#C0392B")
    light_green = colors.HexColor("#E8F5EE")
    light_red = colors.HexColor("#FDF0EE")
    gray = colors.HexColor("#6C757D")
    light_gray = colors.HexColor("#F5F6FA")
    border = colors.HexColor("#DEE2E6")
    white = colors.white

    def cat_table(data: list[list], header_color, total_color, total_bg) -> Table:
        tbl = Table(data, colWidths=[9 * cm, 5 * cm, 3 * cm])
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), header_color),
                    ("TEXTCOLOR", (0, 0), (-1, 0), white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("BACKGROUND", (0, -1), (-1, -1), total_bg),
                    ("TEXTCOLOR", (0, -1), (-1, -1), total_color),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -2), [white, light_gray]),
                    ("GRID", (0, 0), (-1, -1), 0.5, border),
                    ("PADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        return tbl

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    title_style = ParagraphStyle(
        "DRETitle",
        fontSize=20,
        leading=24,
        fontName="Helvetica-Bold",
        textColor=white,
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    subtitle_style = ParagraphStyle(
        "DRESubtitle",
        fontSize=10,
        leading=14,
        fontName="Helvetica",
        textColor=colors.HexColor("#B0C4DE"),
        alignment=TA_CENTER,
        spaceBefore=4,
    )
    section_style = ParagraphStyle(
        "DRESection", fontSize=11, fontName="Helvetica-Bold", textColor=dark_blue, spaceBefore=12, spaceAfter=6
    )
    meta_style_l = ParagraphStyle("DREMetaL", fontSize=9, fontName="Helvetica", textColor=gray)
    meta_style_r = ParagraphStyle("DREMetaR", fontSize=9, fontName="Helvetica", textColor=gray, alignment=TA_RIGHT)
    footer_style = ParagraphStyle("DREFooter", fontSize=8, fontName="Helvetica", textColor=gray, alignment=TA_CENTER)

    meses = ["", "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_nome = meses[dre.mes]
    periodo = f"{dre.mes:02d}/{dre.ano}"
    gerado_em = date.today().strftime("%d/%m/%Y")
    resultado_positivo = dre.resultado_total >= 0
    resultado_bg = light_green if resultado_positivo else light_red
    resultado_color = green if resultado_positivo else red

    story = []

    header_data = [
        [Paragraph("FINANCAS CRISTAS", title_style)],
        [Paragraph(f"DEMONSTRATIVO DO RESULTADO DO EXERCICIO - {mes_nome.upper()} {dre.ano}", subtitle_style)],
    ]
    header_table = Table(header_data, colWidths=[17 * cm])
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), dark_blue),
                ("PADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, 0), 18),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("TOPPADDING", (0, 1), (-1, 1), 8),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 18),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 8))

    meta_table = Table(
        [[Paragraph(f"Periodo: <b>{periodo}</b>", meta_style_l), Paragraph(f"Gerado em: <b>{gerado_em}</b>", meta_style_r)]],
        colWidths=[8.5 * cm, 8.5 * cm],
    )
    meta_table.setStyle(TableStyle([("PADDING", (0, 0), (-1, -1), 2)]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("RESUMO FINANCEIRO", section_style))
    resumo_data = [
        ["", "Liquidado", "Previsto", "Total"],
        ["Entradas", _fmt_money(dre.entradas_liquidadas), _fmt_money(dre.entradas_previstas), _fmt_money(dre.entradas_total)],
        ["Saidas", _fmt_money(dre.saidas_liquidadas), _fmt_money(dre.saidas_previstas), _fmt_money(dre.saidas_total)],
        ["Resultado", _fmt_money(dre.resultado_liquidado), _fmt_money(dre.resultado_previsto), _fmt_money(dre.resultado_total)],
    ]
    resumo_table = Table(resumo_data, colWidths=[5 * cm, 4 * cm, 4 * cm, 4 * cm])
    resumo_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), medium_blue),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("BACKGROUND", (0, 1), (-1, 1), light_green),
                ("TEXTCOLOR", (1, 1), (-1, 1), green),
                ("BACKGROUND", (0, 2), (-1, 2), light_red),
                ("TEXTCOLOR", (1, 2), (-1, 2), red),
                ("BACKGROUND", (0, 3), (-1, 3), resultado_bg),
                ("TEXTCOLOR", (1, 3), (-1, 3), resultado_color),
                ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, border),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(resumo_table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("ANALISE POR CATEGORIA - ENTRADAS", section_style))
    entradas_data = [["Categoria", "Valor", "% do Total"]]
    for item in dre.entradas_por_categoria:
        entradas_data.append([item.categoria_nome, _fmt_money(item.valor), _fmt_pct(item.valor, dre.entradas_total)])
    if not dre.entradas_por_categoria:
        entradas_data.append(["Sem entradas no periodo.", "", ""])
    entradas_data.append(["TOTAL ENTRADAS", _fmt_money(dre.entradas_total), "100,0%"])
    story.append(cat_table(entradas_data, green, green, light_green))
    story.append(Spacer(1, 20))

    story.append(Paragraph("ANALISE POR CATEGORIA - SAIDAS", section_style))
    saidas_data = [["Categoria", "Valor", "% do Total"]]
    for item in dre.saidas_por_categoria:
        saidas_data.append([item.categoria_nome, _fmt_money(item.valor), _fmt_pct(item.valor, dre.saidas_total)])
    if not dre.saidas_por_categoria:
        saidas_data.append(["Sem saidas no periodo.", "", ""])
    saidas_data.append(["TOTAL SAIDAS", _fmt_money(dre.saidas_total), "100,0%"])
    story.append(cat_table(saidas_data, red, red, light_red))
    story.append(Spacer(1, 20))

    result_data = [
        ["Total de Entradas", _fmt_money(dre.entradas_total)],
        ["Total de Saidas", _fmt_money(dre.saidas_total)],
        ["RESULTADO LIQUIDO", _fmt_money(dre.resultado_total)],
    ]
    res_table = Table(result_data, colWidths=[11 * cm, 6 * cm])
    res_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("TEXTCOLOR", (1, 0), (1, 0), green),
                ("TEXTCOLOR", (1, 1), (1, 1), red),
                ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
                ("FONTSIZE", (0, 2), (-1, 2), 12),
                ("BACKGROUND", (0, 2), (-1, 2), resultado_bg),
                ("TEXTCOLOR", (0, 2), (-1, 2), resultado_color),
                ("BACKGROUND", (0, 0), (-1, 0), light_green),
                ("BACKGROUND", (0, 1), (-1, 1), light_red),
                ("GRID", (0, 0), (-1, -1), 0.5, border),
                ("PADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(res_table)
    story.append(Spacer(1, 24))

    footer_table = Table(
        [[Paragraph(f"Relatorio gerado automaticamente pelo sistema Financas Cristas - {mes_nome} {dre.ano}", footer_style)]],
        colWidths=[17 * cm],
    )
    footer_table.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 10), ("LINEABOVE", (0, 0), (-1, 0), 0.5, border)]))
    story.append(footer_table)

    doc.build(story)
    return buffer.getvalue()


def _calcular_dre_mensal(db: Session, user_id: int, mes: int, ano: int) -> DREMensalResponse:
    inicio = date(ano, mes, 1)
    fim = date(ano, mes, monthrange(ano, mes)[1])

    transacoes = db.query(Transacao).filter(
        Transacao.user_id == user_id,
        Transacao.data >= inicio,
        Transacao.data <= fim,
        Transacao.status_liquidacao != StatusLiquidacao.CANCELADO,
    ).all()

    categoria_ids = sorted({t.categoria_id for t in transacoes if t.categoria_id is not None})
    categorias_map: dict[int, str] = {}
    if categoria_ids:
        categorias = db.query(Categoria).filter(Categoria.id.in_(categoria_ids)).all()
        categorias_map = {c.id: c.nome for c in categorias}

    entradas_liquidadas = 0.0
    entradas_previstas = 0.0
    saidas_liquidadas = 0.0
    saidas_previstas = 0.0
    entradas_cat: dict[tuple[int | None, str], float] = {}
    saidas_cat: dict[tuple[int | None, str], float] = {}

    for t in transacoes:
        valor = _valor_efetivo(t)
        liquidada = t.status_liquidacao == StatusLiquidacao.LIQUIDADO
        categoria_nome = categorias_map.get(t.categoria_id, "Sem categoria")
        chave = (t.categoria_id, categoria_nome)

        if t.tipo == TipoTransacao.ENTRADA:
            if liquidada:
                entradas_liquidadas += valor
            else:
                entradas_previstas += valor
            entradas_cat[chave] = entradas_cat.get(chave, 0.0) + valor
        elif t.tipo == TipoTransacao.SAIDA:
            if liquidada:
                saidas_liquidadas += valor
            else:
                saidas_previstas += valor
            saidas_cat[chave] = saidas_cat.get(chave, 0.0) + valor

    def _to_sorted_list(data: dict[tuple[int | None, str], float]) -> list[DRECategoriaResumo]:
        itens = [
            DRECategoriaResumo(categoria_id=cid, categoria_nome=nome, valor=valor)
            for (cid, nome), valor in data.items()
        ]
        return sorted(itens, key=lambda i: i.valor, reverse=True)

    entradas_total = entradas_liquidadas + entradas_previstas
    saidas_total = saidas_liquidadas + saidas_previstas
    resultado_liquidado = entradas_liquidadas - saidas_liquidadas
    resultado_previsto = entradas_previstas - saidas_previstas
    resultado_total = entradas_total - saidas_total

    return DREMensalResponse(
        mes=mes,
        ano=ano,
        entradas_liquidadas=entradas_liquidadas,
        entradas_previstas=entradas_previstas,
        entradas_total=entradas_total,
        saidas_liquidadas=saidas_liquidadas,
        saidas_previstas=saidas_previstas,
        saidas_total=saidas_total,
        resultado_liquidado=resultado_liquidado,
        resultado_previsto=resultado_previsto,
        resultado_total=resultado_total,
        entradas_por_categoria=_to_sorted_list(entradas_cat),
        saidas_por_categoria=_to_sorted_list(saidas_cat),
    )


@router.get("/dre-mensal", response_model=DREMensalResponse)
def obter_dre_mensal(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000, le=2100),
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    return _calcular_dre_mensal(db, access_ctx.effective_user.id, mes, ano)


@router.get("/dre-mensal/export")
def exportar_dre_mensal_csv(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000, le=2100),
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    dre = _calcular_dre_mensal(db, access_ctx.effective_user.id, mes, ano)
    if not dre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relatorio nao encontrado")

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")

    writer.writerow(["DRE Mensal"])
    writer.writerow(["Mes", dre.mes])
    writer.writerow(["Ano", dre.ano])
    writer.writerow([])
    writer.writerow(["Resumo", "Valor"])
    writer.writerow(["Entradas liquidadas", f"{dre.entradas_liquidadas:.2f}"])
    writer.writerow(["Entradas previstas", f"{dre.entradas_previstas:.2f}"])
    writer.writerow(["Entradas total", f"{dre.entradas_total:.2f}"])
    writer.writerow(["Saidas liquidadas", f"{dre.saidas_liquidadas:.2f}"])
    writer.writerow(["Saidas previstas", f"{dre.saidas_previstas:.2f}"])
    writer.writerow(["Saidas total", f"{dre.saidas_total:.2f}"])
    writer.writerow(["Resultado liquidado", f"{dre.resultado_liquidado:.2f}"])
    writer.writerow(["Resultado previsto", f"{dre.resultado_previsto:.2f}"])
    writer.writerow(["Resultado total", f"{dre.resultado_total:.2f}"])
    writer.writerow([])
    writer.writerow(["Entradas por categoria"])
    writer.writerow(["Categoria", "Valor"])
    for item in dre.entradas_por_categoria:
        writer.writerow([item.categoria_nome, f"{item.valor:.2f}"])
    writer.writerow([])
    writer.writerow(["Saidas por categoria"])
    writer.writerow(["Categoria", "Valor"])
    for item in dre.saidas_por_categoria:
        writer.writerow([item.categoria_nome, f"{item.valor:.2f}"])

    content = buffer.getvalue()
    filename = f"dre_mensal_{ano}_{mes:02d}.csv"
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/dre-mensal/export-pdf")
def exportar_dre_mensal_pdf(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000, le=2100),
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    dre = _calcular_dre_mensal(db, access_ctx.effective_user.id, mes, ano)
    if not dre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relatorio nao encontrado")

    if REPORTLAB_AVAILABLE:
        pdf_content = _build_reportlab_pdf(dre)
    else:
        now = date.today().isoformat()
        separator = "-" * 90
        lines = [
            "FINANCAS CRISTAS - RELATORIO GERENCIAL",
            "DRE MENSAL",
            separator,
            f"Periodo: {dre.mes:02d}/{dre.ano}    Gerado em: {now}",
            separator,
            "",
            "RESUMO FINANCEIRO",
            _pad_row("Entradas liquidadas", _fmt_money(dre.entradas_liquidadas)),
            _pad_row("Entradas previstas", _fmt_money(dre.entradas_previstas)),
            _pad_row("Entradas total", _fmt_money(dre.entradas_total)),
            _pad_row("Saidas liquidadas", _fmt_money(dre.saidas_liquidadas)),
            _pad_row("Saidas previstas", _fmt_money(dre.saidas_previstas)),
            _pad_row("Saidas total", _fmt_money(dre.saidas_total)),
            _pad_row("Resultado liquidado", _fmt_money(dre.resultado_liquidado)),
            _pad_row("Resultado previsto", _fmt_money(dre.resultado_previsto)),
            _pad_row("Resultado total", _fmt_money(dre.resultado_total)),
            "",
            "ANALISE POR CATEGORIA - ENTRADAS",
            separator,
            _pad_row("Categoria", "Valor"),
            separator,
        ]
        if dre.entradas_por_categoria:
            for item in dre.entradas_por_categoria:
                lines.append(_pad_row(item.categoria_nome, _fmt_money(item.valor)))
        else:
            lines.append("Sem entradas no periodo.")

        lines.extend(
            [
                "",
                "ANALISE POR CATEGORIA - SAIDAS",
                separator,
                _pad_row("Categoria", "Valor"),
                separator,
            ]
        )
        if dre.saidas_por_categoria:
            for item in dre.saidas_por_categoria:
                lines.append(_pad_row(item.categoria_nome, _fmt_money(item.valor)))
        else:
            lines.append("Sem saidas no periodo.")
        pdf_content = _build_simple_pdf(lines)

    filename = f"dre_mensal_{ano}_{mes:02d}.pdf"
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
