from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.database.connection import close_db, init_db
from api.routers import logs, policies, stats, users


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


@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, str]:
    return {"status": "healthy"}
