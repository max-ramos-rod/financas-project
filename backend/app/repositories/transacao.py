from app.core.repositories import SQLAlchemyRepository
from app.models import Transacao


class TransacaoRepository(SQLAlchemyRepository[Transacao]):
    model = Transacao
