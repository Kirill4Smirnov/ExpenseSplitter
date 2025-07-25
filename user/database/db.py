from typing import Annotated

from sqlmodel import SQLModel, create_engine, Session
from fastapi import Depends
from os import environ

engine = create_engine(environ["DATABASE_URL"])
SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
