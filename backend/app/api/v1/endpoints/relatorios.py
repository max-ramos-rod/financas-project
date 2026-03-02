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


def _pad_row(label: str, value: str, total_width: int = 90) -> str:
    label = (label or "")[:60]
    value = value or ""
    spaces = max(2, total_width - len(label) - len(value))
    return f"{label}{' ' * spaces}{value}"


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

    now = date.today().isoformat()
    separator = "-" * 90

    lines = [
        "FINANCAS CRISTAIS - RELATORIO GERENCIAL",
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
