from pydantic import BaseModel


class DatabaseSettings(BaseModel):
    user: str
    password: str
    host: str
    name: str
    port: int = 5432
