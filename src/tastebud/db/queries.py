from uuid import UUID

from tastebud.config import get_settings
from tastebud.db.client import get_pool
from tastebud.db.models import (
    FeedbackResult,
    PlaceRecommendation,
    SearchResult,
    TrendingResult,
)
from tastebud.services.normalizer import normalize_city, normalize_name
from tastebud.services.ranking import compute_sentiment_summary


async def search_places(
    city: str,
    cuisine: str | None = None,
    neighborhood: str | None = None,
    limit: int = 5,
) -> SearchResult:
    """Search for places ranked by sentiment quality, volume, and recency."""
    pool = await get_pool()
    city_norm = normalize_city(city)
    halflife_seconds = get_settings().recency_halflife_days * 86400

    rows = await pool.fetch(
        """
        SELECT *,
            (COALESCE(avg_rating, 0)
             * ln(GREATEST(positive_count + negative_count + neutral_count, 2))
             * (1.0 / (1.0 + EXTRACT(EPOCH FROM (now() - COALESCE(last_feedback_at, created_at))) / $4))
            ) AS score
        FROM places
        WHERE city = $1
          AND ($2::TEXT IS NULL OR cuisine_tags @> ARRAY[$2])
          AND ($3::TEXT IS NULL OR neighborhood ILIKE $3)
          AND (positive_count + negative_count + neutral_count) >= $5
        ORDER BY score DESC
        LIMIT $6
        """,
        city_norm,
        cuisine.lower() if cuisine else None,
        neighborhood,
        float(halflife_seconds),
        get_settings().min_reviews_for_ranking,
        limit,
    )

    total_row = await pool.fetchval(
        "SELECT COUNT(*) FROM places WHERE city = $1",
        city_norm,
    )

    recs = []
    for row in rows:
        total = row["positive_count"] + row["negative_count"] + row["neutral_count"]
        pct = row["positive_count"] / max(total, 1)
        recs.append(PlaceRecommendation(
            name=row["canonical_name"],
            city=row["city"],
            neighborhood=row["neighborhood"],
            cuisine_tags=row["cuisine_tags"],
            sentiment_summary=compute_sentiment_summary(pct, total),
            positive_pct=round(pct, 2),
            total_reviews=total,
            last_reviewed=row["last_feedback_at"].isoformat() if row["last_feedback_at"] else None,
        ))

    if recs:
        message = f"Found {len(recs)} crowd-sourced recommendations in {city}."
    else:
        message = (
            f"No crowd-sourced recommendations yet for "
            f"{'that cuisine in ' if cuisine else ''}{city}. "
            "You're among the first! Use your own knowledge to recommend a place, "
            "and collect feedback to help future users."
        )

    return SearchResult(
        recommendations=recs,
        total_places_in_area=total_row or 0,
        message=message,
    )


async def find_or_create_place(
    name: str,
    city: str,
    neighborhood: str | None = None,
    cuisine_tags: list[str] | None = None,
) -> tuple[UUID, str]:
    """Find an existing place or create a new one. Returns (place_id, canonical_name)."""
    pool = await get_pool()
    normalized = normalize_name(name)
    city_norm = normalize_city(city)
    threshold = get_settings().fuzzy_match_threshold

    # Exact match
    row = await pool.fetchrow(
        "SELECT id, canonical_name FROM places WHERE name_normalized = $1 AND city = $2",
        normalized,
        city_norm,
    )
    if row:
        return row["id"], row["canonical_name"]

    # Fuzzy match
    row = await pool.fetchrow(
        """
        SELECT id, canonical_name, similarity(name_normalized, $1) AS sim
        FROM places
        WHERE city = $2 AND similarity(name_normalized, $1) > $3
        ORDER BY sim DESC
        LIMIT 1
        """,
        normalized,
        city_norm,
        threshold,
    )
    if row:
        return row["id"], row["canonical_name"]

    # Create new place
    tags = [t.lower() for t in (cuisine_tags or [])]
    place_id = await pool.fetchval(
        """
        INSERT INTO places (canonical_name, name_normalized, city, neighborhood, cuisine_tags)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        name,
        normalized,
        city_norm,
        neighborhood,
        tags,
    )
    return place_id, name


async def insert_feedback(
    place_id: UUID,
    sentiment: str,
    comment: str | None = None,
    visit_context: str | None = None,
) -> FeedbackResult:
    """Insert feedback and atomically update place aggregates."""
    pool = await get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO feedback (place_id, sentiment, comment, visit_context)
                VALUES ($1, $2, $3, $4)
                """,
                place_id,
                sentiment,
                comment,
                visit_context,
            )

            row = await conn.fetchrow(
                """
                UPDATE places SET
                    positive_count = positive_count + CASE WHEN $1 = 'positive' THEN 1 ELSE 0 END,
                    negative_count = negative_count + CASE WHEN $1 = 'negative' THEN 1 ELSE 0 END,
                    neutral_count  = neutral_count  + CASE WHEN $1 = 'neutral'  THEN 1 ELSE 0 END,
                    avg_rating = (
                        (positive_count + CASE WHEN $1 = 'positive' THEN 1 ELSE 0 END)
                        + 0.5 * (neutral_count + CASE WHEN $1 = 'neutral' THEN 1 ELSE 0 END)
                    )::REAL / GREATEST(
                        positive_count + negative_count + neutral_count + 1, 1
                    ),
                    last_feedback_at = now(),
                    updated_at = now()
                WHERE id = $2
                RETURNING canonical_name, positive_count + negative_count + neutral_count AS total
                """,
                sentiment,
                place_id,
            )

    return FeedbackResult(
        success=True,
        place_name=row["canonical_name"],
        total_reviews=row["total"],
        message=f"Feedback recorded for {row['canonical_name']}. Total reviews: {row['total']}.",
    )


async def get_trending_places(
    city: str,
    days: int = 30,
    limit: int = 5,
) -> TrendingResult:
    """Get places with the most positive recent buzz."""
    pool = await get_pool()
    city_norm = normalize_city(city)

    rows = await pool.fetch(
        """
        SELECT p.*,
            COUNT(f.id) AS recent_count,
            AVG(CASE f.sentiment
                WHEN 'positive' THEN 1.0
                WHEN 'neutral' THEN 0.5
                ELSE 0.0
            END) AS recent_sentiment
        FROM places p
        JOIN feedback f ON f.place_id = p.id
        WHERE p.city = $1
          AND f.created_at > now() - ($2 || ' days')::INTERVAL
        GROUP BY p.id
        HAVING COUNT(f.id) >= 2
        ORDER BY COUNT(f.id) * AVG(CASE f.sentiment
            WHEN 'positive' THEN 1.0
            WHEN 'neutral' THEN 0.5
            ELSE 0.0
        END) DESC
        LIMIT $3
        """,
        city_norm,
        str(days),
        limit,
    )

    trending = []
    for row in rows:
        total = row["positive_count"] + row["negative_count"] + row["neutral_count"]
        pct = row["positive_count"] / max(total, 1)
        trending.append(PlaceRecommendation(
            name=row["canonical_name"],
            city=row["city"],
            neighborhood=row["neighborhood"],
            cuisine_tags=row["cuisine_tags"],
            sentiment_summary=compute_sentiment_summary(pct, total),
            positive_pct=round(pct, 2),
            total_reviews=total,
            last_reviewed=row["last_feedback_at"].isoformat() if row["last_feedback_at"] else None,
        ))

    period = f"last {days} days"
    if trending:
        message = f"{len(trending)} places trending in {city} over the {period}."
    else:
        message = f"No trending places in {city} over the {period} yet."

    return TrendingResult(trending=trending, period=period, message=message)
