-- =========================================================
-- TABUĽKA: projects
-- Základné údaje projektu + uložená hlavička KSP
-- =========================================================

CREATE TABLE IF NOT EXISTS public.projects
(
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Rozpracované',
    createds_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    header_metadata JSONB
);
