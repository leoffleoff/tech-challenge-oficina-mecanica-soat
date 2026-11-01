import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[5]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.domain.entities.servico import Servico
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.sqlalchemy_repositories import SQLAlchemyServicoRepository
from app.presentation.dependencies.auth import get_current_admin
from app.presentation.schemas.schemas import ServicoCreate, ServicoResponse

router = APIRouter(
    prefix="/servicos",
    tags=["4. Catálogo de Serviços (Admin)"],
    dependencies=[Depends(get_current_admin)],
)


@router.post("", response_model=ServicoResponse, status_code=status.HTTP_201_CREATED, summary="Cadastrar serviço")
def criar_servico(payload: ServicoCreate, db: Session = Depends(get_db)):
    repo = SQLAlchemyServicoRepository(db)
    novo = Servico(
        nome=payload.nome,
        descricao=payload.descricao,
        preco_base=payload.preco_base,
        tempo_estimado_minutos=payload.tempo_estimado_minutos,
    )
    return repo.criar(novo)


@router.get("", response_model=List[ServicoResponse], summary="Listar serviços")
def listar_servicos(db: Session = Depends(get_db)):
    repo = SQLAlchemyServicoRepository(db)
    return repo.listar_todos()


@router.get("/{servico_id}", response_model=ServicoResponse, summary="Buscar serviço por ID")
def buscar_servico(servico_id: int, db: Session = Depends(get_db)):
    repo = SQLAlchemyServicoRepository(db)
    servico = repo.buscar_por_id(servico_id)
    if not servico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Serviço não encontrado.")
    return servico


@router.put("/{servico_id}", response_model=ServicoResponse, summary="Atualizar serviço")
def atualizar_servico(servico_id: int, payload: ServicoCreate, db: Session = Depends(get_db)):
    repo = SQLAlchemyServicoRepository(db)
    if not repo.buscar_por_id(servico_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Serviço não encontrado.")
    atualizado = Servico(
        id=servico_id,
        nome=payload.nome,
        descricao=payload.descricao,
        preco_base=payload.preco_base,
        tempo_estimado_minutos=payload.tempo_estimado_minutos,
    )
    return repo.atualizar(atualizado)


@router.delete("/{servico_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover serviço")
def deletar_servico(servico_id: int, db: Session = Depends(get_db)):
    repo = SQLAlchemyServicoRepository(db)
    if not repo.deletar(servico_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Serviço não encontrado.")