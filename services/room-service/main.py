import os
import shutil
import httpx
from fastapi import FastAPI, Depends, Body, HTTPException, File, UploadFile
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient

from auth import get_user, require_role

app = FastAPI()

# Database setup
client = MongoClient("mongodb://mongodb:27017")
db = client["study"]
rooms_col = db["rooms"]

RESERVATION_SERVICE_URL = "http://reservation-service:8000"

# Ensure uploads directory exists
UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Serve static files so images can be viewed via /uploads/filename.jpg
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.post("/rooms")
def create(room: dict = Body(...), user=Depends(get_user)):
    require_role(user, ["staff", "admin"])
    rooms_col.insert_one(room)
    return {"msg": "created"}

@app.put("/rooms/{room_id}")
def update(room_id: str, data: dict = Body(...), user=Depends(get_user)):
    require_role(user, ["staff", "admin"])
    
    # Handle Room ID change (renaming files and syncing with reservation-service)
    new_id = data.get("room_id")
    if new_id and new_id != room_id:
        room = rooms_col.find_one({"room_id": room_id})
        if room:
            # 1. Rename photo file if it exists
            if room.get("photo_url"):
                old_filename = room["photo_url"].split("/")[-1]
                ext = old_filename.split(".")[-1]
                new_filename = f"{new_id}.{ext}"
                
                old_path = os.path.join(UPLOAD_DIR, old_filename)
                new_path = os.path.join(UPLOAD_DIR, new_filename)
                
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                
                data["photo_url"] = f"/uploads/{new_filename}"
            
            # 2. Sync with reservation-service (Internal API call)
            try:
                httpx.put(f"{RESERVATION_SERVICE_URL}/internal/update-room-id?old_id={room_id}&new_id={new_id}", timeout=5.0)
            except Exception as e:
                print(f"Error syncing with reservation-service: {e}")

    rooms_col.update_one({"room_id": room_id}, {"$set": data})
    return {"msg": "updated"}

@app.delete("/rooms/{room_id}")
def delete(room_id: str, user=Depends(get_user)):
    require_role(user, ["staff", "admin"])
    # Also delete photo file if exists
    room = rooms_col.find_one({"room_id": room_id})
    if room and room.get("photo_url"):
        filename = room["photo_url"].split("/")[-1]
        filepath = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            
    rooms_col.delete_one({"room_id": room_id})
    return {"msg": "deleted"}

@app.get("/rooms")
def get_all():
    return list(rooms_col.find({}, {"_id": 0}))

@app.get("/rooms/{room_id}")
def get_one(room_id: str):
    room = rooms_col.find_one({"room_id": room_id}, {"_id": 0})
    if not room:
        raise HTTPException(404, "Room not found")
    return room

@app.post("/rooms/{room_id}/photo")
async def upload_photo(room_id: str, file: UploadFile = File(...), user=Depends(get_user)):
    require_role(user, ["staff", "admin"])
    
    # 1. Validate file extension
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png"]:
        raise HTTPException(400, "Only JPG or PNG images are allowed")
    
    # 2. Check if room exists
    room = rooms_col.find_one({"room_id": room_id})
    if not room:
        raise HTTPException(404, "Room not found")

    # 3. Save file using room_id as name to ensure consistency and clean overwrites
    filename = f"{room_id}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 4. Update the room record with the relative photo path
    photo_url = f"/uploads/{filename}"
    rooms_col.update_one({"room_id": room_id}, {"$set": {"photo_url": photo_url}})
    
    return {"photo_url": photo_url}