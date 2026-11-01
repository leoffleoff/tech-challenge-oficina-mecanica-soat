import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.infrastructure.database.models import Base, UsuarioAdminModel
from app.infrastructure.database.session import get_db
from app.infrastructure.security.jwt_handler import get_password_hash
from app.main import app


@pytest.fixture(autouse=True)
def setup_database():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        admin = (
            db.query(UsuarioAdminModel)
            .filter(UsuarioAdminModel.username == settings.ADMIN_USERNAME)
            .first()
        )
        if not admin:
            db.add(
                UsuarioAdminModel(
                    username=settings.ADMIN_USERNAME,
                    password_hash=get_password_hash(settings.ADMIN_PASSWORD),
                    ativo=True,
                )
            )
            db.commit()
    finally:
        db.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def _obter_headers_auth(client: TestClient) -> dict:
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": settings.ADMIN_USERNAME, "password": settings.ADMIN_PASSWORD},
    )
    assert resp.status_code == 200, f"Erro no login: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_healthcheck_e_autenticacao_jwt(client: TestClient):
    resp_health = client.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "healthy"

    # Tentativa de acesso sem token em rota protegida
    resp_unauth = client.get("/api/v1/clientes")
    assert resp_unauth.status_code == 401

    # Login com senha errada
    resp_bad_login = client.post(
        "/api/v1/auth/login",
        data={"username": settings.ADMIN_USERNAME, "password": "wrongpassword"},
    )
    assert resp_bad_login.status_code == 401


def test_crud_completo_clientes_e_veiculos_admin(client: TestClient):
    headers = _obter_headers_auth(client)

    # Criar Cliente
    cli = client.post(
        "/api/v1/clientes",
        json={
            "nome": "Carlos Silva",
            "documento": "11144477735",
            "telefone": "11999991111",
            "email": "carlos@email.com",
            "endereco": "Rua A, 123",
        },
        headers=headers,
    ).json()
    cli_id = cli["id"]

    # Listar e Buscar por ID / Documento
    assert len(client.get("/api/v1/clientes", headers=headers).json()) == 1
    assert client.get(f"/api/v1/clientes/{cli_id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/clientes/documento/{cli['documento']}", headers=headers).status_code == 200

    # Buscar inexistente (404)
    assert client.get("/api/v1/clientes/9999", headers=headers).status_code == 404
    assert client.get("/api/v1/clientes/documento/00000000000", headers=headers).status_code == 404

    # Atualizar Cliente
    upd_cli = client.put(
        f"/api/v1/clientes/{cli_id}",
        json={
            "nome": "Carlos Eduardo Silva",
            "telefone": "11988882222",
            "email": "carlos.edu@email.com",
            "endereco": "Rua B, 456",
        },
        headers=headers,
    ).json()
    assert upd_cli["nome"] == "Carlos Eduardo Silva"

    # Criar Veículo
    veic = client.post(
        "/api/v1/veiculos",
        json={
            "placa": "ABC1D23",
            "marca": "Chevrolet",
            "modelo": "Onix",
            "ano": 2023,
            "cor": "Branco",
            "cliente_id": cli_id,
        },
        headers=headers,
    ).json()
    veic_id = veic["id"]

    # Listar e Buscar Veículo
    assert len(client.get("/api/v1/veiculos", headers=headers).json()) == 1
    assert client.get(f"/api/v1/veiculos/{veic_id}", headers=headers).status_code == 200
    assert client.get("/api/v1/veiculos/9999", headers=headers).status_code == 404

    # Atualizar Veículo
    upd_veic = client.put(
        f"/api/v1/veiculos/{veic_id}",
        json={
            "placa": "ABC1D23",
            "marca": "Chevrolet",
            "modelo": "Onix Plus",
            "ano": 2023,
            "cor": "Preto",
            "cliente_id": cli_id,
        },
        headers=headers,
    ).json()
    assert upd_veic["modelo"] == "Onix Plus"

    # Deletar Veículo e Cliente
    assert client.delete(f"/api/v1/veiculos/{veic_id}", headers=headers).status_code == 204
    assert client.delete(f"/api/v1/veiculos/9999", headers=headers).status_code == 404

    assert client.delete(f"/api/v1/clientes/{cli_id}", headers=headers).status_code == 204
    assert client.delete(f"/api/v1/clientes/9999", headers=headers).status_code == 404


def test_crud_servicos_e_pecas_admin(client: TestClient):
    headers = _obter_headers_auth(client)

    # Serviços
    serv = client.post(
        "/api/v1/servicos",
        json={
            "nome": "Troca de Pastilhas",
            "descricao": "Substituição dianteira",
            "preco_base": "120.00",
            "tempo_estimado_minutos": 45,
        },
        headers=headers,
    ).json()
    serv_id = serv["id"]

    assert len(client.get("/api/v1/servicos", headers=headers).json()) == 1
    assert client.get(f"/api/v1/servicos/{serv_id}", headers=headers).status_code == 200
    assert client.get("/api/v1/servicos/9999", headers=headers).status_code == 404

    upd_serv = client.put(
        f"/api/v1/servicos/{serv_id}",
        json={
            "nome": "Troca de Pastilhas Completa",
            "descricao": "Dianteira e traseira",
            "preco_base": "200.00",
            "tempo_estimado_minutos": 60,
        },
        headers=headers,
    ).json()
    assert upd_serv["preco_base"] == "200.00"

    assert client.delete(f"/api/v1/servicos/{serv_id}", headers=headers).status_code == 204
    assert client.delete(f"/api/v1/servicos/9999", headers=headers).status_code == 404

    # Peças
    peca = client.post(
        "/api/v1/pecas",
        json={
            "nome": "Amortecedor",
            "codigo_sku": "AMT-01",
            "preco_unitario": "300.00",
            "quantidade_estoque": 10,
            "estoque_minimo": 2,
        },
        headers=headers,
    ).json()
    peca_id = peca["id"]

    assert len(client.get("/api/v1/pecas", headers=headers).json()) == 1
    assert client.get(f"/api/v1/pecas/{peca_id}", headers=headers).status_code == 200
    assert client.get("/api/v1/pecas/9999", headers=headers).status_code == 404

    # Repor estoque
    repor = client.patch(
        f"/api/v1/pecas/{peca_id}/repor-estoque",
        json={"quantidade": 5},
        headers=headers,
    ).json()
    assert repor["quantidade_estoque"] == 15

    # Atualizar peça
    client.put(
        f"/api/v1/pecas/{peca_id}",
        json={
            "nome": "Amortecedor Dianteiro",
            "codigo_sku": "AMT-01",
            "preco_unitario": "320.00",
            "quantidade_estoque": 15,
            "estoque_minimo": 2,
        },
        headers=headers,
    )

    assert client.delete(f"/api/v1/pecas/{peca_id}", headers=headers).status_code == 204
    assert client.delete(f"/api/v1/pecas/9999", headers=headers).status_code == 404


def test_fluxo_completo_ordem_servico_e_excecoes_use_cases(client: TestClient):
    headers = _obter_headers_auth(client)

    # Setup cliente, veiculo, servico, peca
    cli = client.post(
        "/api/v1/clientes",
        json={
            "nome": "Ana Souza",
            "documento": "52998224725",
            "telefone": "11988887777",
            "email": "ana@email.com",
        },
        headers=headers,
    ).json()

    veic = client.post(
        "/api/v1/veiculos",
        json={
            "placa": "XYZ9W87",
            "marca": "Ford",
            "modelo": "Ka",
            "ano": 2019,
            "cliente_id": cli["id"],
        },
        headers=headers,
    ).json()

    serv = client.post(
        "/api/v1/servicos",
        json={
            "nome": "Troca de Óleo",
            "descricao": "Óleo 5W30",
            "preco_base": "150.00",
            "tempo_estimado_minutos": 30,
        },
        headers=headers,
    ).json()

    peca = client.post(
        "/api/v1/pecas",
        json={
            "nome": "Filtro de Óleo",
            "codigo_sku": "FLT-99",
            "preco_unitario": "50.00",
            "quantidade_estoque": 5,
            "estoque_minimo": 1,
        },
        headers=headers,
    ).json()

    # Teste de erro: Criar OS com cliente inexistente
    resp_err1 = client.post(
        "/api/v1/ordens-servico",
        json={"cliente_id": 9999, "veiculo_id": veic["id"]},
        headers=headers,
    )
    assert resp_err1.status_code == 404

    # Criar OS com sucesso usando documento do cliente
    os_resp = client.post(
        "/api/v1/ordens-servico",
        json={
            "documento_cliente": "529.982.247-25",
            "veiculo_id": veic["id"],
            "observacoes": "Troca de óleo preventiva",
            "servicos": [{"servico_id": serv["id"], "quantidade": 1}],
            "pecas": [{"peca_id": peca["id"], "quantidade": 1}],
        },
        headers=headers,
    )
    assert os_resp.status_code == 201
    os_data = os_resp.json()
    os_id = os_data["id"]

    # Listar e Detalhar OS
    assert len(client.get("/api/v1/ordens-servico", headers=headers).json()) >= 1
    assert client.get(f"/api/v1/ordens-servico/{os_id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/publico/ordens-servico/{os_id}", headers=headers).status_code == 200
    assert client.get("/api/v1/ordens-servico/9999", headers=headers).status_code == 404

    # Adicionar mais itens após aberto
    add_resp = client.post(
        f"/api/v1/ordens-servico/{os_id}/itens",
        json={
            "servicos": [{"servico_id": serv["id"], "quantidade": 1}],
            "pecas": [],
        },
        headers=headers,
    )
    assert add_resp.status_code == 200

    # Aprovar orçamento
    aprov = client.post(
        f"/api/v1/publico/ordens-servico/{os_id}/avaliar-orcamento",
        json={"aprovado": True},
    )
    assert aprov.status_code == 200

    # Finalizar e Entregar
    client.patch(
        f"/api/v1/ordens-servico/{os_id}/status",
        json={"novo_status": "Finalizada"},
        headers=headers,
    )
    client.patch(
        f"/api/v1/ordens-servico/{os_id}/status",
        json={"novo_status": "Entregue"},
        headers=headers,
    )

    # Métricas
    assert client.get("/api/v1/ordens-servico/metricas/tempo-medio", headers=headers).status_code == 200


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
                "--cov=app",
                "--cov-report=term-missing",
            ],
            cwd=str(ROOT_DIR),
        )
    )
def test_clientes_endpoints_full_coverage(client: TestClient):
    headers = _obter_headers_auth(client)

    # 1. Testar listagem com base de dados vazia
    assert client.get("/api/v1/clientes", headers=headers).json() == []

    # 2. Criar cliente com sucesso (201)
    resp = client.post(
        "/api/v1/clientes",
        json={
            "nome": "Maria da Silva",
            "documento": "529.982.247-25",
            "telefone": "11988887777",
            "email": "maria@email.com",
            "endereco": "Av. Brasil, 500",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    cli_data = resp.json()
    cli_id = cli_data["id"]

    # 3. Tentar criar cliente com documento duplicado (409 Conflict)
    resp_dup = client.post(
        "/api/v1/clientes",
        json={
            "nome": "Outro Nome",
            "documento": "52998224725",
            "telefone": "11977776666",
            "email": "outro@email.com",
        },
        headers=headers,
    )
    assert resp_dup.status_code == 409

    # 4. Listar clientes com registros cadastrados
    lista = client.get("/api/v1/clientes", headers=headers).json()
    assert len(lista) == 1

    # 5. Buscar cliente por ID (Sucesso e 404 Not Found)
    assert client.get(f"/api/v1/clientes/{cli_id}", headers=headers).status_code == 200
    assert client.get("/api/v1/clientes/9999", headers=headers).status_code == 404

    # 6. Buscar cliente por Documento CPF/CNPJ (Sucesso e 404 Not Found)
    assert client.get("/api/v1/clientes/documento/529.982.247-25", headers=headers).status_code == 200
    assert client.get("/api/v1/clientes/documento/000.000.000-00", headers=headers).status_code == 404

    # 7. Atualizar cliente (Sucesso e 404 Not Found)
    resp_upd = client.put(
        f"/api/v1/clientes/{cli_id}",
        json={
            "nome": "Maria da Silva Atualizada",
            "telefone": "11977775555",
            "email": "maria.nova@email.com",
            "endereco": "Av. Argentina, 100",
        },
        headers=headers,
    )
    assert resp_upd.status_code == 200
    assert resp_upd.json()["nome"] == "Maria da Silva Atualizada"

    resp_upd_404 = client.put(
        "/api/v1/clientes/9999",
        json={
            "nome": "Inexistente",
            "telefone": "11900000000",
            "email": "inexistente@email.com",
        },
        headers=headers,
    )
    assert resp_upd_404.status_code == 404

    # 8. Deletar cliente (Sucesso e 404 Not Found)
    assert client.delete(f"/api/v1/clientes/{cli_id}", headers=headers).status_code == 204
    assert client.delete("/api/v1/clientes/9999", headers=headers).status_code == 404
    