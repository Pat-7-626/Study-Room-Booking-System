from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from datetime import datetime

app = FastAPI()

client = MongoClient("mongodb://mongodb:27017")
db = client["study"]
reservations = db["reservations"]

@app.post("/reserve")
def reserve(data: dict):
    # check overlap
    existing = reservations.find_one({
        "room_id": data["room_id"],
        "start": {"$lt": data["end"]},
        "end": {"$gt": data["start"]}
    })

    if existing:
        raise HTTPException(400, "Room already booked")

    reservations.insert_one(data)
    return {"msg": "Reserved"}

@app.get("/reservations")
def get_all():
    return list(reservations.find({}, {"_id": 0}))