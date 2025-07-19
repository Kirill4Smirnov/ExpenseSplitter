from uuid import UUID
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: UUID = Field(primary_key=True)
    username: str = ""
    email: str | None = None
