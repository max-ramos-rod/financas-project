import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional, Set


@dataclass
class TransacaoImportada:
    descricao: str
    valor: float        # sempre positivo
    tipo: str           # "entrada" | "saida"
    data: date
    observacoes: Optional[str] = None


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
