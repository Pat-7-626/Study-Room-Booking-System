from jose import jwt
from fastapi import Header, HTTPException

SECRET = "SECRET123"

def get_user(authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]
        return jwt.decode(token, SECRET)
    except:
        raise HTTPException(401, "Invalid token")

def require_role(user, roles):
    if user["role"] not in roles:
        raise HTTPException(403, "Forbidden")