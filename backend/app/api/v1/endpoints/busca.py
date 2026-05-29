import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import AccessContext, get_access_context
from app.db.session import get_db
from app.models import Conta, TipoConta
from app.models.financeiro import Transacao

router = APIRouter()

_MAX_RESULTS = 10
_MIN_CHARS = 2
_MAX_CHARS = 100


def _sanitize(q: str) -> str:
    return re.sub(r"[%_\\]", lambda m: f"\\{m.group()}", q.strip())


@router.get("")
def buscar(
    q: str = Query(min_length=_MIN_CHARS, max_length=_MAX_CHARS),
    db: Session = Depends(get_db),
    ctx: AccessContext = Depends(get_access_context),
):
    if len(q.strip()) < _MIN_CHARS:
        raise HTTPException(400, "Termo de busca muito curto (mínimo 2 caracteres).")

    uid = ctx.effective_user.id
    termo = f"%{_sanitize(q)}%"

    transacoes = (
        db.query(Transacao)
        .filter(Transacao.user_id == uid, Transacao.descricao.ilike(termo))
        .order_by(Transacao.data.desc())
        .limit(_MAX_RESULTS)
        .all()
    )

    contas = (
        db.query(Conta)
        .filter(Conta.user_id == uid, Conta.ativa.is_(True), Conta.nome.ilike(termo))
        .order_by(Conta.nome)
        .limit(_MAX_RESULTS)
        .all()
    )

    return {
        "query": q,
        "transacoes": [
            {
                "id": t.id,
                "descricao": t.descricao,
                "valor": t.valor,
                "tipo": t.tipo.value,
                "data": t.data.isoformat() if t.data else None,
                "status_liquidacao": t.status_liquidacao.value if t.status_liquidacao else None,
                "conta_id": t.conta_id,
            }
            for t in transacoes
        ],
        "contas": [
            {
                "id": c.id,
                "nome": c.nome,
                "tipo": c.tipo.value,
                "saldo": c.saldo,
            }
            for c in contas
        ],
    }
