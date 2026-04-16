import uuid
import httpx
from datetime import datetime, timedelta, date
from fastapi import FastAPI, Depends, HTTPException, Body
from pymongo import MongoClient

from auth import get_user, require_role

app = FastAPI()

client = MongoClient("mongodb://mongodb:27017")
db = client["study"]
res = db["reservations"]

ROOM_SERVICE_URL = "http://room-service:8000"


def get_room_capacity(room_id: str) -> int:
    """Call room-service to get room capacity (service-based architecture)."""
    try:
        resp = httpx.get(f"{ROOM_SERVICE_URL}/rooms/{room_id}", timeout=5.0)
        if resp.status_code == 200:
            return resp.json().get("capacity", 0)
    except Exception:
        pass
    return 0


@app.post("/reserve")
def reserve(data: dict = Body(...), user=Depends(get_user)):
    require_role(user, ["member"])

    tomorrow_start = datetime.combine(date.today() + timedelta(days=1), datetime.min.time())
    tomorrow_timestamp = tomorrow_start.timestamp() * 1000

    start_ms = data.get("start", 0)
    end_ms = data.get("end", 0)
    group_size = int(data.get("group_size", 1))

    if group_size < 1:
        raise HTTPException(400, "Group size must be at least 1.")

    # Must be at least tomorrow
    if start_ms < tomorrow_timestamp:
        raise HTTPException(400, "Reservations must be made at least 1 day in advance.")

    start_dt = datetime.fromtimestamp(start_ms / 1000.0)
    end_dt = datetime.fromtimestamp(end_ms / 1000.0)

    # Must be exactly 1 hour slot (frontend enforces valid hour slots; no tz-sensitive checks needed)
    if (end_ms - start_ms) != 3600 * 1000:
        raise HTTPException(400, "Each reservation slot is exactly 1 hour.")

    # Fetch room capacity from room-service (service-based call)
    room_capacity = get_room_capacity(data["room_id"])
    if room_capacity == 0:
        raise HTTPException(404, "Room not found.")

    if group_size > room_capacity:
        raise HTTPException(400, f"Group size ({group_size}) exceeds room capacity ({room_capacity}).")

    # Sum existing group_sizes for this room in this exact 1-hour slot
    existing_bookings = list(res.find({
        "room_id": data["room_id"],
        "start": start_ms
    }))
    current_occupancy = sum(b.get("group_size", 1) for b in existing_bookings)

    if current_occupancy + group_size > room_capacity:
        remaining = room_capacity - current_occupancy
        raise HTTPException(400, f"Not enough capacity. Only {remaining} spot(s) left for this slot.")

    data["user_email"] = user["email"]
    data["res_id"] = str(uuid.uuid4())
    res.insert_one(data)

    return {"msg": "reserved"}


@app.put("/reserve/{res_id}")
def update_reserve(res_id: str, data: dict = Body(...), user=Depends(get_user)):
    require_role(user, ["admin"])
    res.update_one({"res_id": res_id}, {"$set": data})
    return {"msg": "updated"}


@app.delete("/reserve/{res_id}")
def cancel(res_id: str, user=Depends(get_user)):
    if user["role"] in ["admin", "staff"]:
        result = res.delete_one({"res_id": res_id})
    else:
        result = res.delete_one({"res_id": res_id, "user_email": user["email"]})

    if result.deleted_count == 0:
        raise HTTPException(404, "Reservation not found or unauthorized")

    return {"msg": "cancelled"}


@app.get("/my-reservations")
def my(user=Depends(get_user)):
    return list(res.find({"user_email": user["email"]}, {"_id": 0}))


@app.get("/all-reservations")
def all_res(user=Depends(get_user)):
    require_role(user, ["staff", "admin"])
    return list(res.find({}, {"_id": 0}))


@app.get("/room-schedule/{room_id}")
def room_schedule(room_id: str):
    """Returns occupied slots with current occupancy for a room."""
    items = list(res.find({"room_id": room_id}, {"_id": 0, "start": 1, "end": 1, "group_size": 1}))
    return items


@app.get("/occupancy-summary")
def occupancy_summary():
    """
    Returns a dict of room_id -> total occupied seats for the CURRENT 1-hour slot.
    Used by the Rooms page to display live capacity remaining for all rooms at once.
    """
    now = datetime.now()
    current_slot_start = int(datetime(now.year, now.month, now.day, now.hour).timestamp() * 1000)

    pipeline = [
        {"$match": {"start": current_slot_start}},
        {"$group": {"_id": "$room_id", "occupied": {"$sum": "$group_size"}}}
    ]
    result = list(res.aggregate(pipeline))
    return {item["_id"]: item["occupied"] for item in result}


@app.get("/slot-occupancy/{room_id}")
def slot_occupancy(room_id: str, start_ms: int = 0):
    """
    Returns the total occupied seats for a specific room + start timestamp (ms).
    Used by the booking form to show live capacity remaining for a chosen slot.
    """
    existing = list(res.find({"room_id": room_id, "start": start_ms}))
    occupied = sum(b.get("group_size", 1) for b in existing)
    return {"occupied": occupied}


@app.put("/internal/update-room-id")
def update_room_id(old_id: str, new_id: str):
    """Internal endpoint called by room-service to maintain data consistency."""
    res.update_many({"room_id": old_id}, {"$set": {"room_id": new_id}})
    return {"msg": f"updated reservations for {old_id} to {new_id}"}