import sys
from pathlib import Path

# Garante que a raiz do projeto seja encontrada
ROOT_DIR = Path(__file__).resolve().parents[4]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import APIRouter
from app.presentation.api.v1.endpoints import (
    auth,
    clientes,
    ordens_servico,
    pecas,
    servicos,
    veiculos,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(clientes.router)
api_router.include_router(veiculos.router)
api_router.include_router(servicos.router)
api_router.include_router(pecas.router)
api_router.include_router(ordens_servico.router_admin)
api_router.include_router(ordens_servico.router_publico)
