from uuid import UUID
from sqlmodel import Field, SQLModel

class Group(SQLModel, table=True):
    id: UUID = Field(primary_key=True)
    name: str

class GroupMember(SQLModel, table=True):
    group_id: UUID = Field(foreign_key="group.id", primary_key=True)
    user_id: UUID = Field(primary_key=True)
    