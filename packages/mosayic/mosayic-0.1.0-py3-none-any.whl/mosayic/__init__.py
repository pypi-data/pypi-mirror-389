
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mosayic.logger import get_logger
from mosayic.services.notifications.routes import notifications_router
from mosayic.webpages.routes import webpages_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


# Set up FastAPI app - docs will be disabled dynamically in production
app = FastAPI(
    lifespan=lifespan,
    generate_unique_id_function=lambda route: route.name
)


# TODO: Set explicit CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(webpages_router)
app.include_router(notifications_router)


# Try to load mosaygent dev routes if available (dev dependency)
try:
    import mosaygent
except ImportError:
    logger.debug("Mosaygent not installed (production mode)")
