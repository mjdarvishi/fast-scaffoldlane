"""Default signup and signin endpoints."""

from fastapi import APIRouter

from app.core.auth.tokens import create_access_token
from app.core.dependency import injector
from app.features.auth.domain.usecases import (
    SigninRequest, SigninUseCase, SignupRequest, SignupUseCase,
)
from app.features.auth.presentation.schema.auth import (
    CredentialsRequest, SignupResponse, TokenResponse,
)


auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post("/signup", response_model=SignupResponse, status_code=201)
async def signup(payload: CredentialsRequest) -> SignupResponse:
    user = await injector.get(SignupUseCase)(
        SignupRequest(email=str(payload.email).lower(), password=payload.password)
    )
    return SignupResponse(id=user.id, email=user.email)


@auth_router.post("/signin", response_model=TokenResponse)
async def signin(payload: CredentialsRequest) -> TokenResponse:
    user = await injector.get(SigninUseCase)(
        SigninRequest(email=str(payload.email).lower(), password=payload.password)
    )
    token, expires_in = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token, expires_in=expires_in)
