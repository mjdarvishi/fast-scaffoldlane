from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UserAccountEntity:
    id: UUID
    email: str


@dataclass(frozen=True)
class UserCredentialsEntity(UserAccountEntity):
    password_hash: str
    is_active: bool
