from fastapi import FastAPI

from backend.routers import auth_router, root_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Sweet Neighbors Club API",
        version="0.1.0",
    )
    app.include_router(root_router)
    app.include_router(auth_router)

    return app


app = create_app()
