from app.core.repositories import SQLAlchemyRepository
from app.models import Categoria


class CategoriaRepository(SQLAlchemyRepository[Categoria]):
    model = Categoria
