from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Place(BaseModel):
    """Database row for a place."""

    id: UUID
    canonical_name: str
    name_normalized: str
    city: str
    neighborhood: str | None = None
    cuisine_tags: list[str] = Field(default_factory=list)
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    avg_rating: float | None = None
    last_feedback_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PlaceRecommendation(BaseModel):
    """A single recommendation returned to the agent."""

    name: str
    city: str
    neighborhood: str | None = None
    cuisine_tags: list[str] = Field(default_factory=list)
    sentiment_summary: str
    positive_pct: float
    total_reviews: int
    last_reviewed: str | None = None


class SearchResult(BaseModel):
    """Response from search_recommendations."""

    recommendations: list[PlaceRecommendation]
    total_places_in_area: int
    message: str


class FeedbackResult(BaseModel):
    """Response from log_feedback."""

    success: bool
    place_name: str
    total_reviews: int
    message: str


class TrendingResult(BaseModel):
    """Response from get_trending."""

    trending: list[PlaceRecommendation]
    period: str
    message: str
