from uuid import UUID, uuid4
from fastapi import FastAPI, HTTPException
from models.group import Group, GroupMember
from database.db import SessionDep
from sqlmodel import select
from os import environ

app = FastAPI()
user_service_url = environ['USER_SERVICE_URL']
expense_service_url = environ['EXPENSE_SERVICE_URL']

@app.post("/groups/", response_model=Group)
def create_group(name: str, session: SessionDep):
    group = Group(id=uuid4(), name=name)
    session.add(group)
    session.commit()
    session.refresh(group)
    return group

@app.delete("/groups/{group_id}")
def delete_group(group_id: UUID, session: SessionDep):
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group_members = session.exec(select(GroupMember).where(GroupMember.group_id == group_id)).all()
    for member in group_members:
        session.delete(member)
    session.delete(group)
    session.commit()
    return {"message": "Group and its members deleted successfully"}

@app.get("/groups/{group_id}")
def check_group(group_id: UUID, session: SessionDep):
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return {"message": "Group exists"}

@app.post("/groups/{group_id}/users/{user_id}")
def add_user_to_group(group_id: UUID, user_id: UUID, session: SessionDep):
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    link = session.get(GroupMember, (group_id, user_id))
    if link:
        raise HTTPException(status_code=400, detail="User already in group")
    group_member = GroupMember(group_id=group_id, user_id=user_id)
    session.add(group_member)
    session.commit()
    return {"message": "User added to group"}

@app.delete("/groups/{group_id}/users/{user_id}")
def remove_user_from_group(group_id: UUID, user_id: UUID, session: SessionDep):
    link = session.get(GroupMember, (group_id, user_id))
    if not link:
        raise HTTPException(status_code=404, detail="User not in group")
    session.delete(link)
    session.commit()
    return {"message": "User removed from group"}

@app.get("/groups/{group_id}/users/{user_id}")
def is_user_in_group(group_id: UUID, user_id: UUID, session: SessionDep):
    link = session.get(GroupMember, (group_id, user_id))
    return {"in_group": bool(link)}

@app.get("/groups/{group_id}/users")
def list_users_in_group(group_id: UUID, session: SessionDep):
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    user_links = session.exec(select(GroupMember).where(GroupMember.group_id == group_id)).all()
    user_ids = [link.user_id for link in user_links]
    return {"user_ids": user_ids}

@app.get("/groups/{user_id}/groups")
def list_groups_for_user(user_id: UUID, session: SessionDep):
    group_links = session.exec(select(GroupMember).where(GroupMember.user_id == user_id)).all()
    group_ids = [link.group_id for link in group_links]
    return {"group_ids": group_ids}
