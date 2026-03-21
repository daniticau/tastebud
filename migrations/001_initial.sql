CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Canonical place registry. Each row is a unique restaurant/food spot.
CREATE TABLE places (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name  TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    city            TEXT NOT NULL,
    neighborhood    TEXT,
    cuisine_tags    TEXT[] DEFAULT '{}',

    positive_count  INTEGER NOT NULL DEFAULT 0,
    negative_count  INTEGER NOT NULL DEFAULT 0,
    neutral_count   INTEGER NOT NULL DEFAULT 0,
    avg_rating      REAL,

    last_feedback_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_places_name_trgm ON places USING gin (name_normalized gin_trgm_ops);
CREATE INDEX idx_places_city ON places (city);
CREATE INDEX idx_places_cuisine ON places USING gin (cuisine_tags);
CREATE INDEX idx_places_city_rating ON places (city, avg_rating DESC NULLS LAST);

-- Individual feedback entries. Fully anonymized — no user IDs.
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
