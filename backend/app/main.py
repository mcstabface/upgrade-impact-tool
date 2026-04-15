from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.review_items import router as review_items_router
from app.api.v1.review_actions import router as review_actions_router
from app.api.v1.review_queue import router as review_queue_router
from app.api.v1.analyses import router as analyses_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.findings import router as findings_router
from app.api.v1.health import router as health_router
from app.api.v1.meta import router as meta_router
from app.api.v1.intakes import router as intakes_router

app = FastAPI(
    title="Upgrade Impact Analysis Tool",
    version="0.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(meta_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(analyses_router, prefix="/api/v1")
app.include_router(findings_router, prefix="/api/v1")
app.include_router(intakes_router, prefix="/api/v1")
app.include_router(review_queue_router, prefix="/api/v1")
app.include_router(review_actions_router, prefix="/api/v1")
app.include_router(review_items_router, prefix="/api/v1")