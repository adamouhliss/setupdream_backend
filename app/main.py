from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os
import logging

from .core.config import settings
from .core.database import engine
from .models import *  # Import all models
from .api.v1.auth import router as auth_router
from .api.v1.orders import router as orders_router
from .api.v1.products import router as products_router
from .api.v1.users import router as users_router
from .api.v1.settings import router as settings_router
from .api.v1.contact import router as contact_router
from .api.v1.seo import router as seo_router
from .api.v1.influencers import router as influencers_router

# Create tables with error handling (database already deployed)
from .core.database import Base
try:
    Base.metadata.create_all(bind=engine)
    logging.info("Connected to existing database successfully")
except Exception as e:
    logging.error(f"Database connection issue: {e}")
    logging.info("App will continue - database may initialize later")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://localhost:5174",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:8080",
        "https://carre-sport.vercel.app",  # Production frontend
        "https://carre-sport-production.up.railway.app",  # Production backend
        "https://carresports.ma",
        "https://www.carresports.ma",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Create upload directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Mount static files
# Custom StaticFiles to add Cache-Control headers
from fastapi.staticfiles import StaticFiles
from starlette.types import Scope, Receive, Send

class CachedStaticFiles(StaticFiles):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Add Cache-Control header (1 year cache for static assets)
                headers = dict(message.get("headers", []))
                headers[b"cache-control"] = b"public, max-age=31536000, immutable"
                message["headers"] = list(headers.items())
            await send(message)
        await super().__call__(scope, receive, send_wrapper)

# Mount static files with caching
app.mount("/uploads", CachedStaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(orders_router, prefix=f"{settings.API_V1_STR}/orders", tags=["orders"])
app.include_router(products_router, prefix=f"{settings.API_V1_STR}/products", tags=["products"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(settings_router, prefix=f"{settings.API_V1_STR}/settings", tags=["settings"])
app.include_router(contact_router, prefix=f"{settings.API_V1_STR}/contact", tags=["contact"])
app.include_router(seo_router, prefix=f"{settings.API_V1_STR}/seo", tags=["seo"])
app.include_router(influencers_router, prefix=f"{settings.API_V1_STR}/influencers", tags=["influencers"])

@app.get("/")
async def root():
    return {"message": "Welcome to Carré Sports API", "version": "1.0.1"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": "carre-sports-full"}

@app.get("/force-deploy")
async def force_deploy():
    """Endpoint to verify new deployment is working"""
    return {"message": "NEW DEPLOYMENT WORKING", "timestamp": "2025-01-07", "version": "1.0.1"} 