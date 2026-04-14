from fastapi import FastAPI
import httpx

app = FastAPI()

AUTH = "http://auth-service:8000"
ROOM = "http://room-service:8000"
RESERVE = "http://reservation-service:8000"

@app.post("/login")
async def login(data: dict):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{AUTH}/login", json=data)
    return res.json()

@app.post("/rooms")
async def create_room(data: dict):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{ROOM}/rooms", json=data)
    return res.json()

@app.get("/rooms")
async def get_rooms():
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{ROOM}/rooms")
    return res.json()

@app.post("/reserve")
async def reserve(data: dict):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{RESERVE}/reserve", json=data)
    return res.json()