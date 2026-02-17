from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.api.deps import AccessContext, get_access_context
from app.schemas.transacao import (
    TransacaoCreate,
    TransacaoUpdate,
    TransacaoResponse,
)

from app.crud import crud_transacao as crud

router = APIRouter()

@router.get("", response_model=List[TransacaoResponse])
def listar_transacoes(
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """
    Lista todas as transações do usuário.
    
    Inclui transações normais e dízimos gerados automaticamente.
    """
    transacoes = crud.get_transacoes(db, access_ctx.effective_user.id, skip, limit)
    return transacoes


@router.get("/{transacao_id}", response_model=TransacaoResponse)
def buscar_transacao(
    transacao_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """Busca uma transação específica"""
    transacao = crud.get_transacao(db, transacao_id, access_ctx.effective_user.id)
    
    if not transacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transação não encontrada"
        )
    
    return transacao


@router.post("", response_model=TransacaoResponse, status_code=status.HTTP_201_CREATED)
def criar_transacao(
    transacao: TransacaoCreate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """
    Cria uma nova transação.
    
    **Sistema de Dízimo Automático:**
    - Se `tem_dizimo=true` e `tipo=entrada`:
      - Cria a entrada normalmente
      - Cria automaticamente uma SAÍDA de dízimo
      - Ambas relacionadas via `transacao_dizimo_uuid`
      - Dízimo criado com `e_dizimo=true`
    
    **Exemplo:**
    ```json
    {
      "conta_id": 1,
      "categoria_id": 5,
      "descricao": "Salário Fevereiro",
      "valor": 5000.00,
      "tipo": "entrada",
      "data": "2024-02-06",
      "tem_dizimo": true,
      "percentual_dizimo": 10.0
    }
    ```
    
    **Resultado:**
    - Entrada: R$ 5.000 (id=1, uuid=abc-123)
    - Saída: R$ 500 (Dízimo, id=2, uuid=abc-123, e_dizimo=true)
    - Saldo: +R$ 4.500
    """
    try:
        nova_transacao = crud.criar_transacao(db, transacao, access_ctx.effective_user.id)
        return nova_transacao
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{transacao_id}", response_model=TransacaoResponse)
def atualizar_transacao(
    transacao_id: int,
    transacao: TransacaoUpdate,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """
    Atualiza uma transação existente.
    
    ⚠️ **Importante:**
    - Não é possível editar transações de dízimo diretamente (e_dizimo=true)
    - Para alterar o dízimo, edite a entrada original
    - Se a entrada tinha dízimo, o dízimo será atualizado automaticamente
    """
    try:
        transacao_atualizada = crud.atualizar_transacao(
            db, transacao_id, access_ctx.effective_user.id, transacao
        )
        
        if not transacao_atualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transação não encontrada"
            )
        
        return transacao_atualizada
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{transacao_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_transacao(
    transacao_id: int,
    db: Session = Depends(get_db),
    access_ctx: AccessContext = Depends(get_access_context)
):
    """
    Deleta uma transação.
    
    ⚠️ **Importante:**
    - Não é possível deletar transações de dízimo diretamente
    - Ao deletar uma entrada com dízimo, o dízimo é deletado automaticamente
    - O saldo da conta é recalculado
    """
    try:
        sucesso = crud.deletar_transacao(db, transacao_id, access_ctx.effective_user.id)
        
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transação não encontrada"
            )
        
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
