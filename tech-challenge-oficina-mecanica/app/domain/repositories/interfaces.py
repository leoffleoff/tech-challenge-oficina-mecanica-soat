from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.cliente import Cliente
from app.domain.entities.veiculo import Veiculo
from app.domain.entities.servico import Servico
from app.domain.entities.peca import Peca
from app.domain.entities.ordem_servico import OrdemServico


class IClienteRepository(ABC):
    @abstractmethod
    def criar(self, cliente: Cliente) -> Cliente:
        pass

    @abstractmethod
    def buscar_por_id(self, cliente_id: int) -> Optional[Cliente]:
        pass

    @abstractmethod
    def buscar_por_documento(self, documento: str) -> Optional[Cliente]:
        pass

    @abstractmethod
    def listar_todos(self) -> List[Cliente]:
        pass

    @abstractmethod
    def atualizar(self, cliente: Cliente) -> Cliente:
        pass

    @abstractmethod
    def deletar(self, cliente_id: int) -> bool:
        pass


class IVeiculoRepository(ABC):
    @abstractmethod
    def criar(self, veiculo: Veiculo) -> Veiculo:
        pass

    @abstractmethod
    def buscar_por_id(self, veiculo_id: int) -> Optional[Veiculo]:
        pass

    @abstractmethod
    def buscar_por_placa(self, placa: str) -> Optional[Veiculo]:
        pass

    @abstractmethod
    def listar_todos(self) -> List[Veiculo]:
        pass

    @abstractmethod
    def atualizar(self, veiculo: Veiculo) -> Veiculo:
        pass

    @abstractmethod
    def deletar(self, veiculo_id: int) -> bool:
        pass


class IServicoRepository(ABC):
    @abstractmethod
    def criar(self, servico: Servico) -> Servico:
        pass

    @abstractmethod
    def buscar_por_id(self, servico_id: int) -> Optional[Servico]:
        pass

    @abstractmethod
    def listar_todos(self) -> List[Servico]:
        pass

    @abstractmethod
    def atualizar(self, servico: Servico) -> Servico:
        pass

    @abstractmethod
    def deletar(self, servico_id: int) -> bool:
        pass


class IPecaRepository(ABC):
    @abstractmethod
    def criar(self, peca: Peca) -> Peca:
        pass

    @abstractmethod
    def buscar_por_id(self, peca_id: int) -> Optional[Peca]:
        pass

    @abstractmethod
    def buscar_por_sku(self, codigo_sku: str) -> Optional[Peca]:
        pass

    @abstractmethod
    def listar_todos(self) -> List[Peca]:
        pass

    @abstractmethod
    def atualizar(self, peca: Peca) -> Peca:
        pass

    @abstractmethod
    def deletar(self, peca_id: int) -> bool:
        pass


class IOrdemServicoRepository(ABC):
    @abstractmethod
    def criar(self, os: OrdemServico) -> OrdemServico:
        pass

    @abstractmethod
    def buscar_por_id(self, os_id: int) -> Optional[OrdemServico]:
        pass

    @abstractmethod
    def listar_todas(self) -> List[OrdemServico]:
        pass

    @abstractmethod
    def listar_por_documento_cliente(self, documento: str) -> List[OrdemServico]:
        pass

    @abstractmethod
    def atualizar(self, os: OrdemServico) -> OrdemServico:
        pass