from datetime import date, datetime
from typing import List, Optional

from .base import TransacaoImportada


def _cnab_date(s: str) -> Optional[date]:
    s = s.strip()
    if not s or s == "00000000":
        return None
    try:
        return datetime.strptime(s, "%Y%m%d").date()
    except ValueError:
        return None


def _cnab_value(s: str, casas: int = 2) -> float:
    try:
        return round(int(s.strip()) / (10 ** casas), 2)
    except (ValueError, ZeroDivisionError):
        return 0.0


def parse_cnab240(content: bytes) -> List[TransacaoImportada]:
    text = content.decode("latin-1", errors="replace")
    lines = [ln for ln in text.splitlines() if len(ln) >= 240]
    result: List[TransacaoImportada] = []

    for line in lines:
        tipo_reg = line[7]   # posição 8 (1-indexed) — tipo do registro
        if tipo_reg != "3":
            continue

        segmento = line[13]  # posição 14 (1-indexed) — segmento

        if segmento == "A":
            # Segmento A — TED / DOC / PIX / transferências
            # Posições (1-indexed → slice 0-indexed):
            #   44-73  → [43:73]  nome do favorecido (30)
            #   94-101 → [93:101] data pagamento AAAAMMDD (8)
            #  110-124 → [109:124] valor pagamento (15, 2 decimais)
            #  145-152 → [144:152] data real do pagamento (8)
            #  153-167 → [152:167] valor real do pagamento (15, 2 decimais)
            nome = line[43:73].strip()
            data_str = line[93:101]
            valor_str = line[109:124]
            data_real_str = line[144:152]
            valor_real_str = line[152:167]

            # Prefere data e valor reais quando disponíveis
            dt = _cnab_date(data_real_str) or _cnab_date(data_str)
            valor_raw = valor_real_str if valor_real_str.strip() not in ("", "000000000000000") else valor_str
            valor = _cnab_value(valor_raw)

            if dt is None or valor <= 0 or not nome:
                continue

            result.append(TransacaoImportada(
                descricao=nome[:200],
                valor=valor,
                tipo="saida",   # Seg. A = pagamento efetuado (saída)
                data=dt,
            ))

        elif segmento == "J":
            # Segmento J — pagamento de boleto
            # Posições (1-indexed → slice 0-indexed):
            #   58-87  → [57:87]  nome do beneficiário (30)
            #   88-95  → [87:95]  data vencimento AAAAMMDD (8)
            #  141-148 → [140:148] data pagamento AAAAMMDD (8)
            #  149-163 → [148:163] valor pago (15, 2 decimais)
            nome = line[57:87].strip()
            data_pgto_str = line[140:148]
            data_venc_str = line[87:95]
            valor_str = line[148:163]

            dt = _cnab_date(data_pgto_str) or _cnab_date(data_venc_str)
            valor = _cnab_value(valor_str)

            if dt is None or valor <= 0:
                continue

            desc = nome or "Boleto"
            result.append(TransacaoImportada(
                descricao=desc[:200],
                valor=valor,
                tipo="saida",   # Boleto = saída
                data=dt,
            ))

        elif segmento == "C":
            # Segmento C — crédito em conta (salário, transferência recebida)
            # Posições (1-indexed → slice 0-indexed):
            #   44-73  → [43:73]  nome do pagador (30)
            #   94-101 → [93:101] data crédito AAAAMMDD (8)
            #  110-124 → [109:124] valor (15, 2 decimais)
            nome = line[43:73].strip()
            data_str = line[93:101]
            valor_str = line[109:124]

            dt = _cnab_date(data_str)
            valor = _cnab_value(valor_str)

            if dt is None or valor <= 0 or not nome:
                continue

            result.append(TransacaoImportada(
                descricao=nome[:200],
                valor=valor,
                tipo="entrada",
                data=dt,
            ))

    return result
