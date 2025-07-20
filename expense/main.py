from uuid import UUID, uuid4
from fastapi import FastAPI, HTTPException
import requests

from models.expense import Expense
from database.db import SessionDep
from sqlmodel import select
from os import environ

app = FastAPI()
user_service_url = environ['USER_SERVICE_URL']
group_service_url = environ['GROUP_SERVICE_URL']

@app.post("/expenses/{amount:float}/{description:str}/{user_id}/{group_id}")    
def add_expense(amount: float, description: str, user_id: UUID, group_id: UUID, session: SessionDep):
    group_response = requests.get(f"{group_service_url}/{group_id}")
    if group_response.status_code != 200:
        raise HTTPException(status_code=404, detail=f"Group not found. Expense is not added")

    user_response = requests.get(f"{user_service_url}/{user_id}")
    if user_response.status_code != 200:
        raise HTTPException(status_code=404, detail=f"User not found. Expense is not added")

    # Check if user is in group, if not, add them
    membership_response = requests.get(f"{group_service_url}/{group_id}/users/{user_id}")
    if membership_response.status_code == 200 and not membership_response.json().get("in_group", False):
        add_member_response = requests.post(f"{group_service_url}/{group_id}/users/{user_id}")
        if add_member_response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Failed to add user to group")
    elif membership_response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Failed to check group membership")

    expense = Expense(id=uuid4(), amount=amount, description=description, user_id=user_id, group_id=group_id)
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

@app.get("/expenses/user/{user_id}")
async def get_expenses_by_user(user_id: UUID, session: SessionDep):
    expenses = session.exec(select(Expense).where(Expense.user_id == user_id)).all()
    if not expenses:
        raise HTTPException(status_code=404, detail="Expenses for this user not found")
    return expenses

@app.get("/expenses/groups/{group_id}/total")
def group_total_expense(group_id: UUID, session: SessionDep):
    members_response = requests.get(f"{group_service_url}/{group_id}/users")
    if members_response.status_code != 200:
        raise HTTPException(status_code=404, detail="Group not found or failed to fetch members")
    user_ids = members_response.json().get("user_ids", [])
    if not user_ids:
        raise HTTPException(status_code=404, detail="No users in group")

    expenses = session.exec(select(Expense).where(Expense.group_id == group_id)).all()
    if not expenses:
        return {"message": "No expenses in group", "total_expense": 0, "user_totals": {}}

    user_totals = {str(uid): 0.0 for uid in user_ids}
    for expense in expenses:
        user_totals[str(expense.user_id)] += expense.amount

    total_expense = sum(user_totals.values())
    return {
        "total_expense": total_expense,
        "user_totals": user_totals
    }

@app.get("/expenses/groups/{group_id}/users/{user_id}/owes")
def user_owes_in_group(group_id: UUID, user_id: UUID, session: SessionDep):
    members_response = requests.get(f"{group_service_url}/{group_id}/users")
    if members_response.status_code != 200:
        raise HTTPException(status_code=404, detail="Group not found or failed to fetch members")
    user_ids = members_response.json().get("user_ids", [])
    if not user_ids or str(user_id) not in [str(uid) for uid in user_ids]:
        raise HTTPException(status_code=404, detail="User not in group")

    expenses = session.exec(select(Expense).where(Expense.group_id == group_id)).all()
    if not expenses:
        return {"message": "No expenses in group", "owes": {}}

    user_totals = {str(uid): 0.0 for uid in user_ids}
    for expense in expenses:
        user_totals[str(expense.user_id)] += expense.amount

    total_expense = sum(user_totals.values())
    per_user_share = total_expense / len(user_ids)
    owes = {}
    for other_id in user_ids:
        other_id_str = str(other_id)
        if str(user_id) == other_id_str:
            continue

        owes[other_id_str] = round((per_user_share - user_totals[str(user_id)]) / (len(user_ids) - 1), 2) if user_totals[str(user_id)] < per_user_share else 0.0
    return {
        "user_id": str(user_id),
        "owes": owes
    }

@app.delete("/expenses/groups/{group_id}/clear")
def clear_group_expenses(group_id: UUID, session: SessionDep):
    expenses = session.exec(select(Expense).where(Expense.group_id == group_id)).all()
    if not expenses:
        return {"message": "No expenses to clear for this group."}
    for expense in expenses:
        session.delete(expense)
    session.commit()
    return {"message": f"All expenses for group {group_id} have been cleared."}
