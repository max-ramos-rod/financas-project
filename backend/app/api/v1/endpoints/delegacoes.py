from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.crud.crud_delegacao import (
    accept_delegacao,
    get_delegacao_by_id,
    get_delegacao_by_token,
    invite_delegacao,
    is_invite_expired,
    list_delegacoes_received,
    list_delegacoes_sent,
    revoke_delegacao,
)
from app.crud.crud_user import create_user, get_user_by_email
from app.db.session import get_db
from app.models import DelegacaoStatus, User, UserRole
from app.schemas.delegacao import (
    DelegacaoConfirmRequest,
    DelegacaoContextOption,
    DelegacaoInviteRequest,
    DelegacaoInviteResponse,
    DelegacaoInviteTokenInfo,
    DelegacaoResponse,
)
from app.services.email import send_invitation_email

router = APIRouter()


@router.post("/invite", response_model=DelegacaoInviteResponse, status_code=status.HTTP_201_CREATED)
def convidar_delegacao(
    payload: DelegacaoInviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invited_email = payload.email.strip().lower()
    if invited_email == current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nao e possivel criar delegacao para o proprio usuario",
        )

    try:
        delegacao, has_account = invite_delegacao(
            db=db,
            owner_user_id=current_user.id,
            invited_email=invited_email,
            can_write=payload.can_write,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    email_sent = False
    if delegacao.invite_token:
        invite_link = f"{settings.FRONTEND_URL}/convites/confirmar?token={delegacao.invite_token}"
        try:
            send_invitation_email(
                to_email=invited_email,
                owner_nome=current_user.nome,
                invite_link=invite_link,
            )
            email_sent = True
        except RuntimeError:
            email_sent = False

    return DelegacaoInviteResponse(
        delegacao=delegacao,
        has_account=has_account,
        email_sent=email_sent,
    )


@router.get("/sent", response_model=List[DelegacaoResponse])
def listar_delegacoes_enviadas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_delegacoes_sent(db, current_user.id)


@router.get("/received", response_model=List[DelegacaoResponse])
def listar_delegacoes_recebidas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_delegacoes_received(db, current_user.id)


@router.post("/{delegacao_id}/accept", response_model=DelegacaoResponse)
def aceitar_delegacao(
    delegacao_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delegacao = get_delegacao_by_id(db, delegacao_id)
    if not delegacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delegacao nao encontrada")
    if delegacao.delegate_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissao para aceitar")

    try:
        return accept_delegacao(db, delegacao)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{delegacao_id}/revoke", response_model=DelegacaoResponse)
def revogar_delegacao(
    delegacao_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delegacao = get_delegacao_by_id(db, delegacao_id)
    if not delegacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delegacao nao encontrada")

    if current_user.id not in (delegacao.owner_user_id, delegacao.delegate_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissao para revogar")

    if delegacao.status == DelegacaoStatus.REVOKED:
        return delegacao

    return revoke_delegacao(db, delegacao)


@router.get("/act-as-options", response_model=List[DelegacaoContextOption])
def listar_contextos_disponiveis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    options: List[DelegacaoContextOption] = [
        DelegacaoContextOption(
            user_id=current_user.id,
            nome=current_user.nome,
            email=current_user.email,
            can_write=True,
            is_owner=True,
        )
    ]

    delegacoes_ativas = [
        item for item in list_delegacoes_received(db, current_user.id)
        if item.status == DelegacaoStatus.ACTIVE
    ]
    for item in delegacoes_ativas:
        options.append(
            DelegacaoContextOption(
                user_id=item.owner.id,
                nome=item.owner.nome,
                email=item.owner.email,
                can_write=item.can_write,
                is_owner=False,
            )
        )
    return options


@router.get("/invite-info/{token}", response_model=DelegacaoInviteTokenInfo)
def convite_por_token(token: str, db: Session = Depends(get_db)):
    delegacao = get_delegacao_by_token(db, token)
    if not delegacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convite nao encontrado")

    return DelegacaoInviteTokenInfo(
        invited_email=delegacao.invited_email,
        owner_nome=delegacao.owner.nome,
        owner_email=delegacao.owner.email,
        has_account=delegacao.delegate_user_id is not None,
        expired=is_invite_expired(delegacao),
    )


@router.post("/confirm/{token}", response_model=DelegacaoResponse)
def confirmar_convite(
    token: str,
    payload: DelegacaoConfirmRequest,
    db: Session = Depends(get_db),
):
    delegacao = get_delegacao_by_token(db, token)
    if not delegacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convite nao encontrado")

    if delegacao.status != DelegacaoStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Convite nao esta pendente")

    if is_invite_expired(delegacao):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Convite expirado")

    if not delegacao.delegate_user_id:
        existing_user = get_user_by_email(db, delegacao.invited_email)
        if existing_user:
            delegacao.delegate_user_id = existing_user.id
            db.add(delegacao)
            db.commit()
            db.refresh(delegacao)
        else:
            if not payload.nome or not payload.password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nome e senha sao obrigatorios para concluir o cadastro",
                )
            new_user = create_user(
                db=db,
                email=delegacao.invited_email,
                password=payload.password,
                nome=payload.nome,
                role=UserRole.USER,
            )
            delegacao.delegate_user_id = new_user.id
            db.add(delegacao)
            db.commit()
            db.refresh(delegacao)

    try:
        return accept_delegacao(db, delegacao)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
