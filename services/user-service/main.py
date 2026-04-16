from fastapi import FastAPI, Depends, Body
from pymongo import MongoClient

from auth import get_user, require_role

app = FastAPI()

client = MongoClient("mongodb://mongodb:27017")
db = client["study"]
users = db["users"]

@app.get("/users")
def get_users(user=Depends(get_user)):
    require_role(user, ["admin"])
    return list(users.find({}, {"_id": 0, "password": 0}))

@app.put("/users/{email}")
def update_user(email: str, data: dict = Body(...), user=Depends(get_user)):
    require_role(user, ["admin"])
    users.update_one({"email": email}, {"$set": {"role": data.get("role", "member")}})
    return {"msg": "updated"}

@app.delete("/users/{email}")
def delete_user(email: str, user=Depends(get_user)):
    require_role(user, ["admin"])
    users.delete_one({"email": email})
    return {"msg": "deleted"}