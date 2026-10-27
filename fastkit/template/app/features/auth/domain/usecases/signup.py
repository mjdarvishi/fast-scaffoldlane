import asyncio
from dataclasses import dataclass

from app.core.dependency import injectable
from app.core.exception.base_exception import AlreadyExistException
from app.core.use_cases.use_case import BaseUseCase
from app.features.auth.domain.entities import UserAccountEntity
from app.features.auth.domain.repositories import UserRepository
from app.features.auth.domain.services.passwords import hash_password


@dataclass(frozen=True)
class SignupRequest:
    email: str
    password: str


@injectable()
class SignupUseCase(BaseUseCase[SignupRequest, UserAccountEntity]):
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def __call__(self, payload: SignupRequest) -> UserAccountEntity:
        password_hash = await asyncio.to_thread(hash_password, payload.password)
        user = await self._user_repository.create(
            email=payload.email, password_hash=password_hash
        )
        if user is None:
            raise AlreadyExistException(message="Email is already registered")
        return user
