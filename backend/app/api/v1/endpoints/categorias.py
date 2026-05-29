from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import AccessContext, get_access_context
from app.core.pagination import PaginationMetaBuilder, PaginationParams
from app.core.responses import PagedResponse
from app.db.session import get_db
from app.schemas.categoria import CategoriaCreate, CategoriaResponse, CategoriaUpdate
from app.services.categoria import CategoriaService

router = APIRouter()
_service = CategoriaService()


@router.get("", response_model=PagedResponse[CategoriaResponse])
def listar_categorias(
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    categorias = _service.listar(db, access_ctx.effective_user.id)
    total = len(categorias)
    params = PaginationParams(page=1, page_size=max(total, 1))
    return PagedResponse(data=categorias, meta=PaginationMetaBuilder.build(total, params))


@router.post("", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
def criar_categoria(
    categoria: CategoriaCreate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    try:
        return _service.criar(db, categoria, access_ctx.effective_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{categoria_id}", response_model=CategoriaResponse)
def atualizar_categoria(
    categoria_id: int,
    categoria: CategoriaUpdate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    try:
        atualizada = _service.atualizar(db, categoria_id, access_ctx.effective_user.id, categoria)
        if not atualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Categoria nao encontrada"
            )
        return atualizada
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    try:
        sucesso = _service.deletar(db, categoria_id, access_ctx.effective_user.id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Categoria nao encontrada"
            )
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
