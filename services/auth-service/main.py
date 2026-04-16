from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from jose import jwt
from passlib.context import CryptContext

app = FastAPI()

client = MongoClient("mongodb://mongodb:27017")
db = client["study"]
users = db["users"]

SECRET = "SECRET123"
pwd = CryptContext(schemes=["bcrypt"])

@app.on_event("startup")
def bootstrap_users():
    """Create default users on startup if they don't exist."""
    defaults = [
        ("admin@example.com", "admin123", "admin"),
        ("staff@example.com", "staff123", "staff"),
        ("member@example.com", "member123", "member")
    ]
    for email, password, role in defaults:
        if not users.find_one({"email": email}):
            print(f"Bootstrapping user: {email} ({role})")
            users.insert_one({
                "email": email,
                "password": pwd.hash(password),
                "role": role
            })

@app.post("/register")
def register(data: dict):
    if users.find_one({"email": data["email"]}):
        raise HTTPException(400, "User exists")

    users.insert_one({
        "email": data["email"],
        "password": pwd.hash(data["password"]),
        "role": data.get("role", "member")
    })

    return {"msg": "User created"}

@app.post("/login")
def login(data: dict):
    user = users.find_one({"email": data["email"]})
    if not user or not pwd.verify(data["password"], user["password"]):
        raise HTTPException(401, "Invalid credentials")

    token = jwt.encode({
        "email": user["email"],
        "role": user["role"]
    }, SECRET)

    return {"access_token": token}