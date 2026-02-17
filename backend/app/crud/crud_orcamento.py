from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional

from app.models import Orcamento
from app.schemas.orcamento import OrcamentoCreate, OrcamentoUpdate


def get_orcamentos(db: Session, user_id: int, mes: Optional[int] = None, ano: Optional[int] = None) -> List[Orcamento]:
    """Lista todos os orçamentos do usuário"""
    query = db.query(Orcamento).filter(Orcamento.user_id == user_id)
    
    if mes:
        query = query.filter(Orcamento.mes == mes)
    if ano:
        query = query.filter(Orcamento.ano == ano)
    
    return query.all()


def get_orcamento(db: Session, orcamento_id: int, user_id: int) -> Optional[Orcamento]:
    """Busca um orçamento específico"""
    return db.query(Orcamento).filter(
        and_(
            Orcamento.id == orcamento_id,
            Orcamento.user_id == user_id
        )
    ).first()


def get_orcamento_categoria_mes(db: Session, categoria_id: int, mes: int, ano: int, user_id: int) -> Optional[Orcamento]:
    """Busca orçamento por categoria, mês e ano"""
    return db.query(Orcamento).filter(
        and_(
            Orcamento.categoria_id == categoria_id,
            Orcamento.mes == mes,
            Orcamento.ano == ano,
            Orcamento.user_id == user_id
        )
    ).first()


def criar_orcamento(db: Session, orcamento: OrcamentoCreate, user_id: int) -> Orcamento:
    """Cria um novo orçamento"""
    db_orcamento = Orcamento(
        user_id=user_id,
        **orcamento.model_dump()
    )
    db.add(db_orcamento)
    db.commit()
    db.refresh(db_orcamento)
    return db_orcamento


def atualizar_orcamento(db: Session, orcamento_id: int, user_id: int, orcamento_update: OrcamentoUpdate) -> Optional[Orcamento]:
    """Atualiza um orçamento existente"""
    db_orcamento = get_orcamento(db, orcamento_id, user_id)
    if not db_orcamento:
        return None
    
    # Atualiza apenas os campos fornecidos
    update_data = orcamento_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_orcamento, key, value)
    
    db.add(db_orcamento)
    db.commit()
    db.refresh(db_orcamento)
    return db_orcamento


def deletar_orcamento(db: Session, orcamento_id: int, user_id: int) -> bool:
    """Deleta um orçamento"""
    db_orcamento = get_orcamento(db, orcamento_id, user_id)
    if not db_orcamento:
        return False
    
    db.delete(db_orcamento)
    db.commit()
    return True