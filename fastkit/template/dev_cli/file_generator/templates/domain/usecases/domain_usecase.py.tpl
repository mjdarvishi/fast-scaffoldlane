from app.core.dependency import injectable
from app.core.use_cases import BaseUseCase
from app.features.{domain}.domain.repositories import {domain_class}Repository


@injectable()
class {domain_class}UseCase(BaseUseCase[dict, dict]):
    def __init__(self, repository: {domain_class}Repository) -> None:
        self._repository = repository

    async def __call__(self, args: dict) -> dict:
        raise NotImplementedError
