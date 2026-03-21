from typing import Annotated

from pydantic import Field

from tastebud.db.queries import find_or_create_place, insert_feedback
from tastebud.server import mcp


@mcp.tool()
async def log_feedback(
    place_name: Annotated[str, Field(description="Name of the restaurant or food place as the user mentioned it.")],
    city: Annotated[str, Field(description="City where the place is located.")],
    sentiment: Annotated[str, Field(description="Overall sentiment: 'positive', 'negative', or 'neutral'. Infer from the user's description.")],
    neighborhood: Annotated[str | None, Field(description="Neighborhood if known.")] = None,
    cuisine_tags: Annotated[list[str] | None, Field(description="Cuisine types (e.g., ['thai', 'noodles']). Infer from conversation.")] = None,
    comment: Annotated[str | None, Field(description="Brief summary of feedback (1 sentence max). Anonymize: no names, no identifying details.")] = None,
    visit_context: Annotated[str | None, Field(description="Context: 'dinner', 'lunch', 'brunch', 'takeout', 'delivery', 'date night', etc.")] = None,
) -> dict:
    """Log anonymized feedback about a food place from a real visit.

    Call this after a user shares how their dining experience went.
    The feedback is fully anonymized — no user identity is stored.
    If the place doesn't exist in the database yet, it will be created.
    """
    if sentiment not in ("positive", "negative", "neutral"):
        return {"success": False, "message": "Sentiment must be 'positive', 'negative', or 'neutral'."}

    place_id, canonical_name = await find_or_create_place(
        name=place_name,
        city=city,
        neighborhood=neighborhood,
        cuisine_tags=cuisine_tags,
    )

    result = await insert_feedback(
        place_id=place_id,
        sentiment=sentiment,
        comment=comment,
        visit_context=visit_context,
    )
    return result.model_dump()
