from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routers.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and tables
    init_db()
    yield


app = FastAPI(
    title="Lyftr AI LLM Service",
    version="1.0.0",
    docs_url=None,  # Only expose requested endpoints
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

# CORS configuration
raw_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=raw_origins if raw_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach router with exactly the 3 public endpoints
app.include_router(chat_router)
