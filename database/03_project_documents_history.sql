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
