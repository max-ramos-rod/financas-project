from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.api.deps import AccessContext, get_access_context
from app.schemas.categoria import (
    CategoriaCreate,
    CategoriaUpdate,
    CategoriaResponse,
)

from app.crud import crud_categoria as crud

router = APIRouter()

@router.get("", response_model=List[CategoriaResponse])
def listar_categorias(
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """
    Lista categorias disponíveis para o usuário.
    
    Retorna:
    - Categorias padrão do sistema (user_id=NULL, padrao=true)
    - Categorias customizadas do usuário (user_id=current_user.id, padrao=false)
    """
    categorias = crud.get_categorias(db, access_ctx.effective_user.id)
    return categorias


@router.post("", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
def criar_categoria(
    categoria: CategoriaCreate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    try:
        return crud.criar_categoria(db, categoria, access_ctx.effective_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{categoria_id}", response_model=CategoriaResponse)
def atualizar_categoria(
    categoria_id: int,
    categoria: CategoriaUpdate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    try:
        atualizada = crud.atualizar_categoria(db, categoria_id, access_ctx.effective_user.id, categoria)
        if not atualizada:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria nao encontrada")
        return atualizada
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    try:
        sucesso = crud.deletar_categoria(db, categoria_id, access_ctx.effective_user.id)
        if not sucesso:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria nao encontrada")
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
