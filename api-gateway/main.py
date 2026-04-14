from fastapi import FastAPI, Request
import httpx

app = FastAPI()

AUTH = "http://auth-service:8000"
ROOM = "http://room-service:8000"
RES = "http://reservation-service:8000"
USER = "http://user-service:8000"

@app.post("/register")
async def register(data: dict):
    async with httpx.AsyncClient() as c:
        return (await c.post(f"{AUTH}/register", json=data)).json()

@app.post("/login")
async def login(data: dict):
    async with httpx.AsyncClient() as c:
        return (await c.post(f"{AUTH}/login", json=data)).json()

@app.get("/rooms")
async def rooms():
    async with httpx.AsyncClient() as c:
        return (await c.get(f"{ROOM}/rooms")).json()

@app.post("/rooms")
async def create_room(data: dict):
    async with httpx.AsyncClient() as c:
        return (await c.post(f"{ROOM}/rooms", json=data)).json()

@app.post("/reserve")
async def reserve(data: dict):
    async with httpx.AsyncClient() as c:
        return (await c.post(f"{RES}/reserve", json=data)).json()

@app.get("/reservations")
async def reservations():
    async with httpx.AsyncClient() as c:
        return (await c.get(f"{RES}/reservations")).json()