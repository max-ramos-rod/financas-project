from typing import Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import Base

ModelT = TypeVar("ModelT", bound=Base)
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)


class CRUDBase(Generic[ModelT, CreateSchemaT, UpdateSchemaT]):
    def __init__(self, model: Type[ModelT]):
        self.model = model

    def get(self, db: Session, id: int, user_id: int) -> Optional[ModelT]:
        return db.query(self.model).filter(
            self.model.id == id,
            self.model.user_id == user_id,
        ).first()

    def get_multi(self, db: Session, user_id: int) -> List[ModelT]:
        return db.query(self.model).filter(self.model.user_id == user_id).all()

    def create(self, db: Session, obj_in: CreateSchemaT, user_id: int) -> ModelT:
        db_obj = self.model(user_id=user_id, **obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: ModelT, obj_in: UpdateSchemaT) -> ModelT:
        for key, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, key, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, id: int, user_id: int) -> bool:
        obj = self.get(db, id, user_id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True
