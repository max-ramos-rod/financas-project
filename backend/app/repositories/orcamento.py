from app.core.repositories import SQLAlchemyRepository
from app.models import Orcamento


class OrcamentoRepository(SQLAlchemyRepository[Orcamento]):
    model = Orcamento
