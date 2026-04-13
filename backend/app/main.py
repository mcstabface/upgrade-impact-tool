from fastapi import FastAPI

from app.api.v1.health import router as health_router

app = FastAPI(
    title="Upgrade Impact Analysis Tool",
    version="0.0.1",
)

app.include_router(health_router, prefix="/api/v1")