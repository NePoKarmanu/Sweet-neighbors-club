from fastapi import FastAPI

from backend.core.middleware import setup_middlewares
from backend.routers import auth_router, listing_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Sweet Neighbors Club API",
        version="0.1.0",
    )
    setup_middlewares(app)

    @app.get("/healthcheck")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(listing_router)
    app.include_router(auth_router)

    return app


app = create_app()
