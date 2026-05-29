import uuid
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.contracts import ContaRepositoryProtocol
from app.domain.cartao_fatura import ResumoFatura, valor_efetivo_transacao
from app.models import Conta, StatusLiquidacao, TipoConta, TipoTransacao, Transacao
from app.repositories import ContaRepository
from app.schemas.conta import ContaCreate, ContaUpdate, PagarFaturaRequest


class ContaService:
    def __init__(self, repo: ContaRepositoryProtocol | None = None) -> None:
        self._repo: ContaRepositoryProtocol = repo if repo is not None else ContaRepository()

    def criar(self, db: Session, conta: ContaCreate, user_id: int) -> Conta:
        data = conta.model_dump()
        if data.get("tipo") == TipoConta.CARTAO_CREDITO:
            data["saldo"] = 0.0
        db_conta = Conta(user_id=user_id, **data)
        self._repo._save(db, db_conta)
        db.commit()
        db.refresh(db_conta)
        return db_conta

    def atualizar(
        self,
        db: Session,
        conta_id: int,
        user_id: int,
        conta_update: ContaUpdate,
    ) -> Optional[Conta]:
        db_conta = db.query(Conta).filter(Conta.id == conta_id, Conta.user_id == user_id).first()
        if not db_conta:
            return None

        update_data = conta_update.model_dump(exclude_unset=True)
        tipo_final = update_data.get("tipo", db_conta.tipo)

        if tipo_final != TipoConta.CARTAO_CREDITO:
            update_data["dia_fechamento"] = None
            update_data["dia_vencimento"] = None
            update_data["limite_credito"] = None
        else:
            if ("tipo" in update_data) or ("dia_fechamento" in update_data) or ("dia_vencimento" in update_data):
                dia_fechamento = update_data.get("dia_fechamento", db_conta.dia_fechamento)
                dia_vencimento = update_data.get("dia_vencimento", db_conta.dia_vencimento)
                if dia_fechamento is None or dia_vencimento is None:
                    raise ValueError("Conta de cartao exige dia_fechamento e dia_vencimento.")
                if dia_fechamento == dia_vencimento:
                    raise ValueError("Dia de fechamento e dia de vencimento nao podem ser iguais.")
            update_data["saldo"] = 0.0

        for key, value in update_data.items():
            setattr(db_conta, key, value)

        self._repo._save(db, db_conta)
        db.commit()
        db.refresh(db_conta)
        return db_conta

    def deletar(self, db: Session, conta_id: int, user_id: int) -> bool:
        db_conta = db.query(Conta).filter(Conta.id == conta_id, Conta.user_id == user_id).first()
        if not db_conta:
            return False
        self._repo.delete(db, db_conta)
        db.commit()
        return True

    def pagar_fatura(
        self,
        db: Session,
        conta_id: int,
        user_id: int,
        payload: PagarFaturaRequest,
        resumo_fatura: ResumoFatura,
    ) -> None:
        conta_cartao = db.query(Conta).filter(Conta.id == conta_id, Conta.user_id == user_id).first()
        if not conta_cartao:
            raise ValueError("Conta nao encontrada")
        if conta_cartao.tipo != TipoConta.CARTAO_CREDITO:
            raise ValueError("Conta nao e cartao de credito")

        conta_pagamento = db.query(Conta).filter(
            Conta.id == payload.conta_pagamento_id,
            Conta.user_id == user_id,
        ).first()
        if not conta_pagamento:
            raise ValueError("Conta de pagamento nao encontrada")
        if conta_pagamento.id == conta_cartao.id:
            raise ValueError("Conta de pagamento deve ser diferente do cartao")
        if conta_pagamento.tipo == TipoConta.CARTAO_CREDITO:
            raise ValueError("Pagamento deve sair de conta nao cartao")

        transacoes = (
            db.query(Transacao)
            .filter(
                Transacao.user_id == user_id,
                Transacao.conta_id == conta_cartao.id,
                Transacao.tipo == TipoTransacao.SAIDA,
                Transacao.data >= resumo_fatura.periodo_inicio,
                Transacao.data <= resumo_fatura.periodo_fim,
                Transacao.status_liquidacao.in_([StatusLiquidacao.PREVISTO, StatusLiquidacao.ATRASADO]),
            )
            .order_by(Transacao.data.asc(), Transacao.id.asc())
            .all()
        )

        if not transacoes:
            raise ValueError("Nao ha itens em aberto nesta fatura")

        valor_total = sum(valor_efetivo_transacao(t) for t in transacoes)
        data_pagamento = payload.data_pagamento or date.today()
        periodo_inicio = resumo_fatura.periodo_inicio
        periodo_fim = resumo_fatura.periodo_fim
        descricao_pagamento = payload.descricao or (
            f"FTPG {conta_cartao.nome} ({periodo_inicio.strftime('%d/%m')} a {periodo_fim.strftime('%d/%m')})"
        )

        conta_pagamento.saldo -= valor_total
        pagamento = Transacao(
            user_id=user_id,
            conta_id=conta_pagamento.id,
            categoria_id=None,
            descricao=descricao_pagamento,
            valor=valor_total,
            tipo=TipoTransacao.TRANSFERENCIA,
            data=data_pagamento,
            data_vencimento=data_pagamento,
            data_liquidacao=data_pagamento,
            status_liquidacao=StatusLiquidacao.LIQUIDADO,
            fixa=False,
            recorrente=False,
            confirmada=True,
            transacao_uuid=str(uuid.uuid4()),
            tem_dizimo=False,
            percentual_dizimo=0,
            e_dizimo=False,
            parcelado=False,
            e_emprestimo=False,
            valor_multa=0,
            valor_juros=0,
            valor_desconto=0,
            tags="pagamento_fatura",
        )
        db.add(pagamento)

        for item in transacoes:
            item.status_liquidacao = StatusLiquidacao.LIQUIDADO
            item.data_liquidacao = data_pagamento
            db.add(item)

        db.add(conta_pagamento)
        db.commit()
