# Tastebud

Crowd-sourced food recommendation engine, deployed as a Poke recipe (MCP server).

## Architecture
- **Server**: Python FastAPI + FastMCP v3.x, mounted at `/mcp`
- **Database**: Supabase (PostgreSQL + pg_trgm for fuzzy name matching)
- **Deploy**: Render via Dockerfile

## Key Files
- `src/tastebud/main.py` — FastAPI entry point, mounts MCP at `/mcp`
- `src/tastebud/server.py` — FastMCP instance with server instructions
- `src/tastebud/tools/` — MCP tools (search, feedback, trending)
- `src/tastebud/db/queries.py` — All SQL queries (asyncpg)
- `src/tastebud/services/normalizer.py` — Place name normalization + dedup
- `migrations/001_initial.sql` — Database schema

## Commands
- `uv sync` — install dependencies
- `uvicorn tastebud.main:app --reload` — run dev server
- `pytest` — run tests

## Design Decisions
- All data anonymized — no user IDs anywhere
- Precomputed aggregates on `places` table (reads never touch `feedback`)
- pg_trgm fuzzy matching for place name dedup (not pgvector)
- asyncpg direct connection (not Supabase Python client)
- Three separate MCP tools, not one omnibus tool
