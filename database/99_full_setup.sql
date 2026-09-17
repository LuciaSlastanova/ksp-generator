-- =========================================================
-- KSP GENERATOR - FULL DATABASE SETUP
-- PostgreSQL / Supabase
-- =========================================================

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

-- =========================================================
-- TABUĽKA: documents
-- Aktuálne dokumenty priradené k projektom
-- =========================================================

CREATE TABLE IF NOT EXISTS public.documents
(
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL,
    document_type TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT documents_project_id_fkey
        FOREIGN KEY (project_id)
        REFERENCES public.projects(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_documents_project_id
    ON public.documents(project_id);

CREATE INDEX IF NOT EXISTS idx_documents_project_type
    ON public.documents(project_id, document_type);

-- =========================================================
-- TABUĽKA: project_documents_history
-- História nahradených / archivovaných dokumentov
-- =========================================================

CREATE TABLE IF NOT EXISTS public.project_documents_history
(
    history_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    original_id BIGINT,
    project_id BIGINT,
    document_type TEXT,
    file_name TEXT,
    file_path TEXT,
    original_created_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_history_project_id
    ON public.project_documents_history(project_id);

CREATE INDEX IF NOT EXISTS idx_document_history_project_type
    ON public.project_documents_history(project_id, document_type);

-- =========================================================
-- FUNKCIA: archive_project_document
-- Pred zmazaním riadku z documents uloží jeho pôvodnú
-- podobu do project_documents_history.
-- =========================================================

CREATE OR REPLACE FUNCTION public.archive_project_document()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO public.project_documents_history
    (
        original_id,
        project_id,
        document_type,
        file_name,
        file_path,
        original_created_at,
        archived_at
    )
    VALUES
    (
        OLD.id,
        OLD.project_id,
        OLD.document_type,
        OLD.file_name,
        OLD.file_path,
        OLD.created_at,
        NOW()
    );

    RETURN OLD;
END;
$$;

-- =========================================================
-- TRIGGER: trg_archive_project_document
-- Spustí archiváciu pred DELETE z tabuľky documents.
-- =========================================================

DROP TRIGGER IF EXISTS trg_archive_project_document
ON public.documents;

CREATE TRIGGER trg_archive_project_document
BEFORE DELETE
ON public.documents
FOR EACH ROW
EXECUTE FUNCTION public.archive_project_document();
