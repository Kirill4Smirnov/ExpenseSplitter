from uuid import UUID, uuid4
from fastapi import FastAPI
from database.db import wait_for_db

from models.user import User
from database.db import SessionDep
from sqlmodel import select

app = FastAPI()


@app.on_event("startup")
def on_startup():
    wait_for_db()


@app.post("/users/{username:str}/{email:str}")
async def add_user(username: str, email: str, session: SessionDep):
    user = User(id=uuid4(), username=username, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.get("/users/{id}")
async def get_user_by_id(id: UUID, session: SessionDep):
    user = session.exec(select(User).where(User.id == id)).all()
    return user


@app.get("/users/")
async def get_users(session: SessionDep):
    users = session.exec(select(User)).all()
    return users
