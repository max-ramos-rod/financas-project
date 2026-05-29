from app.core.repositories import SQLAlchemyRepository
from app.models import Delegacao


class DelegacaoRepository(SQLAlchemyRepository[Delegacao]):
    model = Delegacao
