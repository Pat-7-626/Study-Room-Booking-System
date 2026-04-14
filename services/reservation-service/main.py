from fastapi import FastAPI, HTTPException
from pymongo import MongoClient

app = FastAPI()

client = MongoClient("mongodb://mongodb:27017")
db = client["study"]
res = db["reservations"]

@app.post("/reserve")
def reserve(data: dict):
    overlap = res.find_one({
        "room_id": data["room_id"],
        "start": {"$lt": data["end"]},
        "end": {"$gt": data["start"]}
    })

    if overlap:
        raise HTTPException(400, "Already booked")

    res.insert_one(data)
    return {"msg": "reserved"}

@app.get("/reservations")
def get_all():
    return list(res.find({}, {"_id": 0}))