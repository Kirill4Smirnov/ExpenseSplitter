from uuid import UUID
from sqlmodel import Field, SQLModel, Relationship


class Expense(SQLModel, table=True):
    id: UUID = Field(primary_key=True)
    amount: float = 0
    description: str = ""
    user_id: UUID
    group_id: UUID
