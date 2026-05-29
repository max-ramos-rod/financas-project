from datetime import date
from calendar import monthrange
import uuid
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.domain.cartao_fatura import valor_efetivo_transacao
from app.domain.transacao import (
    impacto_no_saldo,
    normalizar_atraso,
    obter_categoria_dizimo,
    recalcular_meta,
    recalcular_orcamento_mes,
)
from app.models import Conta, Meta, Orcamento, StatusLiquidacao, TipoConta, TipoTransacao, Transacao
from app.schemas.transacao import TransacaoCreate, TransacaoUpdate


def _add_months(base_date: date, months: int) -> date:
    month_index = (base_date.month - 1) + months
    year = base_date.year + (month_index // 12)
    month = (month_index % 12) + 1
    day = min(base_date.day, monthrange(year, month)[1])
    return date(year, month, day)


def get_transacoes(
    db: Session,
    user_id: int,
    tipo: Optional[TipoTransacao] = None,
    status_liquidacao: Optional[StatusLiquidacao] = None,
    fixa: Optional[bool] = None,
    conta_id: Optional[int] = None,
    categoria_id: Optional[int] = None,
    sem_categoria: bool = False,
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    busca: Optional[str] = None,
    valor_modo: Optional[str] = None,
    valor_ref: Optional[float] = None,
    orcamento: Optional[str] = None,
) -> tuple[List[Transacao], int]:
    query = db.query(Transacao).filter(Transacao.user_id == user_id)

    if tipo:
        query = query.filter(Transacao.tipo == tipo)

    if status_liquidacao:
        query = query.filter(Transacao.status_liquidacao == status_liquidacao)

    if fixa is not None:
        query = query.filter(Transacao.fixa == fixa)

    if conta_id is not None:
        query = query.filter(Transacao.conta_id == conta_id)

    if sem_categoria:
        query = query.filter(Transacao.categoria_id.is_(None))
    elif categoria_id is not None:
        query = query.filter(Transacao.categoria_id == categoria_id)

    if mes is not None and ano is not None:
        inicio = date(ano, mes, 1)
        fim = date(ano, mes, monthrange(ano, mes)[1])
        query = query.filter(Transacao.data >= inicio, Transacao.data <= fim)
    elif ano is not None:
        inicio = date(ano, 1, 1)
        fim = date(ano, 12, 31)
        query = query.filter(Transacao.data >= inicio, Transacao.data <= fim)

    if busca:
        query = query.filter(Transacao.descricao.ilike(f"%{busca}%"))

    transacoes = query.order_by(Transacao.data.desc(), Transacao.id.desc()).all()

    for transacao in transacoes:
        normalizar_atraso(transacao)

    if valor_modo and valor_ref is not None:
        if valor_modo == "igual":
            transacoes = [t for t in transacoes if abs(valor_efetivo_transacao(t) - valor_ref) < 0.005]
        elif valor_modo == "gte":
            transacoes = [t for t in transacoes if valor_efetivo_transacao(t) >= valor_ref]
        elif valor_modo == "lte":
            transacoes = [t for t in transacoes if valor_efetivo_transacao(t) <= valor_ref]

    if orcamento in {"fora", "dentro"}:
        hoje = date.today()
        mes_ref = mes or hoje.month
        ano_ref = ano or hoje.year

        inicio = date(ano_ref, mes_ref, 1)
        fim = date(ano_ref, mes_ref, monthrange(ano_ref, mes_ref)[1])

        transacoes_mes = db.query(Transacao).filter(
            Transacao.user_id == user_id,
            Transacao.tipo == TipoTransacao.SAIDA,
            Transacao.data >= inicio,
            Transacao.data <= fim,
            Transacao.status_liquidacao != StatusLiquidacao.CANCELADO,
        ).all()

        gastos_por_categoria: dict[int, float] = {}
        for t in transacoes_mes:
            if t.categoria_id is None:
                continue
            gastos_por_categoria[t.categoria_id] = gastos_por_categoria.get(t.categoria_id, 0.0) + valor_efetivo_transacao(t)

        orcamentos_mes = db.query(Orcamento).filter(
            Orcamento.user_id == user_id,
            Orcamento.mes == mes_ref,
            Orcamento.ano == ano_ref,
        ).all()
        orcado_por_categoria: dict[int, float] = {}
        for o in orcamentos_mes:
            orcado_por_categoria[o.categoria_id] = orcado_por_categoria.get(o.categoria_id, 0.0) + float(o.valor_planejado or 0.0)

        def _fora_orcamento(t: Transacao) -> bool:
            if t.tipo != TipoTransacao.SAIDA:
                return False
            if t.categoria_id is None:
                return True
            orcado = orcado_por_categoria.get(t.categoria_id)
            if orcado is None:
                return True
            gasto = gastos_por_categoria.get(t.categoria_id, 0.0)
            return gasto > orcado

        if orcamento == "fora":
            transacoes = [t for t in transacoes if _fora_orcamento(t)]
        else:
            transacoes = [t for t in transacoes if t.tipo == TipoTransacao.SAIDA and not _fora_orcamento(t)]

    return transacoes, len(transacoes)


def get_transacao(db: Session, transacao_id: int, user_id: int) -> Optional[Transacao]:
    transacao = db.query(Transacao).filter(
        and_(
            Transacao.id == transacao_id,
            Transacao.user_id == user_id,
        )
    ).first()

    if transacao:
        normalizar_atraso(transacao)

    return transacao


def criar_transacao(
    db: Session,
    transacao: TransacaoCreate,
    user_id: int,
) -> Transacao:
    conta = db.query(Conta).filter(
        and_(
            Conta.id == transacao.conta_id,
            Conta.user_id == user_id,
        )
    ).first()

    if not conta:
        raise ValueError("Conta nao encontrada ou nao pertence ao usuario")

    if conta.tipo == TipoConta.CARTAO_CREDITO and transacao.tipo == TipoTransacao.SAIDA:
        transacao.status_liquidacao = StatusLiquidacao.PREVISTO
        transacao.data_liquidacao = None

    if transacao.status_liquidacao == StatusLiquidacao.LIQUIDADO and not transacao.data_liquidacao:
        transacao.data_liquidacao = transacao.data

    is_parcelado = bool(transacao.parcelado or (transacao.total_parcelas and transacao.total_parcelas > 1))

    if is_parcelado and (not transacao.total_parcelas or transacao.total_parcelas < 2):
        raise ValueError("Informe a quantidade de parcelas (minimo 2).")

    if is_parcelado and transacao.recorrente:
        raise ValueError("Uma transacao nao pode ser parcelada e recorrente ao mesmo tempo.")

    if is_parcelado and transacao.total_parcelas and transacao.total_parcelas > 1:
        if transacao.tem_dizimo and transacao.tipo == TipoTransacao.ENTRADA:
            raise ValueError("Parcelamento com dizimo automatico nao e suportado.")

        grupo_uuid = str(uuid.uuid4())
        data_vencimento_base = transacao.data_vencimento or transacao.data
        transacoes_criadas: List[Transacao] = []
        metas_afetadas = set()
        orcamentos_afetados = set()

        for index in range(1, transacao.total_parcelas + 1):
            parcela_data = _add_months(transacao.data, index - 1)
            parcela_vencimento = _add_months(data_vencimento_base, index - 1)
            is_primeira = index == 1
            status_parcela = transacao.status_liquidacao if is_primeira else StatusLiquidacao.PREVISTO

            parcela = Transacao(
                user_id=user_id,
                transacao_uuid=str(uuid.uuid4()),
                conta_id=transacao.conta_id,
                categoria_id=transacao.categoria_id,
                descricao=transacao.descricao,
                valor=transacao.valor,
                tipo=transacao.tipo,
                data=parcela_data,
                data_vencimento=parcela_vencimento,
                data_liquidacao=transacao.data_liquidacao if (is_primeira and status_parcela == StatusLiquidacao.LIQUIDADO) else None,
                status_liquidacao=status_parcela,
                fixa=transacao.fixa,
                recorrente=transacao.recorrente,
                confirmada=transacao.confirmada,
                tem_dizimo=False,
                percentual_dizimo=transacao.percentual_dizimo,
                parcelado=True,
                parcela_atual=index,
                total_parcelas=transacao.total_parcelas,
                grupo_parcelamento_uuid=grupo_uuid,
                e_emprestimo=transacao.e_emprestimo,
                pessoa_emprestimo=transacao.pessoa_emprestimo,
                observacoes=transacao.observacoes,
                tags=transacao.tags,
                valor_multa=transacao.valor_multa if is_primeira else 0.0,
                valor_juros=transacao.valor_juros if is_primeira else 0.0,
                valor_desconto=transacao.valor_desconto if is_primeira else 0.0,
                meta_id=transacao.meta_id,
            )
            db.add(parcela)
            conta.saldo += impacto_no_saldo(parcela)
            transacoes_criadas.append(parcela)
            if parcela.meta_id:
                metas_afetadas.add(parcela.meta_id)
            if parcela.categoria_id and parcela.tipo == TipoTransacao.SAIDA:
                orcamentos_afetados.add((parcela.categoria_id, parcela.data.month, parcela.data.year))

        db.flush()
        for meta_id in metas_afetadas:
            recalcular_meta(db, user_id, meta_id)
        for categoria_id, mes, ano in orcamentos_afetados:
            recalcular_orcamento_mes(db, user_id, categoria_id, mes, ano)
        db.commit()
        db.refresh(transacoes_criadas[0])
        return transacoes_criadas[0]

    db_transacao = Transacao(
        user_id=user_id,
        transacao_uuid=str(uuid.uuid4()),
        **transacao.model_dump(exclude={"tem_dizimo", "percentual_dizimo", "total_parcelas", "pessoa_emprestimo"}),
    )

    if is_parcelado and transacao.total_parcelas:
        db_transacao.grupo_parcelamento_uuid = str(uuid.uuid4())
        db_transacao.parcelado = True
        db_transacao.parcela_atual = 1
        db_transacao.total_parcelas = transacao.total_parcelas

    if transacao.e_emprestimo and transacao.pessoa_emprestimo:
        db_transacao.pessoa_emprestimo = transacao.pessoa_emprestimo

    dizimo_criado = None

    if transacao.tem_dizimo and transacao.tipo == TipoTransacao.ENTRADA:
        dizimo_relacionamento_uuid = str(uuid.uuid4())
        db_transacao.tem_dizimo = True
        db_transacao.percentual_dizimo = transacao.percentual_dizimo
        db_transacao.transacao_dizimo_uuid = dizimo_relacionamento_uuid

        db.add(db_transacao)
        db.flush()

        valor_dizimo = db_transacao.valor * (transacao.percentual_dizimo / 100)
        categoria_dizimo = obter_categoria_dizimo(db, user_id)

        dizimo_criado = Transacao(
            user_id=user_id,
            transacao_uuid=str(uuid.uuid4()),
            conta_id=transacao.conta_id,
            categoria_id=categoria_dizimo.id,
            descricao=f"Dizimo de {db_transacao.descricao}",
            valor=valor_dizimo,
            tipo=TipoTransacao.SAIDA,
            data=db_transacao.data,
            data_vencimento=db_transacao.data_vencimento or db_transacao.data,
            status_liquidacao=StatusLiquidacao.PREVISTO,
            fixa=True,
            recorrente=False,
            confirmada=False,
            tem_dizimo=False,
            e_dizimo=True,
            entrada_origem_id=db_transacao.id,
            transacao_dizimo_uuid=dizimo_relacionamento_uuid,
        )
        db.add(dizimo_criado)
    else:
        db.add(db_transacao)

    conta.saldo += impacto_no_saldo(db_transacao)
    if dizimo_criado:
        conta.saldo += impacto_no_saldo(dizimo_criado)

    db.flush()
    if db_transacao.meta_id:
        recalcular_meta(db, user_id, db_transacao.meta_id)

    orcamentos_afetados = set()
    if db_transacao.categoria_id and db_transacao.tipo == TipoTransacao.SAIDA:
        orcamentos_afetados.add((db_transacao.categoria_id, db_transacao.data.month, db_transacao.data.year))
    if dizimo_criado and dizimo_criado.categoria_id and dizimo_criado.tipo == TipoTransacao.SAIDA:
        orcamentos_afetados.add((dizimo_criado.categoria_id, dizimo_criado.data.month, dizimo_criado.data.year))
    for categoria_id, mes, ano in orcamentos_afetados:
        recalcular_orcamento_mes(db, user_id, categoria_id, mes, ano)

    db.commit()
    db.refresh(db_transacao)
    return db_transacao


def atualizar_transacao(
    db: Session,
    transacao_id: int,
    user_id: int,
    transacao_update: TransacaoUpdate,
) -> Optional[Transacao]:
    db_transacao = get_transacao(db, transacao_id, user_id)
    if not db_transacao:
        return None

    if db_transacao.e_dizimo:
        update_data = transacao_update.model_dump(exclude_unset=True)
        allowed_fields = {"status_liquidacao", "data_liquidacao"}
        invalid_fields = [field for field in update_data.keys() if field not in allowed_fields]
        if invalid_fields:
            raise ValueError("Transacoes de dizimo so permitem baixa (status/data_liquidacao).")
        if (
            update_data.get("status_liquidacao") == StatusLiquidacao.LIQUIDADO
            and not update_data.get("data_liquidacao")
        ):
            raise ValueError("Informe data_liquidacao quando o status for liquidado.")

        conta = db.query(Conta).filter(Conta.id == db_transacao.conta_id, Conta.user_id == user_id).first()
        if not conta:
            raise ValueError("Conta da transacao nao encontrada")

        impacto_antigo = impacto_no_saldo(db_transacao)
        for field, value in update_data.items():
            setattr(db_transacao, field, value)

        impacto_novo = impacto_no_saldo(db_transacao)
        conta.saldo += impacto_novo - impacto_antigo

        db.add(db_transacao)
        db.add(conta)
        db.commit()
        db.refresh(db_transacao)
        return db_transacao

    conta_antiga = db.query(Conta).filter(Conta.id == db_transacao.conta_id, Conta.user_id == user_id).first()
    if not conta_antiga:
        raise ValueError("Conta da transacao nao encontrada")

    dizimo = None
    if db_transacao.transacao_dizimo_uuid:
        dizimo = db.query(Transacao).filter(
            and_(
                Transacao.transacao_dizimo_uuid == db_transacao.transacao_dizimo_uuid,
                Transacao.e_dizimo.is_(True),
            )
        ).first()

    meta_antiga_id = db_transacao.meta_id
    orcamentos_afetados = set()
    if db_transacao.categoria_id and db_transacao.tipo == TipoTransacao.SAIDA:
        orcamentos_afetados.add((db_transacao.categoria_id, db_transacao.data.month, db_transacao.data.year))

    impacto_antigo = impacto_no_saldo(db_transacao)
    update_data = transacao_update.model_dump(exclude_unset=True)

    nova_conta_id = update_data.get("conta_id")
    conta_nova = conta_antiga
    if nova_conta_id and nova_conta_id != conta_antiga.id:
        conta_nova = db.query(Conta).filter(Conta.id == nova_conta_id, Conta.user_id == user_id).first()
        if not conta_nova:
            raise ValueError("Conta de destino nao encontrada")

    for field, value in update_data.items():
        setattr(db_transacao, field, value)

    if (
        update_data.get("status_liquidacao") == StatusLiquidacao.LIQUIDADO
        and not update_data.get("data_liquidacao")
    ):
        raise ValueError("Informe data_liquidacao quando o status for liquidado.")

    conta_final = db.query(Conta).filter(Conta.id == db_transacao.conta_id, Conta.user_id == user_id).first()
    if conta_final and conta_final.tipo == TipoConta.CARTAO_CREDITO and db_transacao.tipo == TipoTransacao.SAIDA:
        db_transacao.status_liquidacao = StatusLiquidacao.PREVISTO
        db_transacao.data_liquidacao = None

    impacto_novo = impacto_no_saldo(db_transacao)

    conta_antiga.saldo -= impacto_antigo
    conta_nova.saldo += impacto_novo

    deve_ter_dizimo = bool(db_transacao.tem_dizimo and db_transacao.tipo == TipoTransacao.ENTRADA)

    if deve_ter_dizimo:
        if not db_transacao.transacao_dizimo_uuid:
            db_transacao.transacao_dizimo_uuid = str(uuid.uuid4())

        if dizimo:
            if dizimo.categoria_id and dizimo.tipo == TipoTransacao.SAIDA:
                orcamentos_afetados.add((dizimo.categoria_id, dizimo.data.month, dizimo.data.year))
            impacto_dizimo_antigo = impacto_no_saldo(dizimo)
            valor_dizimo = db_transacao.valor * (db_transacao.percentual_dizimo / 100)
            dizimo.valor = valor_dizimo
            dizimo.descricao = f"Dizimo de {db_transacao.descricao}"
            dizimo.data = db_transacao.data
            dizimo.data_vencimento = db_transacao.data_vencimento or db_transacao.data
            dizimo.conta_id = db_transacao.conta_id
            if dizimo.categoria_id is None:
                dizimo.categoria_id = obter_categoria_dizimo(db, user_id).id
            impacto_dizimo_novo = impacto_no_saldo(dizimo)
            if dizimo.categoria_id and dizimo.tipo == TipoTransacao.SAIDA:
                orcamentos_afetados.add((dizimo.categoria_id, dizimo.data.month, dizimo.data.year))

            conta_antiga.saldo -= impacto_dizimo_antigo
            conta_nova.saldo += impacto_dizimo_novo
        else:
            categoria_dizimo = obter_categoria_dizimo(db, user_id)
            novo_dizimo = Transacao(
                user_id=user_id,
                transacao_uuid=str(uuid.uuid4()),
                conta_id=db_transacao.conta_id,
                categoria_id=categoria_dizimo.id,
                descricao=f"Dizimo de {db_transacao.descricao}",
                valor=db_transacao.valor * (db_transacao.percentual_dizimo / 100),
                tipo=TipoTransacao.SAIDA,
                data=db_transacao.data,
                data_vencimento=db_transacao.data_vencimento or db_transacao.data,
                data_liquidacao=None,
                status_liquidacao=StatusLiquidacao.PREVISTO,
                fixa=True,
                recorrente=False,
                confirmada=False,
                tem_dizimo=False,
                percentual_dizimo=db_transacao.percentual_dizimo,
                e_dizimo=True,
                entrada_origem_id=db_transacao.id,
                transacao_dizimo_uuid=db_transacao.transacao_dizimo_uuid,
                parcelado=False,
                e_emprestimo=False,
                valor_multa=0.0,
                valor_juros=0.0,
                valor_desconto=0.0,
            )
            db.add(novo_dizimo)
            conta_nova.saldo += impacto_no_saldo(novo_dizimo)
            if novo_dizimo.categoria_id and novo_dizimo.tipo == TipoTransacao.SAIDA:
                orcamentos_afetados.add((novo_dizimo.categoria_id, novo_dizimo.data.month, novo_dizimo.data.year))
    else:
        if dizimo:
            impacto_dizimo_antigo = impacto_no_saldo(dizimo)
            conta_origem_dizimo = conta_nova if dizimo.conta_id == conta_nova.id else conta_antiga
            conta_origem_dizimo.saldo -= impacto_dizimo_antigo
            if dizimo.categoria_id and dizimo.tipo == TipoTransacao.SAIDA:
                orcamentos_afetados.add((dizimo.categoria_id, dizimo.data.month, dizimo.data.year))
            db.delete(dizimo)
        db_transacao.tem_dizimo = False
        db_transacao.transacao_dizimo_uuid = None

    if db_transacao.categoria_id and db_transacao.tipo == TipoTransacao.SAIDA:
        orcamentos_afetados.add((db_transacao.categoria_id, db_transacao.data.month, db_transacao.data.year))

    db.flush()
    metas_afetadas = {meta_id for meta_id in [meta_antiga_id, db_transacao.meta_id] if meta_id}
    for meta_id in metas_afetadas:
        recalcular_meta(db, user_id, meta_id)
    for categoria_id, mes, ano in orcamentos_afetados:
        recalcular_orcamento_mes(db, user_id, categoria_id, mes, ano)

    db.commit()
    db.refresh(db_transacao)
    return db_transacao


def duplicar_transacao(
    db: Session,
    transacao_id: int,
    user_id: int,
) -> Optional[Transacao]:
    original = get_transacao(db, transacao_id, user_id)
    if not original:
        return None

    if original.e_dizimo:
        raise ValueError("Transacoes de dizimo nao podem ser duplicadas diretamente. Duplique a entrada original.")

    hoje = date.today()

    if original.parcelado:
        nova_transacao = Transacao(
            user_id=user_id,
            transacao_uuid=str(uuid.uuid4()),
            conta_id=original.conta_id,
            categoria_id=original.categoria_id,
            descricao=original.descricao,
            valor=original.valor,
            tipo=original.tipo,
            data=hoje,
            data_vencimento=hoje,
            data_liquidacao=None,
            status_liquidacao=StatusLiquidacao.PREVISTO,
            fixa=original.fixa,
            recorrente=original.recorrente,
            confirmada=original.confirmada,
            tem_dizimo=False,
            percentual_dizimo=original.percentual_dizimo,
            transacao_dizimo_uuid=None,
            e_dizimo=False,
            entrada_origem_id=None,
            parcelado=True,
            parcela_atual=original.parcela_atual,
            total_parcelas=original.total_parcelas,
            grupo_parcelamento_uuid=str(uuid.uuid4()) if original.grupo_parcelamento_uuid else None,
            e_emprestimo=original.e_emprestimo,
            pessoa_emprestimo=original.pessoa_emprestimo,
            observacoes=original.observacoes,
            tags=original.tags,
            valor_multa=original.valor_multa or 0,
            valor_juros=original.valor_juros or 0,
            valor_desconto=original.valor_desconto or 0,
            meta_id=original.meta_id,
        )

        db.add(nova_transacao)
        db.flush()

        if nova_transacao.meta_id:
            recalcular_meta(db, user_id, nova_transacao.meta_id)
        if nova_transacao.categoria_id and nova_transacao.tipo == TipoTransacao.SAIDA:
            recalcular_orcamento_mes(
                db,
                user_id,
                nova_transacao.categoria_id,
                nova_transacao.data.month,
                nova_transacao.data.year,
            )

        db.commit()
        db.refresh(nova_transacao)
        return nova_transacao

    transacao_copia = TransacaoCreate(
        conta_id=original.conta_id,
        categoria_id=original.categoria_id,
        descricao=original.descricao,
        valor=original.valor,
        tipo=original.tipo,
        data=hoje,
        data_vencimento=hoje,
        data_liquidacao=None,
        status_liquidacao=StatusLiquidacao.PREVISTO,
        fixa=original.fixa,
        recorrente=original.recorrente,
        confirmada=original.confirmada,
        tem_dizimo=bool(original.tem_dizimo and original.tipo == TipoTransacao.ENTRADA),
        percentual_dizimo=original.percentual_dizimo or 10.0,
        parcelado=False,
        total_parcelas=None,
        e_emprestimo=original.e_emprestimo,
        pessoa_emprestimo=original.pessoa_emprestimo,
        observacoes=original.observacoes,
        tags=original.tags,
        valor_multa=original.valor_multa or 0,
        valor_juros=original.valor_juros or 0,
        valor_desconto=original.valor_desconto or 0,
        meta_id=original.meta_id,
    )
    return criar_transacao(db, transacao_copia, user_id)


def deletar_transacao(
    db: Session,
    transacao_id: int,
    user_id: int,
) -> bool:
    db_transacao = get_transacao(db, transacao_id, user_id)
    if not db_transacao:
        return False

    if db_transacao.e_dizimo:
        raise ValueError("Transacoes de dizimo nao podem ser deletadas diretamente. Delete a entrada original.")

    conta = db.query(Conta).filter(Conta.id == db_transacao.conta_id, Conta.user_id == user_id).first()
    if not conta:
        raise ValueError("Conta da transacao nao encontrada")

    metas_afetadas = set()
    orcamentos_afetados = set()
    if db_transacao.meta_id:
        metas_afetadas.add(db_transacao.meta_id)
    if db_transacao.categoria_id and db_transacao.tipo == TipoTransacao.SAIDA:
        orcamentos_afetados.add((db_transacao.categoria_id, db_transacao.data.month, db_transacao.data.year))

    conta.saldo -= impacto_no_saldo(db_transacao)

    if db_transacao.tem_dizimo and db_transacao.transacao_dizimo_uuid:
        dizimo = db.query(Transacao).filter(
            and_(
                Transacao.transacao_dizimo_uuid == db_transacao.transacao_dizimo_uuid,
                Transacao.e_dizimo.is_(True),
            )
        ).first()

        if dizimo:
            conta.saldo -= impacto_no_saldo(dizimo)
            if dizimo.categoria_id and dizimo.tipo == TipoTransacao.SAIDA:
                orcamentos_afetados.add((dizimo.categoria_id, dizimo.data.month, dizimo.data.year))
            db.delete(dizimo)

    db.delete(db_transacao)
    db.flush()
    for meta_id in metas_afetadas:
        recalcular_meta(db, user_id, meta_id)
    for categoria_id, mes, ano in orcamentos_afetados:
        recalcular_orcamento_mes(db, user_id, categoria_id, mes, ano)
    db.commit()
    return True
