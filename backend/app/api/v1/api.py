from fastapi import APIRouter
from app.api.v1.endpoints import auth, categorias, metas, orcamentos, transacoes, contas, delegacoes

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(categorias.router, prefix="/categorias", tags=["categorias"])
api_router.include_router(contas.router, prefix="/contas", tags=["contas"])
api_router.include_router(metas.router, prefix="/metas", tags=["metas"])
api_router.include_router(orcamentos.router, prefix="/orcamentos", tags=["orcamentos"])
api_router.include_router(transacoes.router, prefix="/transacoes", tags=["transacoes"])
api_router.include_router(delegacoes.router, prefix="/delegacoes", tags=["delegacoes"])
