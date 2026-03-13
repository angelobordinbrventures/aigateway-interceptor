import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from api.config import settings
from api.database.connection import close_db, init_db
from api.routers import logs, policies, settings as settings_router, stats, users


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="AIGateway Interceptor API",
    description="Backend API for the AIGateway Interceptor",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(policies.router)
app.include_router(logs.router)
app.include_router(users.router)
app.include_router(stats.router)
app.include_router(settings_router.router)


@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, str]:
    return {"status": "healthy"}


@app.get("/certificate/ca.pem", tags=["certificate"])
async def download_ca_certificate():
    cert_paths = [
        "/app/certs/mitmproxy-ca-cert.pem",  # Docker path
        os.path.join(os.path.dirname(__file__), "..", "certs", "mitmproxy-ca-cert.pem"),  # Local dev
        os.path.expanduser("~/.mitmproxy/mitmproxy-ca-cert.pem"),  # Default mitmproxy path
    ]
    for path in cert_paths:
        if os.path.exists(path):
            return FileResponse(
                path,
                media_type="application/x-pem-file",
                filename="aigateway-ca-cert.pem",
            )
    raise HTTPException(status_code=404, detail="CA certificate not found")
