from app.core.repositories import SQLAlchemyRepository
from app.models import Meta


class MetaRepository(SQLAlchemyRepository[Meta]):
    model = Meta
