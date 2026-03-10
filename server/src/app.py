import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.graph.state import CompiledStateGraph

from core import settings
from api.routes import routes

from db.session import engine
from db.models import Base

from contextlib import asynccontextmanager
from typing import Any


def create_app(
    graph: CompiledStateGraph, initial_graph_state: dict, graph_state_schema: Any
) -> FastAPI:
    """Factory function to create the FastAPI app and inject the graph."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # Inject the compiled graph into the application state
    # This makes it globally accessible to your routes
    app.state.graph = graph
    app.state.graph_state_schema = graph_state_schema
    app.state.initial_graph_state = initial_graph_state

    # Configure CORS for the Lovable frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers
    for router, prefix in routes:
        app.include_router(router, prefix=prefix)

    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    print("⏳ Initializing database tables...")

    # This checks the SQLite file. If the tables don't exist, it creates them.
    # If they already exist, it safely does nothing.
    Base.metadata.create_all(bind=engine)

    print("✅ Database ready.")

    yield  # The FastAPI server runs here

    # --- SHUTDOWN LOGIC ---
    print("🛑 Shutting down server...")


def serve(
    app: Any,
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False,
):
    """
    Main entry point to build and serve the debugger.
    Can be imported and called directly in the user's LangGraph project.
    """

    uvicorn.run(app, host=host, port=port, reload=reload)
