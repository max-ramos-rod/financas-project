from app.core.repositories import SQLAlchemyRepository
from app.models import Conta


class ContaRepository(SQLAlchemyRepository[Conta]):
    model = Conta
