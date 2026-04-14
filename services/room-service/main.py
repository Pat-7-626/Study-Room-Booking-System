from fastapi import FastAPI
from pymongo import MongoClient

app = FastAPI()

client = MongoClient("mongodb://mongodb:27017")
db = client["study"]
rooms = db["rooms"]

@app.post("/rooms")
def create(room: dict):
    rooms.insert_one(room)
    return {"msg": "created"}

@app.get("/rooms")
def get_all():
    return list(rooms.find({}, {"_id": 0}))