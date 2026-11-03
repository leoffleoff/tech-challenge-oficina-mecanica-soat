import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.domain.exceptions.domain_exceptions import (
    BusinessRuleException,
    DomainException,
    EntityNotFoundException,
    InsufficientStockException,
    InvalidDocumentException,
    InvalidLicensePlateException,
    InvalidStatusTransitionException,
)
from app.infrastructure.database.models import UsuarioAdminModel
from app.infrastructure.database.session import Base, SessionLocal, engine
from app.infrastructure.security.jwt_handler import get_password_hash
from app.presentation.api.v1.router import api_router


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = (
            db.query(UsuarioAdminModel)
            .filter(UsuarioAdminModel.username == settings.ADMIN_USERNAME)
            .first()
        )
        if not admin:
            novo_admin = UsuarioAdminModel(
                username=settings.ADMIN_USERNAME,
                password_hash=get_password_hash(settings.ADMIN_PASSWORD),
                ativo=True,
            )
            db.add(novo_admin)
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(application: FastAPI):
    init_db()
    yield


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "MVP do Sistema Integrado de Atendimento e Execução de Serviços para Oficina Mecânica. "
            "Desenvolvido com Domain-Driven Design (DDD) e Arquitetura em Camadas para o Tech Challenge - Fase 1 (SOAT FIAP)."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Handlers individuais para evitar conflitos de tupla no FastAPI
    @application.exception_handler(EntityNotFoundException)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundException):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @application.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )

    @application.get("/health", tags=["Healthcheck"], summary="Verifica o status da aplicação")
    def health_check():
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "architecture": "Layered Monolith + DDD",
        }

    application.include_router(api_router, prefix=settings.API_V1_STR)

    return application


app = create_application()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)