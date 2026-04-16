from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICES = {
    "auth": "http://auth-service:8000",
    "room": "http://room-service:8000",
    "res": "http://reservation-service:8000",
    "user": "http://user-service:8000"
}

async def forward(path, method, body=None, headers=None, params=None):
    """Transparently forward requests to services."""
    async with httpx.AsyncClient() as client:
        # We pass content=body instead of json=data to support binary/multipart data.
        resp = await client.request(
            method,
            path,
            content=body,
            headers=headers,
            params=params,
            timeout=10.0
        )
        
        # Exclude certain headers that shouldn't be returned to the client
        exclude_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        resp_headers = {k: v for k, v in resp.headers.items() if k.lower() not in exclude_headers}
        
        return Response(content=resp.content, status_code=resp.status_code, headers=resp_headers)

@app.post("/login")
async def login(req: Request):
    body = await req.body()
    return await forward(f"{SERVICES['auth']}/login", "POST", body, dict(req.headers))

@app.post("/register")
async def register(req: Request):
    body = await req.body()
    return await forward(f"{SERVICES['auth']}/register", "POST", body, dict(req.headers))

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(path: str, req: Request):
    # Forward original headers but remove Host as it causes routing issues
    headers = dict(req.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)

    # Determine backend service
    if path.startswith("rooms") or path.startswith("uploads"):
        url = f"{SERVICES['room']}/{path}"
    elif path.startswith("reserve") or path.startswith("my-reservations") or path.startswith("all-reservations") or path.startswith("room-schedule") or path.startswith("occupancy-summary") or path.startswith("slot-occupancy"):
        url = f"{SERVICES['res']}/{path}"
    elif path.startswith("users"):
        url = f"{SERVICES['user']}/{path}"
    else:
        return Response(content='{"error": "unknown route"}', status_code=404, media_type="application/json")

    # Read binary body if it exists
    body = await req.body()
    
    return await forward(url, req.method, body, headers, dict(req.query_params))