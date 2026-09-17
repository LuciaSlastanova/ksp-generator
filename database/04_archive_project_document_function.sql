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
