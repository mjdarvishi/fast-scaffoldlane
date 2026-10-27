import asyncio
from dataclasses import dataclass

from app.core.dependency import injectable
from app.core.exception.base_exception import AccessDeniyedException
from app.core.use_cases.use_case import BaseUseCase
from app.features.auth.domain.entities import UserAccountEntity
from app.features.auth.domain.repositories import UserRepository
from app.features.auth.domain.services.passwords import verify_password


@dataclass(frozen=True)
class SigninRequest:
    email: str
    password: str


@injectable()
class SigninUseCase(BaseUseCase[SigninRequest, UserAccountEntity]):
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def __call__(self, payload: SigninRequest) -> UserAccountEntity:
        user = await self._user_repository.get_credentials(email=payload.email)
        if user is None or not user.is_active or not await asyncio.to_thread(
            verify_password, payload.password, user.password_hash
        ):
            raise AccessDeniyedException(message="Invalid email or password")
        return UserAccountEntity(id=user.id, email=user.email)
