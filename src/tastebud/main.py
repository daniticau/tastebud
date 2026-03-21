from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastmcp.utilities.lifespan import combine_lifespans

from tastebud.db.client import close_db_pool, init_db_pool
from tastebud.server import mcp


@asynccontextmanager
async def db_lifespan(app: FastAPI):
    """Manage database connection pool lifecycle."""
    await init_db_pool()
    yield
    await close_db_pool()


mcp_app = mcp.http_app(path="/")

app = FastAPI(
    title="Tastebud",
    version="0.1.0",
    lifespan=combine_lifespans(db_lifespan, mcp_app.lifespan),
)


@app.get("/health")
async def health():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}


app.mount("/mcp", mcp_app)
