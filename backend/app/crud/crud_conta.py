from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional

from app.models import Conta
from app.models.financeiro import TipoConta
from app.schemas.conta import ContaCreate, ContaUpdate


def get_contas(db: Session, user_id: int) -> List[Conta]:
    """Lista todas as contas do usuário"""
    return db.query(Conta).filter(Conta.user_id == user_id).all()


def get_conta(db: Session, conta_id: int, user_id: int) -> Optional[Conta]:
    """Busca uma conta específica"""
    return db.query(Conta).filter(
        and_(
            Conta.id == conta_id,
            Conta.user_id == user_id
        )
    ).first()


def criar_conta(db: Session, conta: ContaCreate, user_id: int) -> Conta:
    """Cria uma nova conta"""
    data = conta.model_dump()
    if data.get("tipo") == TipoConta.CARTAO_CREDITO:
        data["saldo"] = 0.0

    db_conta = Conta(
        user_id=user_id,
        **data
    )
    db.add(db_conta)
    db.commit()
    db.refresh(db_conta)
    return db_conta


def atualizar_conta(db: Session, conta_id: int, user_id: int, conta_update: ContaUpdate) -> Optional[Conta]:
    """Atualiza uma conta existente"""
    db_conta = get_conta(db, conta_id, user_id)
    if not db_conta:
        return None
    
    # Atualiza apenas os campos fornecidos
    update_data = conta_update.model_dump(exclude_unset=True)

    tipo_final = update_data.get("tipo", db_conta.tipo)
    if tipo_final != TipoConta.CARTAO_CREDITO:
        update_data["dia_fechamento"] = None
        update_data["dia_vencimento"] = None
        update_data["limite_credito"] = None
    else:
        if ("tipo" in update_data) or ("dia_fechamento" in update_data) or ("dia_vencimento" in update_data):
            dia_fechamento = update_data.get("dia_fechamento", db_conta.dia_fechamento)
            dia_vencimento = update_data.get("dia_vencimento", db_conta.dia_vencimento)
            if dia_fechamento is None or dia_vencimento is None:
                raise ValueError("Conta de cartao exige dia_fechamento e dia_vencimento.")
        # Cartao de credito nao usa saldo manual.
        update_data["saldo"] = 0.0

    for key, value in update_data.items():
        setattr(db_conta, key, value)
    
    db.add(db_conta)
    db.commit()
    db.refresh(db_conta)
    return db_conta


def deletar_conta(db: Session, conta_id: int, user_id: int) -> bool:
    """Deleta uma conta"""
    db_conta = get_conta(db, conta_id, user_id)
    if not db_conta:
        return False
    
    db.delete(db_conta)
    db.commit()
    return True
