import re
import unicodedata

import streamlit as st

from supabase import create_client, Client
from uuid import uuid4


BUCKET_NAME = "project-documents"


# --------------------------------------------------
# SUPABASE CLIENT
# --------------------------------------------------

def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    return create_client(
        url,
        key
    )


# --------------------------------------------------
# BEZPEČNÝ NÁZOV SÚBORU
# --------------------------------------------------

def sanitize_filename(filename):
    normalized = unicodedata.normalize(
        "NFKD",
        filename
    )

    ascii_name = (
        normalized
        .encode(
            "ascii",
            "ignore"
        )
        .decode("ascii")
    )

    safe_name = re.sub(
        r"[^A-Za-z0-9._-]",
        "_",
        ascii_name
    )

    safe_name = re.sub(
        r"_+",
        "_",
        safe_name
    )

    return safe_name


# --------------------------------------------------
# VYTVORENIE PROJEKTU
# --------------------------------------------------

def create_project(
    name,
    status="Rozpracované"
):
    supabase = get_supabase_client()

    data = {
        "name": name,
        "status": status
    }

    response = (
        supabase
        .table("projects")
        .insert(data)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


# --------------------------------------------------
# NAČÍTANIE PROJEKTOV
# --------------------------------------------------

def get_projects():
    supabase = get_supabase_client()

    response = (
        supabase
        .table("projects")
        .select("*")
        .order(
            "createds_at",
            desc=True
        )
        .execute()
    )

    return response.data


# --------------------------------------------------
# ULOŽENIE HLAVIČKY PROJEKTU
# --------------------------------------------------

def save_project_header(
    project_id,
    header_metadata
):
    """
    Uloží finálnu, používateľom skontrolovanú
    hlavičku KSP priamo k projektu.
    """

    supabase = get_supabase_client()

    response = (
        supabase
        .table("projects")
        .update(
            {
                "header_metadata":
                    header_metadata
            }
        )
        .eq(
            "id",
            project_id
        )
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


# --------------------------------------------------
# NAČÍTANIE ULOŽENEJ HLAVIČKY PROJEKTU
# --------------------------------------------------

def get_project_header(
    project_id
):
    """
    Načíta uloženú finálnu hlavičku KSP.
    """

    supabase = get_supabase_client()

    response = (
        supabase
        .table("projects")
        .select(
            "header_metadata"
        )
        .eq(
            "id",
            project_id
        )
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return (
        response.data[0]
        .get(
            "header_metadata"
        )
    )


# --------------------------------------------------
# NAHRATIE SÚBORU K PROJEKTU
# --------------------------------------------------

def upload_project_file(
    project_id,
    uploaded_file,
    document_type
):
    supabase = get_supabase_client()

    safe_file_name = sanitize_filename(
        uploaded_file.name
    )

    unique_name = (
        f"{uuid4()}_"
        f"{safe_file_name}"
    )

    file_path = (
        f"{project_id}/"
        f"{document_type}/"
        f"{unique_name}"
    )

    file_bytes = uploaded_file.getvalue()

    content_type = (
        uploaded_file.type
        if uploaded_file.type
        else "application/octet-stream"
    )

    supabase.storage.from_(
        BUCKET_NAME
    ).upload(
        file_path,
        file_bytes,
        {
            "content-type":
                content_type
        }
    )

    document_data = {
        "project_id":
            project_id,

        "document_type":
            document_type,

        "file_name":
            uploaded_file.name,

        "file_path":
            file_path
    }

    response = (
        supabase
        .table("documents")
        .insert(document_data)
        .execute()
    )

    return response.data


# --------------------------------------------------
# NAČÍTANIE DOKUMENTOV PROJEKTU
# --------------------------------------------------

def get_project_documents(
    project_id
):
    supabase = get_supabase_client()

    response = (
        supabase
        .table("documents")
        .select("*")
        .eq(
            "project_id",
            project_id
        )
        .order(
            "created_at",
            desc=False
        )
        .execute()
    )

    return response.data


# --------------------------------------------------
# NAČÍTANIE NAJNOVŠIEHO DOKUMENTU DANÉHO TYPU
# --------------------------------------------------

def get_latest_project_document(
    project_id,
    document_type
):
    """
    Načíta najnovší aktuálny dokument
    daného typu pre konkrétny projekt.
    """

    supabase = get_supabase_client()

    response = (
        supabase
        .table("documents")
        .select("*")
        .eq(
            "project_id",
            project_id
        )
        .eq(
            "document_type",
            document_type
        )
        .order(
            "created_at",
            desc=True
        )
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


# --------------------------------------------------
# STIAHNUTIE SÚBORU
# --------------------------------------------------

def download_project_file(
    file_path
):
    supabase = get_supabase_client()

    response = (
        supabase
        .storage
        .from_(BUCKET_NAME)
        .download(file_path)
    )

    return response


# --------------------------------------------------
# ARCHIVÁCIA DOKUMENTU
# --------------------------------------------------

def archive_project_document(
    document_id
):
    """
    Odstráni dokument iba z tabuľky documents.

    BEFORE DELETE trigger v Supabase
    automaticky uloží starý záznam do
    project_documents_history.

    Fyzický súbor zostáva v Storage,
    takže historická verzia zostáva zachovaná.
    """

    supabase = get_supabase_client()

    response = (
        supabase
        .table("documents")
        .delete()
        .eq(
            "id",
            document_id
        )
        .execute()
    )

    return response.data


# --------------------------------------------------
# DEFINITÍVNE VYMAZANIE DOKUMENTU
# --------------------------------------------------

def delete_project_document(
    document_id,
    file_path
):
    """
    Definitívne vymaže dokument
    zo Storage aj z tabuľky documents.

    Používať iba vtedy, keď dokument
    nechceme ponechať ani v histórii.
    """

    supabase = get_supabase_client()

    # ------------------------------------------
    # 1. VYMAZANIE SÚBORU ZO STORAGE
    # ------------------------------------------

    if file_path:
        (
            supabase
            .storage
            .from_(BUCKET_NAME)
            .remove(
                [file_path]
            )
        )

    # ------------------------------------------
    # 2. VYMAZANIE ZÁZNAMU Z DATABÁZY
    # ------------------------------------------

    response = (
        supabase
        .table("documents")
        .delete()
        .eq(
            "id",
            document_id
        )
        .execute()
    )

    return response.data


# --------------------------------------------------
# NAČÍTANIE HISTÓRIE DOKUMENTOV
# --------------------------------------------------

def get_project_document_history(
    project_id,
    document_type=None
):
    """
    Načíta historické verzie dokumentov projektu.
    Voliteľne len pre konkrétny document_type.
    """

    supabase = get_supabase_client()

    query = (
        supabase
        .table("project_documents_history")
        .select("*")
        .eq(
            "project_id",
            project_id
        )
    )

    if document_type:
        query = query.eq(
            "document_type",
            document_type
        )

    response = (
        query
        .order(
            "archived_at",
            desc=True
        )
        .execute()
    )

    return response.data
