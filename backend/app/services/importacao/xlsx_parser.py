import io
from datetime import date, datetime
from typing import List, Optional

from .base import (
    COLS_CREDIT,
    COLS_DATE,
    COLS_DEBIT,
    COLS_DESC,
    COLS_VALUE,
    TransacaoImportada,
    _find_col,
    _norm,
    _parse_date,
    _parse_value,
)


def _cell_date(val) -> Optional[date]:
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        return _parse_date(val)
    return None


def _cell_value(val) -> Optional[float]:
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        return _parse_value(val)
    return None


def parse_xlsx(content: bytes) -> List[TransacaoImportada]:
    try:
        import openpyxl
    except ImportError:
        raise ImportError("openpyxl é necessário para importar arquivos XLSX. Execute: pip install openpyxl")

    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    header_idx = 0
    headers_norm: List[str] = []
    for i, row in enumerate(rows[:15]):
        norm = [_norm(str(c or "")) for c in row]
        if any(n in COLS_DATE or n in COLS_DESC or n in COLS_VALUE for n in norm):
            header_idx = i
            headers_norm = norm
            break

    if not headers_norm:
        return []

    col_date = _find_col(headers_norm, COLS_DATE)
    col_desc = _find_col(headers_norm, COLS_DESC)
    col_val = _find_col(headers_norm, COLS_VALUE)
    col_cred = _find_col(headers_norm, COLS_CREDIT)
    col_deb = _find_col(headers_norm, COLS_DEBIT)

    if col_date is None or col_desc is None:
        return []

    result: List[TransacaoImportada] = []

    for row in rows[header_idx + 1:]:
        if not row or all(c is None for c in row):
            continue

        def get(idx: Optional[int]):
            if idx is None or idx >= len(row):
                return None
            return row[idx]

        dt = _cell_date(get(col_date))
        desc_raw = get(col_desc)
        desc = str(desc_raw).strip() if desc_raw is not None else ""

        if dt is None or not desc:
            continue

        if col_val is not None:
            v = _cell_value(get(col_val))
            if v is None:
                continue
            tipo = "entrada" if v > 0 else "saida"
            valor = abs(v)
        elif col_cred is not None and col_deb is not None:
            cred = _cell_value(get(col_cred)) or 0.0
            deb = _cell_value(get(col_deb)) or 0.0
            if cred > 0:
                tipo, valor = "entrada", cred
            elif deb > 0:
                tipo, valor = "saida", deb
            else:
                continue
        else:
            continue

        if valor <= 0:
            continue

        result.append(TransacaoImportada(
            descricao=desc[:200],
            valor=round(valor, 2),
            tipo=tipo,
            data=dt,
        ))

    return result
