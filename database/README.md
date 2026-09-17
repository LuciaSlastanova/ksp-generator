# Database – KSP Generator

SQL skripty pre PostgreSQL / Supabase databázu projektu **KSP Generator**.

## Súbory

- `01_projects.sql` – projekty a uložená hlavička KSP
- `02_documents.sql` – aktuálne projektové dokumenty
- `03_project_documents_history.sql` – história nahradených dokumentov
- `04_archive_project_document_function.sql` – PL/pgSQL funkcia pre archiváciu
- `05_archive_project_document_trigger.sql` – trigger pred vymazaním dokumentu
- `99_full_setup.sql` – všetko vyššie v jednom skripte

## Logika verziovania dokumentov

Aplikácia používa tabuľku `documents` pre aktuálne dokumenty.

Pri nahradení dokumentu:
1. nový dokument sa uloží do `documents`,
2. starý riadok sa z `documents` odstráni,
3. `BEFORE DELETE` trigger automaticky uloží starý riadok do `project_documents_history`,
4. fyzický historický súbor môže zostať v Supabase Storage.

> Poznámka: názov stĺpca `createds_at` v tabuľke `projects` je ponechaný podľa aktuálneho Python kódu aplikácie.
