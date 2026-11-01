import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.domain.value_objects.status_os import StatusOS


# ==================== AUTH ====================
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ==================== CLIENTE ====================
class ClienteCreate(BaseModel):
    nome: str = Field(..., examples=["Leonardo Santos"])
    documento: str = Field(..., description="CPF (11 dígitos) ou CNPJ (14 dígitos)", examples=["52998224725"])
    telefone: str = Field(..., examples=["11988887777"])
    email: str = Field(..., examples=["leonardo@email.com"])
    endereco: Optional[str] = Field(None, examples=["Av. Paulista, 1000 - São Paulo/SP"])


class ClienteUpdate(BaseModel):
    nome: str
    telefone: str
    email: str
    endereco: Optional[str] = None


class ClienteResponse(BaseModel):
    id: int
    nome: str
    documento: str
    documento_formatado: str
    tipo_documento: str
    telefone: str
    email: str
    endereco: Optional[str] = None
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== VEÍCULO ====================
class VeiculoCreate(BaseModel):
    placa: str = Field(..., description="Padrão Antigo (ABC1234) ou Mercosul (BRA2E19)", examples=["BRA2E19"])
    marca: str = Field(..., examples=["Toyota"])
    modelo: str = Field(..., examples=["Corolla XEi"])
    ano: int = Field(..., examples=[2024])
    cor: Optional[str] = Field(None, examples=["Prata"])
    cliente_id: int = Field(..., examples=[1])


class VeiculoUpdate(BaseModel):
    placa: str
    marca: str
    modelo: str
    ano: int
    cor: Optional[str] = None
    cliente_id: int


class VeiculoResponse(BaseModel):
    id: int
    placa: str
    placa_formatada: str
    is_mercosul: bool
    marca: str
    modelo: str
    ano: int
    cor: Optional[str] = None
    cliente_id: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== SERVIÇO ====================
class ServicoCreate(BaseModel):
    nome: str = Field(..., examples=["Troca de Óleo e Filtro"])
    descricao: str = Field(..., examples=["Substituição de óleo sintético 5W30 e filtro de óleo"])
    preco_base: Decimal = Field(..., examples=[Decimal("180.00")])
    tempo_estimado_minutos: int = Field(..., examples=[45])


class ServicoResponse(ServicoCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ==================== PEÇA / INSUMO ====================
class PecaCreate(BaseModel):
    nome: str = Field(..., examples=["Pastilha de Freio Dianteira"])
    codigo_sku: str = Field(..., examples=["FRE-PST-001"])
    preco_unitario: Decimal = Field(..., examples=[Decimal("145.50")])
    quantidade_estoque: int = Field(..., examples=[20])
    estoque_minimo: int = Field(5, examples=[5])


class PecaUpdate(BaseModel):
    nome: str
    codigo_sku: str
    preco_unitario: Decimal
    quantidade_estoque: int
    estoque_minimo: int = 5


class MovimentacaoEstoqueRequest(BaseModel):
    quantidade: int = Field(..., gt=0, description="Quantidade a repor ou dar baixa no estoque", examples=[10])


class PecaResponse(PecaCreate):
    id: int
    precisa_reposicao: bool
    model_config = ConfigDict(from_attributes=True)


# ==================== ORDEM DE SERVIÇO (OS) ====================
class ItemServicoRequest(BaseModel):
    servico_id: int = Field(..., examples=[1])
    quantidade: int = Field(1, gt=0, examples=[1])


class ItemPecaRequest(BaseModel):
    peca_id: int = Field(..., examples=[1])
    quantidade: int = Field(1, gt=0, examples=[2])


class OrdemServicoCreate(BaseModel):
    cliente_id: Optional[int] = Field(None, description="ID do cliente (opcional se informar documento_cliente)", examples=[1])
    documento_cliente: Optional[str] = Field(None, description="CPF ou CNPJ do cliente", examples=["52998224725"])
    veiculo_id: int = Field(..., examples=[1])
    observacoes: Optional[str] = Field(None, examples=["Revisão de freios e alinhamento"])
    servicos: List[ItemServicoRequest] = Field(default_factory=list)
    pecas: List[ItemPecaRequest] = Field(default_factory=list)


class AdicionarItensOSRequest(BaseModel):
    servicos: List[ItemServicoRequest] = Field(default_factory=list)
    pecas: List[ItemPecaRequest] = Field(default_factory=list)


class AtualizarStatusOSRequest(BaseModel):
    novo_status: StatusOS = Field(..., examples=[StatusOS.EM_DIAGNOSTICO])


class AprovacaoOrcamentoRequest(BaseModel):
    aprovado: bool = Field(..., description="True para aprovar o orçamento e iniciar execução; False para rejeitar/cancelar")


class ItemServicoOSResponse(BaseModel):
    servico_id: int
    nome_servico: str
    preco_unitario: Decimal
    quantidade: int
    subtotal: Decimal


class ItemPecaOSResponse(BaseModel):
    peca_id: int
    nome_peca: str
    preco_unitario: Decimal
    quantidade: int
    subtotal: Decimal


class OrdemServicoResponse(BaseModel):
    id: int
    cliente_id: int
    veiculo_id: int
    observacoes: Optional[str] = None
    status: StatusOS
    orcamento_aprovado: Optional[bool] = None
    valor_total_servicos: Decimal
    valor_total_pecas: Decimal
    valor_total_orcamento: Decimal
    servicos: List[ItemServicoOSResponse]
    pecas: List[ItemPecaOSResponse]
    data_abertura: datetime
    data_inicio_execucao: Optional[datetime] = None
    data_finalizacao: Optional[datetime] = None
    data_entrega: Optional[datetime] = None
    tempo_execucao_minutos: Optional[float] = None


class MetricasTempoExecucaoResponse(BaseModel):
    total_ordens_servico: int
    ordens_finalizadas_com_tempo_medido: int
    tempo_medio_execucao_minutos: float
    faturamento_ordens_concluidas: Decimal
    distribuicao_por_status: Dict[str, int]