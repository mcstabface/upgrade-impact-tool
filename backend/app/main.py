import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.review_items import router as review_items_router
from app.api.v1.review_actions import router as review_actions_router
from app.api.v1.review_queue import router as review_queue_router
from app.api.v1.analyses import router as analyses_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.findings import router as findings_router
from app.api.v1.health import router as health_router
from app.api.v1.meta import router as meta_router
from app.api.v1.intakes import router as intakes_router
from app.api.v1.review_comments import router as review_comments_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.observability import router as observability_router
from app.api.v1.usage_events import router as usage_events_router
from app.core.errors import AppError

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Upgrade Impact Analysis Tool",
    version="0.0.1",
)


def build_error_payload(
    *,
    error_class: str,
    message: str,
    recovery_guidance: str,
    retryable: bool = False,
) -> dict:
    return {
        "error_class": error_class,
        "message": message,
        "recovery_guidance": recovery_guidance,
        "retryable": retryable,
    }


@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    validation_messages = []
    for error in exc.errors():
        location = " -> ".join(str(part) for part in error.get("loc", []))
        message = error.get("msg", "Invalid request value")
        validation_messages.append(f"{location}: {message}")

    return JSONResponse(
        status_code=422,
        content=build_error_payload(
            error_class="VALIDATION_ERROR",
            message="Request validation failed.",
            recovery_guidance="Review the submitted values, correct the highlighted fields, and retry the action.",
            retryable=False,
        )
        | {"details": validation_messages},
    )


@app.exception_handler(HTTPException)
async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed."

    if exc.status_code == 403:
        payload = build_error_payload(
            error_class="PERMISSION_ERROR",
            message=detail,
            recovery_guidance="Use a role with permission for this action or return to a screen available to your role.",
            retryable=False,
        )
    elif exc.status_code == 404:
        payload = build_error_payload(
            error_class="SOURCE_DATA_ERROR",
            message=detail,
            recovery_guidance="Return to the previous screen, confirm the target record still exists, and retry from there.",
            retryable=False,
        )
    elif exc.status_code in (400, 422):
        payload = build_error_payload(
            error_class="VALIDATION_ERROR",
            message=detail,
            recovery_guidance="Review the input values and current state, correct any issues, and retry the action.",
            retryable=False,
        )
    else:
        payload = build_error_payload(
            error_class="INTERNAL_ERROR",
            message=detail,
            recovery_guidance="Retry the action. If the problem continues, return to the previous screen and try again later.",
            retryable=False,
        )

    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled exception during request processing",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=500,
        content=build_error_payload(
            error_class="INTERNAL_ERROR",
            message="An unexpected system error occurred.",
            recovery_guidance="Retry the action. If the issue continues, return to the previous screen and try again later.",
            retryable=True,
        ),
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
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(observability_router, prefix="/api/v1")
app.include_router(usage_events_router, prefix="/api/v1")
app.include_router(analyses_router, prefix="/api/v1")
app.include_router(findings_router, prefix="/api/v1")
app.include_router(intakes_router, prefix="/api/v1")
app.include_router(review_queue_router, prefix="/api/v1")
app.include_router(review_actions_router, prefix="/api/v1")
app.include_router(review_items_router, prefix="/api/v1")
app.include_router(review_comments_router, prefix="/api/v1")