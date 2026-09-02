import streamlit as st
from supabase import create_client, Client
from uuid import uuid4


BUCKET_NAME = "project-documents"


def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    return create_client(url, key)


def create_project(name, status="Rozpracované"):
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


def get_projects():
    supabase = get_supabase_client()

    response = (
        supabase
        .table("projects")
        .select("*")
        .order("createds_at", desc=True)
        .execute()
    )

    return response.data


def upload_project_file(
    project_id,
    uploaded_file,
    document_type
):
    supabase = get_supabase_client()

    # Unikátny názov, aby sa súbory neprepisovali
    unique_name = f"{uuid4()}_{uploaded_file.name}"

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

    # 1. uloženie samotného súboru do Storage
    supabase.storage.from_(
        BUCKET_NAME
    ).upload(
        file_path,
        file_bytes,
        {
            "content-type": content_type
        }
    )

    # 2. uloženie informácie o súbore do tabuľky documents
    document_data = {
        "project_id": project_id,
        "document_type": document_type,
        "file_name": uploaded_file.name,
        "file_path": file_path
    }

    response = (
        supabase
        .table("documents")
        .insert(document_data)
        .execute()
    )

    return response.data


def get_project_documents(project_id):
    supabase = get_supabase_client()

    response = (
        supabase
        .table("documents")
        .select("*")
        .eq("project_id", project_id)
        .order("created_at", desc=False)
        .execute()
    )

    return response.data
