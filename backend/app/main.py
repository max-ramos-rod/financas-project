from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.errors import http_exception_handler, validation_exception_handler
from app.core.limiter import limiter, rate_limit_handler

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para registro de despesas pessoais, permitindo aos usuários acompanhar seus gastos e analisar suas finanças de forma eficiente.",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RFC 7807 error handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def read_root():
    return {"message": "API de registro de despesas.", "status": "online"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
