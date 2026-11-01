import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from datetime import timedelta
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domain.entities.cliente import Cliente
from app.domain.entities.veiculo import Veiculo
from app.domain.entities.servico import Servico
from app.domain.entities.peca import Peca
from app.domain.entities.ordem_servico import ItemPecaOS, ItemServicoOS, OrdemServico
from app.infrastructure.database.session import Base, get_db
from app.infrastructure.repositories.sqlalchemy_repositories import (
    SQLAlchemyClienteRepository,
    SQLAlchemyVeiculoRepository,
    SQLAlchemyServicoRepository,
    SQLAlchemyPecaRepository,
    SQLAlchemyOrdemServicoRepository,
)
from app.infrastructure.security.jwt_handler import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_session_get_db_generator():
    gen = get_db()
    db = next(gen)
    assert db is not None
    try:
        next(gen)
    except StopIteration:
        pass


def test_jwt_and_password_hashing():
    hashed = get_password_hash("SenhaForte@2026")
    assert verify_password("SenhaForte@2026", hashed) is True
    assert verify_password("SenhaErrada", hashed) is False
    # Testa o bloco except ValueError quando o hash tem formato inválido
    assert verify_password("SenhaForte@2026", "hash_invalido_nao_bcrypt") is False

    # Testa sem e com expires_delta explícito
    token_padrao = create_access_token(subject="admin")
    token_custom = create_access_token(subject="admin", expires_delta=timedelta(minutes=15))

    payload = decode_access_token(token_padrao)
    payload_custom = decode_access_token(token_custom)
    assert payload is not None and payload["sub"] == "admin"
    assert payload_custom is not None and payload_custom["sub"] == "admin"
    assert decode_access_token("token.invalido.aqui") is None


def test_repositorios_crud_completo_e_delecoes(db_session):
    cliente_repo = SQLAlchemyClienteRepository(db_session)
    veiculo_repo = SQLAlchemyVeiculoRepository(db_session)
    servico_repo = SQLAlchemyServicoRepository(db_session)
    peca_repo = SQLAlchemyPecaRepository(db_session)
    os_repo = SQLAlchemyOrdemServicoRepository(db_session)

    # 1. Cliente CRUD + buscar_por_id + deletar
    cliente = cliente_repo.criar(
        Cliente(
            nome="Leonardo Santos",
            documento="52998224725",
            telefone="11988887777",
            email="leo@acsc.org.br",
            endereco="São Paulo - SP",
        )
    )
    assert cliente_repo.buscar_por_id(cliente.id).id == cliente.id
    assert cliente_repo.buscar_por_id(9999) is None
    assert cliente_repo.buscar_por_documento("529.982.247-25").id == cliente.id
    cliente.nome = "Leonardo S. Santos"
    assert cliente_repo.atualizar(cliente).nome == "Leonardo S. Santos"
    assert len(cliente_repo.listar_todos()) == 1

    # Cria um segundo cliente apenas para testar deleção
    cliente_temp = cliente_repo.criar(
        Cliente(
            nome="Cliente Temporario",
            documento="11222333000181",
            telefone="11977776666",
            email="temp@oficina.com.br",
        )
    )
    assert cliente_repo.deletar(cliente_temp.id) is True
    assert cliente_repo.deletar(9999) is False

    # 2. Veiculo CRUD + buscar_por_id + deletar
    veiculo = veiculo_repo.criar(
        Veiculo(placa="BRA2E19", marca="Toyota", modelo="Corolla", ano=2024, cliente_id=cliente.id)
    )
    assert veiculo_repo.buscar_por_id(veiculo.id).id == veiculo.id
    assert veiculo_repo.buscar_por_id(9999) is None
    assert veiculo_repo.buscar_por_placa("bra2e19").id == veiculo.id
    veiculo.cor = "Prata"
    assert veiculo_repo.atualizar(veiculo).cor == "Prata"
    assert len(veiculo_repo.listar_todos()) == 1

    veiculo_temp = veiculo_repo.criar(
        Veiculo(placa="ABC1234", marca="Fiat", modelo="Uno", ano=2015, cliente_id=cliente.id)
    )
    assert veiculo_repo.deletar(veiculo_temp.id) is True
    assert veiculo_repo.deletar(9999) is False

    # 3. Servico CRUD + buscar_por_id + deletar
    servico = servico_repo.criar(
        Servico(
            nome="Revisão Completa",
            descricao="Revisão de 20.000 km",
            preco_base=Decimal("350.00"),
            tempo_estimado_minutos=120,
        )
    )
    assert servico_repo.buscar_por_id(servico.id).id == servico.id
    assert servico_repo.buscar_por_id(9999) is None
    servico.preco_base = Decimal("380.00")
    assert servico_repo.atualizar(servico).preco_base == Decimal("380.00")
    assert len(servico_repo.listar_todos()) == 1

    servico_temp = servico_repo.criar(
        Servico(
            nome="Lavagem Simples",
            descricao="Lavagem externa",
            preco_base=Decimal("50.00"),
            tempo_estimado_minutos=30,
        )
    )
    assert servico_repo.deletar(servico_temp.id) is True
    assert servico_repo.deletar(9999) is False

    # 4. Peca CRUD + buscar_por_id + deletar
    peca = peca_repo.criar(
        Peca(
            nome="Pastilha de Freio",
            codigo_sku="PST-99",
            preco_unitario=Decimal("140.00"),
            quantidade_estoque=15,
        )
    )
    assert peca_repo.buscar_por_id(peca.id).id == peca.id
    assert peca_repo.buscar_por_id(9999) is None
    assert peca_repo.buscar_por_sku("PST-99").id == peca.id
    peca.baixar_estoque(2)
    assert peca_repo.atualizar(peca).quantidade_estoque == 13
    assert len(peca_repo.listar_todos()) == 1

    peca_temp = peca_repo.criar(
        Peca(
            nome="Lâmpada Farol",
            codigo_sku="LMP-01",
            preco_unitario=Decimal("25.00"),
            quantidade_estoque=10,
        )
    )
    assert peca_repo.deletar(peca_temp.id) is True
    assert peca_repo.deletar(9999) is False

    # 5. Ordem de Serviço Persistência + buscar_por_id + Consulta por CPF/CNPJ
    nova_os = OrdemServico(cliente_id=cliente.id, veiculo_id=veiculo.id, observacoes="Freio fazendo barulho")
    nova_os.adicionar_servico(
        ItemServicoOS(servico_id=servico.id, nome_servico=servico.nome, preco_unitario=servico.preco_base)
    )
    nova_os.adicionar_peca(
        ItemPecaOS(peca_id=peca.id, nome_peca=peca.nome, preco_unitario=peca.preco_unitario, quantidade=2)
    )

    os_salva = os_repo.criar(nova_os)
    assert os_repo.buscar_por_id(os_salva.id).id == os_salva.id
    assert os_repo.buscar_por_id(9999) is None
    assert os_salva.valor_total_orcamento == Decimal("660.00")

    os_salva.disponibilizar_orcamento_para_aprovacao()
    os_salva.aprovar_orcamento()
    os_atualizada = os_repo.atualizar(os_salva)
    assert os_atualizada.status.value == "Em execução"

    lista_cliente = os_repo.listar_por_documento_cliente("529.982.247-25")
    assert len(lista_cliente) == 1
    assert len(os_repo.listar_todas()) == 1


if __name__ == "__main__":
    import subprocess
    raise SystemExit(
        subprocess.call(
            [
                sys.executable,
                "-m",
                "pytest",
                __file__,
                "-v",
                "--cov=app/infrastructure",
                "--cov-report=term-missing",
            ],
            cwd=str(ROOT_DIR),
        )
    )