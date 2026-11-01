from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from app.domain.value_objects.status_os import StatusOS
from app.domain.exceptions.domain_exceptions import (
    BusinessRuleException,
    InvalidStatusTransitionException,
)


@dataclass
class ItemServicoOS:
    servico_id: int
    nome_servico: str
    preco_unitario: Decimal
    quantidade: int = 1
    id: Optional[int] = None

    def __post_init__(self):
        self.preco_unitario = Decimal(str(self.preco_unitario))
        if self.quantidade <= 0:
            raise BusinessRuleException("A quantidade do serviço deve ser maior que zero.")
        if self.preco_unitario <= Decimal("0.00"):
            raise BusinessRuleException("O valor do serviço na OS deve ser maior que zero.")

    @property
    def subtotal(self) -> Decimal:
        return self.preco_unitario * Decimal(self.quantidade)


@dataclass
class ItemPecaOS:
    peca_id: int
    nome_peca: str
    preco_unitario: Decimal
    quantidade: int
    id: Optional[int] = None

    def __post_init__(self):
        self.preco_unitario = Decimal(str(self.preco_unitario))
        if self.quantidade <= 0:
            raise BusinessRuleException("A quantidade de peças na OS deve ser maior que zero.")
        if self.preco_unitario <= Decimal("0.00"):
            raise BusinessRuleException("O valor unitário da peça na OS deve ser maior que zero.")

    @property
    def subtotal(self) -> Decimal:
        return self.preco_unitario * Decimal(self.quantidade)


@dataclass
class OrdemServico:
    """Aggregate Root responsável pelo ciclo de vida completo da Ordem de Serviço."""
    cliente_id: int
    veiculo_id: int
    observacoes: Optional[str] = None
    status: StatusOS = StatusOS.RECEBIDA
    orcamento_aprovado: Optional[bool] = None
    servicos: List[ItemServicoOS] = field(default_factory=list)
    pecas: List[ItemPecaOS] = field(default_factory=list)
    id: Optional[int] = None
    data_abertura: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data_inicio_execucao: Optional[datetime] = None
    data_finalizacao: Optional[datetime] = None
    data_entrega: Optional[datetime] = None

    def adicionar_servico(self, item: ItemServicoOS) -> None:
        if self.status in {StatusOS.FINALIZADA, StatusOS.ENTREGUE, StatusOS.CANCELADA}:
            raise BusinessRuleException(
                f"Não é permitido adicionar serviços com a OS no status '{self.status.value}'."
            )
        self.servicos.append(item)

    def adicionar_peca(self, item: ItemPecaOS) -> None:
        if self.status in {StatusOS.FINALIZADA, StatusOS.ENTREGUE, StatusOS.CANCELADA}:
            raise BusinessRuleException(
                f"Não é permitido adicionar peças com a OS no status '{self.status.value}'."
            )
        self.pecas.append(item)

    @property
    def valor_total_servicos(self) -> Decimal:
        return sum((s.subtotal for s in self.servicos), Decimal("0.00"))

    @property
    def valor_total_pecas(self) -> Decimal:
        return sum((p.subtotal for p in self.pecas), Decimal("0.00"))

    @property
    def valor_total_orcamento(self) -> Decimal:
        return self.valor_total_servicos + self.valor_total_pecas

    def alterar_status(self, novo_status: StatusOS) -> None:
        if not StatusOS.can_transition(self.status, novo_status):
            raise InvalidStatusTransitionException(
                f"Transição de status inválida: de '{self.status.value}' para '{novo_status.value}'."
            )

        agora = datetime.now(timezone.utc)

        if novo_status == StatusOS.AGUARDANDO_APROVACAO:
            if not self.servicos and not self.pecas:
                raise BusinessRuleException(
                    "A OS precisa ter ao menos um serviço ou peça para enviar orçamento para aprovação."
                )

        if novo_status == StatusOS.EM_EXECUCAO:
            if self.orcamento_aprovado is not True:
                raise BusinessRuleException(
                    "A OS só pode entrar 'Em execução' após a aprovação do orçamento pelo cliente."
                )
            if not self.data_inicio_execucao:
                self.data_inicio_execucao = agora

        if novo_status == StatusOS.FINALIZADA:
            self.data_finalizacao = agora

        if novo_status == StatusOS.ENTREGUE:
            self.data_entrega = agora

        self.status = novo_status

    def iniciar_diagnostico(self) -> None:
        self.alterar_status(StatusOS.EM_DIAGNOSTICO)

    def disponibilizar_orcamento_para_aprovacao(self) -> None:
        self.orcamento_aprovado = None
        self.alterar_status(StatusOS.AGUARDANDO_APROVACAO)

    def aprovar_orcamento(self) -> None:
        if self.status != StatusOS.AGUARDANDO_APROVACAO:
            raise InvalidStatusTransitionException(
                "O orçamento só pode ser aprovado quando a OS está 'Aguardando aprovação'."
            )
        self.orcamento_aprovado = True
        self.alterar_status(StatusOS.EM_EXECUCAO)

    def rejeitar_orcamento(self) -> None:
        if self.status != StatusOS.AGUARDANDO_APROVACAO:
            raise InvalidStatusTransitionException(
                "O orçamento só pode ser rejeitado quando a OS está 'Aguardando aprovação'."
            )
        self.orcamento_aprovado = False
        self.alterar_status(StatusOS.CANCELADA)

    def finalizar_servico(self) -> None:
        self.alterar_status(StatusOS.FINALIZADA)

    def entregar_veiculo(self) -> None:
        self.alterar_status(StatusOS.ENTREGUE)

    @property
    def tempo_execucao_minutos(self) -> Optional[float]:
        """Calcula o tempo de execução real entre início da execução e finalização."""
        if self.data_inicio_execucao and self.data_finalizacao:
            delta = self.data_finalizacao - self.data_inicio_execucao
            return round(delta.total_seconds() / 60.0, 2)
        return None