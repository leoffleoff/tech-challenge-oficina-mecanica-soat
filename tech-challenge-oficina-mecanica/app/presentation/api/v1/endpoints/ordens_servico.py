import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[5]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.application.use_cases.ordem_servico_use_cases import OrdemServicoUseCase
from app.domain.entities.ordem_servico import OrdemServico
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.sqlalchemy_repositories import (
    SQLAlchemyClienteRepository,
    SQLAlchemyOrdemServicoRepository,
    SQLAlchemyPecaRepository,
    SQLAlchemyServicoRepository,
    SQLAlchemyVeiculoRepository,
)
from app.presentation.dependencies.auth import get_current_admin
from app.presentation.schemas.schemas import (
    AdicionarItensOSRequest,
    AprovacaoOrcamentoRequest,
    AtualizarStatusOSRequest,
    ItemPecaOSResponse,
    ItemServicoOSResponse,
    MetricasTempoExecucaoResponse,
    OrdemServicoCreate,
    OrdemServicoResponse,
)

router_admin = APIRouter(
    prefix="/ordens-servico",
    tags=["6. Gestão de Ordens de Serviço e Métricas (Admin)"],
    dependencies=[Depends(get_current_admin)],
)

router_publico = APIRouter(
    prefix="/publico/ordens-servico",
    tags=["7. Acompanhamento e Aprovação pelo Cliente (API Pública)"],
)


def _get_use_case(db: Session = Depends(get_db)) -> OrdemServicoUseCase:
    return OrdemServicoUseCase(
        os_repo=SQLAlchemyOrdemServicoRepository(db),
        cliente_repo=SQLAlchemyClienteRepository(db),
        veiculo_repo=SQLAlchemyVeiculoRepository(db),
        servico_repo=SQLAlchemyServicoRepository(db),
        peca_repo=SQLAlchemyPecaRepository(db),
    )


def _map_os_response(os: OrdemServico) -> OrdemServicoResponse:
    return OrdemServicoResponse(
        id=os.id,
        cliente_id=os.cliente_id,
        veiculo_id=os.veiculo_id,
        observacoes=os.observacoes,
        status=os.status,
        orcamento_aprovado=os.orcamento_aprovado,
        valor_total_servicos=os.valor_total_servicos,
        valor_total_pecas=os.valor_total_pecas,
        valor_total_orcamento=os.valor_total_orcamento,
        servicos=[
            ItemServicoOSResponse(
                servico_id=s.servico_id,
                nome_servico=s.nome_servico,
                preco_unitario=s.preco_unitario,
                quantidade=s.quantidade,
                subtotal=s.subtotal,
            )
            for s in os.servicos
        ],
        pecas=[
            ItemPecaOSResponse(
                peca_id=p.peca_id,
                nome_peca=p.nome_peca,
                preco_unitario=p.preco_unitario,
                quantidade=p.quantidade,
                subtotal=p.subtotal,
            )
            for p in os.pecas
        ],
        data_abertura=os.data_abertura,
        data_inicio_execucao=os.data_inicio_execucao,
        data_finalizacao=os.data_finalizacao,
        data_entrega=os.data_entrega,
        tempo_execucao_minutos=os.tempo_execucao_minutos,
    )


# ==================== ROTAS ADMINISTRATIVAS ====================
@router_admin.post(
    "",
    response_model=OrdemServicoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir nova Ordem de Serviço com cálculo automático de orçamento",
)
def criar_ordem_servico(
    payload: OrdemServicoCreate,
    use_case: OrdemServicoUseCase = Depends(_get_use_case),
):
    os_criada = use_case.criar_ordem_servico(
        veiculo_id=payload.veiculo_id,
        cliente_id=payload.cliente_id,
        documento_cliente=payload.documento_cliente,
        observacoes=payload.observacoes,
        servicos_solicitados=[s.model_dump() for s in payload.servicos],
        pecas_solicitadas=[p.model_dump() for p in payload.pecas],
    )
    return _map_os_response(os_criada)


@router_admin.get(
    "/metricas/tempo-medio",
    response_model=MetricasTempoExecucaoResponse,
    summary="Monitorar tempo médio de execução dos serviços e indicadores de OS",
)
def obter_metricas_tempo_medio(use_case: OrdemServicoUseCase = Depends(_get_use_case)):
    return use_case.calcular_metricas_tempo_execucao()


@router_admin.get("", response_model=List[OrdemServicoResponse], summary="Listar todas as Ordens de Serviço")
def listar_ordens_servico(use_case: OrdemServicoUseCase = Depends(_get_use_case)):
    return [_map_os_response(os) for os in use_case.os_repo.listar_todas()]


@router_admin.get("/{os_id}", response_model=OrdemServicoResponse, summary="Detalhar Ordem de Serviço por ID")
def detalhar_ordem_servico(os_id: int, use_case: OrdemServicoUseCase = Depends(_get_use_case)):
    return _map_os_response(use_case.buscar_por_id(os_id))


@router_admin.post(
    "/{os_id}/itens",
    response_model=OrdemServicoResponse,
    summary="Incluir novos serviços ou peças após diagnóstico",
)
def adicionar_itens_ordem_servico(
    os_id: int,
    payload: AdicionarItensOSRequest,
    use_case: OrdemServicoUseCase = Depends(_get_use_case),
):
    os_atualizada = use_case.adicionar_itens_os(
        os_id=os_id,
        servicos_solicitados=[s.model_dump() for s in payload.servicos],
        pecas_solicitadas=[p.model_dump() for p in payload.pecas],
    )
    return _map_os_response(os_atualizada)


@router_admin.patch(
    "/{os_id}/status",
    response_model=OrdemServicoResponse,
    summary="Alterar status da Ordem de Serviço (respeitando máquina de estados)",
)
def atualizar_status_ordem_servico(
    os_id: int,
    payload: AtualizarStatusOSRequest,
    use_case: OrdemServicoUseCase = Depends(_get_use_case),
):
    return _map_os_response(use_case.atualizar_status(os_id, payload.novo_status))


# ==================== ROTAS PÚBLICAS DO CLIENTE ====================
@router_publico.get(
    "/{os_id}",
    response_model=OrdemServicoResponse,
    summary="Consultar andamento e orçamento da OS pelo número",
)
def consultar_os_cliente(os_id: int, use_case: OrdemServicoUseCase = Depends(_get_use_case)):
    return _map_os_response(use_case.buscar_por_id(os_id))


@router_publico.get(
    "/cliente/{documento}",
    response_model=List[OrdemServicoResponse],
    summary="Listar todas as Ordens de Serviço de um cliente pelo CPF ou CNPJ",
)
def consultar_os_por_documento_cliente(
    documento: str,
    use_case: OrdemServicoUseCase = Depends(_get_use_case),
):
    lista = use_case.os_repo.listar_por_documento_cliente(documento)
    return [_map_os_response(os) for os in lista]


@router_publico.post(
    "/{os_id}/avaliar-orcamento",
    response_model=OrdemServicoResponse,
    summary="Aprovar ou rejeitar orçamento da Ordem de Serviço",
)
def avaliar_orcamento_pelo_cliente(
    os_id: int,
    payload: AprovacaoOrcamentoRequest,
    use_case: OrdemServicoUseCase = Depends(_get_use_case),
):
    os_atualizada = use_case.processar_decisao_orcamento(os_id, payload.aprovado)
    return _map_os_response(os_atualizada)