import re
from datetime import date, datetime
from typing import List, Optional

from .base import TransacaoImportada


def _parse_ofx_date(s: str) -> Optional[date]:
    s = re.sub(r"[\[<].*", "", s).strip()[:8]
    try:
        return datetime.strptime(s, "%Y%m%d").date()
    except ValueError:
        return None


def _get_tag(block: str, tag: str) -> Optional[str]:
    m = re.search(rf"<{tag}[^>]*>\s*([^<\n\r]+)", block, re.IGNORECASE)
    return m.group(1).strip() if m else None


def parse_ofx(content: bytes) -> List[TransacaoImportada]:
    text = ""
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"):
        try:
            text = content.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    # Tenta blocos XML-style com closing tag
    blocks = re.findall(r"<STMTTRN[^>]*>(.*?)</STMTTRN>", text, re.DOTALL | re.IGNORECASE)
    if not blocks:
        # SGML-style sem closing tags
        blocks = re.findall(
            r"<STMTTRN>(.*?)(?=<STMTTRN>|</BANKTRANLIST>|<LEDGERBAL>|$)",
            text,
            re.DOTALL | re.IGNORECASE,
        )

    result: List[TransacaoImportada] = []

    for block in blocks:
        trntype = (_get_tag(block, "TRNTYPE") or "other").lower()
        dtposted = _get_tag(block, "DTPOSTED")
        amount_str = _get_tag(block, "TRNAMT")
        memo = _get_tag(block, "MEMO") or _get_tag(block, "NAME") or ""

        if not dtposted or not amount_str or not memo:
            continue

        dt = _parse_ofx_date(dtposted)
        if dt is None:
            continue

        try:
            amount = float(amount_str.replace(",", "."))
        except ValueError:
            continue

        if amount > 0:
            tipo = "entrada"
        elif amount < 0:
            tipo = "saida"
        else:
            continue

        result.append(TransacaoImportada(
            descricao=memo[:200],
            valor=round(abs(amount), 2),
            tipo=tipo,
            data=dt,
        ))

    return result
