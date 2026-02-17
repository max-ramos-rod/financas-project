from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.api.deps import AccessContext, get_access_context
from app.schemas.orcamento import (
    OrcamentoCreate,
    OrcamentoUpdate,
    OrcamentoResponse,
)

from app.crud import crud_orcamento as crud

router = APIRouter()

@router.get("", response_model=List[OrcamentoResponse])
def listar_orcamentos(
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Lista todos os orçamentos do usuário"""
    orcamentos = crud.get_orcamentos(db, access_ctx.effective_user.id, mes, ano)
    return orcamentos


@router.get("/{orcamento_id}", response_model=OrcamentoResponse)
def buscar_orcamento(
    orcamento_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Busca um orçamento específico"""
    orcamento = crud.get_orcamento(db, orcamento_id, access_ctx.effective_user.id)
    
    if not orcamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orçamento não encontrado"
        )
    
    return orcamento


@router.post("", response_model=OrcamentoResponse, status_code=status.HTTP_201_CREATED)
def criar_orcamento(
    orcamento: OrcamentoCreate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Cria um novo orçamento"""
    try:
        novo_orcamento = crud.criar_orcamento(db, orcamento, access_ctx.effective_user.id)
        return novo_orcamento
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{orcamento_id}", response_model=OrcamentoResponse)
def atualizar_orcamento(
    orcamento_id: int,
    orcamento: OrcamentoUpdate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Atualiza um orçamento existente"""
    try:
        orcamento_atualizado = crud.atualizar_orcamento(
            db, orcamento_id, access_ctx.effective_user.id, orcamento
        )
        
        if not orcamento_atualizado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Orçamento não encontrado"
            )
        
        return orcamento_atualizado
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{orcamento_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_orcamento(
    orcamento_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Deleta um orçamento"""
    try:
        sucesso = crud.deletar_orcamento(db, orcamento_id, access_ctx.effective_user.id)
        
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Orçamento não encontrado"
            )
        
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
