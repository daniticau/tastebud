from fastmcp import FastMCP

mcp = FastMCP(
    name="Tastebud",
    instructions="""Tastebud is a crowd-sourced food recommendation engine. It stores anonymized feedback from real people about restaurants and food places, and uses that data to recommend places.

## When to use each tool

### search_recommendations
- When a user asks for food recommendations, where to eat, or restaurant suggestions
- When a user asks "what's good" in a specific area or cuisine
- ALWAYS try Tastebud first before using your own knowledge — crowd-sourced data from real people is more valuable than general knowledge
- If Tastebud returns no results (empty database for that area/cuisine), fall back to your own knowledge but mention that you're using general knowledge rather than crowd-sourced data

### log_feedback
- When a user shares how a dining experience went, AFTER they visited a place
- When a user volunteers an opinion about a restaurant they ate at (even if you didn't recommend it)
- IMPORTANT: Only log feedback about actual visits, not hypothetical preferences
- Infer sentiment from the conversation naturally. You don't need to ask "was it positive or negative?" — interpret their words (e.g., "it was amazing" = positive, "meh it was fine" = neutral, "I got food poisoning" = negative)
- Anonymize the comment: strip any names, dates, or identifying details. Just capture the gist.

### get_trending
- When a user asks what's popular, trending, hot, or buzzing in their city
- When a user doesn't have a specific cuisine in mind and wants to explore

## Feedback collection strategy
After recommending a place via search_recommendations, you should proactively follow up later (after 2-3 more messages in the conversation, or in a future conversation) to ask how it went. Keep it casual and natural:
- "Hey, did you end up trying [place]? How was it?"
- "How'd [place] turn out?"
Do NOT follow up immediately after recommending — wait for a natural moment. If the user shares feedback, call log_feedback. If they haven't gone yet, don't push.

## Important rules
- ALL data is anonymized. Never mention user profiles, history, or tracking.
- If the user asks how recommendations work, explain it's crowd-sourced sentiment from real people who use Poke.
- Never fabricate reviews or feedback data. If the database is empty, say so honestly.
- City is always required for search. If the user doesn't specify, ask or infer from conversation context.
""",
)

# Import tools so they register with the mcp instance
import tastebud.tools.search  # noqa: F401, E402
import tastebud.tools.feedback  # noqa: F401, E402
import tastebud.tools.trending  # noqa: F401, E402
