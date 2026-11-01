import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[5]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.domain.entities.peca import Peca
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.sqlalchemy_repositories import SQLAlchemyPecaRepository
from app.presentation.dependencies.auth import get_current_admin
from app.presentation.schemas.schemas import (
    MovimentacaoEstoqueRequest,
    PecaCreate,
    PecaResponse,
    PecaUpdate,
)

router = APIRouter(
    prefix="/pecas",
    tags=["5. Gestão de Peças, Insumos e Estoque (Admin)"],
    dependencies=[Depends(get_current_admin)],
)


@router.post("", response_model=PecaResponse, status_code=status.HTTP_201_CREATED, summary="Cadastrar peça ou insumo")
def criar_peca(payload: PecaCreate, db: Session = Depends(get_db)):
    repo = SQLAlchemyPecaRepository(db)
    if repo.buscar_por_sku(payload.codigo_sku):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe uma peça com o SKU '{payload.codigo_sku}'.",
        )
    nova = Peca(
        nome=payload.nome,
        codigo_sku=payload.codigo_sku,
        preco_unitario=payload.preco_unitario,
        quantidade_estoque=payload.quantidade_estoque,
        estoque_minimo=payload.estoque_minimo,
    )
    return repo.criar(nova)


@router.get("", response_model=List[PecaResponse], summary="Listar peças e situação de estoque")
def listar_pecas(db: Session = Depends(get_db)):
    repo = SQLAlchemyPecaRepository(db)
    return repo.listar_todos()


@router.get("/{peca_id}", response_model=PecaResponse, summary="Buscar peça por ID")
def buscar_peca(peca_id: int, db: Session = Depends(get_db)):
    repo = SQLAlchemyPecaRepository(db)
    peca = repo.buscar_por_id(peca_id)
    if not peca:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peça não encontrada.")
    return peca


@router.put("/{peca_id}", response_model=PecaResponse, summary="Atualizar cadastro da peça")
def atualizar_peca(peca_id: int, payload: PecaUpdate, db: Session = Depends(get_db)):
    repo = SQLAlchemyPecaRepository(db)
    if not repo.buscar_por_id(peca_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peça não encontrada.")
    atualizada = Peca(
        id=peca_id,
        nome=payload.nome,
        codigo_sku=payload.codigo_sku,
        preco_unitario=payload.preco_unitario,
        quantidade_estoque=payload.quantidade_estoque,
        estoque_minimo=payload.estoque_minimo,
    )
    return repo.atualizar(atualizada)


@router.patch("/{peca_id}/repor-estoque", response_model=PecaResponse, summary="Adicionar unidades ao estoque da peça")
def repor_estoque(peca_id: int, payload: MovimentacaoEstoqueRequest, db: Session = Depends(get_db)):
    repo = SQLAlchemyPecaRepository(db)
    peca = repo.buscar_por_id(peca_id)
    if not peca:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peça não encontrada.")
    peca.repor_estoque(payload.quantidade)
    return repo.atualizar(peca)


@router.delete("/{peca_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover peça do catálogo")
def deletar_peca(peca_id: int, db: Session = Depends(get_db)):
    repo = SQLAlchemyPecaRepository(db)
    if not repo.deletar(peca_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peça não encontrada.")