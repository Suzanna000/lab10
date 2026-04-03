import os
from contextlib import asynccontextmanager

import httpx
import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

GO_BASE = os.getenv("GO_SERVICE_URL", "http://127.0.0.1:8080")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-change-in-production")

security = HTTPBearer(auto_error=False)


def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="invalid token") from e


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(base_url=GO_BASE, timeout=10.0)
    yield
    await app.state.http.aclose()


app = FastAPI(title="Lab10 Python gateway", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "upstream": GO_BASE}


@app.get("/jwt/verify")
async def jwt_verify(creds: HTTPAuthorizationCredentials | None = Depends(security)):
    if creds is None:
        raise HTTPException(status_code=401, detail="missing bearer token")
    payload = decode_jwt(creds.credentials)
    return {"valid": True, "claims": payload}


@app.get("/upstream/protected")
async def upstream_protected(creds: HTTPAuthorizationCredentials | None = Depends(security)):
    if creds is None:
        raise HTTPException(status_code=401, detail="missing bearer token")
    decode_jwt(creds.credentials)
    client: httpx.AsyncClient = app.state.http
    resp = await client.get(
        "/api/protected",
        headers={"Authorization": f"Bearer {creds.credentials}"},
    )
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()
