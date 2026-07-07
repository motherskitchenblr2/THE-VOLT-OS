"""VOLT OS — Main application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.plugins import router as plugins_router
from src.api.pipelines import router as pipelines_router
from src.api.memory import router as memory_router
from src.api.observability import router as observability_router
from src.api.artifacts import router as artifacts_router
from src.api.deployment import router as deployment_router
from src.auth.middleware import ClerkAuthMiddleware
from src.core.database import engine, Base

app = FastAPI(
    title="VOLT OS",
    description="AI Workforce Platform — Modular AI Operating System",
    version="0.1.0",
)

# Auth middleware
app.add_middleware(ClerkAuthMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(plugins_router)
app.include_router(pipelines_router)
app.include_router(memory_router)
app.include_router(observability_router)
app.include_router(artifacts_router)
app.include_router(deployment_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
