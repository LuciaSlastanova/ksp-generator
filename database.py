import os
import streamlit as st
from supabase import create_client, Client


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

    return response


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
