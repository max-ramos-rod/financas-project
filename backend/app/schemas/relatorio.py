from pydantic import BaseModel


class DRECategoriaResumo(BaseModel):
    categoria_id: int | None = None
    categoria_nome: str
    valor: float


class DREMensalResponse(BaseModel):
    mes: int
    ano: int
    entradas_liquidadas: float
    entradas_previstas: float
    entradas_total: float
    saidas_liquidadas: float
    saidas_previstas: float
    saidas_total: float
    resultado_liquidado: float
    resultado_previsto: float
    resultado_total: float
    entradas_por_categoria: list[DRECategoriaResumo]
    saidas_por_categoria: list[DRECategoriaResumo]
