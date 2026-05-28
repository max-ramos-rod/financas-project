from typing import List, Tuple

from .base import TransacaoImportada


def _sniff_cnab240(content: bytes) -> bool:
    """Heurística: todas as primeiras linhas não-vazias têm exatamente 240 chars."""
    lines = content.decode("latin-1", errors="replace").splitlines()
    non_empty = [ln for ln in lines[:5] if ln.strip()]
    return bool(non_empty) and all(len(ln) == 240 for ln in non_empty)


def _sniff_ofx(content: bytes) -> bool:
    sample = content[:1024].decode("latin-1", errors="replace").upper()
    return "OFXHEADER" in sample or "<OFX>" in sample or "<STMTTRN>" in sample


def detectar_e_parsear(content: bytes, filename: str) -> Tuple[str, List[TransacaoImportada]]:
    """Retorna (formato_detectado, lista_de_transacoes). Levanta ValueError se não reconhecido."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in ("ofx", "qfx"):
        from .ofx_parser import parse_ofx
        return "OFX/QFX", parse_ofx(content)

    if ext in ("xlsx", "xls"):
        from .xlsx_parser import parse_xlsx
        return "XLSX", parse_xlsx(content)

    if ext == "csv":
        from .csv_parser import parse_csv
        return "CSV", parse_csv(content)

    if ext in ("ret", "rem", "cnab"):
        from .cnab_parser import parse_cnab240
        return "CNAB 240", parse_cnab240(content)

    # Extensão ambígua (.txt) ou ausente — detecta pelo conteúdo
    if _sniff_ofx(content):
        from .ofx_parser import parse_ofx
        return "OFX", parse_ofx(content)

    if _sniff_cnab240(content):
        from .cnab_parser import parse_cnab240
        return "CNAB 240", parse_cnab240(content)

    # Fallback: tenta CSV
    from .csv_parser import parse_csv
    return "CSV", parse_csv(content)
