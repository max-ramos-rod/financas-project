"""
Script para popular o banco de dados com categorias padrão

Rode após as migrations:
python seed_categorias.py
"""

from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.models import Categoria, TipoTransacao

# ========== CATEGORIAS PADRÃO ==========

CATEGORIAS_PADRAO = [
    # ===== ENTRADAS =====
    {
        "nome": "Salário",
        "icone": "💰",
        "cor": "#10B981",
        "tipo": "entrada",
        "descricao": "Salário mensal"
    },
    {
        "nome": "Freelance",
        "icone": "💼",
        "cor": "#3B82F6",
        "tipo": "entrada",
        "descricao": "Trabalhos freelance e projetos"
    },
    {
        "nome": "Investimentos",
        "icone": "📈",
        "cor": "#8B5CF6",
        "tipo": "entrada",
        "descricao": "Rendimentos de investimentos"
    },
    {
        "nome": "Presente Recebido",
        "icone": "🎁",
        "cor": "#F59E0B",
        "tipo": "entrada",
        "descricao": "Presentes em dinheiro"
    },
    {
        "nome": "Venda",
        "icone": "🏷️",
        "cor": "#06B6D4",
        "tipo": "entrada",
        "descricao": "Venda de produtos ou serviços"
    },
    {
        "nome": "Outras Receitas",
        "icone": "➕",
        "cor": "#6B7280",
        "tipo": "entrada",
        "descricao": "Outras fontes de renda"
    },

    # ===== SAÍDAS - MORADIA =====
    {
        "nome": "Aluguel",
        "icone": "🏠",
        "cor": "#EF4444",
        "tipo": "saida",
        "descricao": "Aluguel residencial"
    },
    {
        "nome": "Condomínio",
        "icone": "🏢",
        "cor": "#DC2626",
        "tipo": "saida",
        "descricao": "Taxa de condomínio"
    },
    {
        "nome": "Energia",
        "icone": "⚡",
        "cor": "#F59E0B",
        "tipo": "saida",
        "descricao": "Conta de luz"
    },
    {
        "nome": "Água",
        "icone": "💧",
        "cor": "#3B82F6",
        "tipo": "saida",
        "descricao": "Conta de água"
    },
    {
        "nome": "Internet",
        "icone": "🌐",
        "cor": "#8B5CF6",
        "tipo": "saida",
        "descricao": "Internet residencial"
    },
    {
        "nome": "Gás",
        "icone": "🔥",
        "cor": "#F97316",
        "tipo": "saida",
        "descricao": "Gás de cozinha"
    },

    # ===== SAÍDAS - ALIMENTAÇÃO =====
    {
        "nome": "Mercado",
        "icone": "🛒",
        "cor": "#10B981",
        "tipo": "saida",
        "descricao": "Compras de supermercado"
    },
    {
        "nome": "Restaurante",
        "icone": "🍽️",
        "cor": "#F59E0B",
        "tipo": "saida",
        "descricao": "Refeições fora de casa"
    },
    {
        "nome": "Lanche",
        "icone": "🍔",
        "cor": "#FCD34D",
        "tipo": "saida",
        "descricao": "Lanches e cafés"
    },

    # ===== SAÍDAS - TRANSPORTE =====
    {
        "nome": "Combustível",
        "icone": "⛽",
        "cor": "#EF4444",
        "tipo": "saida",
        "descricao": "Gasolina, etanol, diesel"
    },
    {
        "nome": "Transporte Público",
        "icone": "🚌",
        "cor": "#3B82F6",
        "tipo": "saida",
        "descricao": "Ônibus, metrô, trem"
    },
    {
        "nome": "Uber/Taxi",
        "icone": "🚕",
        "cor": "#6B7280",
        "tipo": "saida",
        "descricao": "Corridas de aplicativo"
    },
    {
        "nome": "Estacionamento",
        "icone": "🅿️",
        "cor": "#6B7280",
        "tipo": "saida",
        "descricao": "Estacionamento"
    },

    # ===== SAÍDAS - SAÚDE =====
    {
        "nome": "Farmácia",
        "icone": "💊",
        "cor": "#EF4444",
        "tipo": "saida",
        "descricao": "Medicamentos"
    },
    {
        "nome": "Médico",
        "icone": "⚕️",
        "cor": "#DC2626",
        "tipo": "saida",
        "descricao": "Consultas médicas"
    },
    {
        "nome": "Plano de Saúde",
        "icone": "🏥",
        "cor": "#EF4444",
        "tipo": "saida",
        "descricao": "Mensalidade do plano"
    },

    # ===== SAÍDAS - EDUCAÇÃO =====
    {
        "nome": "Mensalidade Escola",
        "icone": "🎓",
        "cor": "#3B82F6",
        "tipo": "saida",
        "descricao": "Escola, faculdade"
    },
    {
        "nome": "Livros",
        "icone": "📚",
        "cor": "#8B5CF6",
        "tipo": "saida",
        "descricao": "Livros e material didático"
    },
    {
        "nome": "Cursos",
        "icone": "💻",
        "cor": "#06B6D4",
        "tipo": "saida",
        "descricao": "Cursos online e presenciais"
    },

    # ===== SAÍDAS - LAZER =====
    {
        "nome": "Cinema",
        "icone": "🎬",
        "cor": "#F59E0B",
        "tipo": "saida",
        "descricao": "Cinema, teatro, shows"
    },
    {
        "nome": "Streaming",
        "icone": "📺",
        "cor": "#EF4444",
        "tipo": "saida",
        "descricao": "Netflix, Spotify, etc"
    },
    {
        "nome": "Viagem",
        "icone": "✈️",
        "cor": "#3B82F6",
        "tipo": "saida",
        "descricao": "Viagens e turismo"
    },
    {
        "nome": "Academia",
        "icone": "🏋️",
        "cor": "#10B981",
        "tipo": "saida",
        "descricao": "Academia e esportes"
    },

    # ===== SAÍDAS - PESSOAL =====
    {
        "nome": "Vestuário",
        "icone": "👕",
        "cor": "#8B5CF6",
        "tipo": "saida",
        "descricao": "Roupas e calçados"
    },
    {
        "nome": "Cabeleireiro",
        "icone": "💇",
        "cor": "#F59E0B",
        "tipo": "saida",
        "descricao": "Salão de beleza"
    },
    {
        "nome": "Cosméticos",
        "icone": "💄",
        "cor": "#EC4899",
        "tipo": "saida",
        "descricao": "Maquiagem e cosméticos"
    },

    # ===== SAÍDAS - OUTROS =====
    {
        "nome": "Cartão de Crédito",
        "icone": "💳",
        "cor": "#6B7280",
        "tipo": "saida",
        "descricao": "Fatura do cartão"
    },
    {
        "nome": "Empréstimo",
        "icone": "🏦",
        "cor": "#EF4444",
        "tipo": "saida",
        "descricao": "Parcelas de empréstimos"
    },
    {
        "nome": "Presente Dado",
        "icone": "🎁",
        "cor": "#F59E0B",
        "tipo": "saida",
        "descricao": "Presentes para outras pessoas"
    },
    {
        "nome": "Pet",
        "icone": "🐕",
        "cor": "#F59E0B",
        "tipo": "saida",
        "descricao": "Despesas com pets"
    },
    {
        "nome": "Outros",
        "icone": "📌",
        "cor": "#6B7280",
        "tipo": "saida",
        "descricao": "Outras despesas"
    },

    # ===== CATEGORIAS CRISTÃS =====
    {
        "nome": "Dízimo",
        "icone": "⛪",
        "cor": "#10B981",
        "tipo": "saida",
        "descricao": "Dízimo para a igreja"
    },
    {
        "nome": "Oferta",
        "icone": "🙏",
        "cor": "#3B82F6",
        "tipo": "saida",
        "descricao": "Ofertas especiais"
    },
    {
        "nome": "Missões",
        "icone": "🌍",
        "cor": "#8B5CF6",
        "tipo": "saida",
        "descricao": "Contribuição para missões"
    },
    {
        "nome": "Acampamento/Retiro",
        "icone": "⛺",
        "cor": "#F59E0B",
        "tipo": "saida",
        "descricao": "Eventos da igreja"
    },
    {
        "nome": "Literatura Cristã",
        "icone": "📖",
        "cor": "#06B6D4",
        "tipo": "saida",
        "descricao": "Livros e materiais cristãos"
    },
    {
        "nome": "Seminário",
        "icone": "🎓",
        "cor": "#3B82F6",
        "tipo": "saida",
        "descricao": "Cursos e seminários teológicos"
    },

    # ===== CATEGORIAS FLEXÍVEIS (tipo=NULL) =====
    {
        "nome": "Transferência",
        "icone": "🔄",
        "cor": "#6B7280",
        "tipo": "transferencia",  # Pode ser entrada ou saída
        "descricao": "Transferências entre contas"
    },
]


def seed_categorias():
    """Popula o banco com categorias padrão"""
    db: Session = SessionLocal()

    try:
        print("🌱 Iniciando seed de categorias padrão...")

        # Verifica se já existem categorias padrão
        count = db.query(Categoria).filter(Categoria.padrao is True).count()

        if count > 0:
            print(f"⚠️  Já existem {count} categorias padrão no banco.")
            resposta = input("Deseja recriar? (s/N): ")
            if resposta.lower() != 's':
                print("❌ Operação cancelada.")
                return

            # Remove categorias padrão antigas
            db.query(Categoria).filter(Categoria.padrao is True).delete()
            db.commit()
            print("🗑️  Categorias antigas removidas.")

        # Cria categorias padrão
        categorias_criadas = 0
        for cat_data in CATEGORIAS_PADRAO:
            categoria = Categoria(
                user_id=None,  # Sem dono (disponível para todos)
                nome=cat_data["nome"],
                icone=cat_data["icone"],
                cor=cat_data["cor"],
                tipo=cat_data["tipo"],
                padrao=True  # É categoria padrão do sistema
            )
            db.add(categoria)
            categorias_criadas += 1

        db.commit()

        print(f"✅ {categorias_criadas} categorias padrão criadas com sucesso!")
        print("\nResumo:")

        # Estatísticas
        entradas = db.query(Categoria).filter(
            Categoria.padrao is True,
            Categoria.tipo == TipoTransacao.ENTRADA
        ).count()

        saidas = db.query(Categoria).filter(
            Categoria.padrao is True,
            Categoria.tipo == TipoTransacao.SAIDA
        ).count()

        flexiveis = db.query(Categoria).filter(
            Categoria.padrao is True,
            Categoria.tipo is None
        ).count()

        print(f"  📈 Entradas: {entradas}")
        print(f"  📉 Saídas: {saidas}")
        print(f"  🔄 Flexíveis: {flexiveis}")
        print(f"  📊 Total: {categorias_criadas}")

    except Exception as e:
        print(f"❌ Erro ao criar categorias: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def listar_categorias():
    """Lista todas as categorias padrão"""
    db: Session = SessionLocal()

    try:
        categorias = db.query(Categoria).filter(
            Categoria.padrao is True
        ).order_by(Categoria.tipo, Categoria.nome).all()

        print("\n📋 CATEGORIAS PADRÃO DO SISTEMA:\n")

        tipo_atual = None
        for cat in categorias:
            if cat.tipo != tipo_atual:
                tipo_atual = cat.tipo
                print(f"\n{'='*50}")
                if cat.tipo == TipoTransacao.ENTRADA:
                    print("📈 ENTRADAS")
                elif cat.tipo == TipoTransacao.SAIDA:
                    print("📉 SAÍDAS")
                else:
                    print("🔄 FLEXÍVEIS (Entrada ou Saída)")
                print(f"{'='*50}\n")

            print(f"{cat.icone}  {cat.nome:30} (cor: {cat.cor})")

        print(f"\n{'='*50}")
        print(f"Total: {len(categorias)} categorias")
        print(f"{'='*50}\n")

    finally:
        db.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--listar":
        listar_categorias()
    else:
        seed_categorias()
