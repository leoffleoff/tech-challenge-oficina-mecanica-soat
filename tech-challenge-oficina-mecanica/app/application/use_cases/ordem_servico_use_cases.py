import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.domain.entities.ordem_servico import ItemPecaOS, ItemServicoOS, OrdemServico
from app.domain.exceptions.domain_exceptions import (
    BusinessRuleException,
    EntityNotFoundException,
)
from app.domain.repositories.interfaces import (
    IClienteRepository,
    IOrdemServicoRepository,
    IPecaRepository,
    IServicoRepository,
    IVeiculoRepository,
)
from app.domain.value_objects.status_os import StatusOS


class OrdemServicoUseCase:
    """Orquestra os fluxos de negócio da Ordem de Serviço garantindo integridade de estoque e status."""

    def __init__(
        self,
        os_repo: IOrdemServicoRepository,
        cliente_repo: IClienteRepository,
        veiculo_repo: IVeiculoRepository,
        servico_repo: IServicoRepository,
        peca_repo: IPecaRepository,
    ):
        self.os_repo = os_repo
        self.cliente_repo = cliente_repo
        self.veiculo_repo = veiculo_repo
        self.servico_repo = servico_repo
        self.peca_repo = peca_repo

    def criar_ordem_servico(
        self,
        veiculo_id: int,
        cliente_id: Optional[int] = None,
        documento_cliente: Optional[str] = None,
        observacoes: Optional[str] = None,
        servicos_solicitados: Optional[List[Dict[str, int]]] = None,
        pecas_solicitadas: Optional[List[Dict[str, int]]] = None,
    ) -> OrdemServico:
        # 1. Identificar cliente por ID ou CPF/CNPJ
        cliente = None
        if cliente_id:
            cliente = self.cliente_repo.buscar_por_id(cliente_id)
        elif documento_cliente:
            cliente = self.cliente_repo.buscar_por_documento(documento_cliente)

        if not cliente:
            raise EntityNotFoundException("Cliente não encontrado para abertura da Ordem de Serviço.")

        # 2. Validar veículo e vínculo com o cliente
        veiculo = self.veiculo_repo.buscar_por_id(veiculo_id)
        if not veiculo:
            raise EntityNotFoundException(f"Veículo ID {veiculo_id} não encontrado.")
        if veiculo.cliente_id != cliente.id:
            raise BusinessRuleException("O veículo informado não pertence ao cliente selecionado.")

        nova_os = OrdemServico(
            cliente_id=cliente.id,
            veiculo_id=veiculo.id,
            observacoes=observacoes,
            status=StatusOS.RECEBIDA,
        )

        # 3. Incluir serviços solicitados
        for item_s in servicos_solicitados or []:
            servico = self.servico_repo.buscar_por_id(item_s["servico_id"])
            if not servico:
                raise EntityNotFoundException(f"Serviço ID {item_s['servico_id']} não encontrado.")
            nova_os.adicionar_servico(
                ItemServicoOS(
                    servico_id=servico.id,
                    nome_servico=servico.nome,
                    preco_unitario=servico.preco_base,
                    quantidade=item_s.get("quantidade", 1),
                )
            )

        # 4. Incluir peças/insumos e reservar/baixar no estoque
        pecas_para_atualizar = []
        for item_p in pecas_solicitadas or []:
            peca = self.peca_repo.buscar_por_id(item_p["peca_id"])
            if not peca:
                raise EntityNotFoundException(f"Peça ID {item_p['peca_id']} não encontrada.")
            qtd = item_p.get("quantidade", 1)
            peca.baixar_estoque(qtd)
            pecas_para_atualizar.append(peca)

            nova_os.adicionar_peca(
                ItemPecaOS(
                    peca_id=peca.id,
                    nome_peca=peca.nome,
                    preco_unitario=peca.preco_unitario,
                    quantidade=qtd,
                )
            )

        for peca in pecas_para_atualizar:
            self.peca_repo.atualizar(peca)

        # Se já nasceu com itens e orçamento calculado, disponibiliza automaticamente para aprovação do cliente
        if nova_os.servicos or nova_os.pecas:
            nova_os.disponibilizar_orcamento_para_aprovacao()

        return self.os_repo.criar(nova_os)

    def adicionar_itens_os(
        self,
        os_id: int,
        servicos_solicitados: Optional[List[Dict[str, int]]] = None,
        pecas_solicitadas: Optional[List[Dict[str, int]]] = None,
    ) -> OrdemServico:
        os_entity = self.buscar_por_id(os_id)

        for item_s in servicos_solicitados or []:
            servico = self.servico_repo.buscar_por_id(item_s["servico_id"])
            if not servico:
                raise EntityNotFoundException(f"Serviço ID {item_s['servico_id']} não encontrado.")
            os_entity.adicionar_servico(
                ItemServicoOS(
                    servico_id=servico.id,
                    nome_servico=servico.nome,
                    preco_unitario=servico.preco_base,
                    quantidade=item_s.get("quantidade", 1),
                )
            )

        pecas_para_atualizar = []
        for item_p in pecas_solicitadas or []:
            peca = self.peca_repo.buscar_por_id(item_p["peca_id"])
            if not peca:
                raise EntityNotFoundException(f"Peça ID {item_p['peca_id']} não encontrada.")
            qtd = item_p.get("quantidade", 1)
            peca.baixar_estoque(qtd)
            pecas_para_atualizar.append(peca)
            os_entity.adicionar_peca(
                ItemPecaOS(
                    peca_id=peca.id,
                    nome_peca=peca.nome,
                    preco_unitario=peca.preco_unitario,
                    quantidade=qtd,
                )
            )

        for peca in pecas_para_atualizar:
            self.peca_repo.atualizar(peca)

        return self.os_repo.atualizar(os_entity)

    def buscar_por_id(self, os_id: int) -> OrdemServico:
        os_entity = self.os_repo.buscar_por_id(os_id)
        if not os_entity:
            raise EntityNotFoundException(f"Ordem de Serviço ID {os_id} não encontrada.")
        return os_entity

    def atualizar_status(self, os_id: int, novo_status: StatusOS) -> OrdemServico:
        os_entity = self.buscar_por_id(os_id)
        os_entity.alterar_status(novo_status)
        return self.os_repo.atualizar(os_entity)

    def processar_decisao_orcamento(self, os_id: int, aprovado: bool) -> OrdemServico:
        os_entity = self.buscar_por_id(os_id)
        if aprovado:
            os_entity.aprovar_orcamento()
        else:
            os_entity.rejeitar_orcamento()
            # Estorna as peças reservadas de volta para o estoque
            for item_peca in os_entity.pecas:
                peca = self.peca_repo.buscar_por_id(item_peca.peca_id)
                if peca:
                    peca.repor_estoque(item_peca.quantidade)
                    self.peca_repo.atualizar(peca)

        return self.os_repo.atualizar(os_entity)

    def calcular_metricas_tempo_execucao(self) -> Dict[str, Any]:
        todas = self.os_repo.listar_todas()
        tempos = [os.tempo_execucao_minutos for os in todas if os.tempo_execucao_minutos is not None]

        por_status: Dict[str, int] = {}
        faturamento_total = Decimal("0.00")
        for os in todas:
            por_status[os.status.value] = por_status.get(os.status.value, 0) + 1
            if os.status in {StatusOS.FINALIZADA, StatusOS.ENTREGUE}:
                faturamento_total += os.valor_total_orcamento

        media_minutos = round(sum(tempos) / len(tempos), 2) if tempos else 0.0
        return {
            "total_ordens_servico": len(todas),
            "ordens_finalizadas_com_tempo_medido": len(tempos),
            "tempo_medio_execucao_minutos": media_minutos,
            "faturamento_ordens_concluidas": faturamento_total,
            "distribuicao_por_status": por_status,
        }