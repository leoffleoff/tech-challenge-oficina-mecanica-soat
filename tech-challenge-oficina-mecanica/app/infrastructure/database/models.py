import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.infrastructure.database.session import Base


class UsuarioAdminModel(Base):
    __tablename__ = "usuarios_admin"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ClienteModel(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    documento = Column(String(14), unique=True, index=True, nullable=False)
    telefone = Column(String(20), nullable=False)
    email = Column(String(150), nullable=False)
    endereco = Column(String(255), nullable=True)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    veiculos = relationship("VeiculoModel", back_populates="cliente", cascade="all, delete-orphan")
    ordens_servico = relationship("OrdemServicoModel", back_populates="cliente")


class VeiculoModel(Base):
    __tablename__ = "veiculos"

    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String(7), unique=True, index=True, nullable=False)
    marca = Column(String(80), nullable=False)
    modelo = Column(String(80), nullable=False)
    ano = Column(Integer, nullable=False)
    cor = Column(String(40), nullable=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    cliente = relationship("ClienteModel", back_populates="veiculos")
    ordens_servico = relationship("OrdemServicoModel", back_populates="veiculo")


class ServicoModel(Base):
    __tablename__ = "servicos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    descricao = Column(Text, nullable=False)
    preco_base = Column(Numeric(10, 2), nullable=False)
    tempo_estimado_minutos = Column(Integer, nullable=False)


class PecaModel(Base):
    __tablename__ = "pecas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    codigo_sku = Column(String(50), unique=True, index=True, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    quantidade_estoque = Column(Integer, nullable=False, default=0)
    estoque_minimo = Column(Integer, nullable=False, default=5)


class OrdemServicoModel(Base):
    __tablename__ = "ordens_servico"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id"), nullable=False, index=True)
    observacoes = Column(Text, nullable=True)
    status = Column(String(40), nullable=False, default="Recebida", index=True)
    orcamento_aprovado = Column(Boolean, nullable=True)

    data_abertura = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    data_inicio_execucao = Column(DateTime(timezone=True), nullable=True)
    data_finalizacao = Column(DateTime(timezone=True), nullable=True)
    data_entrega = Column(DateTime(timezone=True), nullable=True)

    cliente = relationship("ClienteModel", back_populates="ordens_servico")
    veiculo = relationship("VeiculoModel", back_populates="ordens_servico")
    servicos = relationship(
        "ItemServicoOSModel",
        back_populates="ordem_servico",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    pecas = relationship(
        "ItemPecaOSModel",
        back_populates="ordem_servico",
        cascade="all, delete-orphan",
        lazy="joined",
    )


class ItemServicoOSModel(Base):
    __tablename__ = "itens_servico_os"

    id = Column(Integer, primary_key=True, index=True)
    ordem_servico_id = Column(Integer, ForeignKey("ordens_servico.id", ondelete="CASCADE"), nullable=False)
    servico_id = Column(Integer, ForeignKey("servicos.id"), nullable=False)
    nome_servico = Column(String(120), nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    quantidade = Column(Integer, nullable=False, default=1)

    ordem_servico = relationship("OrdemServicoModel", back_populates="servicos")


class ItemPecaOSModel(Base):
    __tablename__ = "itens_peca_os"

    id = Column(Integer, primary_key=True, index=True)
    ordem_servico_id = Column(Integer, ForeignKey("ordens_servico.id", ondelete="CASCADE"), nullable=False)
    peca_id = Column(Integer, ForeignKey("pecas.id"), nullable=False)
    nome_peca = Column(String(120), nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    quantidade = Column(Integer, nullable=False, default=1)

    ordem_servico = relationship("OrdemServicoModel", back_populates="pecas")