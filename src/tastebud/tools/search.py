from typing import Annotated

from pydantic import Field

from tastebud.db.queries import search_places
from tastebud.server import mcp


@mcp.tool()
async def search_recommendations(
    city: Annotated[str, Field(description="City name (e.g., 'San Diego', 'Los Angeles'). Required.")],
    cuisine: Annotated[str | None, Field(description="Type of food/cuisine (e.g., 'thai', 'pizza', 'sushi'). Leave empty for all cuisines.")] = None,
    neighborhood: Annotated[str | None, Field(description="Neighborhood or area within the city (e.g., 'Downtown', 'North Park').")] = None,
    limit: Annotated[int, Field(description="Maximum recommendations to return (1-10).", ge=1, le=10)] = 5,
) -> dict:
    """Search crowd-sourced food recommendations from real people.

    Returns places ranked by community sentiment, review count, and recency.
    Only includes places that real people have recommended through Poke conversations.
    If no results found, returns an empty list — use your own knowledge instead.
    """
    result = await search_places(city, cuisine, neighborhood, limit)
    return result.model_dump()
