def compute_sentiment_summary(positive_pct: float, total: int) -> str:
    """Return a human-readable sentiment summary."""
    if total == 0:
        return "No reviews yet"
    if positive_pct >= 0.8 and total >= 3:
        return "Highly recommended"
    if positive_pct >= 0.6:
        return "Generally positive"
    if positive_pct >= 0.4:
        return "Mixed reviews"
    return "Not well received"
