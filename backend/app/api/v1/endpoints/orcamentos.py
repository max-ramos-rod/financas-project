from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import AccessContext, get_access_context
from app.core.pagination import PaginationMetaBuilder, PaginationParams
from app.core.responses import PagedResponse
from app.db.session import get_db
from app.schemas.orcamento import OrcamentoCreate, OrcamentoResponse, OrcamentoUpdate
from app.services.orcamento import OrcamentoService

router = APIRouter()
_service = OrcamentoService()


@router.get("", response_model=PagedResponse[OrcamentoResponse])
def listar_orcamentos(
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    orcamentos = _service.listar(db, access_ctx.effective_user.id, mes, ano)
    total = len(orcamentos)
    params = PaginationParams(page=1, page_size=max(total, 1))
    return PagedResponse(data=orcamentos, meta=PaginationMetaBuilder.build(total, params))


@router.get("/{orcamento_id}", response_model=OrcamentoResponse)
def buscar_orcamento(
    orcamento_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    orcamento = _service.buscar(db, orcamento_id, access_ctx.effective_user.id)
    if not orcamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado"
        )
    return orcamento


@router.post("", response_model=OrcamentoResponse, status_code=status.HTTP_201_CREATED)
def criar_orcamento(
    orcamento: OrcamentoCreate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    try:
        return _service.criar(db, orcamento, access_ctx.effective_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{orcamento_id}", response_model=OrcamentoResponse)
def atualizar_orcamento(
    orcamento_id: int,
    orcamento: OrcamentoUpdate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    try:
        orcamento_atualizado = _service.atualizar(
            db, orcamento_id, access_ctx.effective_user.id, orcamento
        )
        if not orcamento_atualizado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado"
            )
        return orcamento_atualizado
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{orcamento_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_orcamento(
    orcamento_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context),
):
    try:
        sucesso = _service.deletar(db, orcamento_id, access_ctx.effective_user.id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado"
            )
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
