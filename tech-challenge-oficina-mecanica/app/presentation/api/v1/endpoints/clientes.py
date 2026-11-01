import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[5]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.domain.entities.cliente import Cliente
from app.domain.value_objects.cpf_cnpj import CpfCnpj
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.sqlalchemy_repositories import SQLAlchemyClienteRepository
from app.presentation.dependencies.auth import get_current_admin
from app.presentation.schemas.schemas import ClienteCreate, ClienteResponse, ClienteUpdate

router = APIRouter(
    prefix="/clientes",
    tags=["2. Gestão de Clientes (Admin)"],
    dependencies=[Depends(get_current_admin)],
)


def _map_cliente_response(c: Cliente) -> ClienteResponse:
    return ClienteResponse(
        id=c.id,
        nome=c.nome,
        documento=c.documento.value,
        documento_formatado=c.documento.formatted,
        tipo_documento=c.documento.document_type,
        telefone=c.telefone,
        email=c.email,
        endereco=c.endereco,
        criado_em=c.criado_em,
    )


@router.post("", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED, summary="Cadastrar novo cliente")
def criar_cliente(payload: ClienteCreate, db: Session = Depends(get_db)):
    repo = SQLAlchemyClienteRepository(db)
    doc_vo = CpfCnpj(payload.documento)
    if repo.buscar_por_documento(doc_vo.value):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe um cliente cadastrado com o documento {doc_vo.formatted}.",
        )
    novo = Cliente(
        nome=payload.nome,
        documento=doc_vo,
        telefone=payload.telefone,
        email=payload.email,
        endereco=payload.endereco,
    )
    criado = repo.criar(novo)
    return _map_cliente_response(criado)


@router.get("", response_model=List[ClienteResponse], summary="Listar todos os clientes")
def listar_clientes(db: Session = Depends(get_db)):
    repo = SQLAlchemyClienteRepository(db)
    return [_map_cliente_response(c) for c in repo.listar_todos()]


@router.get("/documento/{documento}", response_model=ClienteResponse, summary="Buscar cliente por CPF ou CNPJ")
def buscar_cliente_por_documento(documento: str, db: Session = Depends(get_db)):
    repo = SQLAlchemyClienteRepository(db)
    cliente = repo.buscar_por_documento(documento)
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")
    return _map_cliente_response(cliente)


@router.get("/{cliente_id}", response_model=ClienteResponse, summary="Buscar cliente por ID")
def buscar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    repo = SQLAlchemyClienteRepository(db)
    cliente = repo.buscar_por_id(cliente_id)
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")
    return _map_cliente_response(cliente)


@router.put("/{cliente_id}", response_model=ClienteResponse, summary="Atualizar dados do cliente")
def atualizar_cliente(cliente_id: int, payload: ClienteUpdate, db: Session = Depends(get_db)):
    repo = SQLAlchemyClienteRepository(db)
    atual = repo.buscar_por_id(cliente_id)
    if not atual:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")

    atualizado_entity = Cliente(
        id=atual.id,
        nome=payload.nome,
        documento=atual.documento,
        telefone=payload.telefone,
        email=payload.email,
        endereco=payload.endereco,
        criado_em=atual.criado_em,
    )
    salvo = repo.atualizar(atualizado_entity)
    return _map_cliente_response(salvo)


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover cliente")
def deletar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    repo = SQLAlchemyClienteRepository(db)
    if not repo.deletar(cliente_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")