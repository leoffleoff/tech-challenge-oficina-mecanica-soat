import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[5]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.domain.entities.veiculo import Veiculo
from app.domain.value_objects.placa import Placa
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.sqlalchemy_repositories import (
    SQLAlchemyClienteRepository,
    SQLAlchemyVeiculoRepository,
)
from app.presentation.dependencies.auth import get_current_admin
from app.presentation.schemas.schemas import VeiculoCreate, VeiculoResponse, VeiculoUpdate

router = APIRouter(
    prefix="/veiculos",
    tags=["3. Gestão de Veículos (Admin)"],
    dependencies=[Depends(get_current_admin)],
)


def _map_veiculo_response(v: Veiculo) -> VeiculoResponse:
    return VeiculoResponse(
        id=v.id,
        placa=v.placa.value,
        placa_formatada=v.placa.formatted,
        is_mercosul=v.placa.is_mercosul,
        marca=v.marca,
        modelo=v.modelo,
        ano=v.ano,
        cor=v.cor,
        cliente_id=v.cliente_id,
        criado_em=v.criado_em,
    )


@router.post("", response_model=VeiculoResponse, status_code=status.HTTP_201_CREATED, summary="Cadastrar veículo")
def criar_veiculo(payload: VeiculoCreate, db: Session = Depends(get_db)):
    cliente_repo = SQLAlchemyClienteRepository(db)
    if not cliente_repo.buscar_por_id(payload.cliente_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente proprietário não encontrado.")

    veiculo_repo = SQLAlchemyVeiculoRepository(db)
    placa_vo = Placa(payload.placa)
    if veiculo_repo.buscar_por_placa(placa_vo.value):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe um veículo cadastrado com a placa {placa_vo.formatted}.",
        )

    novo = Veiculo(
        placa=placa_vo,
        marca=payload.marca,
        modelo=payload.modelo,
        ano=payload.ano,
        cor=payload.cor,
        cliente_id=payload.cliente_id,
    )
    return _map_veiculo_response(veiculo_repo.criar(novo))


@router.get("", response_model=List[VeiculoResponse], summary="Listar todos os veículos")
def listar_veiculos(db: Session = Depends(get_db)):
    repo = SQLAlchemyVeiculoRepository(db)
    return [_map_veiculo_response(v) for v in repo.listar_todos()]


@router.get("/{veiculo_id}", response_model=VeiculoResponse, summary="Buscar veículo por ID")
def buscar_veiculo(veiculo_id: int, db: Session = Depends(get_db)):
    repo = SQLAlchemyVeiculoRepository(db)
    v = repo.buscar_por_id(veiculo_id)
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado.")
    return _map_veiculo_response(v)


@router.put("/{veiculo_id}", response_model=VeiculoResponse, summary="Atualizar veículo")
def atualizar_veiculo(veiculo_id: int, payload: VeiculoUpdate, db: Session = Depends(get_db)):
    repo = SQLAlchemyVeiculoRepository(db)
    atual = repo.buscar_por_id(veiculo_id)
    if not atual:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado.")

    atualizado = Veiculo(
        id=atual.id,
        placa=Placa(payload.placa),
        marca=payload.marca,
        modelo=payload.modelo,
        ano=payload.ano,
        cor=payload.cor,
        cliente_id=payload.cliente_id,
        criado_em=atual.criado_em,
    )
    return _map_veiculo_response(repo.atualizar(atualizado))


@router.delete("/{veiculo_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover veículo")
def deletar_veiculo(veiculo_id: int, db: Session = Depends(get_db)):
    repo = SQLAlchemyVeiculoRepository(db)
    if not repo.deletar(veiculo_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado.")