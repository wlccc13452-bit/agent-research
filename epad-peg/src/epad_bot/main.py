"""Main FastAPI application entry point."""

import logging

from fastapi import FastAPI

from epad_bot import __version__
from epad_bot.api.routes import router as api_router
from epad_bot.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    # Include routers
    app.include_router(api_router, prefix="/api")

    @app.on_event("startup")
    async def startup_event() -> None:
        """Application startup tasks."""
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Application shutdown tasks."""
        logger.info(f"Shutting down {settings.app_name}")

    return app


# Create application instance
app = create_app()


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "epad_bot.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
