import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[5]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.infrastructure.database.models import UsuarioAdminModel
from app.infrastructure.database.session import get_db
from app.infrastructure.security.jwt_handler import create_access_token, verify_password
from app.presentation.schemas.schemas import TokenResponse

router = APIRouter(prefix="/auth", tags=["1. Autenticação Administrativa (JWT)"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autentica usuário administrativo e retorna token JWT",
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = (
        db.query(UsuarioAdminModel)
        .filter(UsuarioAdminModel.username == form_data.username, UsuarioAdminModel.ativo.is_(True))
        .first()
    )
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.username)
    return TokenResponse(access_token=access_token, token_type="bearer")