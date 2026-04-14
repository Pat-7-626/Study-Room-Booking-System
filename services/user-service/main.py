from fastapi import FastAPI
from pymongo import MongoClient

app = FastAPI()

client = MongoClient("mongodb://mongodb:27017")
db = client["study"]
users = db["users"]

@app.get("/users")
def get_users():
    return list(users.find({}, {"_id": 0}))

@app.delete("/users/{email}")
def delete_user(email: str):
    users.delete_one({"email": email})
    return {"msg": "Deleted"}