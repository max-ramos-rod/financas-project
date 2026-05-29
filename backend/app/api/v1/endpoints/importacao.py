from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import AccessContext, get_access_context
from app.crud.crud_transacao import criar_transacao
from app.db.session import get_db
from app.models import Conta, StatusLiquidacao, TipoConta, TipoTransacao
from app.schemas.importacao import ImportacaoErro, ImportacaoResult
from app.schemas.transacao import TransacaoCreate
from app.services.importacao.detector import detectar_e_parsear

router = APIRouter()

MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB


def _status_para_conta(conta: Conta) -> StatusLiquidacao:
    if conta.tipo == TipoConta.CARTAO_CREDITO:
        return StatusLiquidacao.PREVISTO
    return StatusLiquidacao.LIQUIDADO


@router.post("/upload", response_model=ImportacaoResult, status_code=status.HTTP_200_OK)
async def importar_transacoes(
    conta_id: int = Form(...),
    file: UploadFile = File(...),
    ctx: AccessContext = Depends(get_access_context),
    db: Session = Depends(get_db),
):
    conta = db.query(Conta).filter(
        Conta.id == conta_id,
        Conta.user_id == ctx.effective_user.id,
    ).first()
    if not conta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo vazio.")
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo muito grande. Limite: 5 MB.")

    try:
        formato, transacoes = detectar_e_parsear(content, file.filename or "")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Não foi possível ler o arquivo: {exc}",
        )

    if not transacoes:
        return ImportacaoResult(
            formato_detectado=formato,
            total_no_arquivo=0,
            importadas=0,
            duplicatas=[],
            erros=[],
        )

    importadas = 0
    erros: list[ImportacaoErro] = []
    status_liq = _status_para_conta(conta)

    for i, t in enumerate(transacoes):
        try:
            tc = TransacaoCreate(
                conta_id=conta_id,
                descricao=t.descricao,
                valor=t.valor,
                tipo=TipoTransacao(t.tipo),
                data=t.data,
                status_liquidacao=status_liq,
                data_liquidacao=t.data if status_liq == StatusLiquidacao.LIQUIDADO else None,
                tem_dizimo=False,
                parcelado=False,
                fixa=False,
                recorrente=False,
                observacoes=t.observacoes,
            )
            criar_transacao(db, tc, ctx.effective_user.id)
            importadas += 1
        except Exception as exc:
            try:
                db.rollback()
            except Exception:
                pass
            erros.append(ImportacaoErro(
                indice=i,
                descricao=t.descricao,
                motivo=str(exc),
            ))

    return ImportacaoResult(
        formato_detectado=formato,
        total_no_arquivo=len(transacoes),
        importadas=importadas,
        duplicatas=[],
        erros=erros,
    )
