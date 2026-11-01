import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import re
from datetime import timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session

from app.domain.entities.cliente import Cliente
from app.domain.entities.veiculo import Veiculo
from app.domain.entities.servico import Servico
from app.domain.entities.peca import Peca
from app.domain.entities.ordem_servico import ItemPecaOS, ItemServicoOS, OrdemServico
from app.domain.value_objects.cpf_cnpj import CpfCnpj
from app.domain.value_objects.placa import Placa
from app.domain.value_objects.status_os import StatusOS
from app.domain.repositories.interfaces import (
    IClienteRepository,
    IVeiculoRepository,
    IServicoRepository,
    IPecaRepository,
    IOrdemServicoRepository,
)
from app.infrastructure.database.models import (
    ClienteModel,
    VeiculoModel,
    ServicoModel,
    PecaModel,
    OrdemServicoModel,
    ItemServicoOSModel,
    ItemPecaOSModel,
)


def _ensure_utc(dt):
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class SQLAlchemyClienteRepository(IClienteRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_entity(model: ClienteModel) -> Cliente:
        return Cliente(
            id=model.id,
            nome=model.nome,
            documento=CpfCnpj(model.documento),
            telefone=model.telefone,
            email=model.email,
            endereco=model.endereco,
            criado_em=_ensure_utc(model.criado_em),
        )

    def criar(self, cliente: Cliente) -> Cliente:
        model = ClienteModel(
            nome=cliente.nome,
            documento=cliente.documento.value,
            telefone=cliente.telefone,
            email=cliente.email,
            endereco=cliente.endereco,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def buscar_por_id(self, cliente_id: int) -> Optional[Cliente]:
        model = self.db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
        return self._to_entity(model) if model else None

    def buscar_por_documento(self, documento: str) -> Optional[Cliente]:
        cleaned = re.sub(r"\D", "", documento or "")
        model = self.db.query(ClienteModel).filter(ClienteModel.documento == cleaned).first()
        return self._to_entity(model) if model else None

    def listar_todos(self) -> List[Cliente]:
        models = self.db.query(ClienteModel).order_by(ClienteModel.id).all()
        return [self._to_entity(m) for m in models]

    def atualizar(self, cliente: Cliente) -> Cliente:
        model = self.db.query(ClienteModel).filter(ClienteModel.id == cliente.id).first()
        model.nome = cliente.nome
        model.documento = cliente.documento.value
        model.telefone = cliente.telefone
        model.email = cliente.email
        model.endereco = cliente.endereco
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def deletar(self, cliente_id: int) -> bool:
        model = self.db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True


class SQLAlchemyVeiculoRepository(IVeiculoRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_entity(model: VeiculoModel) -> Veiculo:
        return Veiculo(
            id=model.id,
            placa=Placa(model.placa),
            marca=model.marca,
            modelo=model.modelo,
            ano=model.ano,
            cor=model.cor,
            cliente_id=model.cliente_id,
            criado_em=_ensure_utc(model.criado_em),
        )

    def criar(self, veiculo: Veiculo) -> Veiculo:
        model = VeiculoModel(
            placa=veiculo.placa.value,
            marca=veiculo.marca,
            modelo=veiculo.modelo,
            ano=veiculo.ano,
            cor=veiculo.cor,
            cliente_id=veiculo.cliente_id,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def buscar_por_id(self, veiculo_id: int) -> Optional[Veiculo]:
        model = self.db.query(VeiculoModel).filter(VeiculoModel.id == veiculo_id).first()
        return self._to_entity(model) if model else None

    def buscar_por_placa(self, placa: str) -> Optional[Veiculo]:
        cleaned = re.sub(r"[^A-Za-z0-9]", "", placa or "").upper()
        model = self.db.query(VeiculoModel).filter(VeiculoModel.placa == cleaned).first()
        return self._to_entity(model) if model else None

    def listar_todos(self) -> List[Veiculo]:
        models = self.db.query(VeiculoModel).order_by(VeiculoModel.id).all()
        return [self._to_entity(m) for m in models]

    def atualizar(self, veiculo: Veiculo) -> Veiculo:
        model = self.db.query(VeiculoModel).filter(VeiculoModel.id == veiculo.id).first()
        model.placa = veiculo.placa.value
        model.marca = veiculo.marca
        model.modelo = veiculo.modelo
        model.ano = veiculo.ano
        model.cor = veiculo.cor
        model.cliente_id = veiculo.cliente_id
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def deletar(self, veiculo_id: int) -> bool:
        model = self.db.query(VeiculoModel).filter(VeiculoModel.id == veiculo_id).first()
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True


class SQLAlchemyServicoRepository(IServicoRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_entity(model: ServicoModel) -> Servico:
        return Servico(
            id=model.id,
            nome=model.nome,
            descricao=model.descricao,
            preco_base=Decimal(str(model.preco_base)),
            tempo_estimado_minutos=model.tempo_estimado_minutos,
        )

    def criar(self, servico: Servico) -> Servico:
        model = ServicoModel(
            nome=servico.nome,
            descricao=servico.descricao,
            preco_base=servico.preco_base,
            tempo_estimado_minutos=servico.tempo_estimado_minutos,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def buscar_por_id(self, servico_id: int) -> Optional[Servico]:
        model = self.db.query(ServicoModel).filter(ServicoModel.id == servico_id).first()
        return self._to_entity(model) if model else None

    def listar_todos(self) -> List[Servico]:
        models = self.db.query(ServicoModel).order_by(ServicoModel.id).all()
        return [self._to_entity(m) for m in models]

    def atualizar(self, servico: Servico) -> Servico:
        model = self.db.query(ServicoModel).filter(ServicoModel.id == servico.id).first()
        model.nome = servico.nome
        model.descricao = servico.descricao
        model.preco_base = servico.preco_base
        model.tempo_estimado_minutos = servico.tempo_estimado_minutos
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def deletar(self, servico_id: int) -> bool:
        model = self.db.query(ServicoModel).filter(ServicoModel.id == servico_id).first()
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True


class SQLAlchemyPecaRepository(IPecaRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_entity(model: PecaModel) -> Peca:
        return Peca(
            id=model.id,
            nome=model.nome,
            codigo_sku=model.codigo_sku,
            preco_unitario=Decimal(str(model.preco_unitario)),
            quantidade_estoque=model.quantidade_estoque,
            estoque_minimo=model.estoque_minimo,
        )

    def criar(self, peca: Peca) -> Peca:
        model = PecaModel(
            nome=peca.nome,
            codigo_sku=peca.codigo_sku,
            preco_unitario=peca.preco_unitario,
            quantidade_estoque=peca.quantidade_estoque,
            estoque_minimo=peca.estoque_minimo,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def buscar_por_id(self, peca_id: int) -> Optional[Peca]:
        model = self.db.query(PecaModel).filter(PecaModel.id == peca_id).first()
        return self._to_entity(model) if model else None

    def buscar_por_sku(self, codigo_sku: str) -> Optional[Peca]:
        model = self.db.query(PecaModel).filter(PecaModel.codigo_sku == codigo_sku).first()
        return self._to_entity(model) if model else None

    def listar_todos(self) -> List[Peca]:
        models = self.db.query(PecaModel).order_by(PecaModel.id).all()
        return [self._to_entity(m) for m in models]

    def atualizar(self, peca: Peca) -> Peca:
        model = self.db.query(PecaModel).filter(PecaModel.id == peca.id).first()
        model.nome = peca.nome
        model.codigo_sku = peca.codigo_sku
        model.preco_unitario = peca.preco_unitario
        model.quantidade_estoque = peca.quantidade_estoque
        model.estoque_minimo = peca.estoque_minimo
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def deletar(self, peca_id: int) -> bool:
        model = self.db.query(PecaModel).filter(PecaModel.id == peca_id).first()
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True


class SQLAlchemyOrdemServicoRepository(IOrdemServicoRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_entity(model: OrdemServicoModel) -> OrdemServico:
        servicos = [
            ItemServicoOS(
                id=s.id,
                servico_id=s.servico_id,
                nome_servico=s.nome_servico,
                preco_unitario=Decimal(str(s.preco_unitario)),
                quantidade=s.quantidade,
            )
            for s in model.servicos
        ]
        pecas = [
            ItemPecaOS(
                id=p.id,
                peca_id=p.peca_id,
                nome_peca=p.nome_peca,
                preco_unitario=Decimal(str(p.preco_unitario)),
                quantidade=p.quantidade,
            )
            for p in model.pecas
        ]
        return OrdemServico(
            id=model.id,
            cliente_id=model.cliente_id,
            veiculo_id=model.veiculo_id,
            observacoes=model.observacoes,
            status=StatusOS(model.status),
            orcamento_aprovado=model.orcamento_aprovado,
            servicos=servicos,
            pecas=pecas,
            data_abertura=_ensure_utc(model.data_abertura),
            data_inicio_execucao=_ensure_utc(model.data_inicio_execucao),
            data_finalizacao=_ensure_utc(model.data_finalizacao),
            data_entrega=_ensure_utc(model.data_entrega),
        )

    def criar(self, os: OrdemServico) -> OrdemServico:
        model = OrdemServicoModel(
            cliente_id=os.cliente_id,
            veiculo_id=os.veiculo_id,
            observacoes=os.observacoes,
            status=os.status.value,
            orcamento_aprovado=os.orcamento_aprovado,
            data_abertura=os.data_abertura,
            data_inicio_execucao=os.data_inicio_execucao,
            data_finalizacao=os.data_finalizacao,
            data_entrega=os.data_entrega,
        )
        for s in os.servicos:
            model.servicos.append(
                ItemServicoOSModel(
                    servico_id=s.servico_id,
                    nome_servico=s.nome_servico,
                    preco_unitario=s.preco_unitario,
                    quantidade=s.quantidade,
                )
            )
        for p in os.pecas:
            model.pecas.append(
                ItemPecaOSModel(
                    peca_id=p.peca_id,
                    nome_peca=p.nome_peca,
                    preco_unitario=p.preco_unitario,
                    quantidade=p.quantidade,
                )
            )

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def buscar_por_id(self, os_id: int) -> Optional[OrdemServico]:
        model = self.db.query(OrdemServicoModel).filter(OrdemServicoModel.id == os_id).first()
        return self._to_entity(model) if model else None

    def listar_todas(self) -> List[OrdemServico]:
        models = self.db.query(OrdemServicoModel).order_by(OrdemServicoModel.id.desc()).all()
        return [self._to_entity(m) for m in models]

    def listar_por_documento_cliente(self, documento: str) -> List[OrdemServico]:
        cleaned = re.sub(r"\D", "", documento or "")
        models = (
            self.db.query(OrdemServicoModel)
            .join(ClienteModel, OrdemServicoModel.cliente_id == ClienteModel.id)
            .filter(ClienteModel.documento == cleaned)
            .order_by(OrdemServicoModel.id.desc())
            .all()
        )
        return [self._to_entity(m) for m in models]

    def atualizar(self, os: OrdemServico) -> OrdemServico:
        model = self.db.query(OrdemServicoModel).filter(OrdemServicoModel.id == os.id).first()
        model.observacoes = os.observacoes
        model.status = os.status.value
        model.orcamento_aprovado = os.orcamento_aprovado
        model.data_inicio_execucao = os.data_inicio_execucao
        model.data_finalizacao = os.data_finalizacao
        model.data_entrega = os.data_entrega

        model.servicos.clear()
        for s in os.servicos:
            model.servicos.append(
                ItemServicoOSModel(
                    servico_id=s.servico_id,
                    nome_servico=s.nome_servico,
                    preco_unitario=s.preco_unitario,
                    quantidade=s.quantidade,
                )
            )

        model.pecas.clear()
        for p in os.pecas:
            model.pecas.append(
                ItemPecaOSModel(
                    peca_id=p.peca_id,
                    nome_peca=p.nome_peca,
                    preco_unitario=p.preco_unitario,
                    quantidade=p.quantidade,
                )
            )

        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)