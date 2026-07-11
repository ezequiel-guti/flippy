from fastapi import APIRouter, Depends, HTTPException

from app.core.security import TokenData, get_current_user
from app.integrations.supabase_auth import SupabaseAuthError

from .model import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from .services import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest):
    try:
        result = AuthService.register(body.email, body.password)
    except SupabaseAuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return {**result, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    try:
        result = AuthService.login(body.email, body.password)
    except SupabaseAuthError:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")
    return {**result, "token_type": "bearer"}


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest):
    try:
        result = AuthService.refresh(body.refresh_token)
    except SupabaseAuthError:
        raise HTTPException(status_code=401, detail="Refresh token invalido o expirado")
    return {**result, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def me(current_user: TokenData = Depends(get_current_user)):
    profile = AuthService.get_profile(current_user.user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return profile
