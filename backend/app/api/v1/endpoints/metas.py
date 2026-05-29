from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import AccessContext, get_access_context
from app.core.pagination import PaginationMetaBuilder, PaginationParams
from app.core.responses import PagedResponse
from app.crud import crud_meta as crud
from app.db.session import get_db
from app.schemas.meta import MetaCreate, MetaResponse, MetaUpdate
from app.services.meta import MetaService

router = APIRouter()
_service = MetaService()


@router.get("", response_model=PagedResponse[MetaResponse])
def listar_metas(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    all_metas = crud.get_metas(db, access_ctx.effective_user.id)
    total = len(all_metas)
    params = PaginationParams(page=page, page_size=page_size)
    skip = (page - 1) * page_size
    return PagedResponse(
        data=all_metas[skip : skip + page_size],
        meta=PaginationMetaBuilder.build(total, params),
    )


@router.get("/{meta_id}", response_model=MetaResponse)
def buscar_meta(
    meta_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    meta = crud.get_meta(db, meta_id, access_ctx.effective_user.id)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meta não encontrada")
    return meta


@router.post("", response_model=MetaResponse, status_code=status.HTTP_201_CREATED)
def criar_meta(
    meta: MetaCreate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    try:
        return _service.criar(db, meta, access_ctx.effective_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{meta_id}", response_model=MetaResponse)
def atualizar_meta(
    meta_id: int,
    meta: MetaUpdate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    try:
        meta_atualizada = _service.atualizar(db, meta_id, access_ctx.effective_user.id, meta)
        if not meta_atualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Meta não encontrada"
            )
        return meta_atualizada
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{meta_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_meta(
    meta_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    try:
        sucesso = _service.deletar(db, meta_id, access_ctx.effective_user.id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Meta não encontrada"
            )
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
