from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.api.deps import AccessContext, get_access_context
from app.schemas.meta import (
    MetaCreate,
    MetaUpdate,
    MetaResponse,
)

from app.crud import crud_meta as crud

router = APIRouter()

@router.get("", response_model=List[MetaResponse])
def listar_metas(
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Lista todas as metas do usuário"""
    metas = crud.get_metas(db, access_ctx.effective_user.id)
    return metas[skip:skip + limit]


@router.get("/{meta_id}", response_model=MetaResponse)
def buscar_meta(
    meta_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Busca uma meta específica"""
    meta = crud.get_meta(db, meta_id, access_ctx.effective_user.id)
    
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meta não encontrada"
        )
    
    return meta


@router.post("", response_model=MetaResponse, status_code=status.HTTP_201_CREATED)
def criar_meta(
    meta: MetaCreate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Cria uma nova meta"""
    try:
        nova_meta = crud.criar_meta(db, meta, access_ctx.effective_user.id)
        return nova_meta
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{meta_id}", response_model=MetaResponse)
def atualizar_meta(
    meta_id: int,
    meta: MetaUpdate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Atualiza uma meta existente"""
    try:
        meta_atualizada = crud.atualizar_meta(
            db, meta_id, access_ctx.effective_user.id, meta
        )
        
        if not meta_atualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meta não encontrada"
            )
        
        return meta_atualizada
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{meta_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_meta(
    meta_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Deleta uma meta"""
    try:
        sucesso = crud.deletar_meta(db, meta_id, access_ctx.effective_user.id)
        
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meta não encontrada"
            )
        
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
