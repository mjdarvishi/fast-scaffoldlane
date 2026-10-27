from abc import ABC, abstractmethod

from app.features.auth.domain.entities import UserAccountEntity, UserCredentialsEntity


class UserRepository(ABC):
    @abstractmethod
    async def create(self, *, email: str, password_hash: str) -> UserAccountEntity | None:
        """Create a user; return None when the email is already registered."""

    @abstractmethod
    async def get_credentials(self, *, email: str) -> UserCredentialsEntity | None:
        """Fetch local credentials for signin."""
