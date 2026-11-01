import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.domain.entities.cliente import Cliente
from app.domain.entities.veiculo import Veiculo
from app.domain.entities.servico import Servico
from app.domain.entities.peca import Peca
from app.domain.exceptions.domain_exceptions import (
    BusinessRuleException,
    EntityNotFoundException,
)
from app.domain.value_objects.status_os import StatusOS
from app.infrastructure.database.models import Base
from app.infrastructure.repositories.sqlalchemy_repositories import (
    SQLAlchemyClienteRepository,
    SQLAlchemyOrdemServicoRepository,
    SQLAlchemyPecaRepository,
    SQLAlchemyServicoRepository,
    SQLAlchemyVeiculoRepository,
)
from app.application.use_cases.ordem_servico_use_cases import OrdemServicoUseCase


@pytest.fixture
def use_case():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLoc = sessionmaker(bind=engine)
    db = SessionLoc()

    uc = OrdemServicoUseCase(
        os_repo=SQLAlchemyOrdemServicoRepository(db),
        cliente_repo=SQLAlchemyClienteRepository(db),
        veiculo_repo=SQLAlchemyVeiculoRepository(db),
        servico_repo=SQLAlchemyServicoRepository(db),
        peca_repo=SQLAlchemyPecaRepository(db),
    )
    yield uc, db
    db.close()


def test_use_case_criacao_e_fluxos_completos(use_case):
    uc, db = use_case

    # 1. Cadastrar dependências via repositório direto para teste do UseCase
    cli_repo = SQLAlchemyClienteRepository(db)
    veic_repo = SQLAlchemyVeiculoRepository(db)
    serv_repo = SQLAlchemyServicoRepository(db)
    peca_repo = SQLAlchemyPecaRepository(db)

    cli = cli_repo.criar(
        Cliente(
            nome="Maria Oliveira",
            documento="52998224725",
            telefone="11999998888",
            email="maria@email.com",
        )
    )
    veic = veic_repo.criar(
        Veiculo(placa="BRA2E19", marca="VW", modelo="Gol", ano=2021, cliente_id=cli.id if (ano := 2021) else 2021)
    )
    serv = serv_repo.criar(
        Servico(
            nome="Geometria",
            descricao="Geometria e camber",
            preco_base=Decimal("100.00"),
            tempo_estimado_minutos=40,
        )
    )
    pec = peca_repo.criar(
        Peca(
            nome="Correia Dentada",
            codigo_sku="COR-01",
            preco_unitario=Decimal("200.00"),
            quantidade_estoque=10,
        )
    )

    # 2. Testar exceção: Cliente não encontrado
    with pytest.raises(EntityNotFoundException):
        uc.criar_ordem_servico(veiculo_id=veic.id, cliente_id=9999)

    with pytest.raises(EntityNotFoundException):
        uc.criar_ordem_servico(veiculo_id=veic.id, documento_cliente="00000000000")

    # 3. Testar exceção: Veículo não encontrado
    with pytest.raises(EntityNotFoundException):
        uc.criar_ordem_servico(veiculo_id=9999, cliente_id=cli.id)

    # 4. Testar exceção: Veículo não pertence ao cliente
    cli2 = cli_repo.criar(
        Cliente(
            nome="Outro",
            documento="11222333000181",
            telefone="11977776666",
            email="a@b.com",
        )
    )
    with pytest.raises(BusinessRuleException):
        uc.criar_ordem_servico(veiculo_id=veic.id, cliente_id=cli2.id)

    # 5. Criar OS com sucesso usando documento_cliente e incluindo itens
    os_criada = uc.criar_ordem_servico(
        veiculo_id=veic.id,
        documento_cliente="529.982.247-25",
        observacoes="Troca de correia",
        servicos_solicitados=[{"servico_id": serv.id, "quantidade": 1}],
        pecas_solicitadas=[{"peca_id": pec.id, "quantidade": 1}],
    )
    assert os_criada.id is not None
    assert os_criada.status == StatusOS.AGUARDANDO_APROVACAO

    # 6. Adicionar mais itens posteriormente
    os_adicionada = uc.adicionar_itens_os(
        os_id=os_criada.id,
        servicos_solicitados=[{"servico_id": serv.id, "quantidade": 1}],
        pecas_solicitadas=[],
    )
    assert len(os_adicionada.servicos) == 2

    # 7. Rejeitar orçamento (deve estornar estoque)
    os_rejeitada = uc.processar_decisao_orcamento(os_id=os_criada.id, aprovado=False)
    assert os_rejeitada.status == StatusOS.CANCELADA
    
    pec_verif = peca_repo.buscar_por_id(pec.id)
    assert pec_verif.quantidade_estoque == 10  # Voltou ao estoque original

    # 8. Testar métricas sem ordens finalizadas e com ordens finalizadas
    metricas_vazias = uc.calcular_metricas_tempo_execucao()
    assert metricas_vazias["tempo_medio_execucao_minutos"] == 0.0


if __name__ == "__main__":
    import subprocess
    raise SystemExit(
        subprocess.call(
            [sys.executable, "-m", "pytest", __file__, "-v", "--cov=app/application", "--cov-report=term-missing"],
            cwd=str(ROOT_DIR),
        )
    )