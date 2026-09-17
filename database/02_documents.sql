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
