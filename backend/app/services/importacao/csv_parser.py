import csv
import io
import unicodedata
from datetime import date, datetime
from typing import List, Optional, Set

from .base import TransacaoImportada


def _norm(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s.lower().strip())
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def _parse_date(s: str) -> Optional[date]:
    s = s.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y", "%Y%m%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_value(s: str) -> Optional[float]:
    if not s:
        return None
    s = s.strip().replace(" ", "").replace("R$", "")
    if not s or s in ("-", "+"):
        return None
    # "1.234,56" — formato brasileiro
    if "," in s and "." in s:
        if s.rindex(",") > s.rindex("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


COLS_DATE: Set[str] = {"data", "date", "dt", "competencia", "datalancamento", "datalanc", "datamovimento"}
COLS_DESC: Set[str] = {
    "descricao", "historico", "lancamento", "memo", "description",
    "title", "nome", "complemento", "estabelecimento", "detalhes",
    "historicotransacao", "transacao",
}
COLS_VALUE: Set[str] = {"valor", "amount", "value", "vlr", "montante", "valortransacao", "importancia"}
COLS_CREDIT: Set[str] = {"credito", "entrada", "credit", "creditos", "entradas", "valorentrada", "cr"}
COLS_DEBIT: Set[str] = {"debito", "saida", "debit", "debitos", "saidas", "valorsaida", "valordebit", "db", "dc"}


def _find_col(headers: List[str], options: Set[str]) -> Optional[int]:
    for i, h in enumerate(headers):
        if h in options:
            return i
    for i, h in enumerate(headers):
        for opt in options:
            if opt in h or h in opt:
                return i
    return None


def parse_csv(content: bytes) -> List[TransacaoImportada]:
    text = ""
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            text = content.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    first_line = text.split("\n")[0] if text else ""
    delimiter = ";" if first_line.count(";") >= first_line.count(",") else ","

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)

    header_idx = 0
    headers_norm: List[str] = []
    for i, row in enumerate(rows[:15]):
        norm = [_norm(c) for c in row]
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
        if not row or all(c.strip() == "" for c in row):
            continue

        def get(idx: Optional[int]) -> str:
            if idx is None or idx >= len(row):
                return ""
            return row[idx].strip()

        data_str = get(col_date)
        desc = get(col_desc)
        if not data_str or not desc:
            continue

        dt = _parse_date(data_str)
        if dt is None:
            continue

        if col_val is not None:
            v = _parse_value(get(col_val))
            if v is None:
                continue
            tipo = "entrada" if v > 0 else "saida"
            valor = abs(v)
        elif col_cred is not None and col_deb is not None:
            cred = _parse_value(get(col_cred)) or 0.0
            deb = _parse_value(get(col_deb)) or 0.0
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
