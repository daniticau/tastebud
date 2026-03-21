# Tastebud

Crowd-sourced food recommendations through Poke. No reviews, no ratings, no forms.
People just text their Poke agent asking where to eat. Poke recommends places based
on what other real people actually thought. After you visit somewhere, Poke casually
asks how it was — a few messages in DMs, and your opinion gets anonymized and added
to the collective knowledge. Nobody writes a review. Poke just figures it out.

The more people use it, the better it gets. That's the whole thing.

## How It Works

```
User: "Where should I eat tonight? Craving Thai near downtown"
      ↓
Poke calls search_recommendations(cuisine="thai", city="san diego", neighborhood="downtown")
      ↓
Tastebud returns crowd-sourced places ranked by sentiment, volume, recency
      ↓
Poke: "People have been loving Sab E Lee — really strong crowd sentiment
       for their pad see ew. Also heard good things about Supannee House."
      ↓
[user goes to dinner]
      ↓
Poke (later, casually): "How was Sab E Lee?"
User: "Incredible. The green curry was unreal."
      ↓
Poke calls log_feedback(place="Sab E Lee", city="san diego", sentiment="positive",
                         comment="green curry stood out", cuisine_tags=["thai"])
      ↓
Anonymized. Stored. Next person asking about Thai food in SD gets better recs.
```

No user profiles. No tracking. Just aggregate sentiment from real people.

## Why This Works

**Yelp/Google Reviews are broken.** People only review when they're furious or when
the waiter asks them to. The data is skewed, gameable, and full of noise. Most people
who had a great meal never write a word about it.

**Tastebud captures the silent majority.** Poke already has the conversation. A couple
messages after dinner — "How was it?" "So good, the pasta was incredible" — and that
signal is captured. Zero friction. The user barely notices they're contributing.

**Network effect moat.** Every user makes the data better for every other user. Early
adopters seed the database organically. There's no cold start death spiral because
Poke falls back to its own knowledge when the database is empty, and the feedback
loop bootstraps itself.

## Architecture

Tastebud is a Poke recipe — an MCP (Model Context Protocol) server that exposes tools
to Poke's agents via HTTPS.

```
User (iMessage) <-> Poke Agent <-> Tastebud MCP Server <-> Supabase (PostgreSQL)
```

### Stack
- **Server**: Python, FastAPI + FastMCP (MCP protocol handler)
- **Database**: Supabase (PostgreSQL + pg_trgm for fuzzy name matching)
- **Deploy**: Railway
- **Auth**: None for MVP (all data is public and anonymized)

### Project Structure

```
tastebud/
├── pyproject.toml
├── CLAUDE.md
├── .gitignore
├── .env.example
├── Dockerfile
├── src/
│   └── tastebud/
│       ├── __init__.py
│       ├── main.py              # FastAPI app + FastMCP mount
│       ├── server.py            # FastMCP instance, instructions, tool registration
│       ├── config.py            # pydantic-settings
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── search.py        # search_recommendations
│       │   ├── feedback.py      # log_feedback
│       │   └── trending.py      # get_trending
│       ├── db/
│       │   ├── __init__.py
│       │   ├── client.py        # asyncpg connection pool
│       │   ├── models.py        # Pydantic v2 models
│       │   └── queries.py       # SQL query functions
│       └── services/
│           ├── __init__.py
│           ├── normalizer.py    # Place name normalization + fuzzy match
│           └── ranking.py       # Recommendation scoring
├── migrations/
│   └── 001_initial.sql
├── scripts/
│   └── seed.py                  # Cold start seed data
└── tests/
    ├── conftest.py
    ├── test_tools.py
    ├── test_normalizer.py
    └── test_ranking.py
```

## MCP Tools

### `search_recommendations`

Primary tool. Called when a user asks for food recs.

| Parameter      | Type       | Required | Description                          |
|----------------|------------|----------|--------------------------------------|
| cuisine        | string     | no       | Type of food (thai, pizza, sushi)    |
| city           | string     | yes      | City name                            |
| neighborhood   | string     | no       | Area within the city                 |
| limit          | int (1-10) | no       | Max results, default 5               |

Returns ranked places with: name, city, neighborhood, cuisine tags, sentiment summary,
positive percentage, total review count, last reviewed date.

### `log_feedback`

Called after a user shares how a dining experience went.

| Parameter      | Type       | Required | Description                                |
|----------------|------------|----------|--------------------------------------------|
| place_name     | string     | yes      | Restaurant name as user mentioned it       |
| city           | string     | yes      | City                                       |
| neighborhood   | string     | no       | Neighborhood if known                      |
| cuisine_tags   | string[]   | no       | Cuisine types, inferred from conversation  |
| sentiment      | string     | yes      | "positive", "negative", or "neutral"       |
| comment        | string     | no       | One-sentence anonymized summary            |
| visit_context  | string     | no       | "dinner", "lunch", "takeout", etc.         |

Creates the place if it doesn't exist. Updates aggregate scores atomically.

### `get_trending`

Called when a user asks what's hot or popular recently.

| Parameter | Type       | Required | Description                    |
|-----------|------------|----------|--------------------------------|
| city      | string     | yes      | City                           |
| days      | int (7-30) | no       | Look-back window, default 30   |
| limit     | int (1-10) | no       | Max results, default 5         |

Returns places with the most positive recent buzz.

## Database

Two tables. Deliberately minimal.

### `places`

```sql
CREATE TABLE places (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name  TEXT NOT NULL,                -- "Joe's Pizza"
    name_normalized TEXT NOT NULL,                -- "joes pizza" (lowered, stripped)
    city            TEXT NOT NULL,
    neighborhood    TEXT,
    cuisine_tags    TEXT[] DEFAULT '{}',

    -- Precomputed aggregates (updated on each feedback)
    positive_count  INTEGER NOT NULL DEFAULT 0,
    negative_count  INTEGER NOT NULL DEFAULT 0,
    neutral_count   INTEGER NOT NULL DEFAULT 0,
    avg_rating      REAL,                         -- (positive + 0.5*neutral) / total

    last_feedback_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_places_name_trgm ON places USING gin (name_normalized gin_trgm_ops);
CREATE INDEX idx_places_city ON places (city);
CREATE INDEX idx_places_cuisine ON places USING gin (cuisine_tags);
CREATE INDEX idx_places_city_rating ON places (city, avg_rating DESC NULLS LAST);
```

### `feedback`

```sql
CREATE TABLE feedback (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    place_id        UUID NOT NULL REFERENCES places(id),
    sentiment       TEXT NOT NULL CHECK (sentiment IN ('positive', 'negative', 'neutral')),
    comment         TEXT,
    visit_context   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_feedback_place_id ON feedback (place_id);
CREATE INDEX idx_feedback_created_at ON feedback (created_at DESC);
```

No user IDs. No session tokens. No way to reconstruct who said what.

Aggregates on `places` are updated atomically on each feedback insert — the search
hot path never touches the `feedback` table, just reads precomputed scores from
`places`.

## Ranking

Score = quality x volume x recency

```
score = avg_rating
      * ln(max(total_reviews, 2))
      * (1 / (1 + age_seconds / 2592000))
```

| Component | Formula                            | Why                                           |
|-----------|------------------------------------|-----------------------------------------------|
| Quality   | avg_rating (0-1)                   | Higher positive ratio = higher rank            |
| Volume    | ln(total_reviews)                  | Log scale: 100 reviews doesn't crush 10       |
| Recency   | 1 / (1 + age / 30 days)           | 30-day half-life. Stale places decay naturally |

Computed entirely in SQL. Single query, no application-level sorting.

## Place Name Deduplication

The hardest technical problem. "Joe's Pizza", "joes pizza", "Joe's on 5th St" must
resolve to the same place.

### Normalization pipeline
1. Lowercase
2. Strip possessives ('s)
3. Remove punctuation except hyphens
4. Collapse whitespace
5. Remove common suffixes (restaurant, cafe, bar, grill, kitchen, eatery)
6. Strip street-address fragments ("on 5th", "at main st")

### Matching
1. Exact match on normalized name + city
2. Fuzzy match via pg_trgm (similarity > 0.6) within same city
3. No match → create new place

The city filter prevents cross-city false matches. The 0.6 threshold is tunable.

## Server Instructions

These tell Poke's agents when and how to use Tastebud's tools. This is the most
critical piece of the integration — bad instructions = tools never get called.

```
Tastebud is a crowd-sourced food recommendation engine. It stores anonymized
feedback from real people and uses that data to recommend places.

WHEN TO USE EACH TOOL:

search_recommendations:
- When user asks for food recommendations, where to eat, restaurant suggestions
- ALWAYS try Tastebud first before using your own knowledge
- If Tastebud returns empty, fall back to your own knowledge but mention it

log_feedback:
- When user shares how a dining experience went (after an actual visit)
- When user volunteers a restaurant opinion (even unsolicited)
- Infer sentiment naturally from conversation — don't ask "positive or negative?"
- Anonymize comments: strip names, dates, identifying details

get_trending:
- When user asks what's popular, trending, or buzzing in their city
- When user wants to explore without a specific cuisine

FEEDBACK COLLECTION:
After recommending a place, follow up later (after 2-3 more messages, or in
a future conversation) to casually ask how it went. Keep it natural:
"Hey, did you end up trying [place]? How was it?"
Don't push if they haven't gone yet.

RULES:
- All data is anonymized. Never mention profiles or tracking.
- Never fabricate reviews. If the database is empty, say so.
- City is required for search. If unknown, ask or infer from context.
```

## Cold Start

The empty database is a real problem. Three-layer strategy:

1. **Seed script** — Insert 50-100 well-known places per launch city with zero
   reviews. They show up as "known places" but rank at the bottom of any scored query.

2. **Instruction-driven bootstrapping** — Even when Tastebud returns nothing and Poke
   uses its own knowledge, the instructions tell Poke to follow up about wherever the
   user went. That feedback creates the place entry organically.

3. **Graceful empty state** — When no results exist, return a message like: "No
   crowd-sourced recommendations yet for Thai in Downtown SD. You're among the first!"
   This sets expectations and primes the feedback loop.

## Future: Taste Groups

Not in MVP. But the natural extension is friend groups sharing recs — your friend
circle's collective taste. Would require:
- Optional anonymous group tokens (still no user IDs, just group membership signals)
- Group-scoped queries ("what do my friends recommend?")
- Invite links to join taste groups

The schema supports this — add a `group_token` column to `feedback` and filter on it.
No user identity needed, just "this feedback came from someone in group X."

## Deployment

### Railway (MCP server)
- $5/month free credit covers the MVP
- No cold starts (important for MCP session state)
- One-click deploy from GitHub via Dockerfile
- HTTPS included

### Supabase (database)
- Free tier: 500MB storage, 2 projects
- Enable pg_trgm extension via SQL editor
- Connect via direct connection string (not pooler) for asyncpg
- Run `migrations/001_initial.sql` on setup

### Environment Variables
```
TASTEBUD_DATABASE_URL=postgresql://...  # Supabase direct connection string
PORT=8000                                # Railway sets this automatically
```

## Implementation Sequence

| Step | What                                                    |
|------|---------------------------------------------------------|
| 1    | Scaffold: pyproject.toml, CLAUDE.md, .gitignore, dirs   |
| 2    | config.py + db/client.py + migrations/001_initial.sql   |
| 3    | services/normalizer.py + tests                          |
| 4    | db/queries.py — all SQL functions                       |
| 5    | services/ranking.py                                     |
| 6    | tools: search.py, feedback.py, trending.py              |
| 7    | server.py — FastMCP instance + instructions             |
| 8    | main.py — FastAPI wrapper + mount                       |
| 9    | Supabase project setup + run migrations                 |
| 10   | Local testing with MCP Inspector                        |
| 11   | Dockerfile + Railway deploy                             |
| 12   | Seed script + cold start data                           |
| 13   | Submit to Poke recipes                                  |

## Dependencies

```toml
[project]
name = "tastebud"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastmcp>=2.0",
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "asyncpg>=0.30",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",
]
```

## Key Design Decisions

**Precomputed aggregates on `places` instead of computing on read.**
The search path is the hot path. With thousands of feedback rows, a GROUP BY on every
search would be slow. Slightly more complex writes, but reads stay O(1).

**pg_trgm instead of pgvector for name matching.**
Restaurant names are short strings, not semantic documents. Trigram fuzzy matching is
the right tool — simpler, faster, no embedding model needed.

**asyncpg direct instead of Supabase Python client.**
The Supabase client goes through PostgREST (HTTP overhead), doesn't support pg_trgm
operators, and is synchronous. For an async MCP server with fuzzy matching, asyncpg
over the direct connection string is faster and more flexible.

**No user IDs, even hashed.**
Without any ID you can't prevent abuse (100 fake reviews). But hashed IDs create
linkability risk. For MVP, Poke's conversation context provides natural rate-limiting.
Add rate-limiting by session token later if abuse emerges.

**Three tools instead of one omnibus tool.**
Each tool maps to a distinct user intent. Poke's agent can unambiguously pick the
right one. An omnibus tool with a mode parameter would confuse the agent instructions.
