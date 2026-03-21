from typing import Annotated

from pydantic import Field

from tastebud.db.queries import get_trending_places
from tastebud.server import mcp


@mcp.tool()
async def get_trending(
    city: Annotated[str, Field(description="City to get trending places for.")],
    days: Annotated[int, Field(description="Look-back window in days (7-30).", ge=7, le=30)] = 30,
    limit: Annotated[int, Field(description="Maximum results to return (1-10).", ge=1, le=10)] = 5,
) -> dict:
    """Get places that are trending based on recent feedback volume and sentiment.

    Shows places getting the most positive buzz recently.
    Useful when the user asks what's hot, popular, or new.
    """
    result = await get_trending_places(city, days, limit)
    return result.model_dump()
