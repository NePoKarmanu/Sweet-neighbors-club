from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title="Sweet Neighbors Club API",
        version="0.1.0",
    )

    @app.get("/", tags=["root"])
    async def root() -> dict[str, str]:
        return {"detail": "Endpoint is ready"}

    return app


app = create_app()
