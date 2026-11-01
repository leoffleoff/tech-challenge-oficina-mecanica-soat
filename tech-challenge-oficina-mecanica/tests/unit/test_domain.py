import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest

from app.domain.exceptions.domain_exceptions import (
    BusinessRuleException,
    InsufficientStockException,
    InvalidDocumentException,
    InvalidLicensePlateException,
    InvalidStatusTransitionException,
)
from app.domain.value_objects.cpf_cnpj import CpfCnpj
from app.domain.value_objects.placa import Placa
from app.domain.value_objects.status_os import StatusOS
from app.domain.entities.cliente import Cliente
from app.domain.entities.veiculo import Veiculo
from app.domain.entities.servico import Servico
from app.domain.entities.peca import Peca
from app.domain.entities.ordem_servico import ItemPecaOS, ItemServicoOS, OrdemServico


# ==========================================
# TESTES DE VALUE OBJECTS (CPF/CNPJ e PLACA)
# ==========================================
def test_cpf_valido_com_e_sem_mascara():
    cpf = CpfCnpj("529.982.247-25")
    assert cpf.value == "52998224725"
    assert cpf.document_type == "CPF"
    assert cpf.formatted == "529.982.247-25"
    assert str(cpf) == "52998224725"


def test_cnpj_valido_com_e_sem_mascara():
    cnpj = CpfCnpj("11.222.333/0001-81")
    assert cnpj.value == "11222333000181"
    assert cnpj.document_type == "CNPJ"
    assert cnpj.formatted == "11.222.333/0001-81"
    assert str(cnpj) == "11222333000181"


@pytest.mark.parametrize(
    "doc_invalido",
    [
        "111.111.111-11",
        "529.982.247-99",
        "529.982.247-05",
        "11.111.111/1111-11",
        "11.222.333/0001-99",
        "11.222.333/0001-01",
        "12345",
        "",
    ],
)
def test_documento_invalido_dispara_excecao(doc_invalido):
    with pytest.raises(InvalidDocumentException):
        CpfCnpj(doc_invalido)


def test_placa_antiga_e_mercosul_validas():
    placa_antiga = Placa("abc-1234")
    assert placa_antiga.value == "ABC1234"
    assert not placa_antiga.is_mercosul
    assert placa_antiga.formatted == "ABC-1234"
    assert str(placa_antiga) == "ABC1234"

    placa_mercosul = Placa("bra2e19")
    assert placa_mercosul.value == "BRA2E19"
    assert placa_mercosul.is_mercosul
    assert placa_mercosul.formatted == "BRA2E19"


@pytest.mark.parametrize("placa_invalida", ["", "AB1234", "ABCD123", "1234ABC", "ABC12345"])
def test_placa_invalida_dispara_excecao(placa_invalida):
    with pytest.raises(InvalidLicensePlateException):
        Placa(placa_invalida)


# ==========================================
# TESTES DE ENTIDADES (CLIENTE, VEICULO, SERVICO, PECA)
# ==========================================
def test_criacao_cliente_valido_e_regras():
    cliente = Cliente(
        nome="Leonardo Santos",
        documento="52998224725",
        telefone="11999998888",
        email="leonardo@oficina.com.br",
    )
    assert cliente.documento.document_type == "CPF"

    with pytest.raises(BusinessRuleException):
        Cliente(nome="Ab", documento="52998224725", telefone="11999998888", email="a@b.com")

    with pytest.raises(BusinessRuleException):
        Cliente(nome="Leonardo", documento="52998224725", telefone="11999998888", email="invalido")

    with pytest.raises(BusinessRuleException):
        Cliente(nome="Leonardo", documento="52998224725", telefone="123", email="a@b.com")


def test_criacao_veiculo_e_validacoes():
    veiculo = Veiculo(placa="BRA2E19", marca="Honda", modelo="Civic", ano=2022, cliente_id=1)
    assert veiculo.placa.value == "BRA2E19"

    with pytest.raises(BusinessRuleException):
        Veiculo(placa="BRA2E19", marca="", modelo="Civic", ano=2022, cliente_id=1)

    with pytest.raises(BusinessRuleException):
        Veiculo(placa="BRA2E19", marca="Honda", modelo="", ano=2022, cliente_id=1)

    with pytest.raises(BusinessRuleException):
        Veiculo(placa="BRA2E19", marca="Honda", modelo="Civic", ano=1850, cliente_id=1)


def test_criacao_servico_e_validacoes():
    servico = Servico(
        nome="Troca de Óleo",
        descricao="Óleo sintético 5W30",
        preco_base=Decimal("180.00"),
        tempo_estimado_minutos=45,
    )
    assert servico.preco_base == Decimal("180.00")

    with pytest.raises(BusinessRuleException):
        Servico(nome="Oi", descricao="Curto", preco_base=Decimal("100.00"), tempo_estimado_minutos=30)

    with pytest.raises(BusinessRuleException):
        Servico(nome="Alinhamento", descricao="Desc", preco_base=Decimal("0.00"), tempo_estimado_minutos=30)

    with pytest.raises(BusinessRuleException):
        Servico(nome="Alinhamento", descricao="Desc", preco_base=Decimal("100.00"), tempo_estimado_minutos=0)


def test_controle_estoque_peca_e_validacoes():
    peca = Peca(
        nome="Filtro de Óleo",
        codigo_sku="FLT-001",
        preco_unitario=Decimal("45.90"),
        quantidade_estoque=10,
        estoque_minimo=5,
    )
    assert not peca.precisa_reposicao

    peca.baixar_estoque(6)
    assert peca.quantidade_estoque == 4
    assert peca.precisa_reposicao

    with pytest.raises(InsufficientStockException):
        peca.baixar_estoque(5)

    with pytest.raises(BusinessRuleException):
        peca.baixar_estoque(0)

    peca.repor_estoque(10)
    assert peca.quantidade_estoque == 14

    with pytest.raises(BusinessRuleException):
        peca.repor_estoque(0)

    with pytest.raises(BusinessRuleException):
        Peca(nome="", codigo_sku="SKU1", preco_unitario=Decimal("10"), quantidade_estoque=1)

    with pytest.raises(BusinessRuleException):
        Peca(nome="Peca", codigo_sku="", preco_unitario=Decimal("10"), quantidade_estoque=1)

    with pytest.raises(BusinessRuleException):
        Peca(nome="Peca", codigo_sku="SKU1", preco_unitario=Decimal("0"), quantidade_estoque=1)

    with pytest.raises(BusinessRuleException):
        Peca(nome="Peca", codigo_sku="SKU1", preco_unitario=Decimal("10"), quantidade_estoque=-1)


# ==========================================
# TESTES DO AGREGADO ORDEM DE SERVIÇO (OS)
# ==========================================
def test_fluxo_completo_ordem_servico_e_calculo_orcamento():
    os = OrdemServico(cliente_id=1, veiculo_id=1, observacoes="Barulho na suspensão")
    assert os.status == StatusOS.RECEBIDA
    assert os.tempo_execucao_minutos is None

    os.iniciar_diagnostico()
    assert os.status == StatusOS.EM_DIAGNOSTICO

    os.adicionar_servico(
        ItemServicoOS(servico_id=1, nome_servico="Alinhamento e Balanceamento", preco_unitario=Decimal("150.00"))
    )
    os.adicionar_peca(
        ItemPecaOS(peca_id=1, nome_peca="Bucha da Bandeja", preco_unitario=Decimal("80.00"), quantidade=2)
    )

    assert os.valor_total_servicos == Decimal("150.00")
    assert os.valor_total_pecas == Decimal("160.00")
    assert os.valor_total_orcamento == Decimal("310.00")

    os.disponibilizar_orcamento_para_aprovacao()
    assert os.status == StatusOS.AGUARDANDO_APROVACAO

    os.aprovar_orcamento()
    assert os.status == StatusOS.EM_EXECUCAO
    assert os.orcamento_aprovado is True
    assert os.data_inicio_execucao is not None

    os.data_inicio_execucao = datetime.now(timezone.utc) - timedelta(minutes=45)
    os.finalizar_servico()
    assert os.status == StatusOS.FINALIZADA
    assert os.tempo_execucao_minutos is not None
    assert os.tempo_execucao_minutos >= 44.9

    os.entregar_veiculo()
    assert os.status == StatusOS.ENTREGUE
    assert os.data_entrega is not None

    # Não deve permitir adicionar itens após entregue/finalizada
    with pytest.raises(BusinessRuleException):
        os.adicionar_servico(ItemServicoOS(servico_id=2, nome_servico="Lavagem", preco_unitario=Decimal("50.00")))

    with pytest.raises(BusinessRuleException):
        os.adicionar_peca(ItemPecaOS(peca_id=2, nome_peca="Cera", preco_unitario=Decimal("20.00"), quantidade=1))


def test_bloqueio_transicao_invalida_e_rejeicao_orcamento():
    os = OrdemServico(cliente_id=1, veiculo_id=1)

    with pytest.raises(InvalidStatusTransitionException):
        os.finalizar_servico()

    with pytest.raises(InvalidStatusTransitionException):
        os.aprovar_orcamento()

    with pytest.raises(InvalidStatusTransitionException):
        os.rejeitar_orcamento()

    with pytest.raises(BusinessRuleException):
        os.disponibilizar_orcamento_para_aprovacao()

    with pytest.raises(BusinessRuleException):
        ItemServicoOS(servico_id=1, nome_servico="Erro", preco_unitario=Decimal("10.00"), quantidade=0)

    with pytest.raises(BusinessRuleException):
        ItemPecaOS(peca_id=1, nome_peca="Erro", preco_unitario=Decimal("10.00"), quantidade=0)

    os.adicionar_servico(
        ItemServicoOS(servico_id=1, nome_servico="Troca de Óleo", preco_unitario=Decimal("120.00"))
    )
    os.disponibilizar_orcamento_para_aprovacao()

    # Tentar forçar status EM_EXECUCAO sem aprovar orçamento antes
    with pytest.raises(BusinessRuleException):
        os.alterar_status(StatusOS.EM_EXECUCAO)

    os.rejeitar_orcamento()
    assert os.status == StatusOS.CANCELADA
    assert os.orcamento_aprovado is False


if __name__ == "__main__":
    import subprocess
    raise SystemExit(
        subprocess.call(
            [sys.executable, "-m", "pytest", __file__, "-v", "--cov=app/domain", "--cov-report=term-missing"],
            cwd=str(ROOT_DIR),
        )
    )