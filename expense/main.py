from uuid import UUID, uuid4
from fastapi import FastAPI, HTTPException

from models.expense import Expense
from database.db import SessionDep
from sqlmodel import select

app = FastAPI()

@app.post("/expenses/{amount:float}/{description:str}/{user_id}/{group_id}")    
async def add_expense(amount: float, description: str, user_id: UUID, group_id: UUID, session: SessionDep):
    expense = Expense(id = uuid4(), amount=amount, description=description, user_id=user_id, group_id=group_id)
    session.add(expense)
    session.commit()
    return expense

@app.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: UUID, session: SessionDep):
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    session.delete(expense)
    session.commit()
    return {"message": "Expense deleted successfully"}

@app.get("/expenses/{expense_id}")
async def get_expense(expense_id: UUID, session: SessionDep):
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

@app.get("/expenses")
async def get_expenses(session: SessionDep):
    expenses = session.exec(select(Expense)).all()
    return expenses
