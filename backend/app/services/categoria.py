from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.contracts.categoria import CategoriaRepositoryProtocol
from app.models import Categoria, Transacao
from app.repositories.categoria import CategoriaRepository
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate


class CategoriaService:
    def __init__(self, repo: CategoriaRepositoryProtocol | None = None) -> None:
        self._repo: CategoriaRepositoryProtocol = repo if repo is not None else CategoriaRepository()

    def _nome_tipo_duplicado(
        self, db: Session, user_id: int, nome: str, tipo, ignorar_id: Optional[int] = None
    ) -> bool:
        query = db.query(Categoria).filter(
            Categoria.user_id == user_id,
            Categoria.tipo == tipo,
            func.lower(Categoria.nome) == nome.lower(),
        )
        if ignorar_id is not None:
            query = query.filter(Categoria.id != ignorar_id)
        return query.first() is not None

    def criar(self, db: Session, categoria: CategoriaCreate, user_id: int) -> Categoria:
        if self._nome_tipo_duplicado(db, user_id, categoria.nome, categoria.tipo):
            raise ValueError("Ja existe categoria com este nome para este tipo.")
        db_categoria = Categoria(
            user_id=user_id,
            nome=categoria.nome,
            icone=categoria.icone,
            cor=categoria.cor,
            tipo=categoria.tipo,
            padrao=False,
        )
        self._repo._save(db, db_categoria)
        db.commit()
        db.refresh(db_categoria)
        return db_categoria

    def atualizar(
        self, db: Session, categoria_id: int, user_id: int, categoria_update: CategoriaUpdate
    ) -> Optional[Categoria]:
        categoria = db.query(Categoria).filter(
            Categoria.id == categoria_id, Categoria.user_id == user_id
        ).first()
        if not categoria:
            return None
        if categoria.padrao:
            raise ValueError("Categorias padrao nao podem ser editadas.")

        update_data = categoria_update.model_dump(exclude_unset=True)
        nome_final = update_data.get("nome", categoria.nome)
        tipo_final = update_data.get("tipo", categoria.tipo)
        if self._nome_tipo_duplicado(db, user_id, nome_final, tipo_final, ignorar_id=categoria_id):
            raise ValueError("Ja existe categoria com este nome para este tipo.")

        for key, value in update_data.items():
            setattr(categoria, key, value)
        self._repo._save(db, categoria)
        db.commit()
        db.refresh(categoria)
        return categoria

    def deletar(self, db: Session, categoria_id: int, user_id: int) -> bool:
        categoria = db.query(Categoria).filter(
            Categoria.id == categoria_id, Categoria.user_id == user_id
        ).first()
        if not categoria:
            return False
        if categoria.padrao:
            raise ValueError("Categorias padrao nao podem ser excluidas.")
        em_uso = db.query(Transacao).filter(
            and_(Transacao.user_id == user_id, Transacao.categoria_id == categoria_id)
        ).first()
        if em_uso:
            raise ValueError("Categoria em uso por transacoes. Edite as transacoes antes de excluir.")
        self._repo.delete(db, categoria)
        db.commit()
        return True
