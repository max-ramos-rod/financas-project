import logging

from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "about:blank",
            "title": _status_title(exc.status_code),
            "status": exc.status_code,
            "detail": exc.detail,
        },
        headers=getattr(exc, "headers", None) or {},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    detail = "; ".join(
        f"{'.'.join(str(l) for l in e['loc'])}: {e['msg']}" for e in errors
    )
    return JSONResponse(
        status_code=422,
        content={
            "type": "about:blank",
            "title": "Unprocessable Entity",
            "status": 422,
            "detail": detail,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred. Please try again later.",
        },
    )


def _status_title(status_code: int) -> str:
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
    }
    return titles.get(status_code, "Error")
