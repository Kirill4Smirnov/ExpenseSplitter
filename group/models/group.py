from uuid import UUID
from sqlmodel import Field, SQLModel

class Group(SQLModel, table=True):
    id: UUID = Field(primary_key=True)
    name: str 