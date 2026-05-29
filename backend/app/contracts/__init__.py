from .categoria import CategoriaRepositoryProtocol
from .conta import ContaRepositoryProtocol
from .delegacao import DelegacaoRepositoryProtocol
from .meta import MetaRepositoryProtocol
from .orcamento import OrcamentoRepositoryProtocol
from .transacao import TransacaoRepositoryProtocol

__all__ = [
    "CategoriaRepositoryProtocol",
    "ContaRepositoryProtocol",
    "DelegacaoRepositoryProtocol",
    "MetaRepositoryProtocol",
    "OrcamentoRepositoryProtocol",
    "TransacaoRepositoryProtocol",
]
