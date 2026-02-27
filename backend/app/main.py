from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para registro de despesas pessoais, permitindo aos usuários acompanhar seus gastos e analisar suas finanças de forma eficiente.",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)
#app = FastAPI(
#    title="Finanças Cristãs API",
#    version="0.1.0",
#    root_path="/"
#)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "API de registro de despesas.", "status": "online"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
