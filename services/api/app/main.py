import time
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import api, ws
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.graph.build import build_interview_graph
from app.providers.llm.base import LLMProvider
from app.providers.llm.factory import build_llm


def create_app(
    *,
    settings: Settings | None = None,
    llm: LLMProvider | None = None,
    clock: Callable[[], float] = time.time,
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, json=settings.app_env == "production")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = settings
        app.state.llm = llm or build_llm(settings)
        app.state.clock = clock
        app.state.graph = build_interview_graph(app.state.llm, settings, clock=clock)
        yield
        if close := getattr(app.state.llm, "aclose", None):
            await close()

    app = FastAPI(title="Interview Coach API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api.router)
    app.include_router(ws.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "env": settings.app_env}

    return app


app = create_app()
