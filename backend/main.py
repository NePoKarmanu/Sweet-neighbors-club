from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.core.middleware import setup_middlewares
from backend.exceptions import AppError
from backend.routers import auth_router, listing_router, notifications_router, scraping_router
from backend.utils.jwt import warn_if_weak_jwt_secret


def create_app() -> FastAPI:
    warn_if_weak_jwt_secret()
    app = FastAPI(
        title="Sweet Neighbors Club API",
        version="0.1.0",
    )
    setup_middlewares(app)

    @app.get("/healthcheck")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "code": exc.code,
                "meta": exc.meta,
            },
        )

    app.include_router(listing_router)
    app.include_router(notifications_router)
    app.include_router(scraping_router)
    app.include_router(auth_router)

    return app


app = create_app()
