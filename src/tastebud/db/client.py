import asyncpg

from tastebud.config import get_settings

_pool: asyncpg.Pool | None = None


async def init_db_pool() -> None:
    """Initialize the asyncpg connection pool."""
    global _pool
    dsn = get_settings().database_url
    _pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=2,
        max_size=10,
        # Supabase pooler (PgBouncer) requires statement_cache_size=0
        statement_cache_size=0,
    )


async def get_pool() -> asyncpg.Pool:
    """Get the active connection pool. Raises if not initialized."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized")
    return _pool


async def close_db_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
