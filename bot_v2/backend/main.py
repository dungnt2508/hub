"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routers import bot_router, admin_router

app = FastAPI(
    title="Bot V2 API",
    description="Multi-tenant catalog chatbot service",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(bot_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Bot V2",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}
