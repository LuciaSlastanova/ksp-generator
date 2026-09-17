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
