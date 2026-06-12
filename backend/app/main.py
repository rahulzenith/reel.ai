from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.routes import runs, status, ws
from .core.config import settings
from .lifespan import lifespan


def create_app() -> FastAPI:
    app = FastAPI(title="Shorts Factory", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(runs.router, prefix="/api")
    app.include_router(status.router, prefix="/api")
    app.include_router(ws.router)

    # Serve rendered videos so the dashboard can preview them
    settings.outputs_path.mkdir(parents=True, exist_ok=True)
    app.mount("/outputs", StaticFiles(directory=settings.outputs_path), name="outputs")

    return app


app = create_app()
