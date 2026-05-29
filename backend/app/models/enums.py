import enum


class TipoTransacao(str, enum.Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"
    TRANSFERENCIA = "transferencia"


class TipoConta(str, enum.Enum):
    CARTEIRA = "carteira"
    CONTA_CORRENTE = "conta_corrente"
    POUPANCA = "poupanca"
    CARTAO_CREDITO = "cartao_credito"
    INVESTIMENTO = "investimento"
    OUTRO = "outro"


class StatusLiquidacao(str, enum.Enum):
    PREVISTO = "previsto"
    LIQUIDADO = "liquidado"
    ATRASADO = "atrasado"
    CANCELADO = "cancelado"


class DelegacaoStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REVOKED = "revoked"
