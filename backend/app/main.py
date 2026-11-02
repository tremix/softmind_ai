from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.nx.client import NxClient
from app.nx.mock import MockNxClient
from app.routers import analytics, cameras, course, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.mock_mode:
        app.state.nx = MockNxClient()
    else:
        app.state.nx = NxClient(
            settings.nx_url, settings.nx_username, settings.nx_password, settings.nx_verify_tls
        )
    yield
    await app.state.nx.close()


app = FastAPI(title="SoftMind AI — API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (cameras.router, analytics.router, webhooks.router, course.router):
    app.include_router(r)


@app.get("/api/health")
async def health():
    return {"status": "ok", "mock": get_settings().mock_mode}
